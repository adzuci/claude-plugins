# Credit Utilization & Retention — Data Sparring Findings

Source: Data Sparring session (2026-03-06). Presented by Andrew Green.

## Key Finding: Daily Habit Drives Retention, Not Credit Utilization

The single strongest retention signal is **active days per month**, not total credit usage or utilization rate.

| Active Days (credits used) | Retention Rate |
|---|---|
| 1-5 days | < 40% |
| 6-15 days | ~50-60% |
| 26+ days | **76%** |

This holds regardless of how many credits teams use in total. A team that uses 10 credits/day for 26 days retains better than a team that burns 1,000 credits in a single day.

## Utilization Volatility: No Significant Impact

Andrew analyzed coefficient of variation in credit usage across months (15K teams, 2+ months of data). Finding: **volatility does not meaningfully impact churn**. Retention increases slightly with volatility but the difference between groups is not significant. Utilization slope (credit usage trend over 3+ months) decreases similarly for both churned and non-churned teams.

## Feature Usage and Retention

Teams using multiple features retain better. Key features analyzed:
- **Direct dial** — steepest usage decline recently
- **Searcher emails** — high-usage feature, correlated with retention
- **Power-ups** — usage increased significantly since Dec-Jan 2025 (affects analyses of teams paying since Sept)
- Teams could be using additional features beyond the five analyzed

## Pricing & Monetization Insights

### Price-insensitive segment (5-10% of paying customers)
- High-intent teams that frequently hit credit limits are likely less price-sensitive
- Hypothesis: a higher price point on basic monthly plan could improve professional plan take rates
- Testing needed to understand elasticity — estimated impact in "tens of dollars" per customer
- Previous seat discount experiments (by Sarab) lifted retention ~9-10% but were uneconomical due to unit economics

### One-time / non-subscription idea
- Pubudu raised the idea of a separate non-subscription product for customers with narrow, specific needs
- Andrew noted it's a valuable thought exercise but operationally challenging

## Self-Serve Team Profile

- **94% of new self-serve teams start with 1 seat**
- Basic annual plan: $49/seat (simple per-seat model)
- VSB and non-core segments expected to have lower utilization due to narrower use cases
- Organizational maturity affects resource deployment and utilization patterns

## Proposed Experiments

### 1. Soft-cap daily credit limit
Encourage daily engagement by distributing credits across days rather than allowing bulk consumption. Inspired by Duolingo's streak system and Claude's daily usage cap model.

- **Mechanism:** Daily credit allocation or soft gate — users get a daily budget, can still use more but with friction (e.g., "You've used your daily credits, come back tomorrow" or reduced speed)
- **Goal:** Increase active days per month, which is the primary retention driver
- **Bridie's suggestion:** Soft-gating (like Claude's approach) rather than hard limits — maintain access but create natural daily engagement rhythm
- **Owner:** Karthik to explore feasibility and A/B test setup

### 2. Higher price point for basic monthly plan
- Test a price increase targeting high-intent, price-insensitive customers
- Measure impact on FTP (free-to-paid) conversion and professional plan upgrade rates

## Next Steps

- **Karthik:** Set up experimentation infrastructure for soft-gating / daily limits
- **Andrew:** Clean up utilization volatility slides for growth team (clarify labels, move detail to appendix)
- **Sai:** Present AI tool latency findings next session
- **Future sessions:** Presenters bring questions from early analysis stages (Marie's suggestion)

## Relevance to Our Work

This analysis directly relates to the **GOLD_TEAM_CREDITS** table (PR #2672) and credit pipeline work:
- `credits_used_by_feature` VARIANT field enables the multi-feature retention analysis
- Active days analysis would need a new metric: count of distinct days with credits_used > 0 per team per month
- Daily soft-cap implementation would need credit usage tracking at the daily grain — our (ds, team_id) grain in GOLD_TEAM_CREDITS supports this
- Utilization rate = credits_used / credit_limit — directly computable from GOLD_TEAM_CREDITS
