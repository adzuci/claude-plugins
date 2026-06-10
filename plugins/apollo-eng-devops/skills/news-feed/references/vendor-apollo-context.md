# Vendor Apollo Context

Use this reference after feed filtering and before final selection. It is not a substitute for Apps DB; Apps DB is the live ownership source, and gaps should be called out.

## Apps DB Lookup

- Data source: `collection://23bab2b3-b496-800a-b873-000b6835efe9`
- Search by vendor name first, then product names mentioned in the post.
- Use: `Name`, `Owner`, `Owner | Team`, `Users | Team`, `Status`, `Description`, `Website`, `Slack Channel`, `Notes`.
- Treat `Status: Active` as the strongest ownership signal.
- If this file says Apollo uses the vendor/product but Apps DB has no active matching record, flag `Apps DB gap`.
- Anthropic does not currently expose a reliable official RSS feed from its news page; use the configured HTML-listing fallback unless Anthropic later publishes a working feed.

## OpenAI

Apollo connection:

- Apollo uses OpenAI / ChatGPT as an internal engineering AI and API vendor.
- Apps DB currently has an `OpenAI | ChatGPT` record; use Apps DB for current owner and team.
- Relevant surfaces include model availability, API behavior, Codex, Responses/Agents APIs, ChatGPT Enterprise/admin controls, data retention, audit, security, SSO, compliance, and pricing.

Care about announcements when they affect:

- Internal AI workflows, coding agents, support tooling, analytics, or GTM productivity.
- Enterprise controls: SSO, audit logs, retention, data residency, workspace administration, or compliance posture.
- API/runtime changes that could change cost, latency, reliability, eval needs, or model-routing strategy.
- New agent tooling that could reduce toil or create new security review needs.

Default investment paths:

- Pilot with a narrow internal workflow and define evals before rollout.
- Route security/admin-control changes to DevOps/IT/Security owners found in Apps DB.
- For API changes, ask owning product/infra teams to assess cost, model quality, and data-handling implications.

## Anthropic

Apollo connection:

- Apollo engineers use Claude and Claude Code heavily for development workflows.
- Anthropic may appear as Claude, Claude Code, Anthropic, or Claude Enterprise in tools and ownership systems.
- If Apps DB lacks an active Anthropic/Claude record, flag `Apps DB gap`; that likely means the inventory is stale rather than that Apollo has no usage.

Care about announcements when they affect:

- Claude Code, Skills, MCP, enterprise admin/compliance, audit, data controls, API/model behavior, or long-running agent workflows.
- Security/compliance integrations such as DLP, CASB, audit events, admin APIs, or data retention.
- Model releases that change codegen, tool use, cost, latency, safety behavior, or eval requirements.

Default investment paths:

- Evaluate through engineer productivity, security/compliance controls, and compatibility with Apollo's skill/plugin workflows.
- If the announcement is about enterprise controls, route to the Claude Enterprise admin plus DevOps/Security.
- If it is about Claude Code or Skills, route to owners of Apollo's shared Claude/Codex marketplace.

## Cloudflare

Apollo connection:

- Apollo uses Cloudflare for edge network, DNS, CDN/caching, WAF/DDoS/security, bot protection, and customer-facing traffic reliability.
- Apps DB has a Cloudflare record; use it for current owner/team, notes, and support channel details.
- Some non-enterprise Cloudflare usage may exist outside the main enterprise account; call out mismatches or unclear ownership.

Care about announcements when they affect:

- DNS, CDN/cache, WAF, DDoS, bot protection, rules, SSL/TLS, load balancing, tunnels, Cloudflare One, Gateway, CASB, DLP, Access, audit logs, Terraform, Workers, AI Gateway, Workers AI, R2, Queues, or observability/logging.
- Security posture, traffic routing, incident response, account administration, access controls, or support/SLA expectations.
- Platform primitives that could reduce infra toil or move edge logic closer to users.

Default investment paths:

- For security or traffic-path changes, ask DevOps/Security to assess blast radius, configuration drift, and rollback path.
- For developer-platform changes, run a small proof of concept before adding another operational surface.
- For admin/compliance changes, compare the main enterprise account with any non-enterprise accounts and flag gaps.

## Grafana

Apollo connection:

- Apollo uses Grafana for observability and monitoring, including dashboards, alerting, logs, metrics, traces, and incident analysis.
- Apps DB has a `Grafana` record; use it for current owner/team and status.
- Relevant product areas include Grafana Cloud, dashboards, alerting, IRM, SLOs, Loki, Tempo, Mimir, Alloy, k6, synthetic monitoring, Kubernetes monitoring, OpenTelemetry, cost management, RBAC, Terraform provisioning, and Grafana Assistant.

Care about announcements when they affect:

- Alert quality, incident workflows, SLOs, on-call ergonomics, or Slack-based incident response.
- Observability cost, retention, sampling, cardinality, telemetry pipelines, or noisy log/trace reduction.
- Security and access controls such as RBAC, authentication, authorization, auditability, or provisioning changes.
- AI-assisted debugging, query troubleshooting, or assistant features that could reduce DevOps toil.
- Breaking changes or release behavior that could affect dashboards, Terraform-managed resources, data sources, or custom roles.

Default investment paths:

- For alerting/IRM/SLO changes, evaluate against Apollo's incident-response and alert-fatigue workflows before enabling broadly.
- For telemetry-cost or sampling changes, pilot on one high-volume service and compare cost, signal quality, and debugging coverage.
- For RBAC/provisioning changes, audit Terraform-managed Grafana roles and dashboard/data-source permissions before upgrade.
- For AI features, test against real Apollo incidents or dashboard-debugging tasks and verify data exposure boundaries.

## Google Cloud

Apollo connection:

- Apollo uses Google Cloud / GCP for production infrastructure and platform services.
- Search Apps DB for Google Cloud, GCP, Google Kubernetes Engine, BigQuery, Vertex AI, Gemini, Cloud SQL, Cloud CDN, and related products named in the announcement.
- Expected Apps DB match: `Google | Cloud Platform`.
- Treat missing active records for major GCP surfaces as an `Apps DB gap`; cloud inventory often splits ownership by product or team.

Care about announcements when they affect:

- Compute, networking, IAM, Kubernetes/GKE, data platforms, database reliability, security posture, auditability, regions, data residency, quotas, pricing, or support tiers.
- Gemini, Vertex AI, agent tooling, Cloud Assist, model serving, evaluation, observability, or AI-assisted operations.
- Deprecations, breaking changes, default-behavior changes, or migration deadlines on services Apollo likely runs.

Default investment paths:

- Route operational changes to the owning infrastructure team and verify Terraform/config impact.
- For AI platform changes, pilot against one internal workflow and confirm data-handling, cost, and access boundaries.
- For support or reliability changes, compare the release note against Apollo's support tier and incident-response expectations.

## PagerDuty

Apollo connection:

- Apollo likely uses PagerDuty for incident alerting, on-call schedules, escalation, and reliability workflows.
- Search Apps DB for PagerDuty, incident management, on-call, AIOps, and related integrations such as Slack or Microsoft Teams.
- Expected Apps DB match: `PagerDuty`.
- If Apps DB lacks an active PagerDuty record, flag `Apps DB gap` because on-call tooling should have a clear owner.

Care about announcements when they affect:

- AIOps, incident agents, event intelligence, alert grouping, automated triage, responder workflows, schedules, escalation policy behavior, postmortems, or Slack/Teams integrations.
- Reliability reporting, incident analytics, compliance, audit logs, access controls, or API behavior.
- Anything that changes who gets paged, when, and with what context.

Default investment paths:

- Test AI or automation features on historical incidents before enabling automated suppression, grouping, or recommendations.
- Route schedule/escalation changes to DevOps plus affected service owners.
- For Slack/Teams workflows, verify notification noise, permissions, and incident-command ergonomics.

## Slack

Apollo connection:

- Apollo uses Slack as a core collaboration and operational messaging system.
- Search Apps DB for Slack, Slack Enterprise, Slack AI, workflow automation, and internal Slack apps.
- Expected Apps DB match: `Slack`.
- If Apps DB lacks an active Slack record, flag `Apps DB gap`; Slack ownership should be explicit because it touches employee communications and app permissions.

Care about announcements when they affect:

- Slack AI, agents, workflow automation, enterprise search, app platform APIs, admin controls, retention, audit logs, data exports, DLP, SSO, Grid behavior, or app approval workflows.
- Changes that affect incident channels, product/support workflows, internal bots, or security review of Slack apps.

Default investment paths:

- For AI features, evaluate privacy, retention, channel scope, and workspace-level admin controls before rollout.
- For app-platform changes, route to owners of internal Slack apps and bot workflows.
- For security/admin changes, align with IT/Security and update Slack app approval or retention policies if needed.

## Atlassian / Jira

Apollo connection:

- Apollo likely uses Jira and Atlassian Cloud for planning, engineering workflow, ticketing, and possibly incident or support handoffs.
- Search Apps DB for Atlassian, Jira, Jira Service Management, Confluence, Rovo, and Atlassian Intelligence.
- Expected Apps DB match: `Jira`.
- If Apps DB has Jira but no Atlassian/Rovo ownership for AI features, flag the specific `Apps DB gap`.

Care about announcements when they affect:

- Atlassian Intelligence, Rovo, Jira agents, automation, admin controls, user permissions, app access settings, Forge/Connect changes, APIs, issue/work item semantics, data residency, audit, or compliance.
- Workflow changes that affect engineering planning, ticket routing, service management, or integrations with coding agents.

Default investment paths:

- For AI features, start with a constrained Jira workflow and verify data access, permissions, and admin controls.
- For API/platform changes, route to teams owning Jira automation, reporting, and internal integrations.
- For Rovo or agent features, assess whether they overlap with Cursor, Claude, Codex, or internal workflow agents.

## Cursor

Apollo connection:

- Apollo engineers may use Cursor as an AI coding environment or evaluate it alongside Claude Code, Codex, and other coding agents.
- Search Apps DB for Cursor, Anysphere, AI IDE, coding assistant, and related developer-productivity tooling.
- No active Cursor Apps DB match was found during initial implementation; re-check Apps DB at runtime before calling it a gap.
- If Apollo usage is known or likely but Apps DB lacks an active Cursor record, flag `Apps DB gap`.

Care about announcements when they affect:

- Cursor agents, Automations, Jira/Slack/GitHub integrations, enterprise admin, data controls, model routing, usage analytics, codebase indexing, MCP, memory, or pricing.
- Features that overlap with Apollo's Claude/Codex plugin marketplace or long-running agent workflows.

Default investment paths:

- Evaluate on one real engineering workflow with clear success criteria, code-access boundaries, and cost tracking.
- For integrations with Jira, Slack, or GitHub, confirm admin ownership and permission scope before broad enablement.
- Compare new agent or automation features against existing Claude/Codex workflows to avoid duplicative tool sprawl.
