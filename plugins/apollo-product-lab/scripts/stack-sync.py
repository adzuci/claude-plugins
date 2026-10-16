#!/usr/bin/env python3
"""Inspect or merge a stacked PR chain from its bottom branch upward."""
import argparse
import json
import subprocess
import sys


def run(cmd, cwd=None):
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    except FileNotFoundError:
        return 127, ""
    return result.returncode, (result.stdout + result.stderr).strip()


def default_gh(args, cwd=None):
    return run(["gh"] + list(args), cwd)


def default_git(args, cwd=None):
    return run(["git"] + list(args), cwd)


def _json_call(runner, args, label):
    code, output = runner(args)
    if code:
        raise RuntimeError("%s failed" % label)
    try:
        return json.loads(output)
    except (TypeError, ValueError):
        raise RuntimeError("%s returned invalid JSON" % label)


def discover_stack(tip, repo=None, gh=default_gh):
    repo_args = ["--repo", repo] if repo else []
    branch = tip
    seen = set()
    top_down = []
    while branch not in seen:
        seen.add(branch)
        prs = _json_call(
            gh,
            ["pr", "list", "--head", branch, "--state", "open", "--limit", "2", "--json",
             "number,headRefName,baseRefName,url"] + repo_args,
            "gh pr list",
        )
        if not prs:
            break
        if len(prs) > 1:
            raise RuntimeError("more than one open PR has head %s" % branch)
        pr = prs[0]
        if pr.get("headRefName") and pr.get("headRefName") != branch:
            raise RuntimeError("gh returned the wrong head for %s" % branch)
        base = pr.get("baseRefName")
        if not base:
            raise RuntimeError("PR %s has no base branch" % pr.get("number", "unknown"))
        top_down.append({"pr": pr.get("number"), "branch": branch, "base": base, "url": pr.get("url")})
        if base in seen:
            raise RuntimeError("cycle found in PR stack at %s" % base)
        branch = base
    if not top_down:
        raise RuntimeError("no open PR found for tip %s" % tip)
    return list(reversed(top_down)), branch


def _count_behind(git, branch, base):
    code, output = git(["rev-list", "--count", "%s..%s" % (branch, base)])
    if code:
        raise RuntimeError("cannot compare %s with %s" % (branch, base))
    try:
        return int(output.strip())
    except ValueError:
        raise RuntimeError("git rev-list returned an invalid count")


def _conflicts(git, branch, base):
    code, output = git(["merge-tree", "--write-tree", branch, base])
    conflict_text = "CONFLICT" in output or "<<<<<<<" in output
    if code not in (0, 1):
        raise RuntimeError("git merge-tree failed for %s" % branch)
    return code == 1 or conflict_text


def inspect_stack(tip, repo=None, apply=False, gh=default_gh, git=default_git):
    stack, trunk = discover_stack(tip, repo, gh)
    for item in stack:
        item["behind"] = _count_behind(git, item["branch"], item["base"])
        item["conflicts"] = _conflicts(git, item["branch"], item["base"])
    result = {"ok": True, "tip": tip, "trunk": trunk, "applied": apply, "stack": stack, "commands": [], "push_commands": [], "problems": []}

    if not apply:
        updated = set()
        for item in stack:
            base_will_change = item["base"] in updated
            if item["behind"] or base_will_change:
                result["commands"].extend([
                    "git switch %s" % item["branch"],
                    "git -c merge.autostash=false merge --no-edit %s" % item["base"],
                ])
                updated.add(item["branch"])
                result["ok"] = False
                result["problems"].append({
                    "problem": ("%s will need %s after that base is updated" % (item["branch"], item["base"]))
                    if base_will_change and not item["behind"] else
                    "%s is %s commit(s) behind %s" % (item["branch"], item["behind"], item["base"]),
                    "next": "run the bottom-up merge commands before review",
                })
        if any(item["conflicts"] for item in stack):
            result["ok"] = False
            for item in stack:
                if item["conflicts"]:
                    result["problems"].append({"problem": "%s conflicts with %s" % (item["branch"], item["base"]), "next": "resolve that merge before syncing branches above it"})
        return result

    code, dirty = git(["status", "--porcelain"])
    if code:
        raise RuntimeError("git status failed")
    if dirty.strip():
        raise RuntimeError("working tree is dirty; commit or stash it before --apply")
    for item in stack:
        item["behind"] = _count_behind(git, item["branch"], item["base"])
        item["conflicts"] = _conflicts(git, item["branch"], item["base"])
        if not item["behind"]:
            continue
        code, output = git(["switch", item["branch"]])
        if code:
            raise RuntimeError("cannot switch to %s" % item["branch"])
        result["commands"].append("git switch %s" % item["branch"])
        merge_args = ["-c", "merge.autostash=false", "merge", "--no-edit", item["base"]]
        code, output = git(merge_args)
        result["commands"].append("git -c merge.autostash=false merge --no-edit %s" % item["base"])
        if code:
            result["ok"] = False
            result["problems"].append({"problem": "merge stopped on %s" % item["branch"], "next": "resolve or abort the merge; no later stack branch was changed"})
            return result
        item["behind"] = 0
        item["conflicts"] = False

    for item in stack:
        code, _ = git(["merge-base", "--is-ancestor", item["base"], item["branch"]])
        if code:
            result["ok"] = False
            result["problems"].append({"problem": "%s is not an ancestor of %s" % (item["base"], item["branch"]), "next": "merge the base successfully before pushing this branch"})
            continue
        result["push_commands"].append("git push origin %s" % item["branch"])
    return result


def render(result):
    lines = ["Stack sync: %s" % ("OK" if result["ok"] else "NEEDS ACTION")]
    lines.append("Branch | Base | Behind | Conflicts")
    lines.append("--- | --- | ---: | ---")
    for item in result["stack"]:
        lines.append("%s | %s | %s | %s" % (item["branch"], item["base"], item["behind"], "yes" if item["conflicts"] else "no"))
    if result["commands"]:
        lines.append("Commands (bottom-up):")
        lines.extend(result["commands"])
    if result["push_commands"]:
        lines.append("Push commands (not run):")
        lines.extend(result["push_commands"])
    for item in result["problems"]:
        lines.extend(["Problem: " + item["problem"], "Next: " + item["next"]])
    return "\n".join(lines)


def main(argv=None, gh=default_gh, git=default_git):
    parser = argparse.ArgumentParser(description="Inspect or merge a stacked PR chain bottom-up.")
    parser.add_argument("--tip", required=True)
    parser.add_argument("--repo")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = inspect_stack(args.tip, args.repo, args.apply, gh, git)
        print(json.dumps(result, sort_keys=True) if args.json else render(result))
        return 0 if result["ok"] else 1
    except RuntimeError as exc:
        payload = {"ok": False, "error": str(exc), "next": "fix the repository or GitHub state and rerun stack-sync"}
        print(json.dumps(payload, sort_keys=True) if args.json else "Error: %s\nNext: %s" % (exc, payload["next"]), file=sys.stdout if args.json else sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
