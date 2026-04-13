# REP_ACTIVITY_LOG_BY_CONTACT

> One row per sales rep activity event, spanning emails, calls, meetings, opportunity field changes, and sequence contacts — linked to the contact involved.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.REP_ACTIVITY_LOG_BY_CONTACT` |
| **Grain** | One row per activity event (unique_key = surrogate from employee_salesforce_id + entity_id + activity_timestamp_utc + apollo_contact_id + entity_type + activity_type + is_outbound) |
| **Row count** | ~31.9M (as of 2026-03-20) |
| **Date range** | 2015-06-03 to present |
| **Refresh cadence** | Daily (dbt Cloud — `dbt_apollo` project) |
| **Trust level** | Authoritative |
| **Owner** | Kaitlyn Maglietto (dbt model author) |
| **DAG** | dbt Cloud / `dbt_apollo` project |

## Description

`REP_ACTIVITY_LOG_BY_CONTACT` is the canonical fact table for sales rep activity reporting at Apollo. It consolidates all outbound and inbound rep touchpoints — emails, calls, meetings, opportunity field changes, and sequence enrollments — into a single activity log linked to the contact involved. Each record represents one discrete activity event performed by or attributed to a rep, with full context on the rep's org hierarchy (manager, L2 manager, position), the Salesforce account and contact, and whether the activity was inbound or outbound. Looker is the primary consumer, powering sales activity dashboards and reporting.

## Upstream Sources

| Source | Relationship |
|---|---|
| `dim_apollo_emailer_messages` | Email activities + sequence_step_position |
| `dim_mongo_emailer_steps` | Sequence step position for call activities (via emailer_step_id) |
| `FCT_MONGO_PHONE_CALLS` | Call activities |
| Calendar events / meetings data | Meeting activities |
| Salesforce opportunity field history | Opportunity change activities (opp_change_*) |
| `dim_salesforce_contacts` | Salesforce contact + account enrichment |
| `dim_salesforce_accounts` | Account name enrichment |
| `dim_salesforce_user_allocation` | Rep position, manager, L2 manager at time of activity |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| `UNIQUE_KEY` | TEXT | Surrogate key — hash of employee_salesforce_id, entity_id, activity_timestamp_utc, apollo_contact_id, entity_type, activity_type, is_outbound | NOT NULL, unique — dbt tested |
| `EMPLOYEE_SALESFORCE_ID` | TEXT | Salesforce User ID of the rep | Join key to SF user tables |
| `EMPLOYEE_NAME` | TEXT | Full name of the rep | |
| `ENTITY_TYPE` | TEXT | Broad activity category: `email`, `call`, `meeting`, `opportunity`, `contact_sequence` | NOT NULL — dbt tested |
| `ACTIVITY_TYPE` | TEXT | Granular activity label (see full list below) | NOT NULL — dbt tested |
| `IS_OUTBOUND` | BOOLEAN | True = rep-initiated; False = customer-initiated. Defaults to true for activities without a clear direction (opp changes, sequence contacts) | Use to filter inbound vs outbound |
| `ACTIVITY_TIMESTAMP_PT` | TIMESTAMP_NTZ | Pacific Time timestamp of the activity | Primary date column — use for time-based filtering |
| `ENTITY_ID` | TEXT | ID of the underlying record (email id, call id, meeting id, etc.) | NOT NULL — dbt tested |
| `ENTITY_ID_TYPE` | TEXT | Indicates which table entity_id references (e.g. `emailer_messages_id`, `phone_calls_id`, `calendar_event_id`) | Use to know how to join back to source |
| `APOLLO_CONTACT_ID` | TEXT | Apollo internal contact ID. Nullable — null for downloaded emails and some calls | |
| `CALL_DURATION_SECONDS` | NUMBER | Duration in seconds. Only populated for call activities | Null for non-call rows |
| `SEQUENCE_STEP_POSITION` | TEXT | Emailer step position within the sequence. Populated for email and call activities | Null for meetings, opp changes, sequence contacts |
| `IS_NEW_BUSINESS_CONTACT` | BOOLEAN | Meeting only: true if contact has no scheduled meeting in past 180 days | Null for non-meeting rows |
| `IS_NEW_BUSINESS_MEETING` | BOOLEAN | Meeting only: true when ALL matched contacts on the meeting are new business contacts | Null for non-meeting rows |
| `SALESFORCE_CONTACT_ID` | TEXT | SF Contact ID (via dim_salesforce_contacts join). Nullable | |
| `SALESFORCE_ACCOUNT_ID` | TEXT | SF Account ID. Nullable | |
| `SALESFORCE_ACCOUNT_NAME` | TEXT | SF Account name. Nullable | |
| `EMPLOYEE_POSITION_NAME` | TEXT | Rep's position at time of activity (from user allocation). Nullable if no allocation record exists | Point-in-time — reflects org at activity date |
| `EMPLOYEE_MANAGER_NAME` | TEXT | Rep's direct manager at time of activity. Nullable | Point-in-time |
| `EMPLOYEE_L2_MANAGER_NAME` | TEXT | Rep's L2 manager at time of activity. Nullable | Point-in-time |

### ACTIVITY_TYPE values (full list)

**Email:** `email_sent`, `email_delivered`, `email_opened`, `email_replied`, `email_completed`, `email_bounced`, `email_spam_blocked`, `email_interested`

**Call:** `call_completed`, `call_logged`, `call_missed`, `call_answered_by_human`, `call_connected`, `call_not_made_via_apollo`

**Meeting:** `meeting_scheduled_assigned_to_rep`, `meeting_held`, `meeting_attended`, `meeting_cancelled`, `meeting_rescheduled`

**Opportunity (field changes):** `opp_change_created`, `opp_change_stage_name`, `opp_change_close_date`, `opp_change_arr_value`, `opp_change_owner_id`

**Sequence:** `net_new_contact_added_to_sequence`

### ENTITY_TYPE distribution (as of 2026-03-20)

| Entity Type | Row Count |
|---|---|
| email | ~22.1M |
| opportunity | ~7.2M |
| call | ~1.8M |
| meeting | ~482K |
| contact_sequence | ~341K |

## How It's Used

### Common query patterns

**Activity volume by rep and channel (core reporting pattern):**
```sql
SELECT
    employee_name,
    entity_type,
    activity_type,
    DATE_TRUNC('week', activity_timestamp_pt) AS week,
    COUNT(*) AS activity_count
FROM ANALYTICS_DB.ANALYTICS.REP_ACTIVITY_LOG_BY_CONTACT
WHERE is_outbound = TRUE
  AND activity_timestamp_pt >= DATEADD('day', -30, CURRENT_DATE())
GROUP BY 1, 2, 3, 4
ORDER BY 4 DESC, 5 DESC;
```

**Contact & account enrichment join pattern (from Looker — canonical):**
```sql
-- Join to DIM_SALESFORCE_CONTACTS via salesforce_contact_id
-- Join to DIM_SALESFORCE_ACCOUNTS via salesforce_account_id
-- Both are LEFT JOINs — activity rows without a matched SF contact/account are kept
SELECT
    r.employee_l2_manager_name,
    r.employee_manager_name,
    r.employee_name,
    CASE WHEN c.IS_DIRECTOR_OR_ABOVE THEN 'Yes' ELSE 'No' END AS is_director_or_above,
    a.ACCOUNT_SUB_SEGMENT,
    COUNT(DISTINCT CASE WHEN r.activity_type = 'meeting_scheduled_assigned_to_rep' THEN r.entity_id END) AS count_meeting_scheduled
FROM ANALYTICS_DB.ANALYTICS.REP_ACTIVITY_LOG_BY_CONTACT r
LEFT JOIN ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_CONTACTS c
    ON r.salesforce_contact_id = c.ID
LEFT JOIN ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_ACCOUNTS a
    ON r.salesforce_account_id = a.ID
WHERE r.activity_timestamp_pt >= <date_filter>
GROUP BY 1, 2, 3, 4, 5;
```
Note: Looker filters on `IS_DIRECTOR_OR_ABOVE` using `OR (IS_DIRECTOR_OR_ABOVE = 0)` to include nulls — this is a "Yes or No" filter pattern that includes all non-director rows plus nulls.

**New business meetings (outbound, non-repeat contacts):**
```sql
SELECT employee_name, employee_manager_name, COUNT(*) AS new_biz_meetings
FROM ANALYTICS_DB.ANALYTICS.REP_ACTIVITY_LOG_BY_CONTACT
WHERE entity_type = 'meeting'
  AND is_new_business_meeting = TRUE
  AND activity_timestamp_pt >= DATEADD('day', -90, CURRENT_DATE())
GROUP BY 1, 2
ORDER BY 3 DESC;
```

**Sequence email funnel (sent → delivered → opened → replied):**
```sql
SELECT
    activity_type,
    COUNT(*) AS events
FROM ANALYTICS_DB.ANALYTICS.REP_ACTIVITY_LOG_BY_CONTACT
WHERE entity_type = 'email'
  AND activity_type IN ('email_sent','email_delivered','email_opened','email_replied')
GROUP BY 1;
```

### Key consumers

- **Looker — AE/AM Activity Dashboard** (`aeam_activity_dashboard`, `centralized` model, `rep_activity_log_by_contact` explore) — primary consumer (~11K queries/90d). Tiles: Total Emails Sent, Calls Logged, Total Meetings, and a combined rep-level summary table. All activity tiles default to `is_outbound = Yes`. Dashboard filters: Is Director+?, Employee Name, Manager L1/L2, Position, Date.
- **Metaplane** — data quality monitoring (~339 queries/90d).
- **Kaitlyn Maglietto** — model owner, active dbt development.
- **John Choi, Michelle Chang, Howie Chan** — ad hoc sales reporting and analysis.
- **Leo Liu, William Masket** — leadership and business analytics queries.

## Known Issues & Gotchas

- **MAX date of 9999-12-30**: A sentinel/placeholder date appears in the data — filter `activity_timestamp_pt < '2100-01-01'` if doing date range work to avoid polluting aggregations.
- **APOLLO_CONTACT_ID is nullable**: Downloaded emails and some phone calls have no linked contact. Do not use an inner join on this field if you want complete activity counts.
- **EMPLOYEE_POSITION_NAME / manager fields are nullable**: Null when no User Allocation record exists for the rep at the time of the activity (e.g. new hires, reps without allocation history).
- **IS_OUTBOUND defaults to true**: For opportunity field changes and sequence contact additions, `is_outbound = TRUE` is the default — not because they're truly outbound, but because there's no inbound/outbound distinction for those activity types. Filter on `entity_type` first if you care about directional email/call activity.
- **opp_change_* rows are not contact-level activities**: Opportunity field changes are linked to a contact via the opportunity, but `apollo_contact_id` may be null for these rows. They represent deal-level events attributed to the rep, not contact touchpoints.

## Slack Context

- <!-- TODO: search #ask-henry or #dept-analytics for mentions of this table -->

## Business Terms

| Term | Definition |
|---|---|
| New Business Meeting | A meeting where the contact has had no scheduled meeting in the past 180 days (or ever). Captured by `is_new_business_meeting = TRUE`. |
| Outbound Activity | Activity initiated by the rep (`is_outbound = TRUE`). Emails sent, calls made, meetings scheduled by the rep. |
| Inbound Activity | Activity initiated by the contact (`is_outbound = FALSE`). Email replies, inbound calls, etc. |
| Sequence Step Position | The position of the email/call within an outbound sequence (also called emailer step position). |
| User Allocation | Salesforce record that maps a rep to their position, manager, and L2 manager for a given time period. Determines point-in-time org hierarchy. |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-20 | Created context file from Snowflake metadata + query history | Will Masket |
| 2026-03-19 | Model built/updated by Kaitlyn Maglietto (PR #2301 — Outbound new business meetings) | Kaitlyn Maglietto |
