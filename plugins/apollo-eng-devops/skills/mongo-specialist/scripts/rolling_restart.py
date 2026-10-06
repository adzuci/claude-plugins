#!/usr/bin/env python3
"""Guarded, human-run helper: restart a SUBSET of prod mongos routers, one at a time.

DEFAULT IS A DRY RUN: prints the plan and exact commands, runs nothing.
--execute runs them for ONE host at a time with preflight checks, a typed-hostname
confirmation, restart, verification and a soak, and STOPS on the first failure.
Before each host a gate decides GO / WAIT / STOP from evidence (peer connections vs a
ceiling, and whether a leadgenie deploy stage is running or about to land); only GO proceeds.
Never reads or prints credentials. Agents must not run this with --execute.
"""

from __future__ import annotations

import argparse
import json
import shutil
import statistics
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone

# mongos counts per cluster (see references/mongo-clusters.md; re-check before acting).
ROUTERS = {
    "main": 16, "accounts": 6, "contacts": 6, "custom-objects": 6,
    "email": 6, "emailermessages": 6, "noncustomer": 12,
}
PROJECT = "indigo-lotus-415"
ZONE = "us-central1-c"
JOB = "integrations/mongodb"
BUSY = ("in_progress", "queued", "waiting", "pending", "requested")  # non-completed; fail-closed
ACTIVE_JOB = ("in_progress", "queued", "waiting", "pending")
RESTART_MIN = 3          # one router restart
RECOVERY_MIN = 15        # connections back to baseline
DEPLOY_MIN = 11          # typical `deploy / sidekiq-workers`, used when history is unreadable
FALLBACK_LEAD_MIN = 49   # shortest queue-to-deploy-stage seen (2026-09-30: 49, 51, 61)
HISTORY = 5
# Which router group each `deploy / <name>` job's pods use (get_mongos_distribution in
# leadgenie config/application.rb: `-api` pods take the first half, everything else the second).
# karafka is code-derived (no `-api` in its hostname), not confirmed on a live pod.
# Jobs not listed here are unknown and BLOCK (fail closed).
JOB_GROUP = {
    "rails-api": "web", "events-api": "web", "tracking-api": "web", "mcp-api": "web",
    "sidekiq-workers": "worker", "sidekiq-workers-nowait": "worker", "sidekiq-metrics": "worker",
    "leadgenie-cron": "worker", "karafka": "worker",
}
# Default peer-connection ceiling per group (judgment call, 2026-09-30 observations).
# web (routers 0-2): steady ~14.5k, peaked ~19.5k in a web rollout; one restart adds ~7.25k to
# each peer -> ~21.8k, so 22k allows a steady-state restart only. worker (3-5): steady
# ~9.5-10.2k, peaked ~11.8k; one restart adds ~4.9k -> 16k is ~web steady + 10%.
GROUP_CEILING = {"web": 22000, "worker": 16000}
CONN_RETRY_MIN = 10
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


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _have(tool: str) -> bool:
    return shutil.which(tool) is not None


def host_name(cluster: str, n: int) -> str:
    return f"mongos-{cluster}-{n}"


def unit(cluster: str) -> str:
    return f"mongos-{cluster}.service"


def deploy_cmd() -> list:
    return ["gh", "run", "list", "--repo", "apolloio/leadgenie", "--workflow", "production.yml",
            "--limit", "6", "--json", "databaseId,status,conclusion,createdAt,displayTitle"]


def jobs_cmd(run_id) -> list:
    return ["gh", "run", "view", str(run_id), "--repo", "apolloio/leadgenie", "--json", "jobs"]


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


def conns_expr(cluster: str) -> str:
    return f'mongodb_connections{{cluster="{cluster}",role="mongos",state="current"}}'


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
         "  " + shell(deploy_cmd()) + "   # GATE: deploy stage running/imminent -> WAIT",
         "  " + shell(prom_cmd(conns_expr(cluster))) + "   # GATE: predicted peer load vs ceiling",
         "  " + shell(prom_cmd(up_expr(cluster))) + "   # all OTHER routers must be 1"]
    for n in hosts:
        L += ["", f"Host {host_name(cluster, n)}:",
              "  type the hostname to confirm",
              "  " + shell(ssh_cmd(cluster, n, restart_remote(cluster))),
              "  " + shell(prom_cmd(uptime_expr(cluster))) + f"   # {host_name(cluster, n)} < {UPTIME_MAX}s",
              "  " + shell(prom_cmd(up_expr(cluster))) + f"   # {host_name(cluster, n)} == 1 within {UP_TIMEOUT}s",
              f"  soak {soak_min} min; check connections back to baseline (~15 min)"]
    if mute_id:
        L += ["", f"At the end (keep the silence until >= 10 min after the last restart; the alert fires ~4 min after): /apollo-eng-devops:mute-alert expire {mute_id}"]
    return "\n".join(L)


def prom_values(expr: str) -> dict:
    """Return {instance-label: float}. Raises Stop if metrics tooling fails."""
    try:
        r = run_cmd(prom_cmd(expr), timeout=60)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise Stop(f"metrics tooling unavailable ({type(e).__name__})") from e
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


def gh_json(cmd: list):
    """Run a read-only gh command and parse its JSON; any problem fails closed."""
    try:
        r = run_cmd(cmd, timeout=60)
        data = json.loads(r.stdout)
    except (OSError, ValueError, subprocess.TimeoutExpired) as e:
        raise Stop("cannot read gh output; failing closed") from e
    if r.returncode != 0:
        raise Stop(f"gh failed (rc={r.returncode}); failing closed")
    return data


def ts(value) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as e:
        raise Stop(f"unparseable timestamp {value!r}; failing closed") from e


def run_jobs(run_id) -> list:
    data = gh_json(jobs_cmd(run_id))
    jobs = data.get("jobs") if isinstance(data, dict) else None
    if not isinstance(jobs, list):
        raise Stop("unexpected gh jobs output; failing closed")
    return [j for j in jobs if isinstance(j, dict) and str(j.get("name", "")).startswith("deploy /")]


def started(job):
    v = job.get("startedAt")
    return ts(v) if v and ts(v).year > 2000 else None  # skipped jobs report year 1


def minutes(delta) -> float:
    return delta.total_seconds() / 60


def history(runs: list) -> list:
    """(createdAt, deploy jobs) for the last successful runs."""
    ok = [r for r in runs if r.get("status") == "completed" and r.get("conclusion") == "success"]
    return [(ts(r.get("createdAt")), run_jobs(r["databaseId"])) for r in ok[:HISTORY]]


def typical_min(name: str, hist: list) -> float:
    d = [minutes(ts(j["completedAt"]) - started(j)) for _, js in hist for j in js
         if j.get("name") == name and started(j) and j.get("completedAt")]
    return statistics.median(d) if d else DEPLOY_MIN


def lead_min(hist: list):
    """Median minutes from run creation to its first deploy job; (value, samples)."""
    d = [minutes(min(s for s in map(started, js) if s) - created)
         for created, js in hist if any(map(started, js))]
    return (statistics.median(d), len(d)) if d else (FALLBACK_LEAD_MIN, 0)


def hhmm(t: datetime) -> str:
    return t.astimezone(timezone.utc).strftime("%H:%M")


def group_of(cluster: str, n: int) -> str:
    return "web" if n < ROUTERS[cluster] // 2 else "worker"


def deploy_gate(group: str, soak_min: int, margin_min: int):
    """(decision, reasons, retry) from the leadgenie production workflow.

    A deploy job blocks if it serves the target's router group or is unknown; jobs of the
    other group are listed as ignored."""
    runs = gh_json(deploy_cmd())
    if not isinstance(runs, list):
        raise Stop("unexpected gh run list output; failing closed")
    now = _now()
    live = [r for r in runs if r.get("status") in BUSY]
    if not live:
        return "GO", ["deploy: no production run in flight"], None
    hist = history(runs)
    active, ignored, waiting = [], [], []
    for r in live:
        jobs = run_jobs(r.get("databaseId"))
        for j in jobs:
            if j.get("status") in ACTIVE_JOB:
                g = JOB_GROUP.get(j["name"][len("deploy / "):])
                (ignored if g and g != group else active).append(j)
        if not jobs:  # deploy stage not reached yet
            waiting.append(ts(r.get("createdAt")))
    skipped = [f"deploy: ignored '{j['name']}' ({j['status']}): serves the "
               f"{JOB_GROUP[j['name'][len('deploy / '):]]} router group, target is {group}"
               for j in ignored]
    if active:
        reasons, etas = [], []
        for j in active:
            eta = (started(j) or now) + timedelta(minutes=typical_min(j["name"], hist))
            etas.append(eta)
            reasons.append(f"deploy: '{j['name']}' {j['status']}, typical "
                           f"{typical_min(j['name'], hist):.0f} min, ETA {hhmm(eta)} UTC")
        return "WAIT", reasons + skipped, max(max(etas), now)
    if not waiting:
        return "GO", skipped, None
    lead, n = lead_min(hist)
    created = min(waiting)
    remaining = lead - minutes(now - created)
    need = RESTART_MIN + soak_min + RECOVERY_MIN + margin_min
    src = f"median of {n} runs" if n else "fallback, no history"
    why = (f"deploy: run created {hhmm(created)} UTC has no deploy job yet; est. {remaining:.0f} min "
           f"to deploy stage (lead {lead:.0f} min, {src}); need {need} min "
           f"(restart {RESTART_MIN} + soak {soak_min} + recovery {RECOVERY_MIN} + margin {margin_min})")
    if remaining >= need:
        return "GO", [why] + skipped, None
    retry = max(created + timedelta(minutes=lead + DEPLOY_MIN), now + timedelta(minutes=5))
    return "WAIT", [why] + skipped, retry


def conn_gate(cluster: str, n: int, max_conns):
    """Predict peer load if router n restarts; compare to a ceiling."""
    cur = prom_values(conns_expr(cluster))
    count = ROUTERS[cluster]
    half = count // 2  # web/API pods use the first half, sidekiq/cron the second
    name = group_of(cluster, n)
    group = range(0, half) if name == "web" else range(half, count)
    mates = [m for m in group if m != n]
    target, peers = find(cur, cluster, n), {m: find(cur, cluster, m) for m in mates}
    if target is None or None in peers.values():
        raise Stop(f"missing mongodb_connections series for {cluster} group {list(group)}")
    share = target / len(mates)
    pred = {m: v + share for m, v in peers.items()}
    if max_conns:
        ceiling, how = float(max_conns), "--max-conns"
    else:
        ceiling = GROUP_CEILING[name]
        how = f"default for the {name} group (routers {group[0]}-{group[-1]}); --max-conns overrides"
    worst = max(pred, key=pred.get)
    why = [f"connections: {host_name(cluster, n)} has {target:,.0f}; predicted peer max "
           f"{pred[worst]:,.0f} on {host_name(cluster, worst)} (+{share:,.0f} each)",
           f"connections: ceiling {ceiling:,.0f}, {how}"]
    if pred[worst] > ceiling:
        return "WAIT", why, _now() + timedelta(minutes=CONN_RETRY_MIN)
    return "GO", why, None


def gate(cluster: str, n: int, soak_min: int, margin_min: int, max_conns):
    """Combine both signals -> (GO|WAIT|STOP, reasons, earliest retry)."""
    try:
        results = [deploy_gate(group_of(cluster, n), soak_min, margin_min), conn_gate(cluster, n, max_conns)]
    except Stop as e:
        return "STOP", [str(e)], None
    reasons = [r for _, rs, _ in results for r in rs]
    retries = [t for _, _, t in results if t]
    if any(d == "WAIT" for d, _, _ in results):
        return "WAIT", reasons, max(retries)
    return "GO", reasons, None


def format_gate(decision: str, reasons: list, retry) -> str:
    L = [f"GATE: {decision}"] + [f"  - {r}" for r in reasons]
    if decision == "WAIT" and retry:
        L.append(f"  - earliest retry {hhmm(retry)} UTC")
    return "\n".join(L)


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


def restart_one(cluster: str, n: int, soak_min: int, skip_up: bool,
                margin_min: int = 10, max_conns=None) -> None:
    name = host_name(cluster, n)
    print(f"\n=== {name} ===")
    decision, reasons, retry = gate(cluster, n, soak_min, margin_min, max_conns)
    print(format_gate(decision, reasons, retry))
    if decision != "GO":
        raise Stop(f"gate {decision}; nothing restarted")
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
    ap.add_argument("--max-conns", type=int, help="peer connection ceiling (default: per router group, see GROUP_CEILING)")
    ap.add_argument("--deploy-margin-min", type=int, default=10,
                    help="extra minutes required before a queued deploy reaches its deploy stage")
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
        for n in hosts:
            print(f"\nGate preview for {host_name(a.cluster, n)} (read-only):")
            if _have("gh") and _have("gcx"):
                print(format_gate(*gate(a.cluster, n, a.soak_min, a.deploy_margin_min, a.max_conns)))
            else:
                print("  gh/gcx not found; would check deploy stage ETA and predicted peer "
                      "connections vs ceiling, then print GATE: GO|WAIT|STOP")
        return 0
    for n in hosts:
        try:
            restart_one(a.cluster, n, a.soak_min, a.skip_up_check,
                        a.deploy_margin_min, a.max_conns)
        except Stop as e:
            print(f"\nSTOP: {e}. No further hosts touched.")
            print("Inspect: " + shell(ssh_cmd(a.cluster, n, journal_remote(a.cluster))))
            return 1
    print("\nDone. Verify connections at baseline and run /apollo-eng-devops:check-mongo "
          f"{a.cluster}.")
    if a.mute_id:
        print("Expire the silence only once >= 10 min after the last restart (the alert fires ~4 min "
              f"after; if it would lapse first, expire and recreate): /apollo-eng-devops:mute-alert expire {a.mute_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
