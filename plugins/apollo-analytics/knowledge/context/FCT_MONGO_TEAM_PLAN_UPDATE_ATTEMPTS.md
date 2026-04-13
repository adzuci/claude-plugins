# FCT_MONGO_TEAM_PLAN_UPDATE_ATTEMPTS

> Every billing event at Apollo — plan changes, upgrades, new customers. The primary bridge between Apollo teams and Stripe invoices.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_TEAM_PLAN_UPDATE_ATTEMPTS` |
| **Grain** | One row per billing attempt (a single billing event may produce 2–4 failed attempts + 1 successful one) |
| **Row count** | Large (millions of rows across all billing history) |
| **Refresh cadence** | Near real-time (Mongo CDC) |
| **Trust level** | Authoritative — primary source for Flow 1 (plan change) billing events |
| **Owner** | Data Platform / Billing |
| **DAG** | <!-- TODO: verify DAG name --> |

## Description

Mirrors the MongoDB `TeamPlanUpdateAttempt` model. Every time Apollo bills a customer for a plan change, upgrade, new seat, or add-on, a `TeamPlanUpdateAttempt` row is created. A single logical billing event often produces multiple attempt rows (failed payment retries) — only the row with `COMPLETED_AT IS NOT NULL` represents the successful charge.

This is the **Flow 1 bridge table**: it links Apollo `TEAM_ID` to `STRIPE_INVOICE_ID`, making it the canonical join point for plan change / upgrade invoices. Renewal invoices (Flow 2) do NOT appear here — see `FCT_MONGO_STRIPE_WEBHOOK_EVENTS`.

## Upstream Sources

| Source | Relationship |
|---|---|
| MongoDB `TeamPlanUpdateAttempt` collection | 1:1 via CDC |
| `share__xdb23305.stripe.invoices` | Join on `STRIPE_INVOICE_ID = INVOICES.id` |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| `TEAM_ID` | TEXT | Apollo team ID | Primary join key to DIM_MONGO_TEAMS |
| `STRIPE_INVOICE_ID` | TEXT | Stripe invoice ID for this attempt | May be null on failed/draft attempts; join to `INVOICES.id` |
| `STRIPE_SUBSCRIPTION_ID` | TEXT | Stripe subscription ID | Use to correlate with SUBSCRIPTION_ITEMS and change events |
| `STRIPE_CHARGE_ID` | TEXT | Stripe charge ID | |
| `COMPLETED_AT` | TIMESTAMP | Timestamp of successful completion | NULL on failed/pending attempts. Filter `COMPLETED_AT IS NOT NULL` for real charges. **Not a boolean column** — there is no `COMPLETED` flag |
| `ARR_DELTA` | NUMBER | Change in ARR from this billing event (USD) | Apollo's net figure including all discounts; most reliable ARR signal per event |
| `PRODUCT_INFOS_UPDATE` | VARIANT | JSON array of full provisioned product state after this event | More reliable than SUBSCRIPTION_ITEMS (current state only) for point-in-time product state |

## How It's Used

### Common query patterns

```sql
-- All completed plan-change invoices for a team (Flow 1)
SELECT
    a.completed_at           AS event_date,
    a.stripe_invoice_id      AS invoice_id,
    i.amount_due / 100.0     AS amount_usd,
    i.billing_reason,
    a.arr_delta
FROM analytics_db.analytics_dataplatform.fct_mongo_team_plan_update_attempts a
JOIN share__xdb23305.stripe.invoices i ON i.id = a.stripe_invoice_id
WHERE a.team_id = '<team_id>'
  AND a.completed_at IS NOT NULL
  AND a.stripe_invoice_id IS NOT NULL
  AND i.status = 'paid'
ORDER BY a.completed_at DESC;
```

### Key consumers

- Stripe billing recon (Flow 1 invoices)
- ARR delta tracking and waterfall analysis
- Three-way recon (contracted vs. provisioned vs. invoiced)
- `domain/stripe_billing_patterns.md` — canonical reference for all billing analysis

## Known Issues & Gotchas

- **Multi-attempt retry pattern:** A single billing event commonly produces 2–4 rows (failed retries + 1 success). Always filter `COMPLETED_AT IS NOT NULL` — never `completed = true` (that column does not exist).
- **Voided invoice rows:** Rows with `COMPLETED_AT IS NULL` but non-null `STRIPE_INVOICE_ID` indicate failed attempts with a voided invoice in Stripe. Do not count these as real charges.
- **Flow 1 only:** Renewal invoices never appear here. Use `FCT_MONGO_STRIPE_WEBHOOK_EVENTS` for renewals (Flow 2).
- **`ARR_DELTA` vs. `MRR_CHANGE × 12`:** `ARR_DELTA` is net of all discounts (authoritative). Stripe's `SUBSCRIPTION_ITEM_CHANGE_EVENTS.MRR_CHANGE × 12` is list price only — they will differ for discounted customers.
- **`PRODUCT_INFOS_UPDATE` embedded credits:** Fields like embedded credit limits are often null even when credits are provisioned. Use `AGG_TEAM_CREDITS` for credit verification.

## Slack Context

- Primary reference: `domain/stripe_billing_patterns.md` (researched March 2026)

## Business Terms

| Term | Definition |
|---|---|
| Flow 1 | Plan change / upgrade billing path — runs through this table |
| ARR Delta | Net change in annualized recurring revenue from a single billing event, after all discounts |
| `PRODUCT_INFOS_UPDATE` | Point-in-time JSON snapshot of provisioned products after the billing event |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-24 | Created context file from stripe_billing_patterns.md research | Andrew (Jarvis) |
