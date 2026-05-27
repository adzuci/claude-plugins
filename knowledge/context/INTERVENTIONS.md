# INTERVENTIONS

> The enriched intervention pipeline table — one row per team × signal week ×
> metric, combining ML signals with Salesforce outcomes and resolution logic.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATASCIENCE.INTERVENTIONS` |
| **Grain** | One row per `(APOLLO_TEAM_ID, SIGNAL_WEEK, INTERVENTION_METRIC)` — `INTERVENTION_ID` is a hash of this composite key |
| **Row count** | <!-- TODO: run count --> |
| **Refresh cadence** | Interventions are qualified each Monday. SFDC updates to existing interventions are ingested and synced daily.
| **Trust level** | Authoritative for intervention pipeline state — prefer over `SALESFORCE__CUSTOMER_INTERVENTIONS` for signal-level analysis |
| **Owner** | Kaitlyn Maglietto (Analytics Engineering) |
| **DAG** | `signal_interventions_assessment` (dbt_apollo) |

## Description

This is the central table for the intervention pipeline. It qualifies weekly ML
and usage signals from `WEEKLY_TEAM_SIGNALS` to create interventions. The qualification
determines  whether it was actionable. It includes business logic for suppression (cooldown, open
intervention check), auto-closure, and signal resolution inference. Auto-closure and
signal resolution are determined based on the absence of the signal in a future week, if the
intervention is still open. This table also brings in SFDC data each day to give updates on the
intervention status, CE call data, and sentiment data. This is the primary table for measuring
intervention coverage, rep response rates, and signal-to-action effectiveness.

## Upstream Sources

| Source | Relationship |
|---|---|
| `ANALYTICS_DB.ANALYTICS_DATASCIENCE.WEEKLY_TEAM_SIGNALS` | Signal source — `INTERVENTION_ID` = `TEAM_WEEK_SIGNAL_TYPE_KEY` from that table |
| `ANALYTICS_DB.ANALYTICS.SALESFORCE__CUSTOMER_INTERVENTIONS` | SFDC outcomes — joined to get `SFDC_INTERVENTION_STATUS`, `DAYS_TO_COMPLETE`, `MOST_RECENT_SENTIMENT`, `TOTAL_ENGAGEMENT_CALLS` |
| Customer Engagement Intervention junction (SFDC) | Source of `TOTAL_ENGAGEMENT_CALLS` |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| `INTERVENTION_ID` | TEXT | Surrogate PK — hash of `(APOLLO_TEAM_ID, SIGNAL_WEEK, SIGNAL_SOURCE, SIGNAL_TYPE)` | Matches `TEAM_WEEK_SIGNAL_TYPE_KEY` in WEEKLY_TEAM_SIGNALS |
| `APOLLO_TEAM_ID` | TEXT | Apollo/ZP Team ID | Use this for joins to DIM_MONGO_TEAMS, DIM_TEAMS_DAILY_V2 |
| `SFDC_TEAM_ID` | TEXT | Salesforce Apollo Team ID | Not interchangeable with APOLLO_TEAM_ID |
| `SFDC_ACCOUNT_ID` | TEXT | Salesforce Account ID | |
| `SIGNAL_WEEK` | DATE | Monday of the week the signal was generated for | One week before `INTERVENTION_QUALIFIED_DATE` on normal runs |
| `INTERVENTION_QUALIFIED_DATE` | DATE | Date the intervention was created/qualified | Set to current_date() at assessment job runtime |
| `INTERVENTION_METRIC` | TEXT | The signal that triggered this intervention | e.g., `api_enrichment_credits_drop`, `ai_emails_sent_drop` |
| `INTERVENTION_NAME` | TEXT | Display name | e.g., "Lead Prioritization" |
| `INTERVENTION_TEAM` | TEXT | Executing team | e.g., GTME, LCM |
| `INTERVENTION_PILLAR` | TEXT | High-level pillar | e.g., Data Orchestration, Messaging Intelligence |
| `IS_ACTIONABLE` | BOOLEAN | Whether the intervention should be created for a rep to action | False = suppressed by cooldown or open intervention |
| `ACTIONABLE_REASON` | TEXT | Why actionable/suppressed | Values: `is_actionable`, `is_sev_one`, `has_open_intervention_on_metric`, `in_cooldown` |
| `IS_NEW_INTERVENTION` | BOOLEAN | True if this record's signal_week is the latest in the table | Used to determine resolution: prior weeks with no subsequent signal = resolved |
| `IS_SEV_ONE` | BOOLEAN | Severity 1 flag — bypasses qualification checks | |
| `INTERVENTION_STATUS` | TEXT | Resolved status combining SFDC input + auto-close logic | Values: Complete, Not Relevant, Auto Resolved, Not Actionable, Not Started, Pending, In Progress |
| `SFDC_INTERVENTION_STATUS` | TEXT | Raw status from Salesforce | Use `INTERVENTION_STATUS` for most analysis |
| `AUTO_CLOSED_REASON` | TEXT | Why auto-closed (if applicable) | Values: `auto_closed_resolution`, `auto_closed_cooldown`, `auto_closed_open_intervention` |
| `ASSIGNED_STATUS` | TEXT | Set to `auto_close` for non-actionable new interventions | Null for all other records |
| `SIGNAL_RESOLUTION_DATE` | DATE | Inferred date the underlying signal resolved | Null if signal still active |
| `DAYS_TO_COMPLETE` | INTEGER | Days taken or expected to complete | |
| `TOTAL_ENGAGEMENT_CALLS` | INTEGER | Count of customer engagement calls linked to this intervention via SFDC junction | |
| `MOST_RECENT_SENTIMENT` | TEXT | Latest rep-entered sentiment | Values: Positive, Neutral, Negative |
| `LAST_INTERVENTION_QUALIFIED_DATE` | DATE | Prior intervention date for same team + metric | Window function via LAG |
| `NEXT_INTERVENTION_QUALIFIED_DATE` | DATE | Next intervention date for same team + metric | Window function via LEAD |
| `LAST_INTERVENTION_CLOSED_DATE` | DATE | Most recent closed intervention date for same team + metric | Window function via LAG |
| `SIGNAL_OPS_METADATA` | OBJECT | JSON with display metrics for ops teams | Only populated for credit drops and AI messaging drop signals |
| `DESTINATION` | TEXT | System where intervention is created | e.g., `SFDC` |
| `EXPECTED_COMPLETION_DATE` | DATE | Target completion date | |
| `INTERVENTION_CLOSED_DATE` | DATE | Date closed | Null if still open |
| `GTME_OWNER_ID` | TEXT | The SFDC User ID of the GTME who owns the intervention, assigned by SFDC upon intervention creation | |
| `GTME_OWNER_NAME` | TEXT | The name of the GTME who owns the intervention, assigned by SFDC upon intervention creation | |

## How It's Used

### Common query patterns

```sql
-- Active (open) actionable interventions as of latest signal week
SELECT
    APOLLO_TEAM_ID
    , INTERVENTION_NAME
    , INTERVENTION_PILLAR
    , INTERVENTION_TEAM
    , SIGNAL_WEEK
    , INTERVENTION_QUALIFIED_DATE
    , INTERVENTION_STATUS
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.INTERVENTIONS
WHERE 1 = 1
  AND IS_ACTIONABLE = TRUE
  AND IS_NEW_INTERVENTION = TRUE;

-- Intervention actionability breakdown
SELECT
    IS_ACTIONABLE
    , ACTIONABLE_REASON
    , AUTO_CLOSED_REASON
    , COUNT(*) AS TOTAL_INTERVENTIONS
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.INTERVENTIONS
GROUP BY 1,2,3;

-- Intervention resolution rate by pillar (closed interventions)
SELECT
    INTERVENTION_PILLAR
    , COUNT(*) AS total_interventions
    , COUNT_IF(INTERVENTION_STATUS = 'Complete') AS completed
    , COUNT_IF(INTERVENTION_STATUS = 'Auto Resolved') AS auto_resolved
    , COUNT_IF(INTERVENTION_STATUS = 'Not Relevant') AS not_relevant
    , ROUND(completed / total_interventions * 100, 1) AS pct_complete
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.INTERVENTIONS
WHERE 1 = 1
  AND IS_ACTIONABLE = TRUE
GROUP BY 1
ORDER BY total_interventions DESC;

-- Suppression breakdown — why interventions didn't fire
SELECT
    ACTIONABLE_REASON
    , COUNT(*) AS count
FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.INTERVENTIONS
WHERE 1 = 1
  AND IS_NEW_INTERVENTION = TRUE
  AND IS_ACTIONABLE = FALSE
GROUP BY 1;
```

### Key consumers

- Signal interventions assessment pipeline
  (`signal_interventions_assessment`, `export_weekly_interventions_sfdc`)
- `ANALYTICS_DB.ANALYTICS.SALESFORCE__CUSTOMER_INTERVENTIONS` — receives
  exported records
- Intervention coverage and rep response rate reporting

## Known Issues & Gotchas

- **`SIGNAL_WEEK` ≠ `INTERVENTION_QUALIFIED_DATE`** — `SIGNAL_WEEK` is the
  week the signal was generated (typically one Monday prior).
  `INTERVENTION_QUALIFIED_DATE` is when the assessment job ran. Use
  `SIGNAL_WEEK` for signal timing analysis, `INTERVENTION_QUALIFIED_DATE` for
  when reps received it.
- **`IS_NEW_INTERVENTION = TRUE` for current-week only** — this flag resets
  every weekly run. For historical analysis of whether a signal was "new" at
  a specific point in time, use the current date to compare to the
  `INTERVENTION_QUALIFIED_DATE`.
- **`INTERVENTION_STATUS` vs `SFDC_INTERVENTION_STATUS`** —
  `INTERVENTION_STATUS` is the resolved field that layers auto-close logic on
  top of Salesforce. Use it for most analysis. `SFDC_INTERVENTION_STATUS` is
  the raw value.
- **`SIGNAL_OPS_METADATA` — this is the information provided in SFDC for the
actioning team.
- **`APOLLO_TEAM_ID` ≠ `SFDC_TEAM_ID`** — always join to team dimension
  tables using `APOLLO_TEAM_ID`.
- **Assessment job timing** — job normally runs the Monday after signal_week.
  Off-schedule runs cause `INTERVENTION_QUALIFIED_DATE` to drift from
  `SIGNAL_WEEK + 7 days`. Check both when debugging timing issues. SFDC data
  is ingested daily.
- **Intervention Metric vs Intervention Name** — the metric is the signal that
 triggered the intervention, the name is the display name of the intervention.
 Only the intervention name is passed through to SFDC.

## Business Terms

| Term | Definition |
|---|---|
| Signal | A detected customer health indicator from any source, normalized to team-week grain |
| Intervention | A call-to-action for reps triggered by a signal to engage a customer around a detected signal (churn, credit drop, usage decline) |
| Signal Week | The Monday of the week the underlying ML/usage signal was generated for |
| Intervention Qualified Date | The date the intervention was qualified, typically a week after the signal week |
| Cooldown | A suppression window preventing new interventions for the same team + metric when a recent one was just created or resolved |
| SEV 1 | Severity 1 — highest urgency classification, bypasses cooldown and open-intervention checks |
| Auto Resolved | Intervention auto-closed because the underlying signal stopped firing |
| Not Actionable | Intervention suppressed by cooldown or existing open intervention for the same metric |

## Related Tables

| Table | Relationship |
|---|---|
| `ANALYTICS_DB.ANALYTICS_DATASCIENCE.WEEKLY_TEAM_SIGNALS` | Upstream signal source; `INTERVENTION_ID` = `TEAM_WEEK_SIGNAL_TYPE_KEY` |
| `ANALYTICS_DB.ANALYTICS.SALESFORCE_CUSTOMER_INTERVENTIONS` | SFDC outcomes synced back via Fivetran |
| `ANALYTICS_DB.ANALYTICS.MAP_CUSTOMER_ENGAGEMENTS_TO_INTERVENTIONS` | Junction table to link engagements to interventions, required to join interventions and customer engagements |
| `ANALYTICS_DB.ANALYTICS.SALESFORCE_CUSTOMER_ENGAGEMENTS` | Customer engagement data, use `MAP_CUSTOMER_ENGAGEMENTS_TO_INTERVENTIONS` to join to interventions |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-06 | Created context file | Kaitlyn Maglietto |
