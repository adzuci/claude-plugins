#!/usr/bin/env python3
"""Propose evidence-based rule lifecycle changes without editing reviewer prompts."""
import argparse
import datetime
import difflib
import glob
import importlib.util
import json
import os


HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.dirname(HERE)
DEFAULT_PROBES = os.path.join(PLUGIN, "framework", "rules", "probes")
DEFAULT_PROPOSALS = os.path.join(PLUGIN, "framework", "rules", "proposals")
SPEC = importlib.util.spec_from_file_location("harness_rule_registry", os.path.join(HERE, "rule_registry.py"))
REGISTRY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REGISTRY)


def load_probes(directory):
    probes = {}
    for path in glob.glob(os.path.join(directory, "*.json")):
        try:
            with open(path, encoding="utf-8") as handle:
                probe = json.load(handle)
            if isinstance(probe.get("rule"), str) and isinstance(probe.get("scored"), str):
                probes.setdefault(probe["rule"], []).append(probe)
        except (OSError, ValueError, AttributeError):
            continue
    for values in probes.values():
        values.sort(key=lambda probe: probe["scored"], reverse=True)
    return probes


def proposed_change(rule, probes):
    status = rule["status"]
    replay = rule.get("replay") if isinstance(rule.get("replay"), dict) else {}
    cases = replay.get("cases") if type(replay.get("cases")) is int else 0
    hits = replay.get("hits") if type(replay.get("hits")) is int else 0
    recent = probes[:1]
    if recent and recent[0].get("complete") is not True:
        return None
    if status == "shadow":
        if not recent:
            return None
        probe = recent[0]
        on = probe.get("on", {})
        cases = on.get("cases") if type(on.get("cases")) is int else cases
        hits = on.get("hits") if type(on.get("hits")) is int else hits
        if cases < 3:
            return None
        fp_rate = on.get("false_positive_rate")
        declined = on.get("declined_cases")
        off = probe.get("off", {})
        adds_hits = probe.get("adds_hits") is True
        recall = REGISTRY.rate(hits, cases)
        comparable = (type(declined) is int and declined > 0
                      and off.get("cases") == cases and off.get("declined_cases") == declined)
        if recall >= 0.6 and isinstance(fp_rate, (int, float)) and fp_rate <= 0.15 and adds_hits and comparable:
            return "active", "%s/%s replay hits (%.3f recall); FP rate %.3f; paired probe on adds hits" % (
                hits, cases, recall, fp_rate)
        return None
    if status == "active":
        latest_fp = recent[0].get("on", {}).get("false_positive_rate") if recent else None
        if isinstance(latest_fp, (int, float)) and latest_fp > 0.3:
            return "retired", "latest scored replay FP rate %.3f exceeds 0.300" % latest_fp
        if len(probes) >= 3 and all(probe.get("complete") is True and probe.get("on", {}).get("hits") == 0
                                    for probe in probes[:3]):
            return "retired", "zero hits in the last three scored replays"
    return None


def render_registry(data):
    return json.dumps(data, indent=2) + "\n"


def build_proposal(registry_path=REGISTRY.DEFAULT_REGISTRY, probes_dir=DEFAULT_PROBES,
                   proposals_dir=DEFAULT_PROPOSALS, today=None, apply_registry=False):
    data, _ = REGISTRY.load_registry(registry_path)
    before = render_registry(data)
    probes = load_probes(probes_dir)
    changes = []
    for rule in data["rules"]:
        proposed = proposed_change(rule, probes.get(rule["id"], []))
        if proposed:
            target, evidence = proposed
            probe = probes[rule["id"]][0]
            on = probe["on"]
            changes.append((rule["id"], rule["status"], target, evidence))
            rule["status"] = target
            rule["replay"] = {"cases": on["cases"], "hits": on["hits"],
                              "false_positives": on["false_positives"], "last_scored": probe["scored"]}
            rule["notes"] = (rule.get("notes", "").rstrip() + " Proposed from replay evidence: " + evidence).strip()
    after = render_registry(data)
    day = today or datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    os.makedirs(proposals_dir, exist_ok=True)
    proposal_path = os.path.join(proposals_dir, day + ".md")
    patch_path = os.path.join(proposals_dir, day + ".patch")
    rows = ["# Rule Lifecycle Proposal: %s" % day, "", "Agent prompts are never edited by this command.", "",
            "| id | from | to | evidence |", "|---|---|---|---|"]
    rows += ["| %s | %s | %s | %s |" % change for change in changes]
    if not changes:
        rows.append("| — | — | — | No rule has enough evidence to change status. |")
    with open(proposal_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(rows) + "\n")
    patch = difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                 fromfile="a/framework/rules/registry.yml",
                                 tofile="b/framework/rules/registry.yml")
    with open(patch_path, "w", encoding="utf-8") as handle:
        handle.writelines(patch)
    if apply_registry and changes:
        REGISTRY.write_registry(registry_path, data)
    return proposal_path, patch_path, changes


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", default=REGISTRY.DEFAULT_REGISTRY)
    parser.add_argument("--probes-dir", default=DEFAULT_PROBES)
    parser.add_argument("--proposals-dir", default=DEFAULT_PROPOSALS)
    parser.add_argument("--apply-registry", action="store_true",
                        help="apply proposed status changes to registry.yml after human approval")
    args = parser.parse_args(argv)
    proposal, patch, changes = build_proposal(args.registry, args.probes_dir, args.proposals_dir,
                                               apply_registry=args.apply_registry)
    print("wrote %s and %s (%s proposed changes)" % (proposal, patch, len(changes)))
    if changes:
        print("Reviewer prompt edits remain manual.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
