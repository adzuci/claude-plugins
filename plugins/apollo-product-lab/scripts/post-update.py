#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys

import storage


def optional(value: str) -> str:
    return "" if value.strip().lower() in ("", "none", "null", "n/a") else value.strip()


def intake_jira_state(initiative: str, run_id: str, root: str) -> tuple[str, bool]:
    if not root or not initiative or not run_id:
        return "", False
    storage.check_slug(initiative)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", run_id):
        raise storage.RecordError(f"unsafe run id {run_id!r}")
    run = os.path.join(root, ".ai", initiative, "runs", run_id)
    try:
        names = os.listdir(run)
    except OSError:
        return "", False
    candidates = []
    for name in names:
        match = re.fullmatch(r"(?:A\.)?intake\.snapshot(?:\.([0-9]+))?\.md", name)
        if match:
            candidates.append((int(match.group(1) or 1), name))
    if not candidates:
        return "", False
    _, name = max(candidates)
    try:
        with open(os.path.join(run, name)) as source:
            for line in source:
                if not re.search(r"jira|tracker\s+(?:epic|issue)", line, re.I):
                    continue
                if re.search(r"(?:jira|tracker\s+(?:epic|issue))\s*:\s*blocked\s*:", line, re.I):
                    return "", True
                match = re.search(r"\b([A-Z][A-Z0-9_]+-[0-9]+)\b", line)
                if match:
                    return match.group(1), False
    except OSError:
        pass
    return "", False


def issue_from_intake(initiative: str, run_id: str, root: str) -> str:
    return intake_jira_state(initiative, run_id, root)[0]


def plan(args, repo_root_fn=storage.repo_root) -> dict:
    updates = storage.validate_profile(args.profile)
    tracker = updates.get("tracker") or "notion"
    blocked = updates.get("tracker_blocked") == "jira"
    initiative = optional(getattr(args, "initiative", ""))
    selected_run = optional(getattr(args, "run", ""))
    intake_issue, intake_blocked = intake_jira_state(
        initiative, selected_run, repo_root_fn()
    ) if initiative and selected_run else ("", False)
    selected_issue = optional(args.issue) or intake_issue
    if not selected_issue and not intake_blocked:
        selected_issue = optional(updates.get("jira_issue", ""))
    links = [link.strip() for link in args.links.split(",") if link.strip()]
    body = f"[{args.stage}] {args.summary}"
    if links:
        body += "\nLinks: " + ", ".join(links)
    calls = []
    status = []
    notion_enabled = tracker in ("notion", "both") or blocked
    if notion_enabled:
        event = optional(getattr(args, "event", ""))
        agent = optional(getattr(args, "agent", ""))
        outcome = optional(getattr(args, "outcome", ""))
        if not all((initiative, selected_run, event, agent, outcome)):
            raise storage.RecordError(
                "Notion updates require --initiative, --run, --event, --agent, and --outcome from the stage ledger event"
            )
        append_args = [initiative, "--run", selected_run, "--event", event, "--stage", args.stage,
                       "--agent", agent, "--outcome", outcome, "--note", args.summary]
        for link in links:
            append_args.extend(("--evidence", link))
        calls.append({
            "tool": "storage.py ledger-entry",
            "args": {
                "page": "FETCHED_LEDGER_PAGE.md",
                "append_args": append_args,
            },
            "next": "execute the printed notion-update-page insert_content plan",
            "summary": body,
        })
        status.append("notion: planned")
    if tracker in ("jira", "both"):
        if blocked:
            status.append("jira: blocked: Atlassian connector unavailable; using Notion fallback")
        elif not selected_issue:
            status.append("jira: blocked: no Jira issue")
        else:
            calls.append({"tool": "mcp__atlassian__addCommentToJiraIssue",
                          "args": {"issueIdOrKey": selected_issue, "commentBody": body}})
            status.append(f"jira: planned for {selected_issue}")
    return {"tracker": tracker, "stage": args.stage, "status": status, "calls": calls}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--links", default="")
    parser.add_argument("--issue", default="")
    parser.add_argument("--initiative", default="")
    parser.add_argument("--run", default="")
    parser.add_argument("--event", default="")
    parser.add_argument("--agent", default="")
    parser.add_argument("--outcome", default="")
    parser.add_argument("--profile", required=True)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(plan(args), indent=2))
    except (OSError, storage.RecordError) as error:
        print(f"post-update: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
