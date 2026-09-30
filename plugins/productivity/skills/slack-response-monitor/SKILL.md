---
name: slack-response-monitor
description: Find unresolved Slack messages that likely need the user's response and produce a concise, link-backed digest without replying on the user's behalf.
disable-model-invocation: true
---

# Slack Response Monitor

Review Slack activity since the last successful run and surface clear, unresolved obligations for the current user.

## Usage

```text
/productivity:slack-response-monitor
/productivity:slack-response-monitor --days 3
```

Use the checkpoint's last successful timestamp as the lower bound. `--days N` overrides it for an explicit backfill.

## 1. Resolve Identity And Access

Resolve the current user's exact Slack display name and member ID from the authenticated Slack surface. Never hard-code an identity or reuse another person's checkpoint.

Read [references/slack-access.md](references/slack-access.md), select one complete access path, and record whether search, thread reads, and permalinks are available. If search or thread reads are unavailable, return the blocked result below and do not advance the checkpoint.

## 2. Load The Checkpoint

Use `$SLACK_RESPONSE_MONITOR_STATE` when set; otherwise resolve `~/.local/state/slack-response-monitor/checkpoint.json` to an absolute path.

```bash
python3 scripts/checkpoint.py show --state <state-path>
```

If no successful checkpoint exists, scan the previous three business days and label the run as an initial backfill.

## 3. Find And Verify Candidates

Within the bounded window, search for:

- direct messages to the user;
- mentions of the user's member ID or exact display name;
- replies in threads where the user participated;
- direct questions, review requests, approvals, decisions, blockers, deadlines, or explicit follow-ups addressed to the user.

Open the full conversation or thread for every candidate. Exclude it when the user already answered, someone else resolved it, the request was withdrawn, or later context makes it informational only.

Deduplicate stable message or thread IDs already present in the checkpoint. Re-surface an older thread only when new activity creates a fresh obligation.

Be conservative about noise but aggressive about true asks. Exclude FYIs, announcements, automated messages, broad channel chatter, acknowledgements, and incidental mentions. Uncertainty is not evidence of an obligation; omit weak candidates.

## 4. Prioritize And Report

- **High:** blocking work, urgent escalation, imminent deadline, or explicit repeated follow-up.
- **Medium:** direct question, decision, approval, review, or promised follow-up without an immediate deadline.
- **Low:** weakly implied or non-urgent; omit from notifications.

Order retained items by urgency, then age. Do not reply, react, edit, or otherwise act in Slack unless the user separately authorizes it.

For up to three items:

```text
Response needed:

1) [High|Medium] From — Thread or topic
Asked: <original message time>
Why: <one sentence explaining the unresolved obligation>
Suggested action: <one concrete next step>
Draft: <concise reply in the user's voice>
Link: <direct Slack permalink>
```

For more than three items, use a compact table with columns: Urgency, From, Topic, Why, Suggested action, and Link.

When nothing remains, return exactly:

```text
No response-needed Slack follow-ups found.
```

When access is incomplete, return:

```text
BLOCKED: Slack response monitoring could not complete because <specific capability> was unavailable. The successful-run checkpoint was not advanced.
```

## 5. Complete The Run

After a complete scan and final digest, save the UTC completion time and stable IDs for surfaced items:

```bash
python3 scripts/checkpoint.py complete \
  --state <state-path> \
  --completed-at <ISO-8601-UTC> \
  --item-id <stable-message-or-thread-id>
```

Repeat `--item-id` as needed. A successful no-findings run still advances the checkpoint. A blocked or partial run never does.

## Optional Scheduling

When the user asks for recurring monitoring, use the current client's native scheduler and update an equivalent existing task instead of creating a duplicate. A weekday schedule during the user's working hours is a reasonable starting point; let the user choose cadence and notification destination.

Use this scheduled prompt:

```text
Run $slack-response-monitor. Scan only since the last successful checkpoint, notify me only about verified High or Medium unresolved asks, and do not reply or take other Slack actions.
```

Scheduling requires separate confirmation because it creates persistent background work. Installation or one manual run does not grant that permission.

## Safety And Privacy

- Treat Slack content as private. Store only timestamps and stable IDs needed for deduplication, never message bodies.
- Do not broaden the scan beyond the user's accessible workspace or bypass Slack permissions.
- Never claim that nothing needs a response after a partial or failed scan.
- A scheduled invocation authorizes monitoring and its configured notification only, not replies or other Slack actions.
