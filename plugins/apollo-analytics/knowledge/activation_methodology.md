# F14D Habit RA Rate — Methodology & OKR

**Purpose:** Document exactly what F14D Habit RA Rate measures, why it's the OKR, and how it drives NRR.

**Audience:** Jarvis, analytics team, product leadership
**Date:** 2026-03-30
**Owner:** Adhiraj Yadav (metric owner), Bridie Meredith (Jarvis context)
**Status:** Measured in Amplitude/Hex; Snowflake version in progress (Gap 7)

______________________________________________________________________

## The Metric

**F14D Habit RA Rate** = % of new teams that complete 4+ Record Actions within 14 days of signup (activation date).

### Formal Definition

```
F14D_HABIT_RA_RATE =
  COUNT(teams with record_actions_in_f14d >= 4) / COUNT(total_teams_activated)
  WHERE team_created_date is within measurement window
  AND account_segment in ('SMB', 'Mid-Market', 'Enterprise') [Golden Pop only]
  AND organization_country NOT IN ('India', 'UAE')
  AND is_free_email_domain = FALSE
```

**Grain:** Team level; counted once per team in their first 14 days.

**Lookback:** Measured rolling; e.g., "What % of teams activated in past 7 days hit 4+ RAs?"

**Current baseline (FY26):** ~12%
**FY27 target:** 17% (+5 percentage points)

______________________________________________________________________

## What is a Record Action (RA)?

A Record Action is a user interaction with an Apollo-tracked contact or account. **14 qualifying actions** (canonical list):

1. **Email outreach** — Sent prospecting email (Outreach)
1. **Email manual** — Sent manual email (not sequence)
1. **Email extension** — Used email extension
1. **Win/Close** — Logged deal (Win/Close feature)
1. **API enrichment** — Enriched contact via API
1. **CRM enrichment** — Enriched via CRM integration
1. **CSV enrichment** — Enriched via bulk upload
1. **Waterfall enrichment** — Enrichment pipeline step completed
1. **GenPipe Traditional** — Generated leads manually
1. **GenPipe NextGen** — Generated leads via AI
1. **Meeting Assistant** — Meeting scheduled/recorded
1. **Scheduler** — Used meeting scheduling
1. **Notes** — Added notes to contact/account
1. **CRM record mgmt** — Modified CRM record

**NOT counted:** Login (friction signal, not value), viewing results (passive), settings changes.

______________________________________________________________________

## Why 4 RAs in 14 Days?

**Empirical basis:**

- Analysis of FY26 cohorts shows teams reaching 4+ RAs by Day 14 have 78% M3 retention vs. 32% for teams with \<4 RAs.
- Threshold of 4 is strategic sweet spot: high enough to signal intent (not random clicks), low enough to be achievable in onboarding window.
- 14-day window aligns with trial period (critical onboarding window before purchase decision).

**What it signals:**

- **Habit formation initiation:** User is repeating actions, not one-time trial
- **Product value discovery:** User found a use case and exercised it
- **Organizational buy-in:** Likely >1 user engaged (vs. solo trial user)
- **Retention predictor:** Exponential lift in M3 retention vs. non-activators

**Why it's the #1 OKR for growth:**

- Early signal: Activation is measurable by Day 14 (vs. NRR lag of 90 days)
- Causality: Activation drives habit → retention; not just correlation
- Actionable: FUX improvements, onboarding timing, value messaging all move this metric
- Balanced scorecard: Tracks customer success (activation) not just sales (ARR)

______________________________________________________________________

## Measurement Window (Golden Population Only)

**Why Golden Pop?** [Per glossary_entries.md]

- **Segments:** SMB + Mid-Market + Enterprise only (excludes VSB)
- **Regions:** AMER + EMEA (excludes APAC, India, UAE due to regulatory/data quality)
- **Domain:** Not free-email (@gmail.com, @hotmail.com, etc.) — signal of company legitimacy

**Why this restriction?**

- VSB teams have \<20 employees; lower attachment potential; different product fit
- APAC/India have data quality issues (enrichment accuracy, email deliverability)
- Freemail teams are often personal side projects (not evaluating for company use)
- **Net effect:** Measurement population is ~60% of all signups (high-intent, high-retention cohort)

**Caveat for Jarvis:** When exec asks "What's our activation rate?" Jarvis must clarify: "This is Golden Pop activation (17% target). Overall activation including all segments/regions is lower (~10%). We focus on Golden Pop because that's where we expect the NRR improvement."

______________________________________________________________________

## Current Status (as of 2026-03-27)

**FY26 Baseline:** 12.1% (measured in Amplitude)
**Q1 2026 Current:** 11.0% (flat to slightly down)

**Why it's not moving:**

1. **Onboarding friction:** New teams hitting 4 RAs by Day 14 requires successful first-run experience
1. **Value clarity:** If product value isn't obvious in first 14 days, no RAs happen
1. **Competing priorities:** Large accounts may delay onboarding; smaller accounts may drop if value unclear

**What we're trying:**

- **FUX redesign (mid-April):** Simplified onboarding; 5-step → 2-step flow → earlier value delivery
- **Success criteria:** 2-3pp lift (13-14%) within 2 weeks post-launch
- **If flat:** Suggests value problem, not UX problem

______________________________________________________________________

## How Snowflake Version Will Work (Gap 7)

Once Adhiraj builds `DIM_ACTIVATION` table:

```sql
SELECT
  TRUNC(t.TEAM_CREATED_DATE, 'DAY') as signup_date,
  COUNT(DISTINCT t.TEAM_ID) as teams_activated,
  COUNT(DISTINCT CASE WHEN a.record_actions_in_f14d >= 4 THEN a.TEAM_ID END) as teams_activated_f14d,
  ROUND(100.0 * COUNT(DISTINCT CASE WHEN a.record_actions_in_f14d >= 4 THEN a.TEAM_ID END)
    / COUNT(DISTINCT t.TEAM_ID), 1) as f14d_rate
FROM ANALYTICS_DB.ANALYTICS.DIM_MONGO_TEAMS t
LEFT JOIN ANALYTICS_DB.ANALYTICS.DIM_ACTIVATION a
  ON t.TEAM_ID = a.TEAM_ID
WHERE YEAR(t.TEAM_CREATED_DATE) = YEAR(CURRENT_DATE())
  AND s.ACCOUNT_SEGMENT IN ('SMB', 'Mid-Market', 'Enterprise')
  AND s.ACCOUNT_REGION IN ('AMER', 'EMEA')
  AND t.IS_FREE_EMAIL_DOMAIN_IND = 0
GROUP BY TRUNC(t.TEAM_CREATED_DATE, 'DAY')
ORDER BY signup_date DESC;
```

**Table:** `DIM_ACTIVATION`
**Grain:** One row per team
**Columns:** team_id, signup_date, record_actions_in_f14d, is_activated_flag, segment, region, is_golden_pop
**Refresh:** Daily
**ETA:** Mid-April 2026

______________________________________________________________________

## Targets & Milestones

| Period | Target | Variance | Notes |
|--------|--------|----------|-------|
| **FY26 (baseline)** | 12% | — | Locked; historical reference |
| **Q1 2026** | 13.5% | -1.5pp (gap) | FUX redesign launching mid-April |
| **Q2 2026** | 15% | -2pp (path dependent) | Results of FUX dependent; if flat, escalate to product |
| **Q3 2026** | 16% | -1pp | Assumes FUX works + DCS programs compound |
| **Q4 2026 (FY27 end)** | 17% | On target | Net +5pp improvement |

**Escalation threshold:** If Q2 activation < 14% after FUX redesign, recommend product team deep-dive into early churn (are teams discovering value?)

______________________________________________________________________

## How Jarvis Uses This

When exec asks: "How are we doing on activation?"

**Jarvis response:**

> "F14D Habit RA Rate is currently **11%** (target: 17%). That's 6 points behind where we need to be. This is the #1 leading indicator for whether our NRR +10pt improvement plan is working. The team is launching onboarding redesign in mid-April that should move this 2-3 points. Until we see that lift (or failure), we won't know if the value problem is UX friction or product quality. Current status: **at risk** unless FUX redesign delivers."

______________________________________________________________________

## See Also

- `theory_of_change.md` — Why activation matters in the causal chain
- `business_state.md` — Current FUX redesign timeline
- `pending_definitions.md` — Gap 7 (Snowflake version in progress)
- `data-catalog/glossary_entries.md` — Golden Population definition
