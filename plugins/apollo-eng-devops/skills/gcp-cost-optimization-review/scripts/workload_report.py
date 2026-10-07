"""workload_report.py — pure helpers for gcp-cost-optimization-review's
`workload=` argument (Step 2b/2c workload attribution and decomposition).

All logic that can be pure lives here as module-level functions so it is
testable without GCP: argument parsing, SQL string building, the WoW anomaly
threshold check, and markdown rendering. The skill (an LLM following
SKILL.md) is expected to run the built SQL via `bq query` itself and feed
the resulting CSV back through `render_markdown`; this module never shells
out to `bq` or `gcloud`.

Reuses the net-cost expression and table name verified in
references/bq-queries.md verbatim — do not drift these two copies apart.

Python 3.9 compatible (see repo CLAUDE.md Testing convention).
"""
from __future__ import annotations

import csv
import sys
from typing import Any, Dict, List, Optional

BILLING_TABLE = (
    "databricks-apolloio.billing_export.gcp_billing_export_v1_0174D0_6590F0_824CC0"
)

# The net-cost expression from references/bq-queries.md — copied verbatim.
NET_COST_EXPR = (
    "SUM(cost) + SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0))"
)

WORKLOAD_LABEL_EXPR = (
    "(SELECT l.value FROM UNNEST(labels) l WHERE l.key = 'infra_workload' LIMIT 1)"
)
CLUSTER_LABEL_EXPR = (
    "(SELECT l.value FROM UNNEST(labels) l WHERE l.key = 'infra_cluster' LIMIT 1)"
)

# Valid label vocabulary, from terraform (2026-09). Unknown values warn and
# continue unscoped rather than failing — see parse_args().
VALID_WORKLOADS = frozenset(
    {"elasticsearch", "gke", "mail-server", "mongo", "pritunl", "redis"}
)
VALID_CLUSTERS = frozenset(
    {
        "accounts",
        "activities-v1",
        "agent-platform",
        "ai-tooling",
        "contacts",
        "custom-objects",
        "custom-objects-v1",
        "email",
        "emailermessages",
        "es8-activities",
        "es8-custom-objects",
        "es8-field-enrichment",
        "es8-main",
        "field-enrichment-v1",
        "kafka-connect",
        "leadgenie-web",
        "main",
        "main-v1",
        "mongo-pritunl",
        "noncustomer",
        "ops",
        "pocus-udm-mongo",
        "pritunl",
        "production",
        "ratelimiter",
        "redis-db",
        "staging",
        "staging-dualstack",
        "staging-sandbox",
        "va-mongo",
        "va-mongo-canary",
    }
)

DEFAULT_WEEKS = 8
DEFAULT_MONTHS = 2
DEFAULT_WOW_PCT = 0.20
DEFAULT_WOW_USD = 2000.0


def parse_args(argv: List[str]) -> Dict[str, Any]:
    """Parse the skill's bare-word argument style into a plain dict.

    Recognized tokens: `html`, `weeks=N`, `workload=<w>[/<c>]`, `commitments`,
    `install-bq`. Unrecognized tokens are collected under "unknown" rather
    than raising — this mirrors the skill's "warn, never fail" contract.
    An unknown workload or cluster value produces a warning string in
    "warnings" but is still recorded, so a caller can decide whether to run
    unscoped.
    """
    result: Dict[str, Any] = {
        "html": False,
        "weeks": DEFAULT_WEEKS,
        "workload": None,
        "cluster": None,
        "commitments": False,
        "install_bq": False,
        "warnings": [],
        "unknown": [],
    }

    for token in argv:
        if token == "html":
            result["html"] = True
        elif token == "commitments":
            result["commitments"] = True
        elif token == "install-bq":
            result["install_bq"] = True
        elif token.startswith("weeks="):
            raw = token[len("weeks=") :]
            try:
                weeks = int(raw)
            except ValueError:
                result["warnings"].append(
                    "weeks='{0}' is not an integer; using default {1}.".format(
                        raw, DEFAULT_WEEKS
                    )
                )
                continue
            if weeks <= 0:
                result["warnings"].append(
                    "weeks={0} is not positive; using default {1}.".format(
                        weeks, DEFAULT_WEEKS
                    )
                )
                continue
            result["weeks"] = weeks
        elif token.startswith("workload="):
            raw = token[len("workload=") :]
            if "/" in raw:
                workload, cluster = raw.split("/", 1)
            else:
                workload, cluster = raw, None

            if workload not in VALID_WORKLOADS:
                result["warnings"].append(
                    "Unknown workload '{0}' — not in {1}. Continuing unscoped "
                    "rather than failing.".format(
                        workload, sorted(VALID_WORKLOADS)
                    )
                )
                # Contract (SKILL.md Step 2b): an unknown value continues
                # *unscoped*. Keeping it as a filter would silently return an
                # empty report instead.
                workload = None
                cluster = None
            elif cluster is not None and cluster not in VALID_CLUSTERS:
                result["warnings"].append(
                    "Unknown cluster '{0}' for workload '{1}' — not in the known "
                    "31-cluster vocabulary. Continuing without the cluster filter.".format(
                        cluster, workload
                    )
                )
                cluster = None

            result["workload"] = workload
            result["cluster"] = cluster
        else:
            result["unknown"].append(token)
            result["warnings"].append(
                "Unrecognized argument '{0}' — ignored.".format(token)
            )

    return result


def _sql_string_literal(value: str) -> str:
    """Quote a value as a BigQuery string literal, escaping backslashes and
    single quotes. parse_args() already drops unknown label values, but the
    builders are importable on their own — never interpolate a raw string
    into SQL."""
    escaped = value.replace("\\", "\\\\").replace("'", "\\'")
    return "'{0}'".format(escaped)


def _workload_filter_clause(
    workload: Optional[str], cluster: Optional[str] = None
) -> str:
    """Build the optional AND-clause fragment scoping a query to one
    workload (and optionally one cluster). Empty string when unscoped."""
    clauses = []
    if workload:
        clauses.append(
            "{0} = {1}".format(WORKLOAD_LABEL_EXPR, _sql_string_literal(workload))
        )
    if cluster:
        clauses.append(
            "{0} = {1}".format(CLUSTER_LABEL_EXPR, _sql_string_literal(cluster))
        )
    if not clauses:
        return ""
    return "\n  AND " + "\n  AND ".join(clauses)


def build_q12_sql(
    workload: Optional[str] = None,
    cluster: Optional[str] = None,
    months: int = DEFAULT_MONTHS,
) -> str:
    """Q12 — MoM net by infra_workload x infra_cluster x project, with a
    first-class (unlabeled) row. See references/bq-queries.md#q12."""
    scope = _workload_filter_clause(workload, cluster)
    return """WITH m AS (
  SELECT
    IFNULL({workload_expr}, '(unlabeled)') AS infra_workload,
    {cluster_expr} AS infra_cluster,
    project.name AS project,
    FORMAT_TIMESTAMP('%Y-%m', usage_start_time) AS mo,
    {net_expr} AS net
  FROM `{table}`
  WHERE DATE(usage_start_time) >= DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL {months} MONTH), MONTH)
    AND DATE(usage_start_time) <  DATE_TRUNC(CURRENT_DATE(), MONTH){scope}
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
LIMIT 30;""".format(
        workload_expr=WORKLOAD_LABEL_EXPR,
        cluster_expr=CLUSTER_LABEL_EXPR,
        net_expr=NET_COST_EXPR,
        table=BILLING_TABLE,
        months=months,
        scope=scope,
    )


def build_q13_sql(workload: Optional[str] = None) -> str:
    """Q13 — WoW net by infra_workload. See references/bq-queries.md#q13.

    Flag threshold (pct > 0.20 AND usd > 2000) is applied by flag_wow() on
    the resulting rows, not baked into this SQL.
    """
    scope = _workload_filter_clause(workload)
    return """WITH d AS (
  SELECT
    IFNULL({workload_expr}, '(unlabeled)') AS infra_workload,
    DATE(usage_start_time) AS dt,
    {net_expr} AS net
  FROM `{table}`
  WHERE DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 15 DAY)
    AND DATE(usage_start_time) <  DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY){scope}
  GROUP BY infra_workload, dt
)
SELECT
  infra_workload,
  ROUND(SUM(IF(dt >= DATE_SUB(CURRENT_DATE(), INTERVAL 8 DAY), net, 0)), 2) AS cur_week,
  ROUND(SUM(IF(dt <  DATE_SUB(CURRENT_DATE(), INTERVAL 8 DAY), net, 0)), 2) AS prev_week
FROM d
GROUP BY infra_workload
ORDER BY (cur_week - prev_week) DESC;""".format(
        workload_expr=WORKLOAD_LABEL_EXPR,
        net_expr=NET_COST_EXPR,
        table=BILLING_TABLE,
        scope=scope,
    )


_Q18_CATEGORY_CASE = """  CASE
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
  END AS category"""


def build_q18_sql(
    workload: str, cluster: Optional[str] = None, weeks: int = DEFAULT_WEEKS
) -> str:
    """Q18 — per-workload cost decomposition into cores/RAM/disk/snapshots/
    NAT/egress, over `weeks` weekly points. See references/bq-queries.md#q18.

    `workload` is required (Step 2c only runs when `workload=` was given).
    """
    if not workload:
        raise ValueError("build_q18_sql requires a workload — Step 2c is workload-scoped only.")
    scope = _workload_filter_clause(workload, cluster)
    return """SELECT
  DATE_TRUNC(DATE(usage_start_time), WEEK(MONDAY)) AS week_start,
{category_case},
  ROUND({net_expr}, 2) AS net_cost
FROM `{table}`
WHERE DATE(usage_start_time) >= DATE_SUB(DATE_TRUNC(CURRENT_DATE(), WEEK(MONDAY)), INTERVAL {weeks} WEEK)
  AND DATE(usage_start_time) <  DATE_TRUNC(CURRENT_DATE(), WEEK(MONDAY)){scope}
GROUP BY week_start, category
ORDER BY week_start, category;""".format(
        category_case=_Q18_CATEGORY_CASE,
        net_expr=NET_COST_EXPR,
        table=BILLING_TABLE,
        weeks=weeks,
        scope=scope,
    )


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def flag_wow(
    rows: List[Dict[str, Any]],
    pct: float = DEFAULT_WOW_PCT,
    usd: float = DEFAULT_WOW_USD,
) -> List[Dict[str, Any]]:
    """Filter WoW rows (as produced by Q13: cur_week/prev_week per row) down
    to anomalies where BOTH conditions hold: relative change > `pct` AND
    absolute delta > `usd`. Returns each flagged row augmented with "delta"
    and "pct_change" (pct_change is None when prev_week is 0 and cur_week is
    also 0 — no meaningful change to report).

    When prev_week is 0 and cur_week is nonzero, the relative-change
    condition is treated as satisfied (a move from zero is unbounded percent
    growth) — the dollar floor still has to clear on its own.
    """
    flagged: List[Dict[str, Any]] = []
    for row in rows:
        cur = _to_float(row.get("cur_week"))
        prev = _to_float(row.get("prev_week"))
        delta = cur - prev

        if prev == 0.0:
            pct_change: Optional[float] = None
            pct_ok = cur != 0.0
        else:
            pct_change = abs(delta) / abs(prev)
            pct_ok = pct_change > pct

        usd_ok = abs(delta) > usd

        if pct_ok and usd_ok:
            out = dict(row)
            out["delta"] = round(delta, 2)
            out["pct_change"] = (
                round(pct_change * 100, 1) if pct_change is not None else None
            )
            flagged.append(out)

    return flagged


def render_markdown(section_title: str, rows: List[Dict[str, Any]]) -> str:
    """Render a list of flat dict rows as a markdown table under an H3
    heading. Column order follows the first row's key insertion order.
    Renders "No rows." when the list is empty rather than an empty table."""
    lines = ["### {0}".format(section_title), ""]

    if not rows:
        lines.append("No rows.")
        return "\n".join(lines)

    columns = list(rows[0].keys())
    lines.append("| " + " | ".join(columns) + " |")
    lines.append("| " + " | ".join("---" for _ in columns) + " |")
    for row in rows:
        cells = ["" if row.get(c) is None else str(row.get(c)) for c in columns]
        lines.append("| " + " | ".join(cells) + " |")

    return "\n".join(lines)


def _read_csv_rows(stream) -> List[Dict[str, Any]]:
    reader = csv.DictReader(stream)
    return [dict(row) for row in reader]


USAGE = (
    "usage: bq query ... --format=csv '<SQL>' | python workload_report.py "
    "[html] [weeks=N] [workload=<w>[/<c>]] [commitments]\n"
    "Reads bq CSV rows on stdin and renders a markdown section. --help prints this."
)


def main(argv: List[str]) -> int:
    if any(token in ("-h", "--help") for token in argv):
        print(USAGE)
        return 0
    args = parse_args(argv)
    for warning in args["warnings"]:
        print("WARN: {0}".format(warning), file=sys.stderr)

    rows = _read_csv_rows(sys.stdin)
    title = "workload={0}".format(args["workload"]) if args["workload"] else "all workloads"
    print(render_markdown(title, rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
