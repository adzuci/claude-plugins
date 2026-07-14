# Live Incident Mode

Use this when the user is **currently paged** or working an **active** Mongo-related
outage — not for Jira ticket bookkeeping (`incident-triage`) or rehearsal (`gameday`).
This is the technical diagnostic playbook; `incident-response` still owns SEV
classification, comms cadence, and postmortem structure — apply both together.

Distilled from a real SEV-2 (`Mongo::Error::NoServerAvailable` against a sick mongos
pair). Treat every step as a starting decision tree, not a fixed script.

## When to invoke this mode

Reach for this mode when either signal is present:

- A **Mongo-flavored PagerDuty page**: `Mongo::Error::NoServerAvailable`, connection /
  server-selection errors, pool exhaustion, or 5xx alerts whose payload or traces carry a
  Mongo signature (a named mongos host, `ServerSelection`, ~30s timeouts).
- The **user is on an incident Zoom or thread about Mongo** — actively debugging a live
  outage, not filing paperwork.

If it's Jira bookkeeping use `incident-triage`; if it's a rehearsal use `gameday`. Pair
with `incident-response` for SEV/comms in all real-incident cases.

## 0. Before anything else

- Suggest the user turn `/fast` mode on — it materially shortens response time while
  paged.
- Confirm the MCPs you'll lean on are connected (Grafana at minimum; Glean/Granola if
  used). Setup is in [`mcp-setup.md`](mcp-setup.md); do this now, not mid-diagnosis,
  because MCP tools only load at session start.
- Check SSH/IAP access to the Mongo VMs early — see
  [`gcloud-access.md`](gcloud-access.md). Missing `roles/iap.tunnelResourceAccessor` or
  a missing VPN route blocks conntrack/fd/kernel-log forensics later; name the escalation
  path now, don't discover the gap mid-incident.
- Anchor every timestamp to a metric or log epoch. Never reconstruct the timeline from
  narrative memory — drift here wastes real time.

## 1. Pull the incident

Follow `../incident-triage/references/pd-access.md` for the MCP-vs-CLI decision (prefer
the `pd` CLI; don't loop-retry an auth-failing MCP):

```bash
pd rest get -e /incidents/<INCIDENT_ID>   # status, escalation, runbook_url if present
pd incident:alerts -i <INCIDENT_ID>       # alert payload: firing values, dashboard links
```

Extract the `runbook_url` and any dashboard/panel links before doing anything else.
Fetch the linked Notion runbook (`notion-fetch`) and follow its decision tree — the
queries below are a starting point when no runbook exists yet or it needs a live check.

## 2. Grafana decision-tree queries

Never read an aggregate when a per-instance view exists — aggregates hide a single sick
instance sagging behind healthy peers. Also check whether Grafana Cloud Adaptive Metrics
is stripping labels you need before trusting a "flat" panel.

| Question | Query pattern |
| --- | --- |
| Edge 5xx by status | `cloudflared_tunnel_response_by_code` (or the edge-5xx panel) broken out **by tunnel**, not summed |
| Deployment correlation | Overlay deploy/rollout markers on the same window before crediting a version |
| Per-mongos connection health | `sum by (instance) (mongodb_connections{cluster="<cluster>", role="mongos", state="current"})` — compare instances, don't sum them |
| Restart detection | `mongodb_instance_uptime_seconds` — a low value on one instance means it recently restarted |
| Server-side call volume (ground truth) | `mongodb_op_counters_total` — verify any client-side APM burst claim against this before believing it |

## 3. Tempo trace forensics

Search for the specific failure signature rather than browsing:

```
{resource.service.name="rails-api" && span.http.status_code=500 && kind=server && duration>29s}
```

Durations landing at **exactly ~30s** are a Mongo driver server-selection timeout, not
an application bug — there is no Mongo span because the driver never got a server.
Open one matching trace and read `exception.message`; it typically names the offending
seed-list mongos verbatim.

**Version A/B test**: during any rollout overlap window, filter the same query by
`resource.service.version` to implicate or exonerate a specific deploy. Test this for
the *rollback* pods too, not just the suspect deploy — a rollback's fresh pods can fail
for the same reason the original pods did (see traps below).

## 4. No-SSH diagnostics

When IAP/SSH access is missing or slow to provision:

- `https://api.apollo.io/admin/app_info/mongo_connection_pool` — refresh-sample across
  pods until one lands on a broken mongos pair (pool size `0` is the tell).
- `gcloud logging read` for kernel-level messages on the affected mongos VMs (read-only).

If you *do* have SSH, the read-only VM forensics block (dmesg / conntrack / ss / nstat
ListenOverflows / fd-vs-limit / mongos log grep) that proved decisive in the SEV-2 is in
[`gcloud-access.md`](gcloud-access.md), along with which mongos VM maps to which cluster.

## 5. Spawn watchers + a cron loop

For anything that outlasts a single diagnostic pass, spawn background Sonnet subagents
and a polling loop instead of manually re-checking:

- `slack-watch` — Glean search for thread deltas. Glean's index can lag minutes to an
  hour; say so in the watcher's output, don't imply it's real-time.
- `mongo-watch` — per-instance connection count + uptime, repeated.
- `impact-watch` — customer impact over the window; see
  [`customer-impact.md`](customer-impact.md) for the exact queries and framing.
- `granola-watch` (**if Granola MCP available** — see [`mcp-setup.md`](mcp-setup.md)) —
  when the incident is on a Zoom/Meet that Granola is recording, follow the live
  transcript so decisions said aloud aren't missed. Pattern:
  `mcp__granola__list_meetings` to find today's untitled/just-started meeting, then on
  each loop tick `mcp__granola__get_meeting_transcript` on that meeting, reporting only
  the **delta** since the last tick (new decisions, owners, action items) — not the whole
  transcript.
- A 3-minute `CronCreate` loop to re-run the impact/health queries (and the Granola
  transcript poll, if running).

**Every watcher prompt must explicitly instruct the subagent to reply via `SendMessage`
to `"main"`.** They will not do this on their own if it isn't spelled out.

## 6. Traps that cost real time

| Trap | What actually happened |
| --- | --- |
| "Time in Ruby" in APM | Mongo driver server-selection wait — no Mongo span is ever emitted, so the APM view attributes it to app code |
| "No slow traces" reads as healthy | The APM/Databases view can't see ops that never executed; absence of slow traces is not evidence of health |
| New Relic burst that looks huge | 30-minute background transactions can flush call counts into a single reported minute, producing a phantom burst — cross-check against `mongodb_op_counters_total` (server-side) before treating it as signal |
| Grafana Cloud Adaptive Metrics | Can silently strip labels a per-instance query depends on — check/exempt rules before trusting a flat-looking panel |
| Version correlation | A new pod can fail because it's **new** (cold connections), not because of new code. A rollback's fresh pods can reproduce the same failure — test rollback pods before crediting the rollback as a fix |
| Mass pod restarts | Re-roll mongos pair assignments and can **re-trigger** a connection storm. Don't mass-restart while a mongos pair is known-sick; rollback ≠ fix when the failure is churn-driven |

## 7. Comms and closeout

Hand off to `incident-response` for SEV classification, comms cadence, timeline
format, and postmortem requirements — don't duplicate that structure here.

- **Status page**: if impact is customer-visible for > 30 min or the incident is SEV-2+,
  post to Better Stack — trigger, Identified → Monitoring → Resolved flow, backdating,
  and customer-safe wording are in [`status-page.md`](status-page.md).
- **Impact number**: quantify excess failures, % of traffic, and per-tunnel split for the
  IC, status page, and Support using [`customer-impact.md`](customer-impact.md).

Resolution criteria should still require a stability window at baseline before declaring
done, and any workflow disabled during mitigation (e.g. a deploy gate) must be explicitly
re-enabled at closeout.
