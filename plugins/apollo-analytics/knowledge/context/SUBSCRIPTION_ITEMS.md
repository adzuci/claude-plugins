# SUBSCRIPTION_ITEMS

> Stripe subscription items table (external data share). Shows the current line items on each Stripe subscription — what products and plans a team is on right now.

## Overview

| Field | Value |
|---|---|
| **Full path** | `SHARE__XDB23305.STRIPE.SUBSCRIPTION_ITEMS` |
| **Grain** | One row per subscription item (a subscription can have multiple items — one per product line) |
| **Refresh cadence** | Near real-time (Stripe data share) |
| **Trust level** | Use with caution — **current state only**, not historical |
| **Owner** | Stripe (external share) |
| **DAG** | N/A — external Stripe data share |

## Description

Current state of subscription line items in Stripe. Each row represents one product line on a Stripe subscription (seat plan, add-on, etc.). Useful for understanding what a team is currently provisioned on, but cannot be used for historical billing analysis.

**Critical limitation:** `SUBSCRIPTION_ITEMS` reflects the team's current plan. For historical rows (e.g., past invoices), joining `SUBSCRIPTION_ITEMS` on `SUBSCRIPTION_ID` will return the team's current plan, not what they were on at the time of that invoice.

## Upstream Sources

| Source | Relationship |
|---|---|
| Stripe (external) | Direct data share |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| `ID` | TEXT | Subscription item ID | |
| `SUBSCRIPTION_ID` | TEXT | Parent Stripe subscription ID | Join key from bridge tables |
| `PLAN_ID` | TEXT | Stripe plan identifier | Pattern: `{product_id}_{interval}_{version}` e.g. `professional_unified_v3_yearly_1`. Often null on invoice line items — use for provisioned-side lookups only |
| `QUANTITY` | INTEGER | Number of seats or units | |

## How It's Used

### Common query patterns

```sql
-- Current billing cadence for a subscription
SELECT
    subscription_id,
    plan_id,
    case
        when plan_id ilike '%yearly%'  then 'annual'
        when plan_id ilike '%monthly%' then 'monthly'
        else 'unknown'
    end as billing_cadence,
    quantity
FROM share__xdb23305.stripe.subscription_items
WHERE subscription_id = '<subscription_id>'
  AND plan_id NOT ILIKE '%addon%';
```

### Key consumers

- Billing cadence lookup (annual vs. monthly) in invoice queries
- Current subscription state checks

## Known Issues & Gotchas

- **Current state only — not historical.** If you join this to a past invoice using `SUBSCRIPTION_ID`, you get the team's current plan, not what they were on at invoice time. For point-in-time product state, use `FCT_MONGO_TEAM_PLAN_UPDATE_ATTEMPTS.PRODUCT_INFOS_UPDATE` instead.
- **`PLAN_ID` is not always populated** on invoice line items — observed as null in real invoices. Use `PLAN_ID` for subscription-side lookups only; use `description` for invoice line item classification.
- **Filter `NOT ILIKE '%addon%'`** when looking for the primary seat plan — add-on items will otherwise pollute billing cadence lookups.
- **Apollo does not use Stripe's subscription billing amounts** — subscription amounts are structural. Actual charged amounts are on `INVOICES.amount_due`.

## Slack Context

- Primary reference: `domain/stripe_billing_patterns.md` (researched March 2026)

## Business Terms

| Term | Definition |
|---|---|
| `plan_id` | Internal Stripe plan identifier encoding product, billing interval, and version |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-24 | Created context file from stripe_billing_patterns.md research | Andrew (Jarvis) |
