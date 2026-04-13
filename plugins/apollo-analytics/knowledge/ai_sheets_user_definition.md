# AI Sheets User Definition — GTM Engineer Persona

**Purpose:** Define what identifies an "AI Sheets power user" in data. Needed for Q5 (AI adoption) and product bet tracking.

**Audience:** Jarvis, product team, analytics
**Date:** 2026-03-30 (DRAFT — AWAITING PRODUCT DEFINITION)
**Owner:** Adhiraj Yadav (AI product owner), Bridie Meredith (Jarvis context)
**Status:** PENDING — Persona definition in progress (Gap 2)

---

## The Problem

Exec question: "How is AI Sheets adoption among GTM Engineers?"

**Current state:**
- Can measure general AI adoption (AI WAU, AI credit consumption)
- Cannot measure "GTM Engineer adoption" because we haven't defined what identifies a GTM Engineer cohort

**Why it matters:**
- AI Sheets is positioned as "AI Sheets for the GTM Engineer" in the H2 bet narrative
- Without a data definition, can't segment attach rate to the intended buyer
- Can't tell if product is reaching target persona or being used by different buyers

---

## What We Need (Placeholder for Definition)

**Proposed definition approaches** (to be validated by product/Adhiraj):

### Option A: Behavioral (Credits & Feature Use)
```
GTM_Engineer cohort =
  Teams where:
  - AI_credit_consumption_l30 > $X (threshold TBD; possibly 10M+ credits/month)
  - multi_tool_call_rate > Y% (simultaneous AI calls, indicating workflow automation)
  - NOT high_email_volume (unlike traditional AE motion)
  - OR explicitly_flagged_as_agentic_workflow_user
```

**Advantage:** Data-driven, objective
**Disadvantage:** Threshold discovery may take 2-4 weeks

### Option B: Segmentation (Team Characteristics)
```
GTM_Engineer cohort =
  Teams where:
  - account_segment = 'SMB' OR 'Mid-Market' (excludes Enterprise CSM-heavy orgs)
  - team_size 2-20 (RevOps/ops size, not massive AE org)
  - job_titles_in_team contain ('RevOps', 'Operations Manager', 'GTM Manager', 'Business Analyst')
  - OR use_cases include 'workflow_automation' or 'lead_scoring'
```

**Advantage:** Persona clarity; actionable for sales
**Disadvantage:** Requires job title data (may not be available in Snowflake)

### Option C: Feature-Flag (Product-Tagged)
```
GTM_Engineer cohort =
  Teams where:
  - is_ai_sheets_beta_tester = TRUE (product team flags interested cohort)
  - OR has_completed_agentic_workflow_onboarding = TRUE
```

**Advantage:** Direct from product; most accurate
**Disadvantage:** Depends on product team's ability to tag cohort

---

## What "AI Sheets" Means (Context)

**AI Sheets** = Agentic workflow feature (experimental H3 product moving to H2):
- Automated lead scoring, filtering, and qualification
- Multi-step workflows (email → search → enrichment → CRM sync)
- Minimal user intervention; system-driven

**Intended value prop for GTM Engineers:**
- Eliminate manual qualification work
- Scale lead processing to 1000s/day
- Cross-functional (enrichment + email + CRM)

**Target buyer:**
- Individual contributor or team lead (RevOps, Operations Manager)
- 5-20 person organization (all-hands-on-deck)
- Using Apollo as central hub for GTM workflow (not just email or enrichment)

---

## Key Metrics (Once Defined)

| Metric | Target | Notes |
|--------|--------|-------|
| **AI Sheets WAU** | 2K by Q2 (pilot), 10K by Q4 | Weekly active users on AI Sheets features |
| **Attach rate** | 15-20% of paid WAT | % of customers using feature |
| **Cohort M3 NRR** | 95%+ | Retention indicator of value |
| **Credit consumption (per user)** | 50K-200K/month (TBD) | Feature intensity signal |
| **Multi-tool call rate** | >3 tools per workflow (TBD) | Workflow automation depth |

---

## Data Table (Goal)

Once definition is finalized:

```
DIM_GTM_ENGINEER_COHORT:
  - team_id (PK)
  - is_gtm_engineer (flag, TRUE/FALSE)
  - gtm_engineer_definition_version (v1.0, etc.)
  - definition_applied_date
  - confidence_score (0-100, TBD)
  - source (behavioral, segmentation, product_flag, etc.)

Grain: One row per team
Refresh: Weekly
```

**Join to:**
- `TEAM_AI_ASSISTANT_DAILY` (AI feature usage)
- `AGG_TEAM_CREDITS` (AI credit consumption)
- `FCT_DAILY_REVENUE` (retention, ARR)

**View (Goal):**
```sql
V_AI_SHEETS_ADOPTION_GTM_ENGINEER:
  SELECT
    date,
    COUNT(DISTINCT team_id) as gtm_engineer_teams,
    COUNT(DISTINCT CASE WHEN is_ai_sheets_active_l7 THEN team_id END) as active_ai_sheets_teams,
    ROUND(100.0 * active / gtm_engineer_teams, 1) as adoption_rate,
    SUM(ai_credits_l7) as total_credits,
    AVG(ai_credits_l7) as avg_credits_per_team
  FROM joined_tables
  WHERE is_gtm_engineer = TRUE
  GROUP BY date
  ORDER BY date DESC
```

---

## Current Status (2026-03-30)

**What we CAN measure:**
- General AI WAU: ~8K (target 15K)
- General AI credit consumption: ~3M credits/month (target 27M)
- General W4 retention for AI: ~20%

**What we CANNOT measure:**
- GTM Engineer adoption (no persona definition yet)
- Product-specific attach rate
- Agentic workflow penetration

---

## Timeline

| Milestone | Owner | ETA | Status |
|-----------|-------|-----|--------|
| **Persona definition finalized** | Adhiraj + AI PM | Q2 (est. end of May) | In progress |
| **Data definition validated** | Bridie (Analytics) | Q2 (est. early June) | Pending product decision |
| **DIM_GTM_ENGINEER_COHORT built** | DE + Analytics | Q2 (est. mid-June) | Pending #1, #2 |
| **Jarvis queries enabled** | Jarvis team | Q2 (est. end of June) | Pending #3 |

**Risk:** If persona definition delays past Q2, GTM Engineer targeting may need to slip to Q3.

---

## How Jarvis Uses This

**Current (before definition):**
> "AI Sheets adoption data isn't yet separated in our warehouse. I can show you overall AI WAU (15K target, current 8K) and credit consumption (27M target, current 3M), but I can't segment to 'GTM Engineer adoption' because the team is still finalizing what identifies an AI Sheets power user. Adhiraj is working on this definition — should be locked by end of Q2."

**Future (after definition):**
> "GTM Engineer AI Sheets adoption: 2K active teams (target 2K at Q2 pilot, 10K at Q4). Attach rate is 18% of SMB/MM paid WAT using the feature. Cohort M3 NRR: 96% (healthy retention). Current trajectory is on track to hit H2 bet graduation criteria."

---

## Related Files

- `pending_definitions.md` — Gap 2 (full context)
- `product_portfolio_taxonomy.md` — AI Sheets as H2 bet
- `annual_targets.md` — AI WAU and credit targets
- `business_state.md` — Current AI momentum
