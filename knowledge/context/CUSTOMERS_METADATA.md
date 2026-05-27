# CUSTOMERS_METADATA

> Stripe customers metadata table (external data share). Key-value metadata on Stripe customers — the bridge between Stripe customer IDs and Apollo team IDs.

## Overview

| Field | Value |
|---|---|
| **Full path** | `SHARE__XDB23305.STRIPE.CUSTOMERS_METADATA` |
| **Grain** | One row per metadata key per customer |
| **Refresh cadence** | Near real-time (Stripe data share) |
| **Trust level** | Authoritative for Stripe ↔ Apollo team ID mapping |
| **Owner** | Stripe (external share) |
| **DAG** | N/A — external Stripe data share |

## Description

Stores key-value metadata attached to Stripe customer objects. The most important use is bridging Stripe's `customer_id` to Apollo's `mongo_id` (team ID). This is the primary join path when starting from a Stripe object (invoice, customer, webhook event) and needing to identify the Apollo team.

Also carries useful context keys like `salesforce_id`, `domain`, and `estimated_arr`.

## Upstream Sources

| Source | Relationship |
|---|---|
| Stripe (external) | Direct data share — metadata set by leadgenie when creating/updating Stripe customers |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| `CUSTOMER_ID` | TEXT | Stripe customer ID | Join key from other Stripe tables |
| `KEY` | TEXT | Metadata key name | Filter to specific keys (see below) |
| `VALUE` | TEXT | Metadata value | |

## Key metadata values

| Key | Value description |
|-----|------------------|
| `mongo_id` | Apollo team ID — primary bridge key |
| `salesforce_id` | SFDC account ID — bridge to opportunities/contracts |
| `salesforce_url` | SFDC account URL |
| `zp_team_url` | Apollo team admin URL |
| `zp_account_url` | Apollo account admin URL |
| `domain` | Customer domain |
| `estimated_arr` | Stripe-side ARR estimate |
| `customer_key` | Internal customer key |

## How It's Used

### Common query patterns

```sql
-- Get Apollo team ID from Stripe customer ID
SELECT value AS apollo_team_id
FROM share__xdb23305.stripe.customers_metadata
WHERE customer_id = '<stripe_customer_id>'
  AND key = 'mongo_id';

-- Join renewal events to Apollo team ID (standard Flow 2 pattern)
JOIN share__xdb23305.stripe.customers_metadata cm
    ON cm.customer_id = w.stripe_customer_id
    AND cm.key = 'mongo_id'
-- cm.value = apollo_team_id
```

### Key consumers

- Flow 2 renewal queries — joining `FCT_MONGO_STRIPE_WEBHOOK_EVENTS` to Apollo team IDs
- Three-way recon — alternative entry point to identify team without going through `FCT_MONGO_TEAM_PLAN_UPDATE_ATTEMPTS`
- SFDC bridge — `salesforce_id` key links Stripe customers to Salesforce opportunities

## Known Issues & Gotchas

- **One row per key** — must filter `AND key = 'mongo_id'` to get exactly the Apollo team ID. Forgetting the key filter returns all metadata rows for that customer.
- **`VALUE` may have extra quotes** — observed `trim(cm.value, '""')` in production queries. Strip quotes when using as a join key: `trim(cm.value, '"') = apollo_team_id`.
- **Not every Stripe customer has all keys** — `salesforce_id` may be missing for self-serve customers.

## Slack Context

- Primary reference: `domain/stripe_billing_patterns.md` (researched March 2026)

## Business Terms

| Term | Definition |
|---|---|
| `mongo_id` | Apollo's internal team identifier stored as Stripe customer metadata |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-24 | Created context file from stripe_billing_patterns.md research | Andrew (Jarvis) |
