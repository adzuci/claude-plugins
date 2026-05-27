# LU_ENUM

> Master enum mapping table: Amplitude event IDs to names, credit type codes, feature type codes, and other source-system integer enums.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.PLAYGROUND.LU_ENUM` |
| **Grain** | (sourced_from, enum_name, enum_id) |
| **Grain columns** | sourced_from, enum_name, enum_id |
| **Row count** | ~1680 |
| **Refresh cadence** | weekly (Monday 6AM) for Amplitude events; manual for credit/feature types |
| **Coverage period** | ongoing |
| **Trust level** | Reference |
| **Owner** | Analytics (Bridie Meredith) |

## Description

Consolidates all integer-to-string enum mappings across Apollo's source systems into a single lookup table. Primary use cases: (1) resolving Amplitude `event_type_id` integers to human-readable event names, (2) mapping `credit_type` and `feature_type` integer codes used in `AGG_TEAM_CREDITS` and `FCT_TEAM_CREDIT_USE_DAILY`. Extracted from leadgenie Ruby `as_enum` definitions plus manual credit/feature type expansions. Populated by three SQL scripts: `lu_enum_amplitude_events.sql`, `lu_enum_amplitude_expansion.sql`, and `lu_enum_credit_expansion.sql`.

## Upstream Sources

| Source | Relationship |
|---|---|
| leadgenie Ruby source (as_enum definitions) | Base credit type and source type mappings |
| FCT_AMPLITUDE_EVENTS | Amplitude event_type_id → event_name (auto-refreshed weekly) |
| Manual credit/feature type expansions | Additional CREDIT_TYPE and FEATURE_TYPE rows added via `lu_enum_credit_expansion.sql` |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| sourced_from | VARCHAR | System/table the enum originates from | Values: `CREDIT_QUOTA`, `CREDIT_USAGE`, `AGG_TEAM_CREDITS`, `AMPLITUDE` |
| enum_name | VARCHAR | Name of the enum set | Values: `CREDIT_TYPE`, `SOURCE_TYPE`, `TYPE_CD`, `FEATURE_TYPE`, `EVENT_TYPE` |
| enum_key | VARCHAR | String key for the enum value | e.g. `unified`, `email_credit`, the event_type_id as string |
| enum_id | NUMBER | Integer ID (source system enum value) | e.g. `7` for unified credit type |
| enum_value | VARCHAR | Human-readable name | e.g. `unified_lead_credit`, `Call Dialed` |
| enum_category | VARCHAR | Legacy backwards-compat category | Use `enum_name` for new queries; `amplitude_event` for old Amplitude joins |
| expiration_at | TIMESTAMP_NTZ | When this mapping expires | NULL = still active |
| status | VARCHAR | Row status | `TEMPORARY` for most rows (pre-full migration) |
| owned_by | VARCHAR | Team owning this mapping | |
| description | VARCHAR | Additional context | |

## Known Issues

- DAG was reverted at some point — verify Amplitude event rows are current before trusting event names
- `enum_category` (legacy) and `sourced_from`/`enum_name` (new schema) coexist — older queries use `ENUM_CATEGORY='amplitude_event'`, newer queries use `SOURCED_FROM='AMPLITUDE' AND ENUM_NAME='EVENT_TYPE'`
- `TYPE_CD` gaps: IDs 37–39 have placeholder rows with `Unknown (N)` values — source system enum IDs not yet documented
- `status='TEMPORARY'` on most rows reflects a planned schema migration that has not completed

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-14 | Created context file from catalog metadata | Pepper (auto) |
