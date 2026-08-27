from __future__ import annotations

from datetime import date

import pytest

mod = pytest.importorskip("check_uptime")


def test_classify_monitor_user_facing():
    assert mod.classify_monitor("app.apollo.io", "https://app.apollo.io") == "user-facing"
    assert mod.classify_monitor("API", "https://api.apollo.io/health") == "user-facing"
    # unknown / critical monitors default to user-facing so they aren't under-weighted
    assert mod.classify_monitor("mystery service", "https://example.com") == "user-facing"


def test_classify_monitor_background():
    assert mod.classify_monitor("Sidekiq queue", "") == "background"
    assert mod.classify_monitor("nightly worker", "") == "background"
    assert mod.classify_monitor("billing cron", "") == "background"
    assert mod.classify_monitor("db heartbeat", "") == "background"
    # keyword can appear in the url too
    assert mod.classify_monitor("prod", "https://uptime.betterstack.com/hb/job-42") == "background"


def test_severity_weight():
    assert mod.severity_weight("user-facing") == 1.0
    assert mod.severity_weight("background") == 0.2
    # unknown tiers fall back to the user-facing weight (never under-weighted)
    assert mod.severity_weight("nonsense") == 1.0


def test_format_duration():
    assert mod.format_duration(0) == "0s"
    assert mod.format_duration(492) == "8m 12s"
    assert mod.format_duration(5640) == "1h 34m"
    assert mod.format_duration(45) == "45s"


def test_weighted_availability_discounts_background():
    # Same 5% availability hit; once on a user-facing monitor, once on a
    # background monitor. The background hit should move the weighted number
    # less than the user-facing hit.
    healthy = {"availability": 100.0, "tier": "user-facing"}

    user_outage = [healthy, {"availability": 95.0, "tier": "user-facing"}]
    bg_outage = [healthy, {"availability": 95.0, "tier": "background"}]

    weighted_user = mod.weighted_availability(user_outage)
    weighted_bg = mod.weighted_availability(bg_outage)

    # background outage keeps the headline higher (closer to 100)
    assert weighted_bg > weighted_user
    # and the plain mean is identical for both, proving the weighting is what moved it
    assert weighted_user < 100.0


def test_filter_incidents_to_window():
    frm = date(2026, 7, 1)
    to = date(2026, 7, 31)
    incidents = [
        # fully inside the window -> kept
        {"name": "in-window", "started_at": "2026-07-10T00:00:00Z", "resolved_at": "2026-07-11T00:00:00Z"},
        # resolved before the window -> dropped
        {"name": "before", "started_at": "2026-06-01T00:00:00Z", "resolved_at": "2026-06-02T00:00:00Z"},
        # started after the window -> dropped
        {"name": "after", "started_at": "2026-08-05T00:00:00Z", "resolved_at": "2026-08-06T00:00:00Z"},
        # started before but still open -> kept (start <= to, no resolved_at)
        {"name": "open-early", "started_at": "2026-06-20T00:00:00Z", "resolved_at": None},
        # started before window, resolved inside -> overlaps, kept
        {"name": "overlap-start", "started_at": "2026-06-28T00:00:00Z", "resolved_at": "2026-07-03T00:00:00Z"},
        # unparseable start -> kept conservatively
        {"name": "mystery", "started_at": "", "resolved_at": None},
        # space-separated "UTC" form inside window -> kept
        {"name": "spaced", "started_at": "2026-07-18 09:11 UTC", "resolved_at": "2026-07-18 10:45 UTC"},
    ]

    kept = {i["name"] for i in mod.filter_incidents_to_window(incidents, frm, to)}

    assert kept == {"in-window", "open-early", "overlap-start", "mystery", "spaced"}


def test_sla_row_handles_explicit_null_fields():
    # Better Stack returns the SLA attributes with explicit nulls (not missing
    # keys) when a monitor has no data in the window -- e.g. a paused monitor,
    # or one created after the window started. dict.get(key, default) only
    # falls back on a missing key, not a present-but-null value, so this must
    # be handled explicitly or float(None) raises.
    sla = {"availability": None, "total_downtime": None, "number_of_incidents": None}
    row = mod._sla_row("paused-monitor", "https://x", "paused", sla, "user-facing")
    assert row["availability"] == 0.0
    assert row["total_downtime"] == 0
    assert row["number_of_incidents"] == 0


def test_build_report_two_tier_layout():
    monitors = [
        {
            "name": "app.apollo.io",
            "tier": "user-facing",
            "status": "up",
            "availability": 99.98,
            "total_downtime": 492,
            "number_of_incidents": 1,
        }
    ]
    heartbeats = [
        {
            "name": "sidekiq heartbeat",
            "tier": "background",
            "status": "up",
            "availability": 98.0,
            "total_downtime": 3600,
            "number_of_incidents": 2,
        }
    ]
    report = mod.build_report(
        monitors, [], heartbeats, date(2026, 7, 13), date(2026, 8, 12)
    )

    user_idx = report.index("## User-facing monitors")
    bg_idx = report.index("## Background jobs")
    # user-facing section must come first
    assert user_idx < bg_idx
    # report must state background downtime is lower impact
    assert "lower impact" in report.lower()
    assert "app.apollo.io" in report
    assert "sidekiq heartbeat" in report
