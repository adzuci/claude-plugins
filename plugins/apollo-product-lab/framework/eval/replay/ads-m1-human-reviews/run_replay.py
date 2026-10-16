#!/usr/bin/env python3
"""Replay eval: how many past human review comments would our AI reviewers catch?

  run_replay.py prepare --out <dir> [--pr N] [--limit K] [--cases cases.jsonl] [--repo apolloio/leadgenie]
  run_replay.py score   --runs <dir> [--cases cases.jsonl]

stdlib + the gh CLI only. The brief written by `prepare` never contains the human comments.
"""
import argparse, fnmatch, json, os, re, subprocess, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CASES = os.path.join(HERE, "cases.jsonl")
INFRA = os.path.normpath(os.path.join(HERE, "../../../apollo-infra-patterns.md"))
LINE_TOLERANCE = 8
DEFAULT_OUTCOMES = os.path.join(HERE, "outcomes.json")
CANONICAL_CATEGORIES = ("correctness", "compliance", "data_loss", "wiring", "test_gap", "perf", "repo_convention", "docs",
                        "security", "design", "pr_hygiene")
CATEGORY_MAP = {
    "comments policy": "docs",
    "api contract fe<->be mismatch": "wiring",
    "naming/readability": "repo_convention",
    "security/permission": "security",
    "performance fe": "perf",
    "concurrency/idempotency": "correctness",
    "correctness/logic bug": "correctness",
    "dead code/duplication/over-engineering": "design",
    "design-system/fabric/ui fidelity": "repo_convention",
    "test quality": "test_gap",
    "missing-state/edge case": "correctness",
    "repo convention": "repo_convention",
    "data model/index/query perf": "perf",
    "observability": "correctness",
}


def canonical_category(name):
    """Map a mining category or a reviewer category to the canonical reviewer vocabulary, else None."""
    key = (name or "").strip().lower()
    if key in CANONICAL_CATEGORIES:
        return key
    return CATEGORY_MAP.get(key)

DROP_GLOBS = ["*.rbi", "sorbet/**", "*.lock", "*lock.json", "*lock.yaml", "pnpm-lock.yaml", "Gemfile.lock",
              "app/_generated/**", "**/_generated/**", "*.snap", "*.min.js"]
RB_BACKEND = [r"^(app|lib)/.*\.rb$", r"^packs/.*\.rb$"]
SPEC = [r"(^|/)spec/"]
BACKEND_CONFIG = [r"^config/.*\.(?:rb|ya?ml)$", r"^packages/.*\.ya?ml$", r"(^|/)package\.yml$", r"^kubernetes/"]
FE = [r"^assets/.*\.(ts|tsx|scss)$", r"^packages/.*\.(ts|tsx|scss)$"]
SEC = [r"^app/(controllers|services|api)/.*\.rb$", r"^packs/[^/]+/app/(controllers|services|api)/.*\.rb$",
       r"^packs/[^/]+/(controllers|services)/.*\.rb$"]
SEC_CONTENT = re.compile(r"^\+.*(before_action|params\.permit|permit!|resources? :|get ['\"]|post ['\"]|webhook|oauth)", re.I | re.M)
ROUTES_FILE = re.compile(r"^config/routes[^/]*\.rb$")
ROUTE_CONTENT = re.compile(r"^\+.*\b(resources?|get|post)\b", re.I | re.M)
DBPERF_CONTENT = re.compile(r"(Mongoid|find_by|where|aggregate|index|perform_async|update_all|push_bulk|\$lookup|\$in|\.hint|\.explain)")


def gh(args):
    r = subprocess.run(["gh"] + args, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError("gh " + " ".join(args) + ": " + r.stderr.strip())
    return r.stdout


def load_cases(path):
    return [json.loads(l) for l in open(path) if l.strip()]


def dropped(path):
    return any(fnmatch.fnmatch(path, g) for g in DROP_GLOBS) or path.startswith("sorbet/")


def clean_diff(raw):
    """Keep per-file sections of a unified diff, dropping noise files. Returns (text, files)."""
    parts = re.split(r"(?m)^(?=diff --git )", raw)
    keep, files = [], []
    for p in parts:
        m = re.match(r"diff --git a/(\S+) b/(\S+)", p)
        if not m:
            continue
        f = m.group(2)
        if dropped(f):
            continue
        keep.append(p)
        files.append(f)
    return "".join(keep), files


def route(files, diff):
    def any_m(pats, f):
        return any(re.search(p, f) for p in pats)
    backend = [f for f in files if any_m(RB_BACKEND, f) and not any_m(SPEC, f)]
    backend_route = backend or [f for f in files if (f.endswith(".rb") and any_m(SPEC, f)) or any_m(BACKEND_CONFIG, f)]
    r = []
    if any(any_m(FE, f) for f in files):
        r.append("frontend-reviewer")
    if backend_route:
        r.append("backend-reviewer")
    route_file = any(f == "config/routes.rb" or (ROUTES_FILE.search(f) and ROUTE_CONTENT.search(diff)) for f in files)
    if any(any_m(SEC, f) for f in backend) or route_file or (backend and SEC_CONTENT.search(diff)):
        r.append("security-reviewer")
    if backend and DBPERF_CONTENT.search(diff):
        r.append("db-perf")
    return r


def infra_checks():
    if not os.path.exists(INFRA):
        return None
    out, head, buf = [], None, None
    for l in open(INFRA):
        if re.match(r"^## IP\d+", l):
            if head and buf:
                out.append(head + "\n" + " ".join(buf))
            head, buf = l.strip(), None
        elif head and l.startswith("- **Check.**"):
            buf = [l.strip()]
        elif buf is not None:
            if l.strip() == "" or l.startswith("- **") or l.startswith("#"):
                out.append(head + "\n" + " ".join(buf))
                head, buf = None, None
            else:
                buf.append(l.strip())
    if head and buf:
        out.append(head + "\n" + " ".join(buf))
    return "\n\n".join(out) or None


def cmd_prepare(a):
    cases = load_cases(a.cases)
    if a.pr:
        cases = [c for c in cases if c["pr"] == a.pr]
    groups = defaultdict(list)
    for c in cases:
        groups[(c["pr"], c["commit_id"], c["base_sha"])].append(c)
    keys = sorted(groups)
    if a.limit:
        keys = keys[: a.limit]
    os.makedirs(a.out, exist_ok=True)
    checks = infra_checks()
    index = []
    for pr, commit, base in keys:
        gid = f"pr{pr}-{commit[:10]}"
        gdir = os.path.join(a.out, gid)
        os.makedirs(os.path.join(gdir, "findings"), exist_ok=True)
        raw = gh(["api", "-H", "Accept: application/vnd.github.v3.diff", f"repos/{a.repo}/compare/{base}...{commit}"])
        diff, files = clean_diff(raw)
        diff_path = os.path.join(gdir, "diff.patch")
        open(diff_path, "w").write(diff)
        reviewers = route(files, diff)
        outs = {r: os.path.join(gdir, "findings", f"{r}.json") for r in reviewers}
        brief = [f"# Reviewer brief {gid}", "",
                 f"Repo: {a.repo}. PR #{pr}. Head (commit under review): `{commit}`. Base: `{base}`.",
                 f"Cleaned diff (noise files dropped): `{diff_path}` ({diff.count(chr(10))} lines, {len(files)} files).",
                 "Review this diff as the PR reviewer would. Findings must cite repo-relative file paths and head-side line numbers.", "",
                 "## Reviewers to run (dispatch by agent type, in parallel)", ""]
        brief += [f"- `{r}` -> write findings JSON to `{p}`" for r, p in outs.items()] or ["- none matched; write nothing"]
        brief += ["", "## Findings format", "",
                  "A JSON array (or `{\"findings\": [...]}`) of objects:",
                  "`{\"file\": str, \"line\": int, \"severity\": \"must-fix|recommended|nit\", \"category\": str, \"rule\": \"B24|IP14|...\" (or \"rule_id\"), \"summary\": str}`",
                  "Use the rule id from your checklist when one applies, else empty string.", ""]
        if checks:
            brief += ["## Infra checks (IP patterns)", "", checks, ""]
        open(os.path.join(gdir, "brief.md"), "w").write("\n".join(brief))
        index.append({"group": gid, "pr": pr, "commit_id": commit, "base_sha": base, "diff": diff_path,
                      "reviewers": reviewers, "outputs": outs, "case_ids": [c["id"] for c in groups[(pr, commit, base)]]})
        print(f"prepared {gid}: {len(files)} files, reviewers={reviewers}, cases={len(groups[(pr, commit, base)])}")
    gpath = os.path.join(a.out, "groups.json")
    merged = {}
    if os.path.exists(gpath):
        merged = {g["group"]: g for g in json.load(open(gpath))}
    merged.update({g["group"]: g for g in index})
    json.dump(sorted(merged.values(), key=lambda g: g["group"]), open(gpath, "w"), indent=2)
    print(f"{len(index)} groups prepared, {len(merged)} in {gpath}")


# ---------- scoring ----------

def finding_rules(f):
    """Rule ids a finding cites, from `rule` or `rule_id` (string, list, or 'B1/IP14' style)."""
    raw = f.get("rule") or f.get("rule_id") or ""
    raw = raw if isinstance(raw, list) else [raw]
    out = set()
    for r in raw:
        out |= {x.strip().upper() for x in re.split(r"[/,;\s]+", str(r or "")) if x.strip()}
    return out


STOPWORDS = {"about", "after", "again", "also", "because", "before", "being", "between", "could", "does", "from",
             "have", "into", "only", "should", "their", "there", "these", "this", "those", "through", "under", "when",
             "where", "which", "while", "with", "would", "your"}


def claim_tokens(text):
    return {token for token in re.findall(r"[a-z0-9_]+", (text or "").lower()) if len(token) >= 4 and token not in STOPWORDS}


def case_matches(case, f):
    """True when finding f counts as catching case. Pure function, unit tested."""
    m = case["match"]
    cat = (f.get("category") or "").strip().lower()
    want = (m["any_of"].get("category") or "").strip().lower()
    rules = {r.upper() for r in list(case.get("expected_rules") or []) + list(m["any_of"].get("rules", []))}
    canon = canonical_category(cat)
    cat_ok = bool(cat) and (cat == want or (canon is not None and canon == canonical_category(want)))
    cited = finding_rules(f)
    semantic_category_match = (not cited and cat_ok and not m.get("rules_only") and
                               bool(claim_tokens(f.get("claim") or f.get("summary")) & claim_tokens(case.get("excerpt"))))
    if not ((rules & cited) or semantic_category_match):
        return False
    if m.get("same_file"):
        if not f.get("file") or not case.get("path") or f["file"] != case["path"]:
            return False
        tol = m.get("line_tolerance") or LINE_TOLERANCE
        try:
            ln = int(f.get("line"))
        except (TypeError, ValueError):
            return False
        return case["line"] is not None and abs(ln - int(case["line"])) <= tol
    return True


def distance(case, f):
    try:
        return abs(int(f.get("line")) - int(case["line"]))
    except (TypeError, ValueError):
        return 10 ** 6


def assign(cases, findings):
    """Greedy one-to-one matching, smallest line distance first. Returns {case_id: finding_index}."""
    pairs = sorted((distance(c, f), c["id"], i) for c in cases for i, f in enumerate(findings) if case_matches(c, f))
    got, used = {}, set()
    for _, cid, i in pairs:
        if cid in got or i in used:
            continue
        got[cid] = i
        used.add(i)
    return got


def load_outcomes(path):
    try:
        return {o["id"]: o.get("outcome", "unknown") for o in json.load(open(path))}
    except (OSError, ValueError, TypeError, KeyError):
        return {}


def read_findings(path):
    try:
        data = json.load(open(path))
    except (OSError, ValueError):
        return []
    if isinstance(data, dict):
        data = data.get("findings", [])
    return [x for x in data if isinstance(x, dict)]


def pct(n, d):
    return round(n / d, 3) if d else None


def cmd_score(a):
    cases = {c["id"]: c for c in load_cases(a.cases)}
    outcomes = load_outcomes(getattr(a, "outcomes", None) or DEFAULT_OUTCOMES)
    index = json.load(open(os.path.join(a.runs, "groups.json")))
    caught, noise, scored = set(), 0, set()
    for g in index:
        findings = []
        for p in g["outputs"].values():
            findings += read_findings(p)
        gcases = [cases[i] for i in g["case_ids"] if i in cases]
        got = assign(gcases, findings)
        for c in gcases:
            scored.add(c["id"])
        caught |= set(got)
        noise += len(findings) - len(got)
    out = lambda c: outcomes.get(c["id"], "unknown")
    scored_cases = [cases[i] for i in sorted(scored)]
    recall_cases = [c for c in scored_cases if out(c) in ("fixed", "deferred")]
    declined = [c for c in scored_cases if out(c) == "declined"]
    unknown = [c for c in scored_cases if out(c) not in ("fixed", "deferred", "declined")]

    def breakdown(keyf, subset):
        d = defaultdict(lambda: [0, 0])
        for c in subset:
            for k in keyf(c):
                d[k][1] += 1
                d[k][0] += c["id"] in caught
        return {k: {"caught": v[0], "total": v[1], "recall": pct(v[0], v[1])} for k, v in sorted(d.items())}

    n_caught = lambda cs: sum(c["id"] in caught for c in cs)
    with_rule = [c for c in recall_cases if not c["rule_gap"]]
    gaps = [c for c in recall_cases if c["rule_gap"]]
    fp_rate = pct(n_caught(declined), len(declined)) or 0
    max_fp_rate = getattr(a, "max_fp_rate", 0.15)
    rep = {
        "scored_cases": len(scored_cases),
        "overall": {"caught": n_caught(recall_cases), "total": len(recall_cases), "recall": pct(n_caught(recall_cases), len(recall_cases))},
        "rule_exists": {"caught": n_caught(with_rule), "total": len(with_rule), "recall": pct(n_caught(with_rule), len(with_rule))},
        "rule_gap": {"caught": n_caught(gaps), "total": len(gaps), "recall": pct(n_caught(gaps), len(gaps))},
        "should_not_flag": {"total": len(declined), "flagged": n_caught(declined),
                            "rate": fp_rate, "max_rate": max_fp_rate,
                            "flagged_cases": [{"id": c["id"], "url": c["url"]} for c in declined if c["id"] in caught]},
        "false_positives_by_rule": breakdown(lambda c: c["expected_rules"] or ["(gap)"], declined),
        "unknown_outcome": {"total": len(unknown), "caught": n_caught(unknown)},
        "by_rule": breakdown(lambda c: c["expected_rules"] or ["(gap)"], recall_cases),
        "by_category": breakdown(lambda c: [c["category"]], recall_cases),
        "by_pr": breakdown(lambda c: [str(c["pr"])], recall_cases),
        "misses": [{"id": c["id"], "url": c["url"], "pr": c["pr"], "path": c["path"], "rules": c["expected_rules"],
                    "category": c["category"], "rule_gap": c["rule_gap"]} for c in recall_cases if c["id"] not in caught],
        "noise_findings": noise,
        "pass_bar": 0.8,
        "pass": (pct(n_caught(with_rule), len(with_rule)) or 0) >= 0.8 and fp_rate <= max_fp_rate,
    }
    json.dump(rep, open(os.path.join(a.runs, "report.json"), "w"), indent=2)
    L = ["# Replay report", "",
         "Regression corpus, not held-out evidence. Recall is scored on fixed and deferred cases.", "",
         f"Recall on fixed/deferred cases: {rep['overall']['caught']}/{rep['overall']['total']} = {rep['overall']['recall']}",
         f"Recall where a rule exists: {rep['rule_exists']['caught']}/{rep['rule_exists']['total']} = {rep['rule_exists']['recall']} (bar 0.8, pass={rep['pass']})",
         f"Rule-gap cases: {rep['rule_gap']['caught']}/{rep['rule_gap']['total']} = {rep['rule_gap']['recall']}",
         f"Should not flag (declined comments), flagged anyway: {rep['should_not_flag']['flagged']}/{rep['should_not_flag']['total']} = {rep['should_not_flag']['rate']} (max {max_fp_rate})",
         f"Unknown outcome, reported only: {rep['unknown_outcome']['caught']}/{rep['unknown_outcome']['total']} caught",
         f"Noise (findings matching no case, not necessarily wrong): {noise}", ""]
    for title, key in (("Per rule", "by_rule"), ("Per category", "by_category"), ("Per PR", "by_pr")):
        L += [f"## {title}", "", "| key | caught | total | recall |", "|---|---|---|---|"]
        L += [f"| {k} | {v['caught']} | {v['total']} | {v['recall']} |" for k, v in rep[key].items()] + [""]
    L += ["## Misses", ""] + [f"- {m['url']} ({m['path']}; rules {m['rules'] or 'gap'}; {m['category']})" for m in rep["misses"]]
    L += ["", "## Flagged but we declined", ""] + [f"- {m['url']}" for m in rep["should_not_flag"]["flagged_cases"]]
    txt = "\n".join(L) + "\n"
    open(os.path.join(a.runs, "report.md"), "w").write(txt)
    print(txt)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("prepare")
    p.add_argument("--out", required=True)
    p.add_argument("--pr", type=int)
    p.add_argument("--limit", type=int)
    p.add_argument("--cases", default=DEFAULT_CASES)
    p.add_argument("--repo", default="apolloio/leadgenie")
    p.set_defaults(fn=cmd_prepare)
    s = sp.add_parser("score")
    s.add_argument("--runs", required=True)
    s.add_argument("--cases", default=DEFAULT_CASES)
    s.add_argument("--outcomes", default=DEFAULT_OUTCOMES)
    s.add_argument("--max-fp-rate", type=float, default=0.15)
    s.set_defaults(fn=cmd_score)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
