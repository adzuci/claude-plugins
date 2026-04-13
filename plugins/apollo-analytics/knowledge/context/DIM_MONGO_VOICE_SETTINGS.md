# DIM_MONGO_VOICE_SETTINGS

> Dimension table for voice/dialer phone number settings. One row per voice setting (phone number) per user.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_VOICE_SETTINGS` |
| **Grain** | One row per voice setting (phone number) |
| **Row count** | ~573K (as of 2026-03-26) |
| **Refresh cadence** | Daily (assumed — ANALYTICS_DATAPLATFORM standard) |
| **Trust level** | High — ANALYTICS_DATAPLATFORM schema |
| **Owner** | Data Platform |
| **DAG** | <!-- TODO: check airflow-dags --> |

## Description

Dimension table containing Twilio phone number configurations for Apollo's dialer product. Each row represents a purchased phone number assigned to a user/team, with metadata on active status, spam status, CNAM registration, SHAKEN/STIR compliance, number type, and region. Use for dialer provisioning analysis, spam rate tracking, and number inventory reporting.

## Upstream Sources

| Source | Relationship |
|---|---|
| MongoDB `voice_settings` collection (assumed) | Raw source — replicated to Snowflake by Data Platform |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| VOICE_SETTING_ID | TEXT | Unique identifier | Primary key |
| USER_ID | TEXT | User the number belongs to | Join to DIM_MONGO_USERS |
| TEAM_ID | TEXT | Team the number belongs to | Join to DIM_MONGO_TEAMS |
| PHONE_NUMBER | TEXT | Actual phone number (e.g., +15105647903) | |
| SID | TEXT | Twilio SID for the number | |
| NUMBER_TYPE | TEXT | local, mobile, or national | |
| COUNTRY_CODE | TEXT | ISO country code (e.g., US, IN) | |
| REGION | TEXT | Geographic region code (e.g., CA) | |
| ACTIVE | BOOLEAN | Whether the number is currently active | Defaults to true |
| IS_DEFAULT | BOOLEAN | Whether this is the user's default number | |
| MARKED_AS_SPAM | BOOLEAN | Whether the number is flagged as spam | Key for spam rate analysis |
| SPAM_CHECK_RETRY_COUNT | NUMBER | Times spam status check has been retried | |
| SPAM_STATUS_LAST_CHECKED_AT | TIMESTAMP_NTZ | Last spam check timestamp | |
| CNAM_REGISTRATION_STATUS_CD | NUMBER | CNAM status: 0=pending, 1=approved, 2=rejected, 3=deregistered, 4=failed | Numeric enum |
| CNAM_FAILURE_REASON | TEXT | Reason for CNAM failure, if applicable | |
| SHAKEN_STIR_ONBOARDING_REQUIRED | BOOLEAN | Pending SHAKEN/STIR registration | |
| SHAKEN_STIR_OFF_BOARDING_REQUIRED | BOOLEAN | Pending SHAKEN/STIR deregistration | |
| IS_MIGRATED_TO_SUBACCOUNT | BOOLEAN | Migrated to Twilio subaccount | |
| VOICE_APPLICATION_SID_SET | BOOLEAN | TwiML SID configured for the number | |
| PURCHASED_AT | TIMESTAMP_NTZ | When the number was purchased | |
| DEACTIVATED_AT | TIMESTAMP_NTZ | When the number was deactivated | NULL if still active |
| CREATED_AT_UTC | TIMESTAMP_NTZ | Record creation timestamp | |
| UPDATED_AT_UTC | TIMESTAMP_NTZ | Last updated timestamp | |
| LOAD_DATE | DATE | Snowflake load date | |

## How It's Used

### Common query patterns

```sql
-- Active number count and spam rate by team
SELECT
    TEAM_ID,
    COUNT(*) AS total_numbers,
    SUM(CASE WHEN ACTIVE THEN 1 ELSE 0 END) AS active_numbers,
    SUM(CASE WHEN MARKED_AS_SPAM THEN 1 ELSE 0 END) AS spam_numbers,
    ROUND(spam_numbers / NULLIF(active_numbers, 0), 3) AS spam_rate
FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_VOICE_SETTINGS
GROUP BY 1;
```

### Key consumers

<!-- TODO: identify from query history -->

## Known Issues & Gotchas

- **CNAM_REGISTRATION_STATUS_CD is numeric enum** — 0=pending, 1=approved, 2=rejected, 3=deregistered, 4=failed. Not a text field.
- **ACTIVE defaults to true** — deactivated numbers have ACTIVE=false AND DEACTIVATED_AT populated.
- **Multiple Twilio SID columns** — CUSTOMER_PROFILE_CHANNEL_ASSIGNMENT_SID, TRUST_PRODUCT_CHANNEL_END_POINT_ASSIGNMENT_SID, VOICE_INTEGRITY_CHANNEL_END_POINT_ASSIGNMENT_SID are all Twilio regulatory/compliance references.

## Business Terms

| Term | Definition |
|---|---|
| SHAKEN/STIR | FCC-mandated caller ID authentication framework to combat robocalls |
| CNAM | Caller Name — the display name shown to call recipients |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-26 | Created context file from Snowflake schema | Anvitha (via Jarvis) |
