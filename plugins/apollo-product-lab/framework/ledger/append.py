#!/usr/bin/env python3
"""Ledger write, validated against schema.json before anything is appended.

Usage (from a run):
    python3 append.py <initiative> --run <run_id> --event <event_id> \
        --stage F.build --agent ads-backend --outcome resolved-clean \
        [--model <served model>] [--tokens <int>] [--minutes <num>] [--prompt-chars <int>] [--evidence <path-or-url>]... \
        [--parent <event_id>] [--evidence-available true] [--surface ads.frontend] \
        [--human <who> --human-rationale "..." --gate-override false] [--note "..."] [--force]

Writes one JSON object per line to <repo root>/.ai/<initiative>/ledger.jsonl, where the repo root is the
current directory (or HARNESS_REPO_ROOT). Run it from the product repo, not from the plugin checkout. Refuses: a record that violates
the schema (unknown field, bad task_class, bad outcome), and a duplicate event_id unless --force
(the retry after an interrupted stage is the common case; the second write must be deliberate).
"""
import argparse, json, math, os, re, sys
from datetime import datetime, timezone
try:
    import fcntl
except ImportError:
    fcntl = None

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = json.load(open(os.path.join(HERE, "schema.json")))

def validate(rec):
    errs = []
    props = SCHEMA["properties"]
    for k in SCHEMA["required"]:
        if k not in rec or rec[k] in (None, ""): errs.append(f"missing {k}")
    for k in rec:
        if k not in props: errs.append(f"unknown field {k}")
    for k, v in rec.items():
        spec = props.get(k)
        if not spec: continue
        if "pattern" in spec and isinstance(v, str) and not re.match(spec["pattern"], v): errs.append(f"{k}={v!r} does not match {spec['pattern']}")
        if "enum" in spec and v not in spec["enum"]: errs.append(f"{k}={v!r} not in {spec['enum']}")
        if spec.get("type") == "integer" and (isinstance(v, bool) or not isinstance(v, int)): errs.append(f"{k} must be an integer")
        if spec.get("type") == "number" and (isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)): errs.append(f"{k} must be a finite number")
        if "minimum" in spec and isinstance(v, (int, float)) and not isinstance(v, bool) and v < spec["minimum"]: errs.append(f"{k} below {spec['minimum']}")
        if spec.get("type") == "boolean" and not isinstance(v, bool): errs.append(f"{k} must be a boolean")
        if spec.get("type") == "array" and not isinstance(v, list): errs.append(f"{k} must be a list")
        if "maxLength" in spec and isinstance(v, str) and len(v) > spec["maxLength"]: errs.append(f"{k} longer than {spec['maxLength']}")
    return errs

def main():
    p = argparse.ArgumentParser()
    p.add_argument("initiative")
    p.add_argument("--run", required=True, dest="run_id")
    p.add_argument("--event", required=True, dest="event_id")
    p.add_argument("--stage", required=True, dest="task_class", help="A.audit, F.build, council.adr-p3, ...")
    p.add_argument("--agent", required=True)
    p.add_argument("--outcome", required=True, choices=SCHEMA["properties"]["outcome"]["enum"])
    p.add_argument("--model", default=None, help="model actually served")
    p.add_argument("--tokens", type=int, default=None)
    p.add_argument("--minutes", type=float, default=None, help="wall-clock minutes (doc 46)")
    p.add_argument("--prompt-chars", dest="prompt_chars", type=int, default=None, help="reviewer prompt size, wc -c (doc 46)")
    p.add_argument("--evidence", action="append", default=[], help="snapshot path, URL, or commit; repeatable")
    p.add_argument("--parent", dest="parent_id", default=None)
    p.add_argument("--evidence-available", dest="evidence_available", default=None)
    p.add_argument("--surface", default=None)
    p.add_argument("--human", default=None)
    p.add_argument("--human-rationale", dest="human_rationale", default=None)
    p.add_argument("--gate-override", dest="gate_override", default=None)
    p.add_argument("--note", default=None)
    p.add_argument("--force", action="store_true", help="allow a duplicate event_id")
    a = p.parse_args()

    rec = {"ts": datetime.now(timezone.utc).isoformat(), "run_id": a.run_id, "event_id": a.event_id,
           "initiative": a.initiative, "task_class": a.task_class, "agent": a.agent, "outcome": a.outcome}
    if a.model: rec["model"] = a.model
    if a.tokens is not None: rec["tokens"] = a.tokens
    if a.minutes is not None: rec["minutes"] = a.minutes
    if a.prompt_chars is not None: rec["prompt_chars"] = a.prompt_chars
    if a.evidence: rec["evidence"] = a.evidence
    if a.parent_id: rec["parent_id"] = a.parent_id
    if a.evidence_available is not None: rec["evidence_available"] = a.evidence_available.lower() in ("1", "true", "yes")
    if a.surface: rec["surface"] = a.surface
    if a.human: rec["human"] = a.human
    if a.human_rationale: rec["human_rationale"] = a.human_rationale
    if a.gate_override is not None: rec["gate_override"] = a.gate_override.lower() in ("1", "true", "yes")
    if a.note: rec["notes"] = a.note

    errs = validate(rec)
    if errs:
        print("refusing to write: " + "; ".join(errs), file=sys.stderr); sys.exit(1)

    # The ledger belongs to the product repo the harness is run from, never to the plugin checkout.
    root = os.environ.get("HARNESS_REPO_ROOT") or os.getcwd()
    path = os.path.abspath(os.path.join(root, ".ai", a.initiative, "ledger.jsonl"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a+") as f:
        if fcntl:  # the same lock storage.py from-notion takes, so an import never loses this line
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        f.seek(0)
        for line in ([] if a.force else f):
            try:
                if json.loads(line).get("event_id") == a.event_id:
                    print(f"refusing to write: event_id {a.event_id} already recorded (use --force for a deliberate second record)", file=sys.stderr); sys.exit(1)
            except json.JSONDecodeError:
                print(f"refusing to write: {path} has a malformed line; repair it first", file=sys.stderr); sys.exit(1)
        f.seek(0, os.SEEK_END)
        f.write(json.dumps(rec, allow_nan=False) + "\n")
    print(f"ledger += {rec['event_id']} ({rec['outcome']}) -> {path}")

if __name__ == "__main__":
    main()
