export const meta = {
  name: 'deep-insights',
  description:
    'Deep-analyze local Claude Code sessions: agent behavior on underspecified prompts + cost-control faux pas, fan-out per session then synthesize a one-screen report with a team-level config recommendation.',
  phases: [
    { title: 'Analyze', detail: 'one agent per flagged session — confirm + quote + judge' },
    { title: 'Synthesize', detail: 'aggregate into one-screen report + team recommendation' },
  ],
}

// args (from the SKILL, built by enumerate_sessions.mjs):
//   { worklistPath, since, totals, model_mix, flag_counts, sessions: [sessionId,...] }
// args may arrive as a real object or (depending on how it was passed) as a
// JSON-encoded string — handle both.
let A = args
if (typeof A === 'string') {
  try {
    A = JSON.parse(A)
  } catch {
    A = {}
  }
}
A = A || {}

// ---------------------------------------------------------------------------
// args loader (robustness) — the orchestration payload is ~18KB: per-session
// fingerprints, session_meta, by_week, and the spend ranking. Inlining that blob
// into the Workflow `args` forces the caller to hand-transcribe 18KB of JSON,
// which is genuinely error-prone — a single flipped session-id hash silently
// mis-keys the leaf cache or drops a session, and a truncated session_meta
// re-triggers the week-attribution bug. So the SKILL instead writes the jq output
// to a file and passes only a tiny { argsFile, [expectSessions], [reviewerModel] };
// there is nothing to transcribe. Workflow scripts can't touch the filesystem, so
// the first agent cat's the file back and we JSON.parse + sanity-check it here.
// (The full inline form still works for debugging / back-compat: if `sessions` is
// already present we skip the loader entirely.)
let loaderRan = false // did the args-loader agent run? (for the self-cost footer split)
async function loadArgsFromFile(path) {
  loaderRan = true
  // Haiku, not the inherited Opus: this agent just `cat`s a ~12KB file back verbatim —
  // pure I/O, zero reasoning. A skill that flags Opus-on-small-tasks must not itself
  // burn Opus to read a file.
  const raw = await agent(
    `Run exactly this command and return ONLY its stdout, verbatim — nothing else:
  cat ${path}
The file is a SINGLE LINE of compact JSON (it may be ~20KB). Return every byte exactly as cat prints
it: no commentary, no code fences, no pretty-printing, no truncation, no trailing explanation. If cat
errors (e.g. file missing), return the literal text "ERROR: " followed by the message.`,
    { label: 'load-args', phase: 'Analyze', model: 'haiku' },
  )
  if (typeof raw !== 'string') throw new Error(`args loader returned non-string for ${path}`)
  const txt = raw.trim()
  if (txt.startsWith('ERROR:')) throw new Error(`args loader could not read ${path}: ${txt}`)
  try {
    return JSON.parse(txt)
  } catch (e) {
    // tolerate a model that wrapped the line in stray prose: grab the outermost {...}
    const a = txt.indexOf('{')
    const b = txt.lastIndexOf('}')
    if (a >= 0 && b > a) {
      try {
        return JSON.parse(txt.slice(a, b + 1))
      } catch {
        /* fall through to the throw */
      }
    }
    throw new Error(`args loader returned unparseable JSON from ${path}: ${String((e && e.message) || e)}`)
  }
}

if (A.argsFile && !(Array.isArray(A.sessions) && A.sessions.length)) {
  const expectSessions = A.expectSessions
  const reviewerOverride = A.reviewerModel
  log(`Loading orchestration args from file: ${A.argsFile}`)
  const loaded = await loadArgsFromFile(A.argsFile)
  if (!loaded || typeof loaded !== 'object') throw new Error('args file did not contain a JSON object')
  if (!loaded.worklistPath) throw new Error('args file missing worklistPath')
  if (!Array.isArray(loaded.sessions) || loaded.sessions.length === 0)
    throw new Error('args file has no sessions to analyze')
  if (!loaded.totals || typeof loaded.totals.cost_usd !== 'number')
    throw new Error('args file missing totals.cost_usd')
  // Integrity cross-check: a flipped/dropped chunk most often shortens the sessions
  // array. The SKILL passes the expected count (one trivially-transcribed integer);
  // a mismatch means the file was truncated in transit — fail loud, don't analyze a
  // silently-partial window.
  if (typeof expectSessions === 'number' && loaded.sessions.length !== expectSessions)
    throw new Error(
      `args integrity check failed: expected ${expectSessions} sessions, file yielded ${loaded.sessions.length} — the args file may be truncated`,
    )
  A = loaded
  if (reviewerOverride && !A.reviewerModel) A.reviewerModel = reviewerOverride
  log(`Loaded args from file: sessions=${A.sessions.length} cost=$${A.totals.cost_usd}`)
}

const worklistPath = A.worklistPath
const sessionIds = Array.isArray(A.sessions) ? A.sessions : []
// prev: the most recent history snapshot (or null) — drives the trend line.
// runDate: today's date (workflows can't call Date.now()), passed in by the SKILL.
const prev = A.prev || null
const runDate = A.date || 'today'
// leaf cache: per-session reviewer findings persist under cacheDir keyed by
// <session>__<fingerprint>.json. Each reviewer checks its own file first and
// returns it verbatim on a hit, so no unchanged session is ever analyzed twice.
// (Workflow scripts can't touch the fs — only the agents can — so the read happens
// inside each agent; the SKILL writes fresh leaves back after the run.)
const cacheDir = A.cacheDir || ''
const fingerprints = A.fingerprints || {}
const byWeek = Array.isArray(A.by_week) ? A.by_week : []
// session_meta: id -> { week, project } for every fan-out session (from the
// enumerator). Lets the synth ground each week's narrative ONLY in the sessions
// that actually fall in that week, instead of guessing which build belongs where.
const sessionMeta = A.session_meta && typeof A.session_meta === 'object' ? A.session_meta : {}
// env: the user's real Claude Code settings that change how burn should be read —
// notably autoCompactEnabled / autoCompactWindow. The synth must not recommend
// turning on compaction the user already has on.
const env = A.env && typeof A.env === 'object' ? A.env : {}

// Mark the CURRENT ISO week as in-progress. The most recent by_week bucket is the
// week the run happens in; if only a few of its 7 days have elapsed, its cumulative
// spend is partial and NOT comparable to completed weeks — without this flag the
// synth reads the low partial total as "burn fell sharply / improving", which is an
// artifact of the week not being over. (new Date(str) is allowed in workflows; only
// argless new Date()/Date.now() are not.)
function mondayOfStr(dstr) {
  const d = new Date(`${dstr}T00:00:00Z`)
  if (isNaN(d.getTime())) return null
  const dow = (d.getUTCDay() + 6) % 7 // 0 = Monday
  const mon = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate() - dow))
  return mon.toISOString().slice(0, 10)
}
const currentWeek = mondayOfStr(runDate)
if (currentWeek) {
  for (const w of byWeek) {
    if (w.week !== currentWeek) continue
    const mon = new Date(`${currentWeek}T00:00:00Z`)
    const today = new Date(`${runDate}T00:00:00Z`)
    const elapsed = Math.round((today.getTime() - mon.getTime()) / 86400000) + 1
    w.partial = true
    w.days_elapsed = Math.max(1, Math.min(7, elapsed))
  }
}
const partialWeek = byWeek.find(w => w.partial) || null
// reviewerModel: which model the per-session fan-out runs on. Default Sonnet (the
// cost/fidelity sweet spot for constrained read+judge work). Overridable via args
// so the fan-out tier can be A/B'd (e.g. 'haiku') without editing the script.
const reviewerModel = A.reviewerModel || 'sonnet'
log(`args: type=${typeof args} worklistPath=${!!worklistPath} sessions=${sessionIds.length} prev=${!!prev} reviewer=${reviewerModel}`)

if (!worklistPath || sessionIds.length === 0) {
  log('No flagged sessions in window — nothing to analyze.')
  return {
    one_screen:
      'INSIGHTS — no sessions found in the selected window. Try a wider --since.',
    burn_analysis: { overall_verdict: 'No sessions in window.', weekly: [], sessions: [] },
    team_harness: [],
    by_week: [],
    fresh_findings: [],
  }
}

log(`Analyzing ${sessionIds.length} flagged sessions from ${worklistPath}`)

// ---------------------------------------------------------------------------
// Schemas
// ---------------------------------------------------------------------------
const SESSION_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['session', 'burn_vs_output', 'underspecified', 'opus_small', 'context_bloat', 'revivals', 'behavior_notes'],
  properties: {
    session: { type: 'string' },
    burn_vs_output: {
      type: 'object',
      additionalProperties: false,
      description:
        'SUBJECTIVE judgment of whether this session\'s spend was worth what it produced. Ground it in the session-level signals (cost_usd, span_days, output.commits/edits/files_touched/test_runs/reverts) AND the arc you read (did work land and stick, or thrash/get reverted/get abandoned? did the user signal satisfaction or frustration?).',
      required: ['cost_usd', 'roi', 'outcome', 'verdict'],
      properties: {
        cost_usd: { type: 'number', description: 'the session cost_usd from its record' },
        roi: {
          type: 'string',
          enum: ['worth-it', 'overpriced', 'wasted'],
          description: 'Was the price fair for what resulted? worth-it = the dollars bought commensurate value; overpriced = real result but cost far more than it should have; wasted = little/nothing of value for the spend. Judge value vs the $, NOT whether git changed.',
        },
        outcome: {
          type: 'string',
          enum: ['landed', 'partial', 'dropped'],
          description: 'Did durable work actually result? landed = the goal was achieved and looks like it stuck (a solved problem / merged change / answered question counts even with NO commit); partial = some achieved, much unfinished; dropped = reverted, abandoned, or superseded. NOT git-bound — a correct diagnosis whose fix lives outside the repo still landed.',
        },
        verdict: {
          type: 'string',
          description: 'ONE subjective sentence: was this spend worth the output? Name the $ and what it bought (or didn\'t).',
        },
      },
    },
    underspecified: {
      type: 'array',
      description:
        'CONFIRMED extreme-underspecified prompts — ambiguous/confusing even WITH prior transcript context (e.g. "no its still not working", "idk fix it"). Skip prompts that are clear given context.',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['quote', 'agent_response', 'ambiguity', 'tokens'],
        properties: {
          quote: { type: 'string', description: 'verbatim human prompt' },
          agent_response: {
            type: 'string',
            enum: ['asked_clarifying', 'assumed', 'wandered', 'recovered_ok'],
            description: 'how the agent reacted to the ambiguity',
          },
          ambiguity: { type: 'string', description: 'one line: why it was ambiguous even in context' },
          tokens: { type: 'number', description: 'tokens the turn consumed' },
        },
      },
    },
    opus_small: {
      type: 'array',
      description:
        'CONFIRMED small/trivial turns run on Opus that Sonnet (or Haiku) would have handled equally well — pure recall, lookups, tiny edits, yes/no, formatting. Skip turns that genuinely needed Opus reasoning.',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['quote', 'task_kind', 'out_tokens', 'cost_usd', 'cheaper_model'],
        properties: {
          quote: { type: 'string' },
          task_kind: { type: 'string', description: 'e.g. fact recall, one-line edit, lookup, yes/no' },
          out_tokens: { type: 'number' },
          cost_usd: { type: 'number' },
          cheaper_model: { type: 'string', enum: ['sonnet', 'haiku'] },
        },
      },
    },
    context_bloat: {
      type: 'array',
      description:
        'CONFIRMED context-hygiene faux pas: cache_break (a large uncached cold re-ingest, >100k tokens on one call — DESCRIBE THE SYMPTOM, do not assume the cause; read the session record\'s `compactions` count and the break\'s `post_compaction` flag to say whether it followed a compaction or, more often, a resume/idle cold re-ingest — NEVER write "never compacted" if compactions.count > 0), unfiltered large outputs pulled in whole (cat/grep/MCP without head/limit/jq), redundant re-reads of files already in context, or retry-loop thrash. Token waste, with evidence.',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['kind', 'evidence', 'est_waste_tokens'],
        properties: {
          kind: {
            type: 'string',
            enum: ['cache_break', 'unfiltered_fetch', 'reread', 'thrash'],
          },
          evidence: { type: 'string', description: 'one line, concrete (file/command/line)' },
          est_waste_tokens: { type: 'number' },
        },
      },
    },
    revivals: {
      type: 'array',
      description:
        'One entry per LARGE resume/idle cold re-ingest on this session (a cache_break with post_compaction=false and >~100k uncached tokens — a long session resumed after its 5-min prompt cache lapsed). Classify each per the `classification` enum. Skip post_compaction=true breaks (not a revive) and small re-ingests; empty array if none. Be conservative — default to unclear, never guess unjustified. See reviewer STEP 2.5 for the full judgment guidance.',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['classification', 'est_reingest_tokens', 'evidence'],
        properties: {
          classification: {
            type: 'string',
            enum: ['justified', 'unjustified', 'unclear'],
            description:
              'justified = the post-revive turns actually USED the loaded context (continued the prior thread, referenced/built on earlier work, the first prompt only makes sense given what was already in context) — the cold re-ingest bought needed continuity. unjustified = the post-revive work was a FRESH, self-contained task that did not need the old context, so re-sending days of transcript cold was avoidable. unclear = cannot tell from the data — DEFAULT to this when in doubt; never guess unjustified.',
          },
          est_reingest_tokens: {
            type: 'number',
            description: 'uncached tokens re-sent on this cold re-ingest (the cache_break `uncached` value)',
          },
          evidence: {
            type: 'string',
            description:
              'one line, concrete: what the FIRST turns after the re-ingest actually did, and why that shows the loaded context was or was not needed (e.g. "next prompt opened an unrelated new feature with no reference to the prior 3 days — context went unused").',
          },
        },
      },
    },
    behavior_notes: {
      type: 'array',
      items: { type: 'string' },
      description:
        '0-3 short notes on how the agent handled this session: wandering vs focused, tool-use effectiveness, whether it gathered org/codebase context before acting on a cross-team task.',
    },
  },
}

const SYNTH_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['one_screen', 'burn_analysis', 'team_harness'],
  properties: {
    one_screen: {
      type: 'string',
      description:
        'The FINAL report, ready to print verbatim. HARD LIMIT: <= 46 lines, and EVERY line <= 96 columns wide (count characters; wrap long sentences onto the next line before hitting 96) — a strict ceiling so it never overflows a 100-col terminal. No tables wider than the terminal. Must fit one screen with NO scrolling. Written in full, readable sentences for a human reader — NOT telegraphic fragments. Exactly two major sections, in this order: BURN vs OUTPUT (the lead) and TEAM HARNESS.',
    },
    burn_analysis: {
      type: 'object',
      additionalProperties: false,
      description:
        'The headline: was the spend worth what it produced? A subjective ledger of the top-burn sessions, a week-by-week read, plus an overall verdict.',
      required: ['overall_verdict', 'weekly', 'sessions'],
      properties: {
        overall_verdict: {
          type: 'string',
          description:
            '2-3 blunt sentences: of the total spend, roughly how much bought work that LANDED and was worth the price vs exploration / thrash / abandoned effort. MUST be week-aware — name the worst/biggest week and the trend across weeks (e.g. "churn peaked the week of May 25 then fell sharply"). Call out the single biggest burner. This is the answer to "I burned 3x budget — was it worth it?"',
        },
        weekly: {
          type: 'array',
          description:
            'One entry per week present in the by_week data (chronological), each a SHORT intelligence read of that week. The deterministic cost/efficiency split is rendered separately from by_week — your job here is the narrative: what drove that week\'s burn and whether it was worth it.',
          items: {
            type: 'object',
            additionalProperties: false,
            required: ['week', 'headline'],
            properties: {
              week: { type: 'string', description: 'the week key (YYYY-MM-DD Monday) from by_week, verbatim' },
              headline: {
                type: 'string',
                description: 'ONE sentence: what this week\'s spend went to and the efficiency read — e.g. "the $1.1k migration churn dominated; mostly thrashy but it shipped."',
              },
            },
          },
        },
        sessions: {
          type: 'array',
          description: 'the top-spend sessions, judged, highest cost first (5-7 of them).',
          items: {
            type: 'object',
            additionalProperties: false,
            required: ['session', 'cost_usd', 'roi', 'outcome', 'verdict'],
            properties: {
              session: { type: 'string', description: 'short session id (first 8 chars ok) — MUST match the id from the spend ranking so the deterministic efficiency label can be merged back in' },
              cost_usd: { type: 'number' },
              roi: { type: 'string', enum: ['worth-it', 'overpriced', 'wasted'] },
              outcome: { type: 'string', enum: ['landed', 'partial', 'dropped'] },
              verdict: { type: 'string', description: 'one blunt sentence: was this $ worth it?' },
            },
          },
        },
        revivals: {
          type: 'array',
          description:
            'OPTIONAL — ONLY the UNJUSTIFIED large resume/idle cold re-ingests flagged by the per-session reviewers (classification === "unjustified"). Each is a precise, evidence-backed cost callout naming the session and the avoidable cold-re-ingest. EXCLUDE every justified and unclear revive — a deliberate revive of a long session is NOT waste and must not appear. Omit the field (or empty array) when there are no unjustified revives; do NOT manufacture entries. This is a per-session burn-ledger callout, NOT a team_harness lever — NEVER turn it into a blanket "use /clear / don\'t revive long sessions / start fresh" rule.',
          items: {
            type: 'object',
            additionalProperties: false,
            required: ['session', 'evidence'],
            properties: {
              session: { type: 'string', description: 'short session id (first 8 chars) — match the spend ranking' },
              est_cost_usd: {
                type: 'number',
                description:
                  'approximate $ the avoidable cold re-ingest cost on this session (estimate from the re-ingest token size relative to this session\'s spend; 0 or omit if you cannot estimate)',
              },
              est_reingest_tokens: { type: 'number', description: 'uncached tokens re-sent cold' },
              evidence: {
                type: 'string',
                description: 'one line: why this revive was unjustified — what the post-revive turns did instead of using the loaded context',
              },
            },
          },
        },
      },
    },
    team_harness: {
      type: 'array',
      description:
        'Concrete, shippable harness changes that move the burn needle — each an AGENT-applicable artifact (settings.json / CLAUDE.md rule / hook / skill / script / config) the agent reads-and-obeys or that configures the runtime, written to disk with a paste-ready body. These are TEAM-WIDE, durable levers, not per-user manual habits. Do NOT emit advice the human performs by hand in the REPL (e.g. `/clear`, starting fresh sessions, not reviving long-idle ones) — that is a deliberate operator choice, not a harness change, and does not belong here.',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['artifact', 'change', 'rationale', 'target_path', 'ready_to_apply'],
        properties: {
          artifact: {
            type: 'string',
            enum: ['settings.json', 'CLAUDE.md', 'hook', 'skill', 'script', 'config'],
            description:
              'the kind of harness artifact this change lands as — all are agent/runtime-applicable and written to disk.',
          },
          change: { type: 'string', description: 'a full sentence describing the edit/addition' },
          rationale: { type: 'string', description: 'which observed pattern it fixes, in a sentence' },
          target_path: {
            type: 'string',
            description:
              'where this lands, e.g. "~/.claude/settings.json", "<repo>/CLAUDE.md", "~/.claude/hooks/precompact.sh" (~/.claude for user-global, <repo> for project-level).',
          },
          ready_to_apply: {
            type: 'string',
            description:
              'the PASTE-READY artifact — the exact text/JSON/script block to drop into target_path (a complete CLAUDE.md paragraph, a valid settings.json fragment, a runnable script); literal content, not a description; this is what the skill offers to write to disk.',
          },
        },
      },
    },
  },
}

// ---------------------------------------------------------------------------
// Phase 1 — fan out: one agent per flagged session
// ---------------------------------------------------------------------------
phase('Analyze')

function sessionPrompt(id) {
  const fp = fingerprints[id] || ''
  const cachePath = cacheDir && fp ? `${cacheDir}/${id}__${fp}.json` : ''
  return `You are an adversarial reviewer for the Claude Code \`insights\` skill, analyzing ONE session.

Session id: ${id}
Worklist (full detail, pre-flagged): ${worklistPath}
${cachePath ? `Leaf-cache path for this session: ${cachePath}` : ''}

STEP 0 — CACHE CHECK (do this FIRST).${cachePath
    ? ` Run:
  cat ${cachePath} 2>/dev/null
If the file EXISTS, is valid JSON, AND already contains every field the structured-output schema
requires (in particular a \`revivals\` array — older leaves predate it), this session is UNCHANGED since
it was last analyzed: return that exact object via the structured-output tool, unmodified, and STOP. Do
NOT re-analyze, do NOT re-judge, do NOT read the transcript. The cached leaf is authoritative. If the
file is absent, unparseable, OR missing a now-required field (a pre-version-bump leaf), treat it as a
MISS and continue to STEP 1 — do NOT return a leaf the current schema would reject.`
    : ' (No cache configured — continue to STEP 1.)'}

STEP 1 — load your slice (run via Bash):
  jq -c '.sessions[] | select(.session=="${id}")' ${worklistPath}
This gives { cost_usd, span_days, output:{commits,edits,files_touched,test_runs,reverts},
compactions:{count,auto,manual,pre_tokens_total}, cache_break_post_compaction, cache_breaks:[{line,uncached,post_compaction}],
plan:{markers,exit_calls}, opus_cost_usd, episodes:[...] }.
The session-level cost_usd / span_days / output are your grounding for the burn-vs-output judgment.
\`compactions.count\` is how many times this session ALREADY auto/manually compacted — if it is > 0 the
session did NOT "fail to compact", so never describe its cache-breaks that way. Each cache_break carries
\`post_compaction\`: true = the cold re-ingest right after a compaction; false = a resume/idle or
organic-growth cold re-ingest (the common case on long-lived sessions whose 5-min prompt cache expired).
Each flagged episode has: line (line number of the human prompt in \`file\`), flags[], full_text (the
human prompt), first_response (agent's first reply), tokens, out, api_calls, n_tool_calls, cost_usd,
cold, cache_read_ratio, reread_files, thrash, big_outputs, cache_break_lines, n_errors, primary_model.

STEP 2 — judge each flagged episode. The enumerator OVER-flags on purpose; your job is to CONFIRM
or DISCARD. Most of what you need is in full_text + first_response. Only when you need more context,
read a window of the raw transcript:
  sed -n '<line>,<line+60>p' <file>     # then eyeball the JSONL, or pipe to: jq -r '.message.content'
Do NOT read whole transcripts — they are multi-MB. Stay surgical.

Confirm only GENUINE instances:
- underspecified: prompt is ambiguous/confusing EVEN WITH the preceding turns (e.g. "no its still
  not working", "idk fix it", "same thing", bare "no"). A terse-but-clear prompt is NOT underspecified.
  Classify how the agent reacted: asked_clarifying / assumed / wandered / recovered_ok.
- opus_small: the turn ran on Opus but was trivial (fact recall, lookup, one-line edit, yes/no,
  formatting) — Sonnet/Haiku would match it. CRITICAL NUANCE: only confirm if the turn was COLD
  (check the episode's \`cold\`/\`cache_read_ratio\` fields — cold means session start / post-/compact,
  little warm cache). A trivial Opus turn MID-WARM-SESSION is NOT a faux pas: switching models there
  busts the model-specific cache and costs MORE than the Opus premium saves. Discard warm ones.
- context_bloat: cache_break (a large >100k cold re-ingest on one call). State the SYMPTOM and read
  the cause from the data — do NOT assert "never /clear'd or /compact'd": if compactions.count > 0 the
  session compacted repeatedly, and most big re-ingests are post_compaction=false (a resume/idle cold
  re-ingest on a long session whose prompt cache lapsed), not a missing-compaction problem. Your evidence
  line should reflect which it is (e.g. "137k cold re-ingest on resume; session already auto-compacted 32x").
  unfiltered_fetch (a >50k-char tool result pulled in whole), reread (same file Read >=2x in a turn).
  DO NOT count repeated \`cd /abs/path &&\` prefixes as waste — cwd resets between Bash calls, so
  re-stating cd is REQUIRED, expected harness behavior, not thrash. Ignore it entirely.
  For everything you do confirm, give concrete one-line evidence + est wasted tokens, and skip
  anything trivial in magnitude (a few thousand tokens is noise; focus on material waste).

STEP 2.5 — REVIVE CHECK (populate \`revivals\`). Separately from the cache_break waste flag above,
classify whether each LARGE resume/idle cold re-ingest on this session was WORTH it. These are the
cache_breaks with post_compaction=false and a big \`uncached\` re-ingest (>~100k tokens): the session was
resumed after its 5-min prompt cache lapsed and re-sent its whole context cold at full input price.
Reviving a long-lived, multi-day session is usually a DELIBERATE, correct choice to reuse accumulated
context — so a big resume re-ingest is NOT automatically waste. For each such break, read the turns
IMMEDIATELY AFTER the re-ingest and judge:
- justified: those turns actually USED the loaded context (continued the prior thread, referenced or
  built on earlier work, the first prompt only makes sense given what was already in context).
- unjustified: the post-revive work was a FRESH, self-contained task that did not need the old context,
  so re-sending days of transcript cold was avoidable. REQUIRES concrete evidence the context went unused.
- unclear: you cannot tell from the data. DEFAULT to this when in doubt — do NOT guess unjustified.
Be conservative: a wrong "unjustified" wrongly scolds a deliberate, correct revive, so most calls should
be justified or unclear. post_compaction=true breaks are NOT revives — skip them here. Empty \`revivals\`
if the session had no large resume/idle re-ingest.

STEP 3 — judge BURN vs OUTPUT for this session (the headline question). Using the session-level
cost_usd, span_days, and output signals (commits / edits / files_touched / test_runs / reverts) PLUS
the arc you read, judge two ORTHOGONAL dimensions — they often disagree, and that's the point:
- roi: worth-it (dollars bought commensurate value) / overpriced (real result, but cost far more
  than it should have) / wasted (little or nothing of value for the spend). Price vs value — NOT
  whether git changed. A $41 session that only concluded "ask infra for a route" is overpriced even
  though the problem got solved.
- outcome: landed (goal achieved and looks like it stuck — a SOLVED PROBLEM, merged change, or
  answered question counts even with ZERO commits) / partial / dropped (reverted, abandoned,
  superseded). Not git-bound: a correct diagnosis whose fix lives outside the repo still landed.
  COMMIT COUNT IS NOISY — work is often committed in a DIFFERENT session, or by the human by hand,
  or squashed later. NEVER infer "dropped" / "un-anchored" / "only in the working tree" from a low
  or zero commit count. Judge landing from whether the work was COMPLETED and looked correct in the
  arc you read (edits that stuck, tests passing, the user moving on satisfied), not from commits.
- verdict: ONE blunt sentence naming the $ and what it bought (or didn't). Be willing to say a
  session was not worth it. Use judgment, not a formula — these two can and should diverge (e.g.
  landed but overpriced for an expensive, dead-simple conclusion).

(A third dimension — efficiency: lean / loose / thrashy — is NOT yours to judge. It is computed
deterministically from the revert/reread/thrash/cache-break signals and merged in after synthesis, so
don't emit it; just focus on the value call above. Note: reverts are split into STUCK reverts —
undoing work mid-flail, real churn — vs PIVOT reverts — a clean, deliberate change of direction, which
is HEALTHY iteration and is NOT counted as waste. When you describe a session, do NOT treat discarding
an explored idea as a problem; only repeated undoing-while-stuck is.)

Quote prompts VERBATIM. Be conservative on the flags — a false positive is worse than a miss — but be
DECISIVE on the burn-vs-output verdict. Return per the schema.`
}

// Reviewers run on Sonnet by default (overridable via args.reviewerModel): this is
// high-volume, constrained read+judge work (load a jq slice, confirm/discard pre-flags,
// quote verbatim). Keeping the fan-out off Opus is the whole cost game — and on-brand
// for a skill that flags Opus-on-small-tasks. Synthesis below inherits the stronger model.
const findings = (
  await parallel(
    sessionIds.map(id => () =>
      agent(sessionPrompt(id), {
        label: `analyze:${id.slice(0, 8)}`,
        phase: 'Analyze',
        schema: SESSION_SCHEMA,
        model: reviewerModel,
      }),
    ),
  )
).filter(Boolean)

// roll up confirmed counts for the synthesis prompt (and as a deterministic backstop)
const roll = { underspecified: 0, opus_small: 0, context_bloat: 0, revivals_unjustified: 0 }
for (const f of findings) {
  roll.underspecified += (f.underspecified || []).length
  roll.opus_small += (f.opus_small || []).length
  roll.context_bloat += (f.context_bloat || []).length
  roll.revivals_unjustified += (f.revivals || []).filter(r => r && r.classification === 'unjustified').length
}
log(
  `Confirmed → underspecified:${roll.underspecified} opus_small:${roll.opus_small} context_bloat:${roll.context_bloat} unjustified-revives:${roll.revivals_unjustified}`,
)

// Tag each finding with its ISO week + project (deterministic, from the enumerator)
// so the weekly narrative is grounded ONLY in sessions that actually fall in a week
// — without this the synth guesses which build belongs to which week.
function projBasename(p) {
  if (!p) return ''
  const parts = String(p).split('-').filter(Boolean)
  return parts.length ? parts.slice(-3).join('-') : String(p)
}
for (const f of findings) {
  const m = sessionMeta[f.session]
  f.week = m ? m.week : null
  f.project = m ? m.project : null
}

// ---------------------------------------------------------------------------
// Phase 2 — synthesize (barrier: needs ALL findings together)
// ---------------------------------------------------------------------------
phase('Synthesize')

const t = A.totals || {}
const mm = A.model_mix || {}
const opusShare =
  mm.opus && (mm.opus.in || mm.opus.out)
    ? Math.round(
        (100 * ((mm.opus.in || 0) + (mm.opus.out || 0))) /
          (Object.values(mm).reduce((a, m) => a + (m.in || 0) + (m.out || 0), 0) || 1),
      )
    : 0

const spendRank = Array.isArray(A.sessions_by_spend) ? A.sessions_by_spend : []

// Per-week digest: the reviewed sessions that ACTUALLY fall in each week, carrying
// the reviewer's own verdict + project. The synth must write each weekly headline
// strictly from this — it is what stops it from crediting, say, the deep-insights
// build to a week it didn't happen in. Cost comes from the spend ranking when ranked.
const costById = {}
for (const r of spendRank) if (r.session) costById[r.session] = r.cost_usd
const weekDigest = byWeek.map(w => ({
  week: w.week,
  cost_usd: w.cost_usd,
  efficiency_cost: w.efficiency_cost,
  sessions: findings
    .filter(f => f.week === w.week)
    .map(f => ({
      id: String(f.session).slice(0, 8),
      project: projBasename(f.project),
      cost_usd: costById[f.session] || null,
      roi: f.burn_vs_output && f.burn_vs_output.roi,
      outcome: f.burn_vs_output && f.burn_vs_output.outcome,
      verdict: f.burn_vs_output && f.burn_vs_output.verdict,
    }))
    .sort((a, b) => (b.cost_usd || 0) - (a.cost_usd || 0)),
}))

// Environment + MEASURED compaction reality. The cache_break burn is widely mis-diagnosed
// as "never compacted"; the enumerator now counts actual compactions and tags each
// cache_break as post-compaction or not, so the synth can state the true cause.
const acOn = env.autoCompactEnabled === true || env.autoCompactEnabled === 'true'
const acWin = env.autoCompactWindow || env.autoCompactTokens || null
const comp = (A.totals && A.totals.compaction) || {}
const compEvents = comp.events || 0
const compAuto = comp.auto || 0
const cbPost = comp.cache_breaks_post || 0
const cbTotal = comp.cache_breaks_total || 0
const resumeShare = cbTotal ? Math.round((100 * (cbTotal - cbPost)) / cbTotal) : 0
const compactionCtx = `COMPACTION REALITY (MEASURED — do not contradict it). Across this window the
sessions compacted ${compEvents} time(s) (${compAuto} automatic). Of ${cbTotal} large cold re-ingests
("cache breaks"), only ${cbPost} immediately followed a compaction — the other ${cbTotal - cbPost}
(~${resumeShare}%) are RESUME/IDLE cold re-ingests: a long-lived session whose Anthropic prompt cache
lapsed (5-min TTL) and re-sent its whole context cold at full input price. THEREFORE:
- NEVER say a session "was never compacted" / "never /clear'd or /compact'd" when ${compEvents} > 0.
- The cache_break burn is NOT a missing-compaction problem and NOT fixed by compacting more (compaction
  itself busts the cache). It is resume/idle cold re-ingest on long-lived sessions whose 5-min prompt
  cache lapsed.
- This is a COST OBSERVATION, not necessarily waste, and NOT a team_harness recommendation. Reviving a
  multi-day session is frequently a DELIBERATE, correct choice — the human needed that accumulated
  context, and the cold re-ingest is the price of the continuity they wanted, not a mistake. The
  per-session reviewers separately classified each large resume/idle re-ingest as justified / unjustified
  / unclear by reading the turns that followed it; their findings carry a \`revivals\` array. A revive is
  waste ONLY when a reviewer marked it \`unjustified\` with evidence the loaded context went unused. So:
  surface ONLY those unjustified revives, as a precise per-session burn-ledger callout naming the session
  and the avoidable $ (burn_analysis.revivals) — exclude every justified/unclear one. Do NOT generalize
  even an unjustified revive into a "use /clear / don't revive long sessions / start fresh" rule: that is
  a per-user manual habit and a deliberate operator call, never a shippable harness lever, and it stays
  out of team_harness. ${
    acOn
      ? `Autocompaction is ALREADY ON${acWin ? ` at a ${acWin}-token window` : ''} — do NOT recommend enabling it or "adding an auto-compact hook".`
      : `(Autocompaction status unknown — but enabling it would NOT address resume cold re-ingest, so don't lead with it.)`
  }`
const envCtx = compactionCtx

// opusplan candidate: `opusplan` runs Opus ONLY in plan mode and Sonnet otherwise.
// Its win = Opus spend on non-planning execution that Sonnet would handle; its cost =
// hard reasoning turns also dropping to Sonnet, plus a model-cache bust on each plan↔
// execute switch. Give the synth the measured signals and let it judge, conditionally.
const op = (A.totals && A.totals.opusplan) || {}
const opCost = op.opus_cost_usd || 0
const totalCost = (A.totals && A.totals.cost_usd) || 0
// Cost-weighted Opus share. Keep this distinct from `opusShare`, which is the
// token-volume share above.
const opusSpendSharePct = totalCost ? Math.round((100 * opCost) / totalCost) : 0
const opusplanCtx = `OPUSPLAN CANDIDATE (MEASURED). Opus accounted for ≈$${opCost} (~${opusSpendSharePct}% of spend)
across ${op.opus_episodes || 0} turns. Plan mode was used in ${op.sessions_using_plan || 0} session(s)
(${op.plan_markers || 0} plan-mode markers, ${op.exit_plan_calls || 0} plans presented). The \`opusplan\`
model setting keeps Opus ONLY while in plan mode and uses Sonnet for everything else. Consider
recommending it in team_harness IFF the data supports it: a high Opus share spent largely on EXECUTION
(edits/lookups/tool-running rather than hard reasoning) is the win — but be honest about the trade-off
(non-plan reasoning also drops to Sonnet, and each plan↔execute switch busts the model cache). If plan
mode is barely used, frame it as "default to Sonnet, escalate to Opus via plan mode for hard design
work", not as a free win. Do NOT recommend it if Opus spend is mostly genuine deep reasoning.`

const prevUsesSpendShare =
  prev && typeof prev.opus_token_share_pct === 'number' && typeof prev.opus_share_pct === 'number'
const trendInstruction = prevUsesSpendShare
  ? 'Compute deltas vs now (spend, Opus $ share, confirmed flag totals)'
  : 'Compute deltas vs now (spend and confirmed flag totals only; do NOT delta Opus share because older snapshots stored token share in opus_share_pct, while this run stores $ share)'
const trendCtx = prev
  ? `PREVIOUS RUN SNAPSHOT (for trend line): ${JSON.stringify(prev)}
${trendInstruction} and lead the header with a short
TREND fragment, e.g. "spend ↓18%${prevUsesSpendShare ? ' · Opus $ share ↓6pts' : ''} vs ${prev.date || 'last run'}". Use ↑/↓/= and be honest.`
  : `No previous snapshot exists — this is the FIRST recorded run. Do NOT fabricate a trend; instead
end the header with "(baseline run — trend starts next time)".`

// Embed the per-session findings, biggest spenders first, so if we hit the context budget the
// drop falls on the cheapest tail — and is NEVER silent: dropped sessions are named so the synth
// knows they exist (their burn is still in the deterministic totals/week-digest/spend-rank above).
const FINDINGS_BUDGET = 120000
const findingsByCost = [...findings].sort((a, b) => (costById[b.session] || 0) - (costById[a.session] || 0))
const keptFindings = []
const droppedFindings = []
let findingsUsed = 2 // enclosing []
for (const f of findingsByCost) {
  const s = JSON.stringify(f)
  if (findingsUsed + s.length + 1 <= FINDINGS_BUDGET) { keptFindings.push(f); findingsUsed += s.length + 1 }
  else droppedFindings.push(String(f.session).slice(0, 8))
}
const findingsBlock = JSON.stringify(keptFindings) + (droppedFindings.length
  ? `\n[TRUNCATED: ${droppedFindings.length} lower-cost session findings omitted to fit context — ${droppedFindings.join(', ')}. Their spend is still fully counted in the deterministic totals, week digest, and spend ranking above; treat them as analyzed-from-aggregates, NOT missing.]`
  : '')
if (droppedFindings.length) log(`synth: findings JSON over ${FINDINGS_BUDGET}c — embedded ${keptFindings.length}, summarized ${droppedFindings.length} cheapest by reference`)

const synthPrompt = `You are the synthesis stage of the \`insights\` skill. Below are per-session findings
(JSON) from ${findings.length} analyzed Claude Code sessions, plus deterministic totals.

DETERMINISTIC TOTALS (window since ${A.since || 'all'}):
- sessions: ${t.sessions}, prompts: ${t.prompts}
- tokens in/out: ${t.in} / ${t.out}, cache-read: ${t.cache_read_pct}%
- est spend: ≈$${t.cost_usd}
- model spend mix: ${JSON.stringify(mm)}  (Opus ≈ ${opusSpendSharePct}% of SPEND / ${opusShare}% of tokens — lead with the $ figure; do NOT conflate the two or write "tokens/spend")
- enumerator pre-flags: ${JSON.stringify(A.flag_counts || {})}
- confirmed by reviewers: ${JSON.stringify(roll)}

WEEK-BY-WEEK BURN (deterministic — cost split by efficiency label per ISO week, Monday-keyed). This
is the spine of the report: the skill is week-oriented. Read the trend across weeks (where did burn
and churn peak? is it improving?) and reflect it in overall_verdict AND one weekly[] entry per week:
${JSON.stringify(byWeek)}
${
  partialWeek
    ? `IMPORTANT — the most recent week (${partialWeek.week}) is the CURRENT, IN-PROGRESS week: only
${partialWeek.days_elapsed} of 7 days have elapsed, so its $${partialWeek.cost_usd} is a PARTIAL total,
NOT comparable to the completed weeks. Do NOT say burn "fell sharply", "collapsed", or is "improving"
based on this week — that is an artifact of the week not being over. In its weekly[] headline and in
overall_verdict, label it in-progress / too early to call; if you want a comparison, use a daily
run-rate (its spend ÷ ${partialWeek.days_elapsed} days vs a prior week ÷ 7), not the raw total. Draw
trend conclusions only across the COMPLETED weeks.`
    : ''
}

WEEK DIGEST (deterministic — which REVIEWED sessions actually fall in each week, with the reviewer's
own project + verdict). This is the ONLY valid basis for a week's narrative. When you write a
weekly[] headline, name only the work in THAT week's \`sessions\` list — do NOT attribute a project,
build, or topic (e.g. "the X build", "the Y migration") to a week unless a session in its bucket
supports it. A week with no notable sessions just gets a terse efficiency read. Sessions are keyed by
short id and carry project basename + roi/outcome + the reviewer's verdict:
${JSON.stringify(weekDigest)}

${envCtx}

${opusplanCtx}

TOP SESSIONS BY SPEND (deterministic — cost_usd, prompts, span_days, work-output signals
commits/edits/files_touched/test_runs/reverts, week, and a precomputed efficiency label
lean/loose/thrashy with its signals). This is where the money went; the single biggest entry may
dominate the window. The \`efficiency\` field here is AUTHORITATIVE — it is computed from the churn
signals, not judged. Do NOT emit efficiency yourself; just reference this label per session. In
efficiency_signals, \`reverts_stuck\` = undoing work mid-flail (real churn, what the label penalizes)
and \`reverts_pivot\` = deliberate changes of direction (HEALTHY iteration, weighted 0): a session
with mostly pivot reverts is exploring well, NOT thrashing — describe it that way:
${JSON.stringify(spendRank)}

${trendCtx}

PER-SESSION FINDINGS (each includes the reviewer's burn_vs_output verdict; biggest spenders first):
${findingsBlock}

Produce the report per schema. The report has exactly TWO major sections, in order: BURN vs OUTPUT
(the lead) and TEAM HARNESS. Write for a human reader in full, readable sentences — not fragments.

MATERIALITY — only surface what matters. A few thousand wasted tokens is noise. NEVER flag repeated
\`cd /abs/path &&\` prefixes (cwd resets between Bash calls, so re-stating cd is required, not waste).
Do NOT include low-ROI developer micro-habits (e.g. "use Sonnet for a $0.80 question") — those are
rounding errors against the burn picture and the user has explicitly dismissed them.

COMMIT COUNT IS A NOISY SIGNAL — do NOT penalize a session or call work "un-anchored / only in the
working tree / dropped" because commits == 0. Work is routinely committed in a DIFFERENT session, by
the human by hand, or squashed later, so zero commits does NOT mean nothing landed. Judge outcome
from whether the work was completed and stuck in the arc, never from the commit count alone; do not
write commit-discipline recommendations or verdicts that assume commits track landing.

1. burn_analysis — THE HEADLINE. The user burned ~3x their expected budget and wants to know if it
   was worth it. Produce:
   - sessions: the top-spend sessions (highest cost first), each judged on roi (worth-it / overpriced
     / wasted) and outcome (landed / partial / dropped) with a blunt one-sentence verdict naming the
     $ and what it bought (or didn't). These two are ORTHOGONAL — let them diverge (e.g. landed but
     overpriced). Use the spend ranking for cost/output signals and the per-session findings for the
     subjective read. For a session in the spend ranking but NOT in the findings, judge from the
     deterministic signals alone (commits/tests/reverts/span) and keep the verdict signal-based.
     Do NOT emit an efficiency field — it is merged in deterministically after you finish. Use the
     spend ranking's session ids verbatim so that merge lands.
   - weekly: ONE entry per week in the by_week data above (chronological), each a single-sentence
     intelligence read of what that week's spend went to and whether it was efficient. Ground it
     STRICTLY in that week's entry in the WEEK DIGEST — the sessions listed there are the only work
     that happened that week. Do NOT name a project/build/topic for a week unless a session in that
     week's digest bucket supports it (no cross-week attribution, no guessing from salience). A week
     with no notable sessions gets a terse cost + efficiency read, nothing invented.
   - overall_verdict: 2-3 blunt sentences — of ≈$${t.cost_usd}, roughly how much bought work that
     LANDED and was worth the price vs exploration / thrash / abandoned effort. Be WEEK-AWARE: name
     the peak-burn / peak-churn week and the trend across weeks, and call out the biggest burner by
     name. Be honest, even unflattering. This is the answer to "was the 3x worth it?"
   - revivals: scan the per-session findings for \`revivals\` entries and surface ONLY the ones the
     reviewer marked \`unjustified\`. For each, emit a precise callout: the session id, the approximate
     avoidable $ (derive from the re-ingest token size relative to that session's spend), the re-ingest
     token size, and the one-line evidence. EXCLUDE every \`justified\` and \`unclear\` revive — a
     deliberate revive of a long session is the price of needed continuity, NOT waste, and must not be
     listed. If there are no unjustified revives, omit the field entirely (do not invent any). This is a
     per-session cost callout for the burn ledger ONLY — it is NOT a team_harness recommendation and must
     NEVER be generalized into a "use /clear / start fresh / don't revive" rule.

2. team_harness — 3-5 CONCRETE, shippable harness changes (settings.json / CLAUDE.md / hook / skill /
   script / config) that move the BURN needle (not micro-habits): gather org context up-front, reduce
   STUCK churn, right-size the model. Each a full sentence naming the artifact and the exact change,
   grounded in an observed pattern, with a real target_path and a literal, paste-ready ready_to_apply
   block (not a description). The biggest lever is a TEAM-WIDE, durable harness change — something
   written to disk once that every future session inherits — NOT a per-user manual habit. At least one
   item must address gathering org/codebase context up-front (a Glean-first rule for cross-team tasks).
   DO NOT recommend "plan before editing" or "reduce reverts" as a blanket rule — reverts split into
   STUCK (wall-banging, real waste) and PIVOT (a deliberate change of mind, HEALTHY). reverts_stuck is
   the only revert signal that justifies a harness change; a high reverts_pivot count is exploration
   working as intended and must NOT be framed as a problem or trigger a plan-gating recommendation. If
   the OPUSPLAN CANDIDATE data supports it (high Opus share spent on execution, not deep reasoning), you
   MAY include an opusplan recommendation — with its trade-off stated — but don't force it.

   DO NOT emit per-user session-hygiene advice as a recommendation — \`/clear\`, \`/compact\`, "start a
   fresh session", "don't revive long-idle sessions", "shorter-lived sessions". The agent cannot run
   those (they are REPL-only human actions), AND reviving a long session is frequently a DELIBERATE,
   correct choice to reuse needed context — so dressing it up as a fixable harness change is wrong on
   both counts. Per the COMPACTION REALITY block, resume/idle cold re-ingest is a cost observation for
   the burn narrative, not a team_harness item; and NEVER recommend "enable autocompaction" or "compact
   more". Every team_harness item must be a real artifact written to a real target_path; if you cannot
   express a lever as a disk-written artifact, it does not belong in team_harness.

3. one_screen — assemble the FINAL report, ready to print verbatim. HARD CONSTRAINTS:
   - <= 46 lines total, and EVERY line <= 96 columns (hard ceiling — wrap before 96 so it never
     overflows a 100-col terminal). MUST fit one terminal screen, NO scrolling.
     (The skill appends a 1-line self-cost footer after this, so stay at or under 46.)
   - Structure:
       a 1-2 line header with the window, total spend, Opus $ share (the ${opusSpendSharePct}% of SPEND figure,
         labeled "Opus $ share" — not the token share), and the TREND fragment above
       BURN vs OUTPUT — the overall verdict (1-2 lines), then a WEEK-BY-WEEK line per week
         ("wk MM-DD: $X · <one-phrase read>"; mark the in-progress current week, e.g.
         "wk MM-DD: $X (in progress, day N/7) · too early to call"), then the top-spend sessions as a compact readable
         ledger: one line each with $ + roi/outcome + the deterministic efficiency label
         (lean/loose/thrashy) from the spend ranking + the verdict
       then, ONLY IF burn_analysis.revivals is non-empty, an "AVOIDABLE REVIVES" callout: one line per
         unjustified revive (session + ≈$ + the one-line evidence), <=96 cols. Omit this block entirely
         when there are none — do NOT add a "no avoidable revives" line, and never a /clear suggestion.
       TEAM HARNESS — the harness changes as readable sentences, one per recommendation
   - Lead with the spend reality and name the biggest burner. Be specific, not generic. Ledger lines
     may be tight but must stay readable and <= 96 cols.
   - Count your lines. If over 46, trim the ledger to the top sessions until it fits.
   - Do NOT add a self-cost footer yourself — the skill appends it.`

const synthesis = await agent(synthPrompt, {
  label: 'synthesize',
  phase: 'Synthesize',
  schema: SYNTH_SCHEMA,
})

// Merge the DETERMINISTIC efficiency label (computed by the enumerator) onto each
// ledger session — the reviewers and synth deliberately don't judge it. Match on
// the spend ranking's ids, tolerating the synth's short (first-8-char) form.
const effByPrefix = {}
for (const r of spendRank) {
  if (!r.session || !r.efficiency) continue
  effByPrefix[r.session] = r.efficiency
  effByPrefix[String(r.session).slice(0, 8)] = r.efficiency
}
function lookupEfficiency(id) {
  if (!id) return 'unknown'
  const s = String(id)
  return effByPrefix[s] || effByPrefix[s.slice(0, 8)] || 'unknown'
}
if (synthesis && synthesis.burn_analysis && Array.isArray(synthesis.burn_analysis.sessions)) {
  for (const s of synthesis.burn_analysis.sessions) {
    s.efficiency = lookupEfficiency(s.session)
  }
}

// Deterministic snapshot for the trend baseline — the SKILL appends this line to
// the history file (~/.claude/deep-insights/history.jsonl) after the run. Built in JS
// (not by the model) so the numbers are exact and comparable across runs.
// opus_share_pct is the $ SHARE (opus_cost_usd / total cost_usd), not token volume —
// the honest "how much money went to Opus" number. opus_token_share_pct is kept
// alongside for context, clearly distinguished.
const snapshot = {
  date: runDate,
  since: A.since || 'all',
  sessions: t.sessions || 0,
  prompts: t.prompts || 0,
  cost_usd: t.cost_usd || 0,
  opus_share_pct: opusSpendSharePct,
  opus_token_share_pct: opusShare,
  cache_read_pct: t.cache_read_pct || 0,
  flag_counts: A.flag_counts || {},
  confirmed: roll,
}

return {
  ...(synthesis || {
    one_screen: 'INSIGHTS — synthesis failed; see raw findings.',
    burn_analysis: { overall_verdict: 'Synthesis failed.', weekly: [], sessions: [] },
    team_harness: [],
  }),
  by_week: byWeek,
  // the leaves to persist — every per-session finding (cache hits returned verbatim
  // by their reviewer + freshly analyzed misses). The SKILL writes these to
  // cacheDir/<session>__<fingerprint>.json so the next run reuses them.
  fresh_findings: findings,
  snapshot,
  // cost_basis: the agent/model split this script KNOWS, so the SKILL's self-cost
  // footer is reproducible instead of a freehand guess. The harness exposes only a
  // single `subagent_tokens` total (no per-model split), so the SKILL still estimates
  // ≈cost from that with an explicit blended rate — but the composition below is exact.
  cost_basis: {
    reviewers: { model: reviewerModel, count: sessionIds.length },
    synth: { model: 'opus (inherited)', count: 1 },
    loader: { model: 'haiku', count: loaderRan ? 1 : 0 },
  },
}
