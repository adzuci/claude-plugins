# LU_AMPLITUDE_FEATURE_RULES

> Maps Amplitude event_type_ids to Apollo product feature classifications via rule-based logic.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.PLAYGROUND.LU_AMPLITUDE_FEATURE_RULES` |
| **Grain** | (feature_flag, event_type_id, rule_id, property_key) |
| **Grain columns** | feature_flag, event_type_id, rule_id, property_key |
| **Row count** | ~130 |
| **Refresh cadence** | manual |
| **Coverage period** | ongoing |
| **Trust level** | Canonical |
| **Owner** | Analytics (Bridie Meredith) |

## Description

Replaces ~500 lines of boolean CASE WHEN logic in `dbt_apollo/models/marts/amplitude/fct_amplitude_events.sql`. Each row is one classification rule: an event matches a feature if its event_type_id matches AND all property conditions for that rule_id are satisfied (AND within a rule, OR across rules for the same feature). This makes dbt feature flag logic queryable and auditable without redeploying dbt.

## Upstream Sources

| Source | Relationship |
|---|---|
| dbt fct_amplitude_events.sql | Extracted rule-by-rule from CASE WHEN boolean logic |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| feature_flag | VARCHAR | Feature boolean name | e.g. `is_dialer`, `is_email`, `is_sequences` |
| domain | VARCHAR | Product domain grouping | Values: `genpipe`, `activity`, `enrichment`, `winclose` |
| event_type_id | NUMBER | Amplitude numeric event ID | Join to LU_ENUM for human-readable name |
| rule_id | NUMBER | Rule number within a feature (OR logic across rules) | Multiple rules per feature are OR'd |
| property_key | VARCHAR | Amplitude event property to filter on | NULL = event_type_id match alone is sufficient |
| property_operator | VARCHAR | Comparison operator | Values: `eq`, `neq`, `in`, `not_in`, `like_any`, `is_not_null`, `is_true`, `gt`, `ilike` |
| property_value | VARCHAR | Expected property value (always TEXT) | Consumers cast as needed |
| deprecated_at | DATE | Date rule was deprecated | NULL = still active |
| notes | VARCHAR | Human-readable event description | e.g. `Call Dialed`, `Email Sent (not via extension)` |

## Known Issues

- Missing 4 features: `is_ai_platform`, `is_engage`, `is_data`, `is_workflows` (incomplete extraction from dbt)
- `property_value` is always TEXT — numeric comparisons require explicit casting in consumers

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-14 | Created context file from catalog metadata | Pepper (auto) |
