---
name: oncall-daily-pending-digest
description: Post a team's daily digest of pending Jira incidents, PagerDuty alerts, and unanswered Slack asks. Run via /apollo-eng:oncall-daily-pending-digest.
disable-model-invocation: true
---

# Daily On-Call Pending Digest

Post one concise Slack message that mentions the current primary on-call DRI and lists the team's outstanding Jira incidents, unacknowledged PagerDuty incidents, and unanswered cross-functional Slack threads.

## Usage

```text
/apollo-eng:oncall-daily-pending-digest <team-key>
/apollo-eng:oncall-daily-pending-digest <team-key> --dry-run
/apollo-eng:oncall-daily-pending-digest <team-key> --pd-schedule-id <id> --delivery-channel-id <id>
```

`<team-key>` is the team's `name` in `apollo-dev-teams.yml`. Optional overrides:

- `--pd-schedule-id <id>`: primary PagerDuty schedule.
- `--pd-service-id <id>`: PagerDuty service; repeat for multiple services.
- `--high-priority-service-id <id>`: PagerDuty service included in the query and rendered first as customer-impacting; repeat as needed.
- `--delivery-channel-id <id>`: destination Slack channel.
- `--xfn-channel-id <id>`: Slack channel scanned for unanswered asks.
- `--team-usergroup-id <id>`: Slack user group mentioned beside the DRI.
- `--jira-impacted-team <value>`: Jira Impacted Team value.
- `--lookback-days <days>`: Slack lookback, default `14`.
- `--due-days <days>`: due-soon threshold, default `7`.
- `--dry-run`: render without posting.

For the original Pricing and Packaging backend setup:

```text
/apollo-eng:oncall-daily-pending-digest growth-pricing-and-packaging-be \
  --pd-schedule-id P0CL0M9 \
  --pd-service-id PU8KTK2 \
  --high-priority-service-id P13OCNA \
  --team-usergroup-id S09BZ0YCZBL
```

Scheduled routines must include the team key and any overrides needed for deterministic resolution.

## Required Access

Before collecting data, identify tools by capability rather than requiring one fixed MCP prefix:

- **Atlassian/Jira MCP (required):** a tool ending in `__searchJiraIssuesUsingJql`. Use read-only JQL searches only.
- **Slack MCP or Claude.ai Slack connector (required):** channel/thread search and read, reaction data, user lookup, and `slack_send_message`. A dry run does not need send permission.
- **PagerDuty MCP or Claude.ai PagerDuty connector (required):** service/schedule discovery, `list_oncalls`, and `list_incidents`.
- **GitHub repository read access (required outside a `leadgenie` checkout):** use the runtime's GitHub API/tool, a GitHub MCP file-reading tool, or authenticated `gh api` access to read `apolloio/leadgenie/apollo-dev-teams.yml` from the default branch.
- **GitHub PR review access (optional):** authenticated `gh pr view` improves Slack-thread classification for PR review asks. Skip that signal if it is unavailable.

Do not silently omit a required source. If a required connector is missing or unauthorized, report it and stop before posting. Do not repeatedly retry `401` or `403` responses.

## Resolve Team Configuration

1. Resolve the canonical team configuration without assuming the current workspace is `leadgenie`:
   - If the current workspace contains `apollo-dev-teams.yml`, read it locally.

   - Otherwise, use the runtime's GitHub API/tool to request `GET /repos/apolloio/leadgenie/contents/apollo-dev-teams.yml`. Parse a raw response as YAML; if the API returns JSON, base64-decode its `content` field first.

   - If no suitable GitHub API tool is available, run this read-only command and parse its YAML output in memory:

     ```bash
     gh api repos/apolloio/leadgenie/contents/apollo-dev-teams.yml \
       -H 'Accept: application/vnd.github.raw+json'
     ```

   - Never cache or copy the file into this plugin; each run should use the current canonical configuration. If local and remote reads both fail, report that GitHub access to `apolloio/leadgenie` is required and stop before posting.
1. Select the exact `teams[].name == <team-key>` entry. Never guess between partial matches.
1. Build the roster from `members[]`, using `name`, `email`, and normalized `github` handles.
1. Resolve defaults, with explicit flags taking precedence:
   - XFN channel: `team_slack_channel_id`.
   - Delivery channel: `pr_review_channel_id`, then `team_slack_channel_id`.
   - Team user group: `team_slack_usergroup_id`. Do not confuse this with `on_call_usergroup_name`; if the caller wants the on-call group mentioned, resolve it through Slack or pass its ID explicitly.
   - Jira Impacted Team: `jira_impacted_team`.
   - PagerDuty services: `pagerduty.service_name`, `pagerduty.pagerduty_high_priority.service_name`, and `pagerduty.pagerduty_low_priority.service_name`, deduplicated and resolved to service IDs through PagerDuty. Ignore missing names.
1. Resolve the primary PagerDuty schedule. Prefer `--pd-schedule-id`. Otherwise search schedules using the team name, description, PagerDuty service names, and `on_call_usergroup_name`; accept only one clearly matching primary schedule. If none or multiple remain, report the candidates and require an override. Never post after an ambiguous schedule match.
1. Resolve the current on-call segment at `now`, then map the DRI to a Slack user by roster email or name. Fall back to plain text if Slack user resolution fails.

Print a compact resolution summary before data collection when running interactively. Include the team key, delivery/XFN channel IDs, Jira Impacted Team, PagerDuty schedule ID, and service IDs so the user can spot a bad match.

## Collect Outstanding Items

Run independent read-only queries concurrently when the tool surface permits.

### Jira

Search the `INCIDENT` project for the selected Impacted Team. Escape the configured value as a JQL string.

Untriaged snapshot:

```text
project = INCIDENT
AND "Impacted Team[Dropdown]" = "<jira-impacted-team>"
AND status = Reported
ORDER BY created ASC
```

Always render this section. List the oldest 10 with linked issue key, summary, and priority. If more exist, add an overflow count and a link to the encoded JQL search. If none exist, render `None — backlog clear. :white_check_mark:`.

Past-due and due-soon snapshot:

```text
project = INCIDENT
AND "Impacted Team[Dropdown]" = "<jira-impacted-team>"
AND statusCategory != Done
AND duedate <= <due-days>d
ORDER BY duedate ASC
```

Split results into `Past due` and `Due within <due-days> days` under one section. Link every issue and include summary, due date, assignee or `unassigned`, and priority. Omit this section when empty.

### PagerDuty

List incidents for all resolved service IDs with `status: ["triggered"]` and no `since` or `until`. `triggered` is the current unacknowledged state; exclude `acknowledged` and `resolved` incidents.

Render high-priority service incidents first. Link every incident and include incident number, title, creation time, and assignee or `unassigned`. Omit empty PagerDuty sections.

### Slack

Read the XFN channel over the lookback window with a response format that includes replies and reactions. Keep messages that make a concrete request of the team, a team member, or the team user group. Exclude bots, announcements without an ask, and requests clearly owned by another team.

Treat a request as handled when any selected-team roster member:

- posts a substantive reply;
- adds a checkmark-style reaction to the parent or a reply (`white_check_mark`, `heavy_check_mark`, or a reaction name containing `check` or `approved`); or
- approves a linked `github.com/apolloio/<repo>/pull/<number>` PR, when authenticated `gh` access is available.

Only threads with none of those signals are pending. Link every pending thread and include a short summary, author, and date. Omit this section when empty. Favor precision over recall because false-positive daily pings train teams to ignore the digest.

## Compose And Send

Use this shape, omitting conditional sections when empty:

```text
:wave: *Daily on-call check-in* — <@DRI_SLACK_ID or DRI_NAME> (Primary, TEAM_DESCRIPTION) [ / <!subteam^TEAM_USERGROUP_ID>]

<high-priority PagerDuty section>

:jira: *Untriaged Jira (N):*
<bullets or clear line>

<past-due / due-soon Jira section>

<other PagerDuty section>

<pending XFN threads section>

<optional unresolved-DRI note>
```

Use Slack-compatible links and emoji. Keep the message terse and do not explain the methodology. Make the DRI mention and team-usergroup mention conditional so unresolved IDs never render as broken mentions.

Unless `--dry-run` is present, send directly to the resolved delivery channel without a confirmation gate. This direct-send behavior supports unattended schedules. If sending fails, surface the error clearly in the run output; never imply delivery succeeded.

## Guardrails

- Perform only read operations in Jira and PagerDuty.
- Post exactly one new Slack message; do not reply, edit, or react elsewhere.
- Never guess unresolved channel, schedule, service, or team identifiers.
- Do not apply backend/frontend exclusions globally. Use only evidence that the request belongs to another team.
- Treat PagerDuty as all-time current state; apply the lookback only to Slack.
