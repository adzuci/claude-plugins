from __future__ import annotations

import pytest

override = pytest.importorskip("propose_override")


def test_override_endpoint():
    assert override.override_endpoint("PSCHED1") == "/schedules/PSCHED1/overrides"


def test_override_body_shape():
    body = override.override_body("PUSER1", "2026-06-10T09:00:00Z", "2026-06-10T17:00:00Z")
    assert body["override"]["user"]["id"] == "PUSER1"
    assert body["override"]["user"]["type"] == "user_reference"
    assert body["override"]["start"] == "2026-06-10T09:00:00Z"


def test_dry_run_is_default_and_makes_no_call(capsys):
    rc = override.main(
        [
            "--schedule",
            "PSCHED1",
            "--user",
            "PUSER1",
            "--start",
            "2026-06-10T09:00:00Z",
            "--end",
            "2026-06-10T17:00:00Z",
        ]
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "DRY RUN" in out
    assert "POST /schedules/PSCHED1/overrides" in out


def test_apply_calls_post(monkeypatch):
    calls = {}

    def fake_post(endpoint, body, runner=None):
        calls["endpoint"] = endpoint
        calls["body"] = body
        return {"override": {"id": "PO1"}}

    monkeypatch.setattr(override.lib, "pd_rest_post", fake_post)
    rc = override.main(
        [
            "--schedule",
            "PSCHED1",
            "--user",
            "PUSER1",
            "--start",
            "2026-06-10T09:00:00Z",
            "--end",
            "2026-06-10T17:00:00Z",
            "--apply",
        ]
    )
    assert rc == 0
    assert calls["endpoint"] == "/schedules/PSCHED1/overrides"
    assert calls["body"]["override"]["user"]["id"] == "PUSER1"
