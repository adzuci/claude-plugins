from __future__ import annotations

from datetime import date

import pytest

lib = pytest.importorskip("lib")


def test_classify_role_secondary_markers():
    assert lib.classify_role("DevOps Secondary") == "secondary"
    assert lib.classify_role("Platform Backup On-Call") == "secondary"
    assert lib.classify_role("DevOps 2nd") == "secondary"
    assert lib.classify_role("DevOps Primary") == "primary"
    # no marker defaults to primary
    assert lib.classify_role("DevOps On-Call") == "primary"


def test_classify_role_word_boundary_does_not_match_substring():
    # "2nd" must not match inside "22nd" (whole-word matching)
    assert lib.classify_role("Rotation 22nd cohort") == "primary"


def test_classify_team():
    assert lib.classify_team("SRE Primary") == "devops"
    assert lib.classify_team("Platform Secondary") == "platform"
    assert lib.classify_team("Growth Pod") is None


def test_classify_team_earliest_marker_wins():
    # "infra" is a devops marker, but the leading "Platform" should win
    assert lib.classify_team("Platform Infra Primary") == "platform"
    # and the reverse: devops leads
    assert lib.classify_team("DevOps Infra Secondary") == "devops"


def test_resolve_schedules_picks_team_and_role():
    schedules = [
        {"id": "P1", "name": "DevOps Primary"},
        {"id": "P2", "name": "DevOps Secondary"},
        {"id": "P3", "name": "Platform Primary"},
        {"id": "P4", "name": "Growth On-Call"},  # ignored
    ]
    resolved = lib.resolve_schedules(schedules, ["devops", "platform"])
    assert resolved[("devops", "primary")]["id"] == "P1"
    assert resolved[("devops", "secondary")]["id"] == "P2"
    assert resolved[("platform", "primary")]["id"] == "P3"
    assert ("growth", "primary") not in resolved


def test_resolve_schedules_first_match_wins():
    schedules = [
        {"id": "A", "name": "DevOps Primary"},
        {"id": "B", "name": "DevOps Primary (legacy)"},
    ]
    resolved = lib.resolve_schedules(schedules, ["devops"])
    assert resolved[("devops", "primary")]["id"] == "A"


def test_resolve_schedules_invokes_on_collision():
    schedules = [
        {"id": "A", "name": "DevOps Primary"},
        {"id": "B", "name": "DevOps Primary (legacy)"},
    ]
    collisions = []
    resolved = lib.resolve_schedules(
        schedules, ["devops"], on_collision=lambda key, kept, dropped: collisions.append((key, kept["id"], dropped["id"]))
    )
    assert resolved[("devops", "primary")]["id"] == "A"
    assert collisions == [(("devops", "primary"), "A", "B")]


def test_window_bounds_and_days():
    start = date(2026, 6, 1)
    s, e = lib.window_bounds(start, 2)
    assert s == start
    assert e == date(2026, 6, 15)
    days = lib.days_in_window(s, e)
    assert len(days) == 14
    assert days[0] == start
    assert days[-1] == date(2026, 6, 14)


def test_window_bounds_rejects_zero_weeks():
    with pytest.raises(ValueError):
        lib.window_bounds(date(2026, 6, 1), 0)


def test_iso_z_uses_z_suffix_not_offset():
    ts = lib.iso_z(date(2026, 6, 1))
    assert ts == "2026-06-01T00:00:00Z"
    assert "+00:00" not in ts
    parsed = lib.parse_iso(ts)
    assert parsed.year == 2026 and parsed.tzinfo is not None


def test_pd_rest_get_uses_runner_and_parses():
    calls = []

    def fake_runner(argv):
        calls.append(list(argv))
        return '{"schedules": [{"id": "P1"}]}'

    out = lib.pd_rest_get("/schedules?limit=100", runner=fake_runner)
    assert out["schedules"][0]["id"] == "P1"
    assert calls[0] == ["pd", "rest:get", "-e", "/schedules?limit=100"]


def test_loads_empty_is_empty_dict():
    assert lib._loads("") == {}
    assert lib._loads("   ") == {}


def test_loads_bad_json_raises_pderror():
    with pytest.raises(lib.PdError):
        lib._loads("{not json")
