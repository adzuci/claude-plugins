#!/usr/bin/env python3
"""Print the PromQL queries /check-mongo runs for one prod Mongo cluster.

Pure: no network, no file I/O. Output is a JSON list of {id, expr, kind}.
kind is "instant" (required) or "optional" (empty result is reported UNKNOWN).
Cluster is validated against an allowlist so it can never inject PromQL labels.
"""

from __future__ import annotations

import argparse
import json
import sys

CLUSTERS = (
    "main", "accounts", "contacts", "custom-objects", "email", "emailermessages",
    "noncustomer",
)
WINDOWS = ("1h", "6h", "24h")
ROLES = ("all", "mongos", "mongod", "mongoc")
ALL_ROLES = ("mongos", "mongod", "mongoc")
JOB = "integrations/mongodb"
BALANCER_IDLE_WINDOW = "30m"
LOOKBACK = "24h"  # how far back a host counts as "seen" when its series has vanished


def normalize_cluster(value: str = "main") -> str:
    name = (value or "").strip().lower()
    if name.startswith("mongo-"):
        name = name[len("mongo-"):]
    if name not in CLUSTERS:
        raise ValueError(f"unknown cluster {value!r}; valid: {', '.join(CLUSTERS)}")
    return name


def _roles(role: str, allowed: tuple) -> str | None:
    picked = [r for r in ALL_ROLES if r in allowed and role in ("all", r)]
    return "|".join(picked) if picked else None


def build_queries(cluster: str = "main", window: str = "1h", role: str = "all") -> list:
    c = normalize_cluster(cluster)
    if window not in WINDOWS:
        raise ValueError(f"window must be one of {', '.join(WINDOWS)}")
    if role not in ROLES:
        raise ValueError(f"role must be one of {', '.join(ROLES)}")

    def sel(roles: str, extra: str = "") -> str:
        return f'cluster="{c}", role=~"{roles}"{extra}'

    every = _roles(role, ALL_ROLES)
    repl = _roles(role, ("mongod", "mongoc"))
    router = _roles(role, ("mongos",))
    job = f', job="{JOB}"'
    current = ', state="current"'

    q = [
        ("uptime", f"mongodb_instance_uptime_seconds{{{sel(every)}}}", "instant"),
        ("restarts", f"resets(mongodb_instance_uptime_seconds{{{sel(every)}}}[{window}])", "instant"),
        ("up", f"up{{{sel(every, job)}}}", "instant"),
        ("up_recent", f"max_over_time(up{{{sel(every, job)}}}[{LOOKBACK}])", "instant"),
    ]
    if repl:
        q += [
            ("repl_lag", "max by (cluster, role, instance, set) "
             f"(mongodb_mongod_replset_member_replication_lag{{{sel(repl)}}})", "instant"),
            ("members_health", "min by (cluster, role, instance, rs_nm) "
             f"(mongodb_members_health{{{sel(repl)}}})", "instant"),
            ("oplog_window", f"mongodb_mongod_replset_oplog_head_timestamp{{{sel(repl)}}}"
             f" - mongodb_mongod_replset_oplog_tail_timestamp{{{sel(repl)}}}", "instant"),
        ]
    if router:
        m = f'cluster="{c}"'
        q += [
            ("connections", f"mongodb_connections{{{sel(router, current)}}}", "instant"),
            ("mem_resident", f"mongodb_ss_mem_resident{{{sel(router)}}}", "instant"),
            ("balancer_enabled", f"max by (cluster) (mongodb_mongos_sharding_balancer_enabled{{{m}}})", "instant"),
            ("balancer_running", "max_over_time(max by (cluster) "
             f"(mongodb_mongos_sharding_chunks_is_balancer_running{{{m}}})[{BALANCER_IDLE_WINDOW}:1m])", "instant"),
            ("shards_draining", f"max by (cluster) (mongodb_mongos_sharding_shards_draining_total{{{m}}})", "instant"),
        ]
    q.append((
        "host_mem_avail_pct",
        f"100 * mongodb_sys_memory_MemAvailable_kb{{{sel(every)}}}"
        f" / mongodb_sys_memory_MemTotal_kb{{{sel(every)}}}",
        "optional",
    ))
    return [{"id": i, "expr": e, "kind": k} for i, e, k in q]


def main(argv: list | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cluster", default="main")
    ap.add_argument("--window", default="1h")
    ap.add_argument("--role", default="all")
    a = ap.parse_args(argv)
    try:
        out = build_queries(a.cluster, a.window, a.role)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
