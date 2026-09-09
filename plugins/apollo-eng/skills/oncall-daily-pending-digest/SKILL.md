---
name: oncall-daily-pending-digest
description: Post a team's daily digest of new and pending Jira incidents, PagerDuty alerts, and unanswered Slack asks. Run via /apollo-eng:oncall-daily-pending-digest.
disable-model-invocation: true
---

# Daily On-Call Pending Digest

Post one concise Slack message that mentions the current primary on-call DRI and lists the team's new and outstanding Jira incidents, unacknowledged PagerDuty incidents, unanswered cross-functional Slack threads, and Pantheon PRs waiting for action.

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
- `--on-call-usergroup-id <id>`: on-call Slack user group mentioned beside the DRI; overrides `on_call_usergroup_name` resolution.
- `--team-usergroup-id <id>`: legacy alias for `--on-call-usergroup-id`; never populate it from `team_slack_usergroup_id`.
- `--jira-impacted-team <value>`: Jira Impacted Team value.
- `--lookback-days <days>`: Slack lookback, default `14`.
- `--due-days <days>`: due-soon threshold, default `7`.
- `--dry-run`: render without posting.

For the original Pricing and Packaging backend setup:

```text
/apollo-eng:oncall-daily-pending-digest growth-pricing-and-packaging-be \
  --pd-schedule-id P0CL0M9 \
  --pd-service-id PU8KTK2 \
  --high-priority-service-id P13OCNA
```

This setup resolves `oncall-xfn-team-pricing-and-packaging` to `S09BZ0YCZBL` through Slack by default.

Scheduled routines must include the team key and any overrides needed for deterministic resolution.

## Required Access

Before collecting data, identify tools by capability rather than requiring one fixed MCP prefix:

- **Atlassian/Jira MCP (required):** tools for JQL search and reading issue details with comments. Keep Jira access read-only; the triggered incident-diagnosis run owns its Jira comment.
- **Slack MCP or Claude.ai Slack connector (required):** channel/thread search and read, message permalinks, reaction data, user and user-group lookup, and `slack_send_message`. A dry run does not need send permission.
- **Pantheon agent trigger (conditional write):** non-dry runs may start up to three missing incident-diagnosis runs through Pantheon's built-in agent-to-agent trigger capability. Trigger only when a displayed untriaged or due-date Jira incident has neither a qualifying record of an existing Pantheon run in its Jira comments nor a qualifying Pantheon Slack thread. An open Pantheon PR is also existing work and must not trigger another run. A failed trigger must not block the digest.
- **PagerDuty MCP or Claude.ai PagerDuty connector (optional enrichment):** service/schedule discovery, `list_oncalls`, and `list_incidents`. Prefer a server-side `service_ids` filter, but support the managed connector's bounded fallback below when that parameter is absent. PagerDuty unavailability must not block the Jira/Slack digest.
- **GitHub repository read access (required outside a `leadgenie` checkout):** use the runtime's GitHub API/tool, a GitHub MCP file-reading tool, or authenticated `gh api` access to read `apolloio/leadgenie/apollo-dev-teams.yml` from the default branch.
- **GitHub PR search access (optional enrichment):** search open Pantheon-authored incident PRs across the `apolloio` organization, then match their Jira incidents to the selected Impacted Team. A search failure must not block the digest.
- **GitHub PR review access (optional):** authenticated `gh pr view` improves Slack-thread classification for PR review asks. Skip that signal if it is unavailable.

Do not silently omit a required source. If Jira, Slack, or GitHub configuration access is missing or unauthorized, report it and stop before posting. Treat any PagerDuty absence, authorization failure, unsupported filter, timeout, or tool error as a non-fatal coverage gap: record one concise note, make no retry, and continue the digest. Do not repeatedly retry `400`, `401`, or `403` responses.

The managed runtime rejects package installation. Never run `pip install`, `npm install`, `apt`, `brew`, or another dependency installer. Do not use Python's third-party `yaml` module. Use the dependency-free extraction command below for the team configuration. Validate PagerDuty access with a narrow service lookup; do not call `get_user_data` or `/users/me`, which returns `400` for the runtime's valid account-level token.

## Resolve Team Configuration

1. Resolve the canonical team configuration without assuming the current workspace is `leadgenie`:
   - If the current workspace contains `apollo-dev-teams.yml`, set `team_config_path` to that file.

   - Otherwise, use authenticated `gh api` to write the current raw file to per-run scratch space, then set `team_config_path` to that file:

     ```bash
     gh api repos/apolloio/leadgenie/contents/apollo-dev-teams.yml \
       -H 'Accept: application/vnd.github.raw+json' \
       > /tmp/apollo-dev-teams.yml
     team_config_path=/tmp/apollo-dev-teams.yml
     ```

     If `gh api` fails, report that GitHub access to `apolloio/leadgenie` is required and stop before posting. Do not install or import a YAML parser as a fallback.

   - Extract only the exact team block from `team_config_path` with tools already present in the managed runtime:

     ```bash
     awk -v target="$team_key" '
       /^  - name: / {
         name = $0
         sub(/^  - name: /, "", name)
         gsub(/^[[:space:]\047\042]+|[[:space:]\047\042]+$/, "", name)
         if (printing && name != target) exit
         if (name == target) { printing = 1; matched = 1 }
       }
       printing { print }
       END { if (!matched) exit 2 }
     ' "$team_config_path"
     ```

     Set `team_key` from the required `<team-key>` argument without interpolating it into the awk program. Treat exit code `2` as an exact-match failure and stop; do not retry with a partial match.

   - Never cache or copy the file into this plugin; `/tmp/apollo-dev-teams.yml` is per-run scratch data. Each run should use the current canonical configuration. If local and remote reads both fail, report that GitHub access to `apolloio/leadgenie` is required and stop before posting.
1. Select the exact `teams[].name == <team-key>` entry. Never guess between partial matches.
1. Build the roster from `members[]`, using `name`, `email`, and normalized `github` handles.
1. Resolve defaults, with explicit flags taking precedence:
   - XFN channel: `team_slack_channel_id`.
   - Delivery channel: `team_slack_channel_id`, then `pr_review_channel_id`.
   - On-call user group: prefer `--on-call-usergroup-id`, with `--team-usergroup-id` accepted as a legacy alias. If both are present, require them to match. Otherwise, when `on_call_usergroup_name` is configured, resolve it to a Slack user-group ID by exact handle or name match. If the field is absent or the lookup has no exact match or is ambiguous, omit the group mention and report why. Never use `team_slack_usergroup_id`; that identifies the general engineering team, not its on-call rotation.
   - Jira Impacted Team: `jira_impacted_team`.
   - PagerDuty services: `pagerduty.service_name`, `pagerduty.pagerduty_high_priority.service_name`, and `pagerduty.pagerduty_low_priority.service_name`, deduplicated and resolved to service IDs through PagerDuty when available. Ignore missing names. If resolution fails, record the short error and continue without PagerDuty incidents.
1. Resolve the primary PagerDuty schedule when PagerDuty is available. Prefer `--pd-schedule-id`. Otherwise search schedules using the team name, description, PagerDuty service names, and `on_call_usergroup_name`; accept only one clearly matching primary schedule. If none or multiple remain, do not guess: record the unresolved reason and continue without a PagerDuty DRI.
1. When a schedule is resolved, resolve the current on-call segment at `now`, then map the DRI to a Slack user by roster email or name. Fall back to plain text if Slack user resolution fails. If the PagerDuty call fails, record the short error and continue with the on-call user-group mention only.

Print a compact resolution summary before data collection when running interactively. Include the team key, delivery/XFN channel IDs, on-call user-group ID or unresolved reason, Jira Impacted Team, PagerDuty schedule ID, and service IDs so the user can spot a bad match.

## Collect Outstanding Items

Run independent read-only queries concurrently when the tool surface permits. Start Jira and Slack collection independently of PagerDuty so a PagerDuty error cannot prevent required-source collection.

### Jira

Search the `INCIDENT` project for the selected Impacted Team. Escape the configured value as a JQL string.

Untriaged incidents:

```text
project = INCIDENT
AND "Impacted Team[Dropdown]" = "<jira-impacted-team>"
AND status = Reported
ORDER BY created ASC
```

Treat a Jira comment as a Pantheon-run record only when it is a current incident-diagnosis result containing both `Classification:` and `Outcome:`, or a legacy `Pantheon Agent - Initial Run Started` or `Pantheon Agent - Retry Run Started` comment. Do not treat a Jira label, arbitrary human comment, or unrelated automation comment as proof of a run.

Render `:jira-ticketed: *Untriaged tickets (N):*`, preserving the full count in the heading but showing at most three incidents ordered oldest first. Omit the section when there are no untriaged incidents.

Past-due and due-soon snapshot:

```text
project = INCIDENT
AND "Impacted Team[Dropdown]" = "<jira-impacted-team>"
AND statusCategory != Done
AND duedate <= <due-days>d
ORDER BY duedate ASC
```

Split results into `Past due` and `Due within <due-days> days` under one section. Show at most the first three issues in each non-empty bucket, ordered by due date ascending. Preserve each bucket's full count in its heading, but do not add overflow rows or `view all` links. Link each displayed issue and include summary, due date, assignee or `unassigned`, and priority. Omit an empty bucket and omit the whole section when both buckets are empty.

Build a deduplicated set of every Jira incident rendered in the untriaged, due-date, and Pantheon PR sections. For each one, search Slack's accessible workspace messages over the configured lookback for the exact issue key or Jira URL, once per issue. Accept a top-level completed incident-diagnosis action that links the exact incident; also accept a legacy top-level announcement ending with `Pantheon will post updates in this thread.` Deduplicate repeated results for the same parent. When one or more valid parents remain, select the most recently active parent (latest reply timestamp, or parent timestamp when it has no replies) and append its permalink as `<SLACK_PERMALINK|Pantheon thread>` wherever the Jira incident is rendered. Render `Pantheon thread not found` only when no valid parent remains. Never discard matching threads merely because more than one exists.

After completing Pantheon PR discovery and the Pantheon-thread lookup, build a deduplicated candidate list from every displayed untriaged and due-date Jira incident, in message order. Exclude any incident linked to an open Pantheon PR. If Pantheon PR discovery failed, do not start a run because the digest cannot establish that a candidate lacks an open Pantheon PR; continue to render the digest and report the coverage gap. Read Jira comments for every remaining candidate. Unless `--dry-run` is present, start an incident-diagnosis run for up to the first three candidates that have neither a Pantheon-run Jira comment nor Pantheon-link evidence. Read [references/pantheon-trigger.md](references/pantheon-trigger.md) before the first trigger. Never retry a failed trigger in the same digest, but continue with other eligible displayed tickets and render one concise kickoff-coverage note. Do not wait for a triggered diagnosis to complete or poll it. In a dry run, do not call Pantheon and report the number of runs that would start.

Link each rendered Jira issue, truncate its one-line summary to 100 characters, and include its required fields. Append its Pantheon-thread result. Do not add an overflow row or `view all` link.

### PagerDuty

PagerDuty is best-effort enrichment. If service, schedule, on-call, or incident collection has already failed, do not retry it. Continue Jira and Slack collection and render one concise note: `PagerDuty coverage unavailable — <short reason>.`

Inspect the available `list_incidents` input schema before calling it. Do not probe the schema by making an unscoped request.

When the tool exposes both `service_ids` and `limit`, query each resolved service ID independently with a bounded, server-side-filtered request equivalent to:

```json
{
  "service_ids": ["<resolved-service-id>"],
  "statuses": ["triggered"],
  "limit": 25
}
```

For service-filtered requests, do not supply `since` or `until`. `triggered` is the current unacknowledged state; exclude `acknowledged` and `resolved` incidents. Follow pagination only for that same service while the response says more records exist, retaining a page size of 25.

After every service-filtered response, verify that each incident's `service.id` equals the requested ID. If the connector accepts `service_ids` but ignores it or returns another service, treat it as the limited connector fallback below.

The managed Claude.ai PagerDuty connector currently omits `service_ids` but exposes both `limit` and `request_scope` values `all`, `assigned`, or `teams`. The `teams` scope means all PagerDuty teams accessible to the connector; it does not mean the selected Apollo team and does not filter to the resolved service IDs. In that environment, make exactly one bounded request:

```json
{
  "request_scope": "teams",
  "statuses": ["triggered"],
  "since": "<now minus 24 hours, RFC 3339 UTC>",
  "limit": 25
}
```

Calculate `since` from the current runtime clock. Never increase this limit, widen the 24-hour window, retry with `request_scope: "all"`, or paginate this response. Verify that the response contains no more than 25 incidents. Retain only incidents whose `service.id` exactly matches a resolved service ID. If the response contains 25 incidents, treat the window as potentially truncated. Never interpret zero retained matches as an all-time clear PagerDuty queue because older triggered incidents are outside this fallback window.

If `list_incidents` lacks `limit`, lacks `request_scope`, or returns more than 25 incidents despite the cap, do not make or retry another incident request and discard an oversized response. Continue with this note: `PagerDuty coverage unavailable — the connector cannot guarantee a bounded incident query.`

If either a service-filtered or fallback `list_incidents` call returns any tool error—including the managed connector rejecting `request_scope: "teams"` for account-level authentication—make no second incident call. Convert the error to `PagerDuty coverage unavailable — the connector could not query team incidents.` and continue composing and posting the Jira/Slack digest. A PagerDuty tool error is never a reason to end the run.

After a valid bounded fallback, continue the digest. Render at most three retained matches under a `Recent PagerDuty incidents (N, last 24 hours)` heading, preserving the full retained count in the heading, then add: `PagerDuty coverage limited to the last 24 hours — the connector checked one page (25 maximum) across its accessible PagerDuty teams and filtered matching services locally.` Do not add an overflow row or `view all` link. If the response hit the limit, append `The connector window may be truncated.` When no matches are retained, omit incident bullets and render only the coverage note. This is an explicit degraded result, not a missing required source and not a reason to stop Jira or Slack collection.

For complete service-filtered results, render high-priority service incidents first. Preserve each PagerDuty section's full incident count in its heading, but show at most three incidents per section and do not add overflow rows or `view all` links. Link each displayed incident and include incident number, title, creation time, and assignee or `unassigned`. Omit empty complete PagerDuty sections.

### Slack

Read the XFN channel over the lookback window with a response format that includes replies and reactions. Keep messages that make a concrete request of the team, a team member, or the team user group. Exclude bots, announcements without an ask, requests clearly owned by another team, and messages directed solely at another bot or agent integration such as `@Apollo Operator`. Keep a message when it also contains a distinct request for the selected team.

Treat a request as handled when any selected-team roster member:

- posts a substantive reply;
- adds a checkmark-style reaction to the parent or a reply (`white_check_mark`, `heavy_check_mark`, or a reaction name containing `check` or `approved`); or
- approves a linked `github.com/apolloio/<repo>/pull/<number>` PR, when authenticated `gh` access is available.

Only threads with none of those signals are pending. Preserve the full pending count in the heading, but show at most three threads and do not add an overflow row or `view all` link. Link each displayed thread and include a short summary, author, and date. Omit this section when empty. Favor precision over recall because false-positive daily pings train teams to ignore the digest.

### GitHub

Search across the `apolloio` organization for open incident PRs authored by the `pantheon-apollo` GitHub App. Include draft PRs because Pantheon opens its PRs as drafts. With authenticated `gh api`, search newest first with a query equivalent to:

```text
GET /search/issues
q=org:apolloio is:pr is:open author:app/pantheon-apollo INCIDENT- in:title
sort=created
order=desc
per_page=50
```

For each result, extract exactly one `INCIDENT-<number>` key from its title; skip a PR with no key or multiple distinct keys. Batch-query Jira for those keys and retain only PRs whose Jira issue has the selected exact Impacted Team value. Complete this discovery before building the Pantheon-thread lookup set so the matched PR incidents are searched too. Continue with the next page only when fewer than three team-matching PRs have been found, stopping at three matches or after 100 GitHub results. Ordering newest first keeps the section focused on the latest agent work waiting for action.

Render this as the final section under `:robot_face: *Pantheon PRs waiting for your action:*`. For each PR, render `<PR_URL|OWNER/REPO#NUMBER>`, its related `<JIRA_URL|INCIDENT-NUMBER>`, the title truncated to 100 characters, the opened date, and that incident's Pantheon-thread result. These links let the on-call DRI take the appropriate action, such as merging or closing the PR, canceling its Pantheon run, or reviewing the underlying incident. Omit the section when no matching PRs exist. If the GitHub or Jira match search fails, do not retry or block the digest; render the final section with one line: `Pantheon PR coverage unavailable — <short reason>.`

## Compose And Send

Formatting is part of the output contract:

- Put each heading on its own line and exactly one blank line between rendered sections.
- Put every Jira incident, pending XFN thread, PagerDuty incident, and Pantheon PR on its own physical line beginning with `• `. Never join multiple items on one line.
- Show at most three items in every list while preserving the full count in its heading.
- Omit every zero-count section and bucket. A source-coverage or unresolved-configuration note may remain when there is no item count.
- Do not put blank lines between items in the same list.
- Under `Jira due dates`, put each bucket heading on its own line, followed immediately by that bucket's incident lines. Put one blank line between the `Past due` and `Due within <due-days> days` buckets.
- Never render a `+ N more` overflow row or `view all` link. The full count in the section or bucket heading is sufficient.
- Put an empty-state or coverage note on its own line below its heading.

Use this literal Slack mrkdwn shape, omitting conditional sections when empty:

```text
:wave: *Daily on-call check-in* — <@DRI_SLACK_ID or DRI_NAME, or "DRI unavailable"> (Primary, TEAM_DESCRIPTION) [ / <!subteam^ON_CALL_USERGROUP_ID>]

:jira-ticketed: *Untriaged tickets (N):*
• <one untriaged Jira incident> — <Pantheon thread result>
• <one untriaged Jira incident> — <Pantheon thread result>

:speech_balloon: *Pending XFN threads (N):*
• <one pending XFN thread>
• <one pending XFN thread>

:calendar: *Jira due dates*
*Past due (N):*
• <one past-due Jira incident> — <Pantheon thread result>
• <one past-due Jira incident> — <Pantheon thread result>

*Due within <due-days> days (N):*
• <one due-soon Jira incident> — <Pantheon thread result>
• <one due-soon Jira incident> — <Pantheon thread result>

<high-priority PagerDuty heading>
• <one high-priority PagerDuty incident>
• <one high-priority PagerDuty incident>

<other PagerDuty heading>
• <one other PagerDuty incident>
• <one other PagerDuty incident>

<optional incomplete PagerDuty coverage note>
<optional unresolved-DRI note>

:robot_face: *Pantheon PRs waiting for your action:*
• <PR_URL|OWNER/REPO#NUMBER> — <JIRA_URL|INCIDENT-NUMBER> — <PR title> — opened <YYYY-MM-DD> — <Pantheon thread result>
• <PR_URL|OWNER/REPO#NUMBER> — <JIRA_URL|INCIDENT-NUMBER> — <PR title> — opened <YYYY-MM-DD> — <Pantheon thread result>
```

Use Slack-compatible links and emoji. Keep the message terse and do not explain the methodology. Make the DRI mention and on-call-usergroup mention conditional so unresolved IDs never render as broken mentions. When present, the Pantheon PR section must be last.

Unless `--dry-run` is present, send directly to the resolved delivery channel without a confirmation gate. This direct-send behavior supports unattended schedules. If sending fails, surface the error clearly in the run output; never imply delivery succeeded.

## Guardrails

- Perform only read operations in Jira and PagerDuty.
- Perform only read operations in GitHub; PR discovery never comments, reviews, labels, closes, or edits a PR.
- Trigger at most three new Pantheon runs, only for displayed untriaged or due-date Jira incidents that are not linked to an open Pantheon PR and have neither a qualifying incident-diagnosis or Pantheon-run Jira comment nor Pantheon-thread evidence. Do not retry a failed trigger in the same digest.
- Never expose, persist, or request Pantheon credentials; agent-to-agent invocation uses the platform-provided authentication.
- Post exactly one new Slack message; do not reply, edit, or react elsewhere.
- Never guess unresolved destination or XFN channel, user-group, schedule, service, or team identifiers. A Pantheon announcement channel may be discovered from an exact content match as described above.
- Do not apply backend/frontend exclusions globally. Use only evidence that the request belongs to another team.
- Treat service-filtered PagerDuty results as all-time current state. Treat the connector fallback as incomplete current-state coverage, state that limitation in the digest, and never infer that an absent incident means the queue is clear. Apply the lookback only to Slack.
