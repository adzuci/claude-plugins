from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

render_ideas_report = pytest.importorskip("render_ideas_report")


def notion_fixture():
    return {
        "results": [
            {
                "url": "https://notion.example/idea-1",
                "properties": {
                    "Idea Name": {"title": [{"plain_text": "Hidden Sequence Step Control"}]},
                    "Status": {"select": {"name": "New"}},
                    "Impact Level": {"select": {"name": "High"}},
                    "Effort to Fix": {"select": {"name": "Low"}},
                    "Product Area": {"select": {"name": "Sequences"}},
                    "Entry Type": {"multi_select": [{"name": "Product Fix"}]},
                    "Date": {"date": {"start": "2026-06-14"}},
                    "Description": {
                        "rich_text": [
                            {
                                "plain_text": (
                                    "Customer could not find the manual email step control while building a sequence."
                                )
                            }
                        ]
                    },
                },
            },
            {
                "url": "https://notion.example/idea-2",
                "properties": {
                    "Idea Name": {"title": [{"plain_text": "Export Error Copy Clarification"}]},
                    "Status": {"select": {"name": "Under Review"}},
                    "Impact Level": {"select": {"name": "Medium"}},
                    "Effort to Fix": {"select": {"name": "Medium"}},
                    "Product Area": {"select": {"name": "Exports"}},
                    "Entry Type": {"multi_select": [{"name": "Product Enhancement"}]},
                    "Date": {"date": {"start": "2026-06-01"}},
                    "Description": {"rich_text": [{"plain_text": "Support saw repeated export confusion."}]},
                },
            },
        ]
    }


def test_normalize_notion_page():
    idea = render_ideas_report.normalize(notion_fixture()["results"][0])

    assert idea.title == "Hidden Sequence Step Control"
    assert idea.status == "New"
    assert idea.impact == "High"
    assert idea.effort == "Low"
    assert idea.product_area == "Sequences"
    assert idea.entry_type == "Product Fix"
    assert idea.date is not None and idea.date.date().isoformat() == "2026-06-14"
    assert idea.url == "https://notion.example/idea-1"


def test_since_cutoff_supports_relative_and_absolute_values():
    now = datetime(2026, 6, 15, 12, tzinfo=timezone.utc)

    assert render_ideas_report.since_cutoff("all", now) is None
    assert render_ideas_report.since_cutoff("2d", now).date().isoformat() == "2026-06-13"
    assert render_ideas_report.since_cutoff("1w", now).date().isoformat() == "2026-06-08"
    assert render_ideas_report.since_cutoff("1m", now).date().isoformat() == "2026-05-16"
    assert render_ideas_report.since_cutoff("2026-06-01", now).date().isoformat() == "2026-06-01"


def test_since_cutoff_rejects_invalid_values():
    now = datetime(2026, 6, 15, 12, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="--since must be"):
        render_ideas_report.since_cutoff("bananas", now)


def test_render_report_filters_timeframe_and_writes_nested_output(tmp_path, monkeypatch, capsys):
    input_path = tmp_path / "ideas.json"
    output_path = tmp_path / "nested" / "report.html"
    input_path.write_text(json.dumps(notion_fixture()))
    monkeypatch.setattr(
        "sys.argv",
        [
            "render_ideas_report.py",
            "--input",
            str(input_path),
            "--output",
            str(output_path),
            "--since",
            "2d",
            "--now",
            "2026-06-15T12:00:00Z",
            "--title",
            "Support Rotation Ideas",
        ],
    )

    assert render_ideas_report.main() == 0
    assert "Wrote 1 ideas" in capsys.readouterr().out

    html = output_path.read_text()
    assert "Rows in scope: 1" in html
    assert "Hidden Sequence Step Control" in html
    assert "Export Error Copy Clarification" not in html
    assert "High Impact / Low Effort" in html
