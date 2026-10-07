---
name: check-mongo
description: "Read-only first-pass health check for one prod Mongo cluster (restarts, routers, replication, oplog, balancer): scripted table for humans, or headless via the shared checks.md spec (Argus) with an escalation handoff."
argument-hint: "[cluster] [--window 1h|6h|24h] [--role mongos|mongod|mongoc|all] [--gce] [--json]"
disable-model-invocation: true
---

# Check Mongo

Read-only triage of one **prod** Mongo cluster from Grafana Cloud metrics. It never runs
`ssh`, `mongosh`, or any write, and never auto-invokes. Prod only.

## Modes

**Human**: run the [Flow](#flow) below.

**Headless (Argus)**: no args, the prompt holds alert JSON, no skills load (`--bare`), so fetch `checks.md` via `gh api` (see [report-shape](references/report-shape.md)). Ask no questions: never ask, just report.

1. Cluster from `signals.cluster` (or the `cluster` label; strip `mongo-`); role/instance from `signals.role`, `signals.instance`. Unknown cluster: say so under Couldn't verify and stop.
1. Scripts usable (python3 present)? Run the Flow. Otherwise follow [`references/checks.md`](references/checks.md) by hand: each query via `mcp__grafana__query_prometheus` (instant, uid `grafanacloud-prom`, `<c>`, `<w>`=`1h`). Name every router and its state (up/down/absent).
1. If the gcloud MCP exists, `run_gcloud_command` for `compute operations list` and `compute instances describe` (`lastStartTimestamp`) only.
1. HUMAN-ONLY, list under Couldn't verify: `journalctl`, `dmesg`, mongos log, `uptime -s` (OOM kill vs self-exit).
1. Emit ONE report in the [Argus shape](references/report-shape.md) (\<=120 words). `evaluate.py --format argus` previews it.

## Arguments

| Argument | Default | Notes |
| --- | --- | --- |
| `cluster` | `main` | `mongo-main` style also works. Valid: `main`, `accounts`, `contacts`, `custom-objects`, `email`, `emailermessages`, `noncustomer`. Unknown: stop, exit 2, list them. |
| `--window` | `1h` | Look-back for restart queries. Max `24h`. Use `6h`+ to catch an older restart. |
| `--role` | `all` | Limit checks to one role. |
| `--gce` | off | Also run `scripts/gce_events.sh` (GCE operations, OOM log lines). Skipped if `gcloud` is missing. |
| `--json` | off | Print evaluator JSON instead of the table. |

## Preflight

Check these before step 1. A missing or unauthorized dependency is the most common
reason this skill stalls, and it is cheap to catch up front.

| Need | Required for | Verify | If missing |
| --- | --- | --- | --- |
| Grafana MCP | every check | `mcp__grafana__query_prometheus` is in the tool list | **Stop.** [mcp-setup.md](../mongo-specialist/references/mcp-setup.md), then restart the session |
| `gcloud` | `--gce` only | `command -v gcloud && gcloud auth list` | Run without `--gce` and list it under Couldn't verify. [gcloud-access.md](../mongo-specialist/references/gcloud-access.md) |
| `gcx` | muting an alert after triage | `command -v gcx` | Not needed for triage. [gcx-setup.md](../mute-alert/references/gcx-setup.md) |

Never run `gcloud auth login` or `gcx login` for the user. Print the command and let
them run it in their own terminal.

A call that is **refused by a permission prompt** is not the same as a dependency that
is missing. Say which call was refused and name the settings rule that would allow it
(e.g. `Bash(gcloud compute ssh <host>:*)`, `mcp__grafana__query_prometheus`). Never let
a refusal turn into a silent UNKNOWN row.

## Flow

1. Run [Preflight](#preflight). Grafana MCP not connected: stop and link the setup rather than reporting every check as UNKNOWN.
1. Build queries: `python scripts/promql.py --cluster <cluster> --window <window> [--role <role>]`. Exit 2 = bad input; report and stop.
1. Run **every** query with `mcp__grafana__query_prometheus` (uid `grafanacloud-prom`, `instant`, `endTime: now`). Never edit an expression or aggregate away `instance`.
1. Save one JSON keyed by query `id` (value = returned series list) to the scratchpad. Use `[]` for a query that errors or is empty; that becomes UNKNOWN, never OK.
1. Evaluate: `python scripts/evaluate.py --results <file> --cluster <cluster> [--role <role>] [--thresholds k=v] [--json]`.
1. With `--gce`, run `bash scripts/gce_events.sh --cluster <cluster> --window <window>` and append it. An empty OOM section is not proof of no OOM (see triage doc).
1. Print the report table (`check | status | evidence | next step`) and the overall status.

## Status legend

| Status | Meaning | Action |
| --- | --- | --- |
| OK | Check passed | None |
| WARN | Worth a look | Report; never escalate on WARN alone |
| ESCALATE | Likely incident | Print reasons and the one command the evaluator emits, then stop. Do not run it. |
| UNKNOWN | No data (label drop, query failure) | Check Grafana Explore; never call it healthy |

The escalation command is `/apollo-eng-devops:mongo-specialist <cluster> incident: <reasons>`.
Load [`host-restart-triage`](../mongo-specialist/references/host-restart-triage.md) for
restarts, router loss or memory, else `live-incident-mode.md`.

## Spec

[`references/checks.md`](references/checks.md) is the single source of truth for queries, thresholds, verdict rules and units. `tests/test_spec_sync.py` fails if the scripts drift from it. Override thresholds with `--thresholds k=v`; defaults are initial guesses.

## Guardrails

- Prod is read-only. Never print secrets or `ssh`.
- `gce_events.sh` allows only `compute operations list`, `logging read`, `auth list`.
- Check **all** routers, not just the alerting one.
- `up==0` or absent = process **or** exporter down; only a human on the host can tell which.

## See also

- [`host-restart-triage`](../mongo-specialist/references/host-restart-triage.md): steps for a restart or router ESCALATE.
- [`mongo-specialist`](../mongo-specialist/SKILL.md) and its [related skills](../mongo-specialist/references/related-mongo-skills.md).
- [`incident-response`](../incident-response/SKILL.md): declare and track when 2+ routers reset or any ESCALATE.
- [`systematic-debugging`](../systematic-debugging/SKILL.md): root-cause method once you have evidence.
- [`grafana-observability`](../grafana-observability/SKILL.md): alert tuning, the `up==0` alert gap.
- [`check-uptime`](../check-uptime/SKILL.md) and [`check-apdex`](../check-apdex/SKILL.md): site-level availability, not Mongo-level.
- Not for index work: use [`create-mongo-index`](../create-mongo-index/SKILL.md).
- [Mongo Alerts Runbook](https://www.notion.so/1ceab2b3b496800a9c1eea5d8d3f67d6).
