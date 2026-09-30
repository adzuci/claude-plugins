from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

mod = pytest.importorskip("promql")

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "promql.py"
IDS = {
    "uptime", "restarts", "up", "repl_lag", "members_health", "oplog_window",
    "connections", "mem_resident", "balancer_enabled", "balancer_running",
    "shards_draining", "up_recent", "host_mem_avail_pct",
}


def by_id(queries):
    return {q["id"]: q for q in queries}


def test_default_cluster_is_main():
    q = mod.build_queries()
    assert all('cluster="main"' in x["expr"] for x in q)


def test_mongo_prefix_accepted():
    assert mod.normalize_cluster("mongo-accounts") == "accounts"
    assert mod.normalize_cluster("custom-objects") == "custom-objects"


@pytest.mark.parametrize("bad", ['main"}or{x="', "prod", "all", "", "main|accounts"])
def test_bad_cluster_rejected(bad):
    with pytest.raises(ValueError, match="main"):
        mod.normalize_cluster(bad)


def test_cli_bad_cluster_exits_2_and_lists_valid():
    p = subprocess.run(
        [sys.executable, str(SCRIPT), "--cluster", "nope"], capture_output=True, text=True
    )
    assert p.returncode == 2
    assert "custom-objects" in p.stderr


def test_stable_query_ids():
    ids = [x["id"] for x in mod.build_queries("main", "1h", "all")]
    assert set(ids) == IDS
    assert ids == [x["id"] for x in mod.build_queries("accounts", "24h", "all")]


def test_window_used_in_range_queries_and_validated():
    q = by_id(mod.build_queries("main", "6h"))
    assert "[6h]" in q["restarts"]["expr"]
    with pytest.raises(ValueError):
        mod.build_queries("main", "7d")


def test_instances_never_aggregated_away():
    q = by_id(mod.build_queries("main"))
    for qid in ("uptime", "up", "connections", "repl_lag"):
        assert "instance" in q[qid]["expr"] or "by (" not in q[qid]["expr"]
    assert 'state="current"' in q["connections"]["expr"]


def test_role_filter_drops_inapplicable_queries():
    ids = {x["id"] for x in mod.build_queries("main", "1h", "mongos")}
    assert "connections" in ids and "repl_lag" not in ids
    ids = {x["id"] for x in mod.build_queries("main", "1h", "mongod")}
    assert "repl_lag" in ids and "connections" not in ids


def test_host_memory_is_optional_kind():
    q = by_id(mod.build_queries("main"))
    assert q["host_mem_avail_pct"]["kind"] == "optional"
    assert q["up"]["kind"] == "instant"


def test_cli_prints_json_list():
    p = subprocess.run(
        [sys.executable, str(SCRIPT), "--cluster", "mongo-main"], capture_output=True, text=True
    )
    assert p.returncode == 0
    out = json.loads(p.stdout)
    assert {"id", "expr", "kind"} <= set(out[0])


def test_up_recent_is_24h_lookback_on_up_for_every_role():
    q = by_id(mod.build_queries("main", "1h"))["up_recent"]
    assert q["expr"].startswith("max_over_time(up{")
    assert q["expr"].endswith("[24h])")
    assert 'job="integrations/mongodb"' in q["expr"]
    assert "mongos|mongod|mongoc" in q["expr"]


def test_up_recent_lookback_ignores_short_window():
    assert by_id(mod.build_queries("main", "1h"))["up_recent"]["expr"] == \
        by_id(mod.build_queries("main", "6h"))["up_recent"]["expr"]


def test_host_memory_uses_exporter_sys_memory_metrics():
    e = by_id(mod.build_queries("contacts"))["host_mem_avail_pct"]["expr"]
    assert "mongodb_sys_memory_MemAvailable_kb" in e and "mongodb_sys_memory_MemTotal_kb" in e
    assert "node_memory" not in e


def test_nonexistent_op_counters_metric_not_queried():
    assert all("mongodb_op_counters_total" not in q["expr"] for q in mod.build_queries("main"))
