#!/usr/bin/env python3
"""Read-only Terraform drift check against HCP Terraform (TFC) workspaces.

For each workspace it queues a plan-only run on the configuration version of the
last applied run, so the plan compares live infra with what was last applied.
Plan-only runs cannot be applied. Output is a compact summary: resource addresses
and changed attribute *names*, never values.

Usage:
  drift_check.py [--workspaces a,b] [--format slack|json] [--timeout 900]
                 [--post-channel <id>]

Exit: 0 report printed, 1 fatal (no token, API down), 2 bad input.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys
import time
import traceback
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

API = "https://app.terraform.io/api/v2"
APP = "https://app.terraform.io/app"
CREDS = Path.home() / ".terraform.d" / "credentials.tfrc.json"
REF = Path(__file__).resolve().parent.parent / "references" / "workspaces.json"
NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")
PLAN_DONE = {"finished"}
PLAN_FAILED = {"errored", "canceled", "discarded", "force_canceled", "unreachable"}
SKILL = "/apollo-eng-devops:resolve-drift"


# --- pure helpers -----------------------------------------------------------


def resolve_token(env, creds_path=CREDS):
    """TFE_TOKEN, then TF_API_TOKEN, then the terraform CLI credentials file."""
    for key in ("TFE_TOKEN", "TF_API_TOKEN"):
        if env.get(key):
            return env[key]
    try:
        data = json.loads(Path(creds_path).read_text())
        return data["credentials"]["app.terraform.io"]["token"]
    except (OSError, KeyError, ValueError):
        return None


def load_workspaces(ref_path, override):
    ref = json.loads(Path(ref_path).read_text())
    if override:
        names = [n.strip() for n in override.split(",") if n.strip()]
    else:
        names = [w["name"] for w in ref["workspaces"]]
    bad = [n for n in names if not NAME_RE.match(n)]
    if bad:
        raise ValueError(f"invalid workspace name(s): {', '.join(bad)}")
    return ref["organization"], names


def changed_attrs(before, after, after_unknown, limit=5):
    """Top-level attribute names that differ. Values are never returned."""
    before, after, unknown = before or {}, after or {}, after_unknown or {}
    keys = sorted(
        k
        for k in set(before) | set(after) | set(unknown)
        if unknown.get(k) is True or before.get(k) != after.get(k)
    )
    if len(keys) > limit:
        return keys[:limit] + [f"+{len(keys) - limit}"]
    return keys


def _action(actions):
    if set(actions) == {"delete", "create"}:
        return "replace"
    return actions[0] if actions else "no-op"


def _entry(rc):
    ch = rc.get("change", {})
    action = _action(ch.get("actions", []))
    attrs = [] if action in ("create", "delete") else changed_attrs(
        ch.get("before"), ch.get("after"), ch.get("after_unknown")
    )
    return {"address": rc["address"], "action": action, "attrs": attrs}


def summarize_plan(plan, top=10):
    """Drift counts only when Terraform would act on it (or the resource is gone).

    Refresh churn in computed fields (etag, updated, state_details) shows up in
    resource_drift with no planned change; that is counted as cosmetic.
    """
    counts = {"drift": 0, "cosmetic": 0, "add": 0, "change": 0, "destroy": 0, "replace": 0}
    drift, pending = [], []
    key = {"create": "add", "update": "change", "delete": "destroy", "replace": "replace"}
    for field in ("resource_changes", "resource_drift"):
        if field not in plan:
            print(f"warning: plan JSON is missing {field}", file=sys.stderr)
    for rc in plan.get("resource_changes") or []:
        e = _entry(rc)
        if rc.get("mode") != "managed" or e["action"] not in key:
            continue
        counts[key[e["action"]]] += 1
        pending.append(e)
    planned = {e["address"] for e in pending}
    for rc in plan.get("resource_drift") or []:
        if rc.get("mode") != "managed":
            continue
        e = _entry(rc)
        if e["action"] == "delete" or e["address"] in planned:
            counts["drift"] += 1
            drift.append(e)
        else:
            counts["cosmetic"] += 1
    return {"counts": counts, "drift": drift[:top], "pending": pending[:top]}


def overall(results):
    states = {r["status"] for r in results}
    for s in ("drift", "error", "pending"):
        if s in states:
            return s
    return "clean"


def slack_escape(text):
    """Plan strings are data: neutralise Slack mentions/links and code-span breaks."""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("`", "'")


def _fmt_entries(entries):
    lines = []
    for e in entries:
        attrs = f" ({', '.join(slack_escape(a) for a in e['attrs'])})" if e["attrs"] else ""
        lines.append(f"  • `{slack_escape(e['address'])}` {e['action']}{attrs}")
    return lines


def format_slack(results, date):
    head = f"*Terraform drift · {date}*"
    cosmetic = sum(r.get("counts", {}).get("cosmetic", 0) for r in results)
    note = f"; {cosmetic} cosmetic refresh-only diffs ignored" if cosmetic else ""
    if overall(results) == "clean":
        names = ", ".join(r["workspace"] for r in results)
        return f"{head} · no drift in {len(results)} workspaces ({names}){note}"
    lines = [head]
    clean = [r["workspace"] for r in results if r["status"] == "clean"]
    for r in results:
        if r["status"] == "clean":
            continue
        link = f" · <{r['run_url']}|run>" if r.get("run_url") else ""
        if r["status"] == "error":
            lines.append(f"*{r['workspace']}* · :warning: couldn't check: {r['error']}{link}")
            continue
        c = r["counts"]
        lines.append(
            f"*{r['workspace']}* · {c['drift']} drifted · pending {c['add']} add, "
            f"{c['change']} change, {c['destroy']} destroy, {c['replace']} replace{link}"
        )
        lines += _fmt_entries(r["drift"])
        if r["pending"] and not r["drift"]:
            lines += _fmt_entries(r["pending"][:3])
        lines.append(f"  → `{SKILL} {r['workspace']}`")
    if clean:
        lines.append(f"_Clean: {', '.join(clean)}_")
    if cosmetic:
        lines.append(f"_{cosmetic} cosmetic refresh-only diffs ignored_")
    return "\n".join(lines)


# --- TFC calls --------------------------------------------------------------


def make_api(token):
    def api(method, path, body=None):
        req = urllib.request.Request(
            API + path,
            method=method,
            data=json.dumps(body).encode() if body is not None else None,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/vnd.api+json",
            },
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
        return json.loads(raw) if raw else {}

    return api


def check_workspace(api, org, name, timeout=900, poll=15):
    result = {"workspace": name, "status": "error", "run_url": None}
    try:
        ws_id = api("GET", f"/organizations/{org}/workspaces/{name}")["data"]["id"]
        runs = api("GET", f"/workspaces/{ws_id}/runs?filter%5Bstatus%5D=applied&page%5Bsize%5D=1")
        if not runs["data"]:
            result["error"] = "no applied run to compare against"
            return result
        cv = runs["data"][0]["relationships"]["configuration-version"]["data"]["id"]
        body = {
            "data": {
                "type": "runs",
                "attributes": {"plan-only": True, "message": "resolve-drift: weekly read-only drift check"},
                "relationships": {
                    "workspace": {"data": {"type": "workspaces", "id": ws_id}},
                    "configuration-version": {"data": {"type": "configuration-versions", "id": cv}},
                },
            }
        }
        run = api("POST", "/runs", body)["data"]
        run_id = run["id"]
        result["run_url"] = f"{APP}/{org}/workspaces/{name}/runs/{run_id}"
        plan_id = run["relationships"]["plan"]["data"]["id"]
        deadline = time.monotonic() + timeout
        while True:
            status = api("GET", f"/plans/{plan_id}")["data"]["attributes"]["status"]
            if status in PLAN_DONE:
                break
            if status in PLAN_FAILED:
                result["error"] = f"plan {status}"
                return result
            if time.monotonic() >= deadline:
                api("POST", f"/runs/{run_id}/actions/cancel", {"comment": "resolve-drift timeout"})
                result["error"] = f"timeout after {timeout}s (run canceled)"
                return result
            time.sleep(poll)
        summary = summarize_plan(api("GET", f"/plans/{plan_id}/json-output"))
    except urllib.error.HTTPError as e:
        hint = {401: " (token invalid)", 403: " (token lacks permission)", 404: " (workspace not found or no access)"}
        result["error"] = f"TFC API HTTP {e.code}{hint.get(e.code, '')}"
        return result
    except (urllib.error.URLError, KeyError, IndexError, ValueError) as e:
        if isinstance(e, (KeyError, IndexError)):
            traceback.print_exc(file=sys.stderr)
        result["error"] = f"TFC API error: {type(e).__name__}"
        return result
    c = summary["counts"]
    has_pending = any(c[k] for k in ("add", "change", "destroy", "replace"))
    result.update(summary)
    result["status"] = "drift" if c["drift"] else ("pending" if has_pending else "clean")
    return result


def post_slack(text, channel, token):
    req = urllib.request.Request(
        "https://slack.com/api/chat.postMessage",
        data=json.dumps({"channel": channel, "text": text, "unfurl_links": False}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    if not data.get("ok"):
        raise RuntimeError(f"Slack post failed: {data.get('error')}")
    return data.get("ts")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--workspaces", help="comma list; default references/workspaces.json")
    p.add_argument("--format", choices=["slack", "json"], default="slack")
    p.add_argument("--timeout", type=int, default=900, help="per-workspace seconds")
    p.add_argument("--post-channel", help="Slack channel/user id; needs SLACK_BOT_TOKEN")
    args = p.parse_args(argv)

    try:
        org, names = load_workspaces(REF, args.workspaces)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    token = resolve_token(os.environ)
    if not token:
        print("error: no TFC token (set TFE_TOKEN or run `terraform login`)", file=sys.stderr)
        return 1

    api = make_api(token)
    # Four concurrent plans limit TFC API pressure; the remaining default
    # workspaces queue in-process and are still bounded by their own timeout.
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda n: check_workspace(api, org, n, args.timeout), names))

    date = _dt.date.today().isoformat()
    if args.format == "json":
        print(json.dumps({"date": date, "overall": overall(results), "results": results}, indent=1))
    else:
        text = format_slack(results, date)
        print(text)
        if args.post_channel:
            slack = os.environ.get("SLACK_BOT_TOKEN")
            if not slack:
                print("error: --post-channel needs SLACK_BOT_TOKEN", file=sys.stderr)
                return 1
            post_slack(text, args.post_channel, slack)
            print(f"posted to {args.post_channel}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
