# LU_TEAM_ATTRIBUTES

> Team-level attribute lookup: segment, region, SFDC fields, MFA status, subscription lifecycle. Current state, not historical.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.PLAYGROUND.LU_TEAM_ATTRIBUTES` |
| **Grain** | team_id |
| **Grain columns** | team_id |
| **Row count** | ~3.4M |
| **Refresh cadence** | daily |
| **Coverage period** | ongoing |
| **Trust level** | Canonical |
| **Owner** | Analytics (Bridie Meredith) |

## Description

Current-state team attribute lookup joining DIM_MONGO_TEAMS, the RT view, SFDC bridge, SFDC ACCOUNT, MFA_CONFIGS (bridged via users), and FREE_EMAIL_PROVIDER_DOMAINS. Replaces dimension attributes previously embedded in DIM_TEAMS_DAILY and DIM_TEAMS. One row per team — not historical. Use for enriching fact tables with segment, region, industry, CSM, and subscription lifecycle at query time.

## Upstream Sources

| Source | Relationship |
|---|---|
| DIM_MONGO_TEAMS | Core team identity, pricing_variant, web_domain, UTM fields |
| DIM_MONGO_TEAMS_RT_VW | team_name, subscription_expiry_date, cancellation_subscription_date (not on materialized DIM) |
| RAW_FIVETRAN_DB.SALESFORCE.APOLLO_TEAM_C | Bridge: team_id → sfdc_account_id |
| RAW_FIVETRAN_DB.SALESFORCE.ACCOUNT | Account segment, region, industry, CSM, health scores |
| DIM_MONGO_MFA_CONFIGS + DIM_MONGO_USERS | MFA status (MFA_CONFIGS.TEAM_ID is NULL — bridged via USER_ID) |
| FREE_EMAIL_PROVIDER_DOMAINS | Free email domain flag |
| DIM_MONGO_USERS | User count aggregates |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| team_id | VARCHAR | Apollo team identifier (PK) | |
| team_name | VARCHAR | Team display name | From RT view, not materialized DIM |
| team_created_at | TIMESTAMP_NTZ | Team creation timestamp | |
| pricing_variant | VARCHAR | Pricing/plan variant | Critical for credit migration analysis |
| web_domain_hash | VARCHAR | Team web domain | DATACONSUMER_ROLE sees SHA256 hash; DEVELOPER_ROLE sees raw domain |
| sfdc_account_id | VARCHAR | Linked Salesforce account ID | NULL if team not bridged to SFDC |
| account_segment | VARCHAR | Account segment from SFDC | Values: `Enterprise`, `Mid-Market`, `SMB`, `VSB` |
| account_segment_override | VARCHAR | Manual segment reclassification | Triggers on closed-won ARR >= $50k; locked intra-year |
| account_region | VARCHAR | Account region from SFDC | e.g. `AMER`, `EMEA` |
| is_core_account | BOOLEAN | Core account flag from SFDC | Used for durable analysis filters |
| industry | VARCHAR | SFDC industry | |
| number_of_employees | NUMBER | Employee count from SFDC | |
| billing_country | VARCHAR | Billing country | |
| is_suspicious_account | BOOLEAN | Suspicious account flag | Exclude from exec-facing analysis |
| sfdc_parent_account_id | VARCHAR | Parent account ID | 658 teams have parent linkage |
| vitally_health_score | NUMBER | Vitally health score | |
| vitally_csm_id | VARCHAR | CSM from Vitally | More populated than sfdc_csm_id (19 distinct values vs near-empty) |
| subscription_expiry_date | DATE | Subscription expiry | From RT view only |
| cancellation_subscription_date | DATE | Cancellation date | From RT view only |
| free_email_domain | VARCHAR | Domain if it's a free email provider | NULL if not a free email domain |
| has_validated_mfa | BOOLEAN | Whether any team user has validated MFA | Bridged via USER_ID (MFA_CONFIGS.TEAM_ID is NULL) |
| user_count | NUMBER | Total user count for team | |
| utm_source | VARCHAR | UTM source at signup | |
| utm_medium | VARCHAR | UTM medium at signup | |
| utm_campaign | VARCHAR | UTM campaign at signup | |

## Known Issues

- `web_domain_hash`: DATACONSUMER_ROLE sees SHA256 hash, not raw domain — free email join uses raw domain (role-aware, requires DEVELOPER_ROLE for raw)
- `MFA_CONFIGS.TEAM_ID` is NULL for all rows — MFA status is bridged via `USER_ID → DIM_MONGO_USERS`; may miss teams with no user records
- `sfdc_csm_id` (CSM_C) is nearly empty (29 rows) — use `vitally_csm_id` (VITALLY_CSM_C) for CSM lookups
- Not historical — joining to a historical fact table will repeat current attributes for all past dates

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-14 | Created context file from catalog metadata | Pepper (auto) |
