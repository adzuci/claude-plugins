---
name: token-burn-dashboard
description: Manual-invocation only. Build a private local token burn dashboard to analyze AI token spending, audit Claude and Codex costs, and render usage heatmaps from measured logs. Run via /apollo-eng:token-burn-dashboard.
disable-model-invocation: true
---

# Local Token Burn Dashboard

**Invoke directly.** This skill is not auto-activated. Run it as a slash command: `/apollo-eng:token-burn-dashboard [args]`. The short description above is intentional so the skill stays out of unrelated sessions and does not bloat model-routing context.

Build a local, engineering-grade token usage dashboard that helps a user see where AI work is going without publishing private usage data or dressing estimates up as facts.

## Operating Contract

- Keep the work local unless the user explicitly approves a destination and publish target.
- Measure before visualizing. Do not invent usage, rates, conversations, sources, or time windows.
- Ask the intake questions before building unless the user already answered them or explicitly says to use defaults.
- Prefer the smallest complete artifact that satisfies the agreed scope.
- Label source confidence clearly: exact, measured, inferred, estimated, or not connected.
- Do not put inferred, estimated, or not connected sources in top KPIs, measured source chips, measured source split cards, driver-share bars, breakdown totals, or largest-row tables.
- Do not expose chat estimates unless an exact local export or API-backed source is connected and validated.

## Intake First

Before implementation, ask up to five concise questions with options. Use `references/intake-options.md` for the question set and defaults. Confirm:

1. Audience and privacy posture.
1. Timeframe.
1. Data thoroughness.
1. Visual direction.
1. Output format and runtime.

If the user says "choose defaults", use: private local artifact, previous calendar month as the initial selected view bounded by actual available data, standard thoroughness, high-end technical OLED-dark dashboard, self-contained HTML plus data ledger.

## Source Discovery

Inspect local usage sources in this order, adapting paths to the current machine:

- `~/.codex/sessions/`
- `~/.codex/archived_sessions/`
- `~/.codex/history.jsonl`
- `~/.claude/usage-data/session-meta/`
- `~/.claude/usage-data/facets/`
- `~/.claude/projects/` for transcript input/output supplements when metadata is missing or stale
- `~/.gemini/antigravity/`
- `~/Library/Application Support/Antigravity/`
- User-provided ChatGPT export folders, only when explicitly provided.
- Other user-provided logs, billing exports, telemetry, or API reports.

Use these inclusion rules:

- For Codex logs, prefer exact `token_count` events when present.
- For Claude logs, use measured `input_tokens` and `output_tokens` from `~/.claude/usage-data/session-meta/` when available, and use facets for titles/context when available. If `session-meta` is missing sessions or stale, supplement missing sessions from `~/.claude/projects/` transcript `message.usage` records using `input_tokens` and `output_tokens` only. Deduplicate repeated transcript snapshots by `message.id`. Do not include transcript `cache_creation_input_tokens` or `cache_read_input_tokens` in top KPIs unless an exact billing/export source is explicitly connected and validated.
- For run counts, count measured local runs rather than only deduped token rows. Codex `token_count` files count as one run each. Claude transcript files with measured usage count as runs, including subagents, while token totals remain deduped by session/conversation to avoid double counting.
- For Antigravity, inspect local state, conversation, and app-support files, but include it only if exact or measured token fields are found and validated. Otherwise list it as found but excluded or not connected in the ledger.
- For ChatGPT or browser chat, require a real export or exact source before showing it.

## Build Workflow

1. Confirm scope with the intake questions.
1. Discover local sources and produce a source ledger with found, missing, included, and excluded sources.
1. Parse usage into a normalized session model with date, source, confidence, title, category, token fields, timestamps, duration, and path metadata when safe.
1. Aggregate by day, week, month, source, and work driver.
1. Generate the selected artifact with a high-end technical visual system.
1. Run browser QA and data integrity checks.
1. Return the local file path, measured sources, actual date range, and validation result.

## Output Shape

Default to a shareable local folder:

```text
token-burn-dashboard-YYYY-MM-DD/
  build-dashboard.mjs
  usage-data.json
  source-ledger.md
  index.html
  evidence/
    browser-qa.json
    dashboard-desktop-1440.png
    dashboard-mobile-390.png
```

The visible dashboard should include:

- Top KPIs: `Exact total`, `Measured total`, `Runs`.
- Daily, Weekly, and Monthly controls that re-render the grid, trend, and breakdown table.
- A user-selectable date range with one unambiguous control surface: visible month/range buttons for common ranges plus `From`/`To` text fields displayed in explicit US format (`MM/DD/YYYY`). Avoid dropdown-only selectors and duplicate native `type=date` inputs because browsers/locales can make those controls confusing or unreliable.
- Initial visible range defaults to the previous calendar month when data exists, not the full discovered span. Still show the actual discovered timeframe in the ledger and available date bounds.
- Actual discovered timeframe, not a hardcoded range.
- Source chips only for measured sources, with clear source totals.
- Daily burn renders as a regular Sunday-to-Saturday calendar grid with weekday headers, leading/trailing empty days, day numbers, intensity, and full US dates on hover or accessible labels. Weekly and Monthly views can use compact intensity grids.
- Trend chart, driver share bars with percentages, source chips, breakdown table, largest measured token rows table, and next-move insight cards.
- A visible source split for measured sources, including separate Codex and Claude totals when both are connected.
- A breakdown table that shows total tokens, source-specific token columns, and measured run counts.
- A source ledger explaining included, missing, and excluded sources, including the difference between deduped token rows and measured local runs when those diverge.

## Design Standard

Read `references/visual-system.md` before implementing or reviewing the dashboard UI. Prioritize professional technical taste: dense but readable, OLED-dark, high-contrast data color, restrained motion, stable layout, keyboard focus, and responsive tables.

## Validation

Read `references/qa-contract.md` before delivery. At minimum verify:

- No external network loads.
- No console errors or page errors.
- No horizontal overflow at mobile and desktop widths.
- Daily, Weekly, and Monthly controls change rendered counts and labels.
- Top KPI labels match the agreed visible metrics.
- No visible unverified chat estimate or not connected source appears as measured.
- `source-ledger.md` explains all included and excluded sources.

## Final Response

Keep the final response short and technical:

- Link the local `index.html`.
- State measured sources and actual date range.
- State whether estimated or missing sources were excluded.
- State validation status and any residual data gaps.
