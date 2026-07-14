---
name: mongo-specialist
description: Manual-invocation only. Shared Apollo MongoDB operations context for safe read-only triage, routing, escalation, and links to cluster, channel, TapData, people, and related-skill references. Run via /apollo-eng-devops:mongo-specialist.
argument-hint: optional model, collection, cluster, incident, or Mongo question
disable-model-invocation: true
---

# Mongo Specialist

Use this as the shared Apollo MongoDB context layer. It is not a task-specific
runbook; it helps other skills and operators find the right Mongo facts, commands,
channels, and consult targets without duplicating stale data.

## Safety boundary

Default to read-only investigation. Do **not** run production writes, topology changes,
index creation/drop commands, balancer changes, chunk moves, shard changes, Atlas writes,
or `mongo-upgrade` actions. If a write might be needed, provide the exact human-run
command with warnings, prerequisites, and an approval/escalation path.

Use an ephemeral Rails console or approved runbook path for production inspection; avoid
mutating live serving pods. Never trust a Mongoid client name by vibe: verify the actual
database and cluster before making recommendations.

## Workflow

1. Classify the task: index creation, unused index cleanup, index discrepancy, sharding,
   **live incident** (currently paged / active outage), collection change audit, access,
   or architecture lookup.
1. If the task is a live incident — a Mongo-flavored PagerDuty page
   (`NoServerAvailable`, connection errors, Mongo-signature 5xx) or a user actively on an
   incident Zoom/thread about Mongo — load
   [`references/live-incident-mode.md`](references/live-incident-mode.md) first. It is the
   technical diagnostic playbook (PagerDuty/Grafana/Tempo triage, watcher subagents
   including Granola transcript follow-along, known traps) and points to the access,
   status-page, and impact references below. Pair it with `incident-response` for
   SEV/comms; use `incident-triage` instead if this is Jira bookkeeping rather than an
   active page, and `gameday` instead if this is a rehearsal, not a real incident.
1. Load only the other reference files that are relevant:
   - `references/read-only-commands.md` for safe inspection commands.
   - `references/mongo-clusters.md` for current known client/cluster mapping, the prod
     mongos cluster inventory (ports/counts/hostnames), pod→mongos distribution, and
     staging SRV endpoints.
   - `references/gcloud-access.md` for gcloud CLI setup, prod/staging projects, SSH to
     Mongo VMs (`--internal-ip`), and the read-only VM forensics block.
   - `references/mcp-setup.md` for enabling the Grafana, Glean, and Granola MCPs.
   - `references/status-page.md` for when and how to post to Better Stack.
   - `references/customer-impact.md` for quantifying customer impact live.
   - `references/slack-channels.md` for escalation and announcement channels.
   - `references/tapdata.md` for Mason/TapData guidance.
   - `references/mongo-people.md` for evidence-based consult targets.
   - `references/related-mongo-skills.md` for which specialized skill should own the task.
1. Cite stale-prone facts as stale-prone. If the decision is important or production
   impacting, tell the user how to verify the current value before acting.
1. Keep the output short and operator-facing: what is known, what is uncertain, what to
   check next, and where to coordinate.

## Delegation

Prefer the narrower skill when the task matches one:

- Use `/apollo-eng-devops:create-mongo-index` for Mongo index creation planning.
- Use `/apollo-eng-devops:gameday` for Mongo incident tabletop drills (rehearsal, not a
  real page).
- Use `/apollo-eng-devops:incident-response` alongside live-incident-mode for SEV
  classification, comms cadence, and postmortems during a real incident.
- Use `/apollo-eng-devops:incident-triage` for Jira INCIDENT ticket bookkeeping.
- Use `/apollo-eng:mongo-pr-guard` for Mongo PR safety review.
- Use repo-local `mongo-index-discrepancies`, `mongo-unused-indexes`,
  `mongo-shard-collection`, or `mongo-collection-check` when those are available and the
  task exactly matches them. These are not shipped with this plugin; confirm they are
  installed in the current workspace before expecting them to run.

## References

- [`references/live-incident-mode.md`](references/live-incident-mode.md) — live incident
  technical diagnostic playbook
- [`references/gcloud-access.md`](references/gcloud-access.md) — gcloud CLI, VM SSH, and
  read-only forensics
- [`references/mcp-setup.md`](references/mcp-setup.md) — Grafana/Glean/Granola MCP setup
- [`references/status-page.md`](references/status-page.md) — Better Stack status-page
  guidance
- [`references/customer-impact.md`](references/customer-impact.md) — quantifying customer
  impact
- [`references/mongo-clusters.md`](references/mongo-clusters.md)
- [`references/slack-channels.md`](references/slack-channels.md)
- [`references/tapdata.md`](references/tapdata.md)
- [`references/mongo-people.md`](references/mongo-people.md)
- [`references/related-mongo-skills.md`](references/related-mongo-skills.md)
- [`references/read-only-commands.md`](references/read-only-commands.md)
