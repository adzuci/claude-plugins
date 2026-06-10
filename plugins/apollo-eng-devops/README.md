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
| `/apollo-eng-devops:kubernetes-specialist` | Kubernetes debugging and rollout specialist for Apollo's GKE clusters |
| `/apollo-eng-devops:grafana-observability` | Grafana dashboard design and alert quality specialist |
| `/apollo-eng-devops:logs-ingestion-rate` | Investigate Apollo's Grafana Cloud logs ingestion rate alert and alert quality |
| `/apollo-eng-devops:incident-response` | Incident commander guide for Apollo production incidents |
| `/apollo-eng-devops:news-feed` | Weekly vendor announcement triage for DevOps-relevant AI, security, observability, platform, and infrastructure changes |
| `/apollo-eng-devops:systematic-debugging` | Four-phase root-cause debugging methodology (investigate → pattern → hypothesize → implement) |

## Skill Stacking

These skills are designed to be enabled simultaneously. Each skill handles a domain; the devops coordinates across all of them.

**Recommended combinations:**

- **Incident investigation**: `devops` + `kubernetes-specialist` + `incident-response`
- **New service launch**: `devops` + `grafana-observability`
- **Alert tuning sprint**: `grafana-observability` + `devops` (for SLO context)
- **Vendor announcement review**: `news-feed` + `grafana-observability` when Grafana changes affect dashboards, alerts, IRM, or telemetry cost
- **Logs ingestion alert**: `logs-ingestion-rate` + `grafana-observability`
- **Architecture design review**: `devops` (design review path)
- **Postmortem writing**: `incident-response`

## Example Prompts

| Prompt | Skills activated |
|---|---|
| "We're seeing 500s spike after today's deploy" | devops (incident path) + kubernetes-specialist + incident-response |
| "Pod keeps restarting with OOMKilled" | kubernetes-specialist OOMKilled triage |
| "Alert noise is too high in the payments service" | grafana-observability alert audit |
| "Investigate the logs ingestion rate alert" | logs-ingestion-rate |
| "Postmortem for Feb 14 incident" | incident-response postmortem template |
| "Design review: new async ingestion pipeline" | devops (design review path) |
| "We need SLOs for the Elasticsearch cluster" | devops (SLOs module) + grafana-observability |

## When to Enable Each Skill

**`devops`** — Enable for any production-touching task. It sets the reliability frame for everything else.

**`kubernetes-specialist`** — Enable when working with pods, deployments, HPAs, node pools, or GKE-level issues. Provides structured kubectl workflows so debugging doesn't skip steps.

**`grafana-observability`** — Enable when creating or reviewing dashboards, tuning alerts, or auditing alert fatigue. Ensures every alert is actionable and every dashboard follows USE/RED method.

**`check-apdex`** — Invoke directly when checking whether Apollo Admin Apdex dipped. Starts with Snowflake and escalates to Grafana only for deep triage.

**`logs-ingestion-rate`** — Enable for Grafana Cloud logs ingestion spikes or alert `eetj859g01kw0f`. Confirms applicability first, then attributes log volume and recommends whether the alert should be tuned.

**`incident-response`** — Enable when declaring an incident, running a war room, writing stakeholder comms, or conducting a postmortem. Provides severity model, comms templates, and blameless postmortem structure.

## How apollo-eng-devops Complements apollo-eng

`apollo-eng` skills help you **ship code**: PR descriptions, security reviews, release posts.

`apollo-eng-devops` skills help you **ship it safely**: SLOs, runbooks, incident command, reliability design reviews.

Use both together when launching a significant feature: `apollo-eng` for the PR, `apollo-eng-devops` for the design review and rollout plan.
