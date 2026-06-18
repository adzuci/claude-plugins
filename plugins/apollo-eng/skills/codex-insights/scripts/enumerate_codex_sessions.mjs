#!/usr/bin/env node
/* eslint-disable no-console */

import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { execFileSync } from 'node:child_process'

const argv = process.argv.slice(2)
const valueFlag = (name, dflt = null) => {
  const i = argv.indexOf(name)
  if (i === -1) return dflt
  const v = argv[i + 1]
  return v === undefined || v.startsWith('--') ? dflt : v
}

const HOME = os.homedir()
const CODEX_HOME = process.env.CODEX_HOME || path.join(HOME, '.codex')
const OUTDIR = valueFlag('--outdir', '/tmp/codex-insights')
const SINCE_RAW = valueFlag('--since', '7d')
const SESSION_LIMIT = Number.parseInt(valueFlag('--sessions', '20'), 10) || 20
const SINCE = parseSince(SINCE_RAW)

fs.mkdirSync(OUTDIR, { recursive: true })

function parseSince(raw) {
  if (!raw || raw === 'all') return null
  const m = /^(\d+)([hd])$/.exec(String(raw))
  if (m) {
    const n = Number.parseInt(m[1], 10)
    return new Date(Date.now() - n * (m[2] === 'h' ? 3600000 : 86400000))
  }
  const d = new Date(raw)
  return Number.isNaN(d.getTime()) ? null : d
}

function walk(dir) {
  const out = []
  try {
    for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
      const p = path.join(dir, ent.name)
      if (ent.isDirectory()) out.push(...walk(p))
      else if (ent.isFile() && ent.name.endsWith('.jsonl')) out.push(p)
    }
  } catch {
    // ignored; missing source dirs are recorded in the ledger
  }
  return out
}

function readSessionIndex() {
  const idx = new Map()
  const p = path.join(CODEX_HOME, 'session_index.jsonl')
  try {
    for (const line of fs.readFileSync(p, 'utf8').split(/\n/)) {
      if (!line.trim()) continue
      const obj = JSON.parse(line)
      if (obj.id) idx.set(obj.id, obj.thread_name || obj.name || obj.id)
    }
  } catch {
    // optional source
  }
  return idx
}

function extractId(file) {
  const m = file.match(/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i)
  return m ? m[0] : path.basename(file, '.jsonl')
}

function parseOriginalTokenCount(output) {
  if (typeof output !== 'string') return 0
  const m = output.match(/Original token count:\s*([0-9]+)/)
  return m ? Number.parseInt(m[1], 10) : 0
}

function addTool(tools, name) {
  if (!name) return
  tools[name] = (tools[name] || 0) + 1
}

function parseRollout(file, index) {
  const id = extractId(file)
  const stat = fs.statSync(file)
  const rec = {
    id,
    file,
    thread_name: index.get(id) || id,
    cwd: '',
    model: '',
    first_ts: null,
    last_ts: null,
    completed: false,
    final_message: '',
    token_events: 0,
    tool_calls: 0,
    tool_outputs: 0,
    tool_output_tokens: 0,
    high_output_events: 0,
    tools: {},
    errors: 0,
    token_history: [],
    total_token_usage: null,
    last_token_usage: null,
    model_context_window: null,
    mtime: stat.mtime.toISOString(),
  }

  const lines = fs.readFileSync(file, 'utf8').split(/\n/)
  for (const line of lines) {
    if (!line.trim()) continue
    let obj
    try {
      obj = JSON.parse(line)
    } catch {
      rec.errors += 1
      continue
    }
    const ts = obj.timestamp || obj.time || obj.created_at
    if (ts) {
      rec.first_ts = rec.first_ts || ts
      rec.last_ts = ts
    }

    if (obj.type === 'session_meta' || obj.type === 'session_meta_payload') {
      const p = obj.payload || obj
      rec.cwd = rec.cwd || p.cwd || p.workdir || ''
      rec.model = rec.model || p.model || ''
      if (p.id && p.id !== id) rec.id = p.id
    }

    const payload = obj.payload || {}
    if (payload.cwd || payload.workdir) rec.cwd = rec.cwd || payload.cwd || payload.workdir
    if (payload.model) rec.model = rec.model || payload.model

    if (obj.type === 'event_msg' && payload.type === 'token_count') {
      rec.token_events += 1
      const info = payload.info || {}
      rec.total_token_usage = info.total_token_usage || rec.total_token_usage
      rec.last_token_usage = info.last_token_usage || rec.last_token_usage
      rec.model_context_window = info.model_context_window || rec.model_context_window
      const usage = info.total_token_usage || {}
      rec.token_history.push({
        ts,
        total_tokens: Number(usage.total_tokens || 0),
        input_tokens: Number(usage.input_tokens || 0),
        cached_input_tokens: Number(usage.cached_input_tokens || 0),
        output_tokens: Number(usage.output_tokens || 0),
        reasoning_output_tokens: Number(usage.reasoning_output_tokens || 0),
      })
    }

    if (obj.type === 'event_msg' && payload.type === 'task_complete') {
      rec.completed = true
      rec.final_message = payload.last_agent_message || ''
    }

    if (obj.type === 'response_item' && payload.type === 'function_call') {
      rec.tool_calls += 1
      addTool(rec.tools, payload.name)
    }

    if (obj.type === 'response_item' && payload.type === 'function_call_output') {
      rec.tool_outputs += 1
      const count = parseOriginalTokenCount(payload.output)
      rec.tool_output_tokens += count
      if (count >= 5000) rec.high_output_events += 1
    }
  }

  const total = rec.total_token_usage || {}
  const last = rec.last_token_usage || {}
  rec.lifetime_total_tokens = Number(total.total_tokens || 0)
  rec.lifetime_input_tokens = Number(total.input_tokens || 0)
  rec.lifetime_cached_input_tokens = Number(total.cached_input_tokens || 0)
  rec.lifetime_output_tokens = Number(total.output_tokens || 0)
  rec.lifetime_reasoning_output_tokens = Number(total.reasoning_output_tokens || 0)
  rec.total_tokens = rec.lifetime_total_tokens
  rec.input_tokens = rec.lifetime_input_tokens
  rec.cached_input_tokens = rec.lifetime_cached_input_tokens
  rec.output_tokens = rec.lifetime_output_tokens
  rec.reasoning_output_tokens = rec.lifetime_reasoning_output_tokens
  rec.last_input_tokens = Number(last.input_tokens || 0)
  rec.last_total_tokens = Number(last.total_tokens || 0)
  rec.span_hours = spanHours(rec.first_ts, rec.last_ts)
  rec.context_ratio = rec.model_context_window ? rec.last_input_tokens / rec.model_context_window : null
  rec.flags = flagsFor(rec)
  return rec
}

function applyWindowDelta(rec, since) {
  if (!since || !Array.isArray(rec.token_history) || rec.token_history.length === 0) {
    rec.window_basis = since ? 'lifetime_no_token_history' : 'lifetime_all'
    return rec
  }
  const events = rec.token_history
    .filter(e => e.ts && !Number.isNaN(new Date(e.ts).getTime()))
    .sort((a, b) => new Date(a.ts) - new Date(b.ts))
  const after = events.filter(e => new Date(e.ts) >= since)
  if (after.length === 0) return null
  const before = [...events].reverse().find(e => new Date(e.ts) < since)
  const last = after[after.length - 1]
  const base = before || { total_tokens: 0, input_tokens: 0, cached_input_tokens: 0, output_tokens: 0, reasoning_output_tokens: 0 }
  for (const key of ['total_tokens', 'input_tokens', 'cached_input_tokens', 'output_tokens', 'reasoning_output_tokens']) {
    rec[key] = Math.max(0, Number(last[key] || 0) - Number(base[key] || 0))
  }
  rec.window_basis = before ? 'delta_from_prior_token_count' : 'session_started_in_window'
  rec.window_start_event = after[0].ts
  rec.window_end_event = last.ts
  rec.flags = flagsFor(rec)
  return rec
}

function spanHours(a, b) {
  if (!a || !b) return 0
  const start = new Date(a).getTime()
  const end = new Date(b).getTime()
  if (!Number.isFinite(start) || !Number.isFinite(end) || end < start) return 0
  return (end - start) / 3600000
}

function flagsFor(s) {
  const flags = []
  if (s.last_input_tokens >= 100000 || (s.context_ratio || 0) >= 0.5) {
    flags.push({ key: 'context_load', label: 'large context load', detail: `${fmt(s.last_input_tokens)} input tokens in the latest turn` })
  }
  if (s.reasoning_output_tokens >= 20000) {
    flags.push({ key: 'reasoning_burn', label: 'high reasoning output', detail: `${fmt(s.reasoning_output_tokens)} reasoning tokens` })
  }
  if (s.span_hours >= 48) {
    flags.push({ key: 'long_session', label: 'long or resumed session', detail: `${s.span_hours.toFixed(1)} hours between first and last event` })
  }
  if (s.high_output_events > 0) {
    flags.push({ key: 'large_tool_output', label: 'large tool output', detail: `${s.high_output_events} tool outputs over 5k tokens` })
  }
  const topToolCount = Math.max(0, ...Object.values(s.tools))
  if (topToolCount >= 12) {
    const top = Object.entries(s.tools).sort((a, b) => b[1] - a[1])[0]
    flags.push({ key: 'repeated_tooling', label: 'repeated tool loop', detail: `${top[0]} called ${top[1]} times` })
  }
  return flags
}

function fmt(n) {
  if (!n) return '0'
  if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`
  if (n >= 1000) return `${Math.round(n / 1000)}k`
  return String(n)
}

function runOptional(cmd, args) {
  try {
    const stdout = execFileSync(cmd, args, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], timeout: 20000 })
    return { ok: true, json: safeJSON(stdout), raw_chars: stdout.length }
  } catch (e) {
    return { ok: false, error: String(e.stderr || e.message || e).slice(0, 500) }
  }
}

function safeJSON(txt) {
  try {
    return JSON.parse(txt)
  } catch {
    return null
  }
}

function summarizeConfig() {
  const p = path.join(CODEX_HOME, 'config.toml')
  const text = fs.existsSync(p) ? fs.readFileSync(p, 'utf8') : ''
  const mcp = [...text.matchAll(/^\[mcp_servers\.([^\]\s]+)\]/gm)].map(m => m[1].replace(/^"|"$/g, ''))
  const plugins = [...text.matchAll(/^\[plugins\.([^\]]+)\]/gm)].map(m => m[1].replace(/^"|"$/g, ''))
  return {
    config_path: p,
    lean_profile_path: path.join(CODEX_HOME, 'lean.config.toml'),
    lean_profile_exists: fs.existsSync(path.join(CODEX_HOME, 'lean.config.toml')),
    model: (text.match(/^model\s*=\s*"([^"]+)"/m) || [])[1] || '',
    model_reasoning_effort: (text.match(/^model_reasoning_effort\s*=\s*"([^"]+)"/m) || [])[1] || '',
    memories_enabled: /use_memories\s*=\s*true/.test(text),
    generate_memories: /generate_memories\s*=\s*true/.test(text),
    mcp_servers: mcp,
    plugins,
  }
}

function summarizePromptInput() {
  const result = runOptional('codex', ['debug', 'prompt-input', 'codex-insights baseline'])
  if (!result.ok || !result.json) return { ok: false, error: result.error || 'unparseable output' }
  const json = result.json
  const items = Array.isArray(json) ? json : Array.isArray(json.items) ? json.items : []
  const components = items.map((item, i) => {
    const text = typeof item === 'string' ? item : JSON.stringify(item)
    return {
      index: i,
      type: item?.type || item?.role || typeof item,
      chars: text.length,
      approx_tokens: Math.ceil(text.length / 4),
    }
  }).sort((a, b) => b.chars - a.chars).slice(0, 10)
  return { ok: true, count: items.length, components }
}

function summarizeDoctor() {
  const result = runOptional('codex', ['doctor', '--summary'])
  return result.ok ? { ok: true, raw_chars: result.raw_chars } : { ok: false, error: result.error }
}

function summarizeCcusage() {
  const available = runOptional('ccusage', ['--version'])
  if (!available.ok) return { available: false, error: available.error }
  return {
    available: true,
    daily: runOptional('ccusage', ['codex', 'daily', '--json']),
    weekly: runOptional('ccusage', ['codex', 'weekly', '--json']),
    session: runOptional('ccusage', ['codex', 'session', '--json']),
  }
}

const index = readSessionIndex()
const sourceDirs = [path.join(CODEX_HOME, 'sessions'), path.join(CODEX_HOME, 'archived_sessions')]
const files = sourceDirs.flatMap(walk)
const parsed = []
for (const file of files) {
  try {
    let rec = parseRollout(file, index)
    const recTime = rec.last_ts || rec.first_ts || rec.mtime
    if (SINCE && recTime && new Date(recTime) < SINCE) continue
    rec = applyWindowDelta(rec, SINCE)
    if (!rec) continue
    if (rec.token_events > 0) parsed.push(rec)
  } catch (e) {
    parsed.push({ id: extractId(file), file, error: String(e.message || e), total_tokens: 0, flags: [] })
  }
}

parsed.sort((a, b) => (b.total_tokens || 0) - (a.total_tokens || 0))
const sessions = parsed.slice(0, SESSION_LIMIT)
const allTotals = parsed.reduce((acc, s) => {
  acc.total_tokens += s.total_tokens || 0
  acc.input_tokens += s.input_tokens || 0
  acc.cached_input_tokens += s.cached_input_tokens || 0
  acc.output_tokens += s.output_tokens || 0
  acc.reasoning_output_tokens += s.reasoning_output_tokens || 0
  acc.tool_calls += s.tool_calls || 0
  acc.tool_output_tokens += s.tool_output_tokens || 0
  return acc
}, { total_tokens: 0, input_tokens: 0, cached_input_tokens: 0, output_tokens: 0, reasoning_output_tokens: 0, tool_calls: 0, tool_output_tokens: 0 })

const allDates = parsed.flatMap(s => [s.window_start_event || s.first_ts, s.window_end_event || s.last_ts]).filter(Boolean).sort()
const config = summarizeConfig()
const data = {
  generated_at: new Date().toISOString(),
  since: SINCE_RAW,
  window_start: SINCE ? SINCE.toISOString() : null,
  actual_range: { start: allDates[0] || null, end: allDates[allDates.length - 1] || null },
  source_confidence: 'exact Codex token_count events',
  snapshot: {
    generated_at: new Date().toISOString(),
    since: SINCE_RAW,
    sessions_found: parsed.length,
    sessions_reported: sessions.length,
    total_tokens: allTotals.total_tokens,
    reasoning_output_tokens: allTotals.reasoning_output_tokens,
    tool_calls: allTotals.tool_calls,
    mcp_count: config.mcp_servers.length,
    plugin_count: config.plugins.length,
    lean_profile_exists: config.lean_profile_exists,
  },
  totals: allTotals,
  config,
  prompt_input: summarizePromptInput(),
  doctor: summarizeDoctor(),
  ccusage: summarizeCcusage(),
  sessions: sessions.map(prepareSessionForOutput),
  flags: summarizeFlags(parsed),
  recommendations: buildRecommendations(config, parsed, allTotals),
}

function prepareSessionForOutput(session) {
  const copy = { ...session }
  delete copy.token_history
  delete copy.total_token_usage
  delete copy.last_token_usage
  delete copy.final_message
  copy.file = copy.file ? copy.file.replace(HOME, '~') : copy.file
  copy.cwd = copy.cwd ? copy.cwd.replace(HOME, '~') : copy.cwd
  return copy
}

function summarizeFlags(rows) {
  const counts = {}
  for (const s of rows) for (const f of s.flags || []) counts[f.key] = (counts[f.key] || 0) + 1
  return counts
}

function buildRecommendations(config, rows, totals) {
  const recs = []
  if (config.lean_profile_exists) {
    recs.push({
      title: 'Use the lean Codex profile for small tasks',
      mode: 'Lean',
      rationale: `Lean mode is available at ${config.lean_profile_path}. Use it for local code, shell, linting, and small report work so the full-power setup remains available for harder work.`,
      artifact: 'codex -p lean\n\nUse the default profile for cross-system research, incidents, architecture, and ambiguous reviews.',
    })
  } else if (config.model_reasoning_effort === 'high') {
    recs.push({
      title: 'Create a lean Codex profile for small tasks',
      mode: 'Lean',
      rationale: 'Your default reasoning effort is high. Keep it for hard work, but make cheap code/search/shell sessions easy to start.',
      artifact: `# ~/.codex/lean.config.toml\nmodel_reasoning_effort = "low"\n\n[memories]\nuse_memories = false\ngenerate_memories = false\n\n[mcp_servers.glean_default]\nenabled = false\n[mcp_servers.grafana]\nenabled = false\n[mcp_servers.granola]\nenabled = false\n[mcp_servers.notion]\nenabled = false\n[mcp_servers.atlassian]\nenabled = false\n[mcp_servers.node_repl]\nenabled = false\n`,
    })
  }
  if (config.mcp_servers.length >= 6) {
    recs.push({
      title: 'Choose MCPs by mode',
      mode: 'Power Modes',
      rationale: `${config.mcp_servers.length} MCP servers are configured (${config.mcp_servers.join(', ')}). That is useful; lean mode makes the small road cheap without taking away the big road.`,
      artifact: 'Use `codex -p lean` for local code/shell work; use full default for cross-system research, incidents, and docs.',
    })
  }
  const contextSessions = rows.filter(s => (s.flags || []).some(f => f.key === 'context_load')).length
  if (contextSessions > 0) {
    recs.push({
      title: 'Spend tokens on judgment, not repeated context re-ingest',
      mode: 'Intervention',
      rationale: `${contextSessions} sessions in this window had large latest-turn context loads.`,
      artifact: 'Before switching topics, ask for a compact handoff or start a fresh thread. For long investigations, save findings to a short Markdown file and restart from that file.',
    })
  }
  if (totals.reasoning_output_tokens >= 50000) {
    recs.push({
      title: 'Watch reasoning output on routine work',
      mode: 'Workflow Coach',
      rationale: `The window includes ${fmt(totals.reasoning_output_tokens)} reasoning output tokens.`,
      artifact: 'Use low or medium reasoning for linting, small edits, command lookups, and report rendering. Reserve high reasoning for architecture, incidents, security reviews, and ambiguous reviews.',
    })
  }
  return recs.slice(0, 5)
}

const compactPath = path.join(OUTDIR, 'compact.json')
const ledgerPath = path.join(OUTDIR, 'source-ledger.md')
fs.writeFileSync(compactPath, JSON.stringify(data, null, 2))
fs.writeFileSync(ledgerPath, renderLedger(data, sourceDirs, files))
console.log(`Codex insights: ${parsed.length} exact sessions found, ${sessions.length} reported, ${fmt(allTotals.total_tokens)} total tokens`)
console.log(`Wrote ${compactPath}`)
console.error(`Source ledger: ${ledgerPath}`)

function renderLedger(data, sourceDirs, files) {
  const lines = ['# Codex Insights Source Ledger', '']
  lines.push(`Generated: ${data.generated_at}`)
  lines.push(`Since: ${data.since}`)
  lines.push('')
  lines.push('## Included Sources')
  for (const dir of sourceDirs) lines.push(`- ${dir}: ${fs.existsSync(dir) ? 'found' : 'missing'}`)
  lines.push(`- ${path.join(CODEX_HOME, 'session_index.jsonl')}: ${fs.existsSync(path.join(CODEX_HOME, 'session_index.jsonl')) ? 'found' : 'missing'}`)
  lines.push('')
  lines.push('## Counts')
  lines.push(`- Rollout files scanned: ${files.length}`)
  lines.push(`- Sessions with exact token_count events: ${data.snapshot.sessions_found}`)
  lines.push(`- Sessions reported: ${data.snapshot.sessions_reported}`)
  lines.push(`- Source confidence: ${data.source_confidence}`)
  lines.push('')
  lines.push('## Optional Cross-Checks')
  lines.push(`- ccusage: ${data.ccusage.available ? 'available' : 'unavailable'}`)
  lines.push(`- codex debug prompt-input: ${data.prompt_input.ok ? 'available' : 'unavailable'}`)
  lines.push(`- codex doctor: ${data.doctor.ok ? 'available' : 'unavailable'}`)
  return `${lines.join('\n')}\n`
}
