---
name: codex-insights
description: Analyze local Codex sessions into a private HTML burn report with ROI and efficiency judgments.
disable-model-invocation: true
---

# /codex-insights — Codex Session Analysis

If this skill is running in Claude Code, stop immediately and respond exactly:
"This skill is only for Codex. Run `/apollo-eng:deep-insights` instead."

**Manual invocation only** (`disable-model-invocation: true`). This Codex counterpart to
`/apollo-eng:deep-insights` produces a self-contained HTML report under
`~/.codex/codex-insights/reports/`. It leads with burn vs output, then gives paste-ready team-harness
changes. Treat it as an empowering intervention: judge honestly what the spend bought, then offer
more capable operating modes instead of restrictions.

Codex has no `Workflow` fan-out tool (the engine `/deep-insights` uses), so the per-session ROI/
outcome judgment runs as a **short sequential pass by this session's model** over a compact
deterministic ledger — not a subagent fan-out. Efficiency, the burn chart, and the config audit
are fully deterministic (zero model tokens); the renderer templates the HTML for free.

## Usage

```text
/apollo-eng:codex-insights [--since 7d|24h|30d|all|YYYY-MM-DD] [--sessions N] [--site-dir PATH] [--vault PATH] [--no-site] [--no-obsidian] [--no-judge] [--open] [--include-session-names]
```

This skill is Codex only. It expects shell/file access for local Codex logs. Claude Code users
should run `/apollo-eng:deep-insights` instead.

## Workflow

1. Parse `$ARGUMENTS`.

   - `--since`: default `7d`; accepts `24h`, `7d`, `30d`, ISO date, or `all`.
   - `--sessions N`: cap the highest-token sessions included in the burn ledger and detailed table.
   - `--site-dir PATH`: override the shareable Codex Sites bundle directory.
   - `--vault PATH`: opt into Obsidian updates for this vault.
   - `--no-site`: skip the Codex Sites bundle.
   - `--no-obsidian`: force-disable vault updates, even if `OBSIDIAN_VAULT` is set.
   - `--no-judge`: skip the burn-vs-output judgment pass and render efficiency-only (deterministic,
     zero model tokens). Use for a quick throwaway look.
   - `--open`: open the generated HTML report.
   - `--include-session-names`: knowingly include thread/session titles in the public site bundle.

1. **Run the deterministic enumerator** (the cheap pre-pass — zero model tokens):

```sh
node <skill-dir>/scripts/enumerate_codex_sessions.mjs --since 7d --sessions 20
```

It writes `/tmp/codex-insights/compact.json` and `/tmp/codex-insights/source-ledger.md`. It reads
`~/.codex/sessions`, `~/.codex/archived_sessions`, and `~/.codex/session_index.jsonl`; exact
`token_count` events are the source of truth. It also parses `~/.codex/config.toml`, trusted
project entries, project-local `.codex/config.toml` files, MCP/plugin state, and feature flags. It
emits, per session, a **computed efficiency label** (lean/loose/thrashy) with its signals, the ISO
week, estimated credits, and deterministic work-output counts (`edit_events`, `test_events`,
`commit_events`, `user_prompt_count`, `completed`) — plus `by_week` (tokens split by efficiency)
and a `burn_analysis.sessions` ledger seed with `roi`/`outcome`/`verdict` left null for the next
step. If safe and available it captures `codex mcp list` as runtime verification and `ccusage` as
a cross-check.

Show the user the stdout line (session count + total tokens). If **0 sessions** are found, stop and
say the window was clean — suggest a wider `--since`.

1. **Judge burn vs output** (the only model-token step; skip if `--no-judge`). Follow the full
   rubric and output shape in [`references/burn-vs-output.md`](references/burn-vs-output.md). Judge
   material sessions from `burn_analysis.sessions` in `compact.json`; inspect targeted transcript
   lines only when the ledger is insufficient. Write the judgments file:

```sh
# /tmp/codex-insights/judgments.json — shape documented in references/burn-vs-output.md
# { overall_verdict, weekly:[{week,headline}], sessions:[{id, roi, outcome, verdict}] }
```

1. **Render the report** (deterministic — zero model tokens). Build the self-cost footer first (a
   skill that audits token spend must disclose its own) using
   [`references/cost-estimation.md`](references/cost-estimation.md): the enumerator and renderer
   cost 0 model tokens; only the judgment pass spends tokens — read `/usage` or `/status` if
   visible, else estimate, and label with `≈`. Then render, passing the judgments file (omit
   `--judgments` if `--no-judge`):

```sh
OUT=~/.codex/codex-insights/reports/report-$(date +%F).html
FOOT="≈ this analysis: enumerator 0 model-tok (deterministic) · judgment ≈<N>k tok · rendering 0 tok"
node <skill-dir>/scripts/render_report.mjs /tmp/codex-insights/compact.json --out "$OUT" \
  --judgments /tmp/codex-insights/judgments.json --footer "$FOOT"
```

The report leads with the **week-by-week burn chart** (tokens split by efficiency) and the
**burn-vs-output ledger** (color-coded ROI / outcome / efficiency badges + one-line verdicts),
then the config/harness sections: Where Tokens Went, Context Load, MCP and Plugin Surface, Project
Scope Audit, Project Split Recommendations, How to Configure This, Insights / Suggestions, Measured
Action Plan, Workflow Rules, Paste-Ready Changes, Other Context-Reduction Moves, and the
Implementation Checklist. The report is self-contained HTML with no external assets and may include
scrubbed local session detail for the current user.

1. Unless `--no-site` was passed, build a local Codex Sites-ready bundle:

```sh
node <skill-dir>/scripts/build_site_bundle.mjs /tmp/codex-insights/compact.json --report "$OUT"
```

This writes `~/.codex/codex-insights/site/` by default with `.openai/hosting.json`, `package.json`,
`build.mjs`, `public/index.html`, `public/data/compact.json`, and `public/source-ledger.md`. Run
`npm run build` in that directory to produce `dist/client` and `dist/server/index.js`.

Keep Sites local-only by default. Do not save or deploy with Sites unless the user explicitly asks.
The site bundle is public-safer than the local HTML: it omits the burn-vs-output ledger (session
labels + verdicts), raw messages, token histories, full token payloads, sensitive path details,
and thread/session titles unless `--include-session-names` was passed.

1. Persist the snapshot:

```sh
mkdir -p ~/.codex/codex-insights
jq -c '.snapshot' /tmp/codex-insights/compact.json >> ~/.codex/codex-insights/history.jsonl
```

The snapshot now carries `credits` and the deterministic `efficiency_mix`, so the trend line tracks
not just how much was spent but how much was churn over time.

1. Optionally update an Obsidian vault only when explicitly configured. If `--no-obsidian` was
   passed, or neither `--vault` nor `OBSIDIAN_VAULT` points to a valid vault, do not run this step
   and report `Obsidian: not configured`.

```sh
node <skill-dir>/scripts/update_obsidian_project.mjs /tmp/codex-insights/compact.json --report "$OUT"
```

This creates or updates `wiki/ai-tooling/token-efficiency-project.md` and adds an Active project
link in `memory/projects.md` without clobbering unrelated content.

1. If `--open` was passed, open the report with `open "$OUT"` on macOS.

## Interpretation Rules

- Apply the burn-vs-output grounding, materiality, and judgment rules only from
  [`references/burn-vs-output.md`](references/burn-vs-output.md); do not duplicate or override them.
- Prefer measured facts over advice. If a field is missing, say it is missing.
- Label `ccusage` as a cross-check, not the source of truth, when exact Codex `token_count` events
  are present.
- Treat parsed config and runtime MCP verification as separate evidence. If they disagree, say
  runtime reflects what this Codex build actually loaded for the current project.
- Prefer project-local `.codex/config.toml` over global MCP enablement when a tool is only useful
  for a narrow workflow. Project-local config only loads for trusted projects.
- For API spend monitoring, check whether `codexbar` or the local cost script exists, but do not
  inspect Tmux config or report Tmux integration as missing. Always provide the paste-ready Tmux
  line as setup guidance.
- Recommend the Apollo-style Codex status line using supported built-ins that apply to Apollo
  currently: current directory, git branch, model/reasoning, context remaining, and token counters.
- Check for unused skills in the measured window. For specialized skills that were not explicitly
  invoked, suggest `disable-model-invocation: true` and remind users to call them with `$skill` or
  `$plugin:skill` only when the skill matches the task.
- Suggest `/usage` for current token/credit visibility and `/status` for current session/model/
  runtime status when those checks would help interpret the report.
- Do not claim exact credit usage per MCP. Codex logs expose exact session-level token counts; MCP
  attribution is only an estimate from MCP call counts and session-level tool-output tokens.
- Frame recommendations as measured workflow moves: use full power when connectors and context are
  needed, use lean mode for local code/search/shell loops, and restart from durable notes when work
  changes shape.
- When prior notes or the current report show context accumulation across large sessions, say
  plainly that the biggest lever is context reset discipline. Recommend fresh threads for unrelated
  tasks, `/compact` when a task gets long, `/clear` when switching tasks, file/path pointers instead
  of large pasted blobs, one clear task per message, targeted search before broad reads, and no
  subagents for simple repo search.
- Include a token-efficient prompt example when helpful: name the repo/path, identify the target
  change or investigation, request `rg`/`git diff` first, constrain reads to relevant files, define
  the desired output, and say whether edits are allowed.
- Offer `/apollo-eng:token-efficiency-assessment` as a follow-up for a deeper habits assessment when
  the user asks for coaching beyond the report.
- When `~/.codex/lean.config.toml` exists, recommend using `codex -p lean` instead of recommending
  profile creation.
- Read `references/intervention-framework.md` when wording the final user-facing summary.
- Read `references/sources.md` only when an Obsidian vault update is explicitly enabled.

## Final Response

Lead with the one-line `overall_verdict` (burn vs output). Then return the report path, optional
local site bundle path, actual measured date range, number of sessions analyzed, Obsidian status
(`not configured`, `disabled`, or `updated`), and the top three team-harness recommendations. Keep
it short.
