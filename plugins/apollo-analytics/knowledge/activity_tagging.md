# Jarvis Activity Tagging — Mandatory Protocol

Every meaningful Jarvis action must fire an activity pulse to Snowflake for
tracking adoption, usage patterns, and ROI. This is non-negotiable for GA.

> **Migration complete — 2026-04-16.** All `--pulse` callsites have been
> migrated off `scripts/snowflake_query.py`. Skills now use either the
> MCP-native tagged `SELECT` described below, or the canonical CLI wrapper
> `python3 scripts/log_session.py end <action> "<detail>" <est_min_saved>`
> (which buffers locally and flushes via MCP at session boundary). The
> legacy Python wrapper has been retired.

## How Pulses Work (MCP-native)

Fire a pulse by running a tagged `SELECT 'pulse'` via the Snowflake MCP
(`mcp__snowflake__read_query`). The tag is a JSON comment at the start of
the SQL, which lands in `SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY` alongside
the session's native `USER_NAME` and `START_TIME`.

```sql
/* {"app":"jarvis","action":"<action_name>","detail":"<context>"} */
SELECT 'pulse' AS status
```

That's the whole protocol. `user` and timestamp are populated by Snowflake
itself (no need to stuff them into the JSON tag — `USER_NAME` and
`START_TIME` are native columns).

### Reading pulses back

```sql
SELECT
  PARSE_JSON(SUBSTR(QUERY_TEXT, 3, POSITION(' */' IN QUERY_TEXT)-3)) AS tag,
  tag:action::STRING AS action,
  tag:detail::STRING AS detail,
  USER_NAME,
  START_TIME
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE QUERY_TEXT ILIKE '/* {"app":"jarvis"%'
  AND START_TIME >= DATEADD('day', -30, CURRENT_TIMESTAMP())
ORDER BY START_TIME DESC
```

## When to Fire Pulses

**Every skill must fire a pulse on successful completion.** The pulse fires
AFTER the work is done, not before. If the skill errors out, no pulse.

| Skill / Action | Pulse action name | Detail format |
|---|---|---|
| `product-debrief` | `product_debrief` | Product area name(s) |
| `metric-movement` | `metric_movement` | Metric name + direction |
| `account-detail` | `account_deep_dive` | Domain or team ID |
| `ai-analytics` | `ai_analytics` | Question summary |
| `analyze-experiment` | `experiment_analysis` | Experiment/flag key |
| `addon-weekly-report` | `weekly_report` | Report type |
| `activity-summary` | `activity_summary` | Squad or employee name |
| `source-catalog` | `catalog_search` | Source system + object |
| `credit-analysis` | `credit_analysis` | Segment or focus area |
| `share-report` | `draft` | Report title + backend |
| `function-debrief` | `function_debrief` | Function name |
| Ad-hoc Snowflake query | `ad_hoc_query` | Brief description |
| Domain explanation | `domain_explanation` | Topic |
| Metric lookup (registry) | `metric_lookup` | Metric name |

## Pulse Examples (MCP-native)

```sql
-- After a product debrief completes
/* {"app":"jarvis","action":"product_debrief","detail":"AI Assistant + Enrichment debrief"} */
SELECT 'pulse'

-- After a metric movement diagnosis
/* {"app":"jarvis","action":"metric_movement","detail":"WAT paid declined 3% WoW"} */
SELECT 'pulse'

-- After an account deep dive
/* {"app":"jarvis","action":"account_deep_dive","detail":"acme.com full profile"} */
SELECT 'pulse'

-- After answering an ad-hoc question
/* {"app":"jarvis","action":"ad_hoc_query","detail":"churn by segment Q1 FY27"} */
SELECT 'pulse'

-- After a metric registry lookup
/* {"app":"jarvis","action":"metric_lookup","detail":"M3 Cohort NRR"} */
SELECT 'pulse'
```

Escape embedded double-quotes in `detail` as `\"`. Keep the JSON comment on
a single line — Snowflake's query-history regex match depends on it.

## Integration with Usage Logs

Pulses complement `usage_log.md` — they don't replace it.

- **Pulses** → real-time, queryable in Snowflake, automatic, used for adoption dashboards
- **Usage logs** → human-readable, git-tracked, includes time-saved estimates, used for ROI reporting

Both must happen. The pulse fires in the skill. The usage log entry is appended at session end.

## For Skill Authors

When creating or updating a skill, add this block at the end of the skill's steps:

```markdown
## Tracking

After successful completion, fire an activity pulse via `mcp__snowflake__read_query`:

\`\`\`sql
/* {"app":"jarvis","action":"<action_name>","detail":"<brief description>"} */
SELECT 'pulse'
\`\`\`
```

Replace `<action_name>` with the appropriate name from the table above.

## Canonical CLI wrapper (preferred for skill `## Tracking` blocks)

```bash
python3 scripts/log_session.py end <action_name> "<detail>" <est_min_saved>
```

`log_session.py` buffers the record to a local JSONL and lets the next
SessionStart / `/jarvis` invocation flush it to `FCT_JARVIS_SESSIONS` via
the Snowflake MCP. Captures `est_min_saved` (which the tagged-SELECT
approach cannot). For ad-hoc pulses outside a skill, the MCP-native
tagged `SELECT` above is also fine.
