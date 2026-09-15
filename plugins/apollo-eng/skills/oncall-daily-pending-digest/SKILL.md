---
name: oncall-daily-pending-digest
description: DM new unaddressed on-call work to each current primary DRI, with an observer copy. Run via /apollo-eng:oncall-daily-pending-digest.
disable-model-invocation: true
---

# Daily On-Call Pending Digest

Send a concise daily Slack DM for work that is both new in the previous 24 hours and
still unaddressed. This is a notification, not the team's full outstanding-work report;
use `/apollo-eng:oncall-weekly-pending-digest` for that shared status.

## Usage

```text
/apollo-eng:oncall-daily-pending-digest <team-key>
/apollo-eng:oncall-daily-pending-digest <team-key> --dry-run
/apollo-eng:oncall-daily-pending-digest <team-key> --pd-schedule-id <id> --delivery-channel-id <id>
```

Supported overrides are `--pd-schedule-id`, repeatable `--pd-service-id`, repeatable
`--high-priority-service-id`, `--delivery-channel-id`, `--xfn-channel-id`,
`--on-call-usergroup-id` (or legacy `--team-usergroup-id`), `--jira-impacted-team`,
`--lookback-days`, `--due-days`, and `--dry-run`. `--lookback-days` and `--due-days` do
not change the fixed 24-hour daily-new cutoff.

Read [the shared workflow](references/shared-workflow.md) before collecting or sending.

## Daily Scope And Delivery

Set `daily_cutoff` to exactly 24 hours before the runtime clock. Resolve every clearly
matching **primary** PagerDuty schedule unless `--pd-schedule-id` pins one. For each
schedule, resolve the current on-call segment and map its user to Slack. Deduplicate
recipients by Slack user ID.

- Send the same message as a DM to every resolved primary DRI.
- Send one identical observer DM to Slack user `@ryanharrs`; resolve that exact handle to
  a user ID before sending. Do not send an observer duplicate when Ryan is already a DRI.
- When no primary DRI can be resolved, send the message to the resolved delivery channel
  instead, then send Ryan the observer DM.
- A partial schedule-resolution failure does not invoke channel fallback when at least one
  DRI resolved. Record all resolution errors in the run log only.
- In `--dry-run`, render the message and intended recipient IDs without sending or
  triggering Pantheon.

## Collect New Unaddressed Items

Use the shared source rules, but apply these daily filters:

- **Untriaged Jira:** `status = Reported` and `created >= daily_cutoff`; display only
  incidents still in that state.
- **Pending XFN threads:** parent message timestamp is at or after `daily_cutoff` and the
  existing roster reply, qualifying reaction, and linked-PR approval checks find no
  handling signal.
- **PagerDuty:** only triggered incidents whose trigger/creation timestamp is at or after
  `daily_cutoff`. Retain the shared bounded-query and coverage rules.
- **Pantheon PRs:** include all matching open Pantheon incident PRs regardless of age.
  Render at most five, newest first, and preserve the full count in the heading.

Do not query or render Jira Past due or Due soon sections in this daily digest. Build
Pantheon trigger candidates only from displayed daily untriaged Jira incidents; retain the
shared maximum of three non-dry-run starts and all duplicate-work safeguards.

## Message Contract

Use Slack mrkdwn. Begin with:

```text
:wave: *Daily on-call check-in* — <comma-separated primary DRI mentions or "DRI unavailable"> (Primary, TEAM_DESCRIPTION)
```

Then conditionally render, with one blank line between sections:

```text
:jira-ticketed: *New untriaged tickets (N):*
• <JIRA_URL|INCIDENT-NUMBER> — <summary> — <priority> [— <SLACK_PERMALINK|Pantheon thread>]

:speech_balloon: *New pending XFN threads (N):*
• <SLACK_PERMALINK|summary> — <author>

<PagerDuty heading for new triggered incidents (N)>
• <PAGERDUTY_URL|#NUMBER> — <title>

:robot_face: *Pantheon PRs waiting for your action (N):*
• <PR_URL|OWNER/REPO#NUMBER> — <JIRA_URL|INCIDENT-NUMBER> — <PR title> [— <SLACK_PERMALINK|Pantheon thread>]
```

Show at most three Jira, XFN, and PagerDuty items per section. Omit zero-count sections;
never add a `+ N more` row or a `view all` link. Do not include source-coverage,
Pantheon-thread-lookup, or DRI-resolution diagnostics in the Slack message. Keep those in
the run log.
