# FCT Table Architecture — DE-Owned Building Blocks for Team Analytics

> **Purpose:** Replace the monolithic `DIM_TEAMS_DAILY` (207 columns, DS-owned, dbt-dependent) with focused, domain-specific fact tables owned by DE. AEs compose what they need by joining building blocks.

> **Author:** Brighid Meredith (DE)
> **Date:** 2026-03-09
> **Status:** Requirements complete, ready for build

---

## Why

`DIM_TEAMS_DAILY` is the most-used analytics table at Apollo (40K+ queries, 49 users in 90 days). But it has serious problems:

1. **Misnomer.** It's a fact table at `(team_id, date)` grain with 160+ activity columns — not a dimension.
2. **Kitchen sink.** Bakes in revenue (ARR), credit usage, dimension attributes (segment, core flag), AND feature activity. Changes to any domain require backfilling the entire 8.5B-row table.
3. **DS-owned, dbt-dependent.** Refresh has been fragile (stuck at Jan 11 in one incident). Schema changes require full incremental backfill.
4. **Trust concerns.** Lives in `ANALYTICS_DATASCIENCE` — not DE-maintained.
5. **Dead weight.** 15 columns used by ≤2 people. 18 columns were already dropped (ordinal gaps).

**The fix:** Decompose into focused building blocks, each with a clear domain, raw source lineage, and Airflow ownership.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                        LOOKUP TABLES                              │
│                   (slowly changing, team-level)                    │
│                                                                   │
│  LU_TEAM_ATTRIBUTES ─── team_id → segment, region, core,         │
│  (BUILD)                 golden_pop, plan, status, setup flags    │
│                                                                   │
│  LU_FISCAL_CALENDAR ─── date → fiscal_year, fiscal_quarter,      │
│  (BUILD)                 fiscal_year_quarter, is_business_day     │
│                                                                   │
│  LU_ENUM ──────────────  amplitude event_type_id → feature_name,  │
│  (EXTEND)                credit_type → name, source → name       │
│                                                                   │
│  LU_FEATURE_USE_CASE ── feature_name → use_case                  │
│  (BUILD)                 (enrichment, genpipe_trad, etc.)         │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                    DOMAIN FACT TABLES                              │
│           grain: (team_id, ds) — one per product domain           │
│                                                                   │
│  FCT_TEAM_EMAIL_DAILY ──── sent/reply counts by channel           │
│  FCT_TEAM_ENRICHMENT_DAILY ── api/csv/waterfall/crm_living_data   │
│  FCT_TEAM_GENPIPE_DAILY ──── 13 features + trad/nextgen meetings  │
│  FCT_TEAM_WINCLOSE_DAILY ── deals/meeting_assistant/scheduler     │
│  FCT_TEAM_ACTIVITY_DAILY ── active_users, extension, meetings,    │
│                              sequences, AI_platform, LinkedIn     │
│  FCT_TEAM_SUPPORT_DAILY ── tickets, conversations, AI handling    │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                    EXISTING TABLES (no changes)                    │
│                                                                   │
│  FCT_DAILY_REVENUE ──── ARR, churn, edition (ANALYTICS)           │
│  FCT_TEAM_CREDITS_DAILY ── credit usage/limits (rename from       │
│                             GOLD_TEAM_CREDITS)                    │
│  DIM_MONGO_TEAMS ──── raw team metadata (ANALYTICS_DATAPLATFORM)  │
└──────────────────────────────────────────────────────────────────┘

                    ┌────────────────────────┐
                    │   AE COMPOSITION LAYER  │
                    │   (AE-owned, not DE)    │
                    │                        │
                    │   JOIN what you need:   │
                    │   FCT_* + LU_* tables   │
                    │   → Looker views        │
                    │   → ad hoc analysis     │
                    │   → FCT_TEAMS_DAILY     │
                    │     (optional, VARIANT)  │
                    └────────────────────────┘
```

---

## Naming Conventions

| Prefix | Meaning | Examples |
|---|---|---|
| `FCT_` | Fact table — measures at a specific grain, changes daily | `FCT_TEAM_EMAIL_DAILY`, `FCT_DAILY_REVENUE` |
| `LU_` | Lookup table — reference data, slowly changing or static | `LU_TEAM_ATTRIBUTES`, `LU_FISCAL_CALENDAR`, `LU_ENUM` |
| `AGG_` | Aggregation — intermediate rollup at a specific grain | `AGG_TEAM_CREDITS` |

**Renames from current state:**

| Current | Rename To | Why |
|---|---|---|
| `GOLD_TEAM_CREDITS` | `FCT_TEAM_CREDITS_DAILY` | It's a daily fact table, not a "gold" tier |
| `DIM_TEAM_ATTRIBUTES` (proposed) | `LU_TEAM_ATTRIBUTES` | Lookup, not a dimension |
| `DIM_FISCAL_CALENDAR` (proposed) | `LU_FISCAL_CALENDAR` | Lookup, not a dimension |

---

## What Each Table Contains

### LU_TEAM_ATTRIBUTES

**Grain:** One row per `team_id` (current state, not historical)
**Refresh:** Daily
**Source:** Raw only — no dbt dependency

| Column | Source Table | Source Column |
|---|---|---|
| `team_id` | `ANALYTICS_DATAPLATFORM.DIM_MONGO_TEAMS` | `TEAM_ID` |
| `sfdc_account_id` | `RAW_FIVETRAN_DB.SALESFORCE.APOLLO_TEAM_C` | `ACCOUNT_C` (via `TEAM_ID_C` bridge) |
| `account_segment` | `RAW_FIVETRAN_DB.SALESFORCE.ACCOUNT` | `ACCOUNT_SEGMENT_C` |
| `account_region` | same | `ACCOUNT_REGION_C` |
| `is_core_account` | same | `ZP_ACCOUNT_IS_CORE_C` |
| `is_golden_population` | Derived | segment IN (SMB,MM,Ent) AND region IN (AMER,EMEA) |
| `is_free_email_domain` | `DIM_MONGO_TEAMS` | `WEB_DOMAIN` check against free email list |
| `pricing_variant` | `DIM_MONGO_TEAMS` | `PRICING_VARIANT` |
| `team_status` | `DIM_MONGO_TEAMS` | `STATUS_CD` |
| `team_created_at` | `DIM_MONGO_TEAMS` | `CREATED_AT_UTC` |
| `has_mfa` | `ANALYTICS_DATAPLATFORM.DIM_MONGO_MFA_CONFIGS` | EXISTS check |
| `number_of_employees` | `RAW_FIVETRAN_DB.SALESFORCE.ACCOUNT` | `NUMBER_OF_EMPLOYEES` |
| `billing_country` | same | `BILLING_COUNTRY` |
| `has_suspicious_team` | same | `SUSPICIOUS_ACCOUNT_C` |
| `calendar_linked_users` | Amplitude/Mongo (setup event) | |
| `sso_enabled_users` | Amplitude/Mongo (setup event) | |
| `conversation_intel_setup_users` | Amplitude/Mongo (setup event) | |

**Join path (all raw):**
```sql
DIM_MONGO_TEAMS t
LEFT JOIN RAW_FIVETRAN_DB.SALESFORCE.APOLLO_TEAM_C bridge
    ON t.TEAM_ID = bridge.TEAM_ID_C AND NOT bridge.IS_DELETED
LEFT JOIN RAW_FIVETRAN_DB.SALESFORCE.ACCOUNT acct
    ON bridge.ACCOUNT_C = acct.ID AND NOT acct.IS_DELETED
LEFT JOIN DIM_MONGO_MFA_CONFIGS mfa
    ON t.TEAM_ID = mfa.TEAM_ID
```

### LU_FISCAL_CALENDAR

**Grain:** One row per `calendar_date`
**Refresh:** Static (generate once, extend annually)

| Column | Type | Description |
|---|---|---|
| `calendar_date` | DATE | |
| `fiscal_year` | NUMBER | FY starts February (e.g., March 2026 = FY2027) |
| `fiscal_quarter` | NUMBER | 1-4, starting from February |
| `fiscal_year_quarter` | TEXT | e.g., 'FY2027-1' |
| `calendar_month` | DATE | First of month |
| `calendar_week` | DATE | Monday of week |
| `is_business_day` | BOOLEAN | Mon-Fri |

### FCT_TEAM_EMAIL_DAILY

**Grain:** `(team_id, ds)`
**Source:** `RAW_MONGO_DB.RAW_COLLECTIONS.emailer_messages`

| Column | Description | Filter Logic |
|---|---|---|
| `sent_outreach_automatic_user_count_l1/l7/l28` | Users who sent auto outreach emails | type='outreach_automatic_email', status IN ('Completed','Failed') |
| `sent_outreach_manual_user_count_l1/l7/l28` | Users who sent manual emails | type='outreach_manual_email' |
| `sent_extension_user_count_l1/l7/l28` | Users who sent via extension | type='extension_email' |
| `reply_received_*_user_count_l1/l7/l28` | Users who received replies | Same filters + replied=1 |
| `interest_received_*_user_count_l1/l7/l28` | Users who received interest signals | Interest classification logic |

### FCT_TEAM_ENRICHMENT_DAILY

**Grain:** `(team_id, ds)`
**Sources:** Amplitude events + Mongo waterfall requests

| Column | Source | Notes |
|---|---|---|
| `api_user_count_l1/l7/l28` | Amplitude | Event type IDs via LU_ENUM |
| `csv_user_count_l1/l7/l28` | Amplitude | |
| `crm_living_data_user_count_l1/l7/l28` | Amplitude | |
| `waterfall_user_count_l1/l7/l28` | Mongo (`typed_custom_field_auto_generate_workflow_requests`) | Filter: waterfall_template NOT NULL, root_request, third_party=true |
| `*_interest_user_count_l1/l7/l28` | Amplitude | "Looked but didn't use" signal |

### FCT_TEAM_GENPIPE_DAILY

**Grain:** `(team_id, ds)`
**Sources:** Amplitude events + Mongo emailer_messages + rule_actions

| Column Group | Source | Notes |
|---|---|---|
| `traditional_user_count_l1/l7/l28` | Mongo emailer_messages | Meetings booked via sequences, NOT via Plays |
| `nextgen_diy_user_count_l1/l7/l28` | Mongo emailer_messages + rule_actions | Meetings booked via Plays (INNER JOIN rule_actions) |
| `feature_{dialer,email,sequence,workflow,record_actioned,list_building,actions_platform,power_up,ai_sequence,ai_messaging,scores,signals,ai_filters}_user_count_l1/l7/l28` | Amplitude | 13 features, each with L1/L7/L28 = 39 columns |
| `features_total_user_count_l1/l7/l28` | Derived | SUM of above features |
| `*_interest_user_count_l1/l7/l28` | Amplitude | Interest signals for traditional + nextgen |

### FCT_TEAM_WINCLOSE_DAILY

**Grain:** `(team_id, ds)`
**Sources:** Amplitude + Mongo emailer_messages + Customer.io

| Column | Source | Notes |
|---|---|---|
| `deals_user_count_l1/l7/l28` | Amplitude | Deal interactions |
| `meeting_assistant_user_count_l1/l7/l28` | Amplitude + Mongo (conversation_followup) + Customer.io (msg ID 103) | **3-source merge** |
| `scheduler_user_count_l1/l7/l28` | Amplitude | |
| `notes_user_count_l1/l7/l28` | Amplitude | |
| `*_interest_user_count_l1/l7/l28` | Amplitude | |

### FCT_TEAM_ACTIVITY_DAILY

**Grain:** `(team_id, ds)`
**Source:** Amplitude events

| Column | Description |
|---|---|
| `active_user_count_l1/l7/l28` | Any qualifying activity |
| `count_of_users` | Total users on team |
| `paid_seat_limit` | Seat limit |
| `extension_user_count_l1/l7/l28` | Chrome extension usage |
| `meeting_booked_user_count_l1/l7/l28` | Meetings booked |
| `meeting_recorded_user_count_l1/l7/l28` | Meetings recorded |
| `sequence_created_user_count_l1/l7/l28` | Sequences created |
| `ai_platform_user_count_l1/l7/l28` | AI platform usage |
| `linkedin_user_count_l1/l7/l28` | LinkedIn prospecting |
| `home_user_count_l1/l7/l28` | Home page visits |
| `analytics_user_count_l1/l7/l28` | Analytics page visits |
| `has_any_event_user_count_l1/l7/l28` | Any Amplitude/Mongo event |
| `use_case_enrichment_active_l1/l7/l28` | Enrichment use case active users |
| `use_case_genpipe_trad_active_l1/l7/l28` | GenPipe traditional active |
| `use_case_genpipe_nextgen_active_l1/l7/l28` | GenPipe nextgen active |
| `use_case_winclose_active_l1/l7/l28` | Win/Close active |

### FCT_TEAM_SUPPORT_DAILY

**Grain:** `(team_id, ds)`
**Source:** `RAW_FIVETRAN_DB.INTERCOM.*`

| Column | Description |
|---|---|
| `conversations_count_l1/l7` | Non-escalated conversations |
| `tickets_count_l1/l7` | Escalated tickets |
| `interactions_count_l1/l7` | Combined |
| `human_only_chat_count_l1/l7` | Human-only handled chats |
| `human_only_ticket_count_l1/l7` | Human-only handled tickets |
| `ai_participated_count_l1/l7` | AI + human handled |
| `support_team_handled_count_l1/l7` | Any support team handled |
| `ai_only_count_l1/l7` | AI-only handled |

Note: Support only has L1/L7 (no L28) — matches current DIM_TEAMS_DAILY.

---

## How AEs Use This

### Example: "NRR by segment this quarter"
```sql
SELECT
    lu.account_segment,
    fc.fiscal_year_quarter,
    SUM(r.ARR) / SUM(r.PREVIOUS_DATE_PERIOD_ARR) AS nrr
FROM FCT_DAILY_REVENUE r
JOIN LU_TEAM_ATTRIBUTES lu ON r.APOLLO_TEAM_ID = lu.team_id
JOIN LU_FISCAL_CALENDAR fc ON r.DATE_PERIOD = fc.calendar_date
WHERE fc.fiscal_year_quarter = 'FY2027-1'
  AND r.PREVIOUS_DATE_PERIOD_IS_ACTIVE = TRUE
  AND lu.is_core_account = TRUE
GROUP BY 1, 2
```

### Example: "Paid WAT by segment"
```sql
SELECT
    lu.account_segment,
    a.ds,
    COUNT(DISTINCT a.team_id) AS paid_wat
FROM FCT_TEAM_ACTIVITY_DAILY a
JOIN LU_TEAM_ATTRIBUTES lu ON a.team_id = lu.team_id
JOIN FCT_DAILY_REVENUE r ON a.team_id = r.APOLLO_TEAM_ID AND a.ds = r.DATE_PERIOD
WHERE a.active_user_count_l7 > 0
  AND r.ARR > 0
  AND lu.is_core_account = TRUE
GROUP BY 1, 2
```

### Example: "Multi-product teams"
```sql
SELECT
    lu.account_segment,
    a.ds,
    a.team_id,
    (CASE WHEN e.api_user_count_l7 > 0 OR e.csv_user_count_l7 > 0 THEN 1 ELSE 0 END)
    + (CASE WHEN em.sent_outreach_automatic_user_count_l7 > 0 THEN 1 ELSE 0 END)
    + (CASE WHEN g.features_total_user_count_l7 > 0 THEN 1 ELSE 0 END)
    + (CASE WHEN w.deals_user_count_l7 > 0 THEN 1 ELSE 0 END)
    AS use_case_count
FROM FCT_TEAM_ACTIVITY_DAILY a
JOIN LU_TEAM_ATTRIBUTES lu ON a.team_id = lu.team_id
LEFT JOIN FCT_TEAM_ENRICHMENT_DAILY e ON a.team_id = e.team_id AND a.ds = e.ds
LEFT JOIN FCT_TEAM_EMAIL_DAILY em ON a.team_id = em.team_id AND a.ds = em.ds
LEFT JOIN FCT_TEAM_GENPIPE_DAILY g ON a.team_id = g.team_id AND a.ds = g.ds
LEFT JOIN FCT_TEAM_WINCLOSE_DAILY w ON a.team_id = w.team_id AND a.ds = w.ds
WHERE lu.is_core_account = TRUE
```

### Optional: FCT_TEAMS_DAILY (VARIANT compact version)

If AEs want a single-table experience, they can build a view or table:

```sql
SELECT
    a.team_id, a.ds,
    a.active_user_count_l1, a.active_user_count_l7, a.active_user_count_l28,
    a.count_of_users, a.paid_seat_limit,
    OBJECT_CONSTRUCT(
        'api_l7', e.api_user_count_l7,
        'csv_l7', e.csv_user_count_l7,
        'waterfall_l7', e.waterfall_user_count_l7,
        'crm_living_data_l7', e.crm_living_data_user_count_l7
    ) AS enrichment,
    OBJECT_CONSTRUCT(
        'sent_auto_l7', em.sent_outreach_automatic_user_count_l7,
        'sent_manual_l7', em.sent_outreach_manual_user_count_l7,
        'sent_ext_l7', em.sent_extension_user_count_l7
    ) AS email,
    OBJECT_CONSTRUCT(
        'traditional_l7', g.traditional_user_count_l7,
        'nextgen_diy_l7', g.nextgen_diy_user_count_l7,
        'features_total_l7', g.features_total_user_count_l7
    ) AS genpipe,
    OBJECT_CONSTRUCT(
        'deals_l7', w.deals_user_count_l7,
        'meeting_assistant_l7', w.meeting_assistant_user_count_l7
    ) AS winclose
FROM FCT_TEAM_ACTIVITY_DAILY a
LEFT JOIN FCT_TEAM_ENRICHMENT_DAILY e USING (team_id, ds)
LEFT JOIN FCT_TEAM_EMAIL_DAILY em USING (team_id, ds)
LEFT JOIN FCT_TEAM_GENPIPE_DAILY g USING (team_id, ds)
LEFT JOIN FCT_TEAM_WINCLOSE_DAILY w USING (team_id, ds)
```

---

## Build Priority & Dependencies

```
P0 (unblocks everything):
  LU_TEAM_ATTRIBUTES ──── no deps
  LU_FISCAL_CALENDAR ──── no deps
  LU_ENUM (amplitude) ─── no deps (extract from dbt fct_amplitude_events.sql)

P0.5 (SFDC table migrations — high query volume, straightforward):
  LU_SFDC_ACCOUNTS ────── replaces DIM_SALESFORCE_ACCOUNTS (424K queries, 46 users)
  LU_SFDC_APOLLO_TEAMS ── replaces DIM_SALESFORCE_APOLLO_TEAMS (314K queries, 57 users)
  LU_SFDC_USERS ────────── replaces DIM_SALESFORCE_USERS (trivial, 828 rows)

P1 (core domain FCTs):
  FCT_TEAM_EMAIL_DAILY ──────── depends on: emailer_messages (Mongo)
  FCT_TEAM_ENRICHMENT_DAILY ── depends on: Amplitude + LU_ENUM + waterfall (Mongo)
  FCT_TEAM_ACTIVITY_DAILY ──── depends on: Amplitude + LU_ENUM

P1.5 (user-level lookups):
  LU_USER_ATTRIBUTES ────────── replaces DIM_USERS (40K queries, 27 users)
  LU_USER_ACTIVATION_MILESTONES  replaces DIM_USER_ACTIVATION (14K queries)
  LU_TEAM_ACTIVATION_MILESTONES  replaces DIM_TEAM_ACTIVATION (10K queries)

P2 (complex domain FCTs):
  FCT_TEAM_GENPIPE_DAILY ────── depends on: Amplitude + LU_ENUM + emailer_messages + rule_actions
  FCT_TEAM_WINCLOSE_DAILY ──── depends on: Amplitude + emailer_messages + Customer.io
  FCT_USER_ACTIVITY_DAILY ──── user-level version of team activity

P3 (most complex):
  FCT_TEAM_SUPPORT_DAILY ────── depends on: Intercom (Fivetran) — complex chain
  LU_FEATURE_USE_CASE ────────  manual mapping

NOT migrating (keep dbt-owned):
  DIM_SALESFORCE_OPPORTUNITIES ── complex pipeline stage logic, 21 users
  DIM_SALESFORCE_CONTACTS ─────── niche, complex matching, 9 users
  DIM_ACTIVE_TEAMS_DAILY ──────── DS reference (AEs use FCT_TEAM_ACTIVITY_DAILY instead)
  DIM_SALESFORCE_CAMPAIGNS ────── niche, 4 users
```

---

## SFDC Table Migrations (P0.5)

These three tables replace dbt-built SFDC DIM tables with DE-owned, raw-sourced lookups. They're prioritized P0.5 because SFDC tables are the **most queried** tables in the analytics estate (424K + 314K queries in 90 days).

### LU_SFDC_ACCOUNTS

**Replaces:** `DIM_SALESFORCE_ACCOUNTS` (424K queries, 46 users)
**Grain:** One row per SFDC Account ID
**Source:** `RAW_FIVETRAN_DB.SALESFORCE.ACCOUNT` + `SALESFORCE.USER` (owner name resolution)

| Column | Source | Notes |
|---|---|---|
| `account_id` | `ACCOUNT.ID` | PK |
| `account_name` | `ACCOUNT.NAME` | |
| `account_segment` | `ACCOUNT.ACCOUNT_SEGMENT_C` | VSB/SMB/MM/Ent |
| `account_region` | `ACCOUNT.ACCOUNT_REGION_C` | AMER/EMEA/APAC |
| `is_core` | `ACCOUNT.ZP_ACCOUNT_IS_CORE_C` | Raw SFDC field (97.7% match with dbt logic) |
| `industry` | `ACCOUNT.INDUSTRY` | |
| `number_of_employees` | `ACCOUNT.NUMBER_OF_EMPLOYEES` | |
| `billing_country` | `ACCOUNT.BILLING_COUNTRY` | |
| `owner_id` | `ACCOUNT.OWNER_ID` | FK to USER |
| `owner_name` | `USER.NAME` (via OWNER_ID) | Replaces dbt's GTME_NAME |
| `am_name` | `USER.NAME` (via AM owner field) | Account Manager |
| `csm_name` | `USER.NAME` (via CSM owner field) | CSM |
| `arr` | `ACCOUNT.ARR_C` | SFDC-synced ARR |
| `created_date` | `ACCOUNT.CREATED_DATE` | |
| `suspicious_account` | `ACCOUNT.SUSPICIOUS_ACCOUNT_C` | |

**Key complexity:** Owner name columns require 3 separate JOINs to `SALESFORCE.USER` for GTME, AM, and CSM roles.

### LU_SFDC_APOLLO_TEAMS

**Replaces:** `DIM_SALESFORCE_APOLLO_TEAMS` (314K queries, 57 users)
**Grain:** One row per APOLLO_TEAM_C record (team_id ↔ SFDC account bridge)
**Source:** `RAW_FIVETRAN_DB.SALESFORCE.APOLLO_TEAM_C`

Nearly 1:1 with raw source — minimal transformation needed.

| Column | Source |
|---|---|
| `id` | `APOLLO_TEAM_C.ID` |
| `team_id` | `APOLLO_TEAM_C.TEAM_ID_C` |
| `account_id` | `APOLLO_TEAM_C.ACCOUNT_C` |
| `is_deleted` | `APOLLO_TEAM_C.IS_DELETED` |
| `created_date` | `APOLLO_TEAM_C.CREATED_DATE` |

### LU_SFDC_USERS

**Replaces:** `DIM_SALESFORCE_USERS` (trivial, 828 rows)
**Grain:** One row per SFDC User ID
**Source:** `RAW_FIVETRAN_DB.SALESFORCE.USER`

| Column | Source |
|---|---|
| `user_id` | `USER.ID` |
| `name` | `USER.NAME` |
| `email` | `USER.EMAIL` |
| `role` | `USER.USER_ROLE_ID` → resolve via `SALESFORCE.USER_ROLE` |
| `is_active` | `USER.IS_ACTIVE` |

---

## User-Level Lookups (P1.5)

### LU_USER_ATTRIBUTES

**Replaces:** `DIM_USERS` (40K queries, 27 users)
**Grain:** One row per `user_id`
**Source:** `ANALYTICS_DATAPLATFORM.DIM_MONGO_USERS` + SFDC bridge

Top queried columns: USER_ID, TEAM_ID, EMAIL, IS_ACTIVE, CREATED_AT, ROLE, LOGIN_COUNT

### LU_USER_ACTIVATION_MILESTONES

**Replaces:** `DIM_USER_ACTIVATION` (14K queries)
**Grain:** One row per `user_id`
**Source:** `DIM_MONGO_USERS` + Amplitude activation events

Tracks: first login, first email sent, first enrichment, first sequence, etc.

### LU_TEAM_ACTIVATION_MILESTONES

**Replaces:** `DIM_TEAM_ACTIVATION` (10K queries)
**Grain:** One row per `team_id`
**Source:** `DIM_MONGO_TEAMS` + Amplitude activation events

Tracks: first paid date, first active user, first email campaign, etc.

---

## Raw Source Inventory

| Source | Type | Tables Used By |
|---|---|---|
| `RAW_FIVETRAN_DB.AMPLITUDE.event` | Fivetran sync | Enrichment (api/csv/crm), GenPipe (13 features), WinClose (deals/scheduler/notes), Activity (all) |
| `RAW_MONGO_DB.RAW_COLLECTIONS.emailer_messages` | Mongo export | Email (all), GenPipe (trad/nextgen meetings) |
| `RAW_MONGO_DB.RAW_COLLECTIONS.typed_custom_field_auto_generate_workflow_requests` | Mongo export | Enrichment (waterfall) |
| `RAW_MONGO_DB.RAW_COLLECTIONS.rule_actions` | Mongo export | GenPipe (Plays filter for nextgen) |
| `RAW_FIVETRAN_DB.INTERCOM.*` | Fivetran sync | Support (all) |
| `RAW_FIVETRAN_DB.CUSTOMER_IO.delivery_metrics` | Fivetran sync | WinClose (meeting_assistant call summaries) |
| `RAW_FIVETRAN_DB.SALESFORCE.ACCOUNT` | Fivetran sync | LU_TEAM_ATTRIBUTES |
| `RAW_FIVETRAN_DB.SALESFORCE.APOLLO_TEAM_C` | Fivetran sync | LU_TEAM_ATTRIBUTES (bridge) |
| `ANALYTICS_DATAPLATFORM.DIM_MONGO_TEAMS` | DE mirror | LU_TEAM_ATTRIBUTES |
| `ANALYTICS_DATAPLATFORM.DIM_MONGO_MFA_CONFIGS` | DE mirror | LU_TEAM_ATTRIBUTES (enterprise signal) |

---

## What This Replaces

| Current (DS-owned) | Replaced By (DE-owned) |
|---|---|
| `DIM_TEAMS_DAILY` dimension attributes (IS_PAID, IS_CORE, ARR) | `LU_TEAM_ATTRIBUTES` + `FCT_DAILY_REVENUE` |
| `DIM_TEAMS_DAILY` enrichment columns | `FCT_TEAM_ENRICHMENT_DAILY` |
| `DIM_TEAMS_DAILY` email columns | `FCT_TEAM_EMAIL_DAILY` |
| `DIM_TEAMS_DAILY` genpipe columns | `FCT_TEAM_GENPIPE_DAILY` |
| `DIM_TEAMS_DAILY` winclose columns | `FCT_TEAM_WINCLOSE_DAILY` |
| `DIM_TEAMS_DAILY` activity columns | `FCT_TEAM_ACTIVITY_DAILY` |
| `DIM_TEAMS_DAILY` support columns | `FCT_TEAM_SUPPORT_DAILY` |
| `DIM_TEAMS_DAILY` credit columns | `FCT_TEAM_CREDITS_DAILY` (rename GOLD_TEAM_CREDITS) |
| `DIM_ACTIVE_TEAMS_DAILY` | Not needed — AEs filter `FCT_TEAM_ACTIVITY_DAILY WHERE active_user_count_l1 > 0` |
| `DIM_SALESFORCE_ACCOUNTS` | `LU_SFDC_ACCOUNTS` |
| `DIM_SALESFORCE_APOLLO_TEAMS` | `LU_SFDC_APOLLO_TEAMS` |
| `DIM_SALESFORCE_USERS` | `LU_SFDC_USERS` |
| `DIM_USERS` | `LU_USER_ATTRIBUTES` |
| `DIM_USER_ACTIVATION` | `LU_USER_ACTIVATION_MILESTONES` |
| `DIM_TEAM_ACTIVATION` | `LU_TEAM_ACTIVATION_MILESTONES` |

**None of the existing tables are being deleted.** They continue to exist (DS/dbt-owned). These tables provide DE-owned, trusted alternatives built from raw sources.

**Not migrating:** DIM_SALESFORCE_OPPORTUNITIES (complex pipeline stage logic), DIM_SALESFORCE_CONTACTS (niche, complex matching), DIM_SALESFORCE_CAMPAIGNS (4 users).

---

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-09 | Created from column usage analysis (ACCESS_HISTORY 90d) + dbt upstream tracing | Brighid (via Claude) |
| 2026-03-09 | Added SFDC table migrations (P0.5), user-level lookups (P1.5), full DIM migration map | Brighid (via Claude) |
