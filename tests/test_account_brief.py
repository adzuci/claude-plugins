from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO / "plugins" / "apollo-support" / "skills" / "account-brief"


def read_skill_file(relative: str) -> str:
    return (SKILL_DIR / relative).read_text()


def load_script(name: str):
    path = SKILL_DIR / "scripts" / name
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# SKILL.md frontmatter + routing
# ---------------------------------------------------------------------------


def test_skill_frontmatter_and_usage():
    skill = read_skill_file("SKILL.md")

    assert "name: account-brief" in skill
    assert "disable-model-invocation: true" in skill
    assert "Run via /apollo-support:account-brief." in skill
    assert "/apollo-support:account-brief [target] [--daily] [--html]" in skill
    for ref in (
        "references/account-brief-mode.md",
        "references/daily-ticket-summary.md",
        "references/red-flag-signals.md",
        "references/data-sources.md",
        "references/output-shapes.md",
    ):
        assert ref in skill


# ---------------------------------------------------------------------------
# resolve_target.classify_target — each of the 3 kinds
# ---------------------------------------------------------------------------


def test_classify_target_am():
    resolve = load_script("resolve_target.py")

    assert resolve.classify_target("Adam Blackwell") == "am"
    assert resolve.classify_target("adam@apollo.io") == "am"


def test_classify_target_domain():
    resolve = load_script("resolve_target.py")

    assert resolve.classify_target("acme.com") == "domain"
    assert resolve.classify_target("sub.example.co.uk") == "domain"


def test_classify_target_account_id():
    resolve = load_script("resolve_target.py")

    # All-digits id.
    assert resolve.classify_target("12345678") == "account_id"
    # Salesforce-style 15-char id (contains digits).
    assert resolve.classify_target("001Ab00000XyZ12") == "account_id"


def test_classify_target_rejects_empty():
    resolve = load_script("resolve_target.py")

    with pytest.raises(ValueError):
        resolve.classify_target("   ")


def test_build_lookup_plan_is_read_only_and_optional():
    resolve = load_script("resolve_target.py")

    for kind in ("am", "domain", "account_id"):
        plan = resolve.build_lookup_plan(kind, "value")
        assert plan["kind"] == kind
        assert plan["read_only"] is True
        assert plan["sources"], f"no sources for {kind}"
        assert all(source["optional"] is True for source in plan["sources"])
        names = {source["source"] for source in plan["sources"]}
        assert {"salesforce", "snowflake"}.issubset(names)

    with pytest.raises(ValueError):
        resolve.build_lookup_plan("bogus", "value")


# ---------------------------------------------------------------------------
# render_account_brief — minimal payload, no fabrication
# ---------------------------------------------------------------------------


def test_render_markdown_minimal_payload_omits_missing_without_fabricating():
    render = load_script("render_account_brief.py")

    md = render.render_markdown({"account": {"name": "Acme"}})

    # The one known fact is present.
    assert "# Account Brief: Acme" in md
    # Missing known fields render as the explicit placeholder, not invented values.
    assert "unknown / needs checking" in md
    # Empty sections show literal empty-state lines, not fabricated rows.
    assert "No open support tickets recorded." in md
    assert "No red-flag signals recorded." in md
    assert "No recent activity recorded." in md
    # No em dashes in output.
    assert "—" not in md


def test_render_markdown_sorts_flags_p0_first_and_renders_tickets():
    render = load_script("render_account_brief.py")

    md = render.render_markdown(
        {
            "account": {"name": "Beta", "domain": "beta.com"},
            "open_tickets": [
                {"id": "T-1", "subject": "Login broken", "severity": "P1", "status": "open", "age_days": 5, "owner": "Sam"}
            ],
            "red_flags": [
                {"tier": "P2", "signal": "Usage decline", "detail": "down 30%", "source": "Snowflake"},
                {"tier": "P0", "signal": "At-risk renewal", "detail": "renewal_risk=at-risk", "source": "Salesforce"},
            ],
        }
    )

    assert "beta.com" in md
    assert "Login broken" in md
    # P0 flag must appear before the P2 flag.
    assert md.index("At-risk renewal") < md.index("Usage decline")


def test_render_daily_mode_changes_heading():
    render = load_script("render_account_brief.py")

    md = render.render_markdown({"mode": "daily", "account": {"name": "Gamma"}})
    assert "# Daily Ticket Summary: Gamma" in md


def test_render_html_minimal_payload_is_self_contained():
    render = load_script("render_account_brief.py")

    out = render.render_html({"account": {"name": "<Acme>"}})

    assert out.startswith("<!doctype html>")
    # HTML-escaped, not fabricated.
    assert "&lt;Acme&gt;" in out
    assert "No open support tickets recorded." in out
    # No external asset requests.
    assert "http://" not in out and "https://" not in out


def test_load_payload_rejects_non_object(tmp_path):
    render = load_script("render_account_brief.py")

    path = tmp_path / "payload.json"
    path.write_text(json.dumps(["not", "an", "object"]))
    with pytest.raises(ValueError):
        render.load_payload(str(path))


# ---------------------------------------------------------------------------
# check_dependencies — CLI + agent-checked deps
# ---------------------------------------------------------------------------


def test_dependency_checker_reports_snow_sf_and_intercom(monkeypatch):
    deps = load_script("check_dependencies.py")
    monkeypatch.setattr(deps.shutil, "which", lambda _name: None)

    statuses = deps.collect_statuses()
    names = {item.name: item for item in statuses}

    assert names["snow"].status == "missing"
    assert names["sf"].status == "missing"
    assert names["intercom_mcp"].status == "agent-check-required"


# ---------------------------------------------------------------------------
# reference-file discipline
# ---------------------------------------------------------------------------


def test_references_have_read_only_and_no_fabrication_discipline():
    mode = read_skill_file("references/account-brief-mode.md")
    flags = read_skill_file("references/red-flag-signals.md")
    sources = read_skill_file("references/data-sources.md")

    assert "Never mutate any source" in mode
    assert "Trace every flag to an explicit source value" in flags
    for tier in ("P0", "P1", "P2"):
        assert tier in flags
    # Snowflake + Salesforce fetch forms, no hardcoded creds.
    assert "snow sql --connection apollo" in sources
    assert "sf api request rest --target-org apollo-sfdc" in sources
    assert "OPTIONAL" in sources


def test_reference_files_have_no_em_dashes():
    for name in (
        "references/account-brief-mode.md",
        "references/daily-ticket-summary.md",
        "references/red-flag-signals.md",
        "references/data-sources.md",
        "references/output-shapes.md",
    ):
        assert "—" not in read_skill_file(name), f"Em dash found in {name}"
