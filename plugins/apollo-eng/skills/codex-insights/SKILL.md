---
name: codex-insights
description: Analyze local Codex token usage and generate a private HTML efficiency report.
disable-model-invocation: true
---

# /codex-insights — Codex Session Analysis

If this skill is running in Claude Code, stop immediately and respond exactly:
"This skill is only for Codex. Run `/apollo-eng:deep-insights` instead."

Manual invocation only (`disable-model-invocation: true`). Run a local, deterministic Codex usage
review with arguments like `--since 7d`, `--sessions 20`, `--site-dir PATH`, `--vault PATH`,
`--no-obsidian`, `--no-site`, `--open`, and `--include-session-names`. Obsidian is optional and
opt-in. Treat this as an empowering
intervention: show the user where tokens are going, generate a private HTML report, optionally build a
local Codex Sites-ready bundle, then offer more capable operating modes instead of restrictions.

## Usage

```text
/apollo-eng:codex-insights [--since 7d|24h|30d|all|YYYY-MM-DD] [--sessions N] [--site-dir PATH] [--vault PATH] [--no-site] [--no-obsidian] [--open] [--include-session-names]
```

This skill is Codex only. It expects shell/file access for local Codex logs. Claude Code users should
run `/apollo-eng:deep-insights` instead.

## Workflow

1. Parse `$ARGUMENTS`.
   - `--since`: default `7d`; accepts `24h`, `7d`, `30d`, ISO date, or `all`.
   - `--sessions N`: cap the highest-token sessions included in the detailed table.
   - `--site-dir PATH`: override the shareable Codex Sites bundle directory.
   - `--vault PATH`: opt into Obsidian updates for this vault.
   - `--no-site`: skip the Codex Sites bundle.
   - `--no-obsidian`: force-disable vault updates, even if `OBSIDIAN_VAULT` is set.
   - `--open`: open the generated HTML report.
   - `--include-session-names`: knowingly include thread/session titles in the public site bundle.
1. Run the deterministic enumerator:

```sh
node <skill-dir>/scripts/enumerate_codex_sessions.mjs --since 7d --sessions 20
```

It writes `/tmp/codex-insights/compact.json` and `/tmp/codex-insights/source-ledger.md`. It reads `~/.codex/sessions`, `~/.codex/archived_sessions`, and `~/.codex/session_index.jsonl`; exact `token_count` events are the source of truth. It also parses `~/.codex/config.toml`, trusted project entries, project-local `.codex/config.toml` files when present, MCP/plugin state, and feature flags that affect context/tool surface. If safe and available, it captures `codex mcp list` as runtime verification and labels it separately from config parsing. If `ccusage` is installed, the enumerator also captures `ccusage codex daily/weekly/session --json` as a cross-check.

1. Render the report:

```sh
OUT=~/.codex/codex-insights/reports/report-$(date +%F).html
node <skill-dir>/scripts/render_report.mjs /tmp/codex-insights/compact.json --out "$OUT"
```

The report is self-contained HTML with no external assets. It may include scrubbed local session
detail for the current user. It includes: Where Tokens Went, Context Load, MCP and Plugin Surface,
Project Scope Audit, Project Split Recommendations, How to Configure This, Insights / Suggestions,
Skill Surface Hygiene, MCP Credit Attribution, Measured Action Plan, Workflow Rules, Paste-Ready
Changes, Other Context-Reduction Moves, and the Implementation Checklist.

1. Unless `--no-site` was passed, build a local Codex Sites-ready bundle:

```sh
node <skill-dir>/scripts/build_site_bundle.mjs /tmp/codex-insights/compact.json --report "$OUT"
```

This writes `~/.codex/codex-insights/site/` by default with `.openai/hosting.json`, `package.json`,
`build.mjs`, `public/index.html`, `public/data/compact.json`, and `public/source-ledger.md`. Run
`npm run build` in that directory to produce `dist/client` and `dist/server/index.js`.

Keep Sites local-only by default. Do not save or deploy with Sites unless the user explicitly asks.
The site bundle is public-safer than the local HTML: it omits raw messages, token histories, full token
payloads, sensitive path details, and thread/session titles unless `--include-session-names` was
passed.

1. Persist the snapshot:

```sh
mkdir -p ~/.codex/codex-insights
jq -c '.snapshot' /tmp/codex-insights/compact.json >> ~/.codex/codex-insights/history.jsonl
```

1. Optionally update an Obsidian vault only when explicitly configured. If `--no-obsidian` was passed,
   or neither `--vault` nor `OBSIDIAN_VAULT` points to a valid vault, do not run this step and report
   `Obsidian: not configured`.

```sh
node <skill-dir>/scripts/update_obsidian_project.mjs /tmp/codex-insights/compact.json --report "$OUT"
```

This creates or updates `wiki/ai-tooling/token-efficiency-project.md` and adds an Active project link
in `memory/projects.md` without clobbering unrelated content. Obsidian updates only run when `--vault`
points to a valid vault or `OBSIDIAN_VAULT` points to a valid vault.

1. If `--open` was passed, open the report with `open "$OUT"` on macOS.

## Interpretation Rules

- Prefer measured facts over advice. If a field is missing, say it is missing.
- Label `ccusage` as a cross-check, not the source of truth, when exact Codex `token_count` events are present.
- Treat parsed config and runtime MCP verification as separate evidence. If they disagree, say runtime reflects what this Codex build actually loaded for the current project.
- Prefer project-local `.codex/config.toml` over global MCP enablement when a tool is only useful for a narrow workflow. Project-local config only loads for trusted projects.
- For API spend monitoring, check whether `codexbar` or the local cost script exists, but do not
  inspect Tmux config or report Tmux integration as missing. Always provide the paste-ready Tmux line
  as setup guidance.
- Recommend the Apollo-style Codex status line using supported built-ins that apply to Apollo currently: current directory, git branch, model/reasoning, context remaining, and token counters.
- Check for unused skills in the measured window. For specialized skills that were not explicitly
  invoked, suggest `disable-model-invocation: true` and remind users to call them with `$skill` or
  `$plugin:skill` only when the skill matches the task.
- Suggest `/usage` for current token/credit visibility and `/status` for current session/model/runtime
  status when those checks would help interpret the report.
- Do not claim exact credit usage per MCP. Codex logs expose exact session-level token counts; MCP
  attribution is only an estimate from MCP call counts and session-level tool-output tokens unless
  additional instrumentation is available.
- Keep findings material. Do not report tiny token amounts or expected setup overhead as problems.
- Frame recommendations as measured workflow moves: use full power when connectors and context are
  needed, use lean mode for local code/search/shell loops, and restart from durable notes when work
  changes shape.
- When prior notes or the current report show context accumulation across large sessions, say plainly
  that the biggest lever is context reset discipline. Recommend fresh threads for unrelated tasks,
  `/compact` when a task gets long, `/clear` when switching tasks, file/path pointers instead of large
  pasted blobs, one clear task per message, targeted search before broad reads, and no subagents for
  simple repo search.
- Include a token-efficient prompt example when helpful: name the repo/path, identify the target
  change or investigation, request `rg`/`git diff` first, constrain reads to relevant files, define the
  desired output, and say whether edits are allowed.
- Offer `/apollo-eng:token-efficiency-assessment` as a follow-up for a deeper habits assessment when
  the user asks for coaching beyond the report.
- When `~/.codex/lean.config.toml` exists, recommend using `codex -p lean` instead of recommending profile creation.
- Read `references/intervention-framework.md` when wording the final user-facing summary.
- Read `references/sources.md` only when an Obsidian vault update is explicitly enabled.

## Final Response

Return the report path, optional local site bundle path, actual measured date range, number of
sessions analyzed, Obsidian status (`not configured`, `disabled`, or `updated`), and the top three
recommendations. Keep it short.
