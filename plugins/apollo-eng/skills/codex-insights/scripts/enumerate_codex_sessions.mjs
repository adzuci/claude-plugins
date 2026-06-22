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

function collectInvocationMentions(text, rec) {
  for (const match of String(text || '').matchAll(/\$([A-Za-z0-9_-]+(?::[A-Za-z0-9_-]+)?)/g)) {
    addTool(rec.skill_invocations, `$${match[1]}`)
  }
  for (const match of String(text || '').matchAll(/\/([A-Za-z0-9_-]+:[A-Za-z0-9_-]+|usage|status)\b/g)) {
    addTool(rec.slash_commands, `/${match[1]}`)
    if (match[1].includes(':')) addTool(rec.skill_invocations, `$${match[1]}`)
  }
}

function textFromMessageContent(value) {
  if (typeof value === 'string') return value
  if (Array.isArray(value)) {
    return value.map(item => {
      if (typeof item === 'string') return item
      if (item && typeof item === 'object') return item.text || item.content || ''
      return ''
    }).filter(Boolean).join('\n')
  }
  if (value && typeof value === 'object') return value.text || value.content || ''
  return ''
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
    skill_invocations: {},
    slash_commands: {},
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
    if (obj.type === 'event_msg' && payload.type === 'user_message') {
      collectInvocationMentions(payload.text || payload.message || payload.content || '', rec)
    }
    if (obj.type === 'response_item' && payload.type === 'message' && payload.role === 'user') {
      collectInvocationMentions(textFromMessageContent(payload.content), rec)
    }
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
    return { ok: false, error: optionalCommandError(cmd, args, e) }
  }
}

function runOptionalText(cmd, args) {
  try {
    const stdout = execFileSync(cmd, args, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], timeout: 20000 })
    return { ok: true, text: stdout, raw_chars: stdout.length }
  } catch (e) {
    return { ok: false, error: optionalCommandError(cmd, args, e) }
  }
}

function optionalCommandError(cmd, args, error) {
  const text = String(error?.stderr || error?.message || error || '')
  if (cmd === 'codex' && /PATH aliases: Operation not permitted|Operation not permitted \(os error 1\)/.test(text)) {
    return `${cmd} ${args.join(' ')} is unavailable in the current sandbox because PATH alias creation is denied; rerun outside the sandbox if this optional cross-check is needed.`
  }
  return text.slice(0, 500)
}

function safeJSON(txt) {
  try {
    return JSON.parse(txt)
  } catch {
    return null
  }
}

function splitSection(raw) {
  const out = []
  let cur = ''
  let quoted = false
  for (let i = 0; i < raw.length; i += 1) {
    const ch = raw[i]
    if (ch === '"' && raw[i - 1] !== '\\') quoted = !quoted
    if (ch === '.' && !quoted) {
      out.push(unquoteToml(cur.trim()))
      cur = ''
    } else {
      cur += ch
    }
  }
  if (cur.trim()) out.push(unquoteToml(cur.trim()))
  return out
}

function unquoteToml(value) {
  const v = String(value || '').trim()
  if (v.startsWith('"') && v.endsWith('"')) return v.slice(1, -1).replace(/\\"/g, '"')
  return v
}

function stripInlineComment(line) {
  let quoted = false
  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i]
    if (ch === '"' && line[i - 1] !== '\\') quoted = !quoted
    if (ch === '#' && !quoted) return line.slice(0, i)
  }
  return line
}

function parseTomlValue(raw) {
  const value = raw.trim()
  if (value === 'true') return true
  if (value === 'false') return false
  if (value.startsWith('[') && value.endsWith(']')) {
    const inner = value.slice(1, -1).trim()
    if (!inner) return []
    const items = []
    let cur = ''
    let quoted = false
    for (let i = 0; i < inner.length; i += 1) {
      const ch = inner[i]
      if (ch === '"' && inner[i - 1] !== '\\') quoted = !quoted
      if (ch === ',' && !quoted) {
        items.push(parseTomlValue(cur))
        cur = ''
      } else {
        cur += ch
      }
    }
    if (cur.trim()) items.push(parseTomlValue(cur))
    return items
  }
  if (value.startsWith('"') && value.endsWith('"')) return unquoteToml(value)
  if (/^-?\d+(\.\d+)?$/.test(value)) return Number(value)
  return value
}

function tomlArrayDepth(line) {
  let quoted = false
  let depth = 0
  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i]
    if (ch === '"' && line[i - 1] !== '\\') quoted = !quoted
    if (quoted) continue
    if (ch === '[') depth += 1
    if (ch === ']') depth -= 1
  }
  return depth
}

function incompleteTomlValue(raw) {
  const value = raw.trim()
  if (value.startsWith('"""') && !value.slice(3).includes('"""')) return { type: 'triple', terminator: '"""' }
  if (value.startsWith("'''") && !value.slice(3).includes("'''")) return { type: 'triple', terminator: "'''" }
  if (value.startsWith('[')) {
    const depth = tomlArrayDepth(value)
    if (depth > 0) return { type: 'array', depth }
  }
  return null
}

function parseCodexToml(text) {
  const tables = new Map()
  let section = ''
  let multiline = null
  for (const raw of String(text || '').split(/\n/)) {
    const line = stripInlineComment(raw).trim()
    if (multiline) {
      if (multiline.type === 'triple' && line.includes(multiline.terminator)) multiline = null
      else if (multiline.type === 'array') {
        multiline.raw += `\n${line}`
        multiline.depth += tomlArrayDepth(line)
        if (multiline.depth <= 0) {
          if (!tables.has(multiline.section)) tables.set(multiline.section, {})
          tables.get(multiline.section)[multiline.key] = parseTomlValue(multiline.raw)
          multiline = null
        }
      }
      continue
    }
    if (!line) continue
    const sec = /^\[\[?(.+?)\]?\]$/.exec(line)
    if (sec) {
      section = sec[1].trim()
      if (!tables.has(section)) tables.set(section, {})
      continue
    }
    const kv = /^([A-Za-z0-9_.-]+)\s*=\s*(.+)$/.exec(line)
    if (!kv) continue
    const pending = incompleteTomlValue(kv[2])
    if (pending) {
      multiline = { ...pending, key: kv[1], section, raw: kv[2] }
      continue
    }
    if (!tables.has(section)) tables.set(section, {})
    tables.get(section)[kv[1]] = parseTomlValue(kv[2])
  }
  return tables
}

function commentedDisabledMcps(text) {
  const out = new Map()
  for (const match of String(text || '').matchAll(/^#\s*(?:Disabled.*?:\s*)?\[mcp_servers\.([^\]\s]+)\]/gm)) {
    const name = unquoteToml(match[1])
    if (!out.has(name)) {
      out.set(name, {
        name,
        enabled: false,
        status: 'globally disabled',
        source_layer: 'global-commented',
        scope: 'global',
        disabled_reason: 'commented out in global config',
      })
    }
  }
  return [...out.values()]
}

function mcpEntriesFromTables(tables, sourceLayer, scope, projectPath = '') {
  const entries = []
  for (const [section, values] of tables.entries()) {
    const parts = splitSection(section)
    if (parts[0] !== 'mcp_servers' || parts.length !== 2) continue
    const name = parts[1]
    const enabled = values.enabled !== false
    entries.push({
      name,
      transport: values.url ? 'http' : values.command ? 'stdio' : '',
      url: values.url || '',
      command: values.command || '',
      args: Array.isArray(values.args) ? values.args : [],
      enabled,
      status: enabled ? (scope === 'project' ? 'project-scoped' : 'globally enabled') : (scope === 'project' ? 'project-disabled override' : 'globally disabled'),
      source_layer: sourceLayer,
      scope,
      project_path: projectPath,
    })
  }
  return entries
}

function pluginEntriesFromTables(tables, sourceLayer) {
  const entries = []
  for (const [section, values] of tables.entries()) {
    const parts = splitSection(section)
    if (parts[0] !== 'plugins' || parts.length !== 2) continue
    entries.push({
      name: parts[1],
      enabled: values.enabled !== false,
      source_layer: sourceLayer,
    })
  }
  return entries
}

function featureFlagsFromTables(tables) {
  const pick = names => Object.fromEntries(names.flatMap(name => {
    const values = tables.get(name)
    return values ? Object.entries(values) : []
  }))
  return {
    features: pick(['features']),
    memories: pick(['memories']),
    desktop: pick(['desktop']),
    tui: pick(['tui']),
  }
}

function projectCountsFromText(text) {
  const counts = new Map()
  for (const match of String(text || '').matchAll(/^\[projects\.((?:"[^"]+")|[^\]\s]+)\]/gm)) {
    const projectPath = unquoteToml(match[1])
    counts.set(projectPath, (counts.get(projectPath) || 0) + 1)
  }
  return counts
}

function projectEntriesFromTables(tables, projectCounts = new Map()) {
  const projects = []
  for (const [section, values] of tables.entries()) {
    const parts = splitSection(section)
    if (parts[0] !== 'projects' || parts.length !== 2) continue
    const projectPath = parts[1]
    const exists = fs.existsSync(projectPath)
    const localConfigPath = path.join(projectPath, '.codex', 'config.toml')
    projects.push({
      path: projectPath,
      trust_level: values.trust_level || '',
      trusted: values.trust_level === 'trusted',
      exists,
      stale: !exists,
      duplicate: (projectCounts.get(projectPath) || 0) > 1,
      config_path: localConfigPath,
      config_exists: exists && fs.existsSync(localConfigPath),
    })
  }
  return projects
}

function parseRuntimeMcpList(text) {
  const lines = String(text || '').split(/\n/).map(line => line.trim()).filter(Boolean)
  const rows = []
  for (const line of lines) {
    if (line.startsWith('WARNING:') || line.startsWith('Name ')) continue
    const parts = line.split(/\s{2,}/)
    if (parts.length < 4) continue
    rows.push({
      name: parts[0],
      url: parts[1] === '-' ? '' : parts[1],
      bearer_token_env_var: parts[2] === '-' ? '' : parts[2],
      status: parts[3] || '',
      auth: parts.slice(4).join(' ') || '',
    })
  }
  return rows
}

function runtimeMcpVerification() {
  const result = runOptionalText('codex', ['mcp', 'list'])
  if (!result.ok) return { ok: false, command: 'codex mcp list', error: result.error }
  return {
    ok: true,
    command: 'codex mcp list',
    note: 'Runtime verification reflects what this Codex build loaded for the current project.',
    rows: parseRuntimeMcpList(result.text),
    raw_chars: result.raw_chars,
  }
}

function classifyBroadMcp(entry) {
  const broad = new Set(['glean_default', 'granola', 'intercom', 'grafana', 'sentry', 'browser', 'node_repl', 'notion', 'atlassian', 'apollo_snowflake'])
  return broad.has(entry.name)
}

function inferProjectCluster(projectPath, sessions) {
  const hay = `${projectPath} ${sessions.map(s => `${s.cwd || ''} ${s.thread_name || ''}`).join(' ')}`.toLowerCase()
  if (/support|intercom|customer|macro|granola/.test(hay)) return 'support'
  if (/triage|incident|grafana|sentry|alert|oncall|pagerduty/.test(hay)) return 'triage'
  if (/skill|claude-plugins|docs|codex|context7/.test(hay)) return 'skills/docs'
  return 'coding/default'
}

function commandExists(name) {
  const paths = String(process.env.PATH || '').split(path.delimiter).filter(Boolean)
  return paths.some(dir => {
    const candidate = path.join(dir, name)
    try {
      fs.accessSync(candidate, fs.constants.X_OK)
      return true
    } catch {
      return false
    }
  })
}

function summarizeSpendMonitoring(featureFlags) {
  const scriptPath = path.join(HOME, '.local', 'bin', 'codex-cost.sh')
  const statusLine = featureFlags?.tui?.status_line
  const statusLineText = Array.isArray(statusLine) ? statusLine.join(' ') : String(statusLine || '')
  const codexStatusLineMentionsSpend = /cost|spend|credit|codexbar|codex-cost/i.test(statusLineText)
  const codexbarAvailable = commandExists('codexbar')
  const scriptExists = fs.existsSync(scriptPath)
  return {
    monitoring_api_spend: codexbarAvailable || scriptExists || codexStatusLineMentionsSpend,
    codexbar_available: codexbarAvailable,
    codex_cost_script_path: scriptPath,
    codex_cost_script_exists: scriptExists,
    codex_status_line_mentions_spend: codexStatusLineMentionsSpend,
  }
}

function walkSkillFiles(dir, depth = 0) {
  if (depth > 8) return []
  const out = []
  try {
    for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
      const p = path.join(dir, ent.name)
      if (ent.isDirectory()) out.push(...walkSkillFiles(p, depth + 1))
      else if (ent.isFile() && ent.name === 'SKILL.md') out.push(p)
    }
  } catch {
    // optional source
  }
  return out
}

function frontmatterField(text, field) {
  const fm = /^---\n([\s\S]*?)\n---/.exec(String(text || ''))
  if (!fm) return null
  const m = new RegExp(`^${field}:\\s*(.+)$`, 'm').exec(fm[1])
  return m ? m[1].trim().replace(/^['"]|['"]$/g, '') : null
}

function skillInvocationForPath(skillPath, name) {
  const parts = skillPath.split(path.sep)
  const skillIdx = parts.lastIndexOf('skills')
  const cacheIdx = parts.lastIndexOf('cache')
  if (cacheIdx !== -1 && skillIdx > cacheIdx + 2) {
    const plugin = parts[skillIdx - 2]
    return `$${plugin}:${name}`
  }
  return `$${name}`
}

function discoverSkills() {
  const roots = [
    path.join(CODEX_HOME, 'skills'),
    path.join(CODEX_HOME, 'plugins', 'cache'),
  ]
  const seen = new Set()
  const skills = []
  for (const file of roots.flatMap(root => walkSkillFiles(root))) {
    if (seen.has(file)) continue
    seen.add(file)
    const text = fs.readFileSync(file, 'utf8')
    const name = frontmatterField(text, 'name') || path.basename(path.dirname(file))
    const disabled = frontmatterField(text, 'disable-model-invocation') === 'true'
    skills.push({
      name,
      invocation: skillInvocationForPath(file, name),
      path: file.replace(HOME, '~'),
      disable_model_invocation: disabled,
    })
  }
  return skills.sort((a, b) => a.invocation.localeCompare(b.invocation))
}

function summarizeSkillUsage(rows) {
  const inventory = discoverSkills()
  const counts = {}
  const slashCounts = {}
  for (const row of rows) {
    for (const [name, count] of Object.entries(row.skill_invocations || {})) counts[name] = (counts[name] || 0) + count
    for (const [name, count] of Object.entries(row.slash_commands || {})) slashCounts[name] = (slashCounts[name] || 0) + count
  }
  const withUsage = inventory.map(skill => ({
    ...skill,
    invocations: counts[skill.invocation] || counts[`$${skill.name}`] || 0,
  }))
  const unusedModelInvoked = withUsage
    .filter(skill => skill.invocations === 0 && !skill.disable_model_invocation)
    .slice(0, 20)
  const invoked = withUsage
    .filter(skill => skill.invocations > 0)
    .sort((a, b) => b.invocations - a.invocations)
    .slice(0, 20)
  return {
    inventory_count: inventory.length,
    invoked_count: withUsage.filter(skill => skill.invocations > 0).length,
    unused_model_invoked_count: withUsage.filter(skill => skill.invocations === 0 && !skill.disable_model_invocation).length,
    unused_model_invoked: unusedModelInvoked,
    invoked,
    slash_commands: slashCounts,
    usage_seen: Boolean(slashCounts['/usage']),
    status_seen: Boolean(slashCounts['/status']),
    disable_guidance: 'For specialized skills that should only run on explicit demand, set disable-model-invocation: true in SKILL.md and invoke them with $skill or $plugin:skill only when the task matches.',
  }
}

function summarizeMcpAttribution(rows) {
  const byServer = {}
  for (const row of rows) {
    const mcpCalls = Object.entries(row.tools || {})
      .map(([tool, calls]) => {
        const match = /^mcp__(.+?)__/.exec(tool)
        return match ? { server: match[1], calls } : null
      })
      .filter(Boolean)
    const totalMcpCalls = mcpCalls.reduce((sum, item) => sum + item.calls, 0)
    for (const item of mcpCalls) {
      const bucket = byServer[item.server] || { server: item.server, calls: 0, estimated_tool_output_tokens: 0 }
      bucket.calls += item.calls
      if (totalMcpCalls > 0) {
        bucket.estimated_tool_output_tokens += Math.round((row.tool_output_tokens || 0) * (item.calls / totalMcpCalls))
      }
      byServer[item.server] = bucket
    }
  }
  return {
    exact_credit_attribution_available: false,
    note: 'Codex token_count events are session-level. MCP-level credit attribution is estimated from MCP call counts and session-level tool-output tokens only.',
    servers: Object.values(byServer).sort((a, b) => b.estimated_tool_output_tokens - a.estimated_tool_output_tokens).slice(0, 20),
  }
}

function summarizeConfig() {
  const p = path.join(CODEX_HOME, 'config.toml')
  const text = fs.existsSync(p) ? fs.readFileSync(p, 'utf8') : ''
  const tables = parseCodexToml(text)
  const featureFlags = featureFlagsFromTables(tables)
  const projectEntries = projectEntriesFromTables(tables, projectCountsFromText(text))
  const trustedProjects = projectEntries.filter(project => project.trusted)
  const projectConfigs = []
  const projectScopedMcps = []
  const projectPlugins = []
  for (const project of trustedProjects) {
    if (!project.config_exists) continue
    const localText = fs.readFileSync(project.config_path, 'utf8')
    const localTables = parseCodexToml(localText)
    const mcpEntries = mcpEntriesFromTables(localTables, 'project', 'project', project.path)
    const pluginEntries = pluginEntriesFromTables(localTables, 'project')
    projectScopedMcps.push(...mcpEntries)
    projectPlugins.push(...pluginEntries.map(plugin => ({ ...plugin, project_path: project.path })))
    projectConfigs.push({
      project_path: project.path,
      config_path: project.config_path,
      mcp_count: mcpEntries.length,
      plugin_count: pluginEntries.length,
      feature_flags: featureFlagsFromTables(localTables),
    })
  }
  const globalActiveMcps = mcpEntriesFromTables(tables, 'global', 'global')
  const disabledCommentMcps = commentedDisabledMcps(text)
  const allMcps = [...globalActiveMcps, ...disabledCommentMcps, ...projectScopedMcps]
  const enabledGlobalMcps = globalActiveMcps.filter(entry => entry.enabled)
  const disabledGlobalMcps = [...globalActiveMcps.filter(entry => !entry.enabled), ...disabledCommentMcps]
  const pluginEntries = [...pluginEntriesFromTables(tables, 'global'), ...projectPlugins]
  const enabledPlugins = pluginEntries.filter(plugin => plugin.enabled).map(plugin => plugin.name)
  const staleProjects = projectEntries.filter(project => project.stale)
  const duplicateProjects = projectEntries.filter(project => project.duplicate)
  return {
    config_path: p,
    lean_profile_path: path.join(CODEX_HOME, 'lean.config.toml'),
    lean_profile_exists: fs.existsSync(path.join(CODEX_HOME, 'lean.config.toml')),
    model: tables.get('')?.model || '',
    model_reasoning_effort: tables.get('')?.model_reasoning_effort || '',
    memories_enabled: tables.get('memories')?.use_memories === true,
    generate_memories: tables.get('memories')?.generate_memories === true,
    mcp_servers: enabledGlobalMcps.map(entry => entry.name),
    plugins: enabledPlugins,
    feature_flags: featureFlags,
    spend_monitoring: summarizeSpendMonitoring(featureFlags),
    plugin_entries: pluginEntries,
    project_entries: projectEntries,
    project_configs: projectConfigs,
    stale_project_entries: staleProjects,
    duplicate_project_entries: duplicateProjects,
    mcp_audit: {
      enabled_global: enabledGlobalMcps,
      disabled_global: disabledGlobalMcps,
      project_scoped: projectScopedMcps,
      all: allMcps,
      broad_global_flags: enabledGlobalMcps.filter(classifyBroadMcp).map(entry => ({
        name: entry.name,
        reason: 'Broad or workflow-specific MCP is globally enabled; prefer project-local config when only needed for a narrow mode.',
      })),
      runtime_verification: runtimeMcpVerification(),
    },
  }
}

function summarizePromptInput() {
  const result = runOptional('codex', ['debug', 'prompt-input', 'codex-insights baseline'])
  if (!result.ok || !result.json) return { ok: false, error: promptInputError(result.error || 'unparseable output') }
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

function promptInputError(error) {
  const text = String(error || '')
  if (/PATH aliases: Operation not permitted|Operation not permitted \(os error 1\)|PATH alias creation is denied/.test(text)) {
    return 'codex debug prompt-input is unavailable in the current sandbox because PATH alias creation is denied; rerun outside the sandbox to capture prompt shape.'
  }
  return text
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
const skillUsage = summarizeSkillUsage(parsed)
const mcpAttribution = summarizeMcpAttribution(parsed)
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
    mcp_count: config.mcp_audit.all.length,
    enabled_global_mcp_count: config.mcp_audit.enabled_global.length,
    disabled_global_mcp_count: config.mcp_audit.disabled_global.length,
    project_scoped_mcp_count: config.mcp_audit.project_scoped.length,
    plugin_count: config.plugins.length,
    trusted_project_count: config.project_entries.filter(project => project.trusted).length,
    stale_project_count: config.stale_project_entries.length,
    lean_profile_exists: config.lean_profile_exists,
  },
  totals: allTotals,
  config,
  skill_usage: skillUsage,
  mcp_attribution: mcpAttribution,
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
      artifact: `# ~/.codex/lean.config.toml\nmodel_reasoning_effort = "low"\n\n[memories]\nuse_memories = false\ngenerate_memories = false\n\n# Keep production/debugging MCPs out of this profile unless a task explicitly needs them.\n`,
    })
  }
  if (config.mcp_audit.enabled_global.length >= 4 || config.mcp_audit.broad_global_flags.length > 0) {
    recs.push({
      title: 'Move narrow MCPs into project-local configs',
      mode: 'Project Scope',
      rationale: `${config.mcp_audit.enabled_global.length} MCP servers are globally enabled. Project-local .codex/config.toml keeps support, triage, and docs tools available without loading them for every coding task.`,
      artifact: projectSplitSnippets(config, rows),
    })
  }
  if (config.stale_project_entries.length > 0) {
    recs.push({
      title: 'Clean stale trusted project entries',
      mode: 'Config Hygiene',
      rationale: `${config.stale_project_entries.length} trusted project entries point at paths that no longer exist. They do not help current work and make config audits noisier.`,
      artifact: config.stale_project_entries.slice(0, 12).map(project => `# remove stale project entry\n[projects."${project.path}"]`).join('\n\n'),
    })
  }
  const oneOffProjects = config.project_entries.filter(project => project.trusted && project.path.includes('/Documents/Codex/20')).length
  if (oneOffProjects >= 10) {
    recs.push({
      title: 'Use narrow durable project folders for repeated modes',
      mode: 'Project Split',
      rationale: `${oneOffProjects} trusted project entries look like one-off session folders. Durable support, triage, and skills folders reduce config growth and keep project MCP scope explicit.`,
      artifact: 'Use stable roots such as ~/Documents/Codex/projects/support, ~/Documents/Codex/projects/triage, and ~/Documents/Codex/projects/skills instead of trusting every scratch folder.',
    })
  }
  const contextSessions = rows.filter(s => (s.flags || []).some(f => f.key === 'context_load')).length
  if (contextSessions > 0) {
    recs.push({
      title: 'Use context reset discipline',
      mode: 'Intervention',
      rationale: `${contextSessions} sessions in this window had large latest-turn context loads. The biggest lever is resetting context at task boundaries instead of resuming huge old sessions.`,
      artifact: [
        '1. Start a fresh thread for each unrelated task.',
        '2. Use /compact when a task is getting long, and /clear when switching tasks.',
        '3. Point Codex at files, logs, PRs, or paths instead of pasting large blobs.',
        '4. Ask one clear task per message: goal, path, constraints, and what done means.',
        '5. For investigations, ask for targeted search first, then evidence summary.',
        '6. Avoid subagents for simple repo search; rg, sed, git diff, and focused reads are cheaper.',
        '7. Watch footer token counters; credits are an analytics/dashboard check, not a built-in status-line item.',
        '',
        'Example: In ~/code/apolloio/devops, check whether PR/change X affects prod Mongo networking. Use rg/git diff first, read only relevant Terraform modules/workspaces, and give me findings with file links. Do not make edits.',
      ].join('\n'),
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
  recs.push({
    title: 'Report replay pressure from exact token_count events',
    mode: 'Measured Facts',
    rationale: 'Large session replay and cache pressure should be reported from exact Codex token_count events, not inferred from memory or generic token estimates.',
    artifact: 'Use compact.json totals and per-session token_count deltas as the source of truth; label ccusage and runtime MCP output as cross-checks.',
  })
  return recs.slice(0, 5)
}

function projectSplitSnippets(config, rows) {
  const snippets = [
    {
      name: 'support',
      path: '~/Documents/Codex/projects/support/.codex/config.toml',
      mcps: ['granola', 'glean_default', 'notion', 'intercom'],
    },
    {
      name: 'triage',
      path: '~/Documents/Codex/projects/triage/.codex/config.toml',
      mcps: ['grafana', 'sentry', 'glean_default'],
    },
    {
      name: 'skills/docs',
      path: '~/Documents/Codex/projects/skills/.codex/config.toml',
      mcps: ['context7'],
    },
    {
      name: 'coding/default',
      path: '<repo>/.codex/config.toml',
      mcps: [],
    },
  ]
  const configured = new Set(config.mcp_audit.all.map(entry => entry.name))
  const topicCounts = {}
  for (const row of rows) {
    const cluster = inferProjectCluster(row.cwd || row.thread_name || '', rows)
    topicCounts[cluster] = (topicCounts[cluster] || 0) + 1
  }
  return snippets.map(snippet => {
    const header = `# ${snippet.name} (${snippet.path})`
    const body = snippet.mcps.length === 0
      ? '# No production/debugging MCPs by default. Add only the MCPs this repo actually needs.'
      : snippet.mcps.map(name => {
        const source = config.mcp_audit.all.find(entry => entry.name === name)
        const urlOrCommand = source?.url ? `url = "${source.url}"` : source?.command ? `command = "${source.command}"` : '# configure url or command'
        const note = configured.has(name) ? '' : '\n# Not currently configured globally; add credentials before use.'
        return `[mcp_servers.${name}]\nenabled = true\n${urlOrCommand}${note}`
      }).join('\n\n')
    const inferred = topicCounts[snippet.name] ? `\n# Recent sessions matching this mode: ${topicCounts[snippet.name]}` : ''
    return `${header}${inferred}\n${body}`
  }).join('\n\n')
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
