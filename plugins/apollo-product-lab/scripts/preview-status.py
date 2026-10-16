#!/usr/bin/env python3
"""Report whether the current PR head has a successful preview deployment."""
import argparse
import json
import re
import subprocess
import sys
import time


def run(cmd, cwd=None):
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    except FileNotFoundError:
        return 127, ""
    return result.returncode, result.stdout.strip()


def default_gh(args, cwd=None):
    return run(["gh"] + list(args), cwd)


def _gh_json(gh, args):
    code, output = gh(args)
    if code:
        raise RuntimeError("gh %s failed" % " ".join(args[:3]))
    try:
        return json.loads(output)
    except (TypeError, ValueError):
        raise RuntimeError("gh returned invalid JSON")


def _repo_args(repo):
    return ["--repo", repo] if repo else []


def _workflow_name(run):
    return run.get("workflowName") or run.get("name") or ""


def _latest(runs):
    return max(runs, key=lambda item: (item.get("createdAt") or "", item.get("databaseId") or 0), default=None)


def inspect_preview(pr, repo=None, workflow="preview", wait=0, gh=default_gh, sleep=time.sleep, clock=time.monotonic):
    pr_data = _gh_json(gh, ["pr", "view", str(pr), "--json", "headRefOid,headRefName,url"] + _repo_args(repo))
    head_sha = pr_data.get("headRefOid")
    head_branch = pr_data.get("headRefName")
    if not head_sha:
        raise RuntimeError("PR has no head sha")
    try:
        matcher = re.compile(workflow, re.I)
    except re.error as exc:
        raise ValueError("invalid --workflow regex: %s" % exc)

    deadline = clock() + max(wait, 0)
    while True:
        runs = _gh_json(
            gh,
            ["run", "list", "--commit", head_sha, "--limit", "100", "--json",
             "databaseId,name,workflowName,headSha,status,conclusion,createdAt,url"] + _repo_args(repo),
        )
        matching = [item for item in runs if matcher.search(_workflow_name(item))]
        current = _latest([item for item in matching if item.get("headSha") == head_sha])
        if (current is None or current.get("status") != "completed") and wait > 0 and clock() < deadline:
            sleep(min(5, max(0, deadline - clock())))
            continue
        break

    if current and current.get("status") == "completed" and current.get("conclusion") == "success":
        deployed = current
    elif head_branch:
        all_runs = _gh_json(
            gh,
            ["run", "list", "--branch", head_branch, "--limit", "100", "--json",
             "databaseId,name,workflowName,headSha,status,conclusion,createdAt,url"] + _repo_args(repo),
        )
        current_workflow = _workflow_name(current) if current else None
        deployed = _latest([
            item for item in all_runs
            if matcher.search(_workflow_name(item))
            and (current_workflow is None or _workflow_name(item) == current_workflow)
            and item.get("status") == "completed" and item.get("conclusion") == "success"
        ])
    else:
        deployed = None

    problems = []
    if current is None:
        problems.append({
            "problem": "no preview run exists for the current PR head",
            "next": "trigger a preview deployment for %s" % head_sha[:12],
        })
        conclusion = "missing"
    elif current.get("status") != "completed":
        problems.append({
            "problem": "preview deployment is still running",
            "next": "wait for run %s to finish" % current.get("databaseId", "unknown"),
        })
        conclusion = current.get("status") or "running"
    else:
        conclusion = current.get("conclusion") or "unknown"
        if conclusion in {"failure", "cancelled", "timed_out", "action_required", "startup_failure"}:
            problems.append({
                "problem": "preview deployment %s" % conclusion,
                "next": "open run %s and fix or restart the preview deployment" % current.get("databaseId", "unknown"),
            })
        elif conclusion != "success":
            problems.append({
                "problem": "preview deployment concluded %s" % conclusion,
                "next": "inspect run %s before marking the PR ready" % current.get("databaseId", "unknown"),
            })

    return {
        "ok": not problems,
        "pr": pr,
        "head_sha": head_sha,
        "workflow": workflow,
        "conclusion": conclusion,
        "run": current,
        "deployed_sha": deployed.get("headSha") if deployed else None,
        "problems": problems,
    }


def render(result):
    lines = ["Preview status: %s" % ("OK" if result["ok"] else "NEEDS ACTION")]
    lines.append("PR head: %s" % result["head_sha"])
    lines.append("Conclusion: %s" % result["conclusion"])
    lines.append("Deployed sha: %s" % (result["deployed_sha"] or "none"))
    for item in result["problems"]:
        lines.extend(["Problem: " + item["problem"], "Next: " + item["next"]])
    return "\n".join(lines)


def main(argv=None, gh=default_gh):
    parser = argparse.ArgumentParser(description="Check the preview deployment for a PR's current head.")
    parser.add_argument("--pr", type=int, required=True)
    parser.add_argument("--repo")
    parser.add_argument("--workflow", default="preview", help="case-insensitive workflow-name regex")
    parser.add_argument("--wait", type=int, default=0, metavar="SECONDS")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = inspect_preview(args.pr, args.repo, args.workflow, args.wait, gh=gh)
        print(json.dumps(result, sort_keys=True) if args.json else render(result))
        return 0 if result["ok"] else 1
    except (RuntimeError, ValueError) as exc:
        error = {"ok": False, "error": str(exc), "problems": [], "next": "check gh authentication and the command arguments"}
        print(json.dumps(error, sort_keys=True) if args.json else "Error: %s\nNext: %s" % (exc, error["next"]), file=sys.stdout if args.json else sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
