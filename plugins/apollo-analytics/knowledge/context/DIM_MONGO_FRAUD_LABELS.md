# DIM_MONGO_FRAUD_LABELS

> One row per fraud label event on an Apollo team. The clean Snowflake view of MongoDB's `fraud_labels` collection.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_FRAUD_LABELS` |
| **Grain** | One row per fraud label record (`fraud_label_id`) |
| **Row count** | <!-- TODO: check --> |
| **Refresh cadence** | Daily (dbt, via Airflow `dbt_models_group_1`) |
| **Trust level** | Authoritative (ANALYTICS_DATAPLATFORM) |
| **Owner** | Data Platform / Trust & Safety |
| **DAG** | `dbt_models_group_1` |

## Description

The clean, typed version of MongoDB's `fraud_labels` collection. Each record represents a specific fraud or abuse classification on a team, written either by Apollo's automated detection systems or by an admin manually classifying a team. This table is the most granular view of fraud labels — one row per label per team, not aggregated.

For most analytics use cases, prefer the pre-aggregated `has_fraud_abuse_flag` on `dim_salesforce_apollo_teams` or the silver mart `apollo_team_fraud_abuse_flags`. Use this table directly when you need specific fraud types, timestamps, or per-label detail.

## Upstream Sources

| Source | Relationship |
|---|---|
| `RAW_MONGO_DB.RAW_COLLECTIONS.fraud_labels` | Direct source (via `stg_mongo__fraud_labels` → passthrough to this dim) |

## dbt Lineage

```
RAW_MONGO_DB.RAW_COLLECTIONS.fraud_labels   ← MongoDB production collection
  └─ stg_mongo__fraud_labels                ← Parse JSON, map type_cd → fraud_type
      └─ dim_mongo_fraud_labels              ← This table (clean passthrough)
          └─ apollo_team_fraud_abuse_flags   ← Aggregated per team (silver mart)
              └─ dim_salesforce_apollo_teams ← Final teams table (left joined)
```

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| `fraud_label_id` | VARCHAR | MongoDB ObjectId of the fraud label | PK |
| `team_id` | VARCHAR | Apollo team ID | FK to `dim_mongo_teams` |
| `type_cd` | NUMBER | Numeric fraud type code (0–16) | See taxonomy below |
| `fraud_type` | VARCHAR | Human-readable fraud type string | Derived from `type_cd` |
| `deleted` | BOOLEAN | Whether this label was soft-deleted | Filter `where deleted = false` for active labels |
| `admin_user_id` | VARCHAR | Admin who created the label (if manual) | NULL for automated labels |
| `created_at` | TIMESTAMP_NTZ | When the label was applied | Use for trend analysis |
| `updated_at` | TIMESTAMP_NTZ | Last update timestamp | |

## Fraud Type Taxonomy

| type_cd | fraud_type | Category | Included in `has_fraud_abuse_flag`? |
|---|---|---|---|
| 0 | `fraud_chargeback` | Financial fraud | ✅ Yes |
| 1 | `fraud_ach_return` | Financial fraud | ✅ Yes |
| 2 | `ato_suspected` | Account Takeover | ❌ No — ATO excluded |
| 3 | `ato_confirmed` | Account Takeover | ❌ No — ATO excluded |
| 4 | `ato_confirmed_with_unauthorized_charge` | Account Takeover | ❌ No — ATO excluded |
| 5 | `false_ato_claimed` | ATO-adjacent | ✅ Yes |
| 6 | `affiliate_abuse` | Abuse | ✅ Yes |
| 7 | `reseller_abuse` | Abuse | ✅ Yes |
| 8 | `promotion_abuse` | Abuse | ✅ Yes |
| 9 | `award_credit_abuse` | Abuse | ✅ Yes |
| 10 | `account_sharing_suspected` | Abuse | ✅ Yes |
| 11 | `trials_abuse` | Abuse | ✅ Yes |
| 12 | `brand_identity_spoofing` | Deceptive | ✅ Yes |
| 13 | `auto_data_scraping_detection` | Scraping | ✅ Yes |
| 14 | `human_confirmed_data_scraping` | Scraping | ✅ Yes |
| 15 | `auto_signup_high_risk` | Risk signal | ✅ Yes |
| 16 | `auto_high_risk_usage` | Risk signal | ✅ Yes |

**Why ATO is excluded:** ATO labels (types 2–4) indicate an account was *compromised* — the team is a victim, not an abuser. Excluding them from `has_fraud_abuse_flag` prevents falsely marking victim teams as bad actors.

## How It's Used

### Common query patterns

```sql
-- All active fraud labels for a team
select team_id, fraud_type, created_at
from analytics_db.analytics_dataplatform.dim_mongo_fraud_labels
where team_id = '<id>'
  and deleted = false

-- Count of teams by fraud type
select fraud_type, count(distinct team_id) as teams
from analytics_db.analytics_dataplatform.dim_mongo_fraud_labels
where deleted = false
group by 1
order by 2 desc

-- Teams with abuse labels (non-ATO) in the last 30 days
select distinct team_id, fraud_type, created_at
from analytics_db.analytics_dataplatform.dim_mongo_fraud_labels
where deleted = false
  and fraud_type not in ('ato_suspected', 'ato_confirmed', 'ato_confirmed_with_unauthorized_charge')
  and created_at >= dateadd('day', -30, current_date)
```

### Key consumers

- Trust & Safety / Fraud analytics
- `apollo_team_fraud_abuse_flags` (silver mart, aggregates this table)
- `dim_salesforce_apollo_teams` (final teams table, joins silver mart)

## How Fraud Labels Are Set (Product Context)

Labels are written by the LeadGenie app to MongoDB in real time. Main triggers:

| Trigger | Code location | fraud_type |
|---|---|---|
| Cross-team search reselling (≥6 unique searches from other teams in 24h) | `block_exportapollo_utils.rb` | `reseller_abuse` |
| IP/domain velocity (5+ signups from same source in 24h) | `self_serve_util.rb` | `auto_high_risk_usage` |
| Extreme request rate (10k+/hr) | `self_serve_util.rb` | `auto_high_risk_usage` |
| Darwinium device fraud signal | `darwinium_prospecting_block_middleware.rb` | `auto_signup_high_risk` |
| Manual admin action | Admin tooling | Any type |

When a label is written, the app also sets blocking flags on the Team record (`blocked_due_to_abuse`, `api_key_revoked`, `prospecting_blocked_until`) that enforce access restrictions at request time — **the app does not read from Snowflake to enforce blocks**. MongoDB is the live enforcement layer; Snowflake is the analytics mirror.

## Known Issues & Gotchas

- Always filter `where deleted = false` — soft-deleted labels remain in the table
- ATO types (2, 3, 4) are in this table but excluded from `has_fraud_abuse_flag` in downstream models — if you need them, query directly here
- For most team-level analysis, `dim_salesforce_apollo_teams.has_fraud_abuse_flag` is easier than joining this table
- Labels can exist for teams not in `dim_salesforce_apollo_teams` (e.g. teams without a Salesforce mapping) — use `dim_mongo_teams` for a broader join if needed

## Business Terms

| Term | Definition |
|---|---|
| Fraud label | A record tagging an Apollo team with a specific fraud or abuse classification |
| ATO (Account Takeover) | A fraud type where a team's account was compromised by an outside party; treated separately from intentional abuse |
| `has_fraud_abuse_flag` | Boolean: TRUE if a team has any active non-ATO fraud label |
| Hyper-restrictive | Product mode applied to teams with free email domains or unverifiable companies; reduces rate limits, denies trials, caps seats |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-17 | Created context file from dbt lineage + LeadGenie code analysis | Kirk (via Claude) |
