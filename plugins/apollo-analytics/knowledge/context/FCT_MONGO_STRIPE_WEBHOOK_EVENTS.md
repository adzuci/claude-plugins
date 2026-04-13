# FCT_MONGO_STRIPE_WEBHOOK_EVENTS

> Stripe webhook event log — the bridge table for Flow 2 (renewal) billing. Captures the void→clone invoice pattern Apollo uses for subscription renewals.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.FCT_MONGO_STRIPE_WEBHOOK_EVENTS` |
| **Grain** | One row per Stripe webhook event |
| **Row count** | Large (millions; ~1.3M renewal pairs confirmed as of March 2026) |
| **Refresh cadence** | Near real-time (webhook processing) |
| **Trust level** | Authoritative for Flow 2 renewal invoices |
| **Owner** | Data Platform / Billing |
| **DAG** | <!-- TODO: verify DAG name --> |

## Description

Mirrors the MongoDB `StripeWebhookEvent` model. When Stripe fires a `subscription_cycle` invoice for a renewal, Apollo's webhook intercepts it, voids the auto-generated invoice, and creates a custom `manual` invoice clone. This table records that event, linking both the voided original invoice and the new paid clone.

This is the **Flow 2 bridge table** for renewals. Plan change invoices (Flow 1) do NOT appear here — see `FCT_MONGO_TEAM_PLAN_UPDATE_ATTEMPTS`.

## Upstream Sources

| Source | Relationship |
|---|---|
| MongoDB `StripeWebhookEvent` collection | 1:1 via CDC |
| `share__xdb23305.stripe.invoices` | Join on `CREATED_NEW_STRIPE_INVOICE_ID = INVOICES.id` for the paid clone |
| `share__xdb23305.stripe.customers_metadata` | Join on `STRIPE_CUSTOMER_ID = CUSTOMERS_METADATA.customer_id` to get Apollo team ID |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| `STRIPE_CUSTOMER_ID` | TEXT | Stripe customer ID | Join to `CUSTOMERS_METADATA` with `key = 'mongo_id'` to get Apollo team ID |
| `STRIPE_SUBSCRIPTION_ID` | TEXT | Stripe subscription ID for this renewal | |
| `STRIPE_INVOICE_ID` | TEXT | The **voided** Stripe-generated subscription invoice | `billing_reason = subscription_cycle`, `status = void` in INVOICES |
| `CREATED_NEW_STRIPE_INVOICE_ID` | TEXT | The **paid clone** invoice ID | `billing_reason = manual`, `status = paid`; this is the real cash event |
| `STRIPE_EVENT_TYPE` | TEXT | Stripe event type | Filter to `invoice.created` to isolate renewal clone events |
| `STRIPE_EVENT_CREATED_AT` | TIMESTAMP | When the webhook event was processed | Use as the renewal event timestamp |

## How It's Used

### Common query patterns

```sql
-- All renewal invoices for a team (Flow 2)
SELECT
    w.stripe_event_created_at              AS renewal_date,
    w.created_new_stripe_invoice_id        AS invoice_id,
    i.amount_due / 100.0                   AS amount_usd,
    i.billing_reason
FROM analytics_db.analytics_dataplatform.fct_mongo_stripe_webhook_events w
JOIN share__xdb23305.stripe.invoices i
    ON i.id = w.created_new_stripe_invoice_id
JOIN share__xdb23305.stripe.customers_metadata cm
    ON cm.customer_id = w.stripe_customer_id AND cm.key = 'mongo_id'
WHERE cm.value = '<apollo_team_id>'
  AND w.created_new_stripe_invoice_id IS NOT NULL
  AND w.stripe_event_type = 'invoice.created'
ORDER BY w.stripe_event_created_at DESC;
```

### Key consumers

- Full cash ledger (both billing flows combined)
- Renewal ARR tracking
- `domain/stripe_billing_patterns.md` — canonical reference

## Known Issues & Gotchas

- **Flow 2 only:** Plan change invoices (Flow 1) never appear here. Always union with `FCT_MONGO_TEAM_PLAN_UPDATE_ATTEMPTS` for a complete cash picture.
- **~1.97M draft renewals with no clone** (as of March 2026): `subscription_cycle + draft + no CREATED_NEW_STRIPE_INVOICE_ID`. These are unprocessed renewals or in-flight webhook delays — a completeness risk for full cash coverage.
- **~116K `subscription_cycle + paid + no clone`**: Likely pre-webhook-cloning behavior (older renewals). May need special handling for historical analysis.
- **No `ARR_DELTA`:** Renewals don't change ARR, so no delta is stored here. ARR is unchanged at renewal.
- **Join to Apollo team ID requires going through `CUSTOMERS_METADATA`:** There is no direct `TEAM_ID` column — you must join via `STRIPE_CUSTOMER_ID → CUSTOMERS_METADATA (key='mongo_id') → value = apollo_team_id`.
- **Migration-time void anomaly:** When a team migrates subscriptions, the old sub may auto-generate a `subscription_cycle` invoice that gets voided immediately with no clone. These appear as lone `subscription_cycle + void` rows with no `CREATED_NEW_STRIPE_INVOICE_ID`.

## Slack Context

- Primary reference: `domain/stripe_billing_patterns.md` (researched March 2026)

## Business Terms

| Term | Definition |
|---|---|
| Flow 2 | Renewal billing path — runs through this table |
| Void→clone pattern | Apollo voids Stripe's auto-generated subscription invoice and creates a custom `manual` clone; only the clone is a real charge |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-24 | Created context file from stripe_billing_patterns.md research | Andrew (Jarvis) |
