# Jarvis Knowledge Base Manifest

**Purpose:** Complete inventory of Jarvis's live knowledge base — what's here, how it's organized, and how to maintain it.

**Date:** 2026-04-14
**Status:** Live
**Maintained by:** Bridie Meredith

> **All files in `jarvis/knowledge/` (except this file and `domain_context.md`) are managed by one-way sync from `analytics-copilot`.** Do not edit synced files directly — changes will be overwritten. To update Jarvis's knowledge, edit the source in `analytics-copilot` and run `/sync-jarvis`. The authoritative list of synced files is `analytics-copilot/domain/SYNC_MANIFEST.md`.

______________________________________________________________________

## Overview

| Category | Count |
|---|---|
| Top-level knowledge files | 107 |
| Table context files (`context/`) | 132 (131 tables + template) |
| Metric definitions (`metrics/`) | 6 |
| Analyst suits (`suits/`) | 7 + index |
| **Total files** | **253** |

Three indexes exist — use the right one:

- **This file** — human-readable capability inventory (what's here and why)
- **`domain_context.md`** — auto-generated LLM topic router (129 files, key-fact summaries). This is what Jarvis routes on at query time.
- **`README.md`** — quick-start guide for contributors (how to add/update knowledge)

______________________________________________________________________

## Tier 1: Strategy & Business Context

Always-on references. Jarvis reads these regardless of question type.

| File | Purpose | Status |
|------|---------|--------|
| `annual_targets.md` | FY27 OKR targets by metric. "Are we on track?" → target vs actual | LIVE |
| `theory_of_change.md` | Causal chain: activation → habit → retention → expansion | LIVE |
| `business_state.md` | Current momentum snapshot — updated weekly via `/weekly-context-refresh` | LIVE |
| `product_portfolio_taxonomy.md` | H1/H2/H3 classification + graduation criteria | LIVE |
| `pending_definitions.md` | Known data gaps, fallback responses, and ETAs | LIVE |
| `fiscal_calendar.md` | Apollo FY27 quarter boundaries (Feb-start fiscal year) | LIVE |
| `decisions_log.md` | Authoritative record of strategic decisions by Analytics/Data Leads | LIVE |
| `executive_profiles.md` | What each exec cares about, data consumption style, how to engage | LIVE |
| `active_personas.md` | Background voices (Jarvis, Pepper, Rhodey) that interject when triggered | LIVE |
| `support_channel_context.md` | Guidelines for handling #jarvis-support-qs questions | LIVE |
| `product_disambiguation.md` | "Product" means four different things — which lens to use | LIVE |

## Tier 1a: AOP & Exec Priorities

Strategic planning documents — FY27 annual operating plans by org.

| File | Purpose | Status |
|------|---------|--------|
| `aop_fy27_strategic_priorities.md` | Company-wide FY27 strategic priorities | LIVE |
| `aop_execution_alignment_20260324.md` | FY27 AOP vs actual execution cross-check (2026-03-24 snapshot) | LIVE (snapshot) |
| `executive_priorities_fy27.md` | What needs to be measured per exec priority | LIVE |
| `executive_measurement_requirements.md` | Dimensions, grains, and data gaps for exec questions | LIVE |
| `fy27_aop_analytics.md` | Analytics org AOP | LIVE |
| `fy27_aop_growth_acquisition.md` | Growth & Acquisition AOP | LIVE |
| `fy27_aop_gtme_partnerships_support.md` | GTME, Partnerships & Support AOP | LIVE |
| `fy27_aop_org_map.md` | Org map & ownership reference | LIVE |
| `fy27_aop_rnd.md` | R&D AOP | LIVE |
| `rnd_okr_structure.md` | R&D OKR structure for FY27 — team organization + scorecard | LIVE (snapshot) |
| `conversion_team_q2_fy27_okr.md` | Conversion team Q2 FY27 — 3 KRs: Trial W2 CVR, W2 FTP, SS Annual Purchase Rate | LIVE |
| `aop_execution_alignment_20260420.md` | FY27 AOP vs actual execution cross-check (2026-04-20 snapshot) | LIVE (snapshot) |
| `expansion_team_q2_fy27_okr.md` | Expansion team Q2 FY27 OKRs — Obj 2 improve NRR (H1) | LIVE |
| `q2_fy27_rnd_product_strategy.md` | Q2 FY27 R&D product strategy across all product teams — compiled cross-team reference | LIVE |

## Tier 2: Metric Methodologies

Loaded when the question is metric-specific.

| File | Metric/Domain | Status |
|------|---------------|--------|
| `activation_methodology.md` | F14D Habit RA Rate — formula, golden population, caveats | LIVE |
| `churn_taxonomy_draft.md` | Churn reasons by category — framework for "why churning?" | DRAFT |
| `ai_sheets_user_definition.md` | GTM Engineer cohort definition | DRAFT (pending product confirmation) |
| `inbound_team_identification.md` | Inbound add-on revenue attribution — data source + mapping | DRAFT (pending product flag) |
| `new_trial_influenced_ss_arr.md` | Trial-influenced self-serve ARR — 14-day attribution window | LIVE |
| `credit_types.md` | Canonical credit type reference (waterfall, enrichment, etc.) | LIVE |
| `credit_utilization_and_retention.md` | Credit utilization & retention findings (data sparring) | LIVE |
| `hvo_activation_findings.md` | HVO activation & retention findings — dialer lift, segment impact | LIVE |
| `deliverability.md` | Email deliverability domain reference | LIVE |
| `mcp_analytics.md` | MCP connector analytics — user identification, adoption cohorts | LIVE |
| `credits.md` | Canonical credit cap utilization reference — supersedes utilization narrative in credit_types.md | LIVE |
| `nrr_segment_definition.md` | Canonical NRR/GRR segment definition validated by Leo Liu (2026-04-24) | LIVE |
| `m0_credit_attach_signal.md` | M0 credit attach = churn risk flag (61% M3 churn); M1+ attach = healthy signal | LIVE |
| `phantom_churn_reactivation.md` | Phantom churn/reactivation events in FCT_DAILY_REVENUE caused by Salesforce renewal cycling | LIVE |

### Metric Definitions (`metrics/`)

AE-owned metric definitions — the spec for each metric before it enters `LU_SAVED_METRICS`.

| File | Metric |
|------|--------|
| `metrics/f14d_habit_ra_rate.md` | F14D Habit Record Action Rate |
| `metrics/free_to_paid_rate.md` | Free-to-Paid Conversion Rate |
| `metrics/inbound_revenue_attribution.md` | Inbound Revenue Attribution |
| `metrics/m3_cohort_nrr.md` | M3 Cohort NRR |
| `metrics/ss_annual_purchase_rate.md` | Self-Serve Annual Purchase Rate |
| `metrics/trial_w2_conversion_rate.md` | Trial W2 Conversion Rate |

## Tier 3: Domain Knowledge

SQL patterns, join logic, revenue structure, add-on tracking.

| File | Purpose | Status |
|------|---------|--------|
| `sql_patterns.md` | Canonical SQL patterns for common analytical questions | LIVE |
| `segment_join_canonical.md` | How to join segment data — LU_TEAM_SEGMENT is canonical | LIVE |
| `lu_team_segment_patterns.md` | 5 reusable SQL patterns for segment-sliced queries | LIVE |
| `lu_saved_metrics.sql` | Registry SQL for saved metrics | LIVE |
| `glossary_entries.md` | Metric and term definitions | LIVE |
| `revenue_org_structure.md` | Revenue org structure — how to debrief revenue, motion splits | LIVE |
| `sales_motion_definitions.md` | Rep-driven vs self-serve definition inventory | LIVE |
| `stripe_billing_patterns.md` | Apollo's Stripe billing patterns — critical for Stripe data analysis | LIVE |
| `dialer_addon_churn.md` | Dialer add-on churn tracker | LIVE |
| `dialer_addon_purchases.md` | Dialer add-on purchases | LIVE |
| `inbound_addon_churn.md` | Inbound add-on churn tracker | LIVE |
| `inbound_addon_purchases.md` | Inbound add-on purchases | LIVE |
| `de_owned_tables_architecture.md` | FCT table architecture — DE-owned building blocks for team analytics | LIVE |
| `dim_table_infrastructure.md` | DIM table landscape, lineage, and rebuild plan | LIVE |
| `signal_sources.md` | Signals pipeline — source reference for WEEKLY_TEAM_SIGNALS | LIVE |
| `cbr_data_sources.md` | CBR data sources & methodology | LIVE |
| `hex_cbr_notebooks.md` | Hex CBR & Growth notebook context extract | LIVE |
| `hex_notebooks_context.md` | Hex notebooks — SQL table sources, metric definitions, business rules | LIVE |
| `amplitude_event_check.md` | Amplitude event check — skill reference for investigating metric moves | LIVE |
| `amplitude_protected_events.md` | Protected Amplitude event_type_ids — cannot be renamed/deleted | LIVE |
| `source_catalog.md` | Source catalog skill reference | LIVE |
| `ask_henry_query_guide.md` | Ground-truth table/filter/assumption guide for Ask Henry answers | LIVE |
| `ask_henry_questions.md` | Bank of real questions from #ask-henry Slack bot | LIVE |
| `mongo_collection_check.md` | Audit recent code changes affecting Mongo collections | LIVE |
| `crm_integration.md` | CRM integration analytics — which table to use, metric definitions, data gaps | LIVE |
| `dialer.md` | Dialer product, access, and entitlement — modes, metering, Jan 2026 add-on structural break | LIVE |
| `domain_compact.md` | Auto-generated compact summary of 127 domain files — LLM router reference | LIVE |
| `finance.md` | Master index for all finance, revenue, and billing knowledge | LIVE |
| `gtme_did_playbook.md` | Reusable DiD causal playbook for GTME CSM effectiveness analysis | LIVE |
| `gtme_interventions_status_l26w.md` | GTME interventions status over last 26 weeks from analytics_datascience.interventions | LIVE |
| `gtme_managed_teams.md` | Definition and identification of GTME managed teams (paid + custom plan + gtme_name) | LIVE |
| `hex_notebooks_context_v2.md` | Hex notebook context extract v2 — addendum covering 14 projects not in v1 | LIVE |
| `hex_project_catalog.md` | Full inventory of all Hex projects in Apollo org, organized by product area | LIVE |
| `partnerships.md` | Partnerships domain context — tech partnerships, data sources, analytics coverage | LIVE |
| `partnerships_identification.md` | How to identify partnership teams via FCT_AMPLITUDE_EVENTS partner_id (no native logging) | LIVE |
| `cbr_weekly_context.md` | Live OKR status and business metrics from CBR #18 (Apr 28-29 2026) | LIVE (snapshot) |

## Tier 4: Org & People

Team structure, department profiles, squad coverage.

| File | Purpose | Status |
|------|---------|--------|
| `team_roster.md` | Apollo analytics team roster | LIVE |
| `department_profiles.md` | Department → analytics partner mapping | LIVE |
| `squad_profiles.md` | Squad-level profiles, identifies gaps in analytics support | LIVE |
| `player_cards.md` | Analytics Pokemon Trainer Cards (team fun) | LIVE |
| `pokemon_compendium.md` | Full trainer card compendium reference | LIVE |
| `zone_assignments.yaml` | DS/AE zone coverage — source of truth for who owns what | LIVE |
| `org_pulse.md` | Org pulse snapshot (generated via `/org-pulse-scan`) | LIVE (snapshot) |
| `analytics_org_tree.md` | Analytics/Data org reporting chain from LU_DARWINBOX_POSITIONS (2026-04-20 snapshot) | LIVE (snapshot) |
| `squad_summaries_current.md` | Auto-generated squad activity summaries — week of 2026-05-11 | LIVE (snapshot) |

## Tier 5: Table Context (`context/`)

One `.md` file per approved Snowflake table — schema, trust tier, join patterns, caveats. **132 files** (131 tables + `_TEMPLATE.md`). The query guardrail enforces that every queried table has a context file.

Not listed individually here — see `context/` directory. Key tables:

| File | Table | Domain |
|------|-------|--------|
| `context/FCT_DAILY_REVENUE.md` | `FCT_DAILY_REVENUE` | Revenue/ARR |
| `context/FCT_MONTHLY_REVENUE.md` | `FCT_MONTHLY_REVENUE` | Revenue/NRR |
| `context/AGG_TEAM_CREDITS.md` | `AGG_TEAM_CREDITS` | Credit pipeline |
| `context/DIM_TEAMS_DAILY.md` | `DIM_TEAMS_DAILY` | Team snapshots |
| `context/DIM_USERS_DAILY.md` | `DIM_USERS_DAILY` | User snapshots |
| `context/PRODUCT_METRICS_DAILY.md` | `PRODUCT_METRICS_DAILY` | WAT, feature usage |
| `context/WEEKLY_TEAM_SIGNALS.md` | `WEEKLY_TEAM_SIGNALS` | Signals pipeline |
| `context/LU_TEAM_SEGMENT.md` | `LU_TEAM_SEGMENT` | Segment lookup |
| `context/LU_EMPLOYEE_ACTIVITY.md` | `LU_EMPLOYEE_ACTIVITY` | Employee activity digest |

## Tier 6: Analyst Suits (`suits/`)

Suits teach Jarvis to think and communicate like a specific analyst. See `suits/index.md` for full routing rules.

| File | Codename | Analyst | Domain |
|------|----------|---------|--------|
| `suits/index.md` | — | — | Routing rules, domain triggers, Iron Legion roster |
| `suits/mark_l.md` | Mark L | Leo Liu | NRR/GRR, cohort retention, mix-shift, dark-mode HTML |
| `suits/friday.md` | Friday | Leo Liu (leader) | Coaching, career, team direction |
| `suits/war_machine.md` | War Machine | Pubudu | MECE, stat-sig, experiments |
| `suits/iron_patriot.md` | Iron Patriot | Pubudu (SQL) | Auto-invoked by War Machine for SQL |
| `suits/pepper.md` | Pepper | Bridie | Credits, foundation, infrastructure, critic mode |
| `suits/veronica.md` | Veronica | Shyam | Signals, cross-domain, enrichment |
| `suits/jarvis_protocol.md` | Jarvis Protocol | Andrew | Metric methodology, experiment rigor |

## Tier 7: Templates & Report Standards

Reusable frameworks for analysis output.

| File | Purpose | Status |
|------|---------|--------|
| `product_debrief_template.md` | Canonical 3-step execution framework for product debriefs | LIVE |
| `template_answer_scaffolding.md` | Step-by-step question → answer workflow | LIVE |
| `template_cbr_report.md` | Company Business Review report template | LIVE |
| `template_cpo_okr_report.md` | CPO OKR cadence report — execution template (no cached data) | LIVE |
| `template_metric_definition.md` | Metric definition spec for handoff to analytics | LIVE |
| `template_question_patterns.md` | Reusable patterns for common question types | LIVE |
| `template_alert_anomaly.md` | Structure for proactive alert notifications to execs | LIVE |
| `template_common_assumptions.md` | Default assumptions when answering questions | LIVE |
| `template_data_source.md` | Template for documenting new data sources | LIVE |
| `template_eval_test_case.md` | Format for scorecard eval test case definitions | LIVE |
| `template_stakeholder_update.md` | Lightweight ad-hoc update format for exec stakeholders | LIVE |
| `html_report_standard.md` | Shared dark-mode HTML styling for all Jarvis reports | LIVE |
| `REPORT_TEMPLATE_REGISTRY.md` | Registry of available report templates | LIVE |
| `handoff_template.md` | Reusable handoff template — owner handoff and consumer adoption tracks | LIVE |
| `personal_action_board.md` | The next_up.md pattern — Tony-voice action board template for teammates | LIVE |
| `finance_onboarding.md` | Finance team Jarvis onboarding guide — pre-read and first-week reference | LIVE |
| `finance_onboarding_facilitator_runbook.md` | Facilitator runbook for Finance × Jarvis live onboarding session (30 min) | LIVE |

## Tier 8: Jarvis Internal (Maintenance & Ops)

Not for exec-facing responses — used by the analytics team to maintain Jarvis.

| File | Purpose | Status |
|------|---------|--------|
| `jarvis_identity.md` | Jarvis identity & relationships (Leo = father, Bridie = godmother) | LIVE |
| `jarvis_characters.md` | Character backstory: Henry, Shyam, Papa Curl, Pride & Dignity protocol | LIVE |
| `jarvis_health_playbook.md` | How to keep Jarvis accurate: sync, refresh, scorecard | LIVE |
| `jarvis_update_protocol.md` | How to update the knowledge base; sync workflow and policy | LIVE |
| `jarvis_action_log.md` | Improvements shipped + backlog | LIVE |
| `contribution_guidelines.md` | Protected files, edit policies, contribution rules | LIVE |
| `quality_check_process.md` | Context quality control process | LIVE |
| `measurement_gap_tracker.md` | Standing tracker for executive measurement gaps | LIVE |
| `activity_tagging.md` | Activity pulse protocol — mandatory tagging for every action | LIVE |
| `mcp_tool_guidelines.md` | Token-efficient MCP usage (Glean, Notion, Gmail, Snowflake) | LIVE |
| `pepper_watchlist.yaml` | Live gap registry — Pepper checks on every data question | LIVE |
| `pepper_audit_log.jsonl` | Pepper audit trail | LIVE |
| `authoring_guide.md` | Best practices for domain files and skill authoring | LIVE |
| `jarvis_pain_points.md` | Accumulated improvement signals and resolution actions | LIVE |
| `jarvis_registry_health.md` | LU_SAVED_METRICS status and table accessibility report | LIVE |
| `jarvis_schema_drift.md` | Documentation vs Snowflake schema comparison report | LIVE |
| `offboarding_protocol.md` | Standard process for analytics team member departure | LIVE |
| `persistent_claude_session.md` | How-to for long-running Claude Code sessions in terminals | LIVE |
| `skill_registry.md` | All analytics copilot skills with status and validation | LIVE |
| `snowflake_mcp_setup.md` | Connect Claude Code to Snowflake via MCP server | LIVE |
| `table_registration_checklist.md` | Three-location registration requirement for new tables | LIVE |
| `hammer.md` | Bad analytics archive — documented flawed analyses and the failure modes behind them | LIVE |
| `jarvis_pulse_runbook.md` | Load-bearing runbook for Jarvis usage measurement system — ops, ownership, break-glass | LIVE |

## Tier 9: Point-in-Time Reports & Project Docs

Snapshots and project-specific docs. Not evergreen — retained for historical context.

| File | Purpose | Status |
|------|---------|--------|
| `analytics_report_2026_03_19.md` | Copilot analytics snapshot (2026-03-18) | Snapshot |
| `ask_henry_plugin_test_report.md` | Plugin validation against 60 real exec questions | Snapshot |
| `copilot_roi.md` | ROI quantification — what was built, speed, what it replaced | Snapshot |
| `dept_assessment_2026-03-11.md` | Analytics team state snapshot (2026-03-11) | Snapshot |
| `dim_teams_daily_v2_gap_analysis.md` | Column coverage verification before V2 promotion | Snapshot |
| `jarvis_slack_bot.md` | FastAPI + Bolt architecture for dedicated Slack app | Reference |
| `metrics_on_demand_architecture.md` | Design for custom metric measurement infrastructure | Reference |
| `project_dim_teams_daily_rebuild.md` | Foundation table rebuild project tracking | Reference |
| `biweekly_insights_findings_2026-05-06.md` | Durable findings from 2026-05-06 bi-weekly product insights review (MCP, dialer, etc.) | Snapshot |
| `support_perception_analysis_apr2026.md` | Apollo support perception multi-source analysis (Notion, 2026-04-03) | Snapshot |

______________________________________________________________________

## Files NOT Managed by Sync

Edit these directly in the jarvis repo:

| File | Why |
|---|---|
| `JARVIS_KNOWLEDGE_BASE_MANIFEST.md` | This file — jarvis-native capability inventory |
| `domain_context.md` | Auto-generated by `scripts/build_domain_context.py` from `analytics-copilot/domain/index.md` |

______________________________________________________________________

## How This Knowledge Base Is Maintained

All synced files flow from `analytics-copilot` via `scripts/sync-jarvis.sh`. The sync is one-way and intentional.

**To update something Jarvis knows:** Edit the source in `analytics-copilot`, then run `/sync-jarvis`.
**To add a new file:** Create in `analytics-copilot/domain/`, add to `SYNC_MANIFEST.md`, add a `cp` line to `sync-jarvis.sh`, run `/sync-jarvis`.

For the full sync reference, see `README.md` in this directory.

______________________________________________________________________

**Last updated:** 2026-05-13
**Next review:** Weekly (business_state.md, org_pulse.md), Quarterly (all others)
