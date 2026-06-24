# apollo-eng-devops

DevOps, SRE, and production reliability skills for Apollo engineers.

## Philosophy

**Ship it safely.** Every change to production carries risk. These skills encode Apollo's SRE philosophy: define what "good" looks like before shipping, measure it continuously, and respond to failures in a structured, blameless way.

These skills are grounded in the Google SRE Book and Apollo's internal operational patterns across GKE, Elasticsearch, MongoDB, Redpanda, and Sidekiq. They are useful for any Apollo engineer who ships code to production — not just the infra team.

## Skills

| Invoke command | Purpose |
|---|---|
| `/apollo-eng-devops:check-apdex` | Snowflake-first Apdex dip investigation with Grafana deep triage |
| `/apollo-eng-devops:devops` | SRE devops — applies reliability engineering to any production task |
| `/apollo-eng-devops:gameday` | MongoDB incident gameday drills for on-call practice |
| `/apollo-eng-devops:grafana-observability` | Grafana dashboard design and alert quality specialist |
| `/apollo-eng-devops:incident-response` | Incident commander guide for Apollo production incidents |
| `/apollo-eng-devops:incident-triage` | Triage Jira INCIDENT tickets and PD/Grafana alert follow-up |
| `/apollo-eng-devops:kubernetes-specialist` | Kubernetes debugging and rollout specialist — **invoke explicitly** (not auto-routed) |
| `/apollo-eng-devops:logs-ingestion-rate` | Investigate Apollo's Grafana Cloud logs ingestion rate alert and alert quality |
| `/apollo-eng-devops:news-feed` | Weekly vendor announcement triage for DevOps-relevant AI, security, observability, platform, and infrastructure changes |
| `/apollo-eng-devops:oncall` | DevOps + Platform PagerDuty schedule, review, swap, and override companion |
| `/apollo-eng-devops:oncall-handoff` | Daily or weekly DevOps PD handoff focused on the outgoing caller's on-call shift |
| `/apollo-eng-devops:sidekiq-worker-specialist` | Tune Sidekiq worker Helm values — max_workers, resources, autoscaling |
| `/apollo-eng-devops:systematic-debugging` | Four-phase root-cause debugging methodology (investigate → pattern → hypothesize → implement) |
| `/apollo-eng-devops:wtf-does-this-do` | First-pass explanation of unfamiliar skills, plugins, repos, or scripts |

## Skill Stacking

These skills are designed to be enabled simultaneously. Each skill handles a domain; the devops coordinates across all of them.

**Recommended combinations:**

- **Incident investigation**: `devops` + `/apollo-eng-devops:kubernetes-specialist` + `incident-response`
- **On-call handoff**: `oncall-handoff` + `oncall` + `incident-triage` + `grafana-observability`
- **New service launch**: `devops` + `grafana-observability`
- **Alert tuning sprint**: `grafana-observability` + `devops` (for SLO context)
- **Vendor announcement review**: `news-feed` + `grafana-observability` when Grafana changes affect dashboards, alerts, IRM, or telemetry cost
- **Logs ingestion alert**: `logs-ingestion-rate` + `grafana-observability`
- **Jira incident queue cleanup**: `incident-triage` + `oncall`
- **Mongo incident practice**: `gameday` + `incident-response`
- **Architecture design review**: `devops` (design review path)
- **Postmortem writing**: `incident-response`
- **Sidekiq worker specialist PR**: `sidekiq-worker-specialist` + `/apollo-eng-devops:kubernetes-specialist` (post-deploy verification)

## Example Prompts

| Prompt | Skills activated |
|---|---|
| "We're seeing 500s spike after today's deploy" | devops (incident path) + `/apollo-eng-devops:kubernetes-specialist` + incident-response |
| "Pod keeps restarting with OOMKilled" | `/apollo-eng-devops:kubernetes-specialist` OOMKilled triage |
| "Alert noise is too high in the payments service" | grafana-observability alert audit |
| "Investigate the logs ingestion rate alert" | logs-ingestion-rate |
| "Make a weekly on-call handoff artifact" | oncall-handoff |
| "Review unassigned production incidents" | incident-triage |
| "Who is on DevOps on-call next week?" | oncall schedule |
| "Run a MongoDB failover tabletop" | gameday |
| "Postmortem for Feb 14 incident" | incident-response postmortem template |
| "Design review: new async ingestion pipeline" | devops (design review path) |
| "We need SLOs for the Elasticsearch cluster" | devops (SLOs module) + grafana-observability |
| "Bump max_workers for my_queue_worker" | sidekiq-worker-specialist |
| "Add a new Sidekiq queue to production" | sidekiq-worker-specialist |

## When to Enable Each Skill

**`devops`** — Enable for any production-touching task. It sets the reliability frame for everything else.

**`kubernetes-specialist`** — Invoke explicitly via `/apollo-eng-devops:kubernetes-specialist` when working with pods, deployments, HPAs, node pools, or GKE-level issues. Does not auto-activate from natural-language prompts.

**`sidekiq-worker-specialist`** — Enable when editing `kubernetes/production/sidekiq-workers/values.yaml`: new queues, `max_workers` / `threads_per_pod` tuning, resource changes, or shared-cluster queue additions.

**`grafana-observability`** — Enable when creating or reviewing dashboards, tuning alerts, or auditing alert fatigue. Ensures every alert is actionable and every dashboard follows USE/RED method.

**`check-apdex`** — Invoke directly when checking whether Apollo Admin Apdex dipped. Starts with Snowflake and escalates to Grafana only for deep triage.

**`logs-ingestion-rate`** — Enable for Grafana Cloud logs ingestion spikes or alert `eetj859g01kw0f`. Confirms applicability first, then attributes log volume and recommends whether the alert should be tuned.

**`incident-response`** — Enable when declaring an incident, running a war room, writing stakeholder comms, or conducting a postmortem. Provides severity model, comms templates, and blameless postmortem structure.

**`incident-triage`** — Invoke directly when reviewing Jira INCIDENT tickets, reconciling PD-linked alerts, or cleaning up unassigned production incident queues.

**`oncall`** — Invoke directly for PagerDuty schedule review, weekly incident review, shift swaps, and proposed overrides.

**`oncall-handoff`** — Invoke directly when the outgoing DevOps on-call needs a daily or weekly handoff focused on their DevOps PD shift, Slack context, PagerDuty pages, Grafana evidence, Jira follow-up, and runbook gaps.

**`gameday`** — Invoke directly for MongoDB incident drills, tabletop scenarios, and on-call practice.

**`wtf-does-this-do`** — Invoke directly when you need to understand an unfamiliar skill, plugin, repo, script, or artifact before changing it.

## How apollo-eng-devops Complements apollo-eng

`apollo-eng` skills help you **ship code**: PR descriptions, security reviews, release posts.

`apollo-eng-devops` skills help you **ship it safely**: SLOs, runbooks, incident command, reliability design reviews.

Use both together when launching a significant feature: `apollo-eng` for the PR, `apollo-eng-devops` for the design review and rollout plan.
