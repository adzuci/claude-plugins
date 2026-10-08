---
name: oncall-weekly-pending-digest
description: Post a team's shared weekly status of outstanding on-call work. Run via /apollo-eng:oncall-weekly-pending-digest.
disable-model-invocation: true
---

# Weekly On-Call Pending Digest

Post the team's full outstanding-work status to its resolved Slack delivery channel. This is
the shared weekly counterpart to the new-work daily DMs.

## Usage

```text
/apollo-eng:oncall-weekly-pending-digest <team-key>
/apollo-eng:oncall-weekly-pending-digest <team-key> --dry-run
/apollo-eng:oncall-weekly-pending-digest <team-key> --pd-schedule-id <id> --delivery-channel-id <id>
```

Supported overrides are `--pd-schedule-id`, repeatable `--pd-service-id`, repeatable
`--high-priority-service-id`, `--delivery-channel-id`, `--xfn-channel-id`,
`--on-call-usergroup-id` (or legacy `--team-usergroup-id`), `--jira-impacted-team`,
`--lookback-days`, `--due-days`, and `--dry-run`. The default Slack lookback is 14 days and
the due-soon threshold is 7 days.

Read [the shared workflow](../oncall-daily-pending-digest/references/shared-workflow.md)
before collecting or sending.

## Weekly Scope And Delivery

Resolve the delivery channel from `--delivery-channel-id`, then `team_slack_channel_id`, then
`pr_review_channel_id`. If it cannot be resolved exactly, stop before posting. Resolve all
clear primary schedules to show current primary DRI mentions; an unresolved DRI is a logged
coverage gap, not a delivery failure.

Unless `--dry-run` is present, post exactly one message to the delivery channel without a
confirmation gate. When every section is empty, post nothing and report the skip in the run
log. In a dry run, render the message and destination without posting or
triggering Pantheon.

## Collect Outstanding Items

- **Untriaged Jira:** all selected-team `status = Reported` incidents, oldest first.
- **Jira deadlines:** selected-team non-Done incidents due on or before the configured
  threshold, split into Past due and Due soon, due-date order.
- **PagerDuty:** current triggered incidents for resolved services under the shared bounded
  query rules; show high-priority service results first.
- **Pending XFN threads:** all still-unaddressed concrete asks in the configurable 14-day
  lookback.

Build Pantheon trigger candidates from displayed untriaged and deadline Jira incidents using
the shared safeguards. Do not render Pantheon PRs in the weekly digest, even though their
existence prevents duplicate Pantheon triggering.

## Message Contract

Use Slack mrkdwn. Begin with:

```text
:wave: *Weekly On-Call Status* — <comma-separated primary DRI mentions or "DRI unavailable"> (Primary, TEAM_DESCRIPTION) [ / <!subteam^ON_CALL_USERGROUP_ID>]
```

Then conditionally render, with one blank line between sections:

```text
:jira-ticketed: *Untriaged tickets (N):*
• <JIRA_URL|INCIDENT-NUMBER> — <summary> — <priority> [— <SLACK_PERMALINK|Pantheon thread>]

:speech_balloon: *Pending XFN threads (N):*
• <SLACK_PERMALINK|summary> — <author>

:calendar: *Jira deadlines*
*Past due (N):*
• <JIRA_URL|INCIDENT-NUMBER> — <summary> — <priority> [— <SLACK_PERMALINK|Pantheon thread>]

*Due soon (N):*
• <JIRA_URL|INCIDENT-NUMBER> — <summary> — <priority> [— <SLACK_PERMALINK|Pantheon thread>]

<PagerDuty heading (N)>
• <PAGERDUTY_URL|#NUMBER> — <title>
```

Show at most three items in every list while preserving full counts in headings. Omit every
zero-count section/bucket and never add `+ N more` or `view all` rows. Do not include
PagerDuty coverage, DRI-resolution, or Pantheon-thread-lookup diagnostics in the channel
message; retain them in run logs.
