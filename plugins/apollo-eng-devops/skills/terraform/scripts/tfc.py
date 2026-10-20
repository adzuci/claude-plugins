#!/usr/bin/env python3
"""Compact Terraform Cloud helper. Prints summaries, never raw plan JSON or tokens.

Read-only: status, run, plan, find-workspaces.
Mutating (require --yes): apply, discard, cancel, unlock, force-unlock.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HOST = "app.terraform.io"
API = f"https://{HOST}/api/v2"
IAM_RE = re.compile(r"(_iam_|_iam$|^aws_iam|^azurerm_role_|_role_assignment|_service_account_key)")
URL_RE = re.compile(r"^https://app\.terraform\.io/app/([^/]+)/workspaces/([^/]+)(?:/runs/(run-[A-Za-z0-9]+))?")


def parse_run_url(url: str):
    m = URL_RE.match(url)
    if not m:
        raise ValueError(f"not an {HOST} workspace or run URL: {url}")
    return m.group(1), m.group(2), m.group(3)


def load_token(home: Path | None = None) -> str:
    for var in ("TFE_TOKEN", "TF_TOKEN_app_terraform_io"):
        if os.environ.get(var):
            return os.environ[var]
    path = (home or Path.home()) / ".terraform.d" / "credentials.tfrc.json"
    try:
        return json.loads(path.read_text())["credentials"][HOST]["token"]
    except (OSError, KeyError, ValueError):
        raise RuntimeError("no TFC token: run `terraform login` or set TFE_TOKEN")


def summarize_plan(plan: dict, cap: int = 25) -> dict:
    counts = {"create": 0, "update": 0, "delete": 0, "replace": 0}
    destroy, replace, iam = [], [], []
    for rc in plan.get("resource_changes", []):
        actions = rc.get("change", {}).get("actions", [])
        addr, typ = rc.get("address", "?"), rc.get("type", "")
        if actions == ["create"]:
            kind = "create"
        elif actions == ["update"]:
            kind = "update"
        elif actions == ["delete"]:
            kind = "delete"
        elif set(actions) == {"delete", "create"}:
            kind = "replace"
        else:
            continue
        counts[kind] += 1
        if kind == "delete":
            destroy.append(addr)
        elif kind == "replace":
            replace.append(addr)
        if IAM_RE.search(typ):
            iam.append(addr)
    return {"counts": counts, "destroy": destroy[:cap], "replace": replace[:cap], "iam": iam[:cap]}


def dirs_from_files(files: list[str]) -> list[str]:
    out = set()
    for f in files:
        if f.endswith((".tf", ".tfvars", ".tf.json")):
            out.add(os.path.dirname(f) or ".")
    return sorted(out)


def match_workspaces(workspaces: list[dict], dirs: list[str]) -> list[dict]:
    wanted = {d.strip("/") or "." for d in dirs}
    return [w for w in workspaces if (w.get("working-directory") or ".").strip("/") in wanted]


def workspace_from_provider_tf(text: str):
    """Return (org, workspace) from a terraform cloud/backend block, else None."""
    org = re.search(r'organization\s*=\s*"([^"]+)"', text)
    name = re.search(r'\bname\s*=\s*"([^"]+)"', text)
    return (org.group(1), name.group(1)) if org and name else None


EXCLUDE_RE = re.compile(
    r"terraform/.*modules|terraform/.*/tfc-permissions|terraform/gcp/prod/(ops_agent|validation|cf-functions)"
    r"|terraform/gcp/staging/.*mongo.*|terraform/.*cf-functions?"
)
COMMENT_RE = re.compile(r"Terraform Cloud Plan Output on (\S+)")
COUNTS_RE = re.compile(r"Plan: (\d+) to add, (\d+) to change, (\d+) to destroy")
RUN_RE = re.compile(r"/runs/(run-[A-Za-z0-9]+)")


def plan_required(path: str) -> bool:
    """Mirror devops tfc-plan.yml: does a changed file trigger a PR plan?"""
    return path.startswith("terraform/") and not EXCLUDE_RE.search(path)


def workspace_name_for_path(path: str):
    """Mirror tfc-plan.yml naming: dir under terraform/, '/' and '_' become '-'."""
    if not path.startswith("terraform/"):
        return None
    rel = os.path.dirname(path)[len("terraform/"):]
    return rel.replace("/", "-").replace("_", "-") or None


def workspaces_for_files(files: list[str]):
    ws, skipped = [], []
    for f in files:
        if plan_required(f):
            name = workspace_name_for_path(f)
            if name and name not in ws:
                ws.append(name)
        elif f.startswith("terraform/"):
            skipped.append(f)
    return ws, skipped


def parse_plan_comment(body: str):
    m, c, r = COMMENT_RE.search(body), COUNTS_RE.search(body), RUN_RE.search(body)
    if not (m and c and r):
        return None
    return {"workspace": m.group(1), "add": int(c.group(1)), "change": int(c.group(2)),
            "destroy": int(c.group(3)), "run": r.group(1)}


def pick_plan_run(runs: list[dict], since: str):
    """Newest plan-only run created at or after `since` (ISO8601 UTC, lexically comparable)."""
    cands = [r for r in runs if r["attributes"].get("plan-only") and r["attributes"]["created-at"] >= since]
    return max(cands, key=lambda r: r["attributes"]["created-at"]) if cands else None


def lock_summary(ws: dict, run: dict | None) -> str:
    if not ws.get("attributes", {}).get("locked"):
        return "unlocked"
    holder = ws.get("relationships", {}).get("locked-by", {}).get("data") or {}
    s = f"locked by {holder.get('type', '?')} {holder.get('id', '?')}"
    if run:
        s += f" (status {run['attributes']['status']}, created {run['attributes']['created-at']})"
    return s


def require_yes(yes: bool, what: str) -> None:
    if not yes:
        sys.exit(f"refusing to {what} without --yes (confirm with the user first)")


def api(method: str, path: str, body: dict | None = None, raw: bool = False):
    req = urllib.request.Request(
        path if path.startswith("http") else f"{API}{path}",
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Authorization": f"Bearer {load_token()}",
            "Content-Type": "application/vnd.api+json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read()
    except urllib.error.HTTPError as e:
        sys.exit(f"TFC API {method} {path.split('?')[0]} -> {e.code} {e.reason}")
    if raw:
        return data
    return json.loads(data) if data else {}


def get_workspace(org: str, name: str) -> dict:
    return api("GET", f"/organizations/{org}/workspaces/{urllib.parse.quote(name)}")["data"]


def cmd_status(a):
    org, name, _ = parse_run_url(a.target) if a.target.startswith("http") else (a.org, a.target, None)
    ws = get_workspace(org, name)
    cur = ws.get("relationships", {}).get("current-run", {}).get("data")
    run = api("GET", f"/runs/{cur['id']}")["data"] if cur else None
    locker = ws.get("relationships", {}).get("locked-by", {}).get("data")
    lock_run = run if locker and cur and locker["id"] == cur["id"] else None
    print(f"workspace: {org}/{name}")
    print(f"lock: {lock_summary(ws, lock_run)}")
    if run:
        at = run["attributes"]
        print(f"current run: {run['id']} status={at['status']} source={at.get('source')} message={at.get('message')!r}")
    print(f"link: https://{HOST}/app/{org}/workspaces/{name}")


def cmd_run(a):
    _, _, run_id = parse_run_url(a.target) if a.target.startswith("http") else (None, None, a.target)
    r = api("GET", f"/runs/{run_id}")["data"]
    at = r["attributes"]
    print(f"{r['id']} status={at['status']} actions={ {k: v for k, v in at.get('actions', {}).items() if v} }")
    print(f"permissions: { {k: v for k, v in at.get('permissions', {}).items() if v} }")
    print(f"has-changes={at.get('has-changes')} refresh-only={at.get('refresh-only')} plan-only={at.get('plan-only')}")


def cmd_plan(a):
    _, _, run_id = parse_run_url(a.target) if a.target.startswith("http") else (None, None, a.target)
    plan_id = api("GET", f"/runs/{run_id}")["data"]["relationships"]["plan"]["data"]["id"]
    plan = json.loads(api("GET", f"/plans/{plan_id}/json-output", raw=True))
    print(json.dumps(summarize_plan(plan), indent=1))


def gh_json(args: list[str]):
    out = subprocess.run(["gh", *args], capture_output=True, text=True)
    if out.returncode:
        sys.exit(f"gh {' '.join(args[:3])} failed: {out.stderr.strip()[:200]}")
    return json.loads(out.stdout)


def plan_for_run(run_id: str) -> dict:
    plan_id = api("GET", f"/runs/{run_id}")["data"]["relationships"]["plan"]["data"]["id"]
    return summarize_plan(json.loads(api("GET", f"/plans/{plan_id}/json-output", raw=True)))


def cmd_pr_plans(a):
    pr = gh_json(["pr", "view", a.pr, "--repo", a.repo, "--json",
                  "files,comments,headRefOid,commits,state,isDraft"])
    files = [f["path"] for f in pr["files"]]
    workspaces, skipped = workspaces_for_files(files)
    since = max((c["committedDate"] for c in pr["commits"]), default="")
    comments = {}
    for c in pr["comments"]:
        parsed = parse_plan_comment(c["body"])
        if parsed:
            comments[parsed["workspace"]] = parsed
    print(f"PR {a.repo}#{a.pr} state={pr['state']} draft={pr['isDraft']} head={pr['headRefOid'][:8]}")
    if skipped:
        print(f"no PR plan for (excluded paths): {skipped[:10]}")
    if not workspaces:
        print("no plannable workspaces in this PR")
        return
    for name in workspaces:
        print(f"\n== {name}")
        cm = comments.get(name)
        if cm:
            print(f"PR comment: +{cm['add']} ~{cm['change']} -{cm['destroy']} run={cm['run']}")
        try:
            ws = get_workspace(a.org, name)
        except SystemExit as e:
            print(f"workspace lookup failed: {e}")
            continue
        run = None
        if cm:
            cand = api("GET", f"/runs/{cm['run']}")["data"]
            run = pick_plan_run([cand], since)
        if not run:
            # plan-only (speculative) runs are hidden from the default run list
            q = f"/workspaces/{ws['id']}/runs?page%5Bsize%5D=20&filter%5Boperation%5D=plan_only"
            run = pick_plan_run(api("GET", q)["data"], since)
        if not run:
            print(f"no plan-only run since {since}; the PR plan may not have run or finished")
            continue
        at = run["attributes"]
        print(f"TFC run: {run['id']} status={at['status']} created={at['created-at']}")
        if cm and cm["run"] != run["id"]:
            print("note: PR comment run was stale or missing; used newest TFC plan-only run since the last commit")
        if at["status"] in ("planned_and_finished", "planned", "cost_estimated", "policy_checked", "policy_soft_failed", "policy_override"):
            print(json.dumps(plan_for_run(run["id"]), indent=1))
        elif at["status"] == "errored":
            print("plan errored: open the run in TFC for the error")
        else:
            print("plan not finished yet")


def cmd_find(a):
    r = api("GET", f"/organizations/{a.org}/workspaces?page%5Bsize%5D=100&search%5Bname%5D={urllib.parse.quote(a.search or '')}")
    wss = [{"name": w["attributes"]["name"], "working-directory": w["attributes"].get("working-directory")} for w in r["data"]]
    print(json.dumps(match_workspaces(wss, a.dirs) if a.dirs else wss))


def cmd_mutate(a):
    action = a.cmd
    require_yes(a.yes, f"{action} {a.target}")
    if action in ("apply", "discard", "cancel"):
        _, _, run_id = parse_run_url(a.target) if a.target.startswith("http") else (None, None, a.target)
        api("POST", f"/runs/{run_id}/actions/{action}", {"comment": a.comment or f"{action} via terraform skill"})
    else:
        org, name, _ = parse_run_url(a.target) if a.target.startswith("http") else (a.org, a.target, None)
        ws = get_workspace(org, name)
        api("POST", f"/workspaces/{ws['id']}/actions/{'force-unlock' if action == 'force-unlock' else 'unlock'}")
    print(f"{action}: ok ({a.target})")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--org", default="apolloio")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, fn in (("status", cmd_status), ("run", cmd_run), ("plan", cmd_plan)):
        s = sub.add_parser(name)
        s.add_argument("target")
        s.set_defaults(fn=fn)
    s = sub.add_parser("pr-plans")
    s.add_argument("pr", help="PR number or URL")
    s.add_argument("--repo", default="apolloio/devops")
    s.set_defaults(fn=cmd_pr_plans)
    s = sub.add_parser("find-workspaces")
    s.add_argument("--search")
    s.add_argument("--dirs", nargs="*")
    s.set_defaults(fn=cmd_find)
    for name in ("apply", "discard", "cancel", "unlock", "force-unlock"):
        s = sub.add_parser(name)
        s.add_argument("target")
        s.add_argument("--yes", action="store_true")
        s.add_argument("--comment")
        s.set_defaults(fn=cmd_mutate)
    a = p.parse_args(argv)
    try:
        a.fn(a)
    except (RuntimeError, ValueError) as e:
        sys.exit(str(e))


if __name__ == "__main__":
    main()
