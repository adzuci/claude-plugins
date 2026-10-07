from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sqr = pytest.importorskip("slow_query_report")

FIXTURE = Path(__file__).parent / "fixtures" / "incident-2026-08-13.json"
Z = timezone.utc


def at(hour, minute, second=0):
    return datetime(2026, 8, 13, hour, minute, second, tzinfo=Z)


def event(shard, sampled, secs, signature="query:contacts:account_id", **ctx):
    context = {"opid": "{}:{}".format(shard, abs(hash(sampled)) % 10**6), "secs_running": secs, "signature": signature}
    context.update(ctx)
    return {"dateCreated": sampled.strftime("%Y-%m-%dT%H:%M:%SZ"), "context": context}


# --------------------------------------------------------------------------- parsing


def test_parse_shard_splits_on_first_colon():
    assert sqr.parse_shard("contacts-16:-819763575") == "contacts-16"
    assert sqr.parse_shard("shard0000:12345") == "shard0000"


def test_parse_shard_returns_none_without_prefix():
    assert sqr.parse_shard("819763575") is None
    assert sqr.parse_shard("") is None
    assert sqr.parse_shard(None) is None


def test_parse_ts_handles_z_and_offset_and_garbage():
    assert sqr.parse_ts("2026-08-13T14:18:08Z") == at(14, 18, 8)
    assert sqr.parse_ts("2026-08-13T14:18:08+00:00") == at(14, 18, 8)
    assert sqr.parse_ts("not a date") is None
    assert sqr.parse_ts(None) is None


def test_parse_ts_assumes_utc_when_naive():
    assert sqr.parse_ts("2026-08-13T14:18:08").tzinfo is timezone.utc


def test_filter_keys_flattens_boolean_operators():
    assert sqr.filter_keys({"account_id": {"$in": ["a"]}}) == ["account_id"]
    assert sqr.filter_keys({"$and": [{"team_id": 1}, {"deleted": False}]}) == ["team_id", "deleted"]
    assert sqr.filter_keys('{"account_id": 1}') == ["account_id"]
    assert sqr.filter_keys("not json") == []


def test_filter_keys_dedupes():
    assert sqr.filter_keys({"$or": [{"a": 1}, {"a": 2}, {"b": 3}]}) == ["a", "b"]


def test_filter_keys_values_reads_in_eq_and_bare():
    assert sqr.filter_keys_values({"account_id": {"$in": ["x", "y"]}}, "account_id") == ["x", "y"]
    assert sqr.filter_keys_values({"account_id": {"$eq": "x"}}, "account_id") == ["x"]
    assert sqr.filter_keys_values({"account_id": "x"}, "account_id") == ["x"]
    assert sqr.filter_keys_values({"team_id": "x"}, "account_id") == []


def test_max_in_size():
    assert sqr.max_in_size({"a": {"$in": list(range(30))}}) == 30
    assert sqr.max_in_size({"a": 1}) == 0
    assert sqr.max_in_size("garbage") == 0


def test_op_interval_backdates_start_by_runtime():
    start, end = sqr.op_interval(event("contacts-1", at(14, 30), 60.0))
    assert end == at(14, 30)
    assert start == at(14, 29)


# --------------------------------------------------------------------------- origin


def test_classify_origin_user_request_high_when_two_signals_agree():
    origin, confidence, evidence = sqr.classify_origin(
        {"source": "Api::V1::AccountsController/show", "server_name": "web-prod-puma-1"}
    )
    assert origin == "user-request"
    assert confidence == "high"
    assert len(evidence) == 2


def test_classify_origin_manual_console_beats_a_lone_signal():
    origin, confidence, _ = sqr.classify_origin({"source": "rails runner scripts/backfill.rb"})
    assert origin == "manual-console"
    assert confidence == "medium"


def test_classify_origin_rake_and_console_variants():
    for value in ("rake contacts:reindex", "bin/rails console", "Rails::Console", "mongosh"):
        origin, _, _ = sqr.classify_origin({"source": value})
        assert origin == "manual-console", value


def test_classify_origin_background_and_scheduled():
    assert sqr.classify_origin({"source": "ContactsExportWorker"})[0] == "background-job"
    assert sqr.classify_origin({"source": "Clockwork::NightlyRollup"})[0] == "scheduled"


def test_classify_origin_conflicting_signals_drop_confidence():
    origin, confidence, _ = sqr.classify_origin(
        {"source": "Api::V1::AccountsController/show", "server_name": "sidekiq-prod-3"}
    )
    assert origin == "user-request"  # `source` is the killer's own attribution and wins
    assert confidence == "low"


def test_classify_origin_unknown_when_nothing_matches():
    origin, confidence, evidence = sqr.classify_origin({"source": "???"})
    assert (origin, confidence, evidence) == ("unknown", "none", [])


def test_every_origin_has_a_plain_english_meaning():
    for name, _pattern in sqr.ORIGIN_PATTERNS:
        assert name in sqr.ORIGIN_MEANING
    assert "unknown" in sqr.ORIGIN_MEANING


# --------------------------------------------------------------------------- fan-out


def test_peak_concurrency_counts_distinct_shards_at_one_instant():
    intervals = [
        (at(14, 0), at(14, 1), "s1"),
        (at(14, 0, 30), at(14, 1, 30), "s2"),
        (at(14, 0, 40), at(14, 2), "s3"),
    ]
    count, when, shards = sqr.peak_concurrency(intervals)
    assert count == 3
    assert when == at(14, 0, 40)
    assert shards == ["s1", "s2", "s3"]


def test_peak_concurrency_ignores_same_shard_repeats():
    intervals = [(at(14, 0), at(14, 5), "s1"), (at(14, 1), at(14, 4), "s1")]
    assert sqr.peak_concurrency(intervals)[0] == 1


def test_peak_concurrency_sequential_ops_never_stack():
    intervals = [(at(14, 0), at(14, 1), "s1"), (at(14, 2), at(14, 3), "s2")]
    assert sqr.peak_concurrency(intervals)[0] == 1


def test_peak_concurrency_empty():
    assert sqr.peak_concurrency([]) == (0, None, [])


def test_fanout_proven_requires_time_overlap():
    events = [event("contacts-16", at(14, 1), 60.0), event("contacts-19", at(14, 1, 10), 60.0)]
    result = sqr.fanout_evidence(events)
    assert result["verdict"] == "proven"
    assert result["peak_concurrent_shards"] == 2
    assert "simultaneously" in result["basis"]


def test_fanout_only_likely_when_shards_never_overlap():
    events = [event("contacts-16", at(14, 1), 5.0), event("contacts-19", at(15, 1), 5.0)]
    result = sqr.fanout_evidence(events)
    assert result["verdict"] == "likely"
    assert "could be sequential" in result["basis"]


def test_fanout_single_shard():
    events = [event("contacts-16", at(14, 1), 5.0), event("contacts-16", at(14, 9), 5.0)]
    assert sqr.fanout_evidence(events)["verdict"] == "single-shard"


def test_fanout_unknown_without_opids():
    events = [{"dateCreated": "2026-08-13T14:00:00Z", "context": {"secs_running": 5}}]
    assert sqr.fanout_evidence(events)["verdict"] == "unknown"


def test_fanout_picks_the_dominant_signature():
    events = [
        event("contacts-16", at(14, 1), 60.0, signature="query:contacts:account_id"),
        event("contacts-19", at(14, 1), 60.0, signature="query:contacts:account_id"),
        event("contacts-27", at(14, 1), 60.0, signature="query:other:thing"),
    ]
    result = sqr.fanout_evidence(events)
    assert result["signature"] == "query:contacts:account_id"
    assert result["events_in_signature"] == 2


# --------------------------------------------------------------------------- pattern


PROVEN = {"verdict": "proven", "distinct_shards": 4}
SINGLE = {"verdict": "single-shard", "distinct_shards": 1}


def test_pattern_never_claims_scatter_gather_without_a_confirmed_shard_key():
    result = sqr.classify_pattern(PROVEN, ["account_id"], [], "unconfirmed")
    assert result["pattern"] == "multi-shard fan-out"
    assert result["confidence"] == "provisional"
    assert "scatter" not in result["pattern"]


def test_pattern_treats_assumed_shard_key_as_unconfirmed():
    result = sqr.classify_pattern(PROVEN, ["account_id"], ["team"], "assumed")
    assert result["confidence"] == "provisional"


def test_pattern_scatter_gather_when_confirmed_mismatch_and_proven_fanout():
    result = sqr.classify_pattern(PROVEN, ["account_id"], ["team"], "mongo-specialist")
    assert result["pattern"] == "scatter-gather"
    assert result["confidence"] == "high"


def test_pattern_scatter_gather_only_medium_when_fanout_merely_likely():
    result = sqr.classify_pattern({"verdict": "likely", "distinct_shards": 3}, ["account_id"], ["team"], "mongo-specialist")
    assert result["confidence"] == "medium"


def test_pattern_targeted_when_filter_covers_shard_key():
    result = sqr.classify_pattern(SINGLE, ["team", "account_id"], ["team"], "mongo-specialist")
    assert result["pattern"] == "targeted (large shard)"


def test_pattern_mismatch_without_observed_fanout():
    result = sqr.classify_pattern(SINGLE, ["account_id"], ["team"], "mongo-specialist")
    assert result["pattern"] == "shard-key mismatch (fan-out unobserved)"


def test_pattern_prose_never_leaks_a_python_list_repr():
    for result in (
        sqr.classify_pattern(PROVEN, ["account_id"], ["team"], "mongo-specialist"),
        sqr.classify_pattern(SINGLE, ["team", "account_id"], ["team"], "mongo-specialist"),
        sqr.classify_pattern(SINGLE, ["account_id"], ["team"], "mongo-specialist"),
    ):
        assert "['" not in result["why"], result["why"]


def test_pattern_indeterminate_when_nothing_is_known():
    result = sqr.classify_pattern({"verdict": "unknown", "distinct_shards": 0}, [], [], "unconfirmed")
    assert result["pattern"] == "indeterminate"


# --------------------------------------------------------------------------- deploys


DEPLOYS = [
    {"version": "app@2026.08.13-new", "dateFinished": "2026-08-13T14:00:00Z"},
    {"version": "app@2026.08.11-old", "dateFinished": "2026-08-11T16:40:00Z"},
]


def test_deploy_correlated_when_onset_follows_deploy_of_the_first_release():
    result = sqr.correlate_deploys("2026-08-13T14:18:08Z", DEPLOYS, "app@2026.08.13-new")
    assert result["verdict"] == "deploy-correlated"
    assert result["lag_minutes"] == pytest.approx(18.1, abs=0.2)
    assert result["nearest"]["version"] == "app@2026.08.13-new"


def test_deploy_pre_existing_when_issue_predates_the_nearest_deploy():
    result = sqr.correlate_deploys("2026-08-13T14:18:08Z", DEPLOYS, "app@2026.08.11-old")
    assert result["verdict"] == "pre-existing"
    assert "not a new regression" in result["note"]


def test_deploy_adjacent_when_release_provenance_unknown():
    result = sqr.correlate_deploys("2026-08-13T14:18:08Z", DEPLOYS, None)
    assert result["verdict"] == "deploy-adjacent"


def test_deploy_pre_existing_when_outside_the_window():
    result = sqr.correlate_deploys("2026-08-13T20:00:00Z", DEPLOYS, None)
    assert result["verdict"] == "pre-existing"
    assert "outside the 120-min window" in result["note"]


def test_deploy_no_data_and_no_deploy_before_onset():
    assert sqr.correlate_deploys("2026-08-13T14:18:08Z", [], None)["verdict"] == "no-deploy-data"
    assert sqr.correlate_deploys("2026-08-10T00:00:00Z", DEPLOYS, None)["verdict"] == "no-deploy-before-onset"


def test_deploy_splits_event_volume_across_the_boundary():
    events = [
        {"dateCreated": "2026-08-13T13:00:00Z"},
        {"dateCreated": "2026-08-13T14:30:00Z"},
        {"dateCreated": "2026-08-13T14:40:00Z"},
    ]
    result = sqr.correlate_deploys("2026-08-13T14:18:08Z", DEPLOYS, "app@2026.08.13-new", events=events)
    assert (result["events_before"], result["events_after"]) == (1, 2)


# --------------------------------------------------------------------------- severity


SCATTER = {"pattern": "scatter-gather", "confidence": "high", "why": ""}
TARGETED = {"pattern": "targeted (large shard)", "confidence": "high", "why": ""}


def test_bump_saturates_at_critical():
    assert sqr.bump("low") == "medium"
    assert sqr.bump("critical") == "critical"
    assert sqr.bump("low", 3) == "critical"


def test_severity_matrix_base_cases():
    assert sqr.propose_severity("fleet", "recurring", SCATTER, False, "pre-existing", "user-request")[0] == "high"
    assert sqr.propose_severity("single-account", "recurring", SCATTER, False, "pre-existing", "user-request")[0] == "medium"
    assert sqr.propose_severity("single-account", "one-window", SCATTER, False, "pre-existing", "user-request")[0] == "low"
    assert sqr.propose_severity("single-account", "one-window", TARGETED, False, "pre-existing", "user-request")[0] == "low"


def test_successful_kill_raises_severity_and_flags_integrity():
    severity, reasons, _ = sqr.propose_severity("single-account", "one-window", SCATTER, True, "pre-existing", "user-request")
    assert severity == "medium"
    assert any("data-integrity" in r for r in reasons)


def test_deploy_correlation_raises_severity():
    severity, reasons, _ = sqr.propose_severity(
        "single-account", "recurring", SCATTER, False, "deploy-correlated", "user-request"
    )
    assert severity == "high"
    assert any("revert" in r for r in reasons)


def test_manual_origin_floors_a_one_off_at_low():
    severity, reasons, _ = sqr.propose_severity(
        "single-account", "one-window", SCATTER, False, "pre-existing", "manual-console"
    )
    assert severity == "low"
    assert any("alert-tuning" in r for r in reasons)


def test_severity_is_provisional_when_pattern_is():
    provisional = {"pattern": "multi-shard fan-out", "confidence": "provisional", "why": ""}
    assert sqr.propose_severity("fleet", "recurring", provisional, False, "pre-existing", "user-request")[2] is True


# --------------------------------------------------------------------------- blast radius


def test_blast_radius_single_account_one_window():
    events = [
        event("s1", at(14, 0), 5.0, filter={"account_id": {"$in": ["acct-a"]}}),
        event("s1", at(14, 5), 5.0, filter={"account_id": {"$in": ["acct-a"]}}),
    ]
    result = sqr.blast_radius(events)
    assert (result["radius"], result["temporality"], result["distinct_accounts"]) == ("single-account", "one-window", 1)


def test_blast_radius_fleet_and_recurring():
    events = [
        event("s1", at(14, 0), 5.0, filter={"account_id": "a"}),
        event("s1", at(14, 5), 5.0, filter={"account_id": "b"}),
        {"dateCreated": "2026-08-14T09:00:00Z", "context": {"filter": {"account_id": "c"}}},
    ]
    result = sqr.blast_radius(events)
    assert result["radius"] == "fleet"
    assert result["temporality"] == "recurring"


# --------------------------------------------------------------------------- recommendations


def digest_for(**over):
    base = {
        "op": {"plan_summary": "IXSCAN { account_id: 1 }", "filter": {"account_id": {"$in": ["a"]}}, "filter_fields": ["account_id"]},
        "origin": {"origin": "user-request"},
        "pattern": {"pattern": "scatter-gather"},
        "shard_key": {"key": ["team"]},
        "blast": {"temporality": "one-window", "radius": "single-account"},
        "deploy": {"verdict": "pre-existing", "nearest": None},
    }
    for key, value in over.items():
        base[key] = {**base[key], **value} if isinstance(value, dict) else value
    return base


def test_recommendations_always_include_the_maxtimems_guardrail():
    recs = sqr.recommendations(digest_for())
    assert any("maxTimeMS" in r["action"] for r in recs)


def test_recommendations_lead_with_process_for_a_manual_op():
    recs = sqr.recommendations(digest_for(origin={"origin": "manual-console"}))
    assert recs[0]["tier"] == "process"
    assert any(r["tier"] == "alerting" for r in recs)


def test_recommendations_warn_against_another_index_on_an_ixscan_fanout():
    recs = sqr.recommendations(digest_for())
    index = [r for r in recs if r["tier"] == "index"]
    assert index and "Do NOT add another index" in index[0]["action"]


def test_recommendations_call_for_an_index_on_collscan():
    recs = sqr.recommendations(digest_for(op={"plan_summary": "COLLSCAN"}))
    assert any("create-mongo-index" in r["why"] or "create-mongo-index" in r["action"] for r in recs)


def test_recommendations_ask_to_confirm_shard_key_before_committing():
    recs = sqr.recommendations(digest_for(pattern={"pattern": "multi-shard fan-out"}))
    assert recs[0]["tier"] == "verify"


def test_recommendations_chunk_a_large_in_list():
    recs = sqr.recommendations(digest_for(op={"filter": {"account_id": {"$in": [str(i) for i in range(40)]}}}))
    assert any("$in" in r["action"] for r in recs)


def test_recommendations_add_architecture_tier_when_recurring():
    recs = sqr.recommendations(digest_for(blast={"temporality": "recurring", "radius": "fleet"}))
    assert any(r["tier"] == "architecture" for r in recs)


def test_recommendations_suggest_revert_when_deploy_correlated():
    recs = sqr.recommendations(
        digest_for(deploy={"verdict": "deploy-correlated", "nearest": {"version": "app@1"}})
    )
    assert any(r["tier"] == "regression" for r in recs)


def test_recommendations_are_ranked_contiguously():
    recs = sqr.recommendations(digest_for())
    assert [r["rank"] for r in recs] == list(range(1, len(recs) + 1))


# --------------------------------------------------------------------------- end to end


@pytest.fixture(scope="module")
def bundle():
    return json.loads(FIXTURE.read_text())


def test_fixture_is_labelled_as_reconstructed(bundle):
    assert bundle["meta"]["source"] != "live"
    assert "egress-blocked" in bundle["meta"]["notes"]


def test_digest_reproduces_the_documented_incident_values(bundle):
    d = sqr.build_digest(bundle)
    assert d["incident"]["event_count"] == 465
    assert d["op"]["collection"] == "contacts"
    assert d["op"]["shard"] == "contacts-16"
    assert d["op"]["secs_running"] == pytest.approx(71.61684)
    assert d["fanout"]["shards"] == ["contacts-16", "contacts-19", "contacts-27", "contacts-28"]
    assert d["op"]["plan_summary"] == "IXSCAN { account_id: 1 }"


def test_digest_defaults_to_provisional_without_a_shard_key(bundle):
    d = sqr.build_digest(bundle)
    assert d["pattern"]["pattern"] == "multi-shard fan-out"
    assert d["severity"]["provisional"] is True


def test_digest_upgrades_to_scatter_gather_once_the_shard_key_is_confirmed(bundle):
    d = sqr.build_digest(bundle, ["team"], "mongo-specialist")
    assert d["pattern"]["pattern"] == "scatter-gather"
    assert d["pattern"]["confidence"] == "high"
    assert d["severity"]["provisional"] is False


def test_digest_attributes_origin_and_deploy(bundle):
    d = sqr.build_digest(bundle)
    assert d["origin"]["origin"] == "user-request"
    assert d["origin"]["confidence"] == "high"
    assert d["deploy"]["verdict"] == "pre-existing"


def test_digest_json_is_serialisable_and_drops_intervals(bundle):
    d = sqr.build_digest(bundle)
    payload = {k: v for k, v in d.items() if k != "_intervals"}
    assert json.loads(json.dumps(payload, default=str))["fanout"]["verdict"] == "proven"


def test_triage_markdown_stays_small_and_deep_adds_the_ticket(bundle):
    d = sqr.build_digest(bundle, ["team"], "mongo-specialist")
    triage = sqr.render_markdown(d, "triage")
    deep = sqr.render_markdown(d, "deep")
    assert len(triage.splitlines()) < 40, "triage mode must stay cheap to read"
    assert len(deep) > len(triage)
    assert "Drafted ticket" in deep and "Drafted ticket" not in triage
    assert "top 3" in triage


def test_markdown_surfaces_the_non_live_data_source(bundle):
    d = sqr.build_digest(bundle)
    assert "reconstructed fixture" in sqr.render_markdown(d, "triage")


def test_markdown_always_carries_the_kill_guardrail(bundle):
    d = sqr.build_digest(bundle)
    assert "[HUMAN] only" in sqr.render_markdown(d, "triage")


def test_ticket_names_evidence_and_never_proposes_a_kill(bundle):
    text = sqr.draft_ticket(sqr.build_digest(bundle, ["team"], "mongo-specialist"))
    assert "Evidence:" in text and "Deploy correlation:" in text and "Origin:" in text
    assert "kill" not in text.lower().replace("kill_attempted", "").replace("kill_succeeded", "").replace("kill state", "")


def test_html_renders_self_contained_with_both_themes(bundle):
    page = sqr.render_html(sqr.build_digest(bundle, ["team"], "mongo-specialist"))
    assert page.startswith("<!doctype html>")
    assert "prefers-color-scheme:dark" in page and 'data-theme=dark' in page
    assert "<svg" in page and "</html>" in page
    assert "http://" not in page and "https://cdn" not in page  # no external assets


def test_html_escapes_hostile_content(bundle):
    hostile = json.loads(json.dumps(bundle))
    hostile["sentry_issue"]["shortId"] = "<script>alert(1)</script>"
    page = sqr.render_html(sqr.build_digest(hostile))
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;" in page


def test_html_states_the_kill_guardrail_and_the_data_source(bundle):
    page = sqr.render_html(sqr.build_digest(bundle))
    assert "human decision" in page.lower()
    assert "reconstructed fixture" in page


def test_timeline_svg_marks_a_deploy_inside_the_window():
    intervals = [(at(14, 0), at(14, 2), "s1"), (at(14, 1), at(14, 3), "s2")]
    tl = sqr.timeline_svg(intervals, "2026-08-13T14:01:00Z")
    assert tl["deploy_drawn"] is True
    assert "deploylab" in tl["svg"] and tl["shown"] == tl["total"] == 2


def test_timeline_svg_omits_a_deploy_outside_the_window():
    tl = sqr.timeline_svg([(at(14, 0), at(14, 2), "s1")], "2026-08-13T09:00:00Z")
    assert tl["deploy_drawn"] is False
    assert "deploylab" not in tl["svg"]


def test_timeline_svg_caps_bars_and_reports_the_cap():
    intervals = [(at(14, 0) + timedelta(seconds=i), at(14, 1) + timedelta(seconds=i), "s%d" % (i % 4)) for i in range(200)]
    tl = sqr.timeline_svg(intervals)
    assert tl["shown"] == sqr.MAX_TIMELINE_BARS
    assert tl["total"] == 200


def test_timeline_svg_handles_no_attributable_ops():
    tl = sqr.timeline_svg([])
    assert "timeline unavailable" in tl["svg"]
    assert (tl["shown"], tl["total"], tl["focused"]) == (0, 0, False)


def test_peak_window_brackets_the_concurrent_burst():
    intervals = [
        (at(14, 0), at(14, 1), "s1"),
        (at(14, 0, 30), at(14, 1, 30), "s2"),
        (at(15, 0), at(15, 1), "s3"),  # a later, lonely op that must not widen the window
    ]
    assert sqr.peak_window(intervals) == (at(14, 0), at(14, 1, 30))


def test_peak_window_is_none_without_a_real_burst():
    assert sqr.peak_window([]) is None
    assert sqr.peak_window([(at(14, 0), at(14, 1), "s1")]) is None


def test_timeline_zooms_to_the_burst_and_drops_far_away_ops():
    intervals = [
        (at(14, 0), at(14, 1), "s1"),
        (at(14, 0, 30), at(14, 1, 30), "s2"),
        (at(15, 0), at(15, 1), "s3"),
    ]
    tl = sqr.timeline_svg(intervals, focus=sqr.peak_window(intervals))
    assert tl["focused"] is True
    assert (tl["shown"], tl["total"]) == (2, 3)
    assert "s3" not in tl["svg"]


def test_fmt_secs_rounds_for_display():
    assert sqr.fmt_secs(71.61684) == "71.6"
    assert sqr.fmt_secs("absent") == "absent"


def test_cli_writes_html_to_disk(tmp_path):
    out = tmp_path / "r.html"
    assert sqr.main(["--bundle", str(FIXTURE), "--format", "html", "--out", str(out)]) == 0
    assert out.read_text().startswith("<!doctype html>")


def test_cli_never_prints_html_to_stdout(monkeypatch, tmp_path, capsys):
    """Dumping 12KB of markup into the caller's context is the cost this script avoids."""
    monkeypatch.setattr(sqr.tempfile, "gettempdir", lambda: str(tmp_path))
    assert sqr.main(["--bundle", str(FIXTURE), "--format", "html"]) == 0
    out = capsys.readouterr().out
    assert "<!doctype html>" not in out
    assert out.startswith("wrote ")
    written = tmp_path / "slow-query-RAILS-BACKEND-4FA7.html"
    assert written.exists() and written.read_text().startswith("<!doctype html>")


def test_default_html_path_sanitises_the_short_id(tmp_path, monkeypatch):
    monkeypatch.setattr(sqr.tempfile, "gettempdir", lambda: str(tmp_path))
    path = sqr.default_html_path({"incident": {"sentry_short_id": "../../etc/passwd"}})
    assert Path(path).parent == tmp_path
    assert ".." not in Path(path).name


def test_cli_json_mode_is_machine_readable(tmp_path, capsys):
    assert sqr.main(["--bundle", str(FIXTURE), "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["fanout"]["verdict"] == "proven"


def test_cli_requires_a_source():
    assert sqr.main([]) == 2
