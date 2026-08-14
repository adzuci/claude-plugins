from __future__ import annotations

import json
from datetime import date

import pytest

gvr = pytest.importorskip("gke_versions_report")


# --- fixtures --------------------------------------------------------------------------

EOL_RESULT = {
    "releases": [
        {"name": "1.36", "eolFrom": "2027-06-28"},
        {"name": "1.35", "eolFrom": "2027-02-28"},
        {"name": "1.34", "eolFrom": "2026-10-27"},
        {"name": "1.33", "eolFrom": "2026-06-28"},
        {"name": "1.30", "eolFrom": "2025-06-28"},
    ]
}

TODAY = date(2026, 7, 30)


def _eol_by_minor():
    return gvr.eol_lookup(EOL_RESULT)


# --- minor_version / eol_lookup -----------------------------------------------------


def test_minor_version_strips_patch_and_build_suffix():
    assert gvr.minor_version("1.34.9-gke.1065000") == "1.34"
    assert gvr.minor_version("1.35.5-gke.1057002") == "1.35"


def test_eol_lookup_keys_by_minor_name():
    lookup = _eol_by_minor()
    assert lookup["1.34"]["eolFrom"] == "2026-10-27"
    assert "1.99" not in lookup


# --- flag_for_version ----------------------------------------------------------------


def test_flag_for_version_past_eol():
    flag, eol_date = gvr.flag_for_version("1.30.5-gke.100", _eol_by_minor(), TODAY)
    assert flag == gvr.PAST_EOL
    assert eol_date == "2025-06-28"


def test_flag_for_version_eol_soon_boundary():
    # 1.33 EOLs 2026-06-28; today is 2026-07-30 -> already past, sanity-check ordering
    # Use 1.34 (EOLs 2026-10-27) to exercise the "soon" window relative to TODAY.
    soon_today = date(2026, 8, 29)  # exactly 59 days before 1.34's eolFrom
    flag, _ = gvr.flag_for_version("1.34.9-gke.1065000", _eol_by_minor(), soon_today)
    assert flag == gvr.EOL_SOON

    just_outside = date(2026, 8, 28)  # 60 days is the window edge; 61 days out
    flag, _ = gvr.flag_for_version("1.34.9-gke.1065000", _eol_by_minor(), just_outside)
    assert flag == gvr.EOL_SOON  # exactly 60 days out is still "soon" (inclusive)

    well_outside = date(2026, 6, 1)
    flag, _ = gvr.flag_for_version("1.34.9-gke.1065000", _eol_by_minor(), well_outside)
    assert flag is None


def test_flag_for_version_supported():
    flag, eol_date = gvr.flag_for_version("1.36.3-gke.100", _eol_by_minor(), TODAY)
    assert flag is None
    assert eol_date == "2027-06-28"


def test_flag_for_version_unknown_minor_returns_none():
    flag, eol_date = gvr.flag_for_version("1.99.0-gke.1", _eol_by_minor(), TODAY)
    assert flag is None
    assert eol_date is None


# --- list_clusters -------------------------------------------------------------------


def test_list_clusters_parses_gcloud_json():
    canned = json.dumps(
        [
            {
                "name": "staging",
                "zone": "us-central1-c",
                "location": "us-central1-c",
                "status": "RUNNING",
                "currentMasterVersion": "1.34.9-gke.1065000",
                "currentNodeVersion": "1.34.8-gke.1278000 *",
            }
        ]
    )

    def fake_runner(argv):
        assert argv[:4] == ["gcloud", "container", "clusters", "list"]
        return canned

    rows = gvr.list_clusters("stage-23704", runner=fake_runner)
    assert rows == [
        {
            "project": "stage-23704",
            "name": "staging",
            "location": "us-central1-c",
            "master_version": "1.34.9-gke.1065000",
            "node_version": "1.34.8-gke.1278000 *",
            "status": "RUNNING",
        }
    ]


def test_list_clusters_treats_gke_api_disabled_as_empty():
    def fake_runner(argv):
        raise gvr.GkeReportError(
            "ResponseError: code=403, message=Kubernetes Engine API has not been used "
            "in project foo before or it is disabled."
        )

    assert gvr.list_clusters("foo", runner=fake_runner) == []


def test_list_clusters_reraises_other_errors():
    def fake_runner(argv):
        raise gvr.GkeReportError("some other failure")

    with pytest.raises(gvr.GkeReportError):
        gvr.list_clusters("foo", runner=fake_runner)


# --- render_report ---------------------------------------------------------------------


def _row(name, flag, eol_date=None):
    return {
        "project": "p",
        "name": name,
        "location": "us-central1-c",
        "master_version": "1.34.9-gke.1065000",
        "node_version": "1.34.9-gke.1065000",
        "status": "RUNNING",
        "flag": flag,
        "eol_date": eol_date,
    }


def test_render_report_sorts_flagged_rows_first():
    rows = [_row("ok", None), _row("soon", gvr.EOL_SOON), _row("past", gvr.PAST_EOL)]
    report = gvr.render_report(rows)
    lines = [line for line in report.splitlines() if line.startswith("| p |")]
    names_in_order = [line.split("|")[2].strip() for line in lines]
    assert names_in_order == ["past", "soon", "ok"]


def test_render_report_includes_flag_labels():
    report = gvr.render_report([_row("past", gvr.PAST_EOL, "2025-06-28")])
    assert "PAST EOL" in report
    assert "2025-06-28" in report


# --- run_kubent --------------------------------------------------------------------------


def test_run_kubent_happy_path():
    calls = []

    def fake_runner(argv):
        calls.append(argv)
        if argv[0] == "gcloud":
            return ""
        assert argv[:2] == ["kubent", "--context"]
        return json.dumps({"1.16": []})

    result = gvr.run_kubent("proj", "staging", "us-central1-c", runner=fake_runner)
    assert "1.16" in result
    assert calls[0][:5] == [
        "gcloud",
        "container",
        "clusters",
        "get-credentials",
        "staging",
    ]
    assert calls[1][1] == "--context"
    assert calls[1][2] == "gke_proj_us-central1-c_staging"


def test_run_kubent_missing_binary_returns_install_hint():
    def fake_runner(argv):
        if argv[0] == "gcloud":
            return ""
        raise gvr.GkeReportError("`kubent` not found on PATH.")

    result = gvr.run_kubent("proj", "staging", "us-central1-c", runner=fake_runner)
    assert "brew install kubent" in result


def test_run_kubent_get_credentials_failure_short_circuits():
    def fake_runner(argv):
        raise gvr.GkeReportError("permission denied")

    result = gvr.run_kubent("proj", "staging", "us-central1-c", runner=fake_runner)
    assert "Could not get credentials" in result


# --- fetch_eol_data caching ------------------------------------------------------------


def test_fetch_eol_data_uses_cache_within_ttl(tmp_path):
    cache_file = tmp_path / "eol-cache.json"
    cache_file.write_text(json.dumps({"_fetched_at": 1000.0, "result": EOL_RESULT}))

    def fail_fetcher(url):
        raise AssertionError("should not hit the network when cache is fresh")

    result = gvr.fetch_eol_data(
        fetcher=fail_fetcher, cache_file=cache_file, ttl_seconds=86400, now=1000.0 + 60
    )
    assert result == EOL_RESULT


def test_fetch_eol_data_refetches_when_cache_stale(tmp_path):
    cache_file = tmp_path / "eol-cache.json"
    cache_file.write_text(json.dumps({"_fetched_at": 0.0, "result": {"releases": []}}))

    def fetcher(url):
        return json.dumps({"result": EOL_RESULT}).encode()

    result = gvr.fetch_eol_data(fetcher=fetcher, cache_file=cache_file, ttl_seconds=10, now=1000.0)
    assert result == EOL_RESULT
    assert json.loads(cache_file.read_text())["result"] == EOL_RESULT
