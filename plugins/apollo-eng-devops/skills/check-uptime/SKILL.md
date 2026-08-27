---
name: check-uptime
description: Pull uptime and availability from Better Stack (Better Uptime) and generate an availability report.
argument-hint: "[--from YYYY-MM-DD] [--to YYYY-MM-DD] [--monitor NAME_OR_ID]"
disable-model-invocation: true
---

# Check Uptime

Run this skill as `/apollo-eng-devops:check-uptime [args]`.

Pull uptime and availability data from Apollo's Better Stack (Better Uptime)
account and produce a severity-weighted markdown availability report for a time
window. Apollo's public status page is
[status.apollo.io](https://status.apollo.io), backed by Better Stack team
`t76664`. The numbers come from **monitors** (active HTTP/ping/port checks) and
**heartbeats** (services that ping a Better Stack URL on a schedule; a missed
ping counts as down).

## Severity Model

Not all downtime is equal, so the report weights it by tier:

| Tier | Weight | What it is |
|---|---:|---|
| user-facing | 1.0 | app.apollo.io, api.apollo.io, auth — surfaces users hit |
| background | 0.2 | Sidekiq/workers/cron/queues and all heartbeats |

**Background-job downtime is weighted below user-facing downtime** because a
failed cron or worker typically retries and is not directly user-visible, while
a downed frontend is immediately visible to customers. The headline number is a
severity-weighted mean (the plain unweighted mean is shown alongside for
reference). Unknown or unclassified monitors default to **user-facing** so
nothing critical is accidentally under-weighted. Tune `SEVERITY_WEIGHTS` in the
script to change the discount.

## Prerequisite: API Token

Set a Better Stack Uptime API token in the `BETTERSTACK_API_TOKEN` environment
variable (Better Stack dashboard → **Uptime → API tokens**). If it is unset the
script exits with a message. The token is sent as a bearer token and is never
printed.

## Usage

Run the script — this is the primary path:

```bash
python scripts/check_uptime.py [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--monitor NAME_OR_ID]
```

All arguments are optional.

| Argument | Default | Meaning |
|---|---:|---|
| `--from YYYY-MM-DD` | 30 days ago | Start of the reporting window |
| `--to YYYY-MM-DD` | today | End of the reporting window |
| `--monitor NAME_OR_ID` | all monitors | Limit to one monitor by `pronounceable_name` (substring, case-insensitive) or numeric id |

The script lists monitors, pulls per-monitor SLA, lists v3 incidents and
heartbeats, classifies each into a severity tier (heartbeats forced to
background), and prints the report below. For raw endpoint/curl detail — SLA,
incidents, heartbeats, pagination, durations-in-seconds — see
[`references/betterstack-api.md`](references/betterstack-api.md).

## Report Format

```markdown
# Apollo Uptime Report

Window: {FROM_DATE} → {TO_DATE} (30 days)
Source: Better Stack team t76664 (status.apollo.io)

Overall availability (severity-weighted): 99.96%
Unweighted mean (reference): 99.68%
Background-job downtime is treated as lower impact than user-facing
(app.apollo.io) downtime, so it moves the headline number less.

Currently down (user-facing): none

## User-facing monitors

| Monitor | Availability | Downtime | Incidents |
|---|---:|---:|---:|
| app.apollo.io | 99.98% | 8m 12s | 1 |
| api.apollo.io | 99.99% | 4m 03s | 1 |
| auth.apollo.io | 99.82% | 1h 34m | 2 |

## Background jobs (lower severity)

These are jobs, workers, and heartbeats. Downtime here is weighted below
user-facing surfaces because a failed background job typically retries and is
not directly user-visible.

| Monitor | Availability | Downtime | Incidents |
|---|---:|---:|---:|
| sidekiq heartbeat | 98.90% | 1h 12m | 3 |

## Recent incidents

- **auth.apollo.io timeout** — started {FROM_DATE} 09:11 UTC, resolved
  {FROM_DATE} 10:45 UTC
```

If no incidents fall in the window, the report says "No incidents in this
window."

## Guardrails

- Do not print the API token or paste it into the report.
- Availability is reported as percentages; durations are converted out of raw
  seconds.
- The report states the exact window and the team/source (`t76664`,
  status.apollo.io) so the reader knows where the numbers come from.
- If the API returns an error or empty set, say so plainly rather than inferring
  availability.
- This skill is read-only — do not open, resolve, or modify incidents or
  monitors.
