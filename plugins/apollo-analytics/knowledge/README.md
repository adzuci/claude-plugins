# Jarvis Knowledge Base

This directory is Jarvis's live knowledge — domain context, metric definitions, table documentation, and business state that Jarvis loads to answer executive questions.

**All files here (except `JARVIS_KNOWLEDGE_BASE_MANIFEST.md` and `domain_context.md`) are managed by one-way sync from `analytics-copilot`.** Do not edit them directly. Changes will be overwritten on the next sync.

______________________________________________________________________

## How Knowledge Gets Into Jarvis

```
analytics-copilot/           jarvis/knowledge/
  domain/          ──┐
  data-catalog/    ──┤  scripts/sync-jarvis.sh  ──►  (this directory)
  metrics/         ──┤  (run: /sync-jarvis)
  sql/             ──┘
```

The sync is one-way and intentional. `analytics-copilot` has version history, team contribution workflows, and richer context. `jarvis/knowledge/` stays lean (token budget for the plugin). The sync script is the abstraction — not two independent sources of truth.

### To update something Jarvis knows

1. Find the source file in `analytics-copilot` (usually `domain/`)
1. Edit it there
1. Run `/sync-jarvis` (or `bash scripts/sync-jarvis.sh` + commit both repos)

### To add a new knowledge file

1. Create the file in `analytics-copilot/domain/` (or appropriate subdirectory)
1. Add it to `analytics-copilot/domain/SYNC_MANIFEST.md`
1. Add a `cp` line to `analytics-copilot/scripts/sync-jarvis.sh`
1. Run `/sync-jarvis`

______________________________________________________________________

## What's In Here

**78 top-level files, 132 context files, 6 metric definitions, 7 suits + index = 224 total.**

For the full inventory with status flags, see `JARVIS_KNOWLEDGE_BASE_MANIFEST.md`.

### Strategy & Business Context (Tier 1 — always loaded)

| File | What it is |
|---|---|
| `business_state.md` | Current momentum snapshot — NRR, activation, product bets, known risks. **Updated weekly.** |
| `annual_targets.md` | FY27 OKR targets by metric. "Are we on track?" |
| `theory_of_change.md` | Causal chain: activation → habit → retention → expansion. |
| `product_portfolio_taxonomy.md` | H1/H2/H3 classification + graduation criteria. |
| `pending_definitions.md` | Known data gaps, fallback responses, and ETAs. |
| `product_disambiguation.md` | "Product" means four different things. Which lens to use. |
| `fiscal_calendar.md` | Apollo FY27 quarter boundaries (Feb-start fiscal year). |
| `decisions_log.md` | Authoritative strategic decisions by Analytics/Data Leads. |
| `executive_profiles.md` | What each exec cares about, data consumption style. |

### AOP & Exec Priorities

| File | What it is |
|---|---|
| `aop_fy27_strategic_priorities.md` | Company-wide FY27 strategic priorities |
| `executive_priorities_fy27.md` | What needs to be measured per exec priority |
| `executive_measurement_requirements.md` | Dimensions, grains, and data gaps for exec questions |
| `fy27_aop_analytics.md` | Analytics org AOP |
| `fy27_aop_growth_acquisition.md` | Growth & Acquisition AOP |
| `fy27_aop_gtme_partnerships_support.md` | GTME, Partnerships & Support AOP |
| `fy27_aop_org_map.md` | Org map & ownership reference |
| `fy27_aop_rnd.md` | R&D AOP |
| `rnd_okr_structure.md` | R&D OKR structure for FY27 Q1 |
| `conversion_team_q2_fy27_okr.md` | Conversion team Q2 FY27 — Trial W2 CVR, W2 FTP, SS Annual Purchase Rate |

### Metric Methodologies (Tier 2 — loaded for metric-specific questions)

| File | Metric |
|---|---|
| `activation_methodology.md` | F14D Habit RA Rate |
| `churn_taxonomy_draft.md` | Churn reasons by category |
| `ai_sheets_user_definition.md` | GTM Engineer cohort definition |
| `inbound_team_identification.md` | Inbound add-on revenue attribution |
| `new_trial_influenced_ss_arr.md` | Trial-influenced self-serve ARR |
| `credit_types.md` | Canonical credit type reference |
| `credit_utilization_and_retention.md` | Credit utilization & retention findings |
| `hvo_activation_findings.md` | HVO activation & retention findings |
| `deliverability.md` | Email deliverability domain reference |
| `mcp_analytics.md` | MCP connector analytics |
| `metrics/*.md` | AE-owned metric definitions (6 files: FTP rate, M3 NRR, F14D, etc.) |

### Domain Knowledge (Tier 3 — SQL, patterns, revenue structure)

| File | What it is |
|---|---|
| `sql_patterns.md` | Canonical SQL patterns for common analytical questions |
| `segment_join_canonical.md` | How to join segment data — LU_TEAM_SEGMENT is canonical |
| `lu_team_segment_patterns.md` | Reusable SQL for segment-sliced queries |
| `lu_saved_metrics.sql` | Registry SQL for saved metrics |
| `glossary_entries.md` | Metric and term definitions |
| `revenue_org_structure.md` | Revenue org structure — motion splits, how to debrief revenue |
| `sales_motion_definitions.md` | Rep-driven vs self-serve definition inventory |
| `stripe_billing_patterns.md` | Apollo's Stripe billing patterns |
| `de_owned_tables_architecture.md` | FCT table architecture — DE-owned building blocks |
| `dim_table_infrastructure.md` | DIM table landscape, lineage, and rebuild plan |
| `signal_sources.md` | Signals pipeline source reference |
| `source_catalog.md` | Source catalog skill reference |
| `amplitude_event_check.md` | Amplitude event check skill reference |
| `amplitude_protected_events.md` | Protected Amplitude event_type_ids |
| `cbr_data_sources.md` | CBR data sources & methodology |
| `hex_cbr_notebooks.md` | Hex CBR & Growth notebook context |
| `hex_notebooks_context.md` | Hex notebook SQL sources and business rules |

### Add-On Tracking

| File | What it is |
|---|---|
| `dialer_addon_churn.md` | Dialer add-on churn tracker |
| `dialer_addon_purchases.md` | Dialer add-on purchases |
| `inbound_addon_churn.md` | Inbound add-on churn tracker |
| `inbound_addon_purchases.md` | Inbound add-on purchases |

### Org & People

| File | What it is |
|---|---|
| `team_roster.md` | Apollo analytics team roster |
| `department_profiles.md` | Department → analytics partner mapping |
| `squad_profiles.md` | Squad-level profiles, analytics support gaps |
| `player_cards.md` | Analytics Pokemon Trainer Cards |
| `zone_assignments.yaml` | DS/AE zone coverage — who owns what |
| `org_pulse.md` | Org pulse snapshot (generated via `/org-pulse-scan`) |

### Table Context (`context/`) — one file per approved Snowflake table

~132 files. Schema, trust tier, join patterns, caveats. The query guardrail enforces every queried table has a context file.

### Templates & Report Standards

| File | What it is |
|---|---|
| `product_debrief_template.md` | Canonical 3-step execution framework for product debriefs |
| `template_answer_scaffolding.md` | Step-by-step question → answer workflow |
| `template_cbr_report.md` | Company Business Review report template |
| `template_cpo_okr_report.md` | CPO OKR cadence report — execution template (no cached data) |
| `template_metric_definition.md` | Metric definition spec for handoff to analytics |
| `template_question_patterns.md` | Reusable patterns for common question types |
| `html_report_standard.md` | Shared dark-mode HTML styling for all Jarvis reports |
| `REPORT_TEMPLATE_REGISTRY.md` | Registry of available report templates |

### Analyst Suits (`suits/`) — methodology + output style

7 suits + routing index. See `suits/index.md` for routing rules.

| File | Codename | Analyst |
|---|---|---|
| `suits/mark_l.md` | Mark L | Leo (analyst) |
| `suits/friday.md` | Friday | Leo (leader) |
| `suits/war_machine.md` | War Machine | Pubudu |
| `suits/iron_patriot.md` | Iron Patriot | Pubudu (SQL) |
| `suits/pepper.md` | Pepper | Bridie |
| `suits/veronica.md` | Veronica | Shyam |
| `suits/jarvis_protocol.md` | Jarvis Protocol | Andrew |

### Jarvis Internal (maintenance & ops — not exec-facing)

| File | What it is |
|---|---|
| `jarvis_identity.md` | Identity & relationships |
| `jarvis_characters.md` | Character backstory, error logging, Pride & Dignity protocol |
| `jarvis_health_playbook.md` | How to keep Jarvis accurate |
| `jarvis_update_protocol.md` | How to update the knowledge base |
| `jarvis_action_log.md` | Improvements shipped + backlog |
| `contribution_guidelines.md` | Protected files, edit policies |
| `quality_check_process.md` | Context quality control process |
| `measurement_gap_tracker.md` | Executive measurement gaps tracker |
| `activity_tagging.md` | Activity pulse protocol |
| `mcp_tool_guidelines.md` | Token-efficient MCP usage |
| `pepper_watchlist.yaml` | Live gap registry |
| `pepper_audit_log.jsonl` | Pepper audit trail |

______________________________________________________________________

## Files NOT Managed by Sync (edit directly in this repo)

| File | Why |
|---|---|
| `JARVIS_KNOWLEDGE_BASE_MANIFEST.md` | Jarvis's capability inventory — jarvis-native |
| `domain_context.md` | Auto-generated from `analytics-copilot/domain/index.md`; regenerated via `scripts/build_domain_context.py` |

______________________________________________________________________

## Sync Reference

| Resource | Location |
|---|---|
| Sync script | `analytics-copilot/scripts/sync-jarvis.sh` |
| Sync manifest (authoritative file list) | `analytics-copilot/domain/SYNC_MANIFEST.md` |
| Skill (recommended way to sync) | `/sync-jarvis` in analytics-copilot |
| Weekly context refresh | `/weekly-context-refresh` — updates `business_state.md` then syncs |
| Update protocol | `jarvis_update_protocol.md` (synced from analytics-copilot) |
