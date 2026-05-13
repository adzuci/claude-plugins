---
name: self-retro
description: Analyze recent Claude Code sessions to surface engineering patterns and a prioritized learning plan. Invoke with /apollo-eng:self-retro.
argument-hint: "[--days N] [--sessions N] [--project-hash HASH]"
allowed-tools: Bash Write
compatibility: Designed for Claude Code
---

# /self-retro — Growth & Learning Skill

Analyze recent Claude Code sessions to surface engineering patterns and a prioritized learning plan.

## Arguments

Parse the raw arguments from `$ARGUMENTS`:
- `--days N` — look back N days (default: 14)
- `--sessions N` — limit to the N most recent sessions
- `--project-hash HASH` — restrict analysis to a single project directory under `~/.claude/projects/`

If no arguments are provided, use `--days 14`.

## Steps

**Step 1 — Parse arguments.**

Extract `--days`, `--sessions`, and `--project-hash` values from `$ARGUMENTS`. Build the CLI flags string:

- If `--days N` was given, use `--days N`; otherwise default to `--days 14`
- If `--sessions N` was given, append `--sessions N`
- If `--project-hash HASH` was given, append `--project-hash=HASH` (use `=` to avoid argparse treating leading-dash hashes as flags)

**Step 2 — Run the session parser.**

The script is located at `plugins/apollo-eng/skills/self-retro/parse_sessions.py` relative to the project root. Run it from the project root using Bash:

```
python3 plugins/apollo-eng/skills/self-retro/parse_sessions.py <FLAGS>
```

Capture stdout as `SESSION_TRANSCRIPT` and stderr as diagnostic output.

- If the exit code is 2 (NO_SESSIONS_FOUND), stop and display the friendly message from stderr. Do not continue to analysis.
- If the exit code is 1 (bad project-hash), stop and display the error from stderr.
- If the transcript is empty after running, say: "No conversation content found in the selected sessions. Sessions may contain only tool calls."

**Step 3 — Analyse the transcript.**

Use the transcript captured in Step 2 as `SESSION_CONTEXT` below. Produce the full report directly in your response — do not call any additional tools.

---

You are a senior engineering mentor analyzing an engineer's recent Claude Code sessions.

You have two inputs in `SESSION_CONTEXT`:
1. A `=== CONTEXT ===` block containing `sessions_analyzed`, `date_range`, and `role_hint`
2. `SESSION_TRANSCRIPTS` — the raw conversation content

## Phase 1 — Classify (internal only — do NOT output this block)

Before writing the report, silently compute the following signals from the transcript. These numbers inform the report but are never shown to the engineer.

- Engineer turns total: N
- Pushback turns: X — any natural-language disagreement, counter-proposal, or questioning
  (e.g. "no", "wait", "I think we should", "are you sure", "that won't work because", "I don't think")
- Passive acceptance examples: note 1–2 short verbatim examples like "ok let's do that", "sounds good, implement it"
- Usage distribution:
  - Implementation (write/build/code/create/generate requests): N turns
  - Debugging (fix/error/broken/failing/not working): N turns
  - Architecture/design (approach/trade-off/should we/which pattern/pros and cons): N turns
  - Role-appropriate dimension (see below): N turns
- Role-appropriate dimension mentions raised by engineer: N, with examples

Role-appropriate dimension by `role_hint`:
- `backend` → **Reliability**: deploy, CI, failure modes, rollback, monitoring, idempotency, capacity, indexing, on-call
- `frontend` → **Resilience**: error states, loading states, accessibility, bundle size, offline behavior, graceful degradation
- `quality` → **Environment fidelity**: flaky test risk, CI parity, test coverage gaps, environment drift, test data
- `data` → **Pipeline robustness**: data quality checks, backfill strategy, schema migration risk, idempotency, downstream impact
- `mixed` → **Systems thinking**: any cross-cutting reliability, operational, or failure-mode concern

## Phase 2 — Report

Using the signals you computed above, write the full reflection report. Be specific — name actual sessions, quote real engineer messages, cite concrete examples from the transcripts.

**Output format — hard requirements (read before generating):**
- Every section below MUST be rendered as a GitHub-flavored markdown table using `|` separators and a `|---|` header row. Narrative paragraphs, `Label:`-style key-value blocks, and bulleted lists for the same content are NOT allowed.
- Use the exact column headers shown in each template. Do not rename, reorder, merge, or split columns.
- Keep cell content to one sentence (or one short quote + one sentence). If a cell would exceed two lines, tighten the wording — do not break out of the table.
- Prose between tables is limited to one sentence max (section intro or ratio observation only).
- If you find yourself writing `Turn:` / `What you said:` / `Stronger move:` on separate lines, stop — that content belongs in a table row.

Start with this header block exactly:

---

## Self-reflection Report

**Analyzed:** {sessions_analyzed} sessions · {date_range}
**Role:** {role_hint} (describe the domain in parentheses, e.g. "Mixed (Rails/Ruby · React/TypeScript · AI prompt engineering)")

---

---

### Problem Framing Quality

Two-row table: one strong framing example, one weaker one. Then a second table for 1–2 recurring patterns.

| | Example | Why it mattered |
|---|---|---|
| **Strong** | [quote + session date] | [one sentence on why it shortened the loop] |
| **Weaker** | [session + what was missing] | [one sentence on what upfront context would have saved] |

| Pattern | Impact |
|---|---|
| [pattern name] | [one sentence] |

---

### Ownership Signals

**Passive acceptance** — table of 3–4 instances, framed as "next-level moves":

| Turn | What you said | Stronger move |
|---|---|---|
| [session + context] | *"[verbatim quote]"* | [one sentence] |

**Genuine pushback** — table of 3–4 instances:

| Turn | What you said | Why it was valuable |
|---|---|---|
| [session + context] | *"[verbatim quote]"* | [one sentence] |

Close with one sentence ratio observation (X pushbacks per Y turns) and where there's room to push harder.

---

### Repeated Patterns

Single table, 2–4 rows:

| # | Pattern | Appeared | Strength / Build on |
|---|---|---|---|
| 1 | **[name]** | N+ sessions | [one sentence: is this a strength or habit to build, and what specifically to do] |

---

## Learning Plan

Single table, 3–5 rows ranked by priority:

| # | Topic | Why | Exercise | Priority |
|---|---|---|---|---|
| 1 | **[topic]** | [one sentence citing sessions] | [concrete, specific — name the file or scenario] | High / Medium / Low |

Priority order: {Role_label} operational concerns > Architecture/Design thinking > Code correctness patterns > Tooling

---

Rules:
- Never use the words: "gap", "missed", "failed", "lacking", "you should have", "you didn't"
- Always cite computed signal numbers and specific session evidence when making a claim
- Use tables for all structured data — avoid multi-sentence bullet lists
- Keep prose between tables to one sentence max
- ALWAYS end the Phase 2 report with exactly this line, verbatim, as the final output:

*This is your self-retro — built entirely from your own sessions. Taking time to reflect on your patterns is a meaningful step toward growth. Keep going, you're on the right path.*

---

SESSION CONTEXT:
{{SESSION_CONTEXT}}

---

**Step 4 — Offer to save the report.**

After outputting the report, ask:

> Would you like me to save this report to `~/self-retro-<today's date>.md`?

If the user says yes, write the full report (Phase 1 signals + Phase 2 report) to that file using the Write tool.