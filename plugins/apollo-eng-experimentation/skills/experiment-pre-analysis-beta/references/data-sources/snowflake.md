# Baselines from Snowflake

Use this to pull baseline inputs from the warehouse. **Always pull fresh — never
reuse a stored baseline.**

## How to run queries

Apollo Claude sessions have the Snowflake analytics MCP (Cortex/"Jarvis" tools).
It is governed — follow its order of operations instead of jumping to raw SQL:

1. `catalog-context-search` — confirm the table exists and get its fully
   qualified name (only catalog-approved tables may be queried).
1. `lookup-saved-metric` / `lookup-business-term` — a pre-approved SQL template
   or official metric definition beats hand-written SQL.
1. The analyst tools (`unified-analytics-agent`, `product-metrics-analyst`,
   `dim-teams-analyst`) — often answer a baseline question directly.
1. `execute-sql` — last resort, fully-qualified catalog tables only; access
   control is enforced server-side.

Useful fact: Amplitude events land in `ANALYTICS_DB.ANALYTICS.FCT_AMPLITUDE_EVENTS`
(the raw Fivetran Amplitude tables are stale — do not use them). This is where
per-user mean/SD pulls for event metrics usually come from.

If the MCP is not available in the session, hand the person a ready-to-run query
with the placeholders filled in and ask them to run it (Snowflake UI or Hex) and
paste the numbers back.

App-side data that lives only in Mongo (account flags, in-app objects, config):
most collections are replicated to the warehouse, so check
`catalog-context-search` for the table first. If it truly isn't replicated, ask
the owning engineer to pull it — production Mongo access is restricted and there
is no connector.

Placeholders to replace every time: `<eligibility_table>`, `<event_table>`,
`<eligible_filter>`, `<surface>`, and the window. Measure on the population that
will actually be eligible for the experiment, over a recent representative window
(≥1 full week; 2–4 weeks smooths seasonality). Compute at the **unit of
randomization** (usually per user), not per event.

## Proportion metric (conversion, activation, retention)

You need the baseline rate `p`:

```sql
SELECT
  COUNT(DISTINCT e.user_id)                                              AS eligible_users,
  COUNT(DISTINCT CASE WHEN a.user_id IS NOT NULL THEN e.user_id END)     AS converters,
  1.0 * COUNT(DISTINCT CASE WHEN a.user_id IS NOT NULL THEN e.user_id END)
      / NULLIF(COUNT(DISTINCT e.user_id), 0)                             AS baseline_rate
FROM <eligibility_table> e
LEFT JOIN <event_table> a
  ON a.user_id = e.user_id
 AND a.event_ts >= e.eligible_ts                 -- outcome must follow eligibility
 AND a.event_ts <  DATEADD('day', <window_days>, e.eligible_ts)   -- fixed conversion window
WHERE e.eligible_ts >= DATEADD('week', -4, CURRENT_DATE)
  AND <eligible_filter>                          -- e.g. e.surface = '<surface>'
;
```

Feed `baseline_rate` to `power_calc.py size --baseline <rate> --effect <change>`.

## Continuous / count metric (sessions, clicks, minutes, revenue)

The rate isn't enough — you need the **per-user mean and standard deviation**,
because variance drives the sample size:

```sql
WITH per_user AS (
  SELECT e.user_id,
         COUNT(ev.event_id) AS metric_value      -- or SUM(ev.amount), etc.
  FROM <eligibility_table> e
  LEFT JOIN <event_table> ev
    ON ev.user_id = e.user_id
   AND ev.event_ts >= e.eligible_ts
   AND ev.event_ts <  DATEADD('day', <window_days>, e.eligible_ts)
  WHERE e.eligible_ts >= DATEADD('week', -4, CURRENT_DATE)
    AND <eligible_filter>
  GROUP BY e.user_id                              -- one row per randomization unit
)
SELECT COUNT(*)                 AS users,
       AVG(metric_value)        AS mean,
       STDDEV_SAMP(metric_value) AS sd,
       VAR_SAMP(metric_value)    AS variance
FROM per_user
;
```

Feed `sd` to `power_calc.py size --sd <sd> --effect <change>`.

## Weekly exposure (the "clock speed")

How many eligible units enter per week — this turns a sample size into weeks:

```sql
SELECT COUNT(DISTINCT user_id)
     / NULLIF(COUNT(DISTINCT DATE_TRUNC('week', eligible_ts)), 0) AS eligible_users_per_week
FROM <eligibility_table>
WHERE eligible_ts >= DATEADD('week', -8, CURRENT_DATE)
  AND <eligible_filter>                           -- SAME filter as the baseline query
;
```

When the proxy is an Amplitude event, `<eligibility_table>` is
`ANALYTICS_DB.ANALYTICS.FCT_AMPLITUDE_EVENTS` filtered on
`EVENT_TYPE = '<proxy event>'` plus the eligibility predicate, with
`EVENT_DATE` as `eligible_ts`.

Feed it to `power_calc.py runtime --weekly-exposure <that number>` (it's the
total across arms; the tool splits by `--arms`).

## Gotchas

- Use the **same eligibility filter** in the baseline and exposure queries, or
  the runtime estimate won't match reality.
- For CUPED variance reduction, also pull each user's **pre-period** metric value
  and compute the pre/post correlation; see `../stats-methods.md`.
- If users cluster (shared accounts/teams), the effective sample is smaller than
  the row count — note it and consider cluster-level randomization.

## Maintenance

- **Table/column names are placeholders.** The Activation team's real source
  tables and eligibility logic live in `teams/activation/metrics.md`.
- **Owner:** the apollo-eng-experimentation plugin maintainers
