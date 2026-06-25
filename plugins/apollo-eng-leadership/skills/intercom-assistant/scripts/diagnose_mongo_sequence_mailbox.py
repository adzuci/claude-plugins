#!/usr/bin/env python3
"""Classify sequence/mailbox issue type and return a Mongo-backed query plan.

This script does NOT make Mongo MCP calls itself.  The assistant calls Mongo MCP
tools directly; this helper provides:
  - classify_issue()      — keyword-based issue-class detection
  - should_trigger_mongo() — True when the issue warrants account-state inspection
  - build_query_plan()    — returns structured check specs (collection names, key
                            fields, filter hints) the assistant uses when calling
                            Mongo MCP tools
  - format_mongo_block()  — renders the structured Mongo private-notes block

Collection mapping (raw Mongo → analytics mirror concept):
  mcp__mongodb-mcp-staging-main           emailer_campaigns  →  FCT_MONGO_EMAILER_CAMPAIGNS
  mcp__mongodb-mcp-staging-main           emailer_steps      →  DIM_MONGO_EMAILER_STEPS
  mcp__mongodb-mcp-staging-emailermessages  (root collection) →  FCT_MONGO_EMAILER_MESSAGES
  mcp__mongodb-mcp-staging-email          email_accounts     →  FCT_MONGO_EMAIL_ACCOUNT_CONTACTS

Usage:
  python3 scripts/diagnose_mongo_sequence_mailbox.py --question "why isn't my sequence sending"
  python3 scripts/diagnose_mongo_sequence_mailbox.py --question "..." --team-id 123 --json
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from typing import Sequence


# ---------------------------------------------------------------------------
# Issue classes
# ---------------------------------------------------------------------------

SEQUENCE_ACTIVATION = "sequence_activation_sending_failure"
CONTACT_ENROLLMENT = "contact_enrollment_failure"
DELAYED_SCHEDULED = "delayed_scheduled_send"
MAILBOX_LINKAGE = "mailbox_linkage_auth_ramp"
DELIVERABILITY = "deliverability_configuration"
UNKNOWN = "unknown"

ALL_ISSUE_CLASSES = (
    SEQUENCE_ACTIVATION,
    CONTACT_ENROLLMENT,
    DELAYED_SCHEDULED,
    MAILBOX_LINKAGE,
    DELIVERABILITY,
)

# ---------------------------------------------------------------------------
# Keyword sets (lower-case, checked against lower-case input)
# ---------------------------------------------------------------------------

_SEQUENCE_ACTIVATION_KEYWORDS = frozenset(
    {
        "sequence not sending",
        "sequence is active but not",
        "active but not sending",
        "not sending",
        "sequence paused",
        "sequence on but",
        "step toggle",
        "step disabled",
        "warm-up limit",
        "warmup limit",
        "send cap",
        "dynamic variable",
        "missing variable",
        "template missing",
        "activation",
        "won't send",
        "wont send",
        "sequence broken",
        "not activate",
    }
)

_CONTACT_ENROLLMENT_KEYWORDS = frozenset(
    {
        "add to sequence",
        "add_contact",
        "contacts added",
        "enrolled but nothing",
        "contact not enrolled",
        "enrollment failed",
        "failed to enroll",
        "never started",
        "sequence not starting",
        "no emails sent",
        "nothing happened",
        "silent failure",
        "contacts not in sequence",
    }
)

_DELAYED_SCHEDULED_KEYWORDS = frozenset(
    {
        "delayed",
        "stuck",
        "scheduled email",
        "scheduled send",
        "queued",
        "send window",
        "not received",
        "email not arriving",
        "email not sent",
        "follow-up not",
        "follow up not",
        "slow send",
        "pending send",
        "emails late",
        "daily limit",
        "send limit",
    }
)

_MAILBOX_LINKAGE_KEYWORDS = frozenset(
    {
        "mailbox",
        "mailboxes",
        "disconnected",
        "unlinked",
        "keeps unlinking",
        "ramp",
        "ramp-up",
        "warmup",
        "warm up",
        "mailbox assignment",
        "sending limit",
        "mailbox connected",
        "mailbox not",
        "email account",
        "email accounts",
        "spf",
        "dkim",
        "dmarc",
        "oauth",
    }
)

_DELIVERABILITY_KEYWORDS = frozenset(
    {
        "deliverability",
        "spam",
        "bounce",
        "bounced",
        "reputation",
        "tracking domain",
        "blacklist",
        "blocklist",
        "undeliverable",
        "inbox rate",
        "open rate low",
        "authentication issue",
        "domain authentication",
        "sending reputation",
    }
)

# These indicate the question is purely informational — skip Mongo
_INFORMATIONAL_ONLY_PATTERNS = frozenset(
    {
        "how do i",
        "how to",
        "what is",
        "what are",
        "where is",
        "can i",
        "does apollo",
        "is it possible",
        "best practice",
        "what's the difference",
        "what is the difference",
    }
)

# Investigative phrases that override the informational gate
_INVESTIGATIVE_OVERRIDES = frozenset(
    {
        "why isn't",
        "why is it not",
        "why won't",
        "why wont",
        "why didn't",
        "why didnt",
        "why is my",
        "not working",
        "broken",
        "stuck",
        "failed",
        "issue with",
        "problem with",
    }
)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CheckSpec:
    """One check the assistant should run against a Mongo collection."""

    label: str
    mcp_server: str
    collection: str
    description: str
    key_fields: list[str] = field(default_factory=list)
    filter_hint: str = ""


@dataclass
class QueryPlan:
    issue_class: str
    checks: list[CheckSpec]
    rationale: str


@dataclass
class IssueClassification:
    issue_class: str
    trigger_mongo: bool
    confidence: str  # "high" | "medium" | "low"
    matched_signals: list[str]


# ---------------------------------------------------------------------------
# Classification logic
# ---------------------------------------------------------------------------


def _signals(text: str, keywords: frozenset[str]) -> list[str]:
    lower = text.lower()
    return [kw for kw in sorted(keywords) if kw in lower]


def classify_issue(description: str) -> IssueClassification:
    """Return issue class and whether Mongo investigation is warranted."""
    lower = description.lower()

    informational = bool(_signals(lower, _INFORMATIONAL_ONLY_PATTERNS))
    investigative = bool(_signals(lower, _INVESTIGATIVE_OVERRIDES))

    buckets: list[tuple[str, list[str]]] = [
        (SEQUENCE_ACTIVATION, _signals(lower, _SEQUENCE_ACTIVATION_KEYWORDS)),
        (CONTACT_ENROLLMENT, _signals(lower, _CONTACT_ENROLLMENT_KEYWORDS)),
        (DELAYED_SCHEDULED, _signals(lower, _DELAYED_SCHEDULED_KEYWORDS)),
        (MAILBOX_LINKAGE, _signals(lower, _MAILBOX_LINKAGE_KEYWORDS)),
        (DELIVERABILITY, _signals(lower, _DELIVERABILITY_KEYWORDS)),
    ]

    best_class, best_signals = max(buckets, key=lambda t: len(t[1]))

    if not best_signals:
        return IssueClassification(
            issue_class=UNKNOWN,
            trigger_mongo=False,
            confidence="low",
            matched_signals=[],
        )

    # Informational questions only skip Mongo if no investigative override
    skip_mongo = informational and not investigative and best_class not in (
        SEQUENCE_ACTIVATION,
        CONTACT_ENROLLMENT,
    )

    confidence = "high" if len(best_signals) >= 3 else "medium" if len(best_signals) >= 1 else "low"

    return IssueClassification(
        issue_class=best_class,
        trigger_mongo=not skip_mongo,
        confidence=confidence,
        matched_signals=best_signals,
    )


def should_trigger_mongo(description: str) -> bool:
    return classify_issue(description).trigger_mongo


# ---------------------------------------------------------------------------
# Query plans per issue class
# ---------------------------------------------------------------------------

_PLANS: dict[str, QueryPlan] = {
    SEQUENCE_ACTIVATION: QueryPlan(
        issue_class=SEQUENCE_ACTIVATION,
        rationale="Sequence appears active but is not sending. Check campaign state, step toggles, enrollment, send history, and warm-up/cap state.",
        checks=[
            CheckSpec(
                label="Campaign state",
                mcp_server="mcp__mongodb-mcp-staging-main",
                collection="emailer_campaigns",
                description="Verify sequence active/paused status, settings, and owner.",
                key_fields=["_id", "name", "status", "active", "settings", "user_id", "team_id"],
                filter_hint="Filter by sequence/campaign ID or team_id if known.",
            ),
            CheckSpec(
                label="Step toggles",
                mcp_server="mcp__mongodb-mcp-staging-main",
                collection="emailer_steps",
                description="Check each step is enabled, has a valid template, and has no missing dynamic variables.",
                key_fields=["_id", "emailer_campaign_id", "active", "type", "subject", "body_text"],
                filter_hint="Join on emailer_campaign_id from the campaign check.",
            ),
            CheckSpec(
                label="Contact enrollment",
                mcp_server="mcp__mongodb-mcp-staging-main",
                collection="emailer_contacts",
                description="Confirm contacts are actually enrolled in the sequence.",
                key_fields=["_id", "emailer_campaign_id", "contact_id", "current_step", "status"],
                filter_hint="Filter by emailer_campaign_id. Expect at least one 'active' record if sending should occur.",
            ),
            CheckSpec(
                label="Recent send history",
                mcp_server="mcp__mongodb-mcp-staging-emailermessages",
                collection="emailer_messages",
                description="Check whether any messages were actually sent/delivered vs. pending/failed.",
                key_fields=["_id", "emailer_campaign_id", "status", "sent_at", "scheduled_at", "error"],
                filter_hint="Filter by emailer_campaign_id; look for status='sent','delivered','error','bounced'.",
            ),
        ],
    ),
    CONTACT_ENROLLMENT: QueryPlan(
        issue_class=CONTACT_ENROLLMENT,
        rationale="Contacts were added but no sequence activity started. Verify the enrollment event reached the sequence and contacts are visible.",
        checks=[
            CheckSpec(
                label="Enrollment records",
                mcp_server="mcp__mongodb-mcp-staging-main",
                collection="emailer_contacts",
                description="Confirm contacts appear enrolled in the sequence at all.",
                key_fields=["_id", "emailer_campaign_id", "contact_id", "current_step", "status", "created_at"],
                filter_hint="Filter by emailer_campaign_id. If count is 0, enrollment silently failed.",
            ),
            CheckSpec(
                label="Campaign active check",
                mcp_server="mcp__mongodb-mcp-staging-main",
                collection="emailer_campaigns",
                description="Confirm the campaign is active so new enrollments can proceed.",
                key_fields=["_id", "status", "active", "settings"],
                filter_hint="Filter by campaign ID. Inactive campaigns block new enrollment.",
            ),
            CheckSpec(
                label="Send history post-enroll",
                mcp_server="mcp__mongodb-mcp-staging-emailermessages",
                collection="emailer_messages",
                description="Check whether any messages were queued or sent after the reported enrollment.",
                key_fields=["_id", "contact_id", "emailer_campaign_id", "status", "created_at", "scheduled_at"],
                filter_hint="Filter by contact_id or emailer_campaign_id with created_at after the enrollment date.",
            ),
        ],
    ),
    DELAYED_SCHEDULED: QueryPlan(
        issue_class=DELAYED_SCHEDULED,
        rationale="Emails appear stuck, delayed, or queued. Check message status, scheduled times, daily limits, and mailbox send windows.",
        checks=[
            CheckSpec(
                label="Message statuses",
                mcp_server="mcp__mongodb-mcp-staging-emailermessages",
                collection="emailer_messages",
                description="Find messages in pending/queued/scheduled state and their expected send times.",
                key_fields=["_id", "status", "scheduled_at", "sent_at", "error", "emailer_campaign_id", "contact_id"],
                filter_hint="Filter for status in ('pending','scheduled','queued'). Compare scheduled_at to now.",
            ),
            CheckSpec(
                label="Daily send cap / warm-up state",
                mcp_server="mcp__mongodb-mcp-staging-email",
                collection="email_accounts",
                description="Check daily send limit, warm-up status, and remaining quota for the assigned mailbox.",
                key_fields=["_id", "email", "daily_send_limit", "warmup_enabled", "warmup_status", "sent_today"],
                filter_hint="Filter by the sending email address or mailbox ID.",
            ),
            CheckSpec(
                label="Send window settings",
                mcp_server="mcp__mongodb-mcp-staging-main",
                collection="emailer_campaigns",
                description="Check send window (days/hours) configured on the campaign.",
                key_fields=["_id", "settings.send_window", "settings.timezone"],
                filter_hint="Filter by campaign ID. A restrictive send window blocks emails outside configured hours.",
            ),
        ],
    ),
    MAILBOX_LINKAGE: QueryPlan(
        issue_class=MAILBOX_LINKAGE,
        rationale="Mailbox connectivity or assignment issue. Check mailbox auth state, linkage, ramp status, and daily caps.",
        checks=[
            CheckSpec(
                label="Mailbox auth state",
                mcp_server="mcp__mongodb-mcp-staging-email",
                collection="email_accounts",
                description="Check OAuth/auth status, last connection time, and error flags.",
                key_fields=["_id", "email", "provider", "status", "auth_error", "last_connected_at", "active"],
                filter_hint="Filter by the customer's email address or team_id.",
            ),
            CheckSpec(
                label="Warm-up and ramp status",
                mcp_server="mcp__mongodb-mcp-staging-email",
                collection="email_accounts",
                description="Confirm warm-up is enabled, current ramp level, and daily limit.",
                key_fields=["_id", "email", "warmup_enabled", "warmup_status", "warmup_current_volume", "daily_send_limit"],
                filter_hint="Filter by mailbox ID or email address.",
            ),
            CheckSpec(
                label="Mailbox-sequence assignment",
                mcp_server="mcp__mongodb-mcp-staging-main",
                collection="emailer_campaigns",
                description="Verify which mailbox(es) are assigned to send for this sequence.",
                key_fields=["_id", "name", "settings.email_account_ids", "settings.rotation_mode"],
                filter_hint="Filter by campaign ID. settings.email_account_ids shows assigned mailboxes.",
            ),
        ],
    ),
    DELIVERABILITY: QueryPlan(
        issue_class=DELIVERABILITY,
        rationale="Deliverability or authentication issue. Surface available mailbox auth/DNS state; defer deep root-cause to escalation.",
        checks=[
            CheckSpec(
                label="Mailbox auth and provider",
                mcp_server="mcp__mongodb-mcp-staging-email",
                collection="email_accounts",
                description="Check provider, SPF/DKIM/DMARC flags visible in account record, and auth errors.",
                key_fields=["_id", "email", "provider", "status", "auth_error", "spf_valid", "dkim_valid", "dmarc_valid"],
                filter_hint="Filter by customer email address or team_id.",
            ),
            CheckSpec(
                label="Recent bounce / error messages",
                mcp_server="mcp__mongodb-mcp-staging-emailermessages",
                collection="emailer_messages",
                description="Check for bounced or error messages to surface bounce codes.",
                key_fields=["_id", "status", "error", "bounce_code", "sent_at", "contact_id"],
                filter_hint="Filter for status in ('bounced','error') for this team. Limit to recent records.",
            ),
        ],
    ),
}


def build_query_plan(issue_class: str) -> QueryPlan | None:
    return _PLANS.get(issue_class)


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------


def format_mongo_block(
    classification: IssueClassification,
    checks_run: list[str] | None = None,
    verified_facts: list[str] | None = None,
    remaining_unknowns: list[str] | None = None,
    escalation_trigger: str | None = None,
    unavailable: bool = False,
) -> str:
    """Render the private-notes Mongo block."""
    if unavailable:
        return (
            "**Mongo checks:** Mongo MCP unavailable -- answer is not Mongo-verified. "
            "Proceed with Intercom and Glean evidence only; note this gap in private notes."
        )

    lines = ["**Mongo evidence (private -- do not share with customer)**", ""]
    lines.append(f"Issue class: `{classification.issue_class}`")
    lines.append(f"Confidence: {classification.confidence}")
    if classification.matched_signals:
        lines.append(f"Signals matched: {', '.join(classification.matched_signals[:5])}")
    lines.append("")

    lines.append("Mongo checks run:")
    for c in (checks_run or []):
        lines.append(f"  - {c}")
    if not checks_run:
        lines.append("  (none run)")
    lines.append("")

    lines.append("Verified Mongo-backed facts:")
    for f in (verified_facts or []):
        lines.append(f"  - {f}")
    if not verified_facts:
        lines.append("  (none yet)")
    lines.append("")

    lines.append("Remaining unknowns:")
    for u in (remaining_unknowns or []):
        lines.append(f"  - {u}")
    if not remaining_unknowns:
        lines.append("  (none identified)")
    lines.append("")

    lines.append(f"Escalation trigger: {escalation_trigger or 'none -- continue with current evidence'}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--question", required=True, help="Customer issue description.")
    parser.add_argument("--team-id", help="Apollo team ID (for Mongo filter hints).")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    classification = classify_issue(args.question)
    plan = build_query_plan(classification.issue_class)

    if args.json:
        out: dict = {
            "classification": asdict(classification),
            "query_plan": (
                {
                    "issue_class": plan.issue_class,
                    "rationale": plan.rationale,
                    "checks": [asdict(c) for c in plan.checks],
                }
                if plan
                else None
            ),
        }
        if args.team_id:
            out["team_id"] = args.team_id
        print(json.dumps(out, indent=2))
        return 0

    print(f"Issue class:      {classification.issue_class}")
    print(f"Trigger Mongo:    {classification.trigger_mongo}")
    print(f"Confidence:       {classification.confidence}")
    print(f"Matched signals:  {', '.join(classification.matched_signals) or '(none)'}")
    if plan:
        print(f"\nQuery plan — {plan.rationale}\n")
        for i, check in enumerate(plan.checks, 1):
            print(f"  {i}. [{check.label}]")
            print(f"     MCP server: {check.mcp_server}")
            print(f"     Collection: {check.collection}")
            print(f"     Fields:     {', '.join(check.key_fields)}")
            if check.filter_hint:
                print(f"     Filter:     {check.filter_hint}")
    else:
        print("\nNo query plan available for this issue class.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
