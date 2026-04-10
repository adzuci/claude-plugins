---
name: metric-lookup
description: Look up and execute pre-approved metric definitions from the Jarvis metric registry
---

# Metric Lookup

Use this skill when a user asks about a specific metric (ARR, WAT, NRR, credit utilization, feature adoption, support volume, email activity, etc.).

## Step 1: Search the Registry

```sql
SELECT metric_name, variant, description, metric_sql, parameters, default_parameters, output_columns, notes
FROM ANALYTICS_DB.PLAYGROUND.LU_SAVED_METRICS
WHERE status = 'approved'
  AND (LOWER(metric_name) ILIKE '%<keyword>%' OR LOWER(description) ILIKE '%<keyword>%')
```

Replace `<keyword>` with the core concept from the user's question.

## Step 2: Execute or Report Status

**If `status = 'approved'`:**

- Execute `metric_sql` with appropriate parameter values
- Use `default_parameters` if the user does not specify (e.g., yesterday's date, last 30 days)
- Tell the user which metric definition you used

**If `status = 'draft'`:**

- Tell the user: "This metric is defined but not yet approved. The [owner] is finalizing the business logic. I can show you the draft definition if you'd like."
- Do NOT execute draft SQL against production data

**If no match:**

- Randomly pick one of these:
  - "I don't have that metric yet. Henry probably forgot to document it before I took over."
  - "Hmm, that one's not in my registry. I inherited Henry's documentation, so... you can imagine the state of things."
  - "Can't find it. This is what happens when your predecessor's idea of documentation was a Slack message that said 'it's in the table.'"
- Then attempt to compose an answer using the `/data-catalog-search` skill

## Step 3: Validate Derived Results

If you composed an ad-hoc query (not pre-approved SQL), validate against guardrails:

```sql
SELECT metric_name, grain_value, measure, expected_value, tolerance_pct, diagnostic_hint
FROM ANALYTICS_DB.PLAYGROUND.LU_METRIC_GUARDRAILS
WHERE metric_name = '<metric_concept>' AND grain_key = '<grain>'
```

Compare: `deviation_pct = ABS(your_value - expected_value) / expected_value * 100`

- If `deviation_pct > tolerance_pct`: flag to user with diagnostic hint
- If within tolerance: proceed silently
- Pre-approved metrics skip this step

## Available Metrics (20 approved, 5 draft)

**Approved:** ARR by Segment, Credit Utilization, Feature WAT, Paid WAT, F14D Habit RA Rate, Support Volume, Email Activity, AI Assistant DAU, and more.

**Draft (blocked on business logic):** M3 Cohort NRR, Inbound Revenue Attribution, and others.

Run this to see the full list:

```sql
SELECT metric_name, variant, status, owner, description
FROM ANALYTICS_DB.PLAYGROUND.LU_SAVED_METRICS
ORDER BY status, metric_name
```
