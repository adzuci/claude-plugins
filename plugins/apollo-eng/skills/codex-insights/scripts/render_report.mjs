#!/usr/bin/env node
/* eslint-disable no-console */

import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { esc, fmt } from './html_utils.mjs'

const argv = process.argv.slice(2)
const input = argv.find(a => !a.startsWith('--')) || '/tmp/codex-insights/compact.json'
const flag = name => {
  const i = argv.indexOf(name)
  return i === -1 ? null : argv[i + 1]
}
const out = flag('--out') || path.join(os.homedir(), '.codex', 'codex-insights', 'reports', `report-${new Date().toISOString().slice(0, 10)}.html`)
const footer = flag('--footer') || ''
const judgmentsPath = flag('--judgments')

const data = JSON.parse(fs.readFileSync(input, 'utf8'))
fs.mkdirSync(path.dirname(out), { recursive: true })

// Merge the skill's judgment pass (ROI / outcome / verdict per session, plus an overall
// verdict and per-week headlines) onto the deterministic burn ledger from the enumerator.
// efficiency is already computed and is never overwritten by judgment. Robust to a missing
// file: the ledger still renders with the computed efficiency and an "unjudged" note.
let judgments = null
if (judgmentsPath && fs.existsSync(judgmentsPath)) {
  try { judgments = JSON.parse(fs.readFileSync(judgmentsPath, 'utf8')) } catch { judgments = null }
}
const burn = data.burn_analysis || { overall_verdict: null, weekly: [], sessions: [] }
if (judgments) {
  const byId = new Map()
  for (const j of judgments.sessions || []) if (j && j.id) byId.set(j.id, j)
  burn.sessions = (burn.sessions || []).map(s => {
    const j = byId.get(s.id) || {}
    return { ...s, roi: j.roi || s.roi, outcome: j.outcome || s.outcome, verdict: j.verdict || s.verdict }
  })
  if (judgments.overall_verdict) burn.overall_verdict = judgments.overall_verdict
  if (Array.isArray(judgments.weekly) && judgments.weekly.length) burn.weekly = judgments.weekly
}

const scrub = s => String(s ?? '').replaceAll(os.homedir(), '~')
const pct = (n, d) => d ? `${Math.round((n / d) * 100)}%` : 'n/a'

const stat = (label, value) => `<div class="stat"><div class="stat-v">${esc(value)}</div><div class="stat-k">${esc(label)}</div></div>`
const badge = (text, tone = 'mut') => `<span class="badge ${tone}">${esc(text)}</span>`

// Dimension badge (ROI / outcome / efficiency) with a tone per value, mirroring
// deep-insights so the two reports read the same.
const DIM_TONE = {
  'worth-it': 'good', landed: 'good', lean: 'good',
  overpriced: 'warn', partial: 'warn', loose: 'warn',
  wasted: 'bad', dropped: 'bad', thrashy: 'bad',
}
const dimBadge = (dim, val) => {
  const v = String(val || 'unjudged').toLowerCase()
  const tone = DIM_TONE[v] || 'mut'
  return `<span class="badge ${tone}"><span class="dim">${esc(dim)}</span>${esc(v.replace(/-/g, ' '))}</span>`
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const weekLabel = wk => {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(wk || '')
  return m ? `${MONTHS[+m[2] - 1]} ${m[3]}` : (wk || '—')
}

const weeks = Array.isArray(data.by_week) ? data.by_week.filter(w => w.week && w.week !== 'undated') : []
const maxWeekTokens = weeks.reduce((m, w) => Math.max(m, w.total_tokens || 0), 0) || 1
const headlineByWeek = {}
for (const w of burn.weekly || []) if (w && w.week) headlineByWeek[w.week] = w.headline
const weekSeg = (tokens, cls) => {
  const w = ((tokens || 0) / maxWeekTokens) * 100
  return w > 0 ? `<span class="seg ${cls}" style="width:${w.toFixed(2)}%" title="${cls} ${fmt(tokens)} tok"></span>` : ''
}
const weekChart = weeks.map(w => {
  const et = w.efficiency_tokens || {}
  const bar = weekSeg(et.lean, 'good') + weekSeg(et.loose, 'warn') + weekSeg(et.thrashy, 'bad')
  const head = headlineByWeek[w.week]
  return `
    <div class="wk">
      <div class="wk-top">
        <span class="wk-label">${esc(weekLabel(w.week))}</span>
        <span class="wk-track">${bar}</span>
        <span class="wk-cost">${esc(fmt(w.total_tokens))}</span>
      </div>
      ${head ? `<p class="wk-head">${esc(scrub(head))}</p>` : ''}
    </div>`
}).join('\n')

const burnRows = (burn.sessions || []).map(s => {
  const signals = []
  if (s.edit_events) signals.push(`${s.edit_events} edits`)
  if (s.test_events) signals.push(`${s.test_events} test runs`)
  if (s.commit_events) signals.push(`${s.commit_events} commits`)
  if (s.user_prompt_count) signals.push(`${s.user_prompt_count} prompts`)
  signals.push(s.completed ? 'completed' : 'no completion event')
  const verdict = s.verdict
    ? esc(scrub(s.verdict))
    : `<span class="mut">Not judged this run — efficiency is computed; run the judgment step for ROI/outcome. Signals: ${esc(signals.join(' · '))}.</span>`
  return `
    <div class="card">
      <div class="card-head">
        <span class="cost">${esc(fmt(s.total_tokens))} tok<span class="mut"> · ≈${esc(fmt(s.credits))} cr</span></span>
        <span class="sid">${esc(scrub(s.label || s.id))}</span>
        <span class="badges">${dimBadge('ROI', s.roi)}${dimBadge('outcome', s.outcome)}${dimBadge('efficiency', s.efficiency)}</span>
      </div>
      <p class="verdict">${verdict}</p>
    </div>`
}).join('\n')

const topSessions = (data.sessions || []).map(s => `
  <div class="row">
    <div>
      <strong>${esc(s.thread_name || s.id)}</strong>
      <div class="mut">${esc(scrub(s.cwd || s.file || ''))}</div>
      <div class="chips">${(s.flags || []).map(f => badge(f.label, f.key === 'context_load' ? 'warn' : f.key === 'large_tool_output' ? 'bad' : 'mut')).join('')}</div>
    </div>
    <div class="num">${fmt(s.total_tokens)}</div>
  </div>`).join('\n')

const recs = (data.recommendations || []).map((r, i) => `
  <div class="rec">
    <div class="rec-head"><span class="pill">${i + 1}</span><strong>${esc(r.title)}</strong>${badge(r.mode || 'mode', 'blue')}</div>
    <p>${esc(scrub(r.rationale))}</p>
    ${r.artifact ? `<pre><code>${esc(scrub(r.artifact))}</code></pre>` : ''}
  </div>`).join('\n')

const promptBits = data.prompt_input?.ok
  ? (data.prompt_input.components || []).map(c => `<li>${esc(c.type)}: ${fmt(c.approx_tokens)} approx tokens</li>`).join('')
  : `<li>Unavailable: ${esc(data.prompt_input?.error || 'not captured')}</li>`

const config = data.config || {}
const mcpAudit = config.mcp_audit || { enabled_global: [], disabled_global: [], project_scoped: [], broad_global_flags: [], runtime_verification: { ok: false } }
const pluginEntries = config.plugin_entries || (config.plugins || []).map(name => ({ name, enabled: true, source_layer: 'global' }))
const pluginList = pluginEntries.slice(0, 30).map(s => `<code>${esc(s.name)}:${s.enabled ? 'on' : 'off'}@${esc(s.source_layer || 'global')}</code>`).join(' ')

function mcpTable(rows, empty) {
  if (!rows || rows.length === 0) return `<p class="mut">${esc(empty)}</p>`
  return `<table><thead><tr><th>Name</th><th>Status</th><th>Transport</th><th>Endpoint</th><th>Source</th></tr></thead><tbody>${rows.map(row => `
    <tr>
      <td><code>${esc(row.name)}</code></td>
      <td>${esc(row.status || (row.enabled ? 'enabled' : 'disabled'))}</td>
      <td>${esc(row.transport || (row.url ? 'http' : row.command ? 'stdio' : ''))}</td>
      <td>${esc(scrub(row.url || row.command || ''))}</td>
      <td>${esc(row.project_path ? `${row.source_layer}: ${scrub(row.project_path)}` : row.source_layer || row.scope || '')}</td>
    </tr>`).join('')}</tbody></table>`
}

function projectRows(rows, empty) {
  if (!rows || rows.length === 0) return `<p class="mut">${esc(empty)}</p>`
  return `<table><thead><tr><th>Finding</th><th>Trust</th><th>Path</th><th>Project Config</th></tr></thead><tbody>${rows.slice(0, 40).map(row => `
    <tr>
      <td>${row.stale ? badge('stale', 'bad') : ''}${row.duplicate ? badge('duplicate', 'warn') : ''}</td>
      <td>${esc(row.trust_level || '')}</td>
      <td><code>${esc(scrub(row.path))}</code></td>
      <td>${row.config_exists ? `<code>${esc(scrub(row.config_path))}</code>` : '<span class="mut">none found</span>'}</td>
    </tr>`).join('')}</tbody></table>`
}

function runtimeMcpBlock(runtime) {
  if (!runtime?.ok) return `<p class="mut">Runtime verification unavailable: ${esc(runtime?.error || 'not run')}</p>`
  const rows = runtime.rows || []
  if (rows.length === 0) return '<p class="mut">Runtime verification ran, but no MCP rows were parsed.</p>'
  return `<p class="mut">${esc(runtime.note || 'Runtime verification reflects what this Codex build loaded.')}</p>
  <table><thead><tr><th>Name</th><th>Status</th><th>URL</th><th>Auth</th></tr></thead><tbody>${rows.map(row => `
    <tr><td><code>${esc(row.name)}</code></td><td>${esc(row.status)}</td><td>${esc(row.url)}</td><td>${esc(row.auth)}</td></tr>`).join('')}</tbody></table>`
}

function contextReductionMoves() {
  const leanLine = config.lean_profile_exists
    ? `Use the existing lean profile at <code>${esc(scrub(config.lean_profile_path))}</code>.`
    : 'Create <code>~/.codex/lean.config.toml</code> for low-reasoning local code/search/shell sessions.'
  return `
    <ul>
      <li>Disable unused global MCPs and plugins; move narrow workflows into project-local <code>.codex/config.toml</code>.</li>
      <li>Use stable support, triage, and skills/docs project folders instead of trusting every scratch folder.</li>
      <li>Start fresh threads for different modes instead of carrying one long thread across unrelated work.</li>
      <li>${leanLine}</li>
      <li>Keep <code>AGENTS.md</code> short; move verbose workflow docs into skills or linked references.</li>
      <li>Keep high-noise tools such as browser, node, Grafana, and Sentry off by default and enable them only in scoped projects.</li>
      <li>Report large session replay/cache pressure using exact Codex <code>token_count</code> events.</li>
    </ul>`
}

function actionTable() {
  const flags = data.flags || {}
  const totals = data.totals || {}
  const sessionCount = data.snapshot?.sessions_found || 0
  const cacheShare = pct(totals.cached_input_tokens, totals.input_tokens + totals.cached_input_tokens)
  const toolOutputShare = pct(totals.tool_output_tokens, totals.total_tokens)
  const rows = [
    {
      signal: `${fmt(totals.tool_output_tokens)} tool-output tokens (${toolOutputShare})`,
      read: 'Tool output is a primary replay driver.',
      move: 'Route large logs, diffs, and generated artifacts to files; ask Codex to inspect targeted snippets or summarized ledgers.',
    },
    {
      signal: `${flags.repeated_tooling || 0} sessions with repeated tool loops`,
      read: 'Repeated reads/searches are burning context without adding new judgment.',
      move: 'After the third similar tool call, write a scratch ledger of facts and switch to validating hypotheses.',
    },
    {
      signal: `${flags.context_load || 0} sessions with large context load`,
      read: 'Long-running threads are carrying too much setup across task boundaries.',
      move: 'Start new threads from a short handoff when switching repos, incidents, support cases, or report generation modes.',
    },
    {
      signal: `${fmt(totals.reasoning_output_tokens)} reasoning tokens`,
      read: 'High reasoning is useful, but routine shell/report loops should not pay for it.',
      move: config.lean_profile_exists ? 'Use the existing lean profile for local code, search, shell, lint, and report rendering.' : 'Create a lean profile for local code, search, shell, lint, and report rendering.',
    },
    {
      signal: `${cacheShare} cache share across ${fmt(sessionCount)} exact sessions`,
      read: 'Cache is doing useful work, but high cache/replay still means large threads are being rehydrated.',
      move: 'Keep durable context in files/Obsidian and restart from the relevant note instead of resuming broad historical threads.',
    },
  ]
  return `<table><thead><tr><th>Measured Signal</th><th>Read</th><th>Next Move</th></tr></thead><tbody>${rows.map(row => `
    <tr>
      <td>${esc(row.signal)}</td>
      <td>${esc(row.read)}</td>
      <td>${esc(row.move)}</td>
    </tr>`).join('')}</tbody></table>`
}

function contextResetDiscipline() {
  const flags = data.flags || {}
  const totals = data.totals || {}
  const sessionCount = data.snapshot?.sessions_found || 0
  const replayTokens = (totals.input_tokens || 0) + (totals.cached_input_tokens || 0)
  const shouldShow = (flags.context_load || 0) > 0 || replayTokens >= 100000 || sessionCount >= 20
  if (!shouldShow) return ''
  return `<div class="panel">
    <strong>Context reset discipline</strong>
    <p>Yes. The biggest lever here is context reset discipline. This report shows context accumulation pressure, so the practical rule is to reset context at task boundaries instead of carrying large old threads forward.</p>
    <ol>
      <li>Start a fresh thread for each unrelated task. Avoid resuming a huge old session unless the old context is truly needed.</li>
      <li>Use <code>/compact</code> when a task is getting long, and <code>/clear</code> when switching tasks.</li>
      <li>Point Codex at files, logs, PRs, or paths instead of pasting large blobs into chat.</li>
      <li>Ask one clear task per message: goal, relevant path, constraints, and what done means.</li>
      <li>For investigations, ask for targeted search first, then summarize evidence.</li>
      <li>Avoid subagents for simple repo search; <code>rg</code>, <code>sed</code>, <code>git diff</code>, and focused file reads are cheaper.</li>
      <li>Watch the footer token counters already configured in Codex; credits themselves are an analytics/dashboard check, not a built-in status-line item.</li>
    </ol>
    <p class="mut">Token-efficient prompt example:</p>
    <pre><code>${esc('In ~/code/apolloio/devops, check whether PR/change X affects prod Mongo networking. Use rg/git diff first, read only relevant Terraform modules/workspaces, and give me findings with file links. Do not make edits.')}</code></pre>
    <p class="mut">For a deeper habits pass, run <code>/apollo-eng:token-efficiency-assessment</code>. It checks config signals, asks the habit questions, and saves results to Notion when that MCP is available or locally otherwise.</p>
  </div>`
}

function workflowRules() {
  const rules = [
    ['Local edits / lint / tests', config.lean_profile_exists ? 'Start with `codex -p lean`.' : 'Create and use a lean profile.'],
    ['Cross-system incidents / support / docs', 'Use full-power config, but write a source ledger early and restart from it when the investigation changes shape.'],
    ['Large command output', 'Save output to a file and ask for the exact lines or structured summary needed.'],
    ['Research mode', 'Turn connectors on deliberately, capture a short brief, then restart or compact before implementation.'],
    ['Cost visibility', 'Use Codex status-line tokens for live token pressure and codexbar for enterprise dollar tracking.'],
  ]
  return `<table><thead><tr><th>Work Type</th><th>Rule</th></tr></thead><tbody>${rules.map(([kind, rule]) => `
    <tr><td>${esc(kind)}</td><td>${esc(rule)}</td></tr>`).join('')}</tbody></table>`
}

function durableMemoryInsight() {
  const memoryOn = config.memories_enabled || config.feature_flags?.memories?.use_memories === true
  const generated = config.generate_memories || config.feature_flags?.memories?.generate_memories === true
  const projectConfigs = config.project_configs || []
  const obsidianProject = (config.project_entries || []).find(project => /obsidian-vault/.test(project.path || ''))
  const status = memoryOn || obsidianProject ? 'detected' : 'not detected'
  const details = [
    memoryOn ? 'Codex memories enabled' : 'Codex memories not enabled in parsed config',
    generated ? 'memory generation enabled' : 'memory generation not enabled',
    obsidianProject ? `trusted vault project: ${scrub(obsidianProject.path)}` : 'no trusted Obsidian vault project found',
    `${projectConfigs.length} project-local configs parsed`,
  ]
  return `<div class="panel">
    <strong>Durable memory: ${esc(status)}</strong>
    <p class="mut">${details.map(esc).join(' · ')}</p>
    <p>Keep using Obsidian/local notes as the durable context layer. This report should measure whether Codex reuses that context efficiently; it should not ask you to set up memory again when the config already shows it.</p>
  </div>`
}

function skillHygieneInsight() {
  const usage = data.skill_usage || {}
  const unused = usage.unused_model_invoked || []
  const invoked = usage.invoked || []
  const rows = unused.slice(0, 8).map(skill => `
    <tr>
      <td><code>${esc(skill.invocation)}</code></td>
      <td>${esc(scrub(skill.path || ''))}</td>
      <td>Add <code>disable-model-invocation: true</code>; invoke with <code>${esc(skill.invocation)}</code> only when the task clearly matches.</td>
    </tr>`).join('')
  const invokedList = invoked.length
    ? `<p class="mut">Recently invoked: ${invoked.slice(0, 8).map(skill => `<code>${esc(skill.invocation)}</code> (${skill.invocations})`).join(' ')}</p>`
    : '<p class="mut">No explicit skill invocations were detected in this window.</p>'
  const usageReminder = usage.usage_seen ? '/usage was seen in this window.' : 'Run /usage when you need current token/credit visibility.'
  const statusReminder = usage.status_seen ? '/status was seen in this window.' : 'Run /status when you need current session/model/runtime status.'
  return `<div class="panel">
    <strong>Skill surface hygiene</strong>
    <p class="mut">${esc(usage.inventory_count || 0)} skills found · ${esc(usage.invoked_count || 0)} explicitly invoked · ${esc(usage.unused_model_invoked_count || 0)} unused skills may still be model-invoked.</p>
    ${invokedList}
    <p>${esc(usage.disable_guidance || 'Use specialized skills only when appropriate.')}</p>
    <p>${esc(usageReminder)} ${esc(statusReminder)}</p>
    ${rows ? `<table><thead><tr><th>Unused Skill</th><th>Path</th><th>Suggested Change</th></tr></thead><tbody>${rows}</tbody></table>` : '<p class="mut">No unused model-invoked skills found in the measured window.</p>'}
  </div>`
}

function mcpAttributionInsight() {
  const attribution = data.mcp_attribution || {}
  const rows = (attribution.servers || []).slice(0, 8).map(server => `
    <tr>
      <td><code>${esc(server.server)}</code></td>
      <td>${esc(fmt(server.calls))}</td>
      <td>${esc(fmt(server.estimated_tool_output_tokens))}</td>
    </tr>`).join('')
  return `<div class="panel">
    <strong>MCP credit attribution: estimate only</strong>
    <p class="mut">${esc(attribution.note || 'Codex logs do not expose exact MCP-level credit attribution.')}</p>
    ${rows ? `<table><thead><tr><th>MCP</th><th>Calls</th><th>Estimated Tool-Output Tokens</th></tr></thead><tbody>${rows}</tbody></table>` : '<p class="mut">No MCP tool calls were detected in this window.</p>'}
  </div>`
}

const CODEXBAR_TMUX_INSTRUCTIONS = [
  'brew install --cask codexbar',
  'mkdir -p ~/.local/bin',
  "cat > ~/.local/bin/codex-cost.sh <<'EOF'",
  '#!/bin/bash',
  'OUTPUT=$(codexbar cost --provider codex 2>/dev/null)',
  '',
  'if [ -n "$OUTPUT" ]; then',
  "  TOKEN_STR=$(echo \"$OUTPUT\" | grep \"Today:\" | awk '{print $4}')",
  '  ',
  '  if [ -n "$TOKEN_STR" ]; then',
  "    RAW_VAL=$(echo \"$TOKEN_STR\" | sed 's/[A-Za-z]//g')",
  '    ',
  '    if [[ "$TOKEN_STR" == *M* ]]; then',
  "      CREDITS=$(awk -v val=\"$RAW_VAL\" 'BEGIN {print val * 1000}')",
  '    elif [[ "$TOKEN_STR" == *K* ]]; then',
  '      CREDITS=$RAW_VAL',
  '    else',
  "      CREDITS=$(awk -v val=\"$RAW_VAL\" 'BEGIN {print val / 1000}')",
  '    fi',
  '    ',
  "    CUSTOM_COST=$(awk -v creds=\"$CREDITS\" 'BEGIN {printf \"%.2f\", creds * 0.04}')",
  '    echo "Codex: \\$${CUSTOM_COST}"',
  '  else',
  '    echo "Codex: Unavail"',
  '  fi',
  'else',
  '  echo "Codex: Unavail"',
  'fi',
  'EOF',
  'chmod +x ~/.local/bin/codex-cost.sh',
  '',
  '# Add this to ~/.tmux.conf',
  'set -g status-right "#[fg=green]#( ~/.local/bin/codex-cost.sh )"',
].join('\n')

const ADAM_CODEX_STATUS_LINE = [
  'current-dir',
  'git-branch',
  'model-with-reasoning',
  'context-remaining',
  'used-tokens',
  'total-input-tokens',
  'total-output-tokens',
]

const CODEX_STATUSLINE_INSTRUCTIONS = [
  '# ~/.codex/config.toml',
  '[desktop]',
  'show-context-window-usage = true',
  '',
  '[tui]',
  `status_line = [${ADAM_CODEX_STATUS_LINE.map(item => `"${item}"`).join(', ')}]`,
  'status_line_use_colors = true',
].join('\n')

function spendMonitoringInsight() {
  const spend = config.spend_monitoring || {}
  const status = spend.monitoring_api_spend
    ? 'detected'
    : spend.codexbar_available
      ? 'codexbar installed'
      : 'not detected'
  const details = [
    spend.codexbar_available ? 'codexbar is available on PATH' : 'codexbar was not found on PATH',
    spend.codex_cost_script_exists ? `cost script exists at ${scrub(spend.codex_cost_script_path)}` : `cost script missing at ${scrub(spend.codex_cost_script_path || '~/.local/bin/codex-cost.sh')}`,
    spend.codex_status_line_mentions_spend ? 'Codex status line mentions spend/cost' : 'Codex status line does not mention spend/cost',
  ]
  return `
    <div class="panel">
      <strong>API spend monitor: ${esc(status)}</strong>
      <p class="mut">${details.map(esc).join(' · ')}</p>
      <p>For real-time enterprise overage tracking inside Tmux, install <code>codexbar</code> and scale token output to Apollo's custom enterprise overage rate: <code>$0.04</code> per credit, where <code>1 credit = 1K tokens</code>.</p>
      <pre><code>${esc(CODEXBAR_TMUX_INSTRUCTIONS)}</code></pre>
    </div>`
}

function statuslineInsight() {
  const tui = config.feature_flags?.tui || {}
  const desktop = config.feature_flags?.desktop || {}
  const currentItems = Array.isArray(tui.status_line) ? tui.status_line : []
  const configuredCore = ADAM_CODEX_STATUS_LINE.every((item, i) => currentItems[i] === item)
  const extraItems = currentItems.slice(ADAM_CODEX_STATUS_LINE.length)
  const matchesColors = tui.status_line_use_colors === true
  const matchesDesktop = desktop['show-context-window-usage'] === true
  const status = configuredCore && matchesColors && matchesDesktop
    ? extraItems.length ? 'detected with extra items' : 'detected'
    : 'not detected'
  const legacyItems = extraItems.filter(item => ['five-hour-limit', 'weekly-limit'].includes(item))
  const extraNote = extraItems.length
    ? ` Current config also has extra status items not included in the recommended Apollo enterprise snippet: ${extraItems.join(', ')}.${legacyItems.length ? ` Remove ${legacyItems.join(', ')} because those limits do not currently apply to Apollo enterprise tracking.` : ''}`
    : ''
  return `
    <div class="panel">
      <strong>Codex status line: ${esc(status)}</strong>
      <p class="mut">Recommended setup mirrors the Apollo-style footer order: directory, branch, model/reasoning, context remaining, and token counters.${esc(extraNote)}</p>
      <p>Use Codex's supported built-in status-line items for token visibility, then use the Tmux <code>codexbar</code> setup above for real-time enterprise credit-cost tracking.</p>
      <pre><code>${esc(CODEX_STATUSLINE_INSTRUCTIONS)}</code></pre>
    </div>`
}

const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Codex Insights — ${esc(new Date(data.generated_at).toLocaleDateString())}</title>
<style>
:root{--bg:#0e1116;--panel:#161b22;--panel2:#1c222b;--line:#2a313c;--ink:#e6edf3;--mut:#9aa7b4;--blue:#6cb6ff;--green:#3fb950;--warn:#d29922;--bad:#f85149}
*{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
.wrap{max-width:960px;margin:0 auto;padding:32px 24px 64px} h1{font-size:24px;margin:0} .sub,.mut{color:var(--mut);font-size:13px}
h2{font-size:13px;text-transform:uppercase;letter-spacing:.08em;color:var(--mut);border-bottom:1px solid var(--line);padding-bottom:8px;margin:34px 0 14px}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin:20px 0}.stat,.rec,.panel,.row{background:var(--panel);border:1px solid var(--line);border-radius:10px}
.stat{padding:12px 14px}.stat-v{font-size:20px;font-weight:700}.stat-k{font-size:11px;color:var(--mut);text-transform:uppercase;letter-spacing:.05em}
.panel{padding:15px 17px;margin:10px 0}.row{display:grid;grid-template-columns:1fr auto;gap:18px;padding:13px 15px;margin:9px 0}.num{font-weight:700;color:var(--blue);font-variant-numeric:tabular-nums}
.badge{display:inline-block;margin:4px 5px 0 0;padding:2px 8px;border-radius:999px;background:#303743;color:var(--mut);font-size:11px;font-weight:700}.badge.warn{background:rgba(210,153,34,.16);color:var(--warn)}.badge.bad{background:rgba(248,81,73,.16);color:var(--bad)}.badge.blue{background:rgba(108,182,255,.14);color:var(--blue)}.badge.good{background:rgba(63,185,80,.16);color:var(--green)}
.badge .dim{font-weight:600;opacity:.62;font-size:9.5px;text-transform:uppercase;letter-spacing:.04em;margin-right:5px}
.legend{color:var(--mut);font-size:12px;margin:-4px 0 14px}.legend b{color:var(--ink);font-weight:600}
.chip{display:inline-block;padding:0 7px;border-radius:10px;font-size:11px;font-weight:600;color:#06121f}.chip.good{background:var(--green)}.chip.warn{background:var(--warn)}.chip.bad{background:var(--bad)}
.weeks{margin:8px 0 4px}.wk{margin-bottom:13px}.wk-top{display:flex;align-items:center;gap:11px}.wk-label{width:52px;font-size:12px;color:var(--mut);font-variant-numeric:tabular-nums;flex:none}
.wk-track{flex:1;height:18px;background:var(--panel);border:1px solid var(--line);border-radius:5px;overflow:hidden;display:flex}.seg{height:100%;display:inline-block}.seg.good{background:var(--green)}.seg.warn{background:var(--warn)}.seg.bad{background:var(--bad)}
.wk-cost{width:72px;text-align:right;font-weight:700;font-variant-numeric:tabular-nums;color:var(--blue);font-size:13px;flex:none}.wk-head{margin:5px 0 0 63px;color:var(--mut);font-size:13px}
.lead{background:linear-gradient(180deg,var(--panel2),var(--panel));border:1px solid var(--line);border-left:3px solid var(--blue);border-radius:10px;padding:16px 18px;margin:0 0 14px;font-size:15px}.lead.mut{color:var(--mut)}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:13px 16px;margin-bottom:10px}.card-head{display:flex;align-items:center;gap:10px;flex-wrap:wrap}.cost{font-weight:700;font-variant-numeric:tabular-nums;color:var(--blue);font-size:15px}.sid{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;color:var(--mut)}.badges{margin-left:auto;display:flex;gap:5px;flex-wrap:wrap}.verdict{margin:9px 0 0;color:var(--ink)}
.rec{padding:14px 16px;margin:10px 0}.rec-head{display:flex;gap:9px;align-items:center;flex-wrap:wrap}.pill{display:inline-flex;align-items:center;justify-content:center;width:21px;height:21px;border-radius:6px;background:var(--blue);color:#06121f;font-weight:800;font-size:12px}
pre{background:#0b0f14;border:1px solid var(--line);border-radius:8px;overflow:auto;padding:12px 13px} code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px}
.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}.foot{margin-top:28px;padding-top:14px;border-top:1px solid var(--line);color:var(--mut);font-family:ui-monospace,Menlo,monospace;font-size:12px}
table{width:100%;border-collapse:collapse;margin:10px 0;background:#0f141b;border:1px solid var(--line)}th,td{text-align:left;border-bottom:1px solid var(--line);padding:8px 9px;vertical-align:top}th{color:var(--mut);font-size:11px;text-transform:uppercase;letter-spacing:.04em}
a{color:var(--blue)}
</style>
</head>
<body><div class="wrap">
<h1>Codex Insights</h1>
<p class="sub">generated ${esc(data.generated_at)} · since ${esc(data.since)} · ${esc(data.source_confidence)}</p>

<div class="stats">
${stat('Exact tokens', fmt(data.totals.total_tokens))}
${stat('Est. credits', fmt(data.totals.credits ?? Math.round((data.totals.total_tokens || 0) / 1000)))}
${stat('Sessions analyzed', data.snapshot.sessions_found)}
${stat('Top sessions shown', data.snapshot.sessions_reported)}
${stat('Reasoning tokens', fmt(data.totals.reasoning_output_tokens))}
${stat('Cache share', pct(data.totals.cached_input_tokens, data.totals.input_tokens + data.totals.cached_input_tokens))}
</div>

<h2>Week by Week — burn &amp; churn over time</h2>
<p class="legend">Bar length ∝ that week's exact tokens; color is the deterministic efficiency split —
  <span class="chip good">lean</span> <span class="chip warn">loose</span> <span class="chip bad">thrashy</span>.
  Credits use Apollo's convention (1 credit ≈ 1K tokens); Codex does not expose exact per-session dollars.</p>
<div class="weeks">${weekChart || '<p class="mut">No weekly data in this window.</p>'}</div>

<h2>Burn vs Output — was the spend worth it?</h2>
${burn.overall_verdict ? `<div class="lead">${esc(scrub(burn.overall_verdict))}</div>` : `<div class="lead mut">ROI and outcome were not judged in this run. Efficiency below is computed deterministically; run the judgment step (see SKILL.md) to add per-session ROI/outcome and an overall verdict.</div>`}
<p class="legend">Each session carries three orthogonal dimensions:
  <b>ROI</b> (was the price fair for what resulted — worth&nbsp;it / overpriced / wasted) and
  <b>outcome</b> (did durable work result — landed / partial / dropped) are <i>judged</i> against
  evidence; <b>efficiency</b> (how much spend was avoidable churn — lean / loose / thrashy) is
  <i>computed</i> from cold-reingest / large-output / tool-loop / reasoning-spin signals, not judged.
  They can disagree (e.g. landed but overpriced).</p>
${burnRows || '<p class="mut">No high-token sessions in this window.</p>'}

<h2>Where Tokens Went</h2>
<div class="panel">The largest sessions are listed below. Findings are based on exact Codex <code>token_count</code> events; optional <code>ccusage</code> data is treated as a cross-check.</div>
${topSessions || '<div class="panel">No exact Codex sessions found in this window.</div>'}

<h2>Context Load</h2>
<div class="cols">
  <div class="panel"><strong>Prompt input shape</strong><ul>${promptBits}</ul></div>
  <div class="panel"><strong>Largest context flags</strong><ul>${Object.entries(data.flags || {}).map(([k,v]) => `<li>${esc(k)}: ${v}</li>`).join('') || '<li>No material flags detected.</li>'}</ul></div>
</div>

<h2>MCP and Plugin Surface</h2>
<div class="panel">
  <strong>${mcpAudit.enabled_global.length} enabled global MCPs</strong>
  ${mcpTable(mcpAudit.enabled_global, 'No enabled global MCPs found in parsed config.')}
  <strong>${mcpAudit.disabled_global.length} disabled global MCPs</strong>
  ${mcpTable(mcpAudit.disabled_global, 'No disabled global MCPs found in parsed config.')}
  <strong>${mcpAudit.project_scoped.length} project-scoped MCP entries</strong>
  ${mcpTable(mcpAudit.project_scoped, 'No project-scoped MCP overrides found under trusted project configs.')}
  <strong>Runtime verification</strong>
  ${runtimeMcpBlock(mcpAudit.runtime_verification)}
  ${(mcpAudit.broad_global_flags || []).length ? `<strong>Broad global tools to consider scoping</strong><ul>${mcpAudit.broad_global_flags.map(flag => `<li><code>${esc(flag.name)}</code>: ${esc(flag.reason)}</li>`).join('')}</ul>` : ''}
  <strong>${pluginEntries.filter(p => p.enabled).length} enabled plugins</strong>
  <p>${pluginList || 'None found'}</p>
</div>

<h2>Project Scope Audit</h2>
<div class="panel">
  <p class="mut">Project <code>.codex/config.toml</code> files only load for trusted projects. This audit parses trusted entries under global <code>[projects]</code>, then reads project-local config only when the project path exists.</p>
  <strong>${(config.project_entries || []).filter(project => project.trusted).length} trusted projects · ${(config.project_configs || []).length} with project config · ${(config.stale_project_entries || []).length} stale · ${(config.duplicate_project_entries || []).length} duplicate</strong>
  ${projectRows([...(config.stale_project_entries || []), ...(config.duplicate_project_entries || [])], 'No stale or duplicate project entries found.')}
</div>

<h2>Project Split Recommendations</h2>
<div class="panel">
  <p>Prefer project-local MCP config when a tool is only useful for a narrow workflow.</p>
  <pre><code>${esc(scrub((data.recommendations || []).find(r => r.mode === 'Project Scope')?.artifact || 'No project-scope snippet generated.'))}</code></pre>
</div>

<h2>How to Configure This</h2>
<div class="panel">
  <ul>
    <li><a href="https://developers.openai.com/codex/config-advanced#project-config-files-codexconfigtoml">Project config files</a>: project <code>.codex/config.toml</code> only loads for trusted projects.</li>
    <li><a href="https://developers.openai.com/codex/mcp">MCP config</a>: define MCP servers globally or in scoped project config.</li>
    <li><a href="https://developers.openai.com/codex/plugins">Plugins</a>: enable installable skills, tools, apps, and runtime bundles.</li>
    <li><a href="https://developers.openai.com/codex/concepts/customization">Customization overview</a>: choose the smallest durable surface for the behavior.</li>
  </ul>
</div>

<h2>Insights / Suggestions</h2>
${spendMonitoringInsight()}
${statuslineInsight()}
${durableMemoryInsight()}
${skillHygieneInsight()}
${mcpAttributionInsight()}

<h2>Measured Action Plan</h2>
<div class="panel">${actionTable()}</div>
${contextResetDiscipline()}

<h2>Workflow Rules</h2>
<div class="panel">${workflowRules()}</div>

<h2>Paste-Ready Changes</h2>
${recs || '<div class="panel">No recommendations generated.</div>'}

<h2>Other Context-Reduction Moves</h2>
<div class="panel">${contextReductionMoves()}</div>

<h2>Implementation Checklist</h2>
<div class="panel">
  <ul>
    <li>Use <code>codex -p lean</code> for small local code, search, shell, lint, and report-rendering sessions.</li>
    <li>Use the default full-power profile when the work genuinely needs connectors, incidents context, docs, or architecture judgment.</li>
    <li>Before switching topics, save a compact handoff or start fresh from a short Markdown file.</li>
    <li>Keep this report script deterministic; add new checks as scripts rather than asking the model to remember more.</li>
  </ul>
</div>

${footer ? `<div class="foot">${esc(footer)}</div>` : ''}
</div></body></html>`

fs.writeFileSync(out, html)
console.log(out)
