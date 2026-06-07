---
name: oncall
description: Manual-invocation only. On-call companion for the DevOps + Platform PagerDuty rotations — render the next two weeks of primary/secondary schedule, review the last week of incidents for recurring failures and runbook gaps, and propose shift overrides. Run via /apollo-eng-devops:oncall.
argument-hint: "[schedule|review|swap|override] [--weeks N] [--days N] [--from DATE --to DATE --cover USER] [--apply]"
disable-model-invocation: true
---

# On-call

A companion for the DevOps and Platform PagerDuty rotations. It wraps the PagerDuty CLI
(`pd`) with four modes: see the schedule, review the week's incidents, swap shifts for a
PTO window, or propose a low-level override. **Read operations are safe; the swap and
override modes are propose-only by default** and never write without an explicit `--apply`.

Run the scripts from this skill's `scripts/` directory.

______________________________________________________________________

## Modes

```
/apollo-eng-devops:oncall [schedule | review | swap | override] [flags]
```

| Mode | What it does | Default |
| --- | --- | --- |
| `schedule` | Render DevOps + Platform primary/secondary on-call for a window | **default when no mode given** |
| `review` | Skim the last week of incidents for recurring failures + runbook gaps | — |
| `swap` | Cover a PTO window by handing the user's overlapping shifts to a covering user | dry-run |
| `override` | Low-level: propose a single override by schedule/user/time | dry-run |

`swap` is the ergonomic PTO workflow ("I'm out June 10–14, cover me"); `override` is the
raw primitive `swap` builds on, for when you already know the exact schedule, user, and
window.

______________________________________________________________________

## Mode: `schedule` (default)

Render who's on call across both teams for the **next two weeks**.

```bash
python3 scripts/oncall_schedule.py --weeks 2 --teams devops,platform
```

Flags: `--weeks N` (default 2), `--teams devops,platform`, `--at YYYY-MM-DD` (window start,
default today). The output is a markdown grid — one row per day, one column per
team×role (e.g. `devops primary`, `devops secondary`, `platform primary`).

**After printing the grid, always ask the caller** (use `AskUserQuestion`):

1. **Propose a shift override** — if yes, switch to the `override` mode flow below.
1. **See a different time window** — if yes, re-run with a different `--at` / `--weeks`.

If the script reports no matching schedules, the team/role name patterns need updating —
point the user at [`references/schedules.md`](references/schedules.md) and
`scripts/lib.py` (`TEAM_PATTERNS` / `ROLE_PATTERNS`).

______________________________________________________________________

## Mode: `review`

Skim the last week of PagerDuty incidents and surface the two patterns that compound:
recurring failures with no fix, and incidents with no runbook.

```bash
python3 scripts/incident_review.py --days 7
```

Present the report, then **make the argument** from
[`references/incident-review-rationale.md`](references/incident-review-rationale.md):
each recurring alert is repeated toil; each no-runbook incident is an undocumented
failure mode. For each finding, propose an action (draft a runbook ticket, link
recurring incidents as `Relates`, or flag the alert for tuning) — **propose, do not
create**. For full Jira INCIDENT-queue triage, hand off to the `incident-triage` skill.

______________________________________________________________________

## Mode: `override`

Propose a shift override. **Dry-run by default** — it prints the exact PagerDuty REST
call and changes nothing until the caller confirms and you re-run with `--apply`.

```bash
# 1. Preview (no change):
python3 scripts/propose_override.py \
  --schedule <SCHED_ID> --user <USER_ID> \
  --start 2026-06-10T09:00:00Z --end 2026-06-10T17:00:00Z

# 2. Only after explicit confirmation:
python3 scripts/propose_override.py \
  --schedule <SCHED_ID> --user <USER_ID> \
  --start 2026-06-10T09:00:00Z --end 2026-06-10T17:00:00Z --apply
```

Resolve `<SCHED_ID>` from the `schedule` grid or
[`references/schedules.md`](references/schedules.md); resolve `<USER_ID>` with
`pd user:list` / `pd rest:get -e /users`. Always show the dry-run output and get explicit
go-ahead before `--apply` — overrides change who gets paged.

______________________________________________________________________

## Mode: `swap`

The common ask: *"I'm on PTO June 10–14, swap my on-call shifts to Priya."* This resolves
the user's on-call shifts in the PTO window across all their schedules (or one via
`--schedule`), clamps an override to **only the overlapping portion** of each shift, and
hands those windows to the covering user. **Dry-run by default.**

### Resolve names → IDs first (read-only)

`swap_shifts.py` works in PagerDuty IDs. Resolve names before calling it — all read-only:

```bash
pd rest:get -e /users/me                 # the calling user's ID (or --me someone else)
pd rest:get -e "/users?query=priya"      # the covering user's ID
pd rest:get -e /schedules                # schedule names → IDs (optional --schedule filter)
```

If a name has zero or multiple matches, **ask which — never guess** who covers an on-call.

### Run it

```bash
# 1. Preview (no change) — PTO dates interpreted in UTC, or the schedule's tz with --schedule:
python3 scripts/swap_shifts.py --from 2026-06-10 --to 2026-06-14 --cover <COVER_ID>

# 2. Only after explicit confirmation:
python3 scripts/swap_shifts.py --from 2026-06-10 --to 2026-06-14 --cover <COVER_ID> --apply
```

Flags: `--from` (required), `--to` (default = `--from`, single day), `--cover` (required),
`--me <ID>` (default: current token user), `--schedule <ID>` (default: all schedules the
user is on), `--tz <IANA>` (default: UTC; the schedule's own tz when `--schedule` is
given), `--apply`.

### Mandatory before any write

1. **Print the preview** the script emits — one numbered row per override (schedule,
   current on-call, covering user, absolute clamped window). The script does this in both
   dry-run and apply.
1. **Require explicit confirmation in the same session**, naming the rows (`apply`,
   `approve 1,3`). A vague "ok" with no preview on screen is not enough — re-print and ask.
1. **Never auto-apply.** There is no `--yes`. Even "just swap it" gets one preview + one
   explicit confirmation.

### Edge cases (handled by the script; call them out to the user)

- **No overlapping shift** → "nothing to do" for that schedule (not on call during PTO there).
- **Partial overlap** → override is clamped to the PTO window; the original on-call keeps
  the non-PTO part of the shift.
- **Covering user not on the schedule** → PagerDuty allows it, but warn they won't appear
  in the normal rotation. Allow only if the user confirms.
- **Multiple schedules** → one row per schedule; confirm the whole set before any write.

### Timezone discipline

- The timezone used to interpret PTO dates is echoed at the top of the preview. It is:
  the target schedule's own timezone when `--schedule <id>` is given; otherwise `--tz`
  if passed; otherwise UTC. `--from 06-10 --to 06-14` means `06-10T00:00` through
  `06-15T00:00` (exclusive) in that zone — all of the 14th covered.
- **Multiple schedules in different timezones:** the all-schedules run uses one window
  timezone for the whole batch. The on-call fetch is padded ±1 day so boundary shifts
  aren't missed, but for tz-sensitive edges run swap **per schedule** with `--schedule`
  (which adopts that schedule's tz) or pass an explicit `--tz`.
- Every timestamp shown and sent is offset-aware ISO 8601. Confirm if the user's region
  differs from the schedule's.

### After applying

Re-check with `pd rest:get -e "/oncalls?schedule_ids[]=<ID>&since=...&until=..."` to show
the covering user is now on call. To undo: remove the override in the PagerDuty UI
(Schedule → Overrides), which restores the original rotation.

______________________________________________________________________

## Setup: PagerDuty CLI

The scripts shell out to the PagerDuty CLI (`pd`). Install and authenticate once:

```bash
npm install -g @pagerduty/cli
pd login            # or set a token: pd config:set token <PD_API_TOKEN>
pd whoami           # verify
```

If `pd` is missing or unauthenticated, the scripts exit with an actionable message rather
than guessing. **Schedule IDs are resolved dynamically by name — you do not need to
pre-fill [`references/schedules.md`](references/schedules.md) for the skill to work.** That
file is an optional cache/override for when real schedule names don't match the built-in
patterns; the `_TODO_` placeholders there are not a setup blocker.

> Note: this is the first `apollo-eng-devops` skill to ship `scripts/`. The plugin's other
> skills use MCP servers; this one wraps the `pd` CLI by design so it also works outside a
> Claude session. The PagerDuty MCP (`incident-triage` uses it) is an alternative if you
> prefer no local CLI.

______________________________________________________________________

## Output discipline

- **Read modes** (`schedule`, `review`) never write. Print and summarize.
- **`override` is propose-never-apply**: show the dry-run REST call, get explicit
  confirmation, then `--apply`.
- Cite schedule/user IDs and PD incident IDs verbatim — never paraphrase who's on call.

______________________________________________________________________

## References

- [`references/schedules.md`](references/schedules.md) — DevOps/Platform schedule name→ID cache and the name-matching rules
- [`references/incident-review-rationale.md`](references/incident-review-rationale.md) — the weekly-review argument and recurring-vs-runbook-gap heuristics
