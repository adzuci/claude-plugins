from __future__ import annotations

import datetime

import pytest

pytest.importorskip("yaml")
pytest.importorskip("requests")

import eol_calendar as ec  # noqa: E402
import sheets_push as sp  # noqa: E402

TODAY = datetime.date(2026, 10, 14)
CFG = {"sheet_name": "Support Windows", "start_year": 2025, "end_year": 2029}
BARS = [
    {"header": "Pritunl", "color": "#5c6bc0"},
    {"label": "Pritunl server", "color": "#5c6bc0", "note": True, "state": "UNKNOWN"},
    {"header": "Mongo", "color": "#13aa52"},
    {"label": "Mongo 6.0", "color": "#13aa52", "running": True, "planned": False,
     "start": datetime.date(2022, 7, 19), "end": datetime.date(2025, 7, 31), "state": "EOL PASSED"},
    {"label": "Mongo 8.0", "color": "#13aa52", "running": False, "planned": False,
     "start": datetime.date(2024, 10, 31), "end": datetime.date(2029, 10, 31), "state": "n/a"},
]
STATUS = [
    dict(product="Mongo", version="6.0", running="running", eol="2025-07-31", state="EOL PASSED",
         tickets=["INFRA-1528", "INFRA-1958"], ticket="INFRA-1528, INFRA-1958", note="n", source="s"),
    dict(product="Debian", version="11", running="running", eol="2026-08-31", state="EOL PASSED",
         tickets=[], ticket="NO TICKET", note="n", source="s"),
]


@pytest.fixture
def payload():
    return ec.to_payload(BARS, STATUS, CFG, today=TODAY)


def test_grid_is_rectangular_with_year_and_month_headers(payload):
    rows, borders, merges = sp.build_grid(payload)
    assert len({len(r) for r in rows}) == 1
    assert len(rows[0]) == 2 + 60
    assert rows[0][2]["userEnteredValue"]["stringValue"] == "2025"
    assert rows[1][2]["userEnteredValue"]["stringValue"] == "J"
    assert len(rows) == len(payload["rows"]) + 3


def test_running_bar_is_outlined_and_flagged(payload):
    rows, borders, merges = sp.build_grid(payload)
    assert len(borders) == 1  # only the running bar
    assert rows[5][1]["userEnteredValue"]["stringValue"] == "EOL PASSED"


def test_calendar_requests_unmerge_and_reset_before_writing(payload):
    reqs = sp.calendar_requests(7, payload)
    kinds = [next(iter(r)) for r in reqs]
    assert kinds[0] == "unmergeCells" and kinds[1] == "repeatCell"
    assert kinds.index("updateCells") > kinds.index("repeatCell")
    assert "updateBorders" in kinds


def test_dry_run_plans_new_tabs_without_api_calls(payload):
    actions = sp.push("sheet-id", payload, "Support Windows", dry_run=True)
    assert any("add tab 'Support Windows'" in a for a in actions)
    assert any("one atomic batch" in a for a in actions)


def test_drop_openedx_only_with_flag(payload):
    assert not any("delete tab" in a for a in sp.push("x", payload, "S", dry_run=True))


def test_rgb_converts_hex():
    assert sp.rgb("#ff0000") == {"red": 1.0, "green": 0.0, "blue": 0.0}


def test_years_are_merged_and_bar_labels_sit_inside_bars(payload):
    rows, _, merges = sp.build_grid(payload)
    year_merges = [m for m in merges if m[0] == 0]
    assert len(year_merges) == 5 and all(n == 12 for _, _, n in year_merges)
    bar_row = 5  # Mongo 6.0
    in_bar = [m for m in merges if m[0] == bar_row]
    assert len(in_bar) == 1
    first_col = in_bar[0][1]
    assert rows[bar_row][first_col]["userEnteredValue"]["stringValue"] == "Mongo 6.0"


def test_short_bars_keep_label_out_of_bar():
    bars = [{"label": "Rust 1.95", "color": "#8d4a1f", "running": True, "planned": False,
             "start": datetime.date(2026, 4, 16), "end": datetime.date(2026, 5, 28), "state": "ROLLING"}]
    payload = ec.to_payload(bars, [], CFG, today=TODAY)
    assert payload["rows"][0]["labelInBar"] is False
    rows, _, merges = sp.build_grid(payload)
    assert [m for m in merges if m[0] == 2] == []


def test_unverified_rows_show_as_note_rows(payload):
    note = next(r for r in payload["rows"] if r["kind"] == "note")
    assert note["status"] == "UNKNOWN"


def test_calendar_requests_merge_after_values_and_add_year_dividers(payload):
    kinds = [next(iter(r)) for r in sp.calendar_requests(7, payload)]
    assert kinds.index("mergeCells") > kinds.index("updateCells")
    assert kinds.count("mergeCells") >= 5


def test_ticket_cells_link_each_key_and_flag_missing_tickets():
    reqs = sp.status_requests(3, STATUS)
    rows = next(r["updateCells"]["rows"] for r in reqs if "updateCells" in r)
    linked = rows[1]["values"][5]
    uris = [run["format"]["link"]["uri"] for run in linked["textFormatRuns"] if "link" in run["format"]]
    assert uris == ["https://apollopde.atlassian.net/browse/INFRA-1528",
                    "https://apollopde.atlassian.net/browse/INFRA-1958"]
    missing = rows[2]["values"][5]
    assert missing["userEnteredValue"]["stringValue"] == "NO TICKET"


def test_ticket_text_flags_only_eol_items_without_tickets():
    assert ec.ticket_text([], "EOL PASSED", True) == "NO TICKET"
    assert ec.ticket_text([], "SUPPORTED", True) == ""
    assert ec.ticket_text([], "EOL PASSED", False) == ""
    assert ec.ticket_text(["INFRA-1"], "EOL PASSED", True) == "INFRA-1"


def test_calendar_rows_carry_hover_notes_with_ticket_links():
    bars = [{"label": "Mongo 6.0", "color": "#13aa52", "running": True, "planned": False,
             "start": datetime.date(2022, 7, 19), "end": datetime.date(2025, 7, 31), "state": "EOL PASSED",
             "hover": ec.row_note("why", ["INFRA-1528"])}]
    payload = ec.to_payload(bars, [], CFG, today=TODAY)
    assert "https://apollopde.atlassian.net/browse/INFRA-1528" in payload["rows"][0]["hover"]
