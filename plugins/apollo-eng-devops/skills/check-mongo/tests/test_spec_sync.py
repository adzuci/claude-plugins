"""references/checks.md is the single source of truth; these tests stop it drifting from the code."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

promql = pytest.importorskip("promql")
evaluate = pytest.importorskip("evaluate")

SPEC = Path(__file__).resolve().parent.parent / "references" / "checks.md"
CELL_SPLIT = re.compile(r"(?<!\\)\|")


def tables():
    """Return {first header cell: [row dicts]} for every markdown table in checks.md."""
    out, header, name = {}, None, None
    for line in SPEC.read_text().splitlines():
        if not line.startswith("|"):
            header = None
            continue
        cells = [c.strip().replace("\\|", "|").strip("`") for c in CELL_SPLIT.split(line.strip())[1:-1]]
        if header is None:
            header, name = cells, cells[0]
            out[name] = []
        elif not set("".join(cells)) <= set("-: "):
            out[name].append(dict(zip(header, cells)))
    return out


def test_spec_exists_and_is_compact():
    assert SPEC.exists()
    assert len(SPEC.read_text().splitlines()) <= 90


def test_queries_match_promql_py_exactly():
    rows = {r["id"]: r for r in tables()["id"]}
    built = promql.build_queries("main", "6h", "all")
    assert list(rows) == [q["id"] for q in built]
    for q in built:
        expr = q["expr"].replace('cluster="main"', 'cluster="<c>"').replace("[6h]", "[<w>]")
        assert rows[q["id"]]["PromQL"] == expr, q["id"]
        assert rows[q["id"]]["kind"] == q["kind"], q["id"]


def test_thresholds_match_evaluate_defaults():
    rows = {r["threshold"]: float(r["default"]) for r in tables()["threshold"]}
    assert rows == evaluate.DEFAULTS


def test_check_ids_match_evaluator_findings(load):
    spec_ids = [r["check"] for r in tables()["check"]]
    got = [f["check"] for f in evaluate.evaluate(load("healthy"), "main")["findings"]]
    assert sorted(spec_ids) == sorted(got)


def test_status_precedence_matches_evaluator():
    ordered = sorted(evaluate.RANK, key=evaluate.RANK.get, reverse=True)
    assert " > ".join(ordered) in SPEC.read_text()


def test_units_and_non_negotiable_rules_are_stated():
    text = SPEC.read_text()
    for needle in ("MB", "GiB", "MemAvailable", "MemTotal", "UNKNOWN", "up==0", "24h", "HUMAN-ONLY",
                   "code=killed", "code=exited", "Fault manager progress monitor", "15-30 min"):
        assert needle in text, needle


def test_report_shape_examples_fit_argus_budget():
    path = SPEC.parent / "report-shape.md"
    assert len(path.read_text().splitlines()) <= 25
    block = path.read_text().split("```text")[1].split("```")[0]
    examples = [e for e in block.split("\n\n") if e.strip()]
    assert len(examples) == 2
    for e in examples:
        assert len(e.split()) <= 120
        for b in ("**Alert**", "**Root cause**", "**Couldn't verify**", "**Next step**"):
            assert b in e


def test_skill_md_stays_scannable_and_documents_modes():
    text = (SPEC.parent.parent / "SKILL.md").read_text()
    assert len(text.splitlines()) <= 100
    assert "disable-model-invocation: true" in text
    for needle in ("## Modes", "signals.cluster", "run_gcloud_command", "references/checks.md",
                   "references/report-shape.md", "HUMAN-ONLY", "never ask"):
        assert needle in text, needle
