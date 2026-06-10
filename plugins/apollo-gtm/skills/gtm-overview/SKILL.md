---
name: gtm-overview
description: Go-to-market motion overview — segments, channels, and launch process. Use when the user asks about Apollo GTM strategy, target customer segments, how to plan a product launch, who owns a GTM metric, or wants to understand PLG vs rep-driven motions.
disable-model-invocation: true
---

# Go-To-Market Overview

Use this skill when someone asks about Apollo's GTM strategy, target segments, launch process, or GTM metrics.

## Target Segments

| Segment | ICP | Primary Channel | Key metric |
|---------|-----|-----------------|------------|
| Enterprise (ENT) | Large orgs, 50+ seats, complex needs | AE-led, rep-driven | ACV $9K → $11K |
| Mid-Market (MM) | 10-49 seats, multi-department | Rep-driven + PLG assist | MM+ENT logos 680 |
| SMB | 3-9 seats, sales-led teams | PLG with rep overlay | VSB+SMB NRR +10pts |
| VSB | 1-2 seats, individual contributors | Pure self-serve / PLG | W2 FTP 4.0% → 4.5% |

**Segment source:** `ANALYTICS_DB.PLAYGROUND.LU_TEAM_ATTRIBUTES.segment` — always join here for segmentation, never compute from ARR ranges.

## GTM Motions

| Motion | What | Owner | Target |
|--------|------|-------|--------|
| Self-Serve / PLG | Free → Paid via product | Dan Cronyn | FTP 4.5%, F14D activation 17% |
| Rep-Driven | AE-led Custom/Org expansion | Adam Carr | $41M new ARR |
| GTME / Expansion | Retention, upsell, save motions | Eric Quanstrom | GRR > 70%, expansion $12.5M |
| Partnerships | Partner-sourced revenue | Jennifer Rhima | $7.2M ARR (→ $30M FY28) |

## Channels & Programs

| Channel | Owner | Focus |
|---------|-------|-------|
| Inbound (website visitors) | Growth team | $6.4M ARR target (H2 product) |
| Outbound sequences | Sales | Rep productivity, sequences + dialer |
| Lifecycle / nurture | Growth team | PQL/PQA pipeline, activation signals |
| Partnerships | Jennifer Rhima | API resellers, international, strategic alliances |
| Marketing (brand + demand) | Marcio Arnecke | MQLs, Stage 1 Opps, brand awareness |

## Launch Process

1. **Intake**: Define the feature/product, target segment, and success metrics. Identify which GTM motion it supports (PLG vs rep-driven).
1. **Cross-functional alignment**: Coordinate with Product (spec), Marketing (positioning), Sales (enablement), Support (docs), and Analytics (measurement).
1. **Pre-launch**: Enable sales team, prepare support docs, set up tracking in Snowflake/Amplitude, define experiment plan if applicable.
1. **Launch**: Execute across channels. Monitor initial adoption via `FCT_TEAM_FEATURE_USERS_DAILY`.
1. **Post-launch**: Measure against success metrics at 7d, 30d, and 90d. Report adoption + retention (not just adoption alone).

## Key Metrics

| Metric | Definition | Where it lives |
|--------|-----------|----------------|
| W2 FTP | Week-2 Free-to-Paid conversion | Growth dashboards |
| F14D Activation | First 14-day activation rate | Amplitude (not yet in Snowflake) |
| PQL/PQA | Product Qualified Lead/Account | Scoring model (not yet built) |
| GRR | Gross Revenue Retention | `FCT_MONTHLY_REVENUE` |
| NRR | Net Revenue Retention (M3 Cohort: 62-78%) | Partially in Snowflake |
| WAT | Weekly Active Teams (paid ~69K, total ~362K) | `DIM_TEAMS_DAILY` |
| Active days | Strongest retention predictor (26+ days = 76% retention) | `FCT_TEAM_FEATURE_USERS_DAILY` |

## Output Format

When someone asks about GTM strategy, present:

> **Motion:** [Self-Serve / Rep-Driven / GTME / Partnerships]
> **Target segment:** [ENT / MM / SMB / VSB]
> **Owner:** [name and function]
> **Key metrics:** [relevant KPIs and current targets]
> **Slack:** [relevant channel]

## Gotchas

- "Paid teams" = ARR > 0 (~106K). Total teams = ~3.5M. Always clarify which.
- "NRR" at Apollo = M3 Cohort NRR (62-78%), NOT aggregate net retention (~96%). Big difference.
- Segments come from SFDC via `LU_TEAM_ATTRIBUTES`, not from ARR thresholds.
- Partnerships has zero analytics infrastructure currently — $7.2M target with no measurement.
