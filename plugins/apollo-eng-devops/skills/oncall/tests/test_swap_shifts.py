from __future__ import annotations

import pytest

swap = pytest.importorskip("swap_shifts")
lib = pytest.importorskip("lib")


def _dt(s):
    return lib.parse_iso(s)


def test_localize_window_exclusive_end_in_tz():
    start, end = swap.localize_window("2026-06-10", "2026-06-14", "America/Los_Angeles")
    # midnight Pacific = 07:00 UTC
    assert start.isoformat() == "2026-06-10T00:00:00-07:00"
    # exclusive end is the 15th at midnight (all of the 14th covered)
    assert end.isoformat() == "2026-06-15T00:00:00-07:00"


def test_localize_window_single_day_default():
    start, end = swap.localize_window("2026-06-10", None, "UTC")
    assert start.isoformat() == "2026-06-10T00:00:00+00:00"
    assert end.isoformat() == "2026-06-11T00:00:00+00:00"


def test_localize_window_rejects_reversed_range():
    with pytest.raises(ValueError):
        swap.localize_window("2026-06-14", "2026-06-10", "UTC")


def test_clamp_overlap_full_partial_none():
    win_s, win_e = _dt("2026-06-10T00:00:00Z"), _dt("2026-06-15T00:00:00Z")
    # fully inside
    assert swap.clamp_overlap(_dt("2026-06-11T00:00:00Z"), _dt("2026-06-12T00:00:00Z"), win_s, win_e) == (
        _dt("2026-06-11T00:00:00Z"),
        _dt("2026-06-12T00:00:00Z"),
    )
    # partial: shift starts before PTO, ends inside → clamp start to window
    assert swap.clamp_overlap(_dt("2026-06-08T00:00:00Z"), _dt("2026-06-11T00:00:00Z"), win_s, win_e) == (
        win_s,
        _dt("2026-06-11T00:00:00Z"),
    )
    # disjoint
    assert swap.clamp_overlap(_dt("2026-06-01T00:00:00Z"), _dt("2026-06-02T00:00:00Z"), win_s, win_e) is None
    # touching boundary (end == win_start) is not an overlap
    assert swap.clamp_overlap(_dt("2026-06-09T00:00:00Z"), _dt("2026-06-10T00:00:00Z"), win_s, win_e) is None


def test_overrides_from_oncalls_filters_and_clamps():
    win_s, win_e = _dt("2026-06-10T00:00:00Z"), _dt("2026-06-15T00:00:00Z")
    oncalls = [
        {  # me, partial overlap → clamped to window start
            "user": {"id": "ME", "summary": "Adam"},
            "schedule": {"id": "SCH1", "summary": "DevOps Primary"},
            "start": "2026-06-08T00:00:00Z",
            "end": "2026-06-12T00:00:00Z",
        },
        {  # someone else → ignored
            "user": {"id": "OTHER", "summary": "Bob"},
            "schedule": {"id": "SCH1", "summary": "DevOps Primary"},
            "start": "2026-06-12T00:00:00Z",
            "end": "2026-06-14T00:00:00Z",
        },
        {  # me but disjoint → ignored
            "user": {"id": "ME"},
            "schedule": {"id": "SCH2", "summary": "DevOps Secondary"},
            "start": "2026-06-01T00:00:00Z",
            "end": "2026-06-02T00:00:00Z",
        },
    ]
    out = swap.overrides_from_oncalls(oncalls, win_s, win_e, cover_id="PRIYA", me_id="ME")
    assert len(out) == 1
    assert out[0]["schedule_id"] == "SCH1"
    assert out[0]["cover_id"] == "PRIYA"
    assert out[0]["start"] == "2026-06-10T00:00:00+00:00"  # clamped
    assert out[0]["end"] == "2026-06-12T00:00:00+00:00"


def test_overrides_skips_unbounded_entries():
    win_s, win_e = _dt("2026-06-10T00:00:00Z"), _dt("2026-06-15T00:00:00Z")
    oncalls = [{"user": {"id": "ME"}, "schedule": {"id": "S"}, "start": None, "end": None}]
    assert swap.overrides_from_oncalls(oncalls, win_s, win_e, "C", "ME") == []


def test_overrides_skips_entries_without_schedule_id():
    # a missing schedule id would otherwise produce /schedules/None/overrides
    win_s, win_e = _dt("2026-06-10T00:00:00Z"), _dt("2026-06-15T00:00:00Z")
    oncalls = [
        {
            "user": {"id": "ME"},
            "schedule": {"summary": "Mystery (no id)"},
            "start": "2026-06-11T00:00:00Z",
            "end": "2026-06-12T00:00:00Z",
        }
    ]
    assert swap.overrides_from_oncalls(oncalls, win_s, win_e, "C", "ME") == []


def test_render_preview_nothing_to_do():
    assert "Nothing to do" in swap.render_preview([], "UTC")


def test_render_preview_table():
    overrides = [
        {
            "schedule_id": "S1",
            "schedule_name": "DevOps Primary",
            "current_user": "Adam",
            "cover_id": "PRIYA",
            "start": "2026-06-10T00:00:00+00:00",
            "end": "2026-06-12T00:00:00+00:00",
        }
    ]
    out = swap.render_preview(overrides, "America/Los_Angeles")
    assert "America/Los_Angeles" in out
    assert "DevOps Primary" in out
    assert "| 1 |" in out


def test_render_preview_shows_cover_name_and_id():
    overrides = [
        {
            "schedule_id": "S1",
            "schedule_name": "DevOps Primary",
            "current_user": "Adam",
            "cover_id": "PRIYA",
            "cover_name": "Priya R",
            "start": "2026-06-10T00:00:00+00:00",
            "end": "2026-06-12T00:00:00+00:00",
        }
    ]
    out = swap.render_preview(overrides, "UTC")
    assert "Priya R (PRIYA)" in out  # human-readable name plus the verbatim id


def test_overrides_carry_cover_name_with_id_fallback():
    win_s, win_e = _dt("2026-06-10T00:00:00Z"), _dt("2026-06-15T00:00:00Z")
    oncalls = [
        {
            "user": {"id": "ME"},
            "schedule": {"id": "S1", "summary": "DevOps Primary"},
            "start": "2026-06-11T00:00:00Z",
            "end": "2026-06-12T00:00:00Z",
        }
    ]
    # name supplied
    out = swap.overrides_from_oncalls(oncalls, win_s, win_e, "PRIYA", "ME", cover_name="Priya R")
    assert out[0]["cover_name"] == "Priya R" and out[0]["cover_id"] == "PRIYA"
    # name omitted → falls back to id
    out2 = swap.overrides_from_oncalls(oncalls, win_s, win_e, "PRIYA", "ME")
    assert out2[0]["cover_name"] == "PRIYA"


def test_main_dry_run_makes_no_post(monkeypatch, capsys):
    # --me is passed, so /users/me is NOT called; the script fetches /oncalls and
    # resolves the cover user's name via /users/<cover-id>.
    def fake_get(endpoint, runner=None):
        if endpoint == "/users/me":
            return {"user": {"id": "ME"}}
        if endpoint.startswith("/oncalls"):
            return {
                "oncalls": [
                    {
                        "user": {"id": "ME", "summary": "Adam"},
                        "schedule": {"id": "SCH1", "summary": "DevOps Primary"},
                        "start": "2026-06-10T00:00:00+00:00",
                        "end": "2026-06-12T00:00:00+00:00",
                    }
                ]
            }
        return {}

    posted = []
    monkeypatch.setattr(swap.lib, "pd_rest_get", fake_get)
    monkeypatch.setattr(swap.lib, "pd_rest_post", lambda *a, **k: posted.append(a) or {"override": {"id": "O1"}})

    rc = swap.main(["--from", "2026-06-10", "--to", "2026-06-11", "--cover", "PRIYA", "--me", "ME", "--tz", "UTC"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "DRY RUN" in out
    assert posted == []  # nothing written without --apply
