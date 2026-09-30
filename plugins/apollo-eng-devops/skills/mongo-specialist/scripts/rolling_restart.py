#!/usr/bin/env python3
"""Guarded, human-run helper: restart a SUBSET of prod mongos routers, one at a time.

DEFAULT IS A DRY RUN: prints the plan and exact commands, runs nothing.
--execute runs them for ONE host at a time with preflight checks, a typed-hostname
confirmation, restart, verification and a soak, and STOPS on the first failure.
Never reads or prints credentials. Agents must not run this with --execute.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time

# mongos counts per cluster (see references/mongo-clusters.md; re-check before acting).
ROUTERS = {
    "main": 16, "accounts": 6, "contacts": 6, "custom-objects": 6,
    "email": 6, "emailermessages": 6, "noncustomer": 12,
}
PROJECT = "indigo-lotus-415"
ZONE = "us-central1-c"
JOB = "integrations/mongodb"
BUSY = ("in_progress", "queued", "waiting", "pending", "requested")
POLL = 15
ACTIVE_TIMEOUT = 120
UP_TIMEOUT = 300
UPTIME_MAX = 300


class Stop(Exception):
    """Abort the procedure; message is printed and nothing further runs."""


def run_cmd(cmd: list, timeout: int = 180) -> subprocess.CompletedProcess:
    """The ONLY place subprocesses are started (tests mock this)."""
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)


def _sleep(seconds: float) -> None:
    time.sleep(seconds)


def host_name(cluster: str, n: int) -> str:
    return f"mongos-{cluster}-{n}"


def unit(cluster: str) -> str:
    return f"mongos-{cluster}.service"


def deploy_cmd() -> list:
    return ["gh", "run", "list", "--repo", "apolloio/leadgenie", "--workflow", "production.yml",
            "--limit", "3", "--json", "status,conclusion,createdAt,displayTitle"]


def ssh_cmd(cluster: str, n: int, remote: str) -> list:
    return ["gcloud", "compute", "ssh", host_name(cluster, n), "--project", PROJECT,
            "--zone", ZONE, "--internal-ip", "--command", remote]


def restart_remote(cluster: str) -> str:
    u = unit(cluster)
    return (f"sudo systemctl restart {u}; sleep 25; systemctl is-active {u}; "
            f'sudo journalctl -u {u} --since "-2min" --no-pager | tail -12')


def active_remote(cluster: str) -> str:
    return f"systemctl is-active {unit(cluster)}"


def journal_remote(cluster: str) -> str:
    return f'sudo journalctl -u {unit(cluster)} --since "-15min" --no-pager | tail -40'


def up_expr(cluster: str) -> str:
    return f'up{{cluster="{cluster}",role="mongos",job="{JOB}"}}'


def uptime_expr(cluster: str) -> str:
    return f'mongodb_instance_uptime_seconds{{cluster="{cluster}",role="mongos"}}'


def prom_cmd(expr: str) -> list:
    return ["gcx", "metrics", "query", expr, "-o", "json"]


def shell(cmd: list) -> str:
    return " ".join(f"'{c}'" if (" " in c or '"' in c or "{" in c) else c for c in cmd)


def validate(cluster: str, hosts_arg: str, role: str, soak_min: int) -> list:
    if role != "mongos":
        raise ValueError(f"role {role!r} refused: only --role mongos is supported "
                         "(change-stream and other roles are out of scope)")
    if cluster not in ROUTERS:
        raise ValueError(f"unknown cluster {cluster!r}; valid: {', '.join(ROUTERS)}")
    if not 0 <= soak_min <= 120:
        raise ValueError("--soak-min must be 0..120")
    parts = [p.strip() for p in hosts_arg.split(",")]
    if not parts or not all(p.isdigit() for p in parts):
        raise ValueError("--hosts must be comma-separated non-negative integers, e.g. 3,4,5")
    hosts = [int(p) for p in parts]
    count = ROUTERS[cluster]
    bad = [h for h in hosts if h >= count]
    if bad:
        raise ValueError(f"host(s) {bad} do not exist; {cluster} has 0..{count - 1}")
    if len(set(hosts)) != len(hosts):
        raise ValueError("--hosts contains duplicates")
    if len(hosts) >= count:
        raise ValueError("refusing: --hosts covers every router of the cluster")
    return hosts


def plan(cluster: str, hosts: list, soak_min: int, mute_id, execute: bool) -> str:
    L = ["DRY RUN (nothing executed; add --execute to run)" if not execute else "EXECUTE",
         f"cluster={cluster} hosts={','.join(map(str, hosts))} one at a time, soak {soak_min} min",
         "", "Preflight (before EACH host):",
         "  " + shell(deploy_cmd()) + "   # refuse if any run is in_progress/queued",
         "  " + shell(prom_cmd(up_expr(cluster))) + "   # all OTHER routers must be 1"]
    for n in hosts:
        L += ["", f"Host {host_name(cluster, n)}:",
              "  type the hostname to confirm",
              "  " + shell(ssh_cmd(cluster, n, restart_remote(cluster))),
              "  " + shell(prom_cmd(uptime_expr(cluster))) + f"   # {host_name(cluster, n)} < {UPTIME_MAX}s",
              "  " + shell(prom_cmd(up_expr(cluster))) + f"   # {host_name(cluster, n)} == 1 within {UP_TIMEOUT}s",
              f"  soak {soak_min} min; check connections back to baseline (~15 min)"]
    if mute_id:
        L += ["", f"At the end: /apollo-eng-devops:mute-alert expire {mute_id}"]
    return "\n".join(L)


def prom_values(expr: str) -> dict:
    """Return {instance-label: float}. Raises Stop if metrics tooling fails."""
    try:
        r = run_cmd(prom_cmd(expr), timeout=60)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise Stop(f"metrics tooling unavailable ({type(e).__name__}); use --skip-up-check "
                   "only if you verified peers another way") from e
    if r.returncode != 0:
        raise Stop("gcx metrics query failed (rc={})".format(r.returncode))
    try:
        data = json.loads(r.stdout)
    except ValueError as e:
        raise Stop("could not parse gcx output") from e
    items = data
    if isinstance(data, dict):
        items = (data.get("data") or data).get("result") if isinstance(
            data.get("data") or data, dict) else None
        items = items if items is not None else data.get("result", [])
    out = {}
    for it in items or []:
        try:
            m = it["metric"]
            out[m.get("instance") or m.get("host") or ""] = float(it["value"][1])
        except (KeyError, TypeError, ValueError, IndexError):
            continue
    return out


def find(values: dict, cluster: str, n: int):
    name = host_name(cluster, n)
    for k, v in values.items():
        if k == name or k.startswith(name + ".") or k.startswith(name + ":"):
            return v
    return None


def check_deploy() -> None:
    try:
        r = run_cmd(deploy_cmd(), timeout=60)
        runs = json.loads(r.stdout)
    except (OSError, ValueError, subprocess.TimeoutExpired) as e:
        raise Stop("cannot determine deploy state; refusing") from e
    if r.returncode != 0 or not isinstance(runs, list):
        raise Stop("cannot determine deploy state; refusing")
    busy = [x for x in runs if x.get("status") in BUSY]
    if busy:
        raise Stop("production deploy is running/queued; do not restart during a deploy")


def check_peers(cluster: str, target: int) -> None:
    vals = prom_values(up_expr(cluster))
    bad = []
    for n in range(ROUTERS[cluster]):
        if n == target:
            continue
        if find(vals, cluster, n) != 1.0:
            bad.append(host_name(cluster, n))
    if bad:
        raise Stop(f"peer routers not up==1 (or missing): {', '.join(bad)}")


def restart_one(cluster: str, n: int, soak_min: int, skip_up: bool) -> None:
    name = host_name(cluster, n)
    print(f"\n=== {name} ===")
    check_deploy()
    if skip_up:
        print("WARNING: --skip-up-check set; peer router health NOT verified.")
    else:
        check_peers(cluster, n)
    answer = input(f"Type the hostname ({name}) to restart it, anything else aborts: ")
    if answer.strip() != name:
        raise Stop("confirmation did not match; aborted, nothing restarted")
    print(f"restarting {name} ...")
    r = run_cmd(ssh_cmd(cluster, n, restart_remote(cluster)), timeout=240)
    lines = [ln.strip() for ln in (r.stdout or "").splitlines()]
    active = "active" in lines
    waited = 0
    while not active and waited < ACTIVE_TIMEOUT:
        _sleep(POLL)
        waited += POLL
        p = run_cmd(ssh_cmd(cluster, n, active_remote(cluster)), timeout=60)
        active = "active" in [ln.strip() for ln in (p.stdout or "").splitlines()]
    if not active:
        raise Stop(f"{name} not active after ~2 min")
    print(f"{name} active; verifying up==1 and uptime<{UPTIME_MAX}s ...")
    waited = 0
    while True:
        up = find(prom_values(up_expr(cluster)), cluster, n)
        ut = find(prom_values(uptime_expr(cluster)), cluster, n)
        if up == 1.0 and ut is not None and ut < UPTIME_MAX:
            break
        if waited >= UP_TIMEOUT:
            raise Stop(f"{name} up/uptime not healthy after 5 min (up={up}, uptime={ut})")
        _sleep(POLL)
        waited += POLL
    print(f"{name} verified. Soak {soak_min} min (watch connections and errors).")
    for left in range(soak_min, 0, -1):
        print(f"  soak: {left} min left")
        _sleep(60)


def main(argv: list | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cluster", required=True)
    ap.add_argument("--hosts", required=True, help="comma-separated router numbers, e.g. 3,4,5")
    ap.add_argument("--role", default="mongos")
    ap.add_argument("--soak-min", type=int, default=10)
    ap.add_argument("--mute-id", help="id from `/apollo-eng-devops:mute-alert create ...` (skill; fallback plugins/apollo-eng-devops/skills/mute-alert/scripts/mute_alert.py), only echoed as an end reminder")
    ap.add_argument("--skip-up-check", action="store_true", help="skip peer up==1 check (unsafe)")
    ap.add_argument("--execute", action="store_true", help="actually run (default: dry run)")
    a = ap.parse_args(argv)
    try:
        hosts = validate(a.cluster, a.hosts, a.role, a.soak_min)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    print(plan(a.cluster, hosts, a.soak_min, a.mute_id, a.execute))
    if not a.execute:
        return 0
    for n in hosts:
        try:
            restart_one(a.cluster, n, a.soak_min, a.skip_up_check)
        except Stop as e:
            print(f"\nSTOP: {e}. No further hosts touched.")
            print("Inspect: " + shell(ssh_cmd(a.cluster, n, journal_remote(a.cluster))))
            return 1
    print("\nDone. Verify connections at baseline and run /apollo-eng-devops:check-mongo "
          f"{a.cluster}.")
    if a.mute_id:
        print(f"Now expire the silence: /apollo-eng-devops:mute-alert expire {a.mute_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
