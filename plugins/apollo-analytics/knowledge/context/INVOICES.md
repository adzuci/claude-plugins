# INVOICES

> Stripe invoices table (external data share). Contains all invoices across both Apollo billing flows — plan changes and renewals.

## Overview

| Field | Value |
|---|---|
| **Full path** | `SHARE__XDB23305.STRIPE.INVOICES` |
| **Grain** | One row per Stripe invoice |
| **Refresh cadence** | Near real-time (Stripe data share) |
| **Trust level** | Authoritative — Stripe source of truth for invoice amounts and status |
| **Owner** | Stripe (external share); Finance / Billing own the business logic |
| **DAG** | N/A — external Stripe data share, not built by Airflow |

## Description

The Stripe invoices table, accessed via Snowflake data sharing from Apollo's Stripe account. Contains every invoice — real billing invoices, voided structural invoices, and draft renewals. Must be filtered carefully to isolate real cash events. Both Flow 1 (plan changes via `FCT_MONGO_TEAM_PLAN_UPDATE_ATTEMPTS`) and Flow 2 (renewals via `FCT_MONGO_STRIPE_WEBHOOK_EVENTS`) join to this table for invoice amounts.

## Upstream Sources

| Source | Relationship |
|---|---|
| Stripe (external) | Direct data share from Apollo's Stripe account |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| `ID` | TEXT | Stripe invoice ID | Primary key; join target for `STRIPE_INVOICE_ID` on Apollo bridge tables |
| `AMOUNT_DUE` | INTEGER | Invoice amount in **cents** | Divide by 100 for USD; includes tax if applicable |
| `SUBTOTAL` | INTEGER | Subtotal before invoice-level discount, in cents | If `SUBTOTAL != AMOUNT_DUE`, an invoice-level discount exists |
| `STATUS` | TEXT | Invoice status | `paid` = real charge; `void` = cancelled; `draft` = not yet finalized |
| `BILLING_REASON` | TEXT | Why the invoice was created | `manual` = real billing invoice; `subscription_cycle` = Stripe auto-generated (usually voided); `subscription_create` = structural/suppressed |
| `CUSTOMER` | TEXT | Stripe customer ID | Join to `CUSTOMERS_METADATA` for Apollo team ID |
| `PERIOD_START` | TIMESTAMP | Start of billing period | Useful for provisioned-state lookups |

## How It's Used

### Common query patterns

```sql
-- Check invoice status and amount for a known invoice ID
SELECT id, amount_due / 100.0 AS amount_usd, billing_reason, status
FROM share__xdb23305.stripe.invoices
WHERE id = '<invoice_id>';

-- Flag invoice-level discounts (subtotal != amount_due)
SELECT id, subtotal / 100.0, amount_due / 100.0,
       (subtotal - amount_due) / 100.0 AS invoice_level_discount_usd
FROM share__xdb23305.stripe.invoices
WHERE id = '<invoice_id>';
```

### Key consumers

- Flow 1 billing recon: joined via `FCT_MONGO_TEAM_PLAN_UPDATE_ATTEMPTS.STRIPE_INVOICE_ID`
- Flow 2 billing recon: joined via `FCT_MONGO_STRIPE_WEBHOOK_EVENTS.CREATED_NEW_STRIPE_INVOICE_ID`
- Three-way recon pattern (`domain/stripe_billing_patterns.md`)

## Known Issues & Gotchas

- **All amounts in cents** — always divide by 100 for USD.
- **Don't trust all invoices as real charges.** `billing_reason = 'subscription_create'` invoices are structural (paid_out_of_band to suppress Stripe billing). Filter to `status = 'paid'` and join through bridge tables to get real billing events.
- **Invoice-level discounts:** When `subtotal != amount_due`, a discount was applied at the invoice level (not line item level). This gap is not captured in `invoice_line_items` or `invoice_line_item_discount_amounts` — check `INVOICES.discount` or the `DISCOUNTS` table.
- **Sales tax included in `amount_due`:** Some customers have `"Sales Tax (Included in the Subtotal)"` line items. Strip these before comparing to contract totals.
- **Three discount mechanisms exist** — see `domain/stripe_billing_patterns.md` for the full pattern. `amount_due` is the cleanest net figure.

## Slack Context

- Primary reference: `domain/stripe_billing_patterns.md` (researched March 2026)

## Business Terms

| Term | Definition |
|---|---|
| `billing_reason = 'manual'` | A real billing invoice created by Apollo's code (not Stripe auto-billing) |
| `billing_reason = 'subscription_cycle'` | Stripe auto-generated renewal invoice — almost always voided and replaced by a manual clone |
| `billing_reason = 'subscription_create'` | Structural invoice immediately suppressed; not a real charge |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-24 | Created context file from stripe_billing_patterns.md research | Andrew (Jarvis) |
