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
const footer = flag('--footer') || 'self-cost: unavailable'

const data = JSON.parse(fs.readFileSync(input, 'utf8'))
const siteDir = flag('--site-dir') || path.join(os.homedir(), '.codex', 'codex-insights', 'site')
fs.mkdirSync(path.dirname(out), { recursive: true })

const scrub = s => String(s ?? '').replaceAll(os.homedir(), '~')
const pct = (n, d) => d ? `${Math.round((n / d) * 100)}%` : 'n/a'

const stat = (label, value) => `<div class="stat"><div class="stat-v">${esc(value)}</div><div class="stat-k">${esc(label)}</div></div>`
const badge = (text, tone = 'mut') => `<span class="badge ${tone}">${esc(text)}</span>`

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

const mcpList = (data.config?.mcp_servers || []).map(s => `<code>${esc(s)}</code>`).join(' ')
const pluginList = (data.config?.plugins || []).slice(0, 20).map(s => `<code>${esc(s)}</code>`).join(' ')

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
.badge{display:inline-block;margin:4px 5px 0 0;padding:2px 8px;border-radius:999px;background:#303743;color:var(--mut);font-size:11px;font-weight:700}.badge.warn{background:rgba(210,153,34,.16);color:var(--warn)}.badge.bad{background:rgba(248,81,73,.16);color:var(--bad)}.badge.blue{background:rgba(108,182,255,.14);color:var(--blue)}
.rec{padding:14px 16px;margin:10px 0}.rec-head{display:flex;gap:9px;align-items:center;flex-wrap:wrap}.pill{display:inline-flex;align-items:center;justify-content:center;width:21px;height:21px;border-radius:6px;background:var(--blue);color:#06121f;font-weight:800;font-size:12px}
pre{background:#0b0f14;border:1px solid var(--line);border-radius:8px;overflow:auto;padding:12px 13px} code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px}
.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}.foot{margin-top:28px;padding-top:14px;border-top:1px solid var(--line);color:var(--mut);font-family:ui-monospace,Menlo,monospace;font-size:12px}
</style>
</head>
<body><div class="wrap">
<h1>Codex Insights</h1>
<p class="sub">generated ${esc(data.generated_at)} · since ${esc(data.since)} · ${esc(data.source_confidence)}</p>

<div class="stats">
${stat('Exact tokens', fmt(data.totals.total_tokens))}
${stat('Sessions found', data.snapshot.sessions_found)}
${stat('Reported sessions', data.snapshot.sessions_reported)}
${stat('Reasoning tokens', fmt(data.totals.reasoning_output_tokens))}
${stat('Tool calls', fmt(data.totals.tool_calls))}
${stat('Cache share', pct(data.totals.cached_input_tokens, data.totals.input_tokens + data.totals.cached_input_tokens))}
</div>

<h2>Where Tokens Went</h2>
<div class="panel">The largest sessions are listed below. Findings are based on exact Codex <code>token_count</code> events; optional <code>ccusage</code> data is treated as a cross-check.</div>
${topSessions || '<div class="panel">No exact Codex sessions found in this window.</div>'}

<h2>Context Load</h2>
<div class="cols">
  <div class="panel"><strong>Prompt input shape</strong><ul>${promptBits}</ul></div>
  <div class="panel"><strong>Largest context flags</strong><ul>${Object.entries(data.flags || {}).map(([k,v]) => `<li>${esc(k)}: ${v}</li>`).join('') || '<li>No material flags detected.</li>'}</ul></div>
</div>

<h2>MCP and Plugin Surface</h2>
<div class="panel"><strong>${data.config.mcp_servers.length} MCPs</strong><p>${mcpList || 'None found'}</p><strong>${data.config.plugins.length} plugins</strong><p>${pluginList || 'None found'}</p></div>

<h2>Two-Agent Intervention</h2>
<div class="cols">
  <div class="panel"><strong>Usage Mirror</strong><p>You are using a powerful setup. The mirror is here to show where the weight sits: exact session tokens, context load, MCP surface, and repeated tool output. No moralizing, just visibility.</p></div>
  <div class="panel"><strong>Workflow Coach</strong><p>More range, less drag. Keep the full setup for broad, ambiguous work; add a lean path for local code, shell, and small edits so tokens buy judgment instead of re-reading setup.</p></div>
</div>

<h2>Power Modes</h2>
<div class="cols">
  <div class="panel"><strong>Full Power</strong><p>Default config, all MCPs, memories on. Use for incidents, cross-system questions, docs, and ambiguous product work.</p></div>
  <div class="panel"><strong>Lean</strong><p>Low reasoning, high-context MCPs off, memories off. Use for local code edits, shell, and focused reviews.</p></div>
  <div class="panel"><strong>Research</strong><p>Turn connectors/web/docs on deliberately, capture a short brief, then restart or compact.</p></div>
  <div class="panel"><strong>Intervention</strong><p>Pick one habit per week from this report. This is a nudge, not a governor.</p></div>
</div>

<h2>Paste-Ready Changes</h2>
${recs || '<div class="panel">No recommendations generated.</div>'}

<h2>Memory Depth</h2>
<div class="panel">
  <p>Future reports will be more detailed if a Karpathy LLM Wiki memory system is set up. Use the beta <code>/apollo-eng:memory-setup</code> skill to set this up, then rerun this report after Codex has richer durable context to inspect.</p>
</div>

<h2>Shareable Codex Site</h2>
<div class="panel">
  <p>Build a self-contained Codex Sites-ready bundle from this report and compact JSON. Obsidian is optional; the site bundle is the portable output for users who do not keep a vault.</p>
  <pre><code>node &lt;skill-dir&gt;/scripts/build_site_bundle.mjs ${esc(scrub(input))} --report ${esc(scrub(out))} --site-dir ${esc(scrub(siteDir))}
cd ${esc(scrub(siteDir))}
npm run build</code></pre>
</div>

<h2>Implementation Checklist</h2>
<div class="panel">
  <ul>
    <li>Use <code>codex -p lean</code> for small local code, search, shell, lint, and report-rendering sessions.</li>
    <li>Use the default full-power profile when the work genuinely needs connectors, incidents context, docs, or architecture judgment.</li>
    <li>Before switching topics, save a compact handoff or start fresh from a short Markdown file.</li>
    <li>Keep this report script deterministic; add new checks as scripts rather than asking the model to remember more.</li>
  </ul>
</div>

<div class="foot">${esc(footer)}</div>
</div></body></html>`

fs.writeFileSync(out, html)
console.log(out)
