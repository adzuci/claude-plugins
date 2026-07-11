import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO / "plugins" / "apollo-eng-leadership" / "skills" / "intercom-assistant"


def read_skill_file(relative: str) -> str:
    return (SKILL_DIR / relative).read_text()


def load_script(name: str):
    path = SKILL_DIR / "scripts" / name
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


def json_from_cli_args(args: list[str]) -> dict:
    json_flag = args.index("--json")
    return json.loads(args[json_flag + 1])


def test_skill_router_covers_support_rotation_copilot_modes():
    skill = read_skill_file("SKILL.md")

    for mode in ("setup", "poll", "pre-call-check", "recap", "wrapup", "calibration", "report"):
        assert f"`{mode}`" in skill

    assert "ask_glean_support_rep_assistant.py" in skill
    assert "routing-and-macros.md" in skill
    assert "mcp__Intercom__*" in skill
    assert "mcp__Granola__get_meeting_transcript" in skill
    assert "references/help-mode.md" in skill
    assert "references/poll-mode.md" in skill
    assert "| `monitor` |" not in skill
    assert "| `triage` |" not in skill
    assert "Former `monitor` and `triage` workflows run through this mode" in skill


def test_live_conversation_assessment_playbook_is_read_only_and_has_output_shape():
    triage = read_skill_file("references/triage-mode.md")

    assert "Live Conversation Assessment Playbook" in triage
    assert "Conversation Summary" in triage
    assert "Suggested Next Steps" in triage
    assert "Draft Reply" in triage
    assert "get_conversation" in triage
    assert "do not send it" in triage.lower()
    assert "--mode live" in triage


def test_setup_mode_teaches_intercom_granola_and_closeout_macro():
    setup = read_skill_file("references/setup-mode.md")
    granola = read_skill_file("references/granola-recipes.md")

    assert "Intercom Details To Pin" in setup
    assert "`granola-recipes.md`" in setup
    assert "## `/Wrap-up`" in granola
    assert "# /Stall" in granola
    assert "# /Deescalate" in granola
    assert "Close Out" in setup
    assert "personal" in setup.lower()
    assert "https://docs.granola.ai/help-center/getting-more-from-your-notes/recipes" in setup
    assert "recommend **Auto**" in setup
    assert "ChatGPT Codex CLI" in setup


def test_recap_recipe_is_read_only_and_has_required_fields():
    recap = read_skill_file("references/recap-recipe.md")

    for field in ("Quick Script:", "Customer:", "Issue:", "Outcome:", "Actions taken:"):
        assert field in recap
    assert "Include only when actionable or meaningful" in recap
    assert "Do not update Intercom automatically" in recap
    assert "`recap` or `wrapup`" in recap
    assert "<name> Closeout" in recap
    assert "mcp__Intercom__get_conversation" in recap
    # recap-recipe rewrite: source ordering + open-conversation guard
    assert "Source Check" in recap
    assert "Open Conversation Check" in recap
    assert "call_summary" in recap


def test_poll_mode_has_queue_summary_and_live_trigger():
    poll = read_skill_file("references/poll-mode.md")

    assert "search_conversations" in poll
    assert "Open Queue" in poll
    assert "assess it in `live`" in poll
    assert "references/live-intercom-mode.md" in poll
    assert "run triage" not in poll
    assert "read-only" in poll


def test_help_mode_has_connector_status_table_and_setup_guidance():
    help_md = read_skill_file("references/help-mode.md")

    assert "Connector Status" in help_md
    assert "Intercom MCP" in help_md
    assert "Granola MCP" in help_md
    assert "Glean CLI" in help_md
    assert "list_companies" in help_md
    assert "get_account_info" in help_md
    assert "Would you like help" in help_md
    assert "setup" in help_md
    assert "ChatGPT Codex CLI" in help_md


def test_routing_reference_has_key_macros_and_clear_route_guardrail():
    routing = read_skill_file("references/routing-and-macros.md")

    assert "`Escalate to Billing`" in routing


def test_technical_escalation_requires_authenticated_role_routing_and_confirmation():
    routing = read_skill_file("references/routing-and-macros.md")
    live = read_skill_file("references/live-intercom-mode.md")
    roster = read_skill_file("references/em-rotation-roster.md")

    # EM: an exact roster match without authenticated identity evidence is insufficient.
    assert (
        "Treat a caller as a verified EM only when an exact roster-name match is corroborated "
        "by trusted, authenticated identity metadata"
    ) in roster
    assert "A name match alone is not sufficient." in roster
    assert "Slack MCP user-profile lookup" in roster
    assert "Apply `em-rotation-roster.md` **Use In Escalations**" in routing

    # PA/CA: Apollo Operator is research support, while customer handoff remains Intercom.
    assert "Product Advocate or Customer Advocate may take a reviewed Apollo Operator research question" in roster
    assert "If stuck, escalate to: <role-specific path; see routing-and-macros.md>" in live
    assert "After explicit confirmation, a human may post it through Slack MCP" in live

    # Unknown or ambiguous identity: no Slack path, with the technical queue as the handoff.
    assert "do not offer any Slack route" in roster
    assert "If authenticated identity metadata is unavailable, incomplete, or ambiguous" in roster
    assert "or when identity metadata is unavailable or ambiguous" in live
    assert "Send only after explicit caller confirmation." in routing
    assert "Sequencing with a confirm-gate" in routing
    assert "confirm the route is correct" in routing
    assert "Propose the confirmed workflow for a human to carry out" in routing
    assert "`Escalate to Billing Renewals`" in routing
    assert "`Escalate to CA - Transfer Chat`" in routing
    assert "`Escalate to Blockages`" in routing
    assert "`Escalate to External Fraud (Chats)`" in routing
    assert "only when the route is clear" in routing
    assert "confirm exact names in IKB" in routing


def test_apollo_operator_reference_requires_review_before_slack_send():
    skill = read_skill_file("SKILL.md")
    operator = read_skill_file("references/apollo-operator.md")

    assert "Determine the caller role before involving Apollo Operator" in skill
    assert "C01JF1PP74N" in operator
    assert "C0ALMDYQ5PT" in operator
    assert "<@U0ABEQ94H7Z>" in operator
    assert "explicit confirmation" in operator
    assert "Slack MCP send-message tool" in operator
    assert "https://apolloio.slack.com/archives/C01JF1PP74N" in operator
    assert "Redact customer names" in operator
    assert "one Apollo Operator thread per Intercom conversation" in operator
    assert "During Live Calls" in operator
    assert "#ama-pa-apollo-operator" in operator
    assert "Team and conversation IDs are expected investigation identifiers" in operator


def test_help_mode_has_slack_fallback_for_operator_questions():
    help_md = read_skill_file("references/help-mode.md")

    assert "Slack MCP" in help_md
    assert "C01JF1PP74N" in help_md
    assert "C0ALMDYQ5PT" in help_md


def test_skill_forbids_emdashes_and_requires_customer_timezone():
    skill = read_skill_file("SKILL.md")

    assert "Never use em dashes" in skill
    assert "convert it to the customer's timezone" in skill


def test_live_mode_leads_with_pre_reply_recap_and_account_tenure():
    live = read_skill_file("references/live-intercom-mode.md")

    assert "Pre-Reply Recap" in live
    assert "Pre-reply recap" in live
    assert "Account age:" in live
    assert "This user signed up:" in live
    assert "company `created_at`" in live
    assert "contact `created_at`" in live
    assert "Do not use em dashes" in live


def test_live_mode_nudges_report_at_end_of_shift_without_running_it():
    live = read_skill_file("references/live-intercom-mode.md")

    assert "When the caller says they are done for the day" in live
    assert "/apollo-eng-leadership:intercom-assistant report --date YYYY-MM-DD" in live
    assert "must not be generated without the caller asking" in live


def test_call_nudges_include_direct_answer_call_language():
    nudges = read_skill_file("references/call-nudges.md")

    assert "Answer Call button" in nudges
    assert "enable your mic and share your screen" in nudges
    assert "Do not offer a call by default" in nudges


def test_dependency_checker_nudges_for_missing_glean(monkeypatch):
    deps = load_script("check_dependencies.py")
    monkeypatch.setattr(deps.shutil, "which", lambda _name: None)

    statuses = deps.collect_statuses()
    glean = next(item for item in statuses if item.name == "glean")

    assert glean.status == "missing"
    assert "glean auth login" in glean.nudge
    assert any(item.name == "intercom_mcp" for item in statuses)


def test_glean_bridge_prompt_and_missing_cli_nudge(monkeypatch):
    bridge = load_script("ask_glean_support_rep_assistant.py")

    prompt = bridge.build_user_prompt(
        "intro",
        "How do exports work?",
        "Acme account",
        glean_assistant="zendesk-kb",
    )
    assert "approved sources only" in prompt
    assert "How do exports work?" in prompt
    assert "Requested Glean assistant/source wrapper: zendesk-kb" in prompt
    assert "Apollo Zendesk KB/IKB pages" in prompt
    assert "Do not invent account-specific facts" in prompt
    assert "macro-suggest" in bridge.MODES

    monkeypatch.setattr(bridge.shutil, "which", lambda _name: None)
    with pytest.raises(bridge.GleanSupportRepAssistantError) as exc:
        bridge.find_glean_cli()
    assert "glean auth login" in str(exc.value)
    assert "not as Support Rep Assistant output" in str(exc.value)


def test_glean_bridge_uses_cli_preserved_payload_shape():
    bridge = load_script("ask_glean_support_rep_assistant.py")

    payload = bridge.build_agent_payload("agent-123", "prompt text")

    assert payload == {"agent_id": "agent-123", "input": {"query": "prompt text"}}


def test_glean_bridge_extracts_nested_text():
    bridge = load_script("ask_glean_support_rep_assistant.py")

    calls = []

    def runner(*_args, **_kwargs):
        calls.append(_args[0])
        return subprocess.CompletedProcess(
            args=["glean"],
            returncode=0,
            stdout='{"result":{"message":{"fragments":[{"text":"Use the export settings page."}]}}}',
            stderr="",
        )

    answer = bridge.run_glean_agent("agent", "prompt", "/usr/bin/glean", runner=runner)
    assert answer == "Use the export settings page."
    sent_payload = json_from_cli_args(calls[0])
    assert sent_payload["agent_id"] == "agent"
    assert sent_payload["input"]["query"] == "prompt"


def test_daily_report_renderer_escapes_html_and_counts_statuses():
    report = load_script("render_daily_report.py")

    html = report.render_html(
        {
            "title": "My Day",
            "calls": [
                {
                    "customer": "<Acme>",
                    "issue": "Export issue",
                    "outcome": "Resolved",
                    "status": "resolved",
                    "product_signals": ["Confusing export button"],
                },
                {"customer": "Beta", "issue": "Billing", "outcome": "Escalated", "status": "escalated"},
            ],
            "themes": ["Exports"],
        },
        "2026-06-18",
    )

    assert "&lt;Acme&gt;" in html
    assert '<div class="kpi-value">2</div>' in html
    assert "Confusing export button" in html
    assert "Support Rotation Daily Report" not in html


def test_daily_report_parses_raw_transcript_into_collapsible_timeline():
    report = load_script("render_daily_report.py")

    html = report.render_html(
        {
            "calls": [
                {
                    "customer": "Pat",
                    "transcript": '[00:00:02] Speaker 1: "Hi, can you hear me?"\n[00:00:33] Speaker 2: "Yes, good morning."',
                }
            ]
        },
        "2026-06-23",
    )

    assert "<details" in html
    assert "Full chat &amp; call timeline (2)" in html
    assert "00:00:02" in html
    assert "Hi, can you hear me?" in html
    # Quotes are stripped from parsed transcript text.
    assert '&quot;Hi, can you hear me?&quot;' not in html


def test_daily_report_structured_timeline_takes_precedence_and_custom_label():
    report = load_script("render_daily_report.py")

    entries = report.normalize_timeline(
        {
            "transcript": "ignored: should not be used",
            "timeline": [{"time": "10:00", "speaker": "Agent", "text": "Hello"}],
        }
    )

    assert entries == [{"time": "10:00", "speaker": "Agent", "text": "Hello"}]

    html = report.render_html(
        {"calls": [{"customer": "Beta", "timeline": [{"speaker": "A", "text": "hi"}], "timeline_label": "Chat log"}]},
        "2026-06-23",
    )
    assert "Chat log (1)" in html


def test_daily_report_omits_timeline_when_no_transcript():
    report = load_script("render_daily_report.py")

    html = report.render_html({"calls": [{"customer": "NoConvo", "issue": "x"}]}, "2026-06-23")

    assert "<details" not in html


def test_daily_report_requires_granola_and_intercom_source_coverage():
    report_ref = read_skill_file("references/daily-report.md")

    assert "do both a Granola pass and an Intercom MCP pass" in report_ref
    assert "mcp__Granola__list_meetings" in report_ref
    assert "mcp__Granola__query_granola_meetings" in report_ref
    assert "mcp__Intercom__get_conversation" in report_ref
    assert "Intercom search/list tool" in report_ref
    assert "missing Granola meetings as missing call-note coverage only" in report_ref
    assert "Never conclude \"no interactions\" from Granola alone" in report_ref
    assert "Prefer Intercom for conversation counts/status and Granola for call coaching/transcript detail" in report_ref

def test_daily_report_renders_shift_activity_shadow_ideas_and_csat():
    report = load_script("render_daily_report.py")

    html = report.render_html(
        {
            "shift": {"start": "9:30 AM", "end": "3:30 PM", "timezone": "America/New_York"},
            "csat_summary": {"label": "Not captured", "rated": 0, "total": 2},
            "cx_score_summary": {"label": "5", "rated": 1, "total": 2},
            "cx_metrics": [
                {
                    "name": "Adam",
                    "chats_started": 7,
                    "calls_started": 2,
                    "screenshare_offered": 2,
                    "avg_handle_time": "Not captured",
                    "avg_call_duration": "17m",
                    "avg_frt": "Not captured",
                    "max_frt": "Not captured",
                    "csat_score": "Not captured",
                }
            ],
            "calls": [
                {
                    "customer": "Fady",
                    "status": "resolved",
                    "channel": "call",
                    "start_time": "11:00 AM",
                    "duration_minutes": 17,
                    "included_call": True,
                },
                {
                    "customer": "Shaquil",
                    "status": "resolved",
                    "channel": "chat",
                    "included_call": False,
                },
            ],
            "shadow_info": [
                {
                    "title": "Claudia shadowing",
                    "context": "Observed analytics-report troubleshooting.",
                    "takeaways": ["Label report lag carefully."],
                }
            ],
            "ideas_generated": [
                {"idea": "Add Intercom source pass", "source": "reporting", "next_action": "Ship in skill"}
            ],
        },
        "2026-06-23",
    )

    assert "Shift window" in html
    assert "Activity Timeline" in html
    assert "Calls Included" in html
    assert "17m" in html
    assert "Feedback Scores" in html
    assert "CSAT" in html
    assert "Not captured" in html
    assert "Records with CSAT" in html
    assert "CX Score rating" in html
    assert "Records with CX Score" in html
    assert "<strong>5 (1/2)</strong>" in html
    assert "<strong>0</strong>" in html
    assert "Not captured%" not in html
    assert "Chats vs. Calls" in html
    assert "Handle Time vs. Call Time" in html
    assert "Avg FRT / Max FRT" in html
    assert "Screenshare Offered" in html
    assert "Shadow Info" in html
    assert "Claudia shadowing" in html
    assert "Ideas Generated" in html
    assert "Add Intercom source pass" in html


def test_daily_report_reference_documents_shift_shadow_ideas_and_csat_fields():
    report_ref = read_skill_file("references/daily-report.md")

    assert "`shift`" in report_ref
    assert "`activity_timeline`" in report_ref
    assert "`cx_metrics`" in report_ref
    assert "`csat_summary`" in report_ref
    assert "`cx_score_summary`" in report_ref
    assert "keep separate from CSAT" in report_ref
    assert "`shadow_info`" in report_ref
    assert "`ideas_generated`" in report_ref
    assert "Handle Time vs. Call Time" in report_ref
    assert "Avg FRT / Max FRT" in report_ref
    assert "screenshares offered" in report_ref
    assert "Shadow info: separate section" in report_ref
    assert "Ideas generated: separate section" in report_ref



# ---------------------------------------------------------------------------
# pre-call-check mode
# ---------------------------------------------------------------------------


def test_pre_call_check_reference_has_framework_and_checklist():
    pcc = read_skill_file("references/pre-call-check.md")

    # 7-step names
    for step in ("Welcome", "Verify", "Set Expectations", "Clarify and Align", "Discovery",
                 "Troubleshoot and Guide", "Confirm and Close"):
        assert step in pcc, f"Missing 7-step name: {step}"

    # Checklist: recording disclosure + identity verification
    assert "recording" in pcc.lower()
    assert "authorized user" in pcc
    assert "Output Shape" in pcc
    assert "Post-Fin" in pcc
    # No em dashes
    assert "—" not in pcc


def test_skill_output_shapes_includes_pre_call_check():
    skill = read_skill_file("SKILL.md")
    # Line 91 area now lists pre-call-check in the output-shapes modes
    assert "`pre-call-check`" in skill


# ---------------------------------------------------------------------------
# call-nudges enforcement
# ---------------------------------------------------------------------------


def test_call_nudges_softened_offer_and_enforcement():
    nudges = read_skill_file("references/call-nudges.md")

    # Existing substring must survive the rewrite
    assert "Do not offer a call by default" in nudges
    # Gated skip conditions
    assert "single fact" in nudges or "single-fact" in nudges
    assert "fewer than 3" in nudges
    # 8-minute re-trigger
    assert "8" in nudges and "minute" in nudges.lower()
    # Banned phrase
    assert "if you prefer to keep this in chat" in nudges
    # Post-call close rule
    assert "Closing After A Call" in nudges or "post-call" in nudges.lower()
    # IKB post-acceptance copy
    assert "Answer Call button" in nudges
    # FRT note
    assert "response-time" in nudges or "FRT" in nudges or "first-response" in nudges
    # No em dashes
    assert "—" not in nudges


# ---------------------------------------------------------------------------
# live-intercom-mode additions
# ---------------------------------------------------------------------------


def test_live_mode_has_fast_start_pattern():
    live = read_skill_file("references/live-intercom-mode.md")
    assert "Quick read" in live or "quick read" in live.lower()
    assert "still digging" in live.lower()


def test_live_mode_has_tool_efficiency_rules():
    live = read_skill_file("references/live-intercom-mode.md")
    assert "once" in live and "get_conversation" in live
    assert "wasted" in live.lower() or "Tool Efficiency" in live


def test_live_mode_has_snooze_and_conflict_guardrails():
    live = read_skill_file("references/live-intercom-mode.md")
    assert "Live Support Snooze for 24 Hours" in live
    assert "mask an unmet SLA" in live
    assert "internal note" in live and "stepping away" in live
    assert "IKB wins" in live
    assert "Never send IKB article" in live or "never send IKB article" in live


def test_sequence_tree_covers_all_five_classes():
    live = read_skill_file("references/live-intercom-mode.md")
    diag = load_script("diagnose_mongo_sequence_mailbox.py")

    for issue_class in diag.ALL_ISSUE_CLASSES:
        assert issue_class in live, f"Sequence tree missing class: {issue_class}"


def test_sequence_tree_classes_match_classifier():
    """Drift catcher: verify each branch maps to a real classify_issue result."""
    diag = load_script("diagnose_mongo_sequence_mailbox.py")

    cases = [
        ("sequence is active but not sending emails", diag.SEQUENCE_ACTIVATION),
        ("contacts added but nothing happened no emails", diag.CONTACT_ENROLLMENT),
        ("emails are stuck queued and delayed", diag.DELAYED_SCHEDULED),
        ("mailbox keeps disconnecting", diag.MAILBOX_LINKAGE),
        ("getting bounces and deliverability issues", diag.DELIVERABILITY),
    ]
    for description, expected_class in cases:
        result = diag.classify_issue(description)
        assert result.issue_class == expected_class, (
            f"classify_issue({description!r}) returned {result.issue_class}, expected {expected_class}"
        )


# ---------------------------------------------------------------------------
# wave2 de-escalation script bank
# ---------------------------------------------------------------------------


def test_wave2_deescalation_has_script_bank():
    wave2 = read_skill_file("references/wave2-patterns.md")

    # At least one fact-based Align and one Acknowledge script
    assert "should just work" in wave2 or "blocking" in wave2
    assert "take it from here" in wave2 or "figure out what" in wave2
    # Gated emotion note
    assert "only when the customer used" in wave2 or "gated" in wave2.lower()
    # Skip-to-Act warning
    assert "dismissive" in wave2
    # Hard-stop pointer
    assert "Escalate to Manager" in wave2


# ---------------------------------------------------------------------------
# diagnose_mongo_sequence_mailbox.py — untested functions
# ---------------------------------------------------------------------------


def test_should_trigger_mongo_returns_false_for_informational():
    diag = load_script("diagnose_mongo_sequence_mailbox.py")

    # Pure informational questions should not trigger Mongo
    assert not diag.should_trigger_mongo("how do I add contacts to a sequence")
    assert not diag.should_trigger_mongo("what is a send window")
    assert not diag.should_trigger_mongo("how to set up mailbox warmup")


def test_should_trigger_mongo_returns_true_for_investigative():
    diag = load_script("diagnose_mongo_sequence_mailbox.py")

    assert diag.should_trigger_mongo("sequence not sending after activation")
    assert diag.should_trigger_mongo("mailbox disconnected not working")
    assert diag.should_trigger_mongo("emails are stuck and delayed")


def test_should_trigger_mongo_investigative_overrides_informational_gate():
    diag = load_script("diagnose_mongo_sequence_mailbox.py")

    # "how do I" is informational, but "not working" overrides the gate when a bucket keyword also matches
    assert diag.should_trigger_mongo("how do I debug mailbox not working")


def test_build_query_plan_returns_plan_for_all_known_classes():
    diag = load_script("diagnose_mongo_sequence_mailbox.py")

    for issue_class in diag.ALL_ISSUE_CLASSES:
        plan = diag.build_query_plan(issue_class)
        assert plan is not None, f"No query plan for {issue_class}"
        assert plan.issue_class == issue_class
        assert len(plan.checks) >= 1
        for check in plan.checks:
            assert check.mcp_server
            assert check.collection
            assert check.key_fields


def test_build_query_plan_returns_none_for_unknown():
    diag = load_script("diagnose_mongo_sequence_mailbox.py")

    assert diag.build_query_plan(diag.UNKNOWN) is None
    assert diag.build_query_plan("nonexistent_class") is None


def test_build_query_plan_check_specs_reference_staging_servers():
    """Regression: verify all checks use staging MCP server names (not prod)."""
    diag = load_script("diagnose_mongo_sequence_mailbox.py")

    for issue_class in diag.ALL_ISSUE_CLASSES:
        plan = diag.build_query_plan(issue_class)
        for check in plan.checks:
            assert "staging" in check.mcp_server, (
                f"{issue_class}/{check.label}: mcp_server {check.mcp_server!r} "
                "does not contain 'staging' — update live-intercom-mode.md collection "
                "table and this test if prod server names are intentional"
            )


def test_format_mongo_block_unavailable_path():
    diag = load_script("diagnose_mongo_sequence_mailbox.py")

    result = diag.format_mongo_block(
        classification=None,
        unavailable=True,
    )
    assert "unavailable" in result.lower()
    assert "Intercom and Glean" in result


def test_format_mongo_block_renders_all_sections():
    diag = load_script("diagnose_mongo_sequence_mailbox.py")

    classification = diag.IssueClassification(
        issue_class=diag.SEQUENCE_ACTIVATION,
        trigger_mongo=True,
        confidence="high",
        matched_signals=["not sending", "sequence on but"],
    )
    result = diag.format_mongo_block(
        classification=classification,
        checks_run=["Campaign state (emailer_campaigns)"],
        verified_facts=["campaign.status = active"],
        remaining_unknowns=["step toggle state not checked"],
        escalation_trigger="none",
    )

    assert "private" in result.lower()
    assert diag.SEQUENCE_ACTIVATION in result
    assert "high" in result
    assert "not sending" in result
    assert "Campaign state" in result
    assert "campaign.status = active" in result
    assert "step toggle state not checked" in result
    assert "none" in result


def test_format_mongo_block_empty_lists_show_placeholders():
    diag = load_script("diagnose_mongo_sequence_mailbox.py")

    classification = diag.IssueClassification(
        issue_class=diag.MAILBOX_LINKAGE,
        trigger_mongo=True,
        confidence="medium",
        matched_signals=["mailbox"],
    )
    result = diag.format_mongo_block(classification=classification)

    assert "(none run)" in result
    assert "(none yet)" in result
    assert "(none identified)" in result


# ---------------------------------------------------------------------------
# apollo-policies.md safety gate
# ---------------------------------------------------------------------------


def test_apollo_policies_has_required_urls_and_age_guidance():
    policies = read_skill_file("references/apollo-policies.md")

    assert "https://www.apollo.io/terms" in policies
    assert "https://www.apollo.io/privacy-policy" in policies
    assert "legal age" in policies
    assert "do not state a specific minimum age" in policies.lower() or "Do not state a specific minimum age" in policies
    assert "privacy-center" in policies or "remove" in policies


# ---------------------------------------------------------------------------
# access-and-credentials-faq.md safety gate
# ---------------------------------------------------------------------------


def test_access_faq_has_hard_stop_and_read_only_guardrail():
    faq = read_skill_file("references/access-and-credentials-faq.md")

    assert "Hard Stop" in faq or "hard stop" in faq.lower()
    assert "account takeover" in faq.lower()
    assert "authorized user" in faq.lower()
    assert "Read-only" in faq or "read-only" in faq.lower()
    assert "SSO" in faq
    assert "seat" in faq.lower()
    # No em dashes
    assert "—" not in faq


# ---------------------------------------------------------------------------
# routing escalation routes + sequencing
# ---------------------------------------------------------------------------


def test_routing_has_escalation_routes_and_sequencing():
    routing = read_skill_file("references/routing-and-macros.md")

    assert "## Escalation Routes" in routing
    # Confirm-gate sequencing
    assert "confirm the route is correct" in routing
    assert "note (private)" in routing and "macro (customer-visible)" in routing
    # Internal-note templates
    assert "Template: Technical Escalation" in routing
    assert "Template: Billing Escalation" in routing
    # Tech handoff sample
    assert "Tech Team" in routing
    # Read-only hardening: workflow execution is proposed for a human, never applied.
    assert "Propose the confirmed workflow for a human to carry out" in routing
    assert "apply the workflow" not in routing.lower()


# ---------------------------------------------------------------------------
# new FAQ references
# ---------------------------------------------------------------------------


def test_billing_triage_reference():
    billing = read_skill_file("references/billing-triage.md")

    # Fraud fork first
    assert "Unauthorized" in billing or "fraud" in billing.lower()
    assert billing.index("Fraud") < billing.index("Refund"), \
        "Fraud fork must appear before Refund in billing triage"
    # Triage/policy boundary
    assert "never states an outcome" in billing or "never state an outcome" in billing.lower()
    # Cancellation -> route to AM/CSM
    assert "AM" in billing or "CSM" in billing
    # Guardrail
    assert "Read-only" in billing
    # Post-Fin framing
    assert "Post-Fin" in billing
    # No em dashes
    assert "—" not in billing


def test_access_faq():
    access = read_skill_file("references/access-and-credentials-faq.md")

    assert "authorized user" in access
    assert "SSO" in access
    assert "Read-only" in access
    assert "Post-Fin" in access
    assert "—" not in access


def test_product_area_faqs():
    faqs = read_skill_file("references/product-area-faqs.md")

    # Both API and Chrome sections present
    assert "## Apollo API" in faqs
    assert "## Chrome Extension" in faqs
    # Key content
    assert "401" in faqs
    assert "429" in faqs
    assert "Chrome Web Store" in faqs
    assert "Read-only" in faqs
    assert "Post-Fin" in faqs
    assert "—" not in faqs


def test_no_emdashes_in_new_references():
    """Em-dash guard on new files and files with new customer-facing copy added this PR.
    routing-and-macros.md is excluded because pre-existing Adam personal-macro table
    uses em dashes as separators and changing it is out of scope."""
    for path in (
        "references/pre-call-check.md",
        "references/billing-triage.md",
        "references/access-and-credentials-faq.md",
        "references/product-area-faqs.md",
        "references/wave2-patterns.md",
        "references/call-nudges.md",
    ):
        content = read_skill_file(path)
        assert "—" not in content, f"Em dash found in {path}"


# ---------------------------------------------------------------------------
# --mongo flag tests
# ---------------------------------------------------------------------------


def test_skill_documents_mongo_flag():
    skill = read_skill_file("SKILL.md")
    assert "--mongo" in skill
    assert "live" in skill


def test_live_mode_documents_mongo_path():
    live = read_skill_file("references/live-intercom-mode.md")
    assert "--mongo" in live
    assert "trigger_mongo" in live
    assert "Mongo MCP unavailable" in live
    assert "Read-only" in live


def test_mongo_trigger_detects_sequence_activation_issue():
    diag = load_script("diagnose_mongo_sequence_mailbox.py")

    result = diag.classify_issue("My sequence is active but not sending any emails to enrolled contacts")
    assert result.trigger_mongo is True
    assert result.issue_class == diag.SEQUENCE_ACTIVATION


def test_mongo_trigger_detects_contact_enrollment_failure():
    diag = load_script("diagnose_mongo_sequence_mailbox.py")

    result = diag.classify_issue("I added contacts to my sequence but nothing happened, no emails were sent")
    assert result.trigger_mongo is True
    assert result.issue_class == diag.CONTACT_ENROLLMENT


def test_mongo_trigger_detects_mailbox_issue():
    diag = load_script("diagnose_mongo_sequence_mailbox.py")

    result = diag.classify_issue("My mailbox keeps disconnecting and emails stop sending")
    assert result.trigger_mongo is True
    assert result.issue_class == diag.MAILBOX_LINKAGE


def test_mongo_no_trigger_for_pure_informational_question():
    diag = load_script("diagnose_mongo_sequence_mailbox.py")

    result = diag.classify_issue("How do I set up a new sequence in Apollo?")
    assert result.trigger_mongo is False


def test_mongo_trigger_for_investigative_how_question():
    diag = load_script("diagnose_mongo_sequence_mailbox.py")

    # "why isn't my sequence sending" is investigative even though it contains "how"
    result = diag.classify_issue("Why isn't my sequence sending emails after activation?")
    assert result.trigger_mongo is True


def test_mongo_query_plan_covers_all_issue_classes():
    diag = load_script("diagnose_mongo_sequence_mailbox.py")

    for issue_class in diag.ALL_ISSUE_CLASSES:
        plan = diag.build_query_plan(issue_class)
        assert plan is not None, f"No query plan for issue class: {issue_class}"
        assert len(plan.checks) >= 2, f"Fewer than 2 checks for {issue_class}"
        for check in plan.checks:
            assert check.mcp_server.startswith("mcp__mongodb-mcp-staging-")
            assert check.collection


def test_mongo_unavailable_degrades_gracefully():
    diag = load_script("diagnose_mongo_sequence_mailbox.py")

    block = diag.format_mongo_block(
        diag.IssueClassification(
            issue_class=diag.SEQUENCE_ACTIVATION,
            trigger_mongo=True,
            confidence="high",
            matched_signals=["not sending"],
        ),
        unavailable=True,
    )
    assert "Mongo MCP unavailable" in block
    assert "not Mongo-verified" in block
    # Should still provide forward path
    assert "Intercom" in block or "Glean" in block


def test_mongo_block_format_has_required_sections():
    diag = load_script("diagnose_mongo_sequence_mailbox.py")

    classification = diag.IssueClassification(
        issue_class=diag.DELAYED_SCHEDULED,
        trigger_mongo=True,
        confidence="medium",
        matched_signals=["delayed", "stuck"],
    )
    block = diag.format_mongo_block(
        classification,
        checks_run=["Message statuses (emailer_messages)"],
        verified_facts=["3 messages in 'pending' state"],
        remaining_unknowns=["Daily cap not verified"],
        escalation_trigger="none",
    )
    assert "Mongo evidence" in block
    assert "private" in block.lower()
    assert diag.DELAYED_SCHEDULED in block
    assert "3 messages in 'pending' state" in block
    assert "Daily cap not verified" in block


def test_live_mode_no_mongo_behavior_unchanged():
    """Without --mongo, the live mode docs should not reference Mongo as required."""
    live = read_skill_file("references/live-intercom-mode.md")
    skill = read_skill_file("SKILL.md")

    # The Intercom-first and Glean-backed workflow must still be the primary path
    assert "Intercom tools before drafting conclusions" in live
    assert "glean-support-rep-assistant.md" in live
    # --mongo is additive and explicitly opt-in
    assert "Without `--mongo`" in skill or "--mongo" in skill


# ---------------------------------------------------------------------------
# CX metrics + teammate grouping tests
# ---------------------------------------------------------------------------


def test_report_renders_cx_metrics_tables():
    report = load_script("render_daily_report.py")
    cx = [{"name": "Ahmed", "chats_started": 7, "calls_started": 4, "screenshare_offered": 0,
            "avg_handle_time": "26m", "avg_call_duration": "28m", "avg_frt": "3m", "max_frt": "7m",
            "csat_score": 100, "csat_rated": 1, "csat_total": 1}]
    html = report.render_html({"calls": [], "cx_metrics": cx}, "2026-06-23")
    assert "Chats vs. Calls" in html
    assert "Handle Time" in html
    assert "Avg FRT" in html
    assert "CSAT" in html
    assert "Ahmed" in html
    assert "100%" in html


def test_report_groups_calls_by_teammate():
    report = load_script("render_daily_report.py")
    calls = [
        {"customer": "Acme", "issue": "x", "teammate": "Griffin"},
        {"customer": "Beta", "issue": "y", "teammate": "Ahmed"},
        {"customer": "Gamma", "issue": "z", "teammate": "Griffin"},
    ]
    html = report.render_html({"calls": calls}, "2026-06-23")
    assert "Griffin" in html
    assert "Ahmed" in html
    # Griffin has 2 calls
    assert "2 call" in html or "(2)" in html


def test_report_without_teammates_unchanged():
    report = load_script("render_daily_report.py")
    html = report.render_html({"calls": [{"customer": "Solo", "issue": "z"}]}, "2026-06-23")
    # Should still render fine without any teammate/cx_metrics fields
    assert "Solo" in html
    assert '<table class="cx-table">' not in html  # no CX tables injected
