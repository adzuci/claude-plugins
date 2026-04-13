# Jarvis Activity Tagging — Mandatory Protocol

Every meaningful Jarvis action must fire an activity pulse to Snowflake for tracking adoption, usage patterns, and ROI. This is non-negotiable for GA.

## How Pulses Work

```bash
python3 scripts/snowflake_query.py --pulse <action_name> --detail "<context>"
```

This fires a `SELECT 'pulse'` with a JSON comment tag that lands in `SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY`. The tag includes: app=jarvis, action, detail, user email, and timestamp. Queryable via:

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

**Every skill must fire a pulse on successful completion.** The pulse fires AFTER the work is done, not before. If the skill errors out, no pulse.

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
| Ad-hoc Snowflake query | `ad_hoc_query` | Brief description |
| Domain explanation | `domain_explanation` | Topic |
| Metric lookup (registry) | `metric_lookup` | Metric name |

## Pulse Command Templates

```bash
# After a product debrief completes
python3 scripts/snowflake_query.py --pulse product_debrief --detail "AI Assistant + Enrichment debrief"

# After a metric movement diagnosis
python3 scripts/snowflake_query.py --pulse metric_movement --detail "WAT paid declined 3% WoW"

# After an account deep dive
python3 scripts/snowflake_query.py --pulse account_deep_dive --detail "acme.com full profile"

# After answering an ad-hoc question
python3 scripts/snowflake_query.py --pulse ad_hoc_query --detail "churn by segment Q1 FY27"

# After a metric registry lookup
python3 scripts/snowflake_query.py --pulse metric_lookup --detail "M3 Cohort NRR"
```

## Integration with Usage Logs

Pulses complement `usage_log.md` — they don't replace it.

- **Pulses** → real-time, queryable in Snowflake, automatic, used for adoption dashboards
- **Usage logs** → human-readable, git-tracked, includes time-saved estimates, used for ROI reporting

Both must happen. The pulse fires in the skill. The usage log entry is appended at session end.

## For Skill Authors

When creating or updating a skill, add this block at the end of the skill's steps:

```markdown
## Tracking

After successful completion, fire an activity pulse:
\`\`\`bash
python3 scripts/snowflake_query.py --pulse <action_name> \
  --detail "<brief description of what was produced>"
\`\`\`
```

Replace `<action_name>` with the appropriate name from the table above.
