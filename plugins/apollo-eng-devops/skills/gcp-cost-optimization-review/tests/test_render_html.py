"""Tests for render_html.py — the deterministic HTML renderer behind the
`html` argument on gcp-cost-optimization-review.

Runs on Python 3.9 and 3.11 (see repo CLAUDE.md Testing convention).
"""
from __future__ import annotations

import json

import pytest

render_html = pytest.importorskip("render_html")


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------


def test_fmt_usd_rounds_large_and_keeps_cents_small():
    assert render_html.fmt_usd(137635) == "$137,635"
    assert render_html.fmt_usd(2.99) == "$2.99"
    assert render_html.fmt_usd(0) == "$0"
    assert render_html.fmt_usd(-1059) == "-$1,059"
    assert render_html.fmt_usd(8430, signed=True) == "+$8,430"


def test_fmt_usd_passes_strings_through_escaped():
    assert render_html.fmt_usd("<b>x</b>") == "&lt;b&gt;x&lt;/b&gt;"


def test_fmt_pct():
    assert render_html.fmt_pct(6.5) == "+6.5%"
    assert render_html.fmt_pct(-0.4) == "-0.4%"


def test_esc_handles_none_and_quotes():
    assert render_html.esc(None) == ""
    assert render_html.esc('a"b') == "a&quot;b"


# ---------------------------------------------------------------------------
# Zero-column folding
# ---------------------------------------------------------------------------


def test_drop_zero_columns_folds_all_zero_columns_and_keeps_key():
    cols = ["Week", "commitments", "pd-ssd", "snapshots", "other"]
    rows = [["w1", 100, 0, 0, 1], ["w2", 120, 0, "$0", 0]]
    new_cols, new_rows, dropped = render_html.drop_zero_columns(cols, rows)
    assert new_cols == ["Week", "commitments", "other"]
    assert new_rows == [["w1", 100, 1], ["w2", 120, 0]]
    assert dropped == ["pd-ssd", "snapshots"]


def test_drop_zero_columns_never_drops_first_column_even_if_zero():
    cols = ["key", "v"]
    rows = [[0, 1], [0, 2]]
    new_cols, _, dropped = render_html.drop_zero_columns(cols, rows)
    assert new_cols == ["key", "v"]
    assert dropped == []


def test_drop_zero_columns_empty_rows_is_noop():
    new_cols, new_rows, dropped = render_html.drop_zero_columns(["a", "b"], [])
    assert new_cols == ["a", "b"]
    assert new_rows == []
    assert dropped == []


def test_render_section_reports_folded_columns_once():
    section = {
        "step": "2c",
        "title": "t",
        "columns": ["Week", "cores", "pd-ssd"],
        "rows": [["w1", 5, 0], ["w2", 6, 0]],
    }
    out = render_html.render_section(section)
    assert "pd-ssd" in out
    assert out.count("folded out of the table") == 1
    assert "<th class=\"r\">cores</th>" in out
    assert "<th class=\"r\">pd-ssd</th>" not in out


def test_render_section_can_disable_folding():
    section = {
        "title": "t",
        "columns": ["Week", "pd-ssd"],
        "rows": [["w1", 0]],
        "fold_zero_columns": False,
    }
    out = render_html.render_section(section)
    assert "pd-ssd</th>" in out
    assert "folded out" not in out


# ---------------------------------------------------------------------------
# Sparkline
# ---------------------------------------------------------------------------


def test_sparkline_emits_one_bar_per_point_with_hover_titles():
    svg = render_html.sparkline_svg([10, 20, 30], ["a", "b", "c"], title="s")
    assert svg.count("<rect") == 3
    assert svg.count("<title>") == 3
    assert 'class="spark-bar last"' in svg
    assert ">a<" in svg and ">c<" in svg  # first and last labels only
    assert ">b<" not in svg


def test_sparkline_needs_two_points():
    assert render_html.sparkline_svg([5]) == ""
    assert render_html.sparkline_svg([]) == ""


def test_sparkline_zero_series_does_not_divide_by_zero():
    svg = render_html.sparkline_svg([0, 0])
    assert "<svg" in svg


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------


def test_recommendations_ranked_by_dollar_then_unknown_last():
    recs = [
        {"action": "no estimate", "monthly_usd": None},
        {"action": "small", "monthly_usd": 40},
        {"action": "big", "monthly_usd": 4000},
    ]
    ordered = [r["action"] for r in render_html.sort_recommendations(recs)]
    assert ordered == ["big", "small", "no estimate"]


def test_render_recommendations_caps_at_four_and_sums_addressable():
    recs = [{"action": "r{0}".format(i), "monthly_usd": 100 * (i + 1)} for i in range(6)]
    out = render_html.render_recommendations(recs)
    assert out.count('<li class="rec">') == 4
    # top four: 600+500+400+300
    assert "$1,800/mo addressable" in out
    assert "r0" not in out and "r1" not in out


def test_render_recommendations_empty_says_so_without_padding():
    out = render_html.render_recommendations([])
    assert "No recommendation cleared the quality bar" in out


def test_render_recommendations_escapes_fields():
    out = render_html.render_recommendations(
        [{"action": "<script>x</script>", "monthly_usd": 1, "what": "a&b"}]
    )
    assert "<script>" not in out
    assert "&lt;script&gt;" in out
    assert "a&amp;b" in out


# ---------------------------------------------------------------------------
# Findings, KPIs, since-last
# ---------------------------------------------------------------------------


def test_findings_unknown_kind_falls_back_to_info():
    out = render_html.render_findings([{"kind": "bogus", "title": "t", "body": "b"}])
    assert 'class="callout info"' in out


def test_kpis_format_numeric_values_and_cap_tone():
    out = render_html.render_kpis(
        [{"label": "x", "value": 1234, "tone": "sideways"}, {"label": "y", "value": "-0.4%", "tone": "up"}]
    )
    assert "$1,234" in out
    assert "kpi-v mono neutral" in out
    assert "kpi-v mono up" in out


def test_since_last_first_run_message():
    out = render_html.render_since_last([], None)
    assert "First run" in out


def test_since_last_status_pills():
    out = render_html.render_since_last(
        [{"recommendation": "r", "status": "DONE"}, {"recommendation": "s", "status": "weird"}],
        "2026-09-07",
    )
    assert 'class="pill done"' in out
    assert 'class="pill open"' in out


# ---------------------------------------------------------------------------
# Whole page
# ---------------------------------------------------------------------------


def test_sample_bundle_is_json_serializable_and_renders():
    bundle = render_html.sample_bundle()
    json.dumps(bundle)
    page = render_html.render_report(bundle)
    assert page.startswith("<!DOCTYPE html>")
    assert "<title>GCP Cost Review, mongo/main</title>" in page
    assert page.rstrip().endswith("</body></html>")
    assert "Accuracy." in page
    assert "Read-only" in page
    assert "<details open>" in page
    assert "</main>" in page and "<footer>" in page


def test_report_has_all_three_theme_states():
    page = render_html.render_report(render_html.sample_bundle())
    assert ":root{color-scheme:light" in page
    assert '@media (prefers-color-scheme:dark){:root:not([data-theme="light"])' in page
    assert ':root[data-theme="dark"]' in page
    assert "@media print" in page


def test_report_has_no_script_tag():
    page = render_html.render_report(render_html.sample_bundle())
    assert "<script" not in page


def test_report_title_defaults_when_scope_is_account_wide():
    page = render_html.render_report({"scope": "all projects", "run_date": "2026-09-14"})
    assert "<title>GCP Cost Review</title>" in page
    assert "First run in this directory" in page


def test_report_prior_run_renders_since_section():
    page = render_html.render_report(
        {"prior_report": "2026-09-07", "since_last": [{"recommendation": "r", "status": "open"}]}
    )
    assert "Since 2026-09-07" in page


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_main_help_and_no_args(capsys):
    assert render_html.main(["--help"]) == 0
    assert "usage" in capsys.readouterr().out
    assert render_html.main([]) == 2


def test_main_sample_bundle_roundtrips_through_file(tmp_path, capsys):
    assert render_html.main(["--sample-bundle"]) == 0
    bundle_json = capsys.readouterr().out
    path = tmp_path / "bundle.json"
    path.write_text(bundle_json, encoding="utf-8")
    assert render_html.main([str(path)]) == 0
    assert "<title>" in capsys.readouterr().out


def test_main_rejects_non_object_bundle(tmp_path, capsys):
    path = tmp_path / "bad.json"
    path.write_text("[1,2]", encoding="utf-8")
    assert render_html.main([str(path)]) == 1
    assert "bundle must be a JSON object" in capsys.readouterr().err
