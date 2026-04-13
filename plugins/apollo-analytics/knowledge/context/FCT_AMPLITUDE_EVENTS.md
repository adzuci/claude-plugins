# FCT_AMPLITUDE_EVENTS

> Amplitude event tracking — user-level product events. One row per event.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.FCT_AMPLITUDE_EVENTS` |
| **Grain** | One row per event |
| **Trust level** | Use with caution (ANALYTICS schema) — some event types have known data quality issues |
| **Owner** | Data / Product Analytics |

## Description

User-level Amplitude event log. Used for product activation signals, feature discovery events, and behavioral funnels that are not yet covered by the `user_*_actions_daily` tables in `ANALYTICS_DATASCIENCE`.

## Key Columns

| Column | Type | Description |
|---|---|---|
| APOLLO_TEAM_ID | VARIANT | Team identifier — joins require `::TEXT` cast (e.g. `evnt.apollo_team_id::TEXT = dtd.apollo_team_id`) |
| USER_ID | TEXT | User identifier |
| EVENT_TYPE | TEXT | Amplitude event name |
| EVENT_DATE | DATE | Date of the event |

## Common Query Patterns

```sql
-- First date a team had a website visitor identified (inbound churn analysis)
SELECT
    apollo_team_id
    , MIN(event_date) AS website_visitor_set_up_event
FROM ANALYTICS_DB.ANALYTICS.FCT_AMPLITUDE_EVENTS
WHERE event_type = 'Website Visitor Company Identified'
    AND event_date >= '2025-11-06'  -- REQUIRED: data issues before this date
GROUP BY 1;
```

## Power Ups Enrichment (event_type_id 813627141)

**Always use `SUM(number_of_records)` not `COUNT(events)`** — one event can enrich 1 to 10,000+ records. Event count is misleading (e.g. 478K events may represent 8.8M records enriched).

### Canonical base filter (apply to every Power Ups query)

```sql
WHERE evnt.event_type_id = 813627141
  -- exclude non-user-initiated previews (source_granular can be null or any value except 'preload_contact')
  AND (evnt.event_properties:source_granular IS NULL
       OR evnt.event_properties:source_granular <> 'preload_contact')
  -- exclude previews (redundant with source_granular filter but apply both)
  AND evnt.event_properties:request_type <> 'preview'
```

### Canonical aggregation columns

```sql
  , SUM(evnt.event_properties:number_of_records)           AS enriched_record_count
  , SUM(evnt.event_properties:number_of_credits_consumed)  AS consumed_credits_count
```

Key `event_properties` fields:
- `source::string` — **use this to identify Default Fields enrichments**: only two values exist: `'default_field'` and `'custom_field'`. `source = 'default_field'` is the canonical filter for Default Fields.
- `enrichment_origin::string` — alternative for Default Fields: `IN ('auto_enrichment', 'autoenrichment')` (both spellings exist; `auto_enrichment` is dominant at 12.4M vs `autoenrichment` at 39K). Slightly undercounts vs `source = 'default_field'` (~12.5M vs 12.9M). For AI Assistant origin: `IN ('aiassistant', 'assistant')`.
- `number_of_records` — records enriched in this event
- `number_of_credits_consumed` — credits consumed in this event; **numbers may not be reliable before 2026-02-25** — always flag when citing pre-2026-02-25 credit figures

### Records enriched query (Paid Core, weekly)
```sql
SELECT
    DATE_TRUNC('week', evnt.event_date) AS week_starting_sun,
    SUM(CASE WHEN evnt.event_properties:enrichment_origin::string IN ('autoenrichment','auto_enrichment')
             THEN evnt.event_properties:number_of_records ELSE 0 END) AS default_fields_records_enriched,
    SUM(CASE WHEN evnt.event_properties:enrichment_origin::string IN ('aiassistant','assistant')
             THEN evnt.event_properties:number_of_records ELSE 0 END) AS ai_assistant_origin_records_enriched
FROM ANALYTICS_DB.ANALYTICS.FCT_AMPLITUDE_EVENTS evnt
JOIN ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_TEAMS_DAILY dtd
    ON evnt.apollo_team_id::TEXT = dtd.apollo_team_id AND evnt.event_date = dtd.ds
WHERE evnt.event_type_id = 813627141
  AND (evnt.event_properties:source_granular IS NULL
       OR evnt.event_properties:source_granular <> 'preload_contact')
  AND evnt.event_properties:request_type <> 'preview'
  AND evnt.event_date >= {START_DATE} AND evnt.event_date < {END_DATE}
  AND dtd.is_core_account_ind = 1 AND dtd.is_free_email_domain_ind = 0 AND dtd.is_paid_ind = 1
GROUP BY 1 ORDER BY 1;
```

Run the same query without DIM_TEAMS_DAILY join for the all-users view.

## AI Messaging (event_type_id 15184751)

Tracks AI-generated emails sent in sequences. Key fields in `event_properties`:
- `num_emails_sent_*` variants — email send counts by type

## Known Issues & Gotchas

- **`Website Visitor Company Identified` unreliable before 2025-11-06** — data quality issues in the upstream Amplitude feed prior to this date. Always filter `event_date >= '2025-11-06'` when using this event type. Any analysis of website visitor setup dates must respect this cutoff.
- Other event types may have their own quality issues — verify against known good dates before using for historical analysis.
- For inbound actions (form enrichment, router publish, visitor search), prefer `USER_INBOUND_ACTIONS_DAILY` over Amplitude events — it's higher trust and purpose-built.

## Related Tables

| Table | Relationship |
|---|---|
| `USER_INBOUND_ACTIONS_DAILY` | Preferred source for inbound feature actions — more reliable than Amplitude |
| `USER_DIALER_ACTIONS_DAILY` | Preferred source for dialer actions |
| `DIM_USERS` | Join on `user_id` for user/team attributes |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-20 | Created — website visitor data issue gotcha, inbound churn usage pattern | Leo (via Claude) |
