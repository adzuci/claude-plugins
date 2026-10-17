from __future__ import annotations

import datetime

import pytest

pytest.importorskip("yaml")
pytest.importorskip("requests")

import eol_calendar as ec  # noqa: E402

TODAY = datetime.date(2026, 10, 14)


def test_column_index_is_months_from_chart_start():
    assert ec.column(2025, 1, start_year=2025) == 0
    assert ec.column(2026, 10, start_year=2025) == 21


def test_parse_date_accepts_iso_and_false():
    assert ec.parse_date("2026-10-01") == datetime.date(2026, 10, 1)
    assert ec.parse_date(False) is None
    assert ec.parse_date(None) is None


@pytest.mark.parametrize(
    "eol,running,expected",
    [
        (datetime.date(2026, 10, 1), True, "EOL PASSED"),
        (datetime.date(2027, 2, 1), True, "EOL < 6 MO"),
        (datetime.date(2028, 1, 1), True, "SUPPORTED"),
        (None, True, "NO EOL"),
        (datetime.date(2026, 10, 1), False, "n/a"),
    ],
)
def test_classify(eol, running, expected):
    assert ec.classify(eol, running, today=TODAY) == expected


def test_merge_prefers_manual_override_and_flags_drift():
    api = {"start": datetime.date(2025, 9, 30), "end": datetime.date(2026, 10, 1)}
    row = {"cycle": "1.34", "end": "2026-12-01"}
    merged, warnings = ec.merge_dates(row, api, "gke")
    assert merged["end"] == datetime.date(2026, 12, 1)
    assert merged["start"] == datetime.date(2025, 9, 30)
    assert len(warnings) == 1 and "gke 1.34" in warnings[0]


def test_merge_without_api_requires_manual_dates():
    with pytest.raises(ValueError, match="missing manual start, end"):
        ec.merge_dates({"cycle": "x"}, None, "pritunl")


def test_merge_without_api_names_only_missing_manual_date():
    with pytest.raises(ValueError, match="missing manual end"):
        ec.merge_dates({"cycle": "x", "start": "2026-01-01"}, None, "pritunl")


def test_bar_clamps_to_chart_window_and_open_end():
    bar = ec.make_bar(
        start=datetime.date(2020, 1, 1), end=None, start_year=2025, end_year=2029
    )
    assert bar == (0, 59)


def test_bar_outside_window_is_none():
    assert (
        ec.make_bar(
            start=datetime.date(2019, 1, 1),
            end=datetime.date(2020, 1, 1),
            start_year=2025,
            end_year=2029,
        )
        is None
    )


def test_apps_script_keeps_status_versions_as_text():
    payload = ec.to_payload([], [], {"sheet_name": "S", "start_year": 2025, "end_year": 2026}, today=TODAY)
    assert 'setNumberFormat("@")' in ec.to_script(payload)
