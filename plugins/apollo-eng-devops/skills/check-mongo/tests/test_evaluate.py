from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

mod = pytest.importorskip("evaluate")

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "evaluate.py"
D = ".us-central1-c.c.indigo-lotus-415.internal:27017"


def ev(results, **thr):
    return mod.evaluate(results, "main", thr)


def finding(report, check):
    return next(f for f in report["findings"] if f["check"] == check)


def set_val(results, key, inst_prefix, value):
    for s in results[key]:
        if s["metric"]["instance"].startswith(inst_prefix):
            s["value"] = value


def test_healthy_is_ok(load):
    r = ev(load("healthy"))
    assert r["status"] == "OK", r["findings"]
    assert r["escalate_reasons"] == []


def test_empty_data_is_unknown_never_ok(load):
    r = ev(load("empty"))
    assert r["status"] == "UNKNOWN"
    assert r["escalate_reasons"] == []


def test_string_prom_values_and_wrapper_normalized(load):
    res = load("healthy")
    res["up"] = {"data": [{"metric": s["metric"], "value": [1.0, "1"]} for s in res["up"]]}
    assert ev(res)["status"] == "OK"


def test_no_primary_escalates(load):
    r = ev(load("no_primary"))
    assert r["status"] == "ESCALATE"
    assert any("main-2" in x and "primar" in x for x in r["escalate_reasons"])


def test_two_primaries_escalates(load):
    res = load("healthy")
    for s in res["uptime"]:
        if s["metric"].get("rs_nm") == "main-1":
            s["metric"]["rs_state"] = "1"
    assert ev(res)["status"] == "ESCALATE"


def test_multi_reset_escalates(load):
    r = ev(load("multi_reset"))
    assert r["status"] == "ESCALATE"
    assert any("restart" in x for x in r["escalate_reasons"])


def test_single_router_reset_is_warn_only(load):
    res = load("healthy")
    set_val(res, "restarts", "mongos-main-0", 1)
    set_val(res, "uptime", "mongos-main-0", 100)
    r = ev(res)
    assert r["status"] == "WARN"
    assert r["escalate_reasons"] == []


def test_single_mongod_reset_escalates(load):
    res = load("healthy")
    set_val(res, "restarts", "mongo-main-shard-1-a", 1)
    assert ev(res)["status"] == "ESCALATE"


def test_uptime_boundary(load):
    res = load("healthy")
    set_val(res, "uptime", "mongos-main-0", 1800)
    assert ev(res)["status"] == "OK"
    set_val(res, "uptime", "mongos-main-0", 1799)
    assert ev(res)["status"] == "WARN"


def test_router_up_zero_escalates(load):
    r = ev(load("router_down"))
    assert r["status"] == "ESCALATE"
    assert any("mongos-main-3" in x for x in r["escalate_reasons"])


def test_router_missing_up_series_escalates(load):
    r = ev(load("router_missing"))
    assert r["status"] == "ESCALATE"
    assert any("mongos-main-3" in x for x in r["escalate_reasons"])


def test_expected_mongos_count_detects_vanished_router(load):
    assert ev(load("healthy"), expected_mongos=5)["status"] == "ESCALATE"
    assert ev(load("healthy"), expected_mongos=4)["status"] == "OK"


def test_half_of_routers_zero_connections_escalates(load):
    res = load("healthy")
    for p in ("mongos-main-0", "mongos-main-1"):
        set_val(res, "connections", p, 0)
    r = ev(res)
    assert r["status"] == "ESCALATE"
    assert finding(r, "mongos_connections")["status"] == "ESCALATE"


def test_less_than_half_zero_connections_not_connection_escalation(load):
    res = load("healthy")
    set_val(res, "connections", "mongos-main-0", 0)
    assert finding(ev(res), "mongos_connections")["status"] != "ESCALATE"


def test_connection_outlier_boundary(load):
    res = load("healthy")
    # median stays 10000; exactly 2x is fine, above is WARN
    set_val(res, "connections", "mongos-main-0", 20000)
    assert finding(ev(res), "mongos_connections")["status"] == "OK"
    set_val(res, "connections", "mongos-main-0", 20001)
    f = finding(ev(res), "mongos_connections")
    assert f["status"] == "WARN"
    assert ev(res)["escalate_reasons"] == []


def test_repl_lag_boundaries(load):
    res = load("healthy")
    set_val(res, "repl_lag", "mongo-main-shard-1-b", 10)
    assert finding(ev(res), "replication_lag")["status"] == "OK"
    set_val(res, "repl_lag", "mongo-main-shard-1-b", 11)
    assert finding(ev(res), "replication_lag")["status"] == "WARN"
    set_val(res, "repl_lag", "mongo-main-shard-1-b", 60)
    assert finding(ev(res), "replication_lag")["status"] == "WARN"
    set_val(res, "repl_lag", "mongo-main-shard-1-b", 61)
    r = ev(res)
    assert r["status"] == "ESCALATE"
    assert any("lag" in x for x in r["escalate_reasons"])


def test_oplog_window_boundaries(load):
    res = load("healthy")
    set_val(res, "oplog_window", "mongo-main-shard-1-a", 86400)
    assert finding(ev(res), "oplog_window")["status"] == "OK"
    set_val(res, "oplog_window", "mongo-main-shard-1-a", 86399)
    assert finding(ev(res), "oplog_window")["status"] == "WARN"
    set_val(res, "oplog_window", "mongo-main-shard-1-a", 21600)
    assert finding(ev(res), "oplog_window")["status"] == "WARN"
    set_val(res, "oplog_window", "mongo-main-shard-1-a", 21599)
    assert ev(res)["status"] == "ESCALATE"


def test_member_health_zero_escalates(load):
    res = load("healthy")
    set_val(res, "members_health", "mongo-main-shard-2-a", 0)
    assert ev(res)["status"] == "ESCALATE"


def test_balancer_enabled_but_idle_is_ok_not_escalation(load):
    res = load("healthy")
    res["balancer_running"][0]["value"] = 0
    r = ev(res)
    assert r["status"] == "OK"
    assert finding(r, "balancer")["status"] == "OK"


def test_balancer_disabled_warns_even_when_running(load):
    # Live 2026-09-29: balancer_enabled==0 while is_balancer_running==1 on main/accounts/contacts.
    res = load("healthy")
    res["balancer_enabled"][0]["value"] = 0
    r = ev(res)
    f = finding(r, "balancer")
    assert f["status"] == "WARN"
    assert "confirm intentional" in f["evidence"] + f["next"]
    assert r["escalate_reasons"] == []


def test_balancer_disabled_and_idle_warns(load):
    res = load("healthy")
    res["balancer_enabled"][0]["value"] = 0
    res["balancer_running"][0]["value"] = 0
    assert finding(ev(res), "balancer")["status"] == "WARN"


def test_draining_escalates_even_when_balancer_disabled(load):
    res = load("healthy")
    res["balancer_enabled"][0]["value"] = 0
    res["shards_draining"][0]["value"] = 2
    assert finding(ev(res), "balancer")["status"] == "ESCALATE"


def test_shard_draining_escalates(load):
    res = load("healthy")
    res["shards_draining"][0]["value"] = 1
    assert ev(res)["status"] == "ESCALATE"


def test_empty_draining_series_means_zero(load):
    res = load("healthy")
    res["shards_draining"] = []
    assert finding(ev(res), "balancer")["status"] == "OK"


def test_thresholds_override(load):
    res = load("healthy")
    set_val(res, "repl_lag", "mongo-main-shard-1-b", 15)
    assert ev(res, lag_warn=20)["status"] == "OK"
    assert ev(res, lag_warn=5)["status"] == "WARN"


def test_missing_repl_data_is_unknown_not_ok(load):
    res = load("healthy")
    res["repl_lag"] = []
    r = ev(res)
    assert finding(r, "replication_lag")["status"] == "UNKNOWN"
    assert r["status"] == "UNKNOWN"


def test_host_memory_absent_is_unknown_finding_but_not_overall(load):
    r = ev(load("healthy"))
    f = finding(r, "host_memory")
    assert f["status"] == "UNKNOWN"
    assert "GCP Monitoring" in f["next"]
    assert r["status"] == "OK"


def set_mem(res, pct_by_prefix):
    res["host_mem_avail_pct"] = [
        {"metric": {"instance": f"{p}.x.internal:27017", "role": "mongos"}, "value": v}
        for p, v in pct_by_prefix.items()
    ]


def test_host_memory_boundaries(load):
    res = load("healthy")
    set_mem(res, {"mongos-main-0": 15, "mongos-main-1": 60})
    assert finding(ev(res), "host_memory")["status"] == "OK"
    set_mem(res, {"mongos-main-0": 14.9, "mongos-main-1": 60})
    f = finding(ev(res), "host_memory")
    assert f["status"] == "WARN" and "mongos-main-0" in f["evidence"]
    assert ev(res)["status"] == "WARN"
    set_mem(res, {"mongos-main-0": 5, "mongos-main-1": 60})
    assert finding(ev(res), "host_memory")["status"] == "WARN"
    set_mem(res, {"mongos-main-0": 4.9, "mongos-main-1": 60})
    r = ev(res)
    assert r["status"] == "ESCALATE"
    assert any(x.startswith("host_memory") for x in r["escalate_reasons"])
    assert "host-restart-triage" in r["next_step"]


def test_host_memory_thresholds_override(load):
    res = load("healthy")
    set_mem(res, {"mongos-main-0": 20})
    assert finding(ev(res), "host_memory")["status"] == "OK"
    assert finding(ev(res, mem_avail_warn=25), "host_memory")["status"] == "WARN"


def test_mem_resident_reported_in_gb_from_mb(load):
    r = ev(load("healthy"))
    assert "GiB" in finding(r, "mongos_memory")["evidence"]


def test_escalate_next_step_names_command(load):
    r = ev(load("multi_reset"))
    assert "/apollo-eng-devops:mongo-specialist main incident:" in r["next_step"]
    assert "host-restart-triage" in r["next_step"]


def test_warn_has_no_next_command(load):
    res = load("healthy")
    set_val(res, "repl_lag", "mongo-main-shard-1-b", 30)
    assert ev(res)["next_step"] == ""


def test_parse_thresholds():
    assert mod.parse_thresholds(["lag_warn=5,lag_escalate=9", "oplog_warn_h=12"]) == {
        "lag_warn": 5.0, "lag_escalate": 9.0, "oplog_warn_h": 12.0,
    }
    with pytest.raises(ValueError):
        mod.parse_thresholds(["bogus=1"])


def test_cli_json_and_markdown(tmp_path):
    fx = Path(__file__).resolve().parent / "fixtures" / "healthy.json"
    base = [sys.executable, str(SCRIPT), "--results", str(fx), "--cluster", "main"]
    j = json.loads(subprocess.run(base + ["--json"], capture_output=True, text=True).stdout)
    assert j["status"] == "OK"
    md = subprocess.run(base, capture_output=True, text=True).stdout
    assert "| Check | Status | Evidence | Next step |" in md
    bad = subprocess.run(base[:-1] + ["nope"], capture_output=True, text=True)
    assert bad.returncode == 2


# --- vanished routers / replsets (lookback) -------------------------------------------

def drop_instance(res, prefix, keys):
    for k in keys:
        res[k] = [s for s in res[k] if not s["metric"]["instance"].startswith(prefix)]


def test_router_absent_everywhere_now_escalates_via_lookback(load):
    res = load("healthy")
    drop_instance(res, "mongos-main-3", ["up", "uptime", "connections", "restarts"])
    r = ev(res)  # expected_mongos NOT set
    assert r["status"] == "ESCALATE"
    f = finding(r, "router_up")
    assert f["status"] == "ESCALATE" and "mongos-main-3" in f["evidence"]


def test_router_up_zero_now_but_up_in_lookback_escalates(load):
    res = load("healthy")
    set_val(res, "up", "mongos-main-3", 0)
    assert finding(ev(res), "router_up")["status"] == "ESCALATE"


def test_lookback_all_routers_still_present_is_ok(load):
    assert finding(ev(load("healthy")), "router_up")["status"] == "OK"


def test_whole_replset_vanished_escalates_via_lookback(load):
    res = load("healthy")
    drop_instance(res, "mongo-main-shard-2", ["up", "uptime", "restarts", "repl_lag", "members_health", "oplog_window"])
    r = ev(res)
    assert r["status"] == "ESCALATE"
    f = finding(r, "members_up")
    assert f["status"] == "ESCALATE"
    assert "mongo-main-shard-2-a" in f["evidence"] and "mongo-main-shard-2-b" in f["evidence"]


def test_member_up_zero_escalates(load):
    res = load("healthy")
    set_val(res, "up", "mongo-main-config-0", 0)
    assert finding(ev(res), "members_up")["status"] == "ESCALATE"


def test_router_next_step_says_process_or_exporter_and_points_at_journal(load):
    f = finding(ev(load("router_down")), "router_up")
    text = f["evidence"] + " " + f["next"]
    assert "router process OR its exporter" in text
    assert "journalctl -u mongos-main.service" in text
    assert "GCE VM state" not in text


def test_restarts_row_does_not_say_monitor_when_router_up_escalates(load):
    res = load("healthy")
    set_val(res, "uptime", "mongos-main-0", 100)
    set_val(res, "up", "mongos-main-3", 0)
    r = ev(res)
    assert finding(r, "router_up")["status"] == "ESCALATE"
    nxt = finding(r, "restarts")["next"]
    assert "monitor" not in nxt and "router_up" in nxt


def test_host_strips_port_and_domain_and_keeps_ip():
    assert mod.host({"instance": "mongos-main-0.us-central1-c.c.p.internal:27019"}) == "mongos-main-0"
    assert mod.host({"instance": "mongos-main-0:27019"}) == "mongos-main-0"
    assert mod.host({"instance": "10.128.0.5:27019"}) == "10.128.0.5"
    assert mod.host({}) == "?"


def test_ip_instance_labels_do_not_collapse_hosts(load):
    res = load("healthy")
    for i, key in enumerate(("up", "up_recent", "uptime", "connections")):
        for j, s in enumerate(x for x in res[key] if x["metric"].get("role") == "mongos"):
            s["metric"]["instance"] = f"10.128.0.{j + 1}:27019"
    r = ev(res)
    assert finding(r, "router_up")["evidence"] == "4/4 routers up"
