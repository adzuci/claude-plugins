"""Tests for workload_report.py — pure helpers backing the `workload=`
argument on gcp-cost-optimization-review (Step 2b/2c).

Runs on Python 3.9 and 3.11 (see repo CLAUDE.md Testing convention).
"""
from __future__ import annotations

import pytest

workload_report = pytest.importorskip("workload_report")


# ---------------------------------------------------------------------------
# parse_args
# ---------------------------------------------------------------------------


def test_parse_args_defaults_when_empty():
    args = workload_report.parse_args([])
    assert args["html"] is False
    assert args["weeks"] == workload_report.DEFAULT_WEEKS
    assert args["workload"] is None
    assert args["cluster"] is None
    assert args["commitments"] is False
    assert args["install_bq"] is False
    assert args["warnings"] == []


def test_parse_args_bare_words():
    args = workload_report.parse_args(["html", "commitments", "install-bq"])
    assert args["html"] is True
    assert args["commitments"] is True
    assert args["install_bq"] is True


def test_parse_args_weeks_override():
    args = workload_report.parse_args(["weeks=6"])
    assert args["weeks"] == 6


def test_parse_args_weeks_non_integer_warns_and_falls_back():
    args = workload_report.parse_args(["weeks=notanumber"])
    assert args["weeks"] == workload_report.DEFAULT_WEEKS
    assert any("weeks=" in w for w in args["warnings"])


def test_parse_args_weeks_non_positive_warns_and_falls_back():
    args = workload_report.parse_args(["weeks=0"])
    assert args["weeks"] == workload_report.DEFAULT_WEEKS
    assert args["warnings"]


def test_parse_args_workload_only():
    args = workload_report.parse_args(["workload=mongo"])
    assert args["workload"] == "mongo"
    assert args["cluster"] is None
    assert args["warnings"] == []


def test_parse_args_workload_and_cluster():
    args = workload_report.parse_args(["workload=mongo/main"])
    assert args["workload"] == "mongo"
    assert args["cluster"] == "main"
    assert args["warnings"] == []


def test_parse_args_unknown_workload_warns_and_continues_unscoped():
    # SKILL.md Step 2b: an unknown value warns and continues UNSCOPED. Keeping
    # it as a filter would silently produce an empty report.
    args = workload_report.parse_args(["workload=not-a-real-workload"])
    assert args["workload"] is None
    assert args["cluster"] is None
    assert len(args["warnings"]) == 1
    assert "Unknown workload" in args["warnings"][0]


def test_parse_args_unknown_workload_with_cluster_drops_both():
    args = workload_report.parse_args(["workload=not-a-real-workload/main"])
    assert args["workload"] is None
    assert args["cluster"] is None


def test_parse_args_unknown_cluster_keeps_workload_drops_cluster():
    args = workload_report.parse_args(["workload=mongo/not-a-real-cluster"])
    assert args["workload"] == "mongo"
    assert args["cluster"] is None
    assert len(args["warnings"]) == 1
    assert "Unknown cluster" in args["warnings"][0]


def test_parse_args_unrecognized_token_is_warned_not_fatal():
    args = workload_report.parse_args(["totally-unsupported"])
    assert "totally-unsupported" in args["unknown"]
    assert args["warnings"]


def test_parse_args_combo():
    args = workload_report.parse_args(["workload=redis/main", "weeks=4", "html"])
    assert args == {
        "html": True,
        "weeks": 4,
        "workload": "redis",
        "cluster": "main",
        "commitments": False,
        "install_bq": False,
        "warnings": [],
        "unknown": [],
    }


# ---------------------------------------------------------------------------
# SQL builders
# ---------------------------------------------------------------------------


def _assert_sql_shape(sql: str):
    assert workload_report.BILLING_TABLE in sql
    assert "infra_workload" in sql
    assert workload_report.NET_COST_EXPR in sql
    # The bq CLI flags are applied when *invoking* bq, never baked into the
    # SQL text itself.
    assert "--maximum_bytes_billed" not in sql
    assert "--format=csv" not in sql
    assert "--dry_run" not in sql


def test_build_q12_sql_unscoped():
    sql = workload_report.build_q12_sql()
    _assert_sql_shape(sql)
    assert "(unlabeled)" in sql
    assert "infra_cluster" in sql
    assert "project.name" in sql


def test_build_q12_sql_scoped_to_workload_and_cluster():
    sql = workload_report.build_q12_sql(workload="mongo", cluster="main")
    _assert_sql_shape(sql)
    assert "= 'mongo'" in sql
    assert "= 'main'" in sql


def test_build_q13_sql_unscoped():
    sql = workload_report.build_q13_sql()
    _assert_sql_shape(sql)
    assert "cur_week" in sql and "prev_week" in sql


def test_build_q13_sql_scoped_to_workload():
    sql = workload_report.build_q13_sql(workload="redis")
    _assert_sql_shape(sql)
    assert "= 'redis'" in sql


def test_sql_builders_escape_single_quotes_in_label_values():
    # parse_args drops unknown values, but the builders are importable on
    # their own — a quote must never break out of the string literal.
    sql = workload_report.build_q12_sql(workload="mo'ngo")
    assert "= 'mo\\'ngo'" in sql
    assert "= 'mo'ngo'" not in sql


def test_build_q18_sql_requires_workload():
    with pytest.raises(ValueError):
        workload_report.build_q18_sql("")


def test_build_q18_sql_contains_all_categories():
    sql = workload_report.build_q18_sql("gke", weeks=8)
    _assert_sql_shape(sql)
    for category in (
        "commitments",
        "cores",
        "ram",
        "pd-ssd",
        "pd-balanced",
        "snapshots",
        "nat",
        "egress",
    ):
        assert "'{0}'".format(category) in sql
    assert "= 'gke'" in sql


def test_build_q18_sql_lookback_scales_with_weeks():
    sql_4 = workload_report.build_q18_sql("gke", weeks=4)
    sql_8 = workload_report.build_q18_sql("gke", weeks=8)
    assert "INTERVAL 4 WEEK" in sql_4
    assert "INTERVAL 8 WEEK" in sql_8
    assert "WEEK(MONDAY)), INTERVAL" in sql_8


# ---------------------------------------------------------------------------
# flag_wow
# ---------------------------------------------------------------------------


def test_flag_wow_requires_both_pct_and_usd_over_threshold():
    rows = [
        # 25% change but only $1,000 delta — usd floor not cleared.
        {"infra_workload": "mongo", "cur_week": 5000, "prev_week": 4000},
        # $6,000 delta and 200% change — both floors cleared.
        {"infra_workload": "redis", "cur_week": 9000, "prev_week": 3000},
        # $3,000 delta but only 10% change — pct floor not cleared.
        {"infra_workload": "gke", "cur_week": 33000, "prev_week": 30000},
    ]
    flagged = workload_report.flag_wow(rows)
    assert [r["infra_workload"] for r in flagged] == ["redis"]
    assert flagged[0]["delta"] == 6000.0
    assert flagged[0]["pct_change"] == 200.0


def test_flag_wow_default_thresholds_are_20pct_and_2000usd():
    # Exactly at the boundary should NOT flag ("> ", not ">=").
    rows = [{"infra_workload": "mongo", "cur_week": 6000.0, "prev_week": 5000.0}]
    # delta=1000 (< 2000), pct=20% (not > 20%) -> not flagged
    assert workload_report.flag_wow(rows) == []


def test_flag_wow_handles_zero_prev_week():
    rows = [{"infra_workload": "gke", "cur_week": 3000.0, "prev_week": 0.0}]
    flagged = workload_report.flag_wow(rows)
    assert len(flagged) == 1
    assert flagged[0]["pct_change"] is None
    assert flagged[0]["delta"] == 3000.0


def test_flag_wow_zero_to_zero_is_not_flagged():
    rows = [{"infra_workload": "pritunl", "cur_week": 0.0, "prev_week": 0.0}]
    assert workload_report.flag_wow(rows) == []


def test_flag_wow_custom_thresholds():
    rows = [{"infra_workload": "mongo", "cur_week": 1100.0, "prev_week": 1000.0}]
    # 10% change, $100 delta — flags only with a much lower threshold.
    assert workload_report.flag_wow(rows, pct=0.05, usd=50.0) == [
        {
            "infra_workload": "mongo",
            "cur_week": 1100.0,
            "prev_week": 1000.0,
            "delta": 100.0,
            "pct_change": 10.0,
        }
    ]
    assert workload_report.flag_wow(rows, pct=0.20, usd=2000.0) == []


# ---------------------------------------------------------------------------
# render_markdown
# ---------------------------------------------------------------------------


def test_render_markdown_empty_rows():
    out = workload_report.render_markdown("Workload attribution", [])
    assert "### Workload attribution" in out
    assert "No rows." in out


def test_render_markdown_table_shape():
    rows = [
        {"infra_workload": "mongo", "delta": 1200.5},
        {"infra_workload": "redis", "delta": -300.0},
    ]
    out = workload_report.render_markdown("Q13 anomalies", rows)
    lines = out.splitlines()
    assert lines[0] == "### Q13 anomalies"
    assert "| infra_workload | delta |" in out
    assert "| mongo | 1200.5 |" in out
    assert "| redis | -300.0 |" in out


def test_render_markdown_none_values_render_as_empty_cell():
    out = workload_report.render_markdown("t", [{"a": 1, "b": None}])
    assert "| 1 |  |" in out


def test_build_q18_sql_matches_commitment_skus_first():
    sql = workload_report.build_q18_sql("mongo", cluster="main")
    assert sql.index("'commitments'") < sql.index("'cores'")
    assert "LIKE 'commitment v1:%'" in sql


def test_main_help_does_not_read_stdin(capsys):
    assert workload_report.main(["--help"]) == 0
    assert "usage:" in capsys.readouterr().out


def test_build_q18_sql_bounds_on_current_monday():
    sql = workload_report.build_q18_sql("mongo", cluster="main")
    assert "DATE_TRUNC(CURRENT_DATE(), WEEK(MONDAY))" in sql
    assert "INTERVAL 1 DAY" not in sql


def test_skill_cluster_vocabulary_matches_script():
    """references/workload-labels.md is the agent-facing copy of VALID_CLUSTERS."""
    import re
    from pathlib import Path

    ref = Path(__file__).resolve().parent.parent / "references" / "workload-labels.md"
    text = ref.read_text()
    section = text.split("Valid `infra_cluster` values", 1)[1].split("An unrecognized", 1)[0]
    listed = set(re.findall(r"`([a-z0-9-]+)`", section))
    assert listed == set(workload_report.VALID_CLUSTERS)
