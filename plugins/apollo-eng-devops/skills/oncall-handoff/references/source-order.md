# Source Order

Start with the caller's DevOps on-call scope and only widen when the evidence connects
directly to DevOps ownership, customer impact, a Sev0/Sev1 incident, or a handoff action.

## Primary Scope

- DevOps PagerDuty services and escalation policies, especially `devops-high-priority`,
  `devops-low-priority`, and Infrastructure escalation policy pages.
- The caller's resolved DevOps shift window from PagerDuty, or the explicit shift window
  supplied by the caller.
- Infrastructure/DevOps Slack channels and threads.
- Grafana alerts owned by DevOps or infrastructure.
- Jira INCIDENT tickets only when linked to DevOps-owned PD/Grafana/Slack evidence.

## Out Of Scope By Default

- Native Data, Data Platform, BE Platform, CDP, Integrations, CI flaky-test, and other
  non-DevOps rotations.
- Company-wide PD queue cleanup.
- Resolved non-DevOps alerts with no Slack thread or DevOps action.

Mention out-of-scope incidents only in a short "FYI / excluded" line if they are Sev0/Sev1,
customer-impacting, routed through DevOps, or explain DevOps noise. Do not spend the report
on Native Data unless the caller explicitly asks.

## Source Order

1. **PagerDuty DevOps scan**: start from the existing on-call review primitive, but filter
   its results down to the caller's DevOps rotation before summarizing:

   ```bash
   cd plugins/apollo-eng-devops/skills/oncall
   # N = the resolved lookback from preflight (1 for daily, 7 for weekly, or --days N).
   python3 scripts/incident_review.py --days N
   ```

   Use its recurring-alert and no-runbook output as a raw signal, not the final scope. Keep
   DevOps-owned pages first, then deepen only alerts that are active, repeated, high
   severity, in the caller's shift, or likely to need next-on-call action.

   Caveat: `incident_review.py` only accepts `--days` and always anchors its window to the
   current UTC time. It cannot honor a backdated `--date` or a shift-aligned start/end. When
   the handoff window is backdated or shift-scoped, treat the script output as a recent-incident
   signal only, then re-scope PD incidents to the resolved `since`/`until` window from preflight
   using the PagerDuty MCP/CLI time-range filters before summarizing. Widen `--days` enough to
   cover a backdated window, then filter back down to the printed window.

1. **Slack context**: read the DevOps handoff channels first:

   Verify channel IDs periodically; renamed or archived Slack channels can make this table
   stale.

   | Channel | Purpose |
   | --- | --- |
   | `#xfn-h-devops` / `#xfn-team-devops` (`C69FJ9NEM`) | Cross-team DevOps requests, on-call mentions, and handoff context. |
   | `#infrastructure-alerts` / `#eng-infrastructure-alerts` (`CCHSWB3DK`) | Infrastructure alert bot messages and alert threads. |
   | `#incident-response-sev0-sev1` (`C0362RC2GR2`) | Critical incident context. |
   | `#team-devops-internal` (`C03ELRU6F7X`) | Daily handoff target when a critical issue occurred. |

   Prefer messages inside the caller's shift window. Include surrounding context outside
   the shift only when it explains an unresolved issue, a handoff ask, or a repeated page.
   Read linked Slack threads from PD notes or Jira before proposing any "resolved / no
   action" outcome. Slack thread context is required because PD resolution is not the same
   as human follow-up completion.

1. **PagerDuty details**: for each relevant DevOps PD incident, collect status,
   responders, service, notes, timestamps, and linked Slack/Jira/Grafana URLs. Use current
   PD status; do not infer state from `[FIRING]` or `[RESOLVED]` in an old title. If a PD
   search returns non-DevOps services, exclude them unless they have a direct DevOps
   handoff action.

1. **Jira follow-up state**: use the `incident-triage` skill's PD reconciliation rules to
   identify DevOps-linked INCIDENT tickets that need assignment, status updates, dedupe,
   comments, or follow-up tickets. Stage proposals only.

1. **Grafana evidence**: for active, repeated, high-severity, or high-blast-radius alerts,
   use `grafana-observability` principles:

   - confirm user-facing impact using RED signals when possible;
   - check saturation/resource context using USE signals for infrastructure;
   - inspect alert actionability and runbook annotations;
   - invoke `logs-ingestion-rate` only for its exact alert UID/name.

1. **Runbooks and guidelines**: for every alert without a runbook signal, search
   Notion/Glean for an existing runbook. Classify each result:

   | Result | Proposal |
   | --- | --- |
   | Good runbook found | Propose linking it from the alert/Jira/PD context. |
   | Partial or stale runbook found | Propose the exact update needed. |
   | No runbook found | Propose creating a stub runbook or INFRA ticket. |
   | Search unavailable | Mark as unverified and include the missing access/tool. |

   Also compare the finding against
   [DevOps / Infrastructure Oncall Guidelines](https://app.notion.com/p/32fab2b3b49680699bf1c1191364dc30)
   (`32fab2b3b49680699bf1c1191364dc30`). If the link breaks, search Notion/Glean by title
   and ID. If the guideline page lacks the process, dashboard, tool-access, escalation, or
   handoff detail needed to avoid repeating the issue, propose a guideline gap update.
