# DIM_AMPLITUDE_ONBOARDING_EVENTS

> Event-level Amplitude onboarding events with USER_ID, event type, and properties.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.DIM_AMPLITUDE_ONBOARDING_EVENTS` |
| **Grain** | One row per event (user × event_at × event_type) |
| **Row count** | Large (millions) |
| **Refresh cadence** | Daily |
| **Coverage period** | ongoing |
| **Trust level** | Use with caution (Amplitude sampling/schema may vary) |
| **Owner** | Analytics |
| **DAG** | unknown |

## Description

Raw Amplitude onboarding event log. Captures user-level events including all "Record Actioned: *" subtypes, prospecting events, and other onboarding milestones. Used to compute F14D Habit RA Rate by RA subtype and to analyze composition of RA actions.

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| `UUID` | TEXT | Event UUID | |
| `USER_ID` | TEXT | Apollo user ID | Join to DIM_USER_ACTIVATION.APOLLO_USER_ID |
| `EVENT_AT` | TIMESTAMP_NTZ | Exact event timestamp | |
| `EVENT_DATE` | DATE | Date of event | Use for daily aggregations |
| `EVENT_TYPE` | TEXT | Event name | e.g. "Record Actioned: Push to 3rd party integration" |
| `EVENT_PROPERTIES` | VARIANT | JSON properties | Contains source, entity type, etc. |

## Known RA Event Types

- `Record Actioned: Push to 3rd party integration` — CRM push (pre-Mar 31 Habit RA proxy)
- `Record Actioned: Add to Sequence`
- `Record Actioned: Add to list`
- `Record Actioned: Export`
- `Record Actioned: Save Contacts` / `Record Actioned: Save Accounts`
- `Record Actioned: Enrich Emails` / `Record Actioned: Enrich Mobile Numbers`
- `Record Actioned: Set Stage`, `Record Actioned: Assign Owner`, etc.

## Known Issues & Gotchas

- No direct TEAM_ID — must join via DIM_USER_ACTIVATION on USER_ID → APOLLO_TEAM_ID
- AI Assistant RA actions do NOT fire these Amplitude events (fix pending Apr 2026)
- MCP actions not tracked here either
