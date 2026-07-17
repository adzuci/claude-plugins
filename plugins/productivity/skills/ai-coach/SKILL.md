---
name: ai-coach
description: Review recent curated AI-work session notes for repeated workflow friction, missed reusable capabilities, and approval-safe durable-memory candidates. Invoke on demand or as the Friday weekly AI Coach routine.
disable-model-invocation: true
---

# AI Coach

Review how the user works with AI tools and produce a concise, evidence-backed improvement queue. Keep recommendations report-only.

## Usage

```text
/ai-coach
/ai-coach weekly --vault ~/obsidian-vault
```

Default to the previous seven days in `weekly` mode and the three newest substantive session notes otherwise.

## Resolve The Vault

Use an explicit `--vault`, `$VAULT`, the current directory when it contains `sessions/`, `~/.config/adzuci-productivity/config.json`, or `~/obsidian-vault`, in that order. Ask for the vault path if none exists. Never recursively scan the home directory.

Use these optional locations when present:

- `sessions/YYYY-MM-DD.md` for curated cross-client work summaries,
- `coaching/log.md` and `coaching/recommendation-history.md` to avoid repetition,
- `coaching/skill-proposals.md` for repeated capability gaps,
- `memory/` for checking proposed durable memories,
- installed skill metadata under the current client's skill roots.

Mark missing sources as unavailable and continue. Do not read raw transcripts, source repositories, secrets, prompt bodies, or token logs.

## Build A Compact Review Set

1. Bound files by date before reading them.
1. Exclude probes, empty captures, and generated test sessions.
1. Deduplicate repeated snapshots by session ID, keeping the latest substantive summary.
1. Prefer `Did`, `Decisions`, `Blockers`, and `Next` bullets over metadata.
1. Record files scanned, exclusions, duplicates collapsed, and substantive sessions reviewed.

## Analyze

Look for:

- repeated manual work that an existing skill, command, or short sequence could remove,
- capabilities repeatedly bypassed or used inconsistently,
- unnecessary context cost or repeated rediscovery,
- approval, safety, or handoff gaps,
- explicit corrections, preferences, and durable decisions worth remembering.

Require evidence from at least two distinct sessions for a workflow recommendation. A single session qualifies only when the avoidable risk or cost is unusually high and the report explains why. Suggest creating or changing a capability only after the pattern appears in at least three sessions.

Verify every recommended invocation from installed skill metadata. Never invent, install, invoke, enable, schedule, or modify a recommended capability.

## Write The Report

Write `coaching/weekly-ai-coach/YYYY-MM-DD-weekly-ai-coach-review.md` in weekly mode, creating parent directories when needed. For an on-demand run, use `coaching/YYYY-MM-DD-ai-coach.md`.

Include:

- date range and source coverage,
- two or fewer high-signal patterns,
- `Recommended workflow upgrades` with zero to three recommendations,
- up to three proposed memory changes,
- one next experiment,
- unavailable sources and confidence caveats.

For each workflow recommendation include the pattern, session evidence, exact discovered invocation, observable benefit, confidence, and one approval-safe next action. Prefer one strong recommendation over three weak ones.

For each memory proposal include the target file, `new` or `update`, exact proposed text, session evidence, and confidence. Never write proposals into `memory/` without explicit approval. When fewer than three proposals are supported, publish fewer rather than adding filler.

## Report Back

Return the report path, recommendation count, memory-proposal count, source gaps, and the strongest next experiment. Keep the chat summary short and do not send messages or publish the report unless separately requested.
