#!/usr/bin/env python3
"""Rebuild cases.jsonl from a human-review mining table plus the GitHub API.

Usage: build_cases.py --mining <mining.md> [--out cases.jsonl] [--repo apolloio/leadgenie]
Only rows whose preventable_by is `static-reviewer` become cases. Stores a short
excerpt, never full comment bodies or diffs.
"""
import argparse, difflib, json, re, subprocess, sys
from collections import defaultdict


def gh(path):
    out = subprocess.run(["gh", "api", path, "--paginate"], capture_output=True, text=True)
    if out.returncode:
        raise RuntimeError(f"gh api {path}: {out.stderr.strip()}")
    txt = out.stdout.strip()
    if not txt:
        return []
    # --paginate on arrays emits concatenated arrays
    dec, i, res = json.JSONDecoder(), 0, []
    while i < len(txt):
        obj, j = dec.raw_decode(txt, i)
        res.extend(obj if isinstance(obj, list) else [obj])
        i = j
        while i < len(txt) and txt[i].isspace():
            i += 1
    return res


def norm(s):
    return re.sub(r"[^a-z0-9 ]", "", s.lower().replace("’", "'")).strip()


def excerpt(body, n=40):
    return " ".join(re.sub(r"```.*?```", " ", body, flags=re.S).split()[:n])


def parse_mining(path):
    rows = []
    for l in open(path).read().split("\n"):
        if not l.startswith("| ") or l.count(" | ") < 7 or l.startswith("| PR "):
            continue
        f = l.strip().strip("|").split(" | ")
        if len(f) != 8 or not f[0].strip().isdigit():
            continue
        f = [x.strip() for x in f]
        rows.append(dict(pr=int(f[0]), loc=f[1], reviewer=f[2], quote=f[3], category=f[4],
                         preventable_by=f[5], rule_text=f[6], existing_rule=f[7]))
    return rows


def rule_ids(s):
    if not s or s.lower() == "none":
        return []
    ids = []
    for tok in re.split(r"[/,;\s]+", s):
        tok = tok.strip("()")
        m = re.fullmatch(r"([A-Z]{1,3})(\d+)(?:-(\d+))?", tok)
        if m:
            if m.group(3):
                ids += [f"{m.group(1)}{k}" for k in range(int(m.group(2)), int(m.group(3)) + 1)]
            else:
                ids.append(tok)
    return ids


def score(quote, body, path_row, c):
    q, b = norm(quote), norm(body)
    s = difflib.SequenceMatcher(None, q, b[: len(q) + 40]).ratio()
    if q and q[:40] in b:
        s = max(s, 0.95)
    if path_row and c.get("path") and c["path"].endswith(path_row):
        s += 0.2
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mining", required=True)
    ap.add_argument("--out", default="cases.jsonl")
    ap.add_argument("--repo", default="apolloio/leadgenie")
    a = ap.parse_args()
    repo = a.repo
    rows = [r for r in parse_mining(a.mining) if r["preventable_by"] == "static-reviewer"]
    byp = defaultdict(list)
    for r in rows:
        byp[r["pr"]].append(r)
    cases, dropped = [], []
    for pr, prrows in sorted(byp.items()):
        meta = gh(f"repos/{repo}/pulls/{pr}")[0]
        base = meta["base"]["sha"]
        commits = gh(f"repos/{repo}/pulls/{pr}/commits")
        line_c = [c for c in gh(f"repos/{repo}/pulls/{pr}/comments")]
        reviews = gh(f"repos/{repo}/pulls/{pr}/reviews")
        issues = gh(f"repos/{repo}/issues/{pr}/comments")
        pool = []
        for c in line_c:
            pool.append(dict(kind="line", id=c["id"], url=c["html_url"], login=c["user"]["login"], path=c["path"],
                             line=c.get("original_line") or c.get("line"), commit=c["original_commit_id"],
                             body=c["body"], created=c["created_at"]))
        for c in reviews:
            if c.get("body"):
                pool.append(dict(kind="review", id=c["id"], url=c["html_url"], login=c["user"]["login"], path=None,
                                 line=None, commit=c["commit_id"], body=c["body"], created=c["submitted_at"]))
        for c in issues:
            def head_at(ts):
                best = commits[0]["sha"]
                for k in commits:
                    if k["commit"]["committer"]["date"] <= ts:
                        best = k["sha"]
                return best
            pool.append(dict(kind="issue", id=c["id"], url=c["html_url"], login=c["user"]["login"], path=None,
                             line=None, commit=head_at(c["created_at"]), body=c["body"], created=c["created_at"]))
        used = set()
        for r in prrows:
            is_review = r["loc"].startswith("(review)")
            path_row = None if is_review else r["loc"].rsplit(":", 1)[0]
            cands = [c for c in pool if c["login"] == r["reviewer"] and c["id"] not in used
                     and (c["kind"] == "line") == (not is_review)]
            best = max(cands, key=lambda c: score(r["quote"], c["body"], path_row, c), default=None)
            if not best or score(r["quote"], best["body"], path_row, best) < 0.55:
                dropped.append((pr, r["quote"][:60], "no matching API comment"))
                continue
            used.add(best["id"])
            ids = rule_ids(r["existing_rule"])
            line = best["line"]
            if best["kind"] == "line" and not best["path"]:
                dropped.append((pr, r["quote"][:60], "no path"))
                continue
            cases.append({
                "id": f"ads-m1-{best['id']}",
                "pr": pr,
                "comment_id": best["id"],
                "comment_kind": best["kind"],
                "url": best["url"],
                "reviewer": best["login"],
                "path": best["path"],
                "line": line,
                "commit_id": best["commit"],
                "base_sha": base,
                "excerpt": excerpt(best["body"]),
                "category": r["category"],
                "expected_rules": ids,
                "rule_gap": not ids,
                "match": {"same_file": best["kind"] == "line", "line_tolerance": 8 if best["kind"] == "line" else None,
                          "any_of": {"rules": ids, "category": r["category"]}},
            })
    with open(a.out, "w") as f:
        for c in cases:
            f.write(json.dumps(c, sort_keys=True) + "\n")
    print(f"cases={len(cases)} dropped={len(dropped)}")
    for d in dropped:
        print("DROP", d)


if __name__ == "__main__":
    main()
