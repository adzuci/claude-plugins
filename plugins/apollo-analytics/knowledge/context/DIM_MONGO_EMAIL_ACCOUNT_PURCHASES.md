# DIM_MONGO_EMAIL_ACCOUNT_PURCHASES

> Email account purchases (Apollo-provisioned sending mailboxes). One row per purchased email account.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_EMAIL_ACCOUNT_PURCHASES` |
| **Grain** | One row per email account purchase |
| **Row count** | ~12.7K (as of 2026-03-26) |
| **Refresh cadence** | Daily (assumed — ANALYTICS_DATAPLATFORM standard) |
| **Trust level** | High — ANALYTICS_DATAPLATFORM schema |
| **Owner** | Data Platform |
| **DAG** | <!-- TODO: check airflow-dags --> |

## Description

Dimension table for email accounts purchased through Apollo (managed sending mailboxes). Tracks provisioning lifecycle — creation, assignment, billing, deletion, and unlinking. Includes account type (shared/private/google/outlook) and status. Use for mailbox provisioning analysis, deliverability capacity planning, and adoption of Apollo-managed email.

## Upstream Sources

| Source | Relationship |
|---|---|
| MongoDB `email_account_purchases` collection (assumed) | Raw source — replicated to Snowflake by Data Platform |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| EMAIL_ACCOUNT_PURCHASE_ID | TEXT | Unique identifier | Primary key |
| TEAM_ID | TEXT | Team that purchased the account | Join to DIM_MONGO_TEAMS |
| CREATOR_USER_ID | TEXT | User who created the purchase | Join to DIM_MONGO_USERS |
| ASSIGNED_USER_ID | TEXT | User the account is assigned to | May differ from creator |
| DOMAIN_PURCHASE_ID | TEXT | Associated domain purchase | |
| EMAIL | TEXT | Email address of the purchased account | |
| FIRST_NAME | TEXT | First name on the account | |
| LAST_NAME | TEXT | Last name on the account | |
| FORWARDING_EMAIL | TEXT | Forwarding address for replies | |
| VENDOR_ID | TEXT | Email service provider vendor ID | |
| EXTERNAL_ID | TEXT | External ID from vendor system | |
| TYPE_CD | TEXT | Account type: shared, private, google, outlook | |
| STATUS_CD | TEXT | Status: pending_setup, active, deleted | |
| BILLING_PERIOD_ENDS_AT | TIMESTAMP_NTZ | When current billing period expires | |
| DELETED_AT | TIMESTAMP_NTZ | When the account was deleted | NULL if active |
| UNLINKED_AT | TIMESTAMP_NTZ | When the account was unlinked | NULL if still linked |
| CREATED_AT_UTC | TIMESTAMP_NTZ | Record creation timestamp | |
| UPDATED_AT_UTC | TIMESTAMP_NTZ | Last updated timestamp | |
| LOAD_DATE | DATE | Snowflake load date | |

## Known Issues & Gotchas

- **CREATOR_USER_ID vs ASSIGNED_USER_ID** — creator is who purchased, assigned is who uses it. They can differ (e.g., admin purchases for reps).
- **STATUS_CD known values**: pending_setup, active, deleted. May have others.
- **TYPE_CD known values**: shared, private, google, outlook. Determines how the mailbox is provisioned and managed.

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-26 | Created context file from Snowflake schema | Anvitha (via Jarvis) |
