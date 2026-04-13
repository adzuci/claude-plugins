# Hex Notebooks — Context Extract

Extracted 2026-03-20 from 4 Hex notebooks via Threads Agent. Covers SQL table sources, metric definitions, section structure, and business rules.

---

## 1. Onboarding Activation and Retention

**Link:** https://app.hex.tech/apollo/app/019746da-bfd8-7008-8f5c-6e29cd956a31/latest
**Purpose:** Measures whether Apollo's onboarding programs (HVO meetings, in-app survey-driven activation) drive feature activation, retention, and revenue retention (GDR). Compares onboarded vs. non-onboarded teams and tracks use-case-specific activation rates based on survey goals.
**Last run (at extract time):** 2025-10-20 (stale; auto-refreshes after 10 hours, ~42 min runtime)

### Section Structure
- Onboarding: % Qualified Teams Going Through HVO, Activation post-HVO, Retention post-HVO, GDR comparison
- Activation: Do people activate what they claim they are here to do? (survey goal → use case)
- Retention: D28 use case retention for intended use case
- Experimentation: Do current activation strategies (different intent → different experience) work?
- Setup Moments

### SQL Queries & Table Sources

| Query | Key Tables | Purpose |
|-------|-----------|---------|
| HVO Meetings Overview | `dbt_development_db.dbt_kmaglietto.team_meetings_overview` | Weekly HVO meeting counts (held, booked, attended, no-show), attendance/no-show rates |
| `onboarded_gdr` (component import) | `dbt_development_db.dbt_kmaglietto.calendar_events`, `analytics_db.analytics.fct_revenue_stats_monthly`, `analytics_db.analytics.dim_salesforce_apollo_teams` | GDR for HVO-attended teams — groups by month of first payment, tracks downgrade/churn ARR vs. first month ARR |
| `non_onboarded_gdr_table` | Same as above + `analytics_db.analytics.dim_salesforce_accounts` | Same GDR calculation for non-HVO teams; optional `is_core_account` Jinja filter |
| `dataframe` (Use Case Activation - Overall) | `ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_USERS` (LATERAL FLATTEN on `in_app_onboarding_goals`), `ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS_DAILY` | Maps survey goals → 5 use cases; F28D activation rate + D28 retention rate. Warehouse: `ELT_WH_DP` |
| `survey_goals_paid_tier` | Same as above | Same as above but adds `is_paid_ind` + `ACCOUNT_SALES_DEPARTMENT_TIER` to GROUP BY; also computes `record_actioned_rate`, `conversion_to_paid_rate` |
| `survey_goals_paid_tier_filtered` | References `survey_goals_paid_tier` | Jinja filter pass-through: `WHERE paid_status = {{paid_status}} AND tier_status = {{tier_status}}` |
| `hvo_meetings_base` | `DBT_DEVELOPMENT_DB.DBT_KMAGLIETTO.team_meetings_overview`, `analytics_db.analytics.fct_amplitude_events`, `ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS_DAILY` | Did HVO-attending teams activate the specific feature they were trained on? And retain at day 28? Amplitude event IDs: 812410671 (Views Set Up), 19916004 (Saved Search), 22834433 (Mailbox Linked) |

### Key Metric Definitions

| Metric | Definition |
|--------|-----------|
| GDR | `1 + (downgrade_and_churn_arr_vs_first_month / end_of_first_month_arr)` — 1.0 = perfect, 0.0 = full churn |
| F28D Activation Rate | % of teams that activated their stated use case within 28 days of survey response |
| D28 Retention Rate | % of activated teams still using that feature at exactly day 28 post-activation (L7 user counts > 0) |
| Onboarded team | At least one user with `participant_attended_conversation = true` and `is_apollo_employee = false` |
| Qualifying user for survey analysis | Core account with non-free email domain, OR paid user; survey response >= 2025-03-26 |
| Maturity window | Cohorts must be ≥ 28 days old before included in activation/retention calculations |
| HVO Activation Rate | % of teams that performed the trained action after HVO meeting (any time within 90 days) |
| HVO Retention Rate | % of teams that performed the trained action during days 22–28 post-meeting |

### Survey Goal → Use Case Mapping
1. `%set automations%` → Genpipe
2. `%optimize meetings%` → Win Close
3. `%use apollo as my crm%` → CRM
4. `%enrich my crm%` → Enrichment
5. Everything else → Leads/Data

### Use Case Activation Definitions (within 28 days)
- **Genpipe**: sequence_created, sequence, ai_sequence, email_sent (manual/auto/extension), workflow, email
- **Win Close**: meeting_assistant, scheduler
- **CRM**: deals, crm_record_management
- **Enrichment**: enrichment_api, enrichment_csv, enrichment_crm_living_data, enrichment_waterfall
- **Leads/Data**: record_actioned

### HVO Topic → Action Mapping
| HVO Topic | Activation Event | Retention Event |
|-----------|-----------------|-----------------|
| Create a contact list | Views Set Up | Views Set Up |
| Create a sequence | Sequence Created | Sequence Created/Used |
| Enrich a contact | Record Actioned | Record Actioned |
| Link my mailbox | Mailbox Linked | Email Used |
| Set-up browser extension | Extension Used | Extension Used |

### Key Performance Numbers (as of last run)
- Paid teams vs. free — Activation: 57.6% vs 33.9% (+23.7 pp); W4 Retention: 57.1% vs 25.5% (+31.6 pp)
- Use Case Hierarchy: Leads/Data > Genpipe > CRM > Enrichment > Win Close (lowest: 3.2% free, 23.9% paid)
- Tier activation surprisingly consistent (37–39.5%); retention better for Tiers 1–3 vs Tier 4

---

## 2. Growth Expansion

**Link:** https://app.hex.tech/apollo/app/019b09ec-f006-7226-8223-938f1a0a4250/latest
**Purpose:** Analyzes self-serve and core account expansion behavior across Apollo's paid customer base. Decomposes ARR into components (seats, add-on credits, inbound fees, discounts), tracks day-over-day expansion events (seat additions, credit upgrades, edition changes), and measures cohort-level expansion rates over time.
**Primary data source:** Daily team audit report from MongoDB, enriched with Salesforce metadata and revenue data.

### Section Structure
- Edition Changes
- Average Seats Per Team
- Paying Teams: Expansion / Upgrade ARR From Feature Gates
- Paying Teams Expanding From First Paid Plan (Core + Non Core)

### SQL Queries & Table Sources

| Query | Key Tables | Purpose |
|-------|-----------|---------|
| `pricing_variant_filter` | `analytics_db.analytics_dataplatform.fct_mongo_daily_team_audit_reports` | Populates Pricing Variants dropdown (distinct values since 2025-11-12) |
| `is_core` | `analytics_db.analytics.dim_salesforce_apollo_teams`, `analytics_db.analytics.dim_salesforce_accounts` | Maps Apollo team → Salesforce `is_core_account` flag |
| `arr_base` (central fact table) | `fct_mongo_daily_team_audit_reports` LEFT JOIN `is_core` | Decomposes daily ARR into: `normal_seat`, `add_on_unified_credits`, `add_on_direct_dial_credits`, `add_on_export_credits`, `add_on_lead_credits`, `inbound_fee`, `discounted_seat_price_difference`. Annualizes: `(amount / billing_interval_months) * 12`. Maps `enterprise`/`organization` → `Custom`. Filter: `date >= 2025-11-12`, `arr > 0`. Legacy coupon discount EXCLUDED (commented out, 12/17/25 Andrew Green). |
| `arr_ss_core` | `arr_base`, `analytics_db.analytics.fct_daily_revenue`, `analytics_db.analytics.dim_salesforce_apollo_teams`, `analytics_db.analytics.dim_salesforce_accounts` | Self-serve core accounts only, enriched with first purchase date |
| `expansion_events` | `arr_base` (aggregated) | Day-over-day expansion via LAG(). Computes `seat_delta`, `arr_delta`, flags: `seat_expanded`, `unified_credit_expanded`, `direct_dial_expanded`, `export_credit_expanded`, `lead_credit_expanded`, `arr_expanded`, `any_expansion`. NOTE: uses `reported_arr` for seat ARR (hack due to legacy coupon inaccuracy). |
| `expansion_events2` | `arr_base` | Seat-specific expansion events with `SEAT_CHANGE` label (e.g., `1-->2`) |
| `credit_expansion_events` | `arr_base` (credit types only) | Credit-specific expansion per credit type using LAG() on `CREDIT_AMOUNT` |
| `new_credit_purchase_events` | `arr_base`, `fct_daily_revenue`, `dim_salesforce_apollo_teams`, `dim_salesforce_accounts` | First-ever credit purchase per type per team; classified by timing relative to first paid date (`at_first_purchase`, `post_first_purchase`, `pre_first_purchase`) |
| `dataframe_2` (Avg Seats) | `arr_base`, `dim_salesforce_apollo_teams`, `dim_salesforce_accounts` | Average Seats Per Team by `account_sales_department_tier` |
| `dataframe_6` (Edition Changes) | `arr_base` | Edition upgrade/downgrade detection via hierarchy (basic=1, professional=2, custom=3). Types: `Basic_to_Professional`, `Professional_to_Custom`, etc. |
| `dataframe_3` (Feature Gate Upgrades) | `analytics_db.analytics_dataplatform.dim_mongo_teams`, `analytics_db.analytics.fct_pricing_variant_changes`, `dim_salesforce_apollo_teams`, `dim_salesforce_accounts`, `analytics_db.analytics.fct_amplitude_events`, `analytics_db.analytics_datascience.int_team_product_info_cleaned`, `analytics_db.analytics.fct_daily_revenue` | Ties upgrade purchases to Feature Gate events seen in Amplitude within 2 days prior. UC pricing variants only (`ilike '%uc%'`). Warehouse: `elt_wh_dp` |
| `dataframe_5` (Cohort Expansion Rates) | `analytics_db.analytics_datascience.int_team_product_info_cleaned`, `generator(rowcount => 400)` | Weekly cohort analysis: % teams expanding (seats/credits) from first paid plan date. Cohort entry: first paid >= 2025-06-01. 90-day / 13-week window. |
| `dataframe_7` (Custom Plans Seat Expansion) | `analytics_db.analytics.fct_daily_revenue`, `analytics_db.analytics.fct_account_edition_changes`, `analytics_db.analytics.fct_apollo_daily_seat_limits`, `analytics_db.analytics.fct_monthly_revenue`, `analytics_db.analytics.fct_apollo_monthly_seat_limits` | Cumulative seat addition rates for Custom-edition teams, split by self-serve vs. rep-assisted. First purchase in 2025, monthly tracking up to 12 months. |

### Key Business Rules

1. **ARR Annualization**: `(value / billing_interval_months) * 12`
2. **Edition Mapping**: `enterprise` and `organization` → `Custom`
3. **Edition Hierarchy**: basic=1 < professional=2 < custom=3 (upgrade/downgrade detection)
4. **Legacy Coupon Discount**: Excluded from calculated ARR (commented out, inaccurate as of 12/17/25)
5. **Seat ARR Workaround**: Expansion events use `reported_arr` filtered to `normal_seat` component
6. **New Credit Purchase**: `CREDIT_AMOUNT > 0 AND COALESCE(PREV_CREDIT_AMOUNT, 0) = 0`
7. **Feature Gate Attribution Window**: 2 days prior to purchase date
8. **Cohort Expansion Window**: 90 days (13 weeks) for weekly; 12 months for Custom edition monthly
9. **Cohort Entry**: First paid plan >= 2025-06-01 for weekly cohort; 2025 calendar year for Custom
10. **Core Account Filter**: Optional toggle → `is_core_account = true` via Salesforce
11. **UC Pricing Variant Filter**: `pricing_variant ilike '%uc%'`

### Input Parameters
- `pricing_variants` — Multi-select filter (from `fct_mongo_daily_team_audit_reports` since 2025-11-12)
- `core_filter` — Boolean toggle for core account restriction

---

## 3. Pricing Dashboard

**Link:** https://app.hex.tech/apollo/app/019746e7-aef3-7008-a6e1-d03bd4fac8e0/latest
**Internal title:** Copy of [TEMP] Price Increase -- F2P + ARR Stats
**Purpose:** Tracks the impact of pricing variant changes on team creation, free-to-paid conversion, and ARR across newly created teams and migrated teams. Supports A/B-style analysis of pricing experiments by comparing conversion rates, purchase behavior, and revenue impact across variants (e.g., `25Q2_UC_AB59`, `24Q4_W59_V3`).
**Last run (at extract time):** 2025-12-10 (auto-refreshes after 1 hour; ~2 min runtime)

### Section Structure
1. Global Parameters
2. New Teams — Last 14 days (BAN cards)
3. New Teams — Week over week (charts)
4. Migrated Teams — Last 14 days (BAN cards)
5. Migrated Teams — Week over week (charts)
6. Recent Migrations: Before and After (under development)

### SQL Queries & Table Sources

| Query | Key Tables | Purpose |
|-------|-----------|---------|
| `df_pricing_variants` | `analytics_db.analytics_dataplatform.dim_mongo_teams` | Populates pricing variant dropdown for teams created in selected date range |
| `df_new_teams_with_purchase` | `analytics_db.analytics_dataplatform.dim_mongo_teams`, `analytics_db.analytics.fct_pricing_variant_changes`, `analytics_db.analytics.dim_salesforce_apollo_teams`, `analytics_db.analytics.dim_salesforce_accounts`, `analytics_db.analytics.fct_daily_revenue` | Core query for New Teams section. CTE chain: resolves earliest pricing variant per team, joins first `new` purchase, filters to variants above threshold. Computes `days_from_changed_to_purchase`, `weeks_from_changed_to_purchase`. |
| `df_ban__teams_created_l14` | `df_new_teams_with_purchase` | L14D BAN cards: teams_created, teams_purchasing, % purchasing, ARR, ARPU |
| `df_new_teams_with_purchase_rates` | `df_new_teams_with_purchase` | Cohorted purchase rates at 1d, 7d, 14d, 21d windows; nulls out rates where cohort not yet mature |
| `df_migrations_with_purchases` | `analytics_db.analytics.fct_pricing_variant_changes`, `analytics_db.analytics_datascience.dim_teams_daily`, `analytics_db.analytics.dim_salesforce_apollo_teams`, `analytics_db.analytics.dim_salesforce_accounts`, `analytics_db.analytics.fct_daily_revenue` | Migrated teams with post-migration purchases. `change_category in ('new', 'upgrade')`. Churn-within-4-days flag. |
| `df_ban__teams_migrated_l14` | `df_migrations_with_purchases` | Same BAN structure for migrated teams |
| `df_migration_batches` | `dbt_development_db.dbt_khlavka.temp__paid_migration_cohorts` | Populates migration batch dropdown (batches 0–29) |
| `df_migrated_with_arr_weeks` | `analytics_db.analytics.fct_pricing_variant_changes`, `analytics_db.analytics.fct_weekly_revenue`, `analytics_db.analytics.dim_salesforce_apollo_teams`, `analytics_db.analytics.dim_salesforce_accounts`, `analytics_db.analytics.dim_date`, `dbt_development_db.dbt_khlavka.temp__paid_migration_cohorts` | Before/After migration ARR analysis. Weekly panel via cross-join to date spine. `total_arr_change_vs_mig_week_start` = ARR change relative to week before migration. Supports batch filtering + churn exclusion. |
| Anomaly Explorer (`dataframe`) | Same as above + `analytics_db.analytics.fct_daily_revenue` | Ad-hoc investigation of individual teams. Hardcoded to `changed_week = '2025-06-15'`. |
| `dataframe_2` | `analytics_db.analytics.fct_monthly_revenue` | One-off lookup for team `661cfb74a28d3e03038f7849` (debug) |

### Key Business Rules

1. **Minimum teams threshold** (`input__min_teams_created`): Variants below threshold excluded from all views
2. **New purchase**: `change_category = 'new'` for new teams; `change_category in ('new', 'upgrade')` for migrated
3. **Parent account exclusion**: `is_parent_account = false` everywhere
4. **Purchase rate maturity**: Rates nulled out if insufficient time has passed for the cohort
5. **Paid at migration**: `fct_weekly_revenue.arr > 0` in the week before migration
6. **First paid before lookback**: Only includes teams whose first paid week was before the lookback window start (for "Paid @ Migration Only" filter)
7. **Churn exclusion**: Teams with churn events 4 days (C24) or 6 days (C41) before migration can be excluded
8. **Week definition**: Sunday-based `date_trunc(week, date + 1) - 1`

### Global Input Parameters
- `input__start_date` — Start date (created or migrated on or after)
- `input__min_teams_created` — Minimum teams created threshold for variant inclusion
- `input__exclude_current_week` — Boolean
- `input__pricing_variant` — Dropdown filter (single variant)
- `input__lookback_weeks` — Weeks before migration (negative numbers)
- `input__migration_batches` — Multi-select migration batches
- `input__ignore_churns_1d_6d_before_migration` — Boolean
- `input__migration_pivots__paid_at_migration` / `input__migration_pivots__free_at_migration` — Boolean

### Dev Note
`dbt_development_db.dbt_khlavka.temp__paid_migration_cohorts` is a dbt dev table (not production). Contains 30 migration batches.

---

## 4. FY27 R&D Performance Dashboard

**Link:** https://app.hex.tech/apollo/app/019c7c97-d667-700d-a7d2-63fea2b9b96f/latest
**Purpose:** Tracks R&D performance across Apollo's product surface to help XFNs monitor Horizon 1, Horizon 2, and Horizon 3 initiatives. Sourced from the [FY-27 R&D Performance Dashboard Notion doc](https://www.notion.so/apolloio/FY-27-R-D-Performance-Dashboard-306ab2b3b49680fabdb9db83d973fe7a).

### Section Structure (12 collapsible sections)
1. Filters / Global Parameters
2. Seat Limits
3. Tara's Queries (master queries: platform_actives, paid_penetration, conversion_rates, nrr_segment, retention, participation_rate)
4. Paid Penetration
5. Active Teams and Users
6. Conversion Rates
7. NRR
8. Retention
9. Participation Rate
10. Activation
11. Support Conversations
12. Data Quality (email deliverability, dialer connect rate)
13. Integration Connections
14. Credits
15. Match Rate / Fill Rate
16. Inbound & Parallel Dialer

### Global Input Parameters
| Parameter | Description |
|-----------|-------------|
| `country` | Filter by `shipping_country` |
| `team_edition` | Filter by plan edition |
| `industry` | Filter by `apollo_industry` |
| `last_n_days` | Lookback window (default 30) |
| `last_n_weeks` | Lookback window in weeks |
| `account_segment` | VSB, SMB, Mid-Market, Enterprise, etc. |
| `tier` | `account_sales_department_tier` |
| `core_or_paid` | Core vs paid filter |
| `customer_type` | all / core / paid / core_and_paid / core_or_paid |
| `core_filter` | all / core / not_core |
| `retention_days` | d7, d14, d28, d90 |
| `activation_window` | Configurable day count |

### SQL Queries & Table Sources

| Query | Key Tables | Purpose |
|-------|-----------|---------|
| `dim_teams_dimensions` | `analytics_db.analytics_datascience.dim_teams` | Distinct filter dimension values for dropdowns. Account segment: `non-core` when `is_core_account=0`, else `coalesce(account_segment, 'unavailable')`. Warehouse: `elt_wh_dp` |
| `seat_metrics` | `analytics_db.analytics_datascience.dim_teams_daily`, `dim_teams`, `dim_users` | Weekly seat metrics for paid teams (last 365 days). Computes avg/median paid seat limits, seat utilization (`active_users / paid_seats`), seat penetration (`paid_seats / sales_department_size`), seat tier distribution (1, 2-3, 4-5, 6+). Warehouse: `elt_wh_dp` |
| `platform_actives` | `analytics_db.analytics_datascience.product_metrics_daily` | DAU/DAT/WAU/WAT/MAU/MAT for `use_case = 'apollo_platform'`. Parses `segment` string via regex (4th group: vsb/smb/mid_market/enterprise). `paid_only_count` and `total_count`. |
| `paid_penetration` | `analytics_db.analytics_datascience.product_metrics_daily` | Same as above with `core_filter` and `account_segment` multi-select. Adds `unpaid_only_count`. |
| `conversion_rates` | `analytics_db.analytics_datascience.product_metrics_daily` | `use_case = 'conversion'`, topics `paid_d7`/`paid_d14`. `daily_conversion_rate = converted_count / cohort_size`. Window functions for weekly/monthly rates. |
| `nrr_segment` | `analytics_db.analytics_datascience.product_metrics_daily` | `use_case = 'nrr'`, `metric = 'amount'`, last day of month only. Components: `nrr_starting_arr`, `nrr_upgrade_arr`, `nrr_churned_and_downgraded_arr`. `segment_nrr_rate = (starting + upgrade + churned_downgraded) / starting`. |
| `retention` | `analytics_db.analytics_datascience.product_metrics_daily` | `use_case = 'retention'`. Topics like `workflow_d7`, `sequence_d28`, `overall_d90`. `daily_retention_rate = retained_count / cohort_size`. |
| `participation_rate` | `analytics_db.analytics_datascience.product_metrics_daily` | Feature-level WAT for: genpipe, win_close, enrichment, ai, crm, extension. `daily_participation_rate = feature_wat / total_wat`. |
| `activation_query` | `ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS` | Feature activation rates within activation window for: Overall, Record Actioned, Enrichment, Call Dialed, Sequence Created, Email Sent (any type), Workflows, Win & Close, Extensions, List Building. Teams must convert to paid within window. |
| `support_conversations_by_tags` | `analytics_db.analytics.dim_support_conversations` LEFT JOIN `dim_teams` | AI-generated tags per conversation (up to 3), unpivoted, ranked by weekly volume. Top 20 shown; rest as "Other". Excludes team IDs `551e3ef07261695147160000` and `68127710414502001d3312fd`. |
| `sequence_emails_sent_stats` | `analytics_db.analytics_dataplatform.fct_mongo_emailer_messages` LEFT JOIN `dim_mongo_email_accounts`, `dim_teams` | Email deliverability metrics. Non-SendGrid/Mailgun only, `outreach_automatic_email` type, 26-week window. Metrics: `delivery_rate`, `overall_bounce_rate`, `spam_blocked_rate`, `open_rate`, `reply_rate`, `unsubscribe_rate`, `interest_received_rate`. |
| `dialer_call_connect_rate` | `analytics_db.analytics_dataplatform.FCT_MONGO_PHONE_CALLS` LEFT JOIN `dim_teams` | Calls with `twilio_call_sid`, last 26 weeks. `connect_rate = calls_connected / calls_dialed`. |
| `crm_integrations_connected_wat` | `analytics_db.analytics_datascience.fct_user_crm_integration_status_daily` LEFT JOIN `dim_users`, `dim_teams` | Weekly distinct paid teams with SFDC, Pipedrive, Hubspot integrations (last 365 days, current week excluded). |
| `WoW_credits_used` | `analytics_db.analytics.agg_team_credits` LEFT JOIN `dim_teams` | Weekly credits used by team, with `credits_used_per_team`. Excludes `ai_email`/`conversation` feature types, `conversation_credit` credit type, and Apollo RevOps instance. |
| `WoW_credits_used_feature_type` | `agg_team_credits` JOIN `dim_teams_daily` | Last 4 complete weeks. WoW % growth via LAG(). |
| `wow_credits_used_by_feature_type` | `analytics_db.analytics.agg_team_credits` | `credits_used_per_team` by week and feature_type. |
| `dataframe_2` (Fill Rate) | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_CSV_ENRICHMENT_JOBS` with LATERAL FLATTEN | `fill_rate = fills / matches` per field name and modality. Specific team IDs (data duel teams), last 90 days before 2026-02-14. |
| `dataframe` (Match Rate) | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_CSV_ENRICHMENT_JOBS` | `match_rate = matches / processed_rows` for Organizations and People. Same scope as fill rate. |
| `arr` (Parallel Dialer ARR) | `analytics_db.analytics.dim_salesforce_apollo_teams`, `dim_salesforce_accounts`, `analytics_db.analytics_dataplatform.dim_mongo_teams_rt_vw`, `analytics_db.analytics.dim_salesforce_opportunities`, `raw_fivetran_db.salesforce.opportunity` | Parallel Dialer plans (`plan_id ilike '%dialer%'`). Hard-coded ARR: monthly=$149×12, yearly=$119×12, quarterly=$149×12. Matches to closed-won opps ±1 day. Priority: Rep-Led > Self-Serve, New Business > Upsell > Renewal. Daily snapshot from 2025-10-01. |
| `inbound_arr` | Same as above | Same structure for `plan_id ilike '%inbound%'`. |
| `base_query` (Dialer/Inbound WAT) | `analytics_db.analytics_datascience.dim_users_daily` LEFT JOIN `user_dialer_actions_daily`, `user_inbound_actions_daily`, `user_workflow_actions_daily`, `user_discovery_actions_daily`, `user_sequence_actions_daily` | 50+ WAU/WAT columns for: email sent, parallel dialer, one-off dialer, inbound sub-actions, workflows, integration workflows, discovery/recommendations, scoring, deliverability, tasks, contact outreach. Since 2025-05-01, paid users only. |

### Key Business Rules

1. **Account Segment Derivation**: `CASE WHEN coalesce(is_core_account,0) = 0 THEN 'non-core' ELSE coalesce(account_segment, 'unavailable') END`
2. **Segment String Parsing**: 4th regex capture group from `paid|not_paid_core|not_core_tier_N_segment_...`
3. **Excluded Team IDs**: `551e3ef07261695147160000` (Apollo RevOps), `68127710414502001d3312fd`, `620210171b9d04008e2ac0e0`, `5b33b1e1079cc732d656a677`
4. **Credit Exclusions**: `feature_type NOT IN ('ai_email', 'conversation')`, `credit_type NOT IN ('conversation_credit')`
5. **Inbound/Dialer ARR pricing (hard-coded)**: Monthly=$149×12/yr, Yearly=$119×12/yr, Quarterly=$149×12/yr
6. **Opportunity Matching**: Closed-won opps matched to plan start dates within ±1 day; Rep-Led > Self-Serve, New Business > Upsell > Renewal > Other
7. **Email Stats Filters**: Non-SendGrid/Mailgun channels, `outreach_automatic_email` type, 26-week window
8. **NRR**: Month-end dates only. `nrr_rate = (starting + upgrade + churned_downgraded) / starting`
9. **Activation Gate**: Team must have converted to paid within `activation_window` days of creation

### Central Data Source: `product_metrics_daily`
The `analytics_db.analytics_datascience.product_metrics_daily` table is the canonical source for:
- Platform actives (DAU/WAU/MAU, DAT/WAT/MAT)
- Paid penetration
- Conversion rates (d7, d14)
- NRR (starting ARR, upgrade ARR, churned/downgraded ARR)
- Retention (by feature and window)
- Participation rate (by feature)

Segment column is a compound string with format `paid|not_paid_core|not_core_tier_N_vsb|smb|mid_market|enterprise|unknown` — parse with 4th regex capture group.

---

## Cross-Notebook Table Source Index

| Table | Schema | Used In |
|-------|--------|---------|
| `product_metrics_daily` | `analytics_datascience` | FY27 R&D (all major metrics) |
| `dim_teams` | `analytics_datascience` | FY27 R&D (segments, activation, seat metrics) |
| `dim_teams_daily` | `analytics_datascience` | FY27 R&D (seats, credits), Pricing Dashboard |
| `dim_users` | `analytics_datascience` | FY27 R&D (seats, CRM integrations), Onboarding Activation |
| `dim_users_daily` | `analytics_datascience` | FY27 R&D (Inbound/Dialer WAT) |
| `fct_user_crm_integration_status_daily` | `analytics_datascience` | FY27 R&D (CRM integrations) |
| `int_team_product_info_cleaned` | `analytics_datascience` | Growth Expansion (cohort expansion) |
| `user_dialer_actions_daily` | `analytics_datascience` | FY27 R&D (Parallel Dialer WAT) |
| `user_inbound_actions_daily` | `analytics_datascience` | FY27 R&D (Inbound WAT) |
| `fct_mongo_daily_team_audit_reports` | `analytics_dataplatform` | Growth Expansion (arr_base) |
| `dim_mongo_teams` | `analytics_dataplatform` | Growth Expansion, Pricing Dashboard |
| `fct_mongo_emailer_messages` | `analytics_dataplatform` | FY27 R&D (email deliverability) |
| `FCT_MONGO_PHONE_CALLS` | `analytics_dataplatform` | FY27 R&D (dialer connect rate) |
| `dim_mongo_teams_rt_vw` | `analytics_dataplatform` | FY27 R&D (Inbound/Dialer ARR) |
| `DIM_MONGO_CSV_ENRICHMENT_JOBS` | `analytics_dataplatform` | FY27 R&D (fill rate, match rate) |
| `fct_daily_revenue` | `analytics` | Growth Expansion, Pricing Dashboard |
| `fct_weekly_revenue` | `analytics` | Pricing Dashboard (before/after migration) |
| `fct_monthly_revenue` | `analytics` | Growth Expansion (Custom expansion), Pricing Dashboard (debug) |
| `fct_revenue_stats_monthly` | `analytics` | Onboarding Activation (GDR) |
| `fct_pricing_variant_changes` | `analytics` | Growth Expansion (feature gates), Pricing Dashboard |
| `fct_amplitude_events` | `analytics` | Growth Expansion (feature gate attribution), Onboarding Activation |
| `fct_account_edition_changes` | `analytics` | Growth Expansion (Custom plan seat expansion) |
| `fct_apollo_daily_seat_limits` | `analytics` | Growth Expansion (Custom plan seat expansion) |
| `fct_apollo_monthly_seat_limits` | `analytics` | Growth Expansion (Custom plan seat expansion) |
| `agg_team_credits` | `analytics` | FY27 R&D (credits WoW) |
| `dim_support_conversations` | `analytics` | FY27 R&D (support tags) |
| `dim_salesforce_accounts` | `analytics` | Growth Expansion, Pricing Dashboard, Onboarding Activation |
| `dim_salesforce_apollo_teams` | `analytics` | Growth Expansion, Pricing Dashboard, Onboarding Activation, FY27 R&D |
| `dim_salesforce_opportunities` | `analytics` | FY27 R&D (Inbound/Dialer ARR) |
| `dim_date` | `analytics` | Pricing Dashboard (date spine for before/after) |
| `team_meetings_overview` | `dbt_development_db.dbt_kmaglietto` | Onboarding Activation (HVO meeting counts, GDR) |
| `calendar_events` | `dbt_development_db.dbt_kmaglietto` | Onboarding Activation (onboarded/non-onboarded GDR) |
| `temp__paid_migration_cohorts` | `dbt_development_db.dbt_khlavka` | Pricing Dashboard (migration batches) |
| `raw_fivetran_db.salesforce.opportunity` | `raw_fivetran_db` | FY27 R&D (products sold field for ARR matching) |
