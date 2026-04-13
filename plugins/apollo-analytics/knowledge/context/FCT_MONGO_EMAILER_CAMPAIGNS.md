# FCT_MONGO_EMAILER_CAMPAIGNS

> Email sequence (campaign) fact table. One row per sequence.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_EMAILER_CAMPAIGNS` |
| **Grain** | One row per emailer campaign (sequence) |
| **Row count** | <!-- TODO: verify --> |
| **Refresh cadence** | Daily (dbt model, ANALYTICS_DATAPLATFORM) |
| **Trust level** | Authoritative (ANALYTICS_DATAPLATFORM) |
| **Owner** | Data Platform |

## Description

Tracks email sequences (campaigns) created in Apollo. Used for sequence-level analytics including creation volume, type, and activation status. Key for AI Assistant outcome analysis — `creation_type_cd = 'ai_assistant'` identifies sequences created through the AI Assistant.

## Upstream Sources

| Source | Relationship |
|---|---|
| MongoDB `emailer_campaigns` collection | Primary source (CDC ingestion) |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| EMAILER_CAMPAIGN_ID | TEXT (PK) | Unique sequence identifier | Join key to FCT_MONGO_EMAILER_MESSAGES |
| USER_ID | TEXT | User who created the sequence | FK to DIM_USERS |
| CREATED_AT_UTC | TIMESTAMP | When the sequence was created | Use for date filtering |
| CREATION_TYPE_CD | TEXT | How the sequence was created | `'ai_assistant'` = created via AI Assistant |
| NUM_CONTACTS | INT | Number of contacts in the sequence | Use `>= 10` threshold for "meaningful" sequences |

## How It's Used

### AI Assistant — sequences created and activated (F7D)

Sequences created via AI Assistant (`creation_type_cd = 'ai_assistant'`) that were activated (at least one email sent) within 7 days of the user's first AI Assistant activation. Paired with `FCT_MONGO_EMAILER_MESSAGES` to confirm activation.

```sql
-- AI-created sequences with ≥10 contacts
seq as (
    select      cam.user_id as apollo_user_id
                , cam.emailer_campaign_id as sequence_id
                , cam.created_at_utc as sequence_created_datetime
                , cam.num_contacts
    from        analytics_db.analytics_dataplatform.fct_mongo_emailer_campaigns cam
    where       cam.creation_type_cd = 'ai_assistant'
    and         cam.created_at_utc > '2025-01-01'
    and         cam.created_at_utc < current_date()
    group by    all
),
-- activated = at least one email sent through the sequence
seq_act as (
    select      seq.*, min(eml.completed_at) as first_email_sent_datetime
    from        seq
    left join   analytics_db.analytics_dataplatform.fct_mongo_emailer_messages eml
                    on  eml.emailer_campaign_id = seq.sequence_id
                    and eml.status = 'Completed'
    group by    all
)
```

**F7D join condition** (join to `assistant_activated` CTE):
```sql
left join seq_act on  seq_act.apollo_user_id = aa.apollo_user_id
                  and date(seq_act.sequence_created_datetime) >= aa.first_active_date
                  and date(seq_act.sequence_created_datetime) <= aa.first_active_date + 7
                  and date(seq_act.first_email_sent_datetime) <= aa.first_active_date + 7
                  and seq_act.num_contacts >= 10
```

### Key consumers
- AI product debrief — F7D high-value action rate
- AI Assistant outcome analysis (`ai_assistant_engagement_queries.sql`, query 13)

## Known Issues & Gotchas

- `NUM_CONTACTS` can be 0 or low for sequences that were created but never populated — use `>= 10` threshold for meaningful sequences in outcome analysis.
- `CREATION_TYPE_CD = 'ai_assistant'` is the canonical flag for AI-created sequences; verify this value hasn't changed if sequence counts look wrong.

## Related Tables

| Table | Relationship |
|---|---|
| `FCT_MONGO_EMAILER_MESSAGES` | Child — one row per email send; join on `emailer_campaign_id`; `status = 'Completed'` for sent emails |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-26 | Created context file — confirmed columns from AI Assistant F7D outcome query | Pubudu (via Jarvis) |
