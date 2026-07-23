---
name: self-retro
description: Weekly engineering self-retro that reflects your own work back as a ranked learning plan. Auto-detects its environment — reads local Claude Code sessions when present, or GitHub/Jira/Glean signals in the cloud. Invoke with /learning:self-retro or /self-retro.
argument-hint: "[--local | --signals] [--days N] [--sessions N] [--project-hash HASH]"
disable-model-invocation: true
compatibility: Claude Code, Codex, and cloud/web routines
---

# /self-retro — Weekly Engineering Self-Retro

Reflect an engineer's own recent work back to them as a specific, evidence-grounded learning plan. The idea is [Harshit Pandey's](https://www.linkedin.com/in/harshit-pandey-84779114a/): keep the retro focused on the work the engineer actually did, and turn it into a small number of concrete next steps.

This skill runs in two environments and picks the right one automatically:

- **Local mode** — you have access to Claude Code session files (`~/.claude/projects/`). The retro is built from the engineer's own conversation transcripts. This is the richest signal.
- **Signals mode** — you are in a cloud or web routine with no local sessions, but you can reach engineering signals: GitHub activity, Jira, and optionally Glean. The retro is built from shipped output instead of transcripts. Pairs with an LLM wiki (an Obsidian vault) pushed to git — see `learning-setup` for scheduling and `references/web-routine.md` for the paste-ready routine prompt.

## Arguments

Parse `$ARGUMENTS`:

- `--local` — force local session mode.
- `--signals` — force engineering-signals mode.
- `--days N` — look back N days (default: 7).
- `--sessions N` — (local) limit to the N most recent sessions.
- `--project-hash HASH` — (local) restrict to one project directory under `~/.claude/projects/`.

If no mode flag is given, detect it (Step 0). If no `--days`, default to 7.

## Step 0 — Detect the environment

Run these read-only checks and pick a mode:

1. **Local sessions available?** Check whether `~/.claude/projects/` exists and contains at least one `*.jsonl` modified within the lookback window:

   ```bash
   ls -d ~/.claude/projects 2>/dev/null && \
     find ~/.claude/projects -name '*.jsonl' -mtime -{days} 2>/dev/null | head -1
   ```

   If that prints a session path, choose **local mode** (unless `--signals` was passed).

2. **Engineering signals reachable?** If there are no local sessions, check whether the `gh` CLI is authenticated:

   ```bash
   gh auth status 2>&1 | head -1
   ```

   If `gh` is authenticated, choose **signals mode**.

3. **Neither?** If there are no local sessions and no reachable signals, stop and say so plainly, for example:

   > This retro needs data to reflect on. I have no local Claude Code sessions in the last {days} days and no authenticated GitHub access in this environment. Run it locally where your Claude Code sessions live, or connect GitHub/Jira/Glean and rerun with `--signals`.

   Do not fabricate a report from nothing.

Echo the chosen mode and lookback window in the report header.

---

## Local mode

**Step L1 — Build the CLI flags.** From `$ARGUMENTS`: default `--days 7`; append `--sessions N` and `--project-hash=HASH` if given (use `=` so an argparse leading-dash hash is not read as a flag).

**Step L2 — Run the session parser.** From the skill directory:

```bash
python3 parse_sessions.py <FLAGS>
```

Capture stdout as `SESSION_CONTEXT`, stderr as diagnostics.

- Exit code 2 (NO_SESSIONS_FOUND): stop and show the friendly stderr message.
- Exit code 1 (bad project-hash): stop and show the stderr error.
- Empty transcript: say "No conversation content found in the selected sessions. Sessions may contain only tool calls."

**Step L3 — Analyze.** Use `SESSION_CONTEXT` as input to the reflection prompt below. Produce the full report directly in your response; do not call other tools.

<details>
<summary>Reflection prompt (local mode)</summary>

You are a senior engineering mentor analyzing an engineer's recent Claude Code sessions.

`SESSION_CONTEXT` contains a `=== CONTEXT ===` block (`sessions_analyzed`, `date_range`, `role_hint`) followed by `SESSION_TRANSCRIPTS`.

### Phase 1 — Classify (internal only — do NOT output this block)

Silently compute from the transcript:

- Engineer turns total: N
- Pushback turns: X — natural-language disagreement, counter-proposal, or questioning ("no", "wait", "I think we should", "are you sure", "that won't work because")
- Passive acceptance: 1–2 short verbatim examples ("ok let's do that", "sounds good, implement it")
- Usage distribution: Implementation / Debugging / Architecture-design / Role-appropriate dimension turn counts
- Role-appropriate dimension mentions raised by the engineer: N with examples

Role-appropriate dimension by `role_hint`:
- `backend` → **Reliability**: deploy, CI, failure modes, rollback, monitoring, idempotency, capacity, indexing, on-call
- `frontend` → **Resilience**: error/loading states, accessibility, bundle size, offline behavior, graceful degradation
- `quality` → **Environment fidelity**: flaky test risk, CI parity, coverage gaps, environment drift, test data
- `data` → **Pipeline robustness**: data-quality checks, backfill strategy, schema-migration risk, idempotency, downstream impact
- `mixed` → **Systems thinking**: any cross-cutting reliability, operational, or failure-mode concern

Honor the dominant work area. Do not overweight a domain the engineer barely touched (e.g. a 10%-of-time area) at the expense of where their time actually went.

### Phase 2 — Report

Every section is a GitHub-flavored markdown table with the exact headers shown. Prose between tables is one sentence max. Cell content is one sentence (or one short quote + one sentence). Cite real sessions and quote real engineer messages.

Start with this header block exactly:

---

## Self-reflection Report

**Analyzed:** {sessions_analyzed} sessions · {date_range}
**Role:** {role_hint} (describe the domain in parentheses)

---

### Problem Framing Quality

| | Example | Why it mattered |
|---|---|---|
| **Strong** | [quote + session date] | [one sentence on why it shortened the loop] |
| **Build on** | [session + what more context would add] | [one sentence on what upfront context would save] |

| Pattern | Impact |
|---|---|
| [pattern name] | [one sentence] |

### Ownership Signals

**Passive acceptance** — 3–4 rows framed as next-level moves:

| Turn | What you said | Stronger move |
|---|---|---|
| [session + context] | *"[verbatim quote]"* | [one sentence] |

**Genuine pushback** — 3–4 rows:

| Turn | What you said | Why it was valuable |
|---|---|---|
| [session + context] | *"[verbatim quote]"* | [one sentence] |

Close with one sentence on the ratio (X pushbacks per Y turns) and where to push harder.

### Repeated Patterns

| # | Pattern | Appeared | Strength / Build on |
|---|---|---|---|
| 1 | **[name]** | N+ sessions | [one sentence] |

## Learning Plan

| # | Topic | Why | Exercise | Priority |
|---|---|---|---|---|
| 1 | **[topic]** | [one sentence citing sessions] | [concrete — name the file or scenario] | High / Medium / Low |

Priority order: {Role_label} operational concerns > Architecture/Design thinking > Code correctness patterns > Tooling.

Rules:
- Never use: "gap", "missed", "failed", "lacking", "you should have", "you didn't".
- Cite computed signal numbers and specific session evidence for every claim.
- End the report with exactly this line, verbatim:

*This is your self-retro — built entirely from your own sessions. Taking time to reflect on your patterns is a meaningful step toward growth. Keep going, you're on the right path.*

SESSION CONTEXT:
{{SESSION_CONTEXT}}

</details>

**Step L4 — Offer to save.** After the report, ask whether to save it to `~/self-retro-<today>.md`. Write it with the Write tool only if the user agrees. If a vault is configured (see `learning-setup`), offer to save into `<vault>/reports/self-retro/` instead.

---

## Signals mode

Build the retro from engineering output, not transcripts. The engineer's identity comes from the environment (a configured GitHub handle, Jira account, and email); do not assert a job title you cannot verify — describe the observed work area instead.

**Step S1 — Resolve the window.** Exactly the last `--days` (default 7) ending today (UTC). Compute `SINCE` with `date -u -d '{days} days ago' +%Y-%m-%d` (or `date -u -v-{days}d +%Y-%m-%d` on BSD). Echo it in the header.

**Step S2 — Gather signals (parallel where possible).** Use only the signals that are reachable; note any that are not.

- **GitHub PRs authored** — `gh search prs --author <handle> --created ">=$SINCE" --json number,title,repository,state,createdAt,mergedAt,url,body --limit 50`. If the handle returns nothing, fall back to `--author=@me`.
- **GitHub PRs reviewed** — `gh search prs --reviewed-by <handle> --updated ">=$SINCE" --json number,title,repository,url --limit 30`.
- **Local commits (if a repo checkout is present)** — `git log --since="$SINCE" --author="<name>" --oneline --all`.
- **Jira touches (if Atlassian MCP reachable)** — search issues where the current user is assignee, reporter, or commenter, updated in the window; pull key, summary, status, last-comment author, priority. For an SRE/on-call engineer, `project = INCIDENT` is usually the highest-signal filter, but do not hard-code a project — use the engineer's actual activity.
- **Glean (optional)** — `from:"<name>" updated:past_week` for RCAs, runbooks, and docs authored in the window.

**Step S3 — Produce the report.** Same spirit as local mode, driven by shipped output:

```
# Weekly Engineering Retro — <SINCE> to <today UTC>  (signals mode)

## What shipped
<table: Repo | PR | Title | State | Merged | Theme>   — group by repo, merged date desc

## What you reviewed
<table: Repo | PR | Title | URL>                       — only if non-empty

## Issues / incidents touched
<table: Key | Title | Status | Your role | Priority>   — only if reachable

## Themes & patterns
2–4 rows: <pattern> | <evidence, cite PRs/keys by number> | <strength or build-on>

## Learning plan (3 items max, ranked)
<topic> | <why, cite evidence> | <concrete exercise> | <priority>
Priority order: Reliability/SRE concerns > Architecture > Code correctness > Tooling.
```

Style: never use "gap / missed / failed / lacking"; lead with tables; one sentence between tables max; quote real PR titles and issue summaries verbatim (do not paraphrase); cite PRs and issue keys verbatim. Keep the retro weighted to where the engineer actually spent time. End the report with exactly:

`*This is your weekly engineering retro — built from your shipped work. Keep going.*`

**Step S4 — Deliver (only when asked or scheduled).** On its own, print the report. `learning-setup` wires the scheduled delivery: store the report in the vault (`<vault>/reports/self-retro/YYYY-MM-DD.md`), update the historical meta report, and optionally DM it on Slack. See `references/web-routine.md` for the full routine prompt.

## Honesty rules (both modes)

- Be honest about an empty week: if nothing shipped or no sessions exist in the window, say so in one line and skip the empty tables — do not pad with filler.
- Never include secret values. PR numbers, issue keys, repo names, account/zone IDs are fine (already public in PRs).
- If a single signal source hangs, skip it and note it in the report (e.g. "Jira unreachable this run"). Budget the whole run to a few minutes.
