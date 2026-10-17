from __future__ import annotations

import pytest


deps = pytest.importorskip("check_dependencies")


def test_collect_statuses_reports_glean(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(deps.shutil, "which", lambda name: "/usr/local/bin/glean" if name == "glean" else None)

    statuses = deps.collect_statuses()

    assert len(statuses) == 1
    assert statuses[0].name == "glean"
    assert statuses[0].status == "available"
    assert statuses[0].detail == "/usr/local/bin/glean"


def test_collect_statuses_gives_setup_nudge_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(deps.shutil, "which", lambda _name: None)

    status = deps.collect_statuses()[0]

    assert status.status == "missing"
    assert "glean auth login" in status.nudge
