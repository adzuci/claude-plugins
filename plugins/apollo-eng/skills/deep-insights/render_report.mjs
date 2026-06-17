#!/usr/bin/env node
// render_report.mjs — deterministic HTML renderer for the deep-insights report.
//
// Turns the workflow's structured result ({ one_screen, burn_analysis, team_harness,
// snapshot }) into a single self-contained, decently readable HTML file. No LLM tokens,
// no external assets — the skill audits token spend, so its own report is rendered for free.
//
// Usage:
//   node render_report.mjs <result.json> --out <report.html> \
//        [--footer "<self-cost line>"] [--prev <prev-snapshot.json>]
//   # result.json may also be piped on stdin (omit the positional arg)

import { readFileSync, writeFileSync } from 'node:fs'

// ---- args -------------------------------------------------------------------
const argv = process.argv.slice(2)
function flag(name) {
  const i = argv.indexOf(name)
  return i >= 0 ? argv[i + 1] : undefined
}
const positional = argv.filter((a, i) => !a.startsWith('--') && (i === 0 || !argv[i - 1].startsWith('--')))
const inPath = positional[0]
const outPath = flag('--out') || 'insights-report.html'
const footer = flag('--footer') || ''
const prevPath = flag('--prev')

// ---- load -------------------------------------------------------------------
function loadJSON(p) {
  return JSON.parse(readFileSync(p, 'utf8'))
}
let raw
if (inPath) {
  raw = readFileSync(inPath, 'utf8')
} else {
  raw = readFileSync(0, 'utf8') // stdin
}
const data = JSON.parse(raw)
const burn = data.burn_analysis || { overall_verdict: '', sessions: [] }
const harness = Array.isArray(data.team_harness) ? data.team_harness : []
const snap = data.snapshot || {}
let prev = null
if (prevPath) {
  try { prev = loadJSON(prevPath) } catch { prev = null }
}

// ---- helpers ----------------------------------------------------------------
const esc = (s) =>
  String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')

const money = (n) => (typeof n === 'number' ? `$${n.toFixed(2)}` : esc(n))

// badge tone per dimension value
const TONE = {
  // roi · outcome · efficiency
  'worth-it': 'good', landed: 'good', lean: 'good',
  overpriced: 'warn', partial: 'warn', loose: 'warn',
  wasted: 'bad', dropped: 'bad', thrashy: 'bad',
  unknown: 'mute',
}
const badge = (dim, val) => {
  const v = String(val || 'unknown').toLowerCase()
  const tone = TONE[v] || 'mute'
  return `<span class="badge ${tone}"><span class="dim">${esc(dim)}</span>${esc(v.replace(/-/g, ' '))}</span>`
}

const delta = (cur, was, unit = '') => {
  if (typeof cur !== 'number' || typeof was !== 'number') return ''
  const d = cur - was
  if (Math.abs(d) < 0.005) return `<span class="delta flat">±0</span>`
  const sign = d > 0 ? '▲' : '▼'
  const cls = d > 0 ? 'up' : 'down'
  return `<span class="delta ${cls}">${sign} ${Math.abs(d).toFixed(unit === '$' ? 2 : 1)}${unit}</span>`
}

// ---- sections ---------------------------------------------------------------
const since = snap.since ? String(snap.since).slice(0, 10) : '—'
const date = snap.date || ''
const totalSpend = money(snap.cost_usd)
// opus_share_pct is the $ share (opus_cost_usd / total) — the honest "how much money
// went to Opus". Older snapshots only carried a token share here; fall back gracefully.
const opusShare = typeof snap.opus_share_pct === 'number' ? `${snap.opus_share_pct}%` : '—'
const cacheRead = typeof snap.cache_read_pct === 'number' ? `${snap.cache_read_pct}%` : '—'

const stats = [
  ['Total spend', totalSpend, prev ? delta(snap.cost_usd, prev.cost_usd, '$') : ''],
  ['Sessions', snap.sessions ?? '—', prev ? delta(snap.sessions, prev.sessions) : ''],
  ['Prompts', snap.prompts ?? '—', prev ? delta(snap.prompts, prev.prompts) : ''],
  ['Opus $ share', opusShare, ''],
  ['Cache reads', cacheRead, ''],
]
  .map(
    ([k, v, d]) =>
      `<div class="stat"><div class="stat-v">${esc(v)} ${d}</div><div class="stat-k">${esc(k)}</div></div>`,
  )
  .join('\n')

// ---- weekly burn chart (deterministic, from by_week) -----------------------
// The skill is week-oriented; this chart is the spine. Each week is a horizontal
// bar whose length is proportional to that week's spend and whose color split is
// the deterministic efficiency mix (lean/loose/thrashy). The narrative headline
// per week comes from the synthesis (burn_analysis.weekly).
const weeks = Array.isArray(data.by_week) ? data.by_week : []
const headlineByWeek = {}
for (const w of burn.weekly || []) if (w && w.week) headlineByWeek[w.week] = w.headline
const maxWeekCost = weeks.reduce((m, w) => Math.max(m, w.cost_usd || 0), 0) || 1
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const weekLabel = (wk) => {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(wk || '')
  return m ? `${MONTHS[+m[2] - 1]} ${m[3]}` : esc(wk || '—')
}
const seg = (cost, cls) => {
  const w = ((cost || 0) / maxWeekCost) * 100
  return w > 0
    ? `<span class="seg ${cls}" style="width:${w.toFixed(2)}%" title="${cls} ${money(cost)}"></span>`
    : ''
}
const weekChart = weeks
  .map((w) => {
    const ec = w.efficiency_cost || {}
    const bar = seg(ec.lean, 'good') + seg(ec.loose, 'warn') + seg(ec.thrashy, 'bad')
    const head = headlineByWeek[w.week]
    // The current ISO week is only partly elapsed; flag it so its short bar isn't
    // misread as a real decline. (by_week.partial / days_elapsed set by the workflow.)
    const ip = w.partial
      ? `<span class="wk-ip" title="week in progress — partial total, not comparable to full weeks">in progress · day ${w.days_elapsed || '?'}/7</span>`
      : ''
    return `
    <div class="wk${w.partial ? ' wk-now' : ''}">
      <div class="wk-top">
        <span class="wk-label">${weekLabel(w.week)}</span>
        <span class="wk-track">${bar}</span>
        <span class="wk-cost">${money(w.cost_usd)}${w.partial ? '<sup>*</sup>' : ''}</span>
      </div>
      ${ip ? `<p class="wk-head">${ip}</p>` : ''}
      ${head ? `<p class="wk-head">${esc(head)}</p>` : ''}
    </div>`
  })
  .join('\n')

const burnRows = (burn.sessions || [])
  .map(
    (s) => `
    <div class="card">
      <div class="card-head">
        <span class="cost">${money(s.cost_usd)}</span>
        <span class="sid">${esc(s.session)}</span>
        <span class="badges">${badge('ROI', s.roi)}${badge('outcome', s.outcome)}${badge('efficiency', s.efficiency)}</span>
      </div>
      <p class="verdict">${esc(s.verdict)}</p>
    </div>`,
  )
  .join('\n')

// Avoidable revives — ONLY the unjustified resume/idle cold re-ingests the reviewers flagged
// (justified/unclear ones are deliberately excluded upstream). A per-session cost callout, never a
// /clear recommendation. Absent/empty array → the whole block is omitted from the document.
const revivals = Array.isArray(burn.revivals) ? burn.revivals : []
const revivalRows = revivals
  .map((r) => {
    const cost = typeof r.est_cost_usd === 'number' && r.est_cost_usd > 0 ? `≈${money(r.est_cost_usd)}` : ''
    const toks = typeof r.est_reingest_tokens === 'number' && r.est_reingest_tokens > 0
      ? `${Math.round(r.est_reingest_tokens / 1000)}k cold re-ingest`
      : ''
    const meta = [cost, toks].filter(Boolean).join(' · ')
    return `
    <div class="revive">
      <div class="revive-head">
        <span class="sid">${esc(r.session)}</span>
        ${meta ? `<span class="revive-cost">${esc(meta)}</span>` : ''}
      </div>
      <p class="why">${esc(r.evidence)}</p>
    </div>`
  })
  .join('\n')

const harnessRows = harness
  .map((h, i) => {
    // Every team-harness item is an agent-applicable artifact written to disk — a paste-ready
    // block with a real target_path. (Per-user REPL habits like /clear are deliberately NOT
    // emitted by the workflow: they aren't shippable harness changes.)
    const code = !h.ready_to_apply
      ? ''
      : `<details><summary>paste-ready artifact${h.target_path ? ` → <code>${esc(h.target_path)}</code>` : ''}</summary><pre><button class="copy" onclick="cp(this)">copy</button><code>${esc(h.ready_to_apply)}</code></pre></details>`
    return `
    <div class="rec">
      <div class="rec-head"><span class="num">${i + 1}</span>
        <span class="kind">${esc(h.artifact || 'change')}</span>
        <span class="rec-title">${esc(h.change)}</span>
      </div>
      ${h.rationale ? `<p class="why">${esc(h.rationale)}</p>` : ''}
      ${code}
    </div>`
  })
  .join('\n')

// ---- document ---------------------------------------------------------------
const html = `<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Claude Code Burn Report${date ? ` — ${esc(date)}` : ''}</title>
<style>
:root{
  --bg:#0e1116; --panel:#161b22; --panel2:#1c222b; --line:#2a313c;
  --ink:#e6edf3; --mut:#9aa7b4; --acc:#6cb6ff;
  --good:#3fb950; --warn:#d29922; --bad:#f85149; --mute:#6e7681;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
.wrap{max-width:860px;margin:0 auto;padding:32px 24px 64px}
h1{font-size:22px;margin:0 0 2px;letter-spacing:-.01em}
.sub{color:var(--mut);font-size:13px;margin:0 0 22px}
h2{font-size:13px;text-transform:uppercase;letter-spacing:.08em;color:var(--mut);
  margin:34px 0 14px;padding-bottom:7px;border-bottom:1px solid var(--line)}
.stats{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0 6px}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:10px;
  padding:11px 15px;min-width:120px;flex:1}
.stat-v{font-size:19px;font-weight:600}
.stat-k{font-size:11px;color:var(--mut);text-transform:uppercase;letter-spacing:.05em;margin-top:2px}
.lead{background:linear-gradient(180deg,var(--panel2),var(--panel));border:1px solid var(--line);
  border-left:3px solid var(--acc);border-radius:10px;padding:16px 18px;margin:0 0 18px;font-size:15px}
.weeks{margin:8px 0 4px}
.wk{margin-bottom:13px}
.wk-top{display:flex;align-items:center;gap:11px}
.wk-label{width:52px;font-size:12px;color:var(--mut);font-variant-numeric:tabular-nums;flex:none}
.wk-track{flex:1;height:18px;background:var(--panel);border:1px solid var(--line);border-radius:5px;
  overflow:hidden;display:flex}
.seg{height:100%;display:inline-block}
.seg.good{background:var(--good)} .seg.warn{background:var(--warn)} .seg.bad{background:var(--bad)}
.wk-cost{width:66px;text-align:right;font-weight:700;font-variant-numeric:tabular-nums;
  color:var(--acc);font-size:13px;flex:none}
.wk-head{margin:5px 0 0 63px;color:var(--mut);font-size:13px}
.wk-now .wk-track{border-style:dashed;opacity:.85}
.wk-ip{display:inline-block;font-size:11px;font-weight:600;color:var(--warn);
  border:1px dashed var(--warn);border-radius:9px;padding:0 7px}
.chip{display:inline-block;padding:0 7px;border-radius:10px;font-size:11px;font-weight:600;color:#06121f}
.chip.good{background:var(--good)} .chip.warn{background:var(--warn)} .chip.bad{background:var(--bad)}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;
  padding:13px 16px;margin-bottom:10px}
.card-head{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.cost{font-weight:700;font-variant-numeric:tabular-nums;color:var(--acc);font-size:15px}
.sid{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;color:var(--mut)}
.badges{margin-left:auto;display:flex;gap:5px}
.badge{font-size:11px;padding:2px 9px;border-radius:20px;font-weight:600;text-transform:lowercase;
  display:inline-flex;align-items:baseline;gap:5px}
.badge .dim{font-weight:600;opacity:.62;font-size:9.5px;text-transform:uppercase;letter-spacing:.04em}
.badge.good{background:rgba(63,185,80,.16);color:var(--good)}
.badge.warn{background:rgba(210,153,34,.16);color:var(--warn)}
.badge.bad{background:rgba(248,81,73,.16);color:var(--bad)}
.badge.mute{background:rgba(110,118,129,.18);color:var(--mut)}
.revive{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--warn);
  border-radius:10px;padding:11px 15px;margin-bottom:10px}
.revive-head{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap}
.revive-cost{margin-left:auto;font-weight:700;font-variant-numeric:tabular-nums;color:var(--warn);font-size:13px}
.legend{color:var(--mut);font-size:12px;margin:-4px 0 14px}
.legend b{color:var(--ink);font-weight:600}
.verdict{margin:9px 0 0;color:var(--ink)}
.rec{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:13px 16px;margin-bottom:10px}
.rec-head{display:flex;align-items:baseline;gap:9px;flex-wrap:wrap}
.num{background:var(--acc);color:#06121f;font-weight:700;border-radius:6px;
  width:20px;height:20px;display:inline-flex;align-items:center;justify-content:center;font-size:12px;flex:none}
.kind{font-size:10px;text-transform:uppercase;letter-spacing:.06em;color:var(--mut);
  border:1px solid var(--line);border-radius:5px;padding:1px 6px}
.rec-title{font-weight:600}
.why{margin:8px 0 0;color:var(--mut);font-size:13.5px}
details{margin-top:10px}
summary{cursor:pointer;color:var(--acc);font-size:13px}
summary code{color:var(--mut)}
pre{position:relative;background:#0b0f14;border:1px solid var(--line);border-radius:8px;
  padding:13px 14px;overflow:auto;margin:9px 0 2px}
pre code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px;line-height:1.5;color:#cdd9e5}
.copy{position:absolute;top:7px;right:7px;background:var(--panel2);color:var(--mut);
  border:1px solid var(--line);border-radius:6px;font-size:11px;padding:3px 8px;cursor:pointer}
.copy:hover{color:var(--ink)}
.delta{font-size:12px;font-weight:600}
.delta.up{color:var(--bad)} .delta.down{color:var(--good)} .delta.flat,.delta{color:var(--mut)}
.foot{margin-top:30px;padding-top:14px;border-top:1px solid var(--line);
  color:var(--mut);font-size:12px;font-family:ui-monospace,Menlo,monospace}
code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
</style></head>
<body><div class="wrap">
  <h1>Claude Code Burn Report</h1>
  <p class="sub">window since ${esc(since)}${date ? ` · generated ${esc(date)}` : ''}${prev ? ' · vs previous run' : ' · baseline run, trend starts next time'}</p>

  <div class="stats">${stats}</div>

  <h2>Week by Week — burn &amp; churn over time</h2>
  <p class="legend">Bar length ∝ that week's spend; color is the deterministic efficiency split —
    <span class="chip good">lean</span> <span class="chip warn">loose</span>
    <span class="chip bad">thrashy</span>.</p>
  <div class="weeks">${weekChart || '<p class="why">No weekly data in this window.</p>'}</div>

  <h2>Burn vs Output — was the spend worth it?</h2>
  <div class="lead">${esc(burn.overall_verdict)}</div>
  <p class="legend">Each session carries three orthogonal dimensions:
    <b>ROI</b> (was the price fair for what resulted — worth&nbsp;it / overpriced / wasted) and
    <b>outcome</b> (did durable work result — landed / partial / dropped) are <i>judged</i> by a
    reviewer; <b>efficiency</b> (how much spend was avoidable churn — lean / loose / thrashy) is
    <i>computed</i> from revert/re-read/thrash/cache-break signals, not judged.
    Green = good, amber = mixed, red = weak. They can disagree (e.g. landed but overpriced).</p>
  ${burnRows || '<p class="why">No high-spend sessions in this window.</p>'}
${revivals.length
  ? `
  <h2>Avoidable Revives — cold re-ingest that didn't earn its keep</h2>
  <p class="legend">A long session resumed after its 5-min prompt cache lapsed re-sends its whole
    context cold at full price. That's usually the fair price of needed continuity — these are only the
    cases a reviewer judged the reloaded context went <b>unused</b>. A per-session cost note, not a
    rule against reviving sessions.</p>
  ${revivalRows}
`
  : ''}
  <h2>Team Harness — shippable changes that move the burn needle</h2>
  ${harnessRows || '<p class="why">No material harness changes recommended.</p>'}

  ${footer ? `<div class="foot">${esc(footer)}</div>` : ''}
</div>
<script>
function cp(b){const t=b.parentElement.querySelector('code').innerText;
  navigator.clipboard.writeText(t).then(()=>{b.textContent='copied';setTimeout(()=>b.textContent='copy',1200)})}
</script>
</body></html>`

writeFileSync(outPath, html)
process.stderr.write(`wrote ${outPath} (${html.length} bytes, ${burn.sessions?.length || 0} sessions, ${harness.length} recs)\n`)
process.stdout.write(outPath + '\n')
