#!/usr/bin/env node
/* eslint-disable no-console */

import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { esc, fmt } from './html_utils.mjs'

const argv = process.argv.slice(2)
const input = argv.find(a => !a.startsWith('--')) || '/tmp/codex-insights/compact.json'
const flag = (name, dflt = null) => {
  const i = argv.indexOf(name)
  if (i === -1) return dflt
  const v = argv[i + 1]
  return v === undefined || v.startsWith('--') ? true : v
}

const HOME = os.homedir()
const today = new Date().toISOString().slice(0, 10)
const report = flag('--report', path.join(HOME, '.codex', 'codex-insights', 'reports', `report-${today}.html`))
const siteDir = flag('--site-dir', path.join(HOME, '.codex', 'codex-insights', 'site'))
const ledger = flag('--ledger', '/tmp/codex-insights/source-ledger.md')
const includeSessionNames = argv.includes('--include-session-names')

const data = JSON.parse(fs.readFileSync(input, 'utf8'))
const ledgerText = fs.existsSync(ledger) ? fs.readFileSync(ledger, 'utf8') : '# Source Ledger\n\nUnavailable.\n'
const publicData = buildPublicData(data, { includeSessionNames })
const reportExists = fs.existsSync(report)

const publicDir = path.join(siteDir, 'public')
const dataDir = path.join(publicDir, 'data')
const openaiDir = path.join(siteDir, '.openai')
fs.mkdirSync(dataDir, { recursive: true })
fs.mkdirSync(openaiDir, { recursive: true })

writeIfMissing(path.join(openaiDir, 'hosting.json'), `${JSON.stringify({ d1: null, r2: null }, null, 2)}\n`)
fs.writeFileSync(path.join(publicDir, 'index.html'), renderPublicIndex(publicData))
fs.writeFileSync(path.join(publicDir, 'source-ledger.md'), scrubString(ledgerText))
fs.writeFileSync(path.join(dataDir, 'compact.json'), `${JSON.stringify(publicData, null, 2)}\n`)

writeIfChanged(path.join(siteDir, 'package.json'), `${JSON.stringify({
  private: true,
  type: 'module',
  scripts: {
    build: 'node build.mjs',
  },
}, null, 2)}\n`)

writeIfChanged(path.join(siteDir, 'build.mjs'), buildScript())

console.log(`Codex Insights site bundle: ${siteDir}`)
console.log(`Report: ${path.join(publicDir, 'index.html')}`)
console.log(`Private report input: ${report}${reportExists ? '' : ' (not found)'}`)
console.log(`Data: ${path.join(dataDir, 'compact.json')}`)

function writeIfMissing(file, text) {
  if (!fs.existsSync(file)) fs.writeFileSync(file, text)
}

function writeIfChanged(file, text) {
  if (!fs.existsSync(file) || fs.readFileSync(file, 'utf8') !== text) fs.writeFileSync(file, text)
}

function scrubString(value) {
  return String(value ?? '').replaceAll(HOME, '~')
}

function scrubValue(value, options = {}) {
  if (Array.isArray(value)) return value.map(item => scrubValue(item, options))
  if (value && typeof value === 'object') {
    const omitted = new Set([
      'final_message',
      'token_history',
      'total_token_usage',
      'last_token_usage',
      'file',
      'cwd',
      'config_path',
      'lean_profile_path',
      'workdir',
      'path',
      'artifact',
    ])
    if (!options.includeSessionNames) omitted.add('thread_name')
    return Object.fromEntries(Object.entries(value)
      .filter(([key]) => !omitted.has(key))
      .map(([key, child]) => [key, scrubValue(child, options)]))
  }
  if (typeof value === 'string') return scrubString(value)
  return value
}

function publicSession(session, index, options) {
  const safe = scrubValue(session, options)
  delete safe.id
  if (options.includeSessionNames && session.thread_name) safe.label = scrubString(session.thread_name)
  else safe.label = `Session ${index + 1}`
  return safe
}

function buildPublicData(source, options) {
  const safe = scrubValue(source, options)
  safe.sessions = (source.sessions || []).map((session, index) => publicSession(session, index, options))
  if (safe.config) {
    delete safe.config.config_path
    delete safe.config.lean_profile_path
  }
  safe.public_bundle = {
    generated_at: source.generated_at,
    includes_session_names: Boolean(options.includeSessionNames),
    privacy: options.includeSessionNames
      ? 'Public bundle includes session names because --include-session-names was passed.'
      : 'Public bundle omits session names, raw messages, token histories, full token payloads, and sensitive local paths.',
  }
  return safe
}

function renderPublicIndex(safe) {
  const rows = (safe.sessions || []).map(session => `
    <tr>
      <td>${esc(session.label)}</td>
      <td>${esc(fmt(session.total_tokens))}</td>
      <td>${esc(session.window_basis || 'exact')}</td>
      <td>${esc((session.flags || []).map(flag => flag.label).join(', ') || 'none')}</td>
    </tr>`).join('')
  const recs = (safe.recommendations || []).slice(0, 5).map(rec => `
    <li><strong>${esc(rec.title)}</strong><br><span>${esc(rec.rationale)}</span></li>`).join('')
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Codex Insights</title>
<style>
body{margin:0;background:#0f1115;color:#e7edf3;font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
main{max-width:960px;margin:0 auto;padding:32px 20px 60px}
h1{font-size:26px;margin:0 0 4px} h2{font-size:13px;text-transform:uppercase;letter-spacing:.06em;color:#9aa8b7;margin-top:30px}
.mut{color:#9aa8b7}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:18px 0}
.card{border:1px solid #28313d;background:#171d25;border-radius:8px;padding:13px 14px}.value{font-size:22px;font-weight:750}
table{width:100%;border-collapse:collapse;border:1px solid #28313d;background:#171d25}th,td{text-align:left;border-bottom:1px solid #28313d;padding:10px 12px;vertical-align:top}th{color:#9aa8b7;font-size:12px}
li{margin:10px 0} code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
</style>
</head>
<body><main>
<h1>Codex Insights</h1>
<p class="mut">Generated ${esc(safe.generated_at)} from ${esc(safe.source_confidence)}. ${esc(safe.public_bundle.privacy)}</p>
<div class="grid">
  <div class="card"><div class="value">${esc(fmt(safe.totals?.total_tokens))}</div><div class="mut">Exact tokens</div></div>
  <div class="card"><div class="value">${esc(safe.snapshot?.sessions_found || 0)}</div><div class="mut">Sessions found</div></div>
  <div class="card"><div class="value">${esc(safe.snapshot?.sessions_reported || 0)}</div><div class="mut">Sessions reported</div></div>
  <div class="card"><div class="value">${esc(fmt(safe.totals?.reasoning_output_tokens))}</div><div class="mut">Reasoning tokens</div></div>
</div>
<h2>Recommendations</h2>
<ol>${recs || '<li>No material recommendations generated.</li>'}</ol>
<h2>Memory Depth</h2>
<p class="mut">Future reports will be more detailed if a Karpathy LLM Wiki memory system is set up. Use the beta <code>/apollo-eng:memory-setup</code> skill to set this up, then rerun this report after Codex has richer durable context to inspect.</p>
<h2>Reported Sessions</h2>
<table><thead><tr><th>Session</th><th>Tokens</th><th>Basis</th><th>Flags</th></tr></thead><tbody>${rows || '<tr><td colspan="4">No sessions reported.</td></tr>'}</tbody></table>
<h2>Privacy</h2>
<p class="mut">The private local report path is intentionally omitted from this bundle. This bundle uses safer summary data and does not include raw messages, token histories, full token payloads, or sensitive local paths.</p>
</main></body></html>
`
}

function buildScript() {
  return `#!/usr/bin/env node
import fs from 'node:fs'
import path from 'node:path'

const root = process.cwd()
const publicDir = path.join(root, 'public')
const distDir = path.join(root, 'dist')
const clientDir = path.join(distDir, 'client')
fs.rmSync(distDir, { recursive: true, force: true })
copyDir(publicDir, clientDir)
fs.mkdirSync(path.join(distDir, 'server'), { recursive: true })
fs.mkdirSync(path.join(distDir, '.openai'), { recursive: true })
fs.copyFileSync(path.join(root, '.openai', 'hosting.json'), path.join(distDir, '.openai', 'hosting.json'))

const files = {}
for (const file of walk(publicDir)) {
  const rel = '/' + path.relative(publicDir, file).split(path.sep).join('/')
  files[rel === '/index.html' ? '/' : rel] = {
    body: fs.readFileSync(file, 'utf8'),
    type: contentType(file),
  }
}

fs.writeFileSync(path.join(distDir, 'server', 'index.js'), \`const files = \${JSON.stringify(files)};

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const key = files[url.pathname] ? url.pathname : '/';
    const file = files[key] || files['/'];
    return new Response(file.body, {
      headers: {
        'content-type': file.type,
        'cache-control': key === '/' ? 'no-store' : 'public, max-age=60',
      },
    });
  },
};
\`)

console.log('Built ' + distDir)

function copyDir(src, dest) {
  fs.mkdirSync(dest, { recursive: true })
  for (const ent of fs.readdirSync(src, { withFileTypes: true })) {
    const sp = path.join(src, ent.name)
    const dp = path.join(dest, ent.name)
    if (ent.isDirectory()) copyDir(sp, dp)
    else fs.copyFileSync(sp, dp)
  }
}

function walk(dir) {
  const out = []
  for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, ent.name)
    if (ent.isDirectory()) out.push(...walk(p))
    else out.push(p)
  }
  return out
}

function contentType(file) {
  if (file.endsWith('.html')) return 'text/html; charset=utf-8'
  if (file.endsWith('.json')) return 'application/json; charset=utf-8'
  if (file.endsWith('.md')) return 'text/markdown; charset=utf-8'
  return 'text/plain; charset=utf-8'
}
`
}
