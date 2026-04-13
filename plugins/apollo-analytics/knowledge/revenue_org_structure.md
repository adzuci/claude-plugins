# Revenue Org Structure & How to Debrief Revenue

**Owner:** Leo | **Updated:** 2026-03-20 | **Source:** RBR #71 + Snowflake validation

---

## The Two Motions

Revenue is tracked in two separate motions. Every metric, table, and report maps to one of these.

### 1. Self-Serve Motion
Everything driven through the product funnel — signups, free-to-paid conversion, lifecycle campaigns.

**North Star metrics:**
- Total Team Registrations
- Total New Self-Serve ARR
- New Paid SS Teams
- New SS ARPT (ARR per paid team — the ACV equivalent for self-serve)
- Inbound S1 Opps (New Biz + Upsell from PLG leads)

**Sub-functions & owners:**
| Function | Owner | What they track |
|----------|-------|----------------|
| Paid Acquisition | Cam Thompson | Ad spend, ROAS, LTV/CAC ratio |
| SEO / AEO | Kelechi Ibe | Organic traffic, non-brand rankings, LLM citations |
| CRO | Nick Gallinelli | Site visit → reg CVR, demo page conversion |
| Free-to-Paid Conversion | Dan Cronyn | FTP cohort table by week and channel |
| Growth Experimentation | Matt Woods | Feature gates, influenced ARR |
| Lifecycle SS F2P | Ben Frutos | MJ email campaigns, PLSM, abandoned pricing page re-engagement |
| Digital Success / VSB Retention | Robert Statsky | VSB + SMB+ NRR cohorts, lifecycle campaigns for retention |
| Pricing & Packaging | Karthik Mahadevan | ARPU, packaging experiments, plan page CVR |
| Growth Expansion | Sourabh Ahuja | SS upsell ARR rate |

**Data sources:**
- `FCT_MONTHLY_REVENUE` — `ARR_SS > 0` for self-serve ARR, `IS_PARENT_ACCOUNT = false` for team level
- `DIM_SALESFORCE_CONTACTS` — signup volume, UTM channel attribution
- `DIM_SALESFORCE_OPPORTUNITIES` — `LEAD_SOURCE_BUCKET = 'System'` for PLG-sourced opps
- `ONBOARDING_HIGH_VELOCITY_TEAMS` — HVO onboarding funnel

---

### 2. Rep-Driven Motion
Everything sold by AEs, AMs, BDRs, Customer Advocates, and GTME.

**Sub-functions & owners:**
| Function | Owner | What they track |
|----------|-------|----------------|
| SMB AE (new logo) | Dana Hensler | S1→S2 CVR, PG$, ACV, outbound volume |
| SMB AM (expansion) | Dana Hensler / Ashley Clough | Upsell ARR, add-on attach rate, OB ACV |
| MM AE | Garris Yeung | S1→S2 CVR, PG$, ACV by channel |
| MM AM | Garris Yeung / Tina Zhang | Expansion ARR, upsell ACV |
| Customer Advocate (CA) | Clark Sun / Paula Urrutia | Chat → S1 → Won conversion, won ARR |
| GTME / Renewals | Tina Zhang | Org plan renewal net book %, next-quarter forecast |
| Rep Demand Gen | Kenny Lee | MQL volume by segment (SMB/MM/ENT) |
| Sales Hiring | Sabrina Silva | Headcount vs FY27 target |

**Data sources:**
- `DIM_SALESFORCE_OPPORTUNITIES` — S1→S2 CVR, PG$, ACV by channel and segment
- `FCT_MONTHLY_REVENUE` — `ARR_REP > 0` for rep-driven ARR; `IS_PARENT_ACCOUNT = true` for exec waterfall
- `DIM_SALESFORCE_ACCOUNTS.ACCOUNT_SALES_DEPARTMENT_TIER` — rep-driven segment (Tier1/2 = MM, Tier3/4 = SMB)

---

## How to Read the NNARR Waterfall by Motion

`FCT_MONTHLY_REVENUE` has 4 ARR motion columns:
- `ARR_SS` — self-serve
- `ARR_REP` — rep-driven
- `ARR_SA` — sales assist
- `arr_labs` — labs (lowercase, small)

Apply `IS_PARENT_ACCOUNT = true` for exec-level waterfall (parent account rollup, RevOps cut).
Apply `IS_PARENT_ACCOUNT = false` for team-level analysis (ACV, new team count).

**Standard waterfall split:**
```sql
SELECT
    DATE_TRUNC('month', mr.DATE_PERIOD)                                    AS month,
    SUM(CASE WHEN mr.CHANGE_CATEGORY = 'new'
             AND mr.IS_PARENT_ACCOUNT THEN mr.ARR_SS  ELSE 0 END)          AS ss_new,
    SUM(CASE WHEN mr.CHANGE_CATEGORY IN ('upgrade','new_reactivated')
             AND mr.IS_PARENT_ACCOUNT THEN mr.ARR_SS  ELSE 0 END)          AS ss_expansion,
    SUM(CASE WHEN mr.CHANGE_CATEGORY = 'new'
             AND mr.IS_PARENT_ACCOUNT THEN mr.ARR_REP ELSE 0 END)          AS rep_new,
    SUM(CASE WHEN mr.CHANGE_CATEGORY IN ('upgrade','new_reactivated')
             AND mr.IS_PARENT_ACCOUNT THEN mr.ARR_REP ELSE 0 END)          AS rep_expansion,
    SUM(CASE WHEN mr.CHANGE_CATEGORY = 'churn'
             AND mr.IS_PARENT_ACCOUNT THEN mr.ARR_CHANGE ELSE 0 END)       AS churn,
    SUM(CASE WHEN mr.CHANGE_CATEGORY = 'downgrade'
             AND mr.IS_PARENT_ACCOUNT THEN mr.ARR_CHANGE ELSE 0 END)       AS downgrade,
    SUM(CASE WHEN mr.IS_PARENT_ACCOUNT THEN mr.ARR_CHANGE ELSE 0 END)      AS net_new_arr
FROM ANALYTICS_DB.ANALYTICS.FCT_MONTHLY_REVENUE mr
LEFT JOIN ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_APOLLO_TEAMS sat
  ON mr.SFDC_TEAM_OR_ACCOUNT_ID = sat.SFDC_TEAM_ID
LEFT JOIN ANALYTICS_DB.ANALYTICS.DIM_SALESFORCE_ACCOUNTS sa
  ON COALESCE(sat.SFDC_ACCOUNT_ID, mr.SFDC_TEAM_OR_ACCOUNT_ID) = sa.ID
WHERE mr.DATE_PERIOD >= DATEADD('month', -6, DATE_TRUNC('month', CURRENT_DATE))
  AND mr.DATE_PERIOD <  DATE_TRUNC('month', CURRENT_DATE)
  AND (NOT sat.IS_SUSPICIOUS_TEAM OR sat.IS_SUSPICIOUS_TEAM IS NULL)
  AND sa.ACCOUNT_SEGMENT IN ('Enterprise', 'Mid-Market', 'SMB', 'VSB')
  AND (NOT sa.HAS_SUSPICIOUS_TEAM OR sa.HAS_SUSPICIOUS_TEAM IS NULL)
GROUP BY 1 ORDER BY 1 DESC;
```

---

## How to Do a Full Revenue Debrief

Pull data from Snowflake across all four lenses. Interpret the numbers — don't copy from any doc. If a doc quotes a number, validate it against Snowflake first.

### 1. Self-Serve
- SS New ARR trend + ARPT (ACV per team) — is volume growing? Is deal size holding?
- FTP cohort — are new signups converting at goal rate by week?
- Channel split (Organic vs Paid) — which acquisition channel is driving growth?

### 2. Rep-Driven
- Closed won by segment × motion (SMB/MM × New Business/Upsell) — which segment/motion is performing?
- ACV trend per segment — are reps closing at the right deal size?
- S1→S2 CVR by channel (LEAD_SOURCE_BUCKET, excl. System) — where is pipeline converting well/poorly?
- PG$ (pipeline generated) — is the top of funnel sufficient for next quarter?

### 3. Retention / Churn
- Churn ARR by segment — VSB dominates in volume; MM/ENT matter in ARR per account
- Downgrade ARR by segment — often a leading indicator before churn
- NRR cohort (12M) — see `domain/sql_patterns.md` for cohort methodology

### 4. Signal to Surface Per Function
| Finding | Relevant function |
|---------|------------------|
| SS ARPT compressing | Growth — Pricing & Packaging (Karthik), Growth Expansion (Sourabh) |
| FTP rate declining | Growth — Lifecycle/F2P (Ben Frutos), Feature Gates (Matt Woods) |
| Demo Request CVR falling | Marketing — Demand Gen (Kenny Lee), CRO (Nick Gallinelli) |
| SMB AE ACV below target | Sales — SMB AE (Dana Hensler) |
| MM Marketing ACV low | Sales — MM funnel (Garris/Tina), Rep Demand Gen (Kenny Lee) |
| VSB churn accelerating | Retention — Digital Success (Robert Statsky), VSB deflection project |
| MM/ENT churn improving | Retention — GTME (Tina Zhang) |
| Outbound BDR volume low | Sales — BDR (hiring/Sabrina Silva), Enablement (Kenny Keesee) |

---

## Key People — Revenue Org

| Name | Role |
|------|------|
| Clark Sun | RevOps lead, RBR owner |
| Max Angell | VP Sales |
| Howie Chan | Sales analytics / finance |
| Dana Hensler | SMB Sales leader (AE + AM) |
| Ashley Clough | SMB AE/AM ops |
| Garris Yeung | MM Sales leader |
| Tina Zhang | MM / GTME analytics + renewals |
| Paula Urrutia | CA / SMB operations |
| Dan Cronyn | Self-Serve / Growth lead |
| Alex Beckham | Growth marketing (Paid, Dialer monetization) |
| Cam Thompson | Paid Acquisition |
| Kelechi Ibe | SEO / AEO |
| Nick Gallinelli | CRO |
| Ben Frutos | Lifecycle / FTP |
| Karthik Mahadevan | Pricing & Packaging |
| Robert Statsky | Digital Success / VSB retention |
| Sourabh Ahuja | Growth Expansion |
| Sabrina Silva | Sales hiring |
| Kenny Lee | Rep Demand Gen |
| Kenny Keesee | Sales Enablement |

---

## VSB Deflection Project
Active initiative to route VSB accounts away from SMB AEs → raises rep ACV. April 2026 cutover to SMB+ definition (paying customers, <10K employees). Channel: `#fy27-vsb-deflection`. Owner: Clark Sun.

## Change Log
| Date | Change | Author |
|------|--------|--------|
| 2026-03-20 | Created from RBR #71 context + Snowflake validation session | Leo |
