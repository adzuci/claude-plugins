#!/usr/bin/env node
/* eslint-disable */
/**
 * enumerate_sessions.mjs  —  data layer for the `insights` skill.
 *
 * Cheap, deterministic pass over ~/.claude/projects/**.jsonl. Produces a
 * per-prompt ("episode") work-list with MODEL attribution and pre-computed
 * cost/behavior signals, so the expensive LLM fan-out only has to *judge* a
 * handful of pre-flagged episodes instead of re-reading whole transcripts.
 *
 * Two outputs:
 *   - stdout: a COMPACT work-list (one entry per session, flagged episodes only,
 *     line numbers + flags + previews, NO bulky signal payloads) — small enough
 *     to hand straight to the Workflow tool as `args`.
 *   - <outdir>/worklist.json: the FULL detail (every flagged episode + signals),
 *     read on demand by fan-out agents via `jq`, never loaded into main context.
 *
 * Usage:
 *   node enumerate_sessions.mjs [--since 7d|24h|ISO] [--sessions N]
 *                               [--project-hash HASH] [--outdir DIR]
 *                               [--dir <projects-dir>]
 *
 * JSONL schema notes (see also the official session-report analyzer):
 *  - One API response is split into MULTIPLE type:"assistant" entries sharing a
 *    requestId/message.id; only the last carries final output_tokens. Dedupe by
 *    requestId, keep max output_tokens.
 *  - type:"user" entries include tool_result blocks, interrupt markers, compact
 *    summaries and meta text. A real human prompt has isMeta/isCompactSummary/
 *    isSidechain falsy and plain-string-or-text content that isn't a tool_result.
 *  - model lives on message.model of assistant entries.
 */

import fs from 'fs'
import os from 'os'
import path from 'path'
import readline from 'readline'

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------
const argv = process.argv.slice(2)
function flag(name, dflt) {
  const i = argv.indexOf(name)
  if (i === -1) return dflt
  const v = argv[i + 1]
  return v === undefined || v.startsWith('--') ? true : v
}
const ROOT = flag('--dir', path.join(os.homedir(), '.claude', 'projects'))
const OUTDIR = flag('--outdir', path.join(os.tmpdir(), 'insights'))
const SINCE = parseSince(flag('--since', '7d'))
const SESSION_LIMIT = parseInt(flag('--sessions', '0'), 10) || 0
const PROJECT_HASH = flag('--project-hash', null)

// Analysis-logic version. Bumped whenever the REVIEWER logic/prompt changes in a way
// that should invalidate cached leaf findings (the fingerprint keys on session state,
// not on how it was analyzed — so without this, a re-run would serve stale findings
// generated under the old prompt). v2: compaction-aware cache_break framing + opusplan.
// v3: per-session revive classification (SESSION_SCHEMA gains a required `revivals`
// array) — pre-v3 leaves lack it, so they MUST roll or a cache hit would return a
// finding the new schema rejects.
const ANALYSIS_VERSION = 'v3'

// thresholds (tunable)
const CACHE_BREAK = 100000 // uncached input on a single call → cache break
const BIG_OUTPUT = 50000 // chars in a single tool_result → unfiltered fetch
const SMALL_OUT = 2000 // output tokens ceiling for a "small" opus turn
const SMALL_CALLS = 3 // api calls ceiling for a "small" turn
const SMALL_TOOLS = 6 // tool calls ceiling for a "small" turn
const REREAD_MIN = 2 // same file Read this many times → re-read
const THRASH_MIN = 3 // same tool input this many times → thrash

// approximate list prices ($/Mtok) for rough cost framing only — labelled "≈"
const PRICES = {
  opus: { in: 15, cache_w: 18.75, cache_r: 1.5, out: 75 },
  sonnet: { in: 3, cache_w: 3.75, cache_r: 0.3, out: 15 },
  haiku: { in: 1, cache_w: 1.25, cache_r: 0.1, out: 5 },
  other: { in: 3, cache_w: 3.75, cache_r: 0.3, out: 15 },
}

function parseSince(s) {
  if (!s || s === true) return null
  const m = /^(\d+)([dh])$/.exec(s)
  if (m)
    return new Date(
      Date.now() - parseInt(m[1], 10) * (m[2] === 'd' ? 86400000 : 3600000),
    )
  const d = new Date(s)
  return isNaN(d) ? null : d
}

function modelFamily(model) {
  if (!model) return 'other'
  const m = model.toLowerCase()
  if (m.includes('opus')) return 'opus'
  if (m.includes('sonnet')) return 'sonnet'
  if (m.includes('haiku')) return 'haiku'
  return 'other'
}

// Monday (UTC) of the week containing ms, as a YYYY-MM-DD string. The skill is
// week-oriented: every session is bucketed into the week it began so burn can be
// read week-over-week.
function mondayOf(ms) {
  const d = new Date(ms)
  const dow = (d.getUTCDay() + 6) % 7 // 0 = Monday
  const mon = new Date(
    Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate() - dow),
  )
  return mon.toISOString().slice(0, 10)
}

// ---------------------------------------------------------------------------
// File discovery (main transcripts only; subagent/workflow tokens roll up via
// the prompt that spawned them, but for behavior analysis we read main files).
// ---------------------------------------------------------------------------
function* walk(dir) {
  let ents
  try {
    ents = fs.readdirSync(dir, { withFileTypes: true })
  } catch {
    return
  }
  for (const e of ents) {
    const p = path.join(dir, e.name)
    if (e.isDirectory()) {
      if (e.name === 'subagents' || e.name === 'workflows') continue
      yield* walk(p)
    } else if (e.isFile() && e.name.endsWith('.jsonl')) yield p
  }
}

function cleanText(s) {
  if (!s) return ''
  return s
    .replace(/<command-[^>]*>/g, ' ')
    .replace(/<\/command-[^>]*>/g, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}
function preview(s, n = 200) {
  const t = cleanText(s)
  return t.length > n ? t.slice(0, n - 1) + '…' : t
}

// extreme-underspecification lexicon: vague even WITH prior transcript context
const VAGUE = [
  /\bstill (not|isn'?t|doesn'?t) work/i,
  /\bnot work/i,
  /\bdoesn'?t work/i,
  /\bdidn'?t work/i,
  /\bidk\b/i,
  /\bfix it\b/i,
  /\bjust fix/i,
  /\bsame (thing|issue|error|problem)\b/i,
  /\btry again\b/i,
  /^no+$/i,
  /^nope$/i,
  /^nah$/i,
  /^(it'?s )?broken$/i,
  /^(still )?broken$/i,
  /^that'?s wrong$/i,
  /^wrong$/i,
  /^no it'?s still/i,
  /^keep going$/i,
  /^continue$/i,
  /^go on$/i,
  /\bwhatever\b/i,
]
function isUnderspecified(text) {
  const t = cleanText(text)
  if (!t) return false
  const words = t.split(/\s+/).filter(Boolean)
  const vague = VAGUE.some(r => r.test(t))
  // short AND vague, OR extremely short (<=4 words) with no concrete noun-ish token
  if (vague && words.length <= 12) return true
  if (words.length <= 4 && !/[\/.]|`|[A-Z][a-z]+[A-Z]/.test(t) && vague)
    return true
  return false
}

// ---------------------------------------------------------------------------
// Per-file parse → episodes
// ---------------------------------------------------------------------------
async function parseFile(file, project, sessionId) {
  const rl = readline.createInterface({
    input: fs.createReadStream(file, { encoding: 'utf8' }),
    crlfDelay: Infinity,
  })

  const episodes = []
  const cacheBreaks = []
  // context compactions (auto or manual). Each compaction REWRITES the prompt prefix,
  // so the next assistant call re-ingests the compacted context COLD — i.e. compaction
  // is a CAUSE of cache-break re-ingest, not a fix for it. We track events + the tokens
  // each one re-ingested so the report can say "compacted 32x @ ~168k" instead of the
  // (often false) "never compacted".
  const compactions = [] // {line, ts, trigger, preTokens}
  let pendingCompactLine = null // a compaction whose cold re-ingest we haven't seen yet
  let planMarkers = 0 // mode-change markers into a non-"normal" (plan) mode — opusplan signal
  // session-level "work output" signals — deterministic grounding for the
  // subjective burn-vs-output judgment (was the spend worth what it produced?)
  const output = { commits: 0, edits: 0, test_runs: 0, reverts: 0, files: {} }
  const modelMix = {} // family -> {in, out, calls} (deduped by requestId)
  function famAdd(fam, rec, sign) {
    if (!modelMix[fam]) modelMix[fam] = { in: 0, out: 0, calls: 0 }
    modelMix[fam].in += sign * (rec.in_uncached + rec.in_cache_w + rec.in_cache_r)
    modelMix[fam].out += sign * rec.out
    modelMix[fam].calls += sign
  }
  let firstTs = null,
    lastTs = null
  let cur = null // current episode
  const seenReq = new Map() // requestId -> committed (per file)
  let lineNo = 0
  let inWindow = false

  function newEpisode(line, ts, text, slash) {
    return {
      line,
      ts,
      text: preview(text || (slash ? '/' + slash : ''), 220),
      full_text: cleanText(text).slice(0, 600),
      first_response: '', // first assistant text block (filled on first hit)
      slash: slash || null,
      models: {}, // family -> calls
      modelRaw: {}, // raw model id -> calls
      api_calls: 0,
      subagent_calls: 0,
      in_uncached: 0,
      in_cache_w: 0,
      in_cache_r: 0,
      out: 0,
      tool_mix: {}, // name -> count
      n_errors: 0,
      n_interrupts: 0,
      reverts: 0, // git undo ops in this turn (classified stuck vs pivot at finalize)
      reads: {}, // file_path -> count
      toolInputs: {}, // signature -> count  (thrash detection)
      big_outputs: [], // {tool, chars, line}
      cache_break_lines: [],
      underspecified: isUnderspecified(text),
    }
  }

  for await (const line of rl) {
    lineNo++
    if (!line) continue
    let e
    try {
      e = JSON.parse(line)
    } catch {
      continue
    }
    const ts = e.timestamp ? Date.parse(e.timestamp) : null
    if (ts && SINCE && ts < SINCE.getTime()) continue
    if (ts) {
      inWindow = true
      if (firstTs === null) firstTs = ts
      lastTs = ts
    }

    // mode markers: Claude Code emits a {type:"mode"} entry on each turn carrying the
    // active mode ("normal" vs "plan"). A non-normal marker means the user used plan
    // mode — the precondition for `opusplan` (Opus only while planning) being a win.
    if (e.type === 'mode') {
      if (e.mode && e.mode !== 'normal') planMarkers++
      continue
    }
    // compaction boundary: the context was just compacted. Record the trigger and the
    // pre-compaction token count (what gets re-ingested cold), and arm pendingCompactLine
    // so the next large uncached call is attributed to this compaction's re-ingest.
    if (e.type === 'system' && e.subtype === 'compact_boundary') {
      const cm = e.compactMetadata || {}
      compactions.push({
        line: lineNo,
        ts: e.timestamp || null,
        trigger: cm.trigger || 'unknown',
        preTokens: cm.preTokens || 0,
      })
      pendingCompactLine = lineNo
      continue
    }

    if (e.type === 'user') {
      if (e.isMeta || e.isCompactSummary || e.isSidechain) continue
      const content = e.message && e.message.content
      let text = null,
        isToolResult = false,
        toolResultChars = 0,
        toolResultErr = false
      if (typeof content === 'string') text = content
      else if (Array.isArray(content)) {
        const first = content[0]
        if (first && first.type === 'tool_result') {
          isToolResult = true
          toolResultErr = !!first.is_error
          const c = first.content
          if (typeof c === 'string') toolResultChars = c.length
          else if (Array.isArray(c))
            toolResultChars = c.reduce(
              (a, b) => a + (b && b.text ? b.text.length : 0),
              0,
            )
        } else if (first && first.type === 'text') text = first.text || ''
      }

      if (isToolResult) {
        if (cur) {
          if (toolResultErr) cur.n_errors++
          if (toolResultChars > BIG_OUTPUT)
            cur.big_outputs.push({
              chars: toolResultChars,
              line: lineNo,
            })
        }
        continue
      }
      if (text == null) continue
      if (
        text.startsWith('<task-notification') ||
        text.startsWith('<scheduled-wakeup') ||
        text.startsWith('<background-task')
      )
        continue
      if (text.startsWith('[Request interrupted')) {
        if (cur) cur.n_interrupts++
        continue
      }
      const sm = /<command-(?:name|message)>\/?([^<]+)<\/command-/.exec(text)
      const slash = sm ? sm[1].trim() : null
      // start a new episode on a real human prompt
      cur = newEpisode(lineNo, e.timestamp || null, text, slash)
      episodes.push(cur)
      // a compaction's cold re-ingest lands on the auto-continuation BEFORE any human
      // prompt; once a human types again, stop attributing later re-ingests to it.
      pendingCompactLine = null
      continue
    }

    if (e.type === 'assistant') {
      const msg = e.message || {}
      const model = msg.model
      const fam = modelFamily(model)
      if (Array.isArray(msg.content)) {
        for (const c of msg.content) {
          if (!c) continue
          if (c.type === 'text' && cur && !cur.first_response && c.text)
            cur.first_response = preview(c.text, 360)
          if (c.type !== 'tool_use') continue
          const name = c.name || 'unknown'
          // session-level work-output signals (independent of episode flags)
          if (name === 'Edit' || name === 'Write' || name === 'MultiEdit' || name === 'NotebookEdit') {
            output.edits++
            if (c.input && c.input.file_path) output.files[c.input.file_path] = true
          }
          if (name === 'Bash' && c.input && c.input.command) {
            const cmd = String(c.input.command)
            if (/\bgit\s+commit\b/.test(cmd)) output.commits++
            // Undo = discarding work already written. Tightened so branch
            // NAVIGATION (`checkout -b`, `checkout <branch>`, `switch`) and bare
            // `git stash` (setting an idea ASIDE, not undoing it) don't count.
            // `git checkout` only counts when it targets a pathspec/HEAD (file
            // restore), never a branch switch.
            const isUndo =
              /\bgit\s+revert\b/.test(cmd) ||
              /\bgit\s+reset\b/.test(cmd) ||
              /\bgit\s+restore\b/.test(cmd) ||
              /\bgit\s+clean\b/.test(cmd) ||
              (/\bgit\s+checkout\b/.test(cmd) &&
                /\bgit\s+checkout\s+(?:-[^\s-]*\s+)*(?:--(?:\s|$)|HEAD\b|\S*\.[a-zA-Z])/.test(cmd) &&
                !/\bgit\s+checkout\s+-b\b/.test(cmd))
            if (isUndo) {
              output.reverts++
              if (cur) cur.reverts = (cur.reverts || 0) + 1
            }
            if (/\b(pytest|jest|vitest|playwright|rspec|mocha|go\s+test|cargo\s+test|(npm|yarn|pnpm)\s+(run\s+)?test)\b/.test(cmd))
              output.test_runs++
          }
          if (cur) {
            cur.tool_mix[name] = (cur.tool_mix[name] || 0) + 1
            if (name === 'Agent' || name === 'Task') cur.subagent_calls++
            // re-read detection
            if (name === 'Read' && c.input && c.input.file_path) {
              const fp = c.input.file_path
              cur.reads[fp] = (cur.reads[fp] || 0) + 1
            }
            // thrash detection: repeated *work/search* signatures only
            // (re-Reading a file is `reread`, not thrash; ignore file_path & inputless tools)
            let sig = null
            if (c.input) {
              if (c.input.command) {
                // strip a leading `cd <path> &&` (cwd resets between Bash calls,
                // so distinct commands share that prefix → false thrash signal)
                const cmd = String(c.input.command).replace(
                  /^\s*cd\s+(?:"[^"]*"|'[^']*'|[^\s&]+)\s*&&\s*/,
                  '',
                )
                sig = name + ':' + cmd.slice(0, 80)
              } else if (c.input.pattern)
                sig = name + ':' + String(c.input.pattern).slice(0, 60)
              else if (c.input.query) sig = name + ':' + String(c.input.query).slice(0, 60)
            }
            if (sig) cur.toolInputs[sig] = (cur.toolInputs[sig] || 0) + 1
          }
        }
      }
      const usage = msg.usage
      if (!usage) continue
      const key = e.requestId || msg.id || `${file}:${e.uuid || lineNo}`
      // dedupe by requestId within file, keep max output
      const prev = seenReq.get(key)
      const out = usage.output_tokens || 0
      if (prev && out < prev.out) continue
      // back out the previous (partial) commit for this requestId if any
      if (prev) {
        if (cur) {
          cur.api_calls -= 1
          cur.in_uncached -= prev.in_uncached
          cur.in_cache_w -= prev.in_cache_w
          cur.in_cache_r -= prev.in_cache_r
          cur.out -= prev.out
          if (prev.fam && cur.models[prev.fam]) cur.models[prev.fam] -= 1
        }
        famAdd(prev.fam, prev, -1)
      }
      const rec = {
        out,
        in_uncached: usage.input_tokens || 0,
        in_cache_w: usage.cache_creation_input_tokens || 0,
        in_cache_r: usage.cache_read_input_tokens || 0,
        fam,
      }
      seenReq.set(key, rec)
      famAdd(fam, rec, +1)
      if (cur) {
        cur.api_calls++
        cur.in_uncached += rec.in_uncached
        cur.in_cache_w += rec.in_cache_w
        cur.in_cache_r += rec.in_cache_r
        cur.out += rec.out
        cur.models[fam] = (cur.models[fam] || 0) + 1
        if (model) cur.modelRaw[model] = (cur.modelRaw[model] || 0) + 1
        const uncached = rec.in_uncached + rec.in_cache_w
        if (uncached > CACHE_BREAK) {
          const postCompaction = pendingCompactLine != null
          cur.cache_break_lines.push(lineNo)
          cacheBreaks.push({ line: lineNo, ts: e.timestamp, uncached, post_compaction: postCompaction })
          // consumed: this break IS the re-ingest the compaction caused
          if (postCompaction) pendingCompactLine = null
        }
      }
    }
  }

  // finalize per-episode flags + signals
  for (const ep of episodes) {
    const fam =
      Object.entries(ep.models).sort((a, b) => b[1] - a[1])[0]?.[0] || 'other'
    ep.primary_model = fam
    ep.tokens = ep.in_uncached + ep.in_cache_w + ep.in_cache_r + ep.out
    const toolCalls = Object.values(ep.tool_mix).reduce((a, b) => a + b, 0)
    ep.n_tool_calls = toolCalls

    const flags = []
    if (ep.underspecified) flags.push('underspecified')

    // "cold" turn: little/no warm cache to bust. cache-read is < half the input,
    // i.e. this is a session start / post-/clear / post-/compact turn rather than
    // a deep warm session. Switching such a turn to a cheaper model is ~free;
    // switching a WARM turn (lots of cache_read) would bust the model-specific
    // cache and cost MORE than the Opus premium saves — so we only flag cold ones.
    const inTotal = ep.in_uncached + ep.in_cache_w + ep.in_cache_r
    ep.cache_read_ratio = inTotal > 0 ? +(ep.in_cache_r / inTotal).toFixed(2) : 0
    ep.cold = inTotal === 0 || ep.cache_read_ratio < 0.5

    // opus-on-small: opus primary AND the turn was trivial AND it was cold.
    // (A trivial Opus turn mid-warm-session is NOT a faux pas — switching models
    // there busts the cache. The actionable habit is starting small/throwaway
    // questions in a fresh Sonnet session, so we target cold turns only.)
    if (
      fam === 'opus' &&
      ep.cold &&
      ep.api_calls <= SMALL_CALLS &&
      ep.out < SMALL_OUT &&
      ep.subagent_calls === 0 &&
      toolCalls <= SMALL_TOOLS
    )
      flags.push('opus_small')

    // re-read: same file Read >= REREAD_MIN within the turn
    ep.reread_files = Object.entries(ep.reads)
      .filter(([, n]) => n >= REREAD_MIN)
      .map(([f, n]) => ({ file: f, n }))
    if (ep.reread_files.length) flags.push('reread')

    // thrash: same command/search re-run >= THRASH_MIN times — flagged only
    // when the turn also hit errors (genuine retry-loop) or the repeat is steep.
    ep.thrash = Object.entries(ep.toolInputs)
      .filter(([, n]) => n >= THRASH_MIN)
      .map(([sig, n]) => ({ sig, n }))
    const maxRepeat = ep.thrash.reduce((a, b) => Math.max(a, b.n), 0)
    if (ep.thrash.length && (ep.n_errors > 0 || maxRepeat >= 4))
      flags.push('thrash')

    // unfiltered fetch / context bloat
    if (ep.big_outputs.length) flags.push('unfiltered_fetch')
    if (ep.cache_break_lines.length) flags.push('cache_break')

    ep.flags = flags
    // est cost ≈
    const p = PRICES[fam] || PRICES.other
    ep.cost_usd =
      (ep.in_uncached * p.in +
        ep.in_cache_w * p.cache_w +
        ep.in_cache_r * p.cache_r +
        ep.out * p.out) /
      1e6
    // drop bulky intermediate maps from the serialized form
    delete ep.toolInputs
    delete ep.reads
    delete ep.models
  }

  const sessionCost = episodes.reduce((a, ep) => a + (ep.cost_usd || 0), 0)
  // opusplan signal: how much of this session ran on Opus, and whether plan mode was
  // used at all. opusplan keeps Opus ONLY for plan mode and drops to Sonnet otherwise,
  // so opus_cost_usd is the spend it would reroute and plan markers say whether the
  // user actually plans (if never, opusplan just = Sonnet-by-default, a quality call).
  let exitPlanCalls = 0,
    opusCost = 0,
    opusEpisodes = 0
  for (const ep of episodes) {
    exitPlanCalls += ep.tool_mix['ExitPlanMode'] || 0
    if (ep.primary_model === 'opus') {
      opusCost += ep.cost_usd || 0
      opusEpisodes++
    }
  }
  const spanDays =
    firstTs && lastTs ? +((lastTs - firstTs) / 86400000).toFixed(1) : 0

  // ---- deterministic efficiency (lean / loose / thrashy) ----
  // "How much of the spend was avoidable churn?" — a pure function of signals this
  // pass already extracts (reverts + per-episode reread/thrash/cache_break flags),
  // so it is computed here rather than judged by an LLM. A probe (Haiku ×10 + Sonnet
  // ×5 on identical inputs) showed models judge this dimension badly: Haiku coin-
  // flipped the churniest session (5 loose / 5 thrashy) and both models tagged the
  // cleanest session "loose" — voting fixes variance, not that bias. This rule is
  // free, perfectly reproducible, and matches intuition on the calibration set.
  // Weights rank the signals by how strongly they evidence wasted work: a STUCK
  // revert (undoing work mid-flail) > a cache break (re-ingesting context) >
  // a redundant re-read > a retry-loop. Crucially, only STUCK reverts count —
  // a PIVOT revert (a clean, deliberate change of direction) is healthy iteration
  // and is weighted 0, so exploring and discarding an idea never reads as churn.
  // Normalized per prompt with a floor of 10 so one revert in an 8-prompt session
  // doesn't spuriously read as "thrashy".
  let eb_cache = 0,
    eb_reread = 0,
    eb_thrash = 0,
    stuckReverts = 0,
    pivotReverts = 0
  for (const ep of episodes) {
    if (ep.flags.includes('cache_break')) eb_cache++
    if (ep.flags.includes('reread')) eb_reread++
    if (ep.flags.includes('thrash')) eb_thrash++
    // Split undos: a revert is STUCK (wall-banging, real waste) only when the
    // turn it lands in shows being-stuck markers — tool/test errors, a thrash or
    // reread flag, or an underspecified ("still broken"/"try again") prompt that
    // kicked it off. A revert in a clean, concretely-directed turn is a deliberate
    // change of mind (PIVOT) — healthy iteration, not waste. Only stuck reverts
    // are penalized. This is the difference between "I chose a different design"
    // and "I keep undoing the same broken attempt", which a raw revert count
    // cannot tell apart.
    const r = ep.reverts || 0
    if (!r) continue
    const stuck =
      ep.n_errors > 0 ||
      ep.flags.includes('thrash') ||
      ep.flags.includes('reread') ||
      ep.underspecified
    if (stuck) stuckReverts += r
    else pivotReverts += r
  }
  const wasteScore =
    stuckReverts * 3 + eb_cache * 2 + eb_reread * 1 + eb_thrash * 0.5
  const wastePerPrompt = wasteScore / Math.max(10, episodes.length)
  const efficiency =
    wastePerPrompt < 0.2 ? 'lean' : wastePerPrompt < 0.6 ? 'loose' : 'thrashy'

  // cache fingerprint: identifies this session's CURRENT state so a leaf finding
  // is reused only while the transcript is unchanged. A session that later grows
  // (more prompts / cost / a newer last_ts) gets a new fingerprint → cache miss →
  // re-analysis. Filename-safe (no colons).
  const cost2 = +sessionCost.toFixed(2)
  const fingerprint = `${ANALYSIS_VERSION}-${episodes.length}p-${Math.round(cost2 * 100)}c-${lastTs ? Math.floor(lastTs / 1000) : 0}`

  return {
    session: sessionId,
    project,
    file,
    first_ts: firstTs ? new Date(firstTs).toISOString() : null,
    last_ts: lastTs ? new Date(lastTs).toISOString() : null,
    week: firstTs ? mondayOf(firstTs) : null,
    fingerprint,
    inWindow,
    n_prompts: episodes.length,
    cost_usd: cost2,
    span_days: spanDays,
    efficiency,
    efficiency_signals: {
      reverts: output.reverts,
      reverts_stuck: stuckReverts, // wall-banging — penalized
      reverts_pivot: pivotReverts, // changed direction — NOT penalized
      cache_break: eb_cache,
      reread: eb_reread,
      thrash: eb_thrash,
      score: +wastePerPrompt.toFixed(3),
    },
    output: {
      commits: output.commits,
      edits: output.edits,
      files_touched: Object.keys(output.files).length,
      test_runs: output.test_runs,
      reverts: output.reverts,
    },
    // compaction reality — kills the false "never compacted" narrative. count/trigger
    // split + total tokens re-ingested, plus how many of this session's cache-breaks
    // were the cold re-ingest immediately after a compaction (vs organic growth/resume).
    compactions: {
      count: compactions.length,
      auto: compactions.filter(c => c.trigger === 'auto').length,
      manual: compactions.filter(c => c.trigger === 'manual').length,
      pre_tokens_total: compactions.reduce((a, c) => a + (c.preTokens || 0), 0),
    },
    cache_break_post_compaction: cacheBreaks.filter(c => c.post_compaction).length,
    // opusplan inputs (see above): plan-mode usage + Opus spend this session.
    plan: { markers: planMarkers, exit_calls: exitPlanCalls },
    opus_cost_usd: +opusCost.toFixed(2),
    opus_episodes: opusEpisodes,
    model_mix: modelMix,
    cache_breaks: cacheBreaks,
    episodes,
  }
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
async function main() {
  let files = [...walk(ROOT)].map(p => {
    const rel = path.relative(ROOT, p)
    const parts = rel.split(path.sep)
    return { p, project: parts[0], sessionId: path.basename(p, '.jsonl') }
  })
  if (PROJECT_HASH && PROJECT_HASH !== true)
    files = files.filter(f => f.project === PROJECT_HASH)
  // most-recent first by mtime
  files.sort((a, b) => mtime(b.p) - mtime(a.p))

  const sessions = []
  for (const f of files) {
    const s = await parseFile(f.p, f.project, f.sessionId)
    if (!s.inWindow || s.n_prompts === 0) continue
    sessions.push(s)
    if (SESSION_LIMIT && sessions.length >= SESSION_LIMIT) break
  }

  // ---- aggregate totals + model mix ----
  const totals = {
    sessions: sessions.length,
    prompts: 0,
    in: 0,
    out: 0,
    cache_read: 0,
    cost_usd: 0,
  }
  const modelMix = {}
  const flagCounts = {
    underspecified: 0,
    opus_small: 0,
    thrash: 0,
    reread: 0,
    unfiltered_fetch: 0,
    cache_break: 0,
  }
  for (const s of sessions) {
    totals.prompts += s.n_prompts
    for (const ep of s.episodes) {
      totals.in += ep.in_uncached + ep.in_cache_w + ep.in_cache_r
      totals.out += ep.out
      totals.cache_read += ep.in_cache_r
      totals.cost_usd += ep.cost_usd
      for (const fl of ep.flags) if (fl in flagCounts) flagCounts[fl]++
    }
    for (const [fam, m] of Object.entries(s.model_mix)) {
      if (!modelMix[fam]) modelMix[fam] = { in: 0, out: 0, calls: 0 }
      modelMix[fam].in += m.in
      modelMix[fam].out += m.out
      modelMix[fam].calls += m.calls
    }
  }
  totals.cache_read_pct =
    totals.in > 0 ? +((100 * totals.cache_read) / totals.in).toFixed(1) : 0
  totals.cost_usd = +totals.cost_usd.toFixed(2)

  // ---- compaction + opusplan rollups (deterministic) ----
  // Nested under totals so they ride the SKILL's `totals: .totals` jq passthrough with
  // no arg-plumbing change. compaction = the real story behind cache-break burn (the
  // window compacted N times, re-ingesting M tokens cold); opusplan = whether routing
  // Opus-to-plan-mode-only would save (opus spend that would move to Sonnet + plan use).
  const compaction = {
    events: 0,
    auto: 0,
    manual: 0,
    pre_tokens_total: 0,
    cache_breaks_post: 0,
    cache_breaks_total: 0,
  }
  const opusplan = {
    plan_markers: 0,
    exit_plan_calls: 0,
    sessions_using_plan: 0,
    opus_cost_usd: 0,
    opus_episodes: 0,
  }
  for (const s of sessions) {
    const c = s.compactions || {}
    compaction.events += c.count || 0
    compaction.auto += c.auto || 0
    compaction.manual += c.manual || 0
    compaction.pre_tokens_total += c.pre_tokens_total || 0
    compaction.cache_breaks_post += s.cache_break_post_compaction || 0
    compaction.cache_breaks_total += (s.cache_breaks || []).length
    const pl = s.plan || {}
    opusplan.plan_markers += pl.markers || 0
    opusplan.exit_plan_calls += pl.exit_calls || 0
    if ((pl.markers || 0) > 0 || (pl.exit_calls || 0) > 0) opusplan.sessions_using_plan++
    opusplan.opus_cost_usd += s.opus_cost_usd || 0
    opusplan.opus_episodes += s.opus_episodes || 0
  }
  opusplan.opus_cost_usd = +opusplan.opus_cost_usd.toFixed(2)
  totals.compaction = compaction
  totals.opusplan = opusplan

  // ---- week-by-week burn (deterministic) — the skill is week-oriented; this
  // drives the burn chart and the week-aware top-level summary. Each week carries
  // total spend + a cost/count split by the deterministic efficiency label, so the
  // chart shows not just how much each week burned but how much of it was churn. ----
  const weekMap = {}
  for (const s of sessions) {
    const wk = s.week || 'undated'
    if (!weekMap[wk])
      weekMap[wk] = {
        week: wk,
        cost_usd: 0,
        sessions: 0,
        prompts: 0,
        efficiency_cost: { lean: 0, loose: 0, thrashy: 0 },
        efficiency_count: { lean: 0, loose: 0, thrashy: 0 },
      }
    const w = weekMap[wk]
    w.cost_usd += s.cost_usd || 0
    w.sessions += 1
    w.prompts += s.n_prompts
    const eff = s.efficiency || 'loose'
    w.efficiency_cost[eff] = (w.efficiency_cost[eff] || 0) + (s.cost_usd || 0)
    w.efficiency_count[eff] = (w.efficiency_count[eff] || 0) + 1
  }
  const byWeek = Object.values(weekMap)
    .map(w => ({
      ...w,
      cost_usd: +w.cost_usd.toFixed(2),
      efficiency_cost: {
        lean: +w.efficiency_cost.lean.toFixed(2),
        loose: +w.efficiency_cost.loose.toFixed(2),
        thrashy: +w.efficiency_cost.thrashy.toFixed(2),
      },
    }))
    .sort((a, b) => (a.week < b.week ? -1 : a.week > b.week ? 1 : 0))

  // id -> fingerprint over ALL enumerated sessions, so the cache layer can key any
  // candidate session's leaf finding regardless of whether it was flagged.
  const fingerprints = {}
  for (const s of sessions) fingerprints[s.session] = s.fingerprint

  // ---- write full detail ----
  fs.mkdirSync(OUTDIR, { recursive: true })
  const worklistPath = path.join(OUTDIR, 'worklist.json')
  const full = {
    generated_at: new Date().toISOString(),
    root: ROOT,
    since: SINCE ? SINCE.toISOString() : null,
    totals,
    model_mix: modelMix,
    flag_counts: flagCounts,
    by_week: byWeek,
    fingerprints,
    sessions,
  }
  fs.writeFileSync(worklistPath, JSON.stringify(full))

  // ---- spend ranking: top sessions by cost, with work-output signals, so the
  // burn-vs-output analysis can target the biggest burners (not just flagged ones)
  // and judge what the money bought. ----
  const sessionsBySpend = [...sessions]
    .sort((a, b) => (b.cost_usd || 0) - (a.cost_usd || 0))
    .slice(0, 10)
    .map(s => ({
      session: s.session,
      project: s.project,
      week: s.week,
      fingerprint: s.fingerprint,
      cost_usd: s.cost_usd || 0,
      prompts: s.n_prompts,
      span_days: s.span_days || 0,
      efficiency: s.efficiency,
      efficiency_signals: s.efficiency_signals,
      output: s.output,
      compactions: s.compactions,
      cache_break_post_compaction: s.cache_break_post_compaction,
      opus_cost_usd: s.opus_cost_usd,
      plan: s.plan,
    }))

  // ---- compact work-list to stdout (flagged episodes only, no bulky payloads) ----
  const compact = {
    worklist_path: worklistPath,
    since: full.since,
    totals,
    model_mix: modelMix,
    flag_counts: flagCounts,
    by_week: byWeek,
    fingerprints,
    sessions_by_spend: sessionsBySpend,
    sessions: sessions
      .map(s => ({
        session: s.session,
        project: s.project,
        file: s.file,
        week: s.week,
        fingerprint: s.fingerprint,
        flagged: s.episodes
          .filter(ep => ep.flags.length)
          .map(ep => ({
            line: ep.line,
            ts: ep.ts,
            model: ep.primary_model,
            flags: ep.flags,
            tokens: ep.tokens,
            out: ep.out,
            cost_usd: +ep.cost_usd.toFixed(3),
            text: ep.text,
          })),
      }))
      .filter(s => s.flagged.length),
  }
  process.stdout.write(JSON.stringify(compact, null, 2) + '\n')

  // human summary to stderr
  const fmt = n =>
    n >= 1e6 ? (n / 1e6).toFixed(1) + 'M' : n >= 1e3 ? (n / 1e3).toFixed(0) + 'k' : '' + n
  process.stderr.write(
    `\ninsights enumerate: ${sessions.length} sessions, ${totals.prompts} prompts, ` +
      `${fmt(totals.in + totals.out)} tokens, ≈$${totals.cost_usd}\n` +
      `flags → underspecified:${flagCounts.underspecified} opus_small:${flagCounts.opus_small} ` +
      `thrash:${flagCounts.thrash} reread:${flagCounts.reread} ` +
      `unfiltered_fetch:${flagCounts.unfiltered_fetch} cache_break:${flagCounts.cache_break}\n` +
      `compaction → ${compaction.events} compactions (auto:${compaction.auto}); only ` +
      `${compaction.cache_breaks_post}/${compaction.cache_breaks_total} cache-breaks follow one → ` +
      `the big cold re-ingests are mostly resume/idle, NOT missing compaction\n` +
      `opusplan → plan used in ${opusplan.sessions_using_plan} sessions; Opus spend ≈$${opusplan.opus_cost_usd} across ${opusplan.opus_episodes} turns\n` +
      `full detail → ${worklistPath}\n`,
  )
}

const _mt = new Map()
function mtime(p) {
  let t = _mt.get(p)
  if (t === undefined) {
    try {
      t = fs.statSync(p).mtimeMs
    } catch {
      t = 0
    }
    _mt.set(p, t)
  }
  return t
}

main().catch(e => {
  console.error(e)
  process.exit(1)
})
