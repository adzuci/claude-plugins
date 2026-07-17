---
name: daily-wrapup
description: Daily end-of-day wrapup and next-day planning. Reviews yesterday's goals, summarizes today, previews tomorrow's calendar, optionally checks on-call, surfaces outstanding requests, and captures tomorrow's goals in your Obsidian vault.
---

# Daily Wrapup

Run a practical end-of-day operating loop. Keep it evidence-first, concise, and actionable. Avoid generic journaling.

## Modes

- **Brief mode**: default `/productivity:daily-wrapup`. Produce the wrapup, ask for the next planning day's goals, and do not assume a later reply will be captured automatically.
- **Goals mode**: when you reply with goals or ask to save goals, write them explicitly with `scripts/append_goals.py`.

## Dashboard Goal Contract

Goals are written to the Obsidian session note at `$VAULT/sessions/YYYY-MM-DD.md`, specifically the `## Goals for tomorrow` section, via `scripts/append_goals.py`.

Rules:

- Keep committed daily goals only in `## Goals for tomorrow` in the target session note.
- Use `scripts/append_goals.py` for goal writes so the section is replaced idempotently and marked with a timestamp.
- In brief mode, goal candidates are suggestions only — not committed until goals mode writes them.
- If you give more than one goal source in chat, consolidate all next-planning-day commitments into that one section.
- Preserve Jira, Slack, GitHub, Notion, or document links in goal text when available.

## Concrete Daily Task Definition

A concrete daily task is small enough to make visible progress tomorrow and specific enough that you can tell whether it happened.

Good daily tasks:

- Start with a verb: `Reply`, `Review`, `Draft`, `Ship`, `Decide`, `Schedule`, `Verify`, `Close`, `Hand off`.
- Name the artifact, person, ticket, thread, PR, or decision.
- Include the next observable outcome, not just the theme.
- Fit in one day, or clearly name the one-day slice of a larger project.
- Link to the ticket, thread, PR, or doc when available.

Avoid vague goals like `work on AI tooling` or `follow up on incidents`. Rewrite as concrete tasks.

## Brief Workflow

### Step 1: Establish Dates

Use the user's local timezone. Treat "today" and "tomorrow" as absolute dates in the output.

Set:

- `TODAY=YYYY-MM-DD`
- `YESTERDAY=YYYY-MM-DD`
- `TOMORROW=YYYY-MM-DD`
- `GOAL_DAY=YYYY-MM-DD`
- `VAULT` from an explicit path, `$VAULT`, `~/.config/adzuci-productivity/config.json`, then `~/obsidian-vault`
- `SESSION_NOTE=$VAULT/sessions/$TODAY.md`

Goal-day rule:

- On Friday, set `GOAL_DAY` to the following Monday and refer to it as `Monday` in goal prompts and recommendations.
- On all other days, set `GOAL_DAY=$TOMORROW`.
- Friday's Monday goals are still saved into Friday's session note so the source stays stable.

Read `$VAULT/index.md` first if available, then only files directly needed for this run.

### Step 2: Build Source Ledger

Before drawing conclusions, track each source checked:

- Source name
- Status: `available`, `unavailable`, `skipped`, or `stale`
- Query window
- Failure text or caveat, if any

Use this ledger to qualify claims. "No outstanding requests found" is allowed only for sources actually searched.

### Step 3: Review Yesterday's Goals

Read yesterday's `## Goals for tomorrow` section if present. For each goal, classify:

- `Done`
- `Partial`
- `Skipped`
- `Still open`

Add one short evidence note from sessions, git, Jira, GitHub, calendar, or conversation context. If yesterday's goals are missing, say so.

### Step 4: Summarize Today

Gather high-signal evidence:

- Today's Obsidian session note
- Current conversation context
- Git activity from active repos
- Recent merged/open PRs you authored (if GitHub is available)
- Recent Jira issue updates assigned to or touched by you (if Jira is available)
- Calendar events from today if useful
- `memory/responsibilities.md` and `memory/projects.md` for priority grounding

Output 3-6 bullets. Prefer verbs, artifacts, tickets, docs, PRs, and decisions.

### Step 5: Preview Tomorrow's Calendar

Summarize tomorrow's calendar in 2-5 bullets:

- Meeting load and obvious clusters
- First/last meeting
- Free windows longer than 60 minutes
- Conflicts or tight transitions
- Prep implied by meetings

If deep work is needed, suggest a specific block only when the calendar evidence supports it.

### Step 6: Check On Call (optional)

**Skip this step** if you are not on call, your org has no on-call rotation, or no on-call tool (PagerDuty CLI, Grafana OnCall, OpsGenie, etc.) is available. Mark it `skipped` in the source ledger and omit the on-call block from the output.

If on-call tooling is available, check the schedule for today and tomorrow. Report:

- Who is on call in each of your org's on-call regions
- Whether you are on call

If you are on call today or tomorrow:

- Treat interrupt budget as real
- Keep tomorrow's top priority smaller and interruption-resilient
- Suggest one proactive on-call hygiene task
- Avoid recommending a long fragile deep-work block unless clearly protected

If you are not on call:

- Recommend tomorrow's work without interrupt budget constraints

If on-call status cannot be determined, report `not verified`.

### Step 7: Find Outstanding Requests

Search bounded windows. Separate:

- Team requests
- Stakeholder requests
- GitHub/Jira review requests

Classify only actionable asks. Ignore FYIs, broad announcements, and already-closed loops. If a source was unavailable, say the request check is incomplete.

### Step 8: Recommend Tomorrow

Include:

- Easy wins: 2-4 small actions under 30 minutes
- Goal candidates: 3-5 possible goals you could choose from
- One priority: the single most important outcome for tomorrow
- Deep work: recommended block or "do not force it" based on calendar + on-call state
- Open loops: items that should go into a backlog
- Energy audit: what seemed energizing, draining, and delegatable based on today's evidence

Build goal candidates from Obsidian evidence, not generic advice. Prefer:

- Unfinished items from today's or yesterday's session notes
- Explicit open loops in `backlog.md`
- Current active projects in `memory/projects.md`
- Recurring responsibilities in `memory/responsibilities.md`
- Bounded outstanding requests from Slack/GitHub/Jira

Each candidate should be small enough for tomorrow, phrased as an outcome, and labeled with a reason like `unblocks someone`, `reduces risk`, `ships work`, or `leverage`. If you are on call, bias candidates toward interruption-resilient work.

When a candidate comes from Jira, Slack, GitHub, Notion, or another source with a URL, include the link.

For the energy audit, keep it short and practical:

- `Gave energy`: 1-3 activities that looked like high-leverage or energizing work.
- `Drained energy`: 1-3 activities that looked like toil, context switching, or avoidable ambiguity.
- `Delegate/systematize`: 1-3 candidates to delegate, automate, batch, or turn into a repeatable workflow.

Infer only from the day's evidence; label low-confidence guesses.

### Step 9: Ask For Goals

End with fast multiple-choice questions.

List the best 3 goal candidates immediately before the questions.

Ask:

- `Energy audit`
  - `Gave energy`: choose `People`, `Building`, `Debugging`, `Planning`, or `Other`.
  - `Drained energy`: choose `Context switching`, `Incidents`, `Meetings`, `Admin`, or `Other`.
  - `Delegate/systematize`: choose `Follow-ups`, `Status updates`, `Debugging`, `Reviews`, or `Other`.
- `MQT` — the single most important outcome for `GOAL_DAY`. Offer choices from the top 3 goal candidates plus `Other`.
- `Goals` — choose `1`, `2`, or `3` goals to commit.
- `Weekday-only items` (weekdays only) — `Approvals`, `Meetings`, `People follow-ups`, `Slack/email replies`, `Handoffs`, or `None`.
- `Sleep/wake` — approximate sleep and wake times.

Tell the user that replying with goals will let `/productivity:daily-wrapup goals` save them to `sessions/$TODAY.md` under `## Goals for tomorrow`, which is the dashboard's goal source. On Fridays, be explicit that this section contains Monday goals.

## Goals Mode

When the user provides goals, normalize them into concrete daily tasks, then write every committed `GOAL_DAY` goal to today's session note under `## Goals for tomorrow`:

```bash
python3 "$(dirname "$0")/scripts/append_goals.py" \
  --date "$TODAY" \
  --vault "${VAULT:-$HOME/obsidian-vault}" \
  --goals "<one goal per line or bullet list>"
```

If the user provides an MQT, preserve it as the first saved goal.

Use `--dry-run` first when the goals are ambiguous or when the target note already has substantial content.

## Output Format

```markdown
Daily wrapup for YYYY-MM-DD

Sources checked
- ...

Yesterday's goals
- ...

Today
- ...

Tomorrow's calendar
- ...

On call (if applicable)
- Today: ...
- Tomorrow: ...

Outstanding requests
- Team: ...
- Stakeholders: ...
- Reviews/Jira: ...

Easy wins
- ...

Goal candidates
- ...

Priority for tomorrow
- ...

Deep work
- ...

Energy audit
- Gave energy: ...
- Drained energy: ...
- Delegate/systematize: ...

Open loops
- ...

[Multiple choice prompts for energy audit, MQT, goals, weekday items, sleep/wake]
```

## Promotion Rules

- Committed daily goals stay only in `sessions/YYYY-MM-DD.md` under `## Goals for tomorrow`.
- Daily reflection and recap content stay in `sessions/YYYY-MM-DD.md`.
- Actionable open loops should be proposed for `backlog.md`.
- Durable wins should be proposed for `memory/brag.md`.
- Repeated AI workflow patterns should be proposed for `coaching/log.md`.

Do not write to those long-term files unless the user explicitly asks.
