from __future__ import annotations

from datetime import date

import pytest

sched = pytest.importorskip("oncall_schedule")


def test_oncall_endpoint_encodes_window():
    ep = sched.oncall_endpoint("PSCHED1", date(2026, 6, 1), date(2026, 6, 15))
    assert ep.startswith("/oncalls?")
    assert "schedule_ids[]=PSCHED1" in ep
    # iso_z emits a Z suffix (not %2B00%3A00); ':' is percent-encoded to %3A
    assert "since=2026-06-01T00%3A00%3A00Z" in ep
    assert "until=2026-06-15T00%3A00%3A00Z" in ep
    assert "%2B00%3A00" not in ep


def test_assignment_for_day_matches_interval():
    oncalls = [
        {
            "start": "2026-06-01T00:00:00Z",
            "end": "2026-06-08T00:00:00Z",
            "user": {"summary": "Alice"},
        },
        {
            "start": "2026-06-08T00:00:00Z",
            "end": "2026-06-15T00:00:00Z",
            "user": {"summary": "Bob"},
        },
    ]
    assert sched.assignment_for_day(oncalls, date(2026, 6, 3)) == "Alice"
    assert sched.assignment_for_day(oncalls, date(2026, 6, 10)) == "Bob"
    assert sched.assignment_for_day(oncalls, date(2026, 5, 1)) == "—"


def test_assignment_for_day_null_bounds_always_on():
    oncalls = [{"start": None, "end": None, "user": {"summary": "Carol"}}]
    assert sched.assignment_for_day(oncalls, date(2026, 6, 3)) == "Carol"


def test_render_grid_shape():
    days = [date(2026, 6, 1), date(2026, 6, 2)]
    columns = [("devops", "primary"), ("platform", "primary")]
    assignments = {
        ("devops", "primary"): [
            {"start": None, "end": None, "user": {"summary": "Alice"}}
        ],
        ("platform", "primary"): [
            {"start": None, "end": None, "user": {"summary": "Bob"}}
        ],
    }
    grid = sched.render_grid(days, columns, assignments)
    lines = grid.splitlines()
    # header + separator + 2 day rows
    assert len(lines) == 4
    assert "devops primary" in lines[0]
    assert "Alice" in grid and "Bob" in grid
    assert "2026-06-01" in grid


def test_parse_args_defaults():
    args = sched.parse_args([])
    assert args.weeks == 2
    assert args.teams == "devops,platform"
