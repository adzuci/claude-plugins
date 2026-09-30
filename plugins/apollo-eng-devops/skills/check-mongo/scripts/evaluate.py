#!/usr/bin/env python3
"""Score saved /check-mongo query results. Pure function: no network, no writes.

Input: JSON {query_id: [series]} where a series is {"metric": {labels}, "value": v}
(v is a number, a numeric string, or a Prometheus [ts, "v"] pair). A wrapper such as
{"data": [...]} or {"result": [...]} is also accepted. Missing/empty = no data.
Overall status precedence: ESCALATE > WARN > UNKNOWN > OK. No data is never OK.
The spec both this file and promql.py must match is references/checks.md (see tests/test_spec_sync.py).
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import defaultdict

DEFAULTS = {
    "uptime_s": 1800.0,          # uptime below this = recent restart
    "reset_hosts": 2.0,          # restarts on >= this many hosts = ESCALATE
    "lag_warn": 10.0,            # seconds, WARN when strictly above
    "lag_escalate": 60.0,        # seconds, ESCALATE when strictly above
    "oplog_warn_h": 24.0,        # hours, WARN when strictly below
    "oplog_escalate_h": 6.0,     # hours, ESCALATE when strictly below
    "conn_outlier_x": 2.0,       # mongos connections > x * median = WARN
    "missing_pct": 50.0,         # % of mongos missing/zero connections = ESCALATE
    "mem_avail_warn": 15.0,      # % host memory available, WARN when strictly below
    "mem_avail_escalate": 5.0,   # % host memory available, ESCALATE when strictly below
    "expected_mongos": 0.0,      # optional override; 0 = unset (the 24h lookback already finds vanished routers)
}
IPV4 = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")
RANK = {"OK": 0, "UNKNOWN": 1, "WARN": 2, "ESCALATE": 3}
CORE = ("router_up", "members_up", "mongos_connections", "restarts", "replication_lag", "primaries",
        "member_health", "oplog_window", "balancer")
ROUTER_UP_NEXT = ("up==0 or a missing series means the router process OR its exporter is down; "
                  "human-run on the host: journalctl -u mongos-{cluster}.service -n 50 (exit code), "
                  "see host-restart-triage")


def parse_thresholds(items: list) -> dict:
    out: dict = {}
    for item in items or []:
        for part in item.split(","):
            if not part.strip():
                continue
            key, _, val = part.partition("=")
            key = key.strip()
            if key not in DEFAULTS:
                raise ValueError(f"unknown threshold {key!r}; valid: {', '.join(DEFAULTS)}")
            out[key] = float(val)
    return out


def _num(v) -> float | None:
    if isinstance(v, (list, tuple)) and len(v) == 2:
        v = v[1]
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if f != f else f


def series(results: dict, qid: str) -> list:
    raw = results.get(qid) or []
    if isinstance(raw, dict):
        raw = raw.get("data") or raw.get("result") or []
        if isinstance(raw, dict):
            raw = raw.get("result") or []
    out = []
    for s in raw:
        labels = s.get("metric") or s.get("labels") or {}
        val = _num(s.get("value"))
        if val is not None:
            out.append((labels, val))
    return out


def host(labels: dict) -> str:
    """Short host name from an instance label; ip:port labels keep the whole IP."""
    name = str(labels.get("instance", "?")).rsplit(":", 1)[0]
    return name if IPV4.match(name) else name.split(".")[0]


def role_of(labels: dict) -> str:
    if labels.get("role"):
        return labels["role"]
    h = host(labels)
    for prefix, role in (("mongos-", "mongos"), ("mongo-", "mongod")):
        if h.startswith(prefix):
            return "mongoc" if "-config-" in h else role
    return "?"


def _f(check, status, evidence, next_step=""):
    return {"check": check, "status": status, "evidence": evidence, "next": next_step}


def _unknown(check, what):
    return _f(check, "UNKNOWN", f"no data for {what} (label drop or query failure)",
              "verify metric in Grafana Explore; do not treat as healthy")


def _short(items, n=5):
    items = sorted(items)
    return ", ".join(items[:n]) + (f" (+{len(items) - n} more)" if len(items) > n else "")


def _hosts(rows, *roles):
    return {host(l) for l, _ in rows if role_of(l) in roles}


def check_router_up(cluster, up, up_recent, uptime, conns, t):
    """A router is 'known' if seen in any current series or in the 24h `up` lookback."""
    known = _hosts(up + up_recent + conns + uptime, "mongos")
    up_ok = {host(l) for l, v in up if role_of(l) == "mongos" and v >= 1}
    if not known:
        return _unknown("router_up", "mongos up/uptime/connections")
    down = sorted(known - up_ok)
    short = max(0, int(t["expected_mongos"]) - len(known)) if t["expected_mongos"] else 0
    if not (down or short):
        return _f("router_up", "OK", f"{len(known)}/{len(known)} routers up")
    parts = []
    if down:
        parts.append(f"{len(down)}/{len(known)} routers down or absent now: {_short(down)}")
    if short:
        parts.append(f"{short} router series absent vs expected_mongos={int(t['expected_mongos'])}")
    return _f("router_up", "ESCALATE", "; ".join(parts), ROUTER_UP_NEXT.format(cluster=cluster))


def check_members_up(up, up_recent):
    """mongod/mongoc hosts seen in the lookback that are absent or up==0 now (covers a vanished replset)."""
    known = _hosts(up + up_recent, "mongod", "mongoc")
    up_ok = {host(l) for l, v in up if role_of(l) in ("mongod", "mongoc") and v >= 1}
    if not known:
        return _unknown("members_up", "mongod/mongoc up")
    down = sorted(known - up_ok)
    if not down:
        return _f("members_up", "OK", f"{len(known)}/{len(known)} mongod/mongoc up")
    return _f("members_up", "ESCALATE", f"{len(down)}/{len(known)} data/config members down or absent now: {_short(down)}",
              "up==0 or missing means process OR exporter down; human-run: journalctl -u <mongod|mongoc unit> and rs.status()")


def check_connections(conns, known_routers, t):
    if not conns:
        return _unknown("mongos_connections", "mongodb_connections")
    vals = {host(l): v for l, v in conns}
    routers = set(vals) | known_routers
    zero = sorted(h for h in routers if vals.get(h, 0) <= 0)
    pct = 100.0 * len(zero) / len(routers)
    med = statistics.median(vals.values())
    hot = sorted(h for h, v in vals.items() if med > 0 and v > t["conn_outlier_x"] * med)
    if pct >= t["missing_pct"]:
        return _f("mongos_connections", "ESCALATE", f"{len(zero)}/{len(routers)} routers missing/zero connections",
                  "check router health and client connectivity")
    if not (hot or zero):
        return _f("mongos_connections", "OK", f"median {med:.0f}, max {max(vals.values()):.0f}")
    bits = []
    if zero:
        bits.append(f"missing/zero: {_short(zero)}")
    if hot:
        bits.append(f">{t['conn_outlier_x']:g}x median ({med:.0f}): {_short(hot)}")
    return _f("mongos_connections", "WARN", "; ".join(bits), "compare per-router panels")


def check_restarts(uptime, resets, t):
    if not uptime and not resets:
        return _unknown("restarts", "mongodb_instance_uptime_seconds")
    hosts = {host(l): role_of(l) for l, v in uptime if v < t["uptime_s"]}
    hosts.update({host(l): role_of(l) for l, v in resets if v > 0})
    if not hosts:
        return _f("restarts", "OK", "no restarts in window")
    by_role = defaultdict(list)
    for h, r in hosts.items():
        by_role[r].append(h)
    ev = "; ".join(f"{r}: {len(v)} ({_short(v, 3)})" for r, v in sorted(by_role.items()))
    major = len(hosts) >= t["reset_hosts"] or "mongoc" in by_role or "mongod" in by_role
    if major:
        return _f("restarts", "ESCALATE", ev, "scope ALL routers with host-restart-triage")
    return _f("restarts", "WARN", ev, "one host restarted; check every router in router_up, then monitor")


def check_replication_lag(lag, t):
    if not lag:
        return _unknown("replication_lag", "replication lag")
    worst = max(lag, key=lambda x: x[1])
    hi = sorted(f"{host(l)}={v:g}s" for l, v in lag if v > t["lag_warn"])
    status = "ESCALATE" if worst[1] > t["lag_escalate"] else "WARN" if worst[1] > t["lag_warn"] else "OK"
    return _f("replication_lag", status,
              f"max {worst[1]:g}s on {host(worst[0])}" + (f"; over warn: {_short(hi, 3)}" if hi else ""),
              "check secondary load/disk and oplog" if status != "OK" else "")


def check_primaries(uptime):
    states = [l for l, _ in uptime if "rs_state" in l]
    if not states:
        return _unknown("primaries", "uptime rs_state label")
    per = defaultdict(int)
    for l in states:
        per[l.get("rs_nm", "?")] += 1 if str(l.get("rs_state")) == "1" else 0
    bad = sorted(f"{rs}={n}" for rs, n in per.items() if n != 1)
    if bad:
        return _f("primaries", "ESCALATE", f"replsets without exactly 1 primary: {_short(bad)}",
                  "check election status / partition")
    return _f("primaries", "OK", f"{len(per)} replsets, 1 primary each")


def check_member_health(health):
    if not health:
        return _unknown("member_health", "mongodb_members_health")
    sick = sorted(host(l) for l, v in health if v < 1)
    if sick:
        return _f("member_health", "ESCALATE", f"unhealthy members reported by: {_short(sick)}",
                  "rs.status() via human-run mongosh")
    return _f("member_health", "OK", f"{len(health)} instances report all members healthy")


def check_oplog(oplog, t):
    if not oplog:
        return _unknown("oplog_window", "oplog head/tail timestamps")
    low = min(oplog, key=lambda x: x[1])
    h = low[1] / 3600.0
    status = "ESCALATE" if h < t["oplog_escalate_h"] else "WARN" if h < t["oplog_warn_h"] else "OK"
    return _f("oplog_window", status, f"min {h:.1f}h on {host(low[0])}",
              "oplog too small for write rate; plan resize" if status != "OK" else "")


def check_balancer(enabled_rows, running_rows, drain_rows):
    """Prod semantics of balancer_enabled are unverified (0 seen on main/accounts/contacts while running==1)."""
    if not enabled_rows or not running_rows:
        return _unknown("balancer", "balancer enabled/running")
    enabled = max(v for _, v in enabled_rows) >= 1
    running = max(v for _, v in running_rows) >= 1
    # shards_draining_total emits no series when nothing is draining (seen live), so empty = 0.
    draining = max((v for _, v in drain_rows), default=0.0)
    ev = f"enabled={int(enabled)}, running(last 30m)={int(running)}, draining shards={draining:g}"
    if draining > 0:
        return _f("balancer", "ESCALATE", ev, "check sh.status() via human-run mongosh")
    if not enabled:
        return _f("balancer", "WARN", ev + "; balancer disabled", "confirm intentional (metric semantics unverified)")
    return _f("balancer", "OK", ev + ("" if running else "; idle is normal when chunks are balanced"))


def check_mongos_memory(mem):
    if not mem:
        return _unknown("mongos_memory", "mongodb_ss_mem_resident")
    top = max(mem, key=lambda x: x[1])  # exporter unit is MB
    return _f("mongos_memory", "INFO", f"max resident {top[1] / 1024:.1f} GiB on {host(top[0])} (metric is MB)")


def check_host_memory(avail_pct, t):
    if not avail_pct:
        return _f("host_memory", "UNKNOWN", "mongodb_sys_memory_* not found for these instances",
                  "check GCP Monitoring memory alerts / VM memory in GCP console")
    low = min(avail_pct, key=lambda x: x[1])
    below = sorted(f"{host(l)}={v:.0f}%" for l, v in avail_pct if v < t["mem_avail_warn"])
    status = ("ESCALATE" if low[1] < t["mem_avail_escalate"]
              else "WARN" if low[1] < t["mem_avail_warn"] else "OK")
    ev = f"min available {low[1]:.0f}% on {host(low[0])}" + (f"; below warn: {_short(below, 3)}" if below else "")
    return _f("host_memory", status, ev,
              "OOM kill risk; human-run: sudo dmesg -T | grep -i -E 'out of memory|killed process'" if status != "OK" else "")


def _overall(findings):
    scored = [f["status"] for f in findings
              if f["check"] in CORE or (f["check"] == "host_memory" and f["status"] in ("WARN", "ESCALATE"))]
    return max(scored, key=lambda s: RANK[s]) if scored else "UNKNOWN"


def router_states(up, up_recent, uptime, conns) -> dict:
    """host -> 'up' | 'down' (series present, up<1) | 'absent' (seen in lookback/other series, no `up` now)."""
    now = {host(l): v for l, v in up if role_of(l) == "mongos"}
    known = _hosts(up + up_recent + conns + uptime, "mongos")
    return {h: ("absent" if h not in now else "up" if now[h] >= 1 else "down") for h in sorted(known)}


def _escalation_command(cluster, reasons):
    ref = ("references/host-restart-triage.md"
           if any(r.startswith(("restarts", "router_up", "members_up", "host_memory")) for r in reasons)
           else "references/live-incident-mode.md")
    return f"/apollo-eng-devops:mongo-specialist {cluster} incident: {'; '.join(reasons)} (load {ref})"


def evaluate(results: dict, cluster: str, thresholds: dict | None = None, role: str = "all") -> dict:
    t = dict(DEFAULTS)
    t.update(thresholds or {})
    has = lambda *g: role == "all" or role in g  # noqa: E731
    up, up_recent = series(results, "up"), series(results, "up_recent")
    uptime, conns = series(results, "uptime"), series(results, "connections")
    F = []

    if has("mongos"):
        router_up = check_router_up(cluster, up, up_recent, uptime, conns, t)
        F.append(router_up)
        F.append(check_connections(conns, _hosts(up + up_recent + uptime, "mongos"), t))
    F.append(check_restarts(uptime, series(results, "restarts"), t))
    if has("mongos") and router_up["status"] == "ESCALATE" and F[-1]["status"] == "WARN":
        F[-1]["next"] = "router_up is ESCALATE: treat as multi-router event, see router_up"

    if has("mongod", "mongoc"):
        F += [check_members_up(up, up_recent),
              check_replication_lag(series(results, "repl_lag"), t),
              check_primaries(uptime),
              check_member_health(series(results, "members_health")),
              check_oplog(series(results, "oplog_window"), t)]

    if has("mongos"):
        F.append(check_balancer(*(series(results, k) for k in ("balancer_enabled", "balancer_running", "shards_draining"))))
        F.append(check_mongos_memory(series(results, "mem_resident")))

    F.append(check_host_memory(series(results, "host_mem_avail_pct"), t))

    reasons = [f"{f['check']}: {f['evidence']}" for f in F if f["status"] == "ESCALATE"]
    overall = _overall(F)
    routers = router_states(up, up_recent, uptime, conns) if has("mongos") else {}
    return {"cluster": cluster, "status": overall, "findings": F, "escalate_reasons": reasons, "routers": routers,
            "next_step": _escalation_command(cluster, reasons) if overall == "ESCALATE" else "",
            "thresholds": t}


def render_markdown(report: dict) -> str:
    esc = lambda s: str(s).replace("|", "\\|").replace("\n", " ")  # noqa: E731
    lines = [f"# check-mongo: {report['cluster']} -> {report['status']}", "",
             "| Check | Status | Evidence | Next step |", "| --- | --- | --- | --- |"]
    for f in report["findings"]:
        lines.append(f"| {f['check']} | {f['status']} | {esc(f['evidence'])} | {esc(f['next'])} |")
    if report["next_step"]:
        lines += ["", "Escalate with:", "", f"    {report['next_step']}"]
    return "\n".join(lines)


ARGUS_WORDS = 120
HUMAN_ONLY = "OOM kill vs self-exit (journalctl, dmesg, mongos log, `uptime -s`) is HUMAN-ONLY"
CLASS = {"router_up": "router down", "members_up": "data/config member down", "restarts": "host restarts",
         "mongos_connections": "router connections", "replication_lag": "replication lag",
         "primaries": "no single primary", "member_health": "unhealthy member", "oplog_window": "short oplog",
         "balancer": "balancer", "host_memory": "host memory pressure"}
CONFIDENCE = {"ESCALATE": 0.6, "WARN": 0.5, "UNKNOWN": 0.2, "OK": 0.7}  # metrics only: never above 0.7


def _clip(text: str, words: int) -> str:
    parts = str(text).split()
    return " ".join(parts[:words]) + (" ..." if len(parts) > words else "")


def _argus_headline(report: dict) -> tuple:
    """Return (classification, impact) for the subtitle line."""
    fs = report["findings"]
    status = report["status"]
    routers = report.get("routers") or {}
    down = [h for h, st in routers.items() if st != "up"]
    if status in ("ESCALATE", "WARN"):
        bad = [f for f in fs if f["status"] == "ESCALATE"] or [f for f in fs if f["status"] == "WARN"]
        cls = CLASS.get(bad[0]["check"], bad[0]["check"])
        impact = (f"{len(down)}/{len(routers)} routers not up" if down else
                  "capacity or availability at risk" if status == "ESCALATE" else "degraded, no outage seen")
        return cls, impact
    if status == "UNKNOWN":
        return "inconclusive", "unknown, no data"
    return "no fault seen in metrics", "none seen"


def _argus_next_step(status: str) -> str:
    if status == "ESCALATE":
        return ("Human runs host-restart-triage on all routers; declare incident if 2+ reset. "
                "Not resolved until every router up and stable 15-30 min.")
    if status == "WARN":
        return "Recheck every router in 15-30 min; not resolved until all up and stable 15-30 min."
    return "Re-run metrics check; not resolved until every router up and stable 15-30 min."


def _argus_post(report: dict, cc: str, ev_words: int) -> str:
    """Build the post with each evidence string clipped to ev_words words."""
    fs = report["findings"]
    status = report["status"]
    bad = [f for f in fs if f["status"] == "ESCALATE"] or [f for f in fs if f["status"] == "WARN"]
    unknown = [f["check"] for f in fs if f["status"] == "UNKNOWN"]
    rt = ", ".join(f"{h} {st}" for h, st in (report.get("routers") or {}).items())
    cls, impact = _argus_headline(report)
    alert = "; ".join(f"{f['check']} {f['status']}: {_clip(f['evidence'], ev_words)}" for f in bad[:2])
    if not alert:
        alert = ("no data for " + ", ".join(unknown[:4])) if status == "UNKNOWN" else "no ESCALATE or WARN"
    if rt:
        alert += f". Routers: {rt}"
    cause = ("Not established from metrics."
             + (" Restarts/absences need host logs to tell OOM kill from self-exit." if status == "ESCALATE" else ""))
    cant = HUMAN_ONLY + ("; no data: " + ", ".join(unknown[:4]) if unknown and status != "UNKNOWN" else "")
    return "\n".join([
        f"*check-mongo · {report['cluster']} · {status}*",
        f"_{cls} · {impact} · confidence {CONFIDENCE[status]:.2f}_",
        f"- **Alert**: {alert}", f"- **Root cause**: {cause}",
        f"- **Couldn't verify**: {cant}", f"- **Next step**: {_argus_next_step(status)}", f"cc: {cc}"])


def render_argus(report: dict, cc: str = "@oncall") -> str:
    """The single Slack post Argus should emit (<=120 words). UNKNOWN is never rendered as healthy."""
    for w in (25, 12, 6, 3):
        text = _argus_post(report, cc, w)
        if len(text.split()) <= ARGUS_WORDS:
            return text
    return _argus_post(report, cc, 3)


def main(argv: list | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results", required=True)
    ap.add_argument("--cluster", default="main")
    ap.add_argument("--role", default="all", choices=["all", "mongos", "mongod", "mongoc"])
    ap.add_argument("--thresholds", action="append", default=[])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--format", choices=["table", "argus"], default="table",
                    help="argus = the <=120-word Slack post Argus should produce (preview for humans/CI)")
    ap.add_argument("--cc", default="@oncall", help="cc line for --format argus")
    a = ap.parse_args(argv)
    try:
        from promql import normalize_cluster
        cluster = normalize_cluster(a.cluster)
        thr = parse_thresholds(a.thresholds)
        with open(a.results) as fh:
            results = json.load(fh)
    except (ValueError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    report = evaluate(results, cluster, thr, a.role)
    if a.json:
        print(json.dumps(report, indent=2))
    else:
        print(render_argus(report, a.cc) if a.format == "argus" else render_markdown(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
