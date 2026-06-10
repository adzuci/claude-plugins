# PagerDuty / Grafana Alert Tickets

The largest class of INCIDENT tickets by volume. PD auto-creates a Jira ticket whenever a Grafana/Prometheus alert fires (and sometimes when one resolves). They look like `[FIRING:N] <alert name> [<service-group>] (<labels>)`.

**Before applying the rules in this file, scan the title and labels against [`vendors.md`](vendors.md).** Many PD alerts fire because of a recognizable upstream vendor pattern (Shifter self-spam, Redis Cloud slowlog, Cloudflare 5XX bursts, etc.). Recognition collapses the investigation — the vendor entry tells you the known failure shape and routing decision in one step.

## Identification

A ticket is a PD alert if any of:

- Title starts with `[FIRING:` or `[RESOLVED:`.
- Description contains `zenprospect.pagerduty.com/incidents/` or `pagerduty.com/incidents/`.
- Reporter is a PD integration service account.
- Label includes `pagerduty`, `grafana-alert`, or `prometheus-alert`.

Examples from the queue:

- `INCIDENT-29126` — `[FIRING:1] High 5XX error count [Infra] Cloudflare (high devops)`
- `INCIDENT-29122` — `[FIRING:1] High Errors from Cloudflare Tunnel Pods [Infra] Cloudflare (high devops prod-app)`
- `INCIDENT-29054` / `INCIDENT-28316` — `High error rate on Sidekiq worker Crawler::SearchEngineLinkedinPersonUpdaterWorker on queue google_linkedin_update_crawler` (same alert, two firings)
- `INCIDENT-28981` — `[FIRING:1] DatasourceError [Growth] Pricing & Packaging (500 Update Plans)`
- `INCIDENT-28896` — `[FIRING:1] Potential Sev1 in progress [Infra] APM & Traces (...)`

## Field extraction

Pull these from the title and description:

- **PD incident URL** — first link in the description. The PD MCP (if available) tells you the canonical status (`triggered` / `acknowledged` / `resolved`).
- **Service group** — the bracketed tag in the title, e.g. `[Infra]`, `[Growth]`, `[Engagement]`. Maps to a Grafana folder / PD service, which usually has an owning team. Cite this in the proposed routing rationale.
- **Severity hints in labels** — `(high devops)`, `(high devops prod-app)`, `(Sev1)`, `(500 Update Plans)`. `high` and `Sev1` raise urgency floor; numeric volumes are blast-radius signal.
- **Metric snapshot** — `Value: A=1046, B=407, ...` lines show what fired. Use these to dedupe (same metric pattern + same service in a short window = same alert).

## Default routing

1. **PD service → team via the PD MCP** if available. `get_incident` returns the service; the service's escalation policy names the owning team. Use this in preference to the service-group tag, which is human-typed and can drift.
1. **Service-group tag fallback** when PD MCP is absent. Common mappings, but verify before posting a reroute comment:
   - `[Infra]` → DevOps / Infra
   - `[Growth]` → Growth pod (resolve via CODEOWNERS for the affected service)
   - `[Engagement]` → Engagement pod
   - `[APM & Traces]` → DevOps / Observability
1. **CODEOWNERS for the workload** when the alert names a specific worker, controller, or endpoint (e.g. `Crawler::SearchEngineLinkedinPersonUpdaterWorker`, `/api/v1/performance_metrics_record/health`). The class/path resolves the same way as a code finding — see `team-lookup.md`.

## PD status reconciliation

Many PD alert tickets are out of sync with their PD incident — but PD state and Jira state are **not** the same thing. The skill's job is to map PD signals to Jira proposals carefully:

**Important: a closed PD does NOT mean the Jira should close.** PD closes when the alerting condition stops firing. The Jira represents human follow-up: investigation, root cause, runbook gap, fix. Those outlive the PD.

For each PD-linked ticket, fetch PD status (`get_incident`) if MCP available, then propose:

| PD signal | Proposed Jira action |
| ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| PD `triggered`, aged > 30 min | Escalate in urgent skim. No state change yet; assign on-call responder if PD has one. |
| PD `acknowledged` by a named responder | Propose assignee = responder, transition Jira to **In Progress**. Ack means someone is investigating. |
| PD has comments/notes from a human responder (any state) | Propose transition to **In Progress** if not already. Comments are investigation evidence. |
| PD `resolved`, no human acks or comments (auto-resolved flap) | The resolved snapshot hides the responder — get the assignee-at-trigger from the log-entry timeline (see "Assignee source" below) before assuming there is none. Propose assignee = that responder, transition to **In Review** or leave Open + add `linked-pd-auto-resolved` comment. **Do not close.** |
| PD `resolved`, had human ack/comments, no follow-up Jira activity in 7+ days | **Gated.** Before proposing Close, extract any Slack URL from the PD notes/log entries and read the thread to confirm no open action items (see "Confirm Slack context before closing"). If the thread is clean → propose **Close (No Action)** with `linked-pd-resolved` comment citing the PD work. If a Slack link exists but can't be read → downgrade to **Ask assignee to confirm + close**. Closing represents human sign-off, not PD state. |
| PD `resolved`, Jira already has follow-up comments / linked PRs | Leave as-is — humans are working it. Note status in the row, propose no transition. |

If PD MCP isn't available, propose `needs PD verification` and link the PD URL in the comment — do not guess the PD state from the Jira title's `[FIRING:N]` / `[RESOLVED:N]` prefix alone, since that reflects the alert at ticket creation, not the current PD state.

### Assignee source

`get_incident` (CLI: `pd rest get -e /incidents/<ID>`) returns the **current** state. For an **auto-resolved** incident that snapshot is misleading: `assignments[]` and `acknowledgements[]` are empty and `last_status_change_by` is a `service_reference`, so it looks like nobody owned it. There almost always was an owner — PD's escalation policy assigns a human **at trigger time**, and that only appears in the log entries, not the resolved-state snapshot. Reading the snapshot alone makes the "assign the responder" batch look empty when it isn't.

When the snapshot shows no human responder, pull the timeline before falling back to cluster-owner-by-team — MCP: `list_log_entries`; CLI: `pd rest get -e /incidents/<ID>/log_entries`. Read in order:

- `trigger_log_entry` → `assignees[].summary` = who PD first assigned.
- `escalate_log_entry` → re-assignment hops (and to whom).
- `acknowledge_log_entry` → who, if anyone, acked.
- `notify_log_entry` → who PD paged.

Resolution order for the proposed Jira assignee, stating the basis in the row:

1. Human acker (`acknowledge_log_entry`) → basis "PD responder (acked)".
1. Assignee-at-trigger / escalation target (`trigger`/`escalate_log_entry`) → basis "PD assignee at trigger, no ack".
1. Cluster owner of the dedup canonical → basis "cluster owner".
1. None of the above → leave unassigned, route by Impacted Team.

Why: a real miss — a pass concluded "no responder to assign" for a batch of auto-resolved cron-OOM and mongos-health flaps from the resolved snapshot alone; the log entries showed every one had been paged and assigned to the be-platform / devops on-call, which was the correct routing all along.

### Why PD-closed isn't Jira-closed

- A PD incident closes when the alert stops firing. That can happen because the problem was fixed, because it auto-recovered (flap), or because someone silenced the alert.
- The Jira's purpose is the **human follow-up loop**: did we acknowledge, investigate, fix the root cause, file a runbook?
- A PD that auto-resolved with no human touch usually means the condition recovered on its own. The Jira should stay open until someone decides whether to investigate or to tune the alert — closing it silently loses signal.
- A PD that resolved after human ack + comments is closer to "done," but the Jira should still capture the outcome before closing: was there a fix? An accepted risk? A follow-up ticket?

### Confirm Slack context before closing

A PD `resolved` status plus a human resolution note is **not** sufficient to close the Jira. Investigation almost always continues in Slack, and the PD note is written before that follow-up lands.

Before proposing any Close (No Action) / resolve for a PD-resolved ticket:

1. Extract any Slack URL (`slack.com/archives/`, `<workspace>.slack.com/...`) from the PD incident's notes and log entries (`list_log_entries`).
1. Follow that link and read the thread. Confirm there are **no remaining action items** — no "still need to," no open follow-up ticket, no unresolved backlog.
1. Only if the thread is clean → propose Close. If a Slack link exists but you cannot read it (no access, dead link), **downgrade the proposal from Close to "Ask assignee to confirm + close"** rather than auto-closing.

Why: a real miss — a PD auto-marked `resolved` with a note ("worker fixed"); the skill proposed Close, but the Slack thread showed the worker's retry-set backlog was still draining and follow-up was unresolved. The note described the immediate fix, not the full follow-up loop. Slack is the source of truth for whether the human loop is done.

## Duplicate handling

PD alerts dedupe heavily because the same flapping condition fires repeatedly. Be aggressive but careful:

- **Same alert title + same service group + within 24h + both still Open** → near-certain duplicate. Canonical is the older ticket with more linked artifacts. Use `dup-merge` template.
- **Same alert title across a longer window (> 24h)** → likely a recurring failure mode, not a duplicate. Link with `Relates` and propose a runbook gap note.
- **Different alert titles but same PD service in the same firing window** → likely the same incident with multiple alert rules firing. Link with `Relates` and pick one as the "lead" for the postmortem.

Examples: INCIDENT-29054 + INCIDENT-28316 are the same Sidekiq crawler worker alert firing on two different days — these are a **recurring failure**, not duplicates. Link as `Relates`, flag the runbook gap.

## Vendor self-spam patterns

When a PD alert fires for a worker or service that calls an external vendor, **always check whether *Apollo* caused the failure before assuming the vendor failed.** Pattern is common enough to deserve its own triage step.

The flagship example is the **Shifter self-spam** pattern documented in [`vendors.md`](vendors.md):

- `Crawler::SearchEngineLinkedinPersonUpdaterWorker` errors burst with `Net::HTTPClientException: 403 "Forbidden"` wrapped as `RuntimeError("Something is wrong with VPN setup")`.
- The exception name suggests an upstream VPN/proxy outage, but in practice the cause is usually Apollo's outbound rate exceeding Shifter tolerance (the recurring pattern across INCIDENT-29534, 29054, 28316, 28094).
- **Triage step**: before staging a route to native-data with "Shifter outage" framing, query Tempo for `rate({span.net.peer.name=~".*shifter\\.io"})` over the alert window. Baseline is ~3–7 req/s. If our rate during the burst was 10–100× baseline (saw 167× in INCIDENT-29534), we caused it. The proposed action becomes "find what enqueued the surge," not "wait for Shifter to recover."

General rule: **if an alert names a worker/endpoint that touches an external vendor, do the cheap "our outbound rate" check first.** Vendor entries in `vendors.md` enumerate the recognition signals and the relevant Grafana queries.

## Urgent skim signals

A PD alert lifts to the urgent list when any of:

- PD status is `triggered` or `acknowledged` right now.
- Label includes `Sev1`, `Sev0`, `prod-app`, or the title contains `Potential Sev` / `Active`.
- Service group is `[Infra]` and the alert is on a customer-facing surface (`app.apollo.io`, Cloudflare, Mongo, ES).
- Metric snapshot shows error rate > 1% or 5XX count > 500 in the firing window.

## What a good triage outcome looks like

- **Acknowledged PD** → propose assignee = responder, transition to In Progress. Ack = investigation in flight.
- **PD with human comments, Jira still Open** → propose transition to In Progress. Comments = investigation.
- **Open PD, no assignee, no comments** → propose assignee = PD on-call responder; leave state Open until ack.
- **Auto-resolved PD, no human touch** → propose comment summarizing the flap; leave Open or move to In Review for someone to decide on tuning. Do not close.
- **Resolved PD with prior human ack, no Jira follow-up in 7+ days** → first extract any Slack URL from the PD notes/log entries and read the thread to confirm no open action items (see "Confirm Slack context before closing"). Thread clean → propose Close (No Action) with the PD work cited. Slack link present but unreadable → downgrade to "Ask assignee to confirm + close." A resolution note alone is not sign-off — the human loop is only done once Slack confirms it.
- **Recurring alert with no runbook** → propose linking the prior ticket as `Relates` + draft an INFRA ticket body for a runbook (do not create until approved).
- **Flapping alert with low signal** → propose surfacing to the alert owner with `pd-tune-this-alert` comment.
