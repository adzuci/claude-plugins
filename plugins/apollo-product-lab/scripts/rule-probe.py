#!/usr/bin/env python3
"""Prepare and score paired rule-on/rule-off replay probes. No model calls."""
import argparse
import contextlib
import datetime
import importlib.util
import io
import json
import os
from types import SimpleNamespace


HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.dirname(HERE)
REPLAY = os.path.join(PLUGIN, "framework", "eval", "replay", "ads-m1-human-reviews")
DEFAULT_CASES = os.path.join(REPLAY, "cases.jsonl")
DEFAULT_OUTCOMES = os.path.join(REPLAY, "outcomes.json")
DEFAULT_PROBES = os.path.join(PLUGIN, "framework", "rules", "probes")


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


REGISTRY = load_module("harness_rule_registry", os.path.join(HERE, "rule_registry.py"))


def load_cases(path=DEFAULT_CASES):
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def prepare(rule_id, out, cases_path=DEFAULT_CASES):
    _, registry = REGISTRY.load_registry()
    if rule_id not in registry:
        raise ValueError("rule %s is not in the registry" % rule_id)
    definitions = REGISTRY.prompt_rules()
    if rule_id not in definitions:
        raise ValueError("rule %s has no prompt definition" % rule_id)
    cases = [case for case in load_cases(cases_path) if rule_id in case.get("expected_rules", [])]
    if not cases:
        raise ValueError("rule %s has no replay cases" % rule_id)
    source = definitions[rule_id]["path"]
    with open(source, encoding="utf-8") as handle:
        prompt = handle.read()
    variants = {"on": prompt, "off": REGISTRY.remove_rule_bullet(prompt, rule_id)}
    os.makedirs(out, exist_ok=True)
    manifest = {"rule": rule_id, "agent": definitions[rule_id]["agent"], "source": source,
                "case_ids": [case["id"] for case in cases]}
    with open(os.path.join(out, "manifest.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
    for mode, text in variants.items():
        directory = os.path.join(out, mode)
        os.makedirs(directory, exist_ok=True)
        prompt_path = os.path.join(directory, os.path.basename(source))
        with open(prompt_path, "w", encoding="utf-8") as handle:
            handle.write(text)
        rows = ["# %s probe: rule %s" % (mode, rule_id), "", "Use the prompt copy at `%s`." % prompt_path,
                "Write normal replay findings. Do not read the human comment or expected rule labels.", "", "## Cases", ""]
        rows += ["- `%s`: PR #%s, base `%s`, head `%s`, file `%s`" %
                 (case["id"], case["pr"], case["base_sha"], case["commit_id"], case["path"])
                 for case in cases]
        with open(os.path.join(directory, "brief.md"), "w", encoding="utf-8") as handle:
            handle.write("\n".join(rows) + "\n")
    return manifest


def score_run(path, cases_path=DEFAULT_CASES, outcomes_path=DEFAULT_OUTCOMES):
    declared_case_ids = validate_outputs(path)
    known_case_ids = {case["id"] for case in load_cases(cases_path)}
    case_ids = [case_id for case_id in declared_case_ids if case_id in known_case_ids]
    replay = load_module("harness_run_replay", os.path.join(REPLAY, "run_replay.py"))
    args = SimpleNamespace(runs=path, cases=cases_path, outcomes=outcomes_path, max_fp_rate=0.15)
    with contextlib.redirect_stdout(io.StringIO()):
        replay.cmd_score(args)
    with open(os.path.join(path, "report.json"), encoding="utf-8") as handle:
        report = json.load(handle)
    report["scored_case_ids"] = case_ids
    return report


def validate_outputs(path):
    index_path = os.path.join(path, "groups.json")
    try:
        with open(index_path, encoding="utf-8") as handle:
            groups = json.load(handle)
    except (OSError, ValueError) as error:
        raise ValueError("probe run %s has no readable groups.json: %s" % (path, error))
    if not isinstance(groups, list) or not groups:
        raise ValueError("probe run %s has no groups" % path)
    case_ids = set()
    for group in groups:
        group_case_ids = group.get("case_ids") if isinstance(group, dict) else None
        if not isinstance(group_case_ids, list) or not all(isinstance(case_id, str) for case_id in group_case_ids):
            raise ValueError("probe run %s has a group with invalid case_ids" % path)
        case_ids.update(group_case_ids)
        outputs = group.get("outputs") if isinstance(group, dict) else None
        if not isinstance(outputs, dict) or not outputs:
            raise ValueError("probe run %s has a group with no declared outputs" % path)
        for output in outputs.values():
            try:
                with open(output, encoding="utf-8") as handle:
                    findings = json.load(handle)
            except (OSError, ValueError) as error:
                raise ValueError("probe run %s has a missing or unreadable output %s: %s" % (path, output, error))
            if isinstance(findings, dict):
                findings = findings.get("findings")
            if not isinstance(findings, list):
                raise ValueError("probe output %s is not a findings list" % output)
    return sorted(case_ids)


def rule_metrics(report, rule_id):
    recall = report.get("by_rule", {}).get(rule_id, {})
    declined = report.get("false_positives_by_rule", {}).get(rule_id)
    per_rule = isinstance(declined, dict)
    declined = declined if per_rule else report.get("should_not_flag", {})
    return {"cases": recall.get("total", 0), "hits": recall.get("caught", 0),
            "recall": recall.get("recall"),
            "false_positives": declined.get("caught", 0) if per_rule else declined.get("flagged", 0),
            "declined_cases": declined.get("total", 0),
            "false_positive_rate": declined.get("recall", declined.get("rate", 0))}


def score_pair(rule_id, on, off, scorer=score_run, probes_dir=DEFAULT_PROBES, today=None):
    _, registry = REGISTRY.load_registry()
    if rule_id not in registry:
        raise ValueError("rule %s is not in the registry" % rule_id)
    on_report = scorer(on)
    off_report = scorer(off)
    on_metrics = rule_metrics(on_report, rule_id)
    off_metrics = rule_metrics(off_report, rule_id)
    if on_metrics["cases"] < 1:
        raise ValueError("paired probe has no fixed or deferred cases for %s" % rule_id)
    if on_metrics["declined_cases"] < 1:
        raise ValueError("paired probe has no declined cases for false-positive evidence")
    on_case_ids = on_report.get("scored_case_ids")
    off_case_ids = off_report.get("scored_case_ids")
    if (not isinstance(on_case_ids, list) or not all(isinstance(case_id, str) for case_id in on_case_ids)
            or not isinstance(off_case_ids, list) or not all(isinstance(case_id, str) for case_id in off_case_ids)):
        raise ValueError("rule-on and rule-off probes did not report exact scored case ids")
    same_cases = set(on_case_ids) == set(off_case_ids)
    same_counts = (on_metrics["cases"] == off_metrics["cases"]
                   and on_metrics["declined_cases"] == off_metrics["declined_cases"])
    on_scored = on_report.get("scored_cases")
    off_scored = off_report.get("scored_cases")
    if on_scored is not None or off_scored is not None:
        if type(on_scored) is not int or type(off_scored) is not int:
            raise ValueError("rule-on and rule-off probes did not report valid scored case counts")
        same_counts = same_counts and on_scored == off_scored
    day = today or datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    result = {"schema": 1, "rule": rule_id, "scored": day, "on": on_metrics, "off": off_metrics,
              "adds_hits": on_metrics["hits"] > off_metrics["hits"],
              "complete": same_cases and same_counts,
              "sources": {"on": on, "off": off}}
    os.makedirs(probes_dir, exist_ok=True)
    path = os.path.join(probes_dir, "%s-%s.json" % (rule_id, day))
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    return path, result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare")
    prep.add_argument("--rule", required=True)
    prep.add_argument("--out", required=True)
    prep.add_argument("--cases", default=DEFAULT_CASES)
    score = commands.add_parser("score")
    score.add_argument("--rule", required=True)
    score.add_argument("--on", required=True)
    score.add_argument("--off", required=True)
    score.add_argument("--probes-dir", default=DEFAULT_PROBES)
    args = parser.parse_args(argv)
    if args.command == "prepare":
        result = prepare(args.rule, args.out, args.cases)
        print("prepared %s cases for %s in %s" % (len(result["case_ids"]), args.rule, args.out))
    else:
        path, result = score_pair(args.rule, args.on, args.off, probes_dir=args.probes_dir)
        print(json.dumps({"probe": path, "adds_hits": result["adds_hits"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
