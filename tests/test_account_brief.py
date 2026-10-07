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
        "references/slack-delivery.md",
    ):
        assert ref in skill


def test_skill_documents_slack_as_default_delivery():
    skill = read_skill_file("SKILL.md")

    # Slack delivery must be stated in SKILL.md itself, not only in a reference,
    # so the agent sees it without loading anything extra.
    assert "Slack Is The Default Delivery" in skill
    assert "--bundle" in skill
    # The exact failure this change exists to prevent.
    assert "Never paste raw HTML" in skill


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


# ---------------------------------------------------------------------------
# Slack summary — mrkdwn correctness, caveat placement, standalone fallback
# ---------------------------------------------------------------------------


SLACK_PAYLOAD = {
    "account": {"name": "Acme", "domain": "acme.com"},
    "data_window": "last 24h from 2026-08-19 09:00 PT",
    "sources": [
        {"name": "Snowflake", "status": "ok"},
        {"name": "Salesforce", "status": "unavailable", "impact": "plan and ARR are unverified"},
    ],
    "caveats": ["Intercom pulled at 09:00 PT. Later conversations not included."],
    "health": {"status": "at risk", "csat": "3.2"},
    "open_tickets": [
        {"id": "T-1", "subject": "Login broken", "severity": "P1", "status": "open", "age_days": 5, "owner": "Sam"}
    ],
    "red_flags": [
        {"tier": "P2", "signal": "Usage decline", "detail": "down 30%", "source": "Snowflake"},
        {"tier": "P0", "signal": "At-risk renewal", "detail": "renewal_risk=at-risk", "source": "Salesforce"},
    ],
}


def test_render_slack_uses_mrkdwn_not_markdown():
    render = load_script("render_account_brief.py")

    out = render.render_slack(SLACK_PAYLOAD)

    # Slack mrkdwn: *bold*, never **bold**, no # headers, no pipe tables.
    assert "**" not in out
    assert not any(line.startswith("#") for line in out.splitlines())
    assert not any(line.startswith("|") for line in out.splitlines())
    assert "*Account Brief: Acme*" in out
    assert "—" not in out


def test_render_slack_puts_caveats_above_the_numbers():
    render = load_script("render_account_brief.py")

    out = render.render_slack(SLACK_PAYLOAD)

    # The whole point: a reader who stops early still sees the gaps.
    assert ":warning:" in out
    assert "Salesforce unavailable: plan and ARR are unverified" in out
    assert "Intercom pulled at 09:00 PT. Later conversations not included." in out
    assert out.index("Data coverage:") < out.index("*Health*")
    assert out.index("Data coverage:") < out.index("*Red flags")


def test_render_slack_reports_clean_coverage_and_flags_unrecorded_coverage():
    render = load_script("render_account_brief.py")

    clean = render.render_slack({"account": {"name": "Acme"}, "sources": [{"name": "Snowflake", "status": "ok"}]})
    assert "No coverage gaps recorded" in clean
    assert ":warning:" not in clean

    # Omitting sources must not read as full coverage.
    silent = render.render_slack({"account": {"name": "Acme"}})
    assert "Source coverage not recorded" in silent


def test_render_slack_stands_alone_and_names_attachments():
    render = load_script("render_account_brief.py")

    with_files = render.render_slack(SLACK_PAYLOAD, ["account-brief.png", "account-brief.html"])
    assert "Full brief attached: account-brief.png, account-brief.html." in with_files

    # If attachments fail, the summary must still say what the reader has.
    without = render.render_slack(SLACK_PAYLOAD)
    assert "No attachment rendered" in without
    # Both carry the actionable content regardless.
    for out in (with_files, without):
        assert "At-risk renewal" in out
        assert "Login broken" in out


def test_render_slack_sorts_p0_first_and_truncates_long_lists():
    render = load_script("render_account_brief.py")

    payload = dict(SLACK_PAYLOAD)
    payload["open_tickets"] = [
        {"id": f"T-{n}", "subject": f"Issue {n}", "severity": "P2", "status": "open", "age_days": n, "owner": "Sam"}
        for n in range(12)
    ]
    out = render.render_slack(payload)

    assert out.index("At-risk renewal") < out.index("Usage decline")
    assert "*Open tickets (12)*" in out
    # Capped, and honest about what was cut rather than silently dropping rows.
    assert f"+{12 - render.SLACK_MAX_TICKETS} more tickets in the attached brief." in out
    assert len(out) <= render.SLACK_CHAR_BUDGET


def test_markdown_and_html_also_lead_with_caveats():
    render = load_script("render_account_brief.py")

    md = render.render_markdown(SLACK_PAYLOAD)
    assert md.index("Data Coverage And Caveats") < md.index("## Health Summary")
    assert "Salesforce unavailable" in md

    out = render.render_html(SLACK_PAYLOAD)
    assert out.index("Data Coverage And Caveats") < out.index("Health Summary")
    assert "caveats-warn" in out
    assert "http://" not in out and "https://" not in out


# ---------------------------------------------------------------------------
# Bundle + PNG — first-class artifact, degrades instead of failing
# ---------------------------------------------------------------------------


def test_render_bundle_writes_every_artifact_and_degrades_without_png(tmp_path, monkeypatch):
    render = load_script("render_account_brief.py")
    png = load_script("render_png.py")

    # Simulate a machine with no PNG renderer installed.
    monkeypatch.setattr(png, "render_png", lambda *a, **k: (False, "no PNG renderer available"))
    monkeypatch.setitem(sys.modules, "render_png", png)

    manifest = render.render_bundle(SLACK_PAYLOAD, tmp_path)

    assert Path(manifest["markdown"]).exists()
    assert Path(manifest["html"]).exists()
    assert Path(manifest["slack_file"]).exists()
    # PNG failure degrades the bundle; it never fails it.
    assert manifest["png"] is None
    assert manifest["attachments"] == ["account-brief.html"]
    assert "At-risk renewal" in manifest["slack_text"]


def test_render_png_reports_actionable_reason_when_no_renderer(tmp_path, monkeypatch):
    png = load_script("render_png.py")

    html_path = tmp_path / "brief.html"
    html_path.write_text("<!doctype html><html><body>hi</body></html>")
    monkeypatch.setattr(png, "render_with_playwright", lambda *a: (_ for _ in ()).throw(ImportError("no playwright")))
    monkeypatch.setattr(png, "CHROME_BINARIES", ("definitely-not-a-browser",))

    ok, detail = png.render_png(html_path, tmp_path / "brief.png")

    assert ok is False
    # The caller needs the fix and the fallback, not just "failed".
    assert "playwright" in detail.lower()
    assert "Attach the HTML file instead" in detail


def test_output_formats_are_mutually_exclusive():
    render = load_script("render_account_brief.py")

    # Each format alone parses fine.
    assert render.parse_args(["--slack"]).slack is True
    assert render.parse_args(["--bundle", "out"]).bundle == "out"

    # Combining them errors instead of silently picking one.
    for combo in (["--slack", "--html"], ["--bundle", "out", "--slack"], ["--html", "--bundle", "out"]):
        with pytest.raises(SystemExit):
            render.parse_args(combo)


def test_render_png_missing_html_does_not_raise(tmp_path):
    png = load_script("render_png.py")

    ok, detail = png.render_png(tmp_path / "absent.html", tmp_path / "out.png")

    assert ok is False
    assert "not found" in detail


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


def test_slack_delivery_reference_states_the_contract():
    slack = read_skill_file("references/slack-delivery.md")

    assert "Never paste the full HTML document" in slack
    # Attachments are best-effort; the summary is the deliverable.
    assert "When Attachments Fail" in slack
    assert "Caveats Go Above The Numbers" in slack
    assert "Freshness And Superseding" in slack
    assert "--bundle" in slack


def test_reference_files_have_no_em_dashes():
    for name in (
        "references/account-brief-mode.md",
        "references/daily-ticket-summary.md",
        "references/red-flag-signals.md",
        "references/data-sources.md",
        "references/output-shapes.md",
        "references/slack-delivery.md",
    ):
        assert "—" not in read_skill_file(name), f"Em dash found in {name}"
