#!/usr/bin/env node
/* eslint-disable no-console */

import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'

const argv = process.argv.slice(2)
const input = argv.find(a => !a.startsWith('--')) || '/tmp/codex-insights/compact.json'
const flag = name => {
  const i = argv.indexOf(name)
  return i === -1 ? null : argv[i + 1]
}
const hasFlag = name => argv.includes(name)
const report = flag('--report') || ''
const siteDir = flag('--site-dir') || path.join(os.homedir(), '.codex', 'codex-insights', 'site')
const explicitVault = flag('--vault')
const vault = chooseVault(explicitVault, process.env.OBSIDIAN_VAULT || '')

if (hasFlag('--no-obsidian')) {
  console.log('Obsidian disabled; skipped update.')
  process.exit(0)
}
if (!vault) {
  console.log('Obsidian not configured; skipped update. Pass --vault PATH or set OBSIDIAN_VAULT to enable.')
  process.exit(0)
}

const data = JSON.parse(fs.readFileSync(input, 'utf8'))

const wikiDir = path.join(vault, 'wiki', 'ai-tooling')
const projectPath = path.join(wikiDir, 'token-efficiency-project.md')
const projectsPath = path.join(vault, 'memory', 'projects.md')
fs.mkdirSync(wikiDir, { recursive: true })
fs.mkdirSync(path.dirname(projectsPath), { recursive: true })

const start = '<!-- codex-insights:start -->'
const end = '<!-- codex-insights:end -->'

function replaceBlock(text, block) {
  const re = new RegExp(`${escapeRe(start)}[\\s\\S]*?${escapeRe(end)}`)
  const wrapped = `${start}\n${block.trim()}\n${end}`
  if (re.test(text)) return text.replace(re, wrapped)
  return `${text.trim()}\n\n${wrapped}\n`
}

function escapeRe(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function chooseVault(explicit, env) {
  if (explicit) return looksLikeVault(explicit) ? explicit : ''
  if (env) return looksLikeVault(env) ? env : ''
  return ''
}

function looksLikeVault(candidate) {
  try {
    if (!fs.existsSync(candidate) || !fs.statSync(candidate).isDirectory()) return false
    return fs.existsSync(path.join(candidate, 'wiki')) || fs.existsSync(path.join(candidate, 'memory')) || fs.existsSync(path.join(candidate, '.obsidian'))
  } catch {
    return false
  }
}

function fmt(n) {
  n = Number(n || 0)
  if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`
  if (n >= 1000) return `${Math.round(n / 1000)}k`
  return String(n)
}

const recs = (data.recommendations || []).map(r => `- **${r.title}** (${r.mode}): ${r.rationale}`).join('\n')
const top = (data.sessions || []).slice(0, 5).map(s => `- ${fmt(s.total_tokens)} tokens - ${s.thread_name || s.id}`).join('\n')

const projectBlock = `
## Latest Snapshot

- **Generated:** ${data.generated_at}
- **Window:** ${data.since}
- **Measured range:** ${data.actual_range.start || 'unknown'} to ${data.actual_range.end || 'unknown'}
- **Exact Codex sessions:** ${data.snapshot.sessions_found}
- **Exact total tokens:** ${fmt(data.totals.total_tokens)}
- **Reasoning output:** ${fmt(data.totals.reasoning_output_tokens)}
- **MCPs configured:** ${data.config.mcp_servers.length}
- **Plugins enabled:** ${data.config.plugins.length}
- **Latest report:** ${report || 'not provided'}
- **Shareable site bundle:** ${siteDir}

## Usage Mirror

Top measured Codex sessions:

${top || '- No exact sessions found in this window.'}

## Workflow Coach

${recs || '- No material recommendations generated.'}

## Power Modes

- **Full Power:** default Codex config for incidents, docs, cross-system research, and ambiguous work.
- **Lean:** low reasoning, memories off, high-context MCPs disabled for local code/shell tasks.
- **Research:** enable connectors deliberately, capture a short brief, then restart or compact.
- **Intervention:** pick one habit per week; this is a nudge, not a governor.

## References

- [Token Efficiency Assessment DB](https://www.notion.so/apolloio/32fab2b3b496806a8be7cfc6ab5142f0?v=32fab2b3b496803d8f65000ca2f041f4)
- [Claude Code Efficiency Guide](https://www.notion.so/apolloio/The-Claude-Code-Efficiency-Guide-Spend-Less-Get-More-bd57d3e370c64243a9c428529db0882f)
- [ccflare relay](https://github.com/apolloio/ccflare-relay)
- Slack: \`#claude-token-enablement\`
`

let projectText = ''
if (fs.existsSync(projectPath)) projectText = fs.readFileSync(projectPath, 'utf8')
else projectText = `---\ntype: project\nstatus: active\ntopic: ai-tooling\n---\n\n# Token Efficiency Project\n\nA living project for Codex and Claude token visibility, context hygiene, and empowering workflow modes.\n`
fs.writeFileSync(projectPath, replaceBlock(projectText, projectBlock))

let projects = fs.existsSync(projectsPath) ? fs.readFileSync(projectsPath, 'utf8') : '---\ntype: projects\n---\n\n## Active\n\n## Paused\n\n## Completed\n'
if (!projects.includes('[[token-efficiency-project|Token Efficiency]]')) {
  const entry = `\n### [[token-efficiency-project|Token Efficiency]]\n- **Status:** Active\n- **Goal:** Make Codex/Claude token spend visible and controllable through reports, lean modes, and empowering workflow habits.\n- **Latest report:** ${report || 'generated by /apollo-eng:codex-insights'}\n- **Shareable site bundle:** ${siteDir}\n`
  if (/^## Active\s*$/m.test(projects)) projects = projects.replace(/^## Active\s*$/m, `## Active\n${entry}`)
  else projects = `${projects.trim()}\n\n## Active\n${entry}\n`
} else {
  projects = projects.replace(/- \*\*Latest report:\*\* .*/g, `- **Latest report:** ${report || 'generated by /apollo-eng:codex-insights'}`)
  if (/- \*\*Shareable site bundle:\*\* .*/.test(projects)) {
    projects = projects.replace(/- \*\*Shareable site bundle:\*\* .*/g, `- **Shareable site bundle:** ${siteDir}`)
  } else {
    projects = projects.replace(/- \*\*Latest report:\*\* .*/g, `$&\n- **Shareable site bundle:** ${siteDir}`)
  }
}
fs.writeFileSync(projectsPath, projects)

console.log(projectPath)
console.log(projectsPath)
