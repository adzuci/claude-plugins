---
name: product-overview
description: Product team overview — roadmap process, prioritization, and how to work with product. Use when the user asks about product roadmap, how to submit a feature request, who owns a product area, Apollo's Horizon model, or how product prioritization works.
---

# Product Overview

Use this skill when someone asks about how the product team works, how to submit a feature request, who owns a product area, or how priorities are decided.

## Roadmap Process

- **Planning cadence**: Quarterly, aligned with the FY27 AOP (Annual Operating Plan). Each quarter maps to ARR ramp targets.
- **Roadmap tool**: Jira for tracking epics and stories. Notion for strategy docs and PRDs.
- **How to submit a request**: Open a Jira ticket in the relevant product area project, or post in `#product-feedback` with context on the use case, expected impact, and target segment.

## Prioritization Framework

Apollo prioritizes based on business impact, measured primarily through NRR contribution:

| Signal | Weight | How it's measured |
|--------|--------|-------------------|
| NRR impact | Highest | Does this reduce churn, increase expansion, or improve activation? |
| Adoption breadth | High | Use cases / WAT (target: 1.18 → 1.33) |
| Retention signal | High | Active days / month (26+ days = 76% retention) |
| Segment alignment | Medium | Which segment benefits? H1 core (VSB+SMB+MM+ENT) gets priority. |
| Revenue attribution | Medium | Can we tie this to ARR? (Credit-to-revenue translation is unsolved.) |

**Who decides**: CPO (Bela Stepanova) sets strategic direction. PMs own prioritization within their area. Quarterly reviews with exec team.

**Review cadence**: Quarterly planning + monthly business reviews. H2 products face revenue gates — ship ARR or get cut.

## Working with Product

| Need | Process |
|------|---------|
| Feature request | Open Jira ticket or post in `#product-feedback` with use case, impact, and segment |
| Bug escalation | File Jira bug with reproduction steps. Critical bugs (revenue-impacting) tag PM + eng lead directly. |
| Spec review | PMs share PRDs in Notion. Engineers review async, then sync in spec review meetings. |
| Product analytics | Work with Kirk Hlavka (frameworks), Sai Sarvepalli (AI), or Adhiraj Yadav (churn) depending on area. |

## Key Contacts

| Area | PM / Owner | Slack |
|------|-----------|-------|
| Overall strategy | Bela Stepanova (CPO) | `#product` |
| Onboarding / activation | James Boone | `#onboarding` |
| Growth / conversion | Dan Cronyn | `#growth` |
| Self-serve analytics | Nipun Jami | `#product` |
| Product feedback | — | `#product-feedback` |

## Horizon Quick Reference

| Horizon | Products | Status |
|---------|----------|--------|
| **H1 — Core** | Sequences, email, enrichment, CRM sync, core search | Optimize — NRR is north star |
| **H2 — Proving** | Inbound ($6.4M), Parallel Dialer ($4.1M), CI ($2.4M), AI Sheets | Validate — must show revenue |
| **H3 — Future** | Agentic platform, unified account intelligence | Explore — must not slow H1/H2 |

## Gotchas

- H2 products have hard revenue gates — if they don't generate ARR, they get deprioritized
- "Active days" is the strongest retention predictor, not credit utilization — frame adoption metrics accordingly
- Multi-product attach rates can't be reliably measured yet (no trusted cross-feature table)
- F14D activation rate is only in Amplitude, not Snowflake — can't query it via the analytics copilot
