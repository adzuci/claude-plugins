---
name: oncall
description: On-call companion for the DevOps + Platform PagerDuty rotations — render the next two weeks of primary/secondary schedule, review the last week of incidents for recurring failures and runbook gaps, and propose shift overrides. Activate when someone asks who is on call, wants the on-call schedule, wants to swap or propose a shift, or wants a weekly incident/runbook review.
argument-hint: "[schedule|review|override] [--weeks N] [--days N] [--teams devops,platform] [--apply]"
---

# On-call

A companion for the DevOps and Platform PagerDuty rotations. It wraps the PagerDuty CLI
(`pd`) with three modes: see the schedule, review the week's incidents, or propose a
shift override. **Read operations are safe; the override mode is propose-only by default**
and never writes without an explicit `--apply`.

Run the scripts from this skill's `scripts/` directory.

______________________________________________________________________

## Modes

```
/apollo-eng-devops:oncall [schedule | review | override] [flags]
```

| Mode | What it does | Default |
| --- | --- | --- |
| `schedule` | Render DevOps + Platform primary/secondary on-call for a window | **default when no mode given** |
| `review` | Skim the last week of incidents for recurring failures + runbook gaps | — |
| `override` | Propose a shift override / swap (dry-run unless `--apply`) | dry-run |

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
