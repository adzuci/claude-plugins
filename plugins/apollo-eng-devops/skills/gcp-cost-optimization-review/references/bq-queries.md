# Verified BigQuery Queries — GCP Cost Optimization Review

All queries below were **executed successfully against the live billing export on 2026-09-05**.
Do not modify the net-cost expression or the finalization-lag windows without re-testing.

**Run pattern:**

```bash
bq query --use_legacy_sql=false --project_id=indigo-lotus-415 \
  --format=csv --dry_run '<SQL>'                                      # dry run first, always
bq query --use_legacy_sql=false --project_id=indigo-lotus-415 \
  --format=csv --maximum_bytes_billed=50000000000 '<SQL>'             # then the real query
```

Every query in this file takes `--format=csv --maximum_bytes_billed=50000000000`, and every first
run of a query in a session gets a `--dry_run` pass before the real one. `--maximum_bytes_billed`
is a cost guardrail (hard-fails instead of scanning an unbounded amount); it is never passed to
`--dry_run` itself since a dry run bills nothing.

**Table:** `databricks-apolloio.billing_export.gcp_billing_export_v1_0174D0_6590F0_824CC0`

______________________________________________________________________

## The net-cost expression (use everywhere)

```sql
SUM(cost) + SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)) AS net_cost
```

Correlated subquery, **not** a top-level `, UNNEST(credits) AS credit` join. The top-level join fans
out one row per credit and double-counts `cost`. Credits are negative, so this subtracts correctly.

Verified reconciliation:

| Month | Gross | Credits | **Net** |
| --- | --- | --- | --- |
| 2026-06 | $2,482,689 | -$998,642 | **$1,484,047** |
| 2026-07 | $2,687,125 | -$1,137,900 | **$1,549,225** |
| 2026-08 | $2,885,548 | -$1,040,173 | **$1,845,374** |

Net matches the $1.51M → $1.89M figures from INFRA-2173. Gross does not.

______________________________________________________________________

<a id="q1"></a>

## Q1 — Monthly net / gross / credits, with credit rate

```sql
SELECT
  FORMAT_TIMESTAMP('%Y-%m', usage_start_time) AS month,
  ROUND(SUM(cost), 2) AS gross_cost,
  ROUND(SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)), 2) AS credits,
  ROUND(SUM(cost) + SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)), 2) AS net_cost,
  ROUND(SAFE_DIVIDE(
    -SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)),
    NULLIF(SUM(cost), 0)) * 100, 1) AS credit_rate_pct
FROM `databricks-apolloio.billing_export.gcp_billing_export_v1_0174D0_6590F0_824CC0`
WHERE DATE(usage_start_time) >= DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 6 MONTH), MONTH)
  AND DATE(usage_start_time) < DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
GROUP BY month
ORDER BY month;
```

The final row is still labeled month-to-date and incomplete — the upper bound only excludes the
unfinalized last day, it does not make the current month complete. `credit_rate_pct` running
~35–40% is normal; a sustained fall with flat gross means commitment coverage is slipping.

______________________________________________________________________

<a id="q2"></a>

## Q2 — MoM net by service

```sql
WITH m AS (
  SELECT
    service.description AS service,
    FORMAT_TIMESTAMP('%Y-%m', usage_start_time) AS mo,
    SUM(cost) + SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)) AS net
  FROM `databricks-apolloio.billing_export.gcp_billing_export_v1_0174D0_6590F0_824CC0`
  WHERE DATE(usage_start_time) >= DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 2 MONTH), MONTH)
    AND DATE(usage_start_time) <  DATE_TRUNC(CURRENT_DATE(), MONTH)
  GROUP BY service, mo
)
SELECT
  service,
  ROUND(SUM(IF(mo = FORMAT_DATE('%Y-%m', DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH)), net, 0)), 2) AS last_mo,
  ROUND(SUM(IF(mo = FORMAT_DATE('%Y-%m', DATE_SUB(CURRENT_DATE(), INTERVAL 2 MONTH)), net, 0)), 2) AS prior_mo,
  ROUND(SUM(IF(mo = FORMAT_DATE('%Y-%m', DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH)), net, 0))
      - SUM(IF(mo = FORMAT_DATE('%Y-%m', DATE_SUB(CURRENT_DATE(), INTERVAL 2 MONTH)), net, 0)), 2) AS delta
FROM m
GROUP BY service
ORDER BY ABS(delta) DESC
LIMIT 20;
```

Both months are complete calendar months, so no finalization-lag exclusion is needed.

______________________________________________________________________

<a id="q3"></a>

## Q3 — MoM net by project ("which projects are increasing")

Same shape as Q2 with `project.name AS project`.

```sql
WITH m AS (
  SELECT
    project.name AS project,
    FORMAT_TIMESTAMP('%Y-%m', usage_start_time) AS mo,
    SUM(cost) + SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)) AS net
  FROM `databricks-apolloio.billing_export.gcp_billing_export_v1_0174D0_6590F0_824CC0`
  WHERE DATE(usage_start_time) >= DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 2 MONTH), MONTH)
    AND DATE(usage_start_time) <  DATE_TRUNC(CURRENT_DATE(), MONTH)
  GROUP BY project, mo
)
SELECT
  project,
  ROUND(SUM(IF(mo = FORMAT_DATE('%Y-%m', DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH)), net, 0)), 2) AS last_mo,
  ROUND(SUM(IF(mo = FORMAT_DATE('%Y-%m', DATE_SUB(CURRENT_DATE(), INTERVAL 2 MONTH)), net, 0)), 2) AS prior_mo,
  ROUND(SUM(IF(mo = FORMAT_DATE('%Y-%m', DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH)), net, 0))
      - SUM(IF(mo = FORMAT_DATE('%Y-%m', DATE_SUB(CURRENT_DATE(), INTERVAL 2 MONTH)), net, 0)), 2) AS delta
FROM m
GROUP BY project
ORDER BY ABS(delta) DESC
LIMIT 15;
```

**Verified output (Aug vs Jul 2026), net:**

| project | last_mo | prior_mo | delta |
| --- | --- | --- | --- |
| production | $1,092,180 | $1,006,656 | +$85,524 |
| data-platform-production | $439,566 | $251,581 | **+$187,985 (+74.7%)** |
| devops | $117,021 | $107,841 | +$9,180 |
| staging | $102,966 | $104,025 | -$1,059 |
| data-platform-stg | $58,250 | $46,736 | +$11,514 |

Note `data-platform-production` is the *largest* mover in dollar terms despite `production` being
4× its size — exactly the case ranking by dollar delta rather than percent is designed to surface.

A `NULL` project row is normal: billing-account-level charges not attributable to a project. Do not
treat it as a data error.

______________________________________________________________________

<a id="q4"></a>

## Q4 — MoM net by service + SKU (names the driver)

```sql
WITH m AS (
  SELECT
    service.description AS svc,
    sku.description AS sku,
    FORMAT_TIMESTAMP('%Y-%m', usage_start_time) AS mo,
    SUM(cost) + SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)) AS net
  FROM `databricks-apolloio.billing_export.gcp_billing_export_v1_0174D0_6590F0_824CC0`
  WHERE DATE(usage_start_time) >= DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 2 MONTH), MONTH)
    AND DATE(usage_start_time) <  DATE_TRUNC(CURRENT_DATE(), MONTH)
  GROUP BY svc, sku, mo
)
SELECT
  svc, sku,
  ROUND(SUM(IF(mo = FORMAT_DATE('%Y-%m', DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH)), net, 0)), 2) AS last_mo,
  ROUND(SUM(IF(mo = FORMAT_DATE('%Y-%m', DATE_SUB(CURRENT_DATE(), INTERVAL 2 MONTH)), net, 0)), 2) AS prior_mo,
  ROUND(SUM(IF(mo = FORMAT_DATE('%Y-%m', DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH)), net, 0))
      - SUM(IF(mo = FORMAT_DATE('%Y-%m', DATE_SUB(CURRENT_DATE(), INTERVAL 2 MONTH)), net, 0)), 2) AS delta
FROM m
GROUP BY svc, sku
ORDER BY ABS(delta) DESC
LIMIT 20;
```

**Verified top movers (Aug vs Jul 2026):**

| svc | sku | last_mo | prior_mo | delta |
| --- | --- | --- | --- | --- |
| Claude Sonnet 4.6 | Input Cache Write Tokens (TTL 3600s) | $69,217 | $1,169 | **+$68,047** |
| Claude Sonnet 4.6 | Input Cache Write Tokens (TTL 300s) | $199,371 | $139,997 | +$59,374 |
| Claude Sonnet 4.6 | Input Cache Read Tokens | $92,862 | $44,366 | +$48,496 |
| Compute Engine | C3D Instance Core running in Americas | $56,489 | $30,372 | +$26,117 |
| Compute Engine | SSD backed PD Capacity | $379,865 | $355,010 | +$24,854 |
| Claude Sonnet 4.6 | Output Tokens | $44,353 | $23,200 | +$21,152 |

The TTL-3600s cache-write row going from ~$1.2K to ~$69K in one month is the clearest single
fingerprint of the INFRA-2173 AI-agent rollout.

______________________________________________________________________

<a id="q5"></a>

## Q5 — Week-over-week by service (anomaly detection)

Compares the last complete 7 days against the 7 before, excluding the unfinalized 2-day tail.

```sql
WITH d AS (
  SELECT
    service.description AS service,
    DATE(usage_start_time) AS dt,
    SUM(cost) + SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)) AS net
  FROM `databricks-apolloio.billing_export.gcp_billing_export_v1_0174D0_6590F0_824CC0`
  WHERE DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 15 DAY)
    AND DATE(usage_start_time) <  DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
  GROUP BY service, dt
)
SELECT
  service,
  ROUND(SUM(IF(dt >= DATE_SUB(CURRENT_DATE(), INTERVAL 8 DAY), net, 0)), 2) AS cur_week,
  ROUND(SUM(IF(dt <  DATE_SUB(CURRENT_DATE(), INTERVAL 8 DAY), net, 0)), 2) AS prev_week,
  ROUND(SAFE_DIVIDE(
    SUM(IF(dt >= DATE_SUB(CURRENT_DATE(), INTERVAL 8 DAY), net, 0))
      - SUM(IF(dt < DATE_SUB(CURRENT_DATE(), INTERVAL 8 DAY), net, 0)),
    NULLIF(SUM(IF(dt < DATE_SUB(CURRENT_DATE(), INTERVAL 8 DAY), net, 0)), 0)) * 100, 1) AS pct_change
FROM d
GROUP BY service
HAVING ABS(cur_week - prev_week) > 500
ORDER BY (cur_week - prev_week) DESC
LIMIT 20;
```

**Verified output (run 2026-09-05):**

| service | cur_week | prev_week | pct_change |
| --- | --- | --- | --- |
| Claude Sonnet 4.6 | $114,391 | $100,493 | +13.8% |
| Compute Engine | $299,366 | $293,827 | +1.9% |

Alert rule: **absolute delta > $500/week AND `ABS(pct_change)` > 15%**. Neither row above clears the
percent floor — correctly reported as "no anomalies above threshold" for that week.

______________________________________________________________________

<a id="q6"></a>

## Q6 — Week-over-week by project

Identical to Q5, substituting `project.name AS project` for the service column and grouping by
`project`. Use a lower dollar floor (`> 250`) since project-level noise is smaller.

```sql
WITH d AS (
  SELECT
    project.name AS project,
    DATE(usage_start_time) AS dt,
    SUM(cost) + SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)) AS net
  FROM `databricks-apolloio.billing_export.gcp_billing_export_v1_0174D0_6590F0_824CC0`
  WHERE DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 15 DAY)
    AND DATE(usage_start_time) <  DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
  GROUP BY project, dt
)
SELECT
  project,
  ROUND(SUM(IF(dt >= DATE_SUB(CURRENT_DATE(), INTERVAL 8 DAY), net, 0)), 2) AS cur_week,
  ROUND(SUM(IF(dt <  DATE_SUB(CURRENT_DATE(), INTERVAL 8 DAY), net, 0)), 2) AS prev_week,
  ROUND(SAFE_DIVIDE(
    SUM(IF(dt >= DATE_SUB(CURRENT_DATE(), INTERVAL 8 DAY), net, 0))
      - SUM(IF(dt < DATE_SUB(CURRENT_DATE(), INTERVAL 8 DAY), net, 0)),
    NULLIF(SUM(IF(dt < DATE_SUB(CURRENT_DATE(), INTERVAL 8 DAY), net, 0)), 0)) * 100, 1) AS pct_change
FROM d
GROUP BY project
HAVING ABS(cur_week - prev_week) > 250
ORDER BY (cur_week - prev_week) DESC
LIMIT 20;
```

______________________________________________________________________

<a id="q7"></a>

## Q7 — Daily net trend for a specific service (plateau vs spike)

Builds on Notion query (d), converted to net.

```sql
SELECT
  DATE(usage_start_time) AS usage_date,
  ROUND(SUM(cost) + SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)), 2) AS net_cost
FROM `databricks-apolloio.billing_export.gcp_billing_export_v1_0174D0_6590F0_824CC0`
WHERE service.description = '<SERVICE_NAME>'
  AND DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 60 DAY)
  AND DATE(usage_start_time) <  DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
GROUP BY usage_date
ORDER BY usage_date;
```

A **new plateau** (steps up and stays) means a shipped change and is what matters. A **single spike**
that returns to baseline is usually a backfill or batch job. Report the distinction explicitly — it
determines whether the finding is structural or transient.

Add `AND project.name = '<PROJECT>'` to isolate a project.

______________________________________________________________________

<a id="q8"></a>

## Q8 — Credits by type (commitment pulse)

**Not run by this skill.** Step 6 hands commitment coverage to `gcp-commitment-review`; this
query is kept only as schema reference for that skill's authors.

Notion query (f), scoped to recent months. Safe to use the top-level `UNNEST` join here because
`cost` is never selected in the same query.

```sql
SELECT
  FORMAT_TIMESTAMP('%Y-%m', usage_start_time) AS month,
  credit.type AS credit_type,
  credit.name AS credit_name,
  ROUND(SUM(credit.amount), 2) AS credit_usd
FROM `databricks-apolloio.billing_export.gcp_billing_export_v1_0174D0_6590F0_824CC0`,
     UNNEST(credits) AS credit
WHERE DATE(usage_start_time) >= DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 4 MONTH), MONTH)
GROUP BY month, credit_type, credit_name
ORDER BY month, credit_usd;
```

`credit_usd` is negative — that is the discount, not an error. Watch
`COMMITTED_USAGE_DISCOUNT` specifically. If it flattens while Compute Engine gross rises,
commitment coverage is falling behind → hand off to `gcp-commitment-review`.

______________________________________________________________________

<a id="q9"></a>

## Q9 — AI / LLM spend by service

```sql
SELECT
  FORMAT_TIMESTAMP('%Y-%m', usage_start_time) AS month,
  service.description AS service,
  ROUND(SUM(cost) + SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)), 2) AS net_cost
FROM `databricks-apolloio.billing_export.gcp_billing_export_v1_0174D0_6590F0_824CC0`
WHERE DATE(usage_start_time) >= DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 3 MONTH), MONTH)
  AND DATE(usage_start_time) < DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
  AND REGEXP_CONTAINS(LOWER(service.description), r'claude|vertex|gemini|anthropic')
GROUP BY month, service
ORDER BY month, net_cost DESC;
```

**Verified matched services (60-day net, run 2026-09-05):**

| service | net |
| --- | --- |
| Claude Sonnet 4.6 | $708,018 |
| Claude Sonnet 4.5 | $9,870 |
| Claude Haiku 4.5 | $9,047 |
| Vertex AI | $6,516 |
| Gemini API | $154 |
| Claude Sonnet 5 | $1.05 |
| Claude Sonnet 4 | $1.01 |

The regex is deliberately broad so new model SKUs appear automatically. **Review the matched list
each run** — a new model name appearing is itself a signal (migration, or a team adopting a new
model). Do not narrow the regex to an allowlist of known names.

To express AI spend as a share of total, divide by the Q1 net for the same month.

______________________________________________________________________

<a id="q10"></a>

## Q10 — AI token-type split (highest-leverage AI signal)

```sql
SELECT
  FORMAT_TIMESTAMP('%Y-%m', usage_start_time) AS month,
  CASE
    WHEN LOWER(sku.description) LIKE '%cache write%' THEN 'cache_write'
    WHEN LOWER(sku.description) LIKE '%cache read%'  THEN 'cache_read'
    WHEN LOWER(sku.description) LIKE '%output token%' THEN 'output'
    WHEN LOWER(sku.description) LIKE '%input token%'  THEN 'input'
    ELSE 'other'
  END AS token_type,
  ROUND(SUM(cost) + SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)), 2) AS net_cost
FROM `databricks-apolloio.billing_export.gcp_billing_export_v1_0174D0_6590F0_824CC0`
WHERE DATE(usage_start_time) >= DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 3 MONTH), MONTH)
  AND DATE(usage_start_time) < DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
  AND REGEXP_CONTAINS(LOWER(service.description), r'claude|vertex|gemini|anthropic')
GROUP BY month, token_type
ORDER BY month, net_cost DESC;
```

**How to read it:** cache-write growing much faster than cache-read means the prompt cache is being
paid for but not hit — an application-side fix (cache key stability, TTL choice), not a capacity
problem. Healthy caching shows cache-read >> cache-write. Aug 2026 showed the opposite.

______________________________________________________________________

<a id="q11"></a>

## Q11 — Label coverage (governance)

```sql
SELECT
  FORMAT_TIMESTAMP('%Y-%m', usage_start_time) AS month,
  ROUND(SUM(IF(ARRAY_LENGTH(labels) > 0, cost, 0)) / NULLIF(SUM(cost), 0) * 100, 1) AS pct_cost_labeled
FROM `databricks-apolloio.billing_export.gcp_billing_export_v1_0174D0_6590F0_824CC0`
WHERE DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 150 DAY)
  AND DATE(usage_start_time) < DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
GROUP BY month
ORDER BY month;
```

**Verified trend (run 2026-09-05):**

| month | pct_cost_labeled |
| --- | --- |
| 2026-05 | 86.6% |
| 2026-06 | 85.0% |
| 2026-07 | 81.8% |
| 2026-08 | 76.8% |
| 2026-09 (MTD) | 71.2% |

**Degrading ~4pp/month.** Weighted by cost, not row count, so it reflects dollars that cannot be
attributed to a team. Report any MoM drop > 3pp as a finding. Note the Notion doc's caveat: some of
this is label *propagation* into the export rather than genuinely unlabeled resources — so treat it
as "attribution blindness" rather than "someone forgot a label", and confirm against
`gcloud compute instances list --format="value(labels)"` before blaming a team.

Uses gross `cost` deliberately: the question is what share of billed usage is attributable, and
credits do not carry labels.

______________________________________________________________________

<a id="q12"></a>

## Q12 — MoM net by infra_workload × infra_cluster × project (workload attribution)

Label access pattern for a repeated `RECORD` field — pulls one key's value out of the `labels`
array:

```sql
(SELECT l.value FROM UNNEST(labels) l WHERE l.key = 'infra_workload' LIMIT 1)
```

```sql
WITH m AS (
  SELECT
    IFNULL(
      (SELECT l.value FROM UNNEST(labels) l WHERE l.key = 'infra_workload' LIMIT 1),
      '(unlabeled)'
    ) AS infra_workload,
    (SELECT l.value FROM UNNEST(labels) l WHERE l.key = 'infra_cluster' LIMIT 1) AS infra_cluster,
    project.name AS project,
    FORMAT_TIMESTAMP('%Y-%m', usage_start_time) AS mo,
    SUM(cost) + SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)) AS net
  FROM `databricks-apolloio.billing_export.gcp_billing_export_v1_0174D0_6590F0_824CC0`
  WHERE DATE(usage_start_time) >= DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 2 MONTH), MONTH)
    AND DATE(usage_start_time) <  DATE_TRUNC(CURRENT_DATE(), MONTH)
    -- AND (SELECT l.value FROM UNNEST(labels) l WHERE l.key = 'infra_workload' LIMIT 1) = '<WORKLOAD>'
    -- AND (SELECT l.value FROM UNNEST(labels) l WHERE l.key = 'infra_cluster' LIMIT 1) = '<CLUSTER>'
  GROUP BY infra_workload, infra_cluster, project, mo
)
SELECT
  infra_workload,
  infra_cluster,
  project,
  ROUND(SUM(IF(mo = FORMAT_DATE('%Y-%m', DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH)), net, 0)), 2) AS last_mo,
  ROUND(SUM(IF(mo = FORMAT_DATE('%Y-%m', DATE_SUB(CURRENT_DATE(), INTERVAL 2 MONTH)), net, 0)), 2) AS prior_mo,
  ROUND(SUM(IF(mo = FORMAT_DATE('%Y-%m', DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH)), net, 0))
      - SUM(IF(mo = FORMAT_DATE('%Y-%m', DATE_SUB(CURRENT_DATE(), INTERVAL 2 MONTH)), net, 0)), 2) AS delta
FROM m
GROUP BY infra_workload, infra_cluster, project
ORDER BY ABS(delta) DESC
LIMIT 30;
```

`(unlabeled)` is a first-class row, not a dropped one — a large or growing `(unlabeled)` net_cost is
itself the finding (see Step 9a label-coverage governance). `infra_cluster` is left `NULL` rather
than coalesced, since an unlabeled cluster under a labeled workload is a narrower gap than an
unlabeled workload.

**Verified output (Aug vs Jul 2026), net:**

| infra_workload | infra_cluster | project | last_mo | prior_mo | delta |
| --- | --- | --- | --- | --- | --- |
| (unlabeled) | | data-platform-production | $439,566 | $251,581 | +$187,986 |
| elasticsearch | main-v1 | production | $122,301 | $93,930 | +$28,372 |
| (unlabeled) | | production | $514,868 | $492,164 | +$22,704 |
| gke | production | production | $143,201 | $131,186 | +$12,015 |
| mongo | main | production | $137,635 | $129,206 | +$8,430 |
| gke | ops | devops | $71,520 | $66,358 | +$5,162 |

The unlabeled `production` row is mostly persistent disk (no infra labels); the unlabeled
`data-platform-production` row is Claude on Vertex.

See [Q18](#q18) for the disk-label gap detail.

______________________________________________________________________

<a id="q13"></a>

## Q13 — WoW net by infra_workload (workload anomaly detection)

Same shape as [Q5](#q5), grouped by `infra_workload` instead of service.

```sql
WITH d AS (
  SELECT
    IFNULL(
      (SELECT l.value FROM UNNEST(labels) l WHERE l.key = 'infra_workload' LIMIT 1),
      '(unlabeled)'
    ) AS infra_workload,
    DATE(usage_start_time) AS dt,
    SUM(cost) + SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)) AS net
  FROM `databricks-apolloio.billing_export.gcp_billing_export_v1_0174D0_6590F0_824CC0`
  WHERE DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 15 DAY)
    AND DATE(usage_start_time) <  DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
  GROUP BY infra_workload, dt
)
SELECT
  infra_workload,
  ROUND(SUM(IF(dt >= DATE_SUB(CURRENT_DATE(), INTERVAL 8 DAY), net, 0)), 2) AS cur_week,
  ROUND(SUM(IF(dt <  DATE_SUB(CURRENT_DATE(), INTERVAL 8 DAY), net, 0)), 2) AS prev_week,
  ROUND(SAFE_DIVIDE(
    SUM(IF(dt >= DATE_SUB(CURRENT_DATE(), INTERVAL 8 DAY), net, 0))
      - SUM(IF(dt < DATE_SUB(CURRENT_DATE(), INTERVAL 8 DAY), net, 0)),
    NULLIF(SUM(IF(dt < DATE_SUB(CURRENT_DATE(), INTERVAL 8 DAY), net, 0)), 0)) * 100, 1) AS pct_change
FROM d
GROUP BY infra_workload
ORDER BY (cur_week - prev_week) DESC;
```

**Flag rule differs from Q5/Q6:** relative change > **20%** **AND** absolute delta > **$2,000**/week
(both must hold), not Q5's 15%/$500. Workload totals are coarser-grained than per-service rows, so
the noise floor is higher. Use `scripts/workload_report.py`'s `flag_wow(rows, pct=0.20, usd=2000.0)`
rather than reimplementing the threshold check by hand.

**Verified output (run 2026-09-14, `workload=mongo/main`), net:**

| infra_workload | cur_week | prev_week |
| --- | --- | --- |
| mongo | $73,058 | $73,367 |

No flag: under both the 20% relative and $2,000 absolute thresholds.

______________________________________________________________________

<a id="q18"></a>

## Q18 — Per-workload cost decomposition (workload=given only)

Splits one workload's net cost into resource categories via `sku.description` pattern matching, 8
weekly points. Only runs when `workload=` is given (Step 2c).

```sql
SELECT
  DATE_TRUNC(DATE(usage_start_time), WEEK(MONDAY)) AS week_start,
  CASE
    WHEN LOWER(sku.description) LIKE 'commitment v1:%'        THEN 'commitments'
    WHEN LOWER(sku.description) LIKE '%core running%'
      OR LOWER(sku.description) LIKE '%instance core%'        THEN 'cores'
    WHEN LOWER(sku.description) LIKE '%ram running%'
      OR LOWER(sku.description) LIKE '%instance ram%'         THEN 'ram'
    WHEN LOWER(sku.description) LIKE '%ssd backed pd%'        THEN 'pd-ssd'
    WHEN LOWER(sku.description) LIKE '%balanced pd%'          THEN 'pd-balanced'
    WHEN LOWER(sku.description) LIKE '%snapshot%'             THEN 'snapshots'
    WHEN LOWER(sku.description) LIKE '%nat gateway%'
      OR LOWER(sku.description) LIKE '%cloud nat%'            THEN 'nat'
    WHEN LOWER(sku.description) LIKE '%network egress%'
      OR LOWER(sku.description) LIKE '%download worldwide destinations%'
      OR LOWER(sku.description) LIKE '%egress%'               THEN 'egress'
    ELSE 'other'
  END AS category,
  ROUND(SUM(cost) + SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)), 2) AS net_cost
FROM `databricks-apolloio.billing_export.gcp_billing_export_v1_0174D0_6590F0_824CC0`
WHERE DATE(usage_start_time) >= DATE_SUB(DATE_TRUNC(CURRENT_DATE(), WEEK(MONDAY)), INTERVAL 8 WEEK)
  AND DATE(usage_start_time) <  DATE_TRUNC(CURRENT_DATE(), WEEK(MONDAY))
  AND (SELECT l.value FROM UNNEST(labels) l WHERE l.key = 'infra_workload' LIMIT 1) = '<WORKLOAD>'
  -- AND (SELECT l.value FROM UNNEST(labels) l WHERE l.key = 'infra_cluster' LIMIT 1) = '<CLUSTER>'
GROUP BY week_start, category
ORDER BY week_start, category;
```

Bounds are 8 complete Monday-to-Sunday weeks, the current partial week excluded: the upper bound
truncates to the most recent Monday before today, and the lower bound steps back 8 weeks from
there. `sku.description` patterns are approximate (no `sku.category` field exists — same caveat as
Q4/Step 4); an `other` bucket that grows unexpectedly means a pattern needs updating, not that the
cost vanished. Cross check `pd-ssd`/`pd-balanced` against
provisioned GB from `gcloud compute disks list` (Step 2c: anchored name prefix, only with `/cluster`, approximate).

**Verified output (run 2026-09-14, `workload=mongo/main`, 4 of 8 weeks shown), net:**

| week_start | commitments | cores | ram |
| --- | --- | --- | --- |
| 2026-07-20 | $30,728 | $363 | $19 |
| 2026-08-03 | $30,726 | $382 | $16 |
| 2026-08-17 | $30,830 | $220 | $5 |
| 2026-08-24 | ~$30,800 | $267 | small |

Two things this run proved. First, **3-year CUD charges carry the instance labels**, so commitment
cost attributes cleanly per workload; that is why `commitments` is its own category and why it
dominates a committed workload like mongo/main. Second, **persistent disks are not labeled with
`infra_workload` or `infra_cluster`**: no PD, snapshot, or disk SKU appears for mongo/main at all,
so `pd-ssd`, `pd-balanced`, and `snapshots` read zero for every workload today. That is a labeling
gap, not a saving. Report it as such, and get disk GB from `gcloud compute disks list` with a
name-pattern filter until the disk labels are backfilled (see Step 2c).

______________________________________________________________________

<a id="q14"></a>

## Q14 — GKE net by namespace and team label (requires GKE cost allocation)

**Not yet verified against production.** As of 2026-09-14 GKE cost allocation is not enabled on the
production cluster (INFRA-2186, devops PRs #4071 / #4072), so the export carries no `k8s-namespace`
or `k8s-label/*` keys and this query returns only `(unlabeled)`. Check
`costManagementConfig.enabled` first (SKILL.md Step 2d). Once enabled, confirm the exact key
spelling before trusting the team split:

```sql
SELECT DISTINCT l.key
FROM `databricks-apolloio.billing_export.gcp_billing_export_v1_0174D0_6590F0_824CC0`, UNNEST(labels) l
WHERE l.key LIKE 'k8s-%'
  AND DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY);
```

Then:

```sql
WITH m AS (
  SELECT
    IFNULL((SELECT l.value FROM UNNEST(labels) l WHERE l.key = 'k8s-namespace' LIMIT 1), '(unlabeled)') AS namespace,
    IFNULL((SELECT l.value FROM UNNEST(labels) l WHERE l.key = 'k8s-label/app.kubernetes.io/area' LIMIT 1), '(unlabeled)') AS team,
    FORMAT_TIMESTAMP('%Y-%m', usage_start_time) AS mo,
    SUM(cost) + SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)) AS net
  FROM `databricks-apolloio.billing_export.gcp_billing_export_v1_0174D0_6590F0_824CC0`
  WHERE DATE(usage_start_time) >= DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 2 MONTH), MONTH)
    AND DATE(usage_start_time) <  DATE_TRUNC(CURRENT_DATE(), MONTH)
    AND (SELECT l.value FROM UNNEST(labels) l WHERE l.key = 'infra_workload' LIMIT 1) = 'gke'
  GROUP BY namespace, team, mo
)
SELECT
  namespace, team,
  ROUND(SUM(IF(mo = FORMAT_DATE('%Y-%m', DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH)), net, 0)), 2) AS last_mo,
  ROUND(SUM(IF(mo = FORMAT_DATE('%Y-%m', DATE_SUB(CURRENT_DATE(), INTERVAL 2 MONTH)), net, 0)), 2) AS prior_mo,
  ROUND(SUM(IF(mo = FORMAT_DATE('%Y-%m', DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH)), net, 0))
      - SUM(IF(mo = FORMAT_DATE('%Y-%m', DATE_SUB(CURRENT_DATE(), INTERVAL 2 MONTH)), net, 0)), 2) AS delta
FROM m
GROUP BY namespace, team
ORDER BY ABS(delta) DESC
LIMIT 20;
```

Cost allocation splits a node's cost across pods by **resource requests**, not usage, and only for
usage after the day it was enabled. A team whose Sidekiq workers request far more CPU than they use
will look expensive here; that is the right-sizing finding, not a billing error. Sidekiq workers all
share the `leadgenie` namespace, so `namespace` alone gives "Sidekiq + web total"; the `team` label
is what splits it. Workers whose queue has no owner in `cluster-owners.yaml` land under
`be-platform` by chart default, so a large `be-platform` row is partly an ownership gap.

______________________________________________________________________

## Per-project drill-down

Add to any query above:

```sql
AND project.name = 'production'   -- BQ uses the NAME, not the project ID
```

Name → ID mapping is in SKILL.md. Mixing them up produces a silent empty result, not an error.
