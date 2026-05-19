# Preflight — Setup, Configuration, and Verification

Run this file before using the GTM system for the first time, after changing connectors, or when troubleshooting. Once preflight passes, use `ROUTER.md` for all runtime task routing.

This file does not contain sales methodology, pipeline architecture, or execution logic. For architecture context, read `SKILL.md`. For runtime routing, read `ROUTER.md`.

---

## What This System Does

This is your sales operating system. It connects to your email, calendar, Slack, and Apollo account and does three things:

**Inbox triage.** Every morning and evening, it reads your unread email, checks your calendar for overlapping meetings, pulls context from Slack deal channels, and classifies each thread. Sales threads get a drafted reply. Everything else gets categorized. The results land in a Slack DM organized by what needs action, what to watch, and what's just informational.

**Sales email processing.** When you paste a sales email thread, it analyzes the deal context, figures out the right move (reply, escalate, wait, nudge, clarify), and drafts a response grounded in what the buyer actually said. It uses Apollo's value framework and your deal stage to shape the message. It won't invent claims or over-commit on your behalf.

**Post-call follow-up.** After a discovery call, demo, or working session, paste the transcript or your notes. It extracts the pain, next steps, and deal state, then writes a follow-up email tied to what was actually discussed. Every claim in the email traces back to something said on the call.

**What it will never do:**
- Send an email. It creates drafts. You review and send.
- Mark emails as read. Your inbox stays exactly as it was.
- Post to a shared Slack channel without confirming with you first.
- Make up information. If it doesn't have a source, it won't assert it as fact.

---

## Required Connectors

The GTM system executes through MCP connectors. Core triage and email processing require Gmail, Google Calendar, and Slack. Other connectors extend capability but are not required for the primary workflows.

| Connector | Required For | Status |
|---|---|---|
| Gmail | Inbox triage, GEN-SE email processing, follow-up drafts | **Required** |
| Google Calendar | Triage context (meeting overlap, timing), scheduling | **Required** |
| Slack | Triage summary delivery, deal channel posts, nudges, DMs | **Required** |
| Apollo MCP | Contact enrichment, account context, sequence management | Optional (enriches triage context) |
| Google Drive | Champion one-pagers, deal summaries, exported artifacts | Optional |
| Notion | Documentation, deal room content | Optional |
| Granola | Meeting transcript retrieval for follow-up engine | Optional |

---

## Configuration

The inbox triage orchestrator and follow-up engine require identity and delivery configuration. Fill in these values once; they persist across sessions in the orchestrator files.

### Required Configuration Fields

```yaml
seller_email: "{{AUTO_DETECTED}}"        # Your work email (detected from Gmail)
seller_domains: ["{{AUTO_DETECTED}}"]     # Your company's email domain (detected from Gmail)
internal_domains: ["{{AUTO_DETECTED}}"]   # Alias domains used by colleagues (detected from Calendar)
slack_user_id: "{{AUTO_DETECTED}}"        # Your Slack member ID (detected from Slack profile)
timezone: "{{AUTO_DETECTED}}"             # Your timezone (detected from Slack/Calendar)
```

These values are auto-detected during the connection verification routine below. The system pulls your email from Gmail, your Slack ID and timezone from your Slack profile, and infers internal alias domains from calendar organizer emails. You confirm or adjust before anything runs.

### Where Configuration Lives

These values are consumed by two files:

1. **`orchestrators/inbox-triage.md`** — Config block near the top. Replace all `{{PLACEHOLDER}}` markers with the confirmed values.
2. **`gense/gense.md`** — Seller identity config block. Uses the same `seller_email`, `seller_domains`, and `internal_domains` values.

The follow-up engine (`orchestrators/followup-engine.md`) inherits seller identity from the triage orchestrator when called from a triage run. When called standalone, pass seller_email as context.

### Auto-Detection Routine

During preflight, the system detects configuration automatically:

1. **seller_email:** Call `gmail_get_profile`. Use the returned `emailAddress`.
2. **seller_domains:** Extract domain from seller_email (everything after @).
3. **internal_domains:** Scan calendar events for the next 7 days. Collect unique domains from organizer/creator emails. Filter to domains that appear 2+ times and are not the seller_domain. Present candidates to the user for confirmation.
4. **slack_user_id:** Call `slack_search_users` with the seller_email. Use the returned `user_id`.
5. **timezone:** Use the timezone from the Slack profile (or Calendar settings as fallback).

After detection, present all values to the user for confirmation before proceeding. The user can accept, adjust, or add missing domains.

---

## Connection Verification Routine

When the user says "run preflight," "verify connections," or "check setup," execute this routine:

### Step 1: Gmail

Call `gmail_search_messages` with query `is:inbox newer_than:1d` and `maxResults: 3`.

- **PASS:** Returns at least 1 message with headers visible.
- **FAIL:** No results or authentication error. Remediation: verify Gmail connector is installed and authenticated in Cowork settings.

### Step 2: Google Calendar

Call `gcal_list_events` for today and tomorrow using the configured timezone.

- **PASS:** Returns event list (even if empty, the call succeeds).
- **FAIL:** Authentication error or no calendar access. Remediation: verify Google Calendar connector is installed. Check that the primary calendar is accessible.

### Step 3: Slack

Call `slack_send_message` to the configured `slack_user_id` (DM to self) with the message: `[apollo-gtm-preflight] Connection verified.`

- **PASS:** Message posts successfully and returns a message link.
- **FAIL:** Authentication error, invalid user ID, or permission denied. Remediation: verify Slack connector is installed. Confirm the slack_user_id is correct (Settings > Profile > ... > Copy Member ID).

### Step 4: Apollo MCP (Optional)

Call `apollo_users_api_profile` to verify the Apollo API connection.

- **PASS:** Returns user profile data.
- **SKIP:** If Apollo MCP is not connected, skip this step. Note: "Apollo MCP not connected. Triage will run without contact enrichment."
- **FAIL:** Authentication error. Remediation: verify Apollo connector is installed and API key is valid.

### Reporting

After all steps, report results in this format:

```
Preflight Results
-----------------
Gmail:    PASS / FAIL [detail]
Calendar: PASS / FAIL [detail]
Slack:    PASS / FAIL [detail]
Apollo:   PASS / FAIL / SKIP [detail]

Configuration (auto-detected):
  seller_email:    [from Gmail]
  seller_domains:  [from email domain]
  internal_domains:[from calendar scan]
  slack_user_id:   [from Slack profile]
  timezone:        [from Slack/Calendar]

Status: READY / NOT READY [list failures]
```

If any required connector fails (Gmail, Calendar, or Slack), status is NOT READY. Do not proceed to triage until all required connectors pass.

---

## Smoke Test

After preflight passes, run a minimal triage to verify end-to-end pipeline execution.

### Procedure

1. Run inbox triage in PM mode with a narrow window: `newer_than:2h` instead of the full PM window.
2. Expected behavior:
   - Gmail search returns threads (or zero, which is valid).
   - Calendar context is gathered.
   - Each thread is classified (GEN-SE gate or pipeline gate).
   - Pipeline runs L1 through L4+ on at least one thread (if any exist).
   - Summary is delivered to Slack DM.
3. Verify the Slack summary arrives and contains the expected tiers (ACT/WATCH/FYI).

### Pass Criteria

- All pipeline layers executed without `pipeline_status: failure` (or failures were correctly routed to ACT tier with structured error states).
- Summary was delivered to Slack.
- No emails were sent (drafts only).
- No emails were marked as read.

### Fail Handling

If the smoke test fails:
- Check preflight results first (connector issue?).
- If connectors are healthy, check the failure state from `pipeline-runtime.md` failure paths for the specific layer that broke.
- Report the failure layer and code to the user for debugging.

---

## Action Menu

After preflight and smoke test complete, present the user with an action menu using `AskUserQuestion`. This is the handoff from setup to usage.

**Instruction to model:** Use `AskUserQuestion` with the following options:

```
Question: "You're all set. What would you like to do?"
Header: "Action"
Options:
  - Label: "Run inbox triage"
    Description: "Process your unread email, check calendar and Slack context, draft replies, and deliver a summary to your Slack DM."
  - Label: "Process an email thread"
    Description: "Paste a sales email thread and get a drafted reply grounded in the deal context."
  - Label: "Write a call follow-up"
    Description: "Paste a call transcript or notes and get a follow-up email tied to what was discussed."
  - Label: "Review a deal"
    Description: "Name a deal and get stage validation, MEDDPICC gap analysis, and recommended next actions."
```

**Routing after selection:**
- "Run inbox triage" → Load `ROUTER.md` Path A
- "Process an email thread" → Load `ROUTER.md` Path B. Prompt user: "Paste the email thread here."
- "Write a call follow-up" → Load `ROUTER.md` Path C. Prompt user: "Paste your call transcript, notes, or recording summary."
- "Review a deal" → Load `ROUTER.md` Path D. Prompt user: "Which deal?"
- User types something else → Load `ROUTER.md` Step 1 and classify normally.

This menu also appears at the start of every returning session (see `ROUTER.md` session-start behavior).

---

## Entry Point Hierarchy

After preflight passes, the system uses this file loading order:

| Situation | Load |
|---|---|
| First-time setup or troubleshooting | This file (`PREFLIGHT.md`) |
| Architecture review or full system map | `SKILL.md` |
| Any runtime task (deal work, triage, email, etc.) | `ROUTER.md` (classifies task, loads only needed files) |

`ROUTER.md` is the runtime entry point. `SKILL.md` is the architecture reference. `PREFLIGHT.md` is setup and verification. They do not overlap.
