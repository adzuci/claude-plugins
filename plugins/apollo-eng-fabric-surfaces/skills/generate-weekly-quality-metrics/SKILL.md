---
name: generate-weekly-quality-metrics
description: Generate the Fabric Surfaces weekly quality metrics Slack report. Activate when user asks to generate fabric surfaces weekly quality metrics, fabric surfaces quality metrics, weekly eng quality report, or posts a Slack thread link for the weekly quality report.
---

# Fabric Surfaces Weekly Engineering Quality Metrics Report

Generate a formatted Slack message with a 7-day snapshot of Fabric Surfaces engineering quality metrics (breached SLAs, open incidents, about-to-breach) using Jira data.

## Prerequisites (MANDATORY)

Before doing anything else, verify these are available:

1. **Atlassian/Jira MCP** — required for all incident data. Check for any tool whose name ends in `__searchJiraIssuesUsingJql` (the prefix varies by how the user named their Atlassian MCP server: commonly `mcp__atlassian__…` for local installs or `mcp__claude_ai_Atlassian__…` for claude.ai installs). If no such tool is available, stop and tell the user:

   > ":warning: **Atlassian MCP is not connected.** This skill requires the Atlassian MCP to query Jira incidents. Please connect it via `/mcp` and try again."
   >
   > Use whichever matching tool name is present in subsequent steps.

1. **Slack MCP** — optional. If any tool whose name ends in `__slack_send_message` is available (e.g., `mcp__claude_ai_Slack__slack_send_message`), use it to post directly. Otherwise, output the message in a code block for the user to copy-paste.

## When to Activate

- User says "generate fabric surfaces weekly quality metrics", "fabric surfaces quality metrics", or "weekly eng quality report"
- User provides a Slack thread link with a request to post the weekly report

## Inputs

- **Slack thread link** (optional): URL like `https://apolloio.slack.com/archives/CHANNEL_ID/pTIMESTAMP?thread_ts=PARENT_TS&cid=CHANNEL_ID`. If provided and Slack MCP is available, the message is posted as a reply in that thread.

## Execution Steps

### Step 1: Compute date range

- `end_date` = today
- `start_date` = today - 7 days
- Format as `Mon DD, YYYY` (e.g., `Apr 13, 2026`)
- Header date range: `<start_date> to <end_date>` (e.g., `Apr 6, 2026 to Apr 13, 2026`)

### Step 2: Run Jira queries in parallel

Use the available `…__searchJiraIssuesUsingJql` tool with `cloudId: "apollopde.atlassian.net"` and these queries. Run all four in parallel.

**Note on fields**:

- Severity: `customfield_10053` (values: `SEV-2`, `SEV-3`, `SEV-4`)
- Impacted Team: `customfield_10114` (value: `Fabric Surfaces`)
- MTTR SLA: `customfield_13244` / JQL field `"MTTR SLA"` (values: `IN PROGRESS`, `BREACHED`, `MET`)
- MTTA SLA target: `customfield_12510` / JQL field `"SLA MTTA Target Date"` (datetime; computed by Time to SLA plugin)
- Status category change: `statuscategorychangedate` (datetime; when the ticket last moved between To Do / In Progress / Done — used as a proxy for ack time)
- Fields to request: `["summary", "customfield_10053", "customfield_12510", "duedate", "status", "statuscategorychangedate", "created"]`
- Use `responseContentFormat: "markdown"` and `maxResults: 50`

**Query A — MTTR Breached (currently open):**

```
project = "INCIDENT" AND "Impacted Team" = "Fabric Surfaces" AND "MTTR SLA" = "BREACHED" AND statusCategory != Done ORDER BY created DESC
```

**Query B — MTTA breach candidates (target passed, ticket still open):**

```
project = "INCIDENT" AND "Impacted Team" = "Fabric Surfaces" AND "SLA MTTA Target Date" < now() AND statusCategory != Done ORDER BY created DESC
```

For each candidate, determine breach state by comparing the most recent `status: Reported → *` transition (from changelog) against `SLA MTTA Target Date`. The full algorithm is in Step 3.

**Query B' — Open tickets WITHOUT `SLA MTTA Target Date` (surfaced for manual check; Jira hasn't populated the field):**

```
project = "INCIDENT" AND "Impacted Team" = "Fabric Surfaces" AND statusCategory != Done AND "SLA MTTA Target Date" is EMPTY ORDER BY created DESC
```

**Query C — All Open Incidents (for count by severity):**

```
project = "INCIDENT" AND "Impacted Team" = "Fabric Surfaces" AND statusCategory != Done ORDER BY created DESC
```

**Query D — About to Breach (next 7 days):**

```
project = "INCIDENT" AND "Impacted Team" = "Fabric Surfaces" AND statusCategory != Done AND due >= "0" AND due <= "7d" ORDER BY duedate ASC
```

### Step 3: Compute MTTA breaches (Jira changelog algorithm)

MTTA treats the clock as restartable — if a ticket is reopened back to `Reported` status, the MTTA SLA restarts and must be met again. The algorithm reflects that.

For each ticket in Query B:

1. Fetch its changelog via the available `…__getJiraIssue` tool with `expand: "changelog"` and `fields: ["customfield_12510", "status"]`.
1. Walk `changelog.histories` chronologically and identify:
   - `latest_reported_at` = timestamp of the **last** `status` change where `toString == "Reported"`. If none, use the ticket's `created` timestamp (it was created in Reported).
   - `latest_ack_at` = timestamp of the **first** `status` change where `fromString == "Reported"` **that occurs after** `latest_reported_at`. If none exists, the ticket is still in Reported.
1. Compare to current `SLA MTTA Target Date`:
   - If `latest_ack_at` is missing (still in Reported) AND target has passed → **breached** (actively breaching).
   - Else if `latest_ack_at > SLA MTTA Target Date` → **breached** (late ack after most recent restart).
   - Else → **not breached** (ack was on time for the most recent MTTA cycle).

> Why this is the right rule: Jira's Time-to-SLA plugin restarts the MTTA timer whenever the ticket re-enters `Reported`. Example: INCIDENT-28072 was ack'd in 6 min initially, but automation re-reported it when the Impacted Team changed. The clock restarted, and the second ack took 6 days → Jira shows it as breached. Naively taking the first-ever ack would miss this.
>
> Conversely, a ticket that goes `Reported → Triage → Mitigation → Done → Triage` (reopen from Done, not Reported) does NOT restart MTTA — the `Done → Triage` transition is ignored because the last `→ Reported` step was the original creation. Example: INCIDENT-27961.

**Handling tickets with null `SLA MTTA Target Date` (Query B'):**

Do not attempt to compute breaches for these — local business-day math is less accurate than Jira's own working-hour calendar and can produce false positives. Instead, skip them from the automated breach count and surface them to the user as a note for manual review, e.g.:

> ⚠️ N open ticket(s) have no `SLA MTTA Target Date` set and were excluded from automated MTTA check. Please spot-check: \<list of keys>.

Typically this list is empty; it only becomes non-empty if the plugin fell behind backfilling a ticket.

### Step 4: Count open incidents by severity

From Query C results, count tickets per severity value. Only include severities with at least one ticket in the output.

### Step 5: Format the Slack message

Use this exact format:

```
:hammer_and_wrench: *Weekly Fabric Surfaces Engineering Quality Metrics – <start_date> to <end_date>*

Hey team! :wave: Here's this week's snapshot of our eng quality signals:

• *Breached Incidents (Missed SLA)*
    ◦ *MTTR*: <MTTR_RESULT>
    ◦ *MTTA*: <MTTA_RESULT>
• *Open Incidents*
    ◦ <TOTAL> currently open
        ▪︎ <X> SEV-2
        ▪︎ <Y> SEV-3
        ▪︎ <Z> SEV-4
    ◦ :link: *<https://apollopde.atlassian.net/issues/?filter=11702|Fabric Surfaces Open Production Incidents>*
• *About-to-Breach (next 7 days)*
    ◦ <ABOUT_TO_BREACH>

__

:blue_book: *MTTA Playbook Reminder* – How to keep our MTTA signal clean
• *Step 1:* Once you've reviewed the incident and confirmed it's valid, move it from `Reported` → `Triage in Progress`
    ◦ :stopwatch: This *stops the MTTA timer* — it tells the team you're actively looking into it. No need to wait until you're fixing it.
• *Step 2:* After triaging (i.e. you've assessed severity and scope), move it to `Prioritized`
    ◦ :spiral_calendar_pad: This means the issue is now queued or scheduled for resolution.

cc: <!subteam^S06M2L5DGDR> <@U02SQFD1F5J>
```

> Note: the lone `__` line between About-to-Breach and the MTTA Playbook Reminder is an intentional Slack section divider (renders as a thin horizontal line). Keep it in the posted message.

**Placeholder rules:**

- `<MTTR_RESULT>`: If Query A returned no tickets → `None :large_green_circle:`. Otherwise → `N ticket(s) :red_circle:` followed by a newline-separated nested bulleted list of `<TICKET_KEY|SUMMARY>` links (each on a new deeply-indented line with `▪︎`, 8 spaces in).
- `<MTTA_RESULT>`: Same format as MTTR but based on Step 3 output. Use `:red_circle:` when breached, `:large_green_circle:` when none.
- `<TOTAL>`: Total count of open tickets from Query C.
- `<X>`, `<Y>`, `<Z>`: Per-severity counts. Omit the line entirely if count is 0 for that severity. Include SEV-0/SEV-1 lines only if they have counts.
- `<ABOUT_TO_BREACH>`: If Query D returned no tickets → `None :large_green_circle:`. Otherwise → `N incident(s) :large_yellow_circle:` with a nested bulleted list below:
  ```
  ◦ N incident(s) :large_yellow_circle:
      ▪︎ <TICKET_KEY|SUMMARY> (due <DUEDATE>)
  ```

**Ticket link format:** Use `<https://apollopde.atlassian.net/browse/TICKET_KEY|TICKET_KEY>` for each issue reference.

### Step 6: Post to Slack or output for copy-paste

**If a Slack thread link is provided AND a `…__slack_send_message` tool is available:**

1. Parse the URL:
   - Channel ID: segment after `/archives/` (e.g., `C06HG89A6S2`)
   - Thread timestamp: use `thread_ts` query param if present; otherwise convert `pTIMESTAMP` → Slack `ts` format (e.g., `p1776075640216289` → `1776075640.216289`)
1. Call the matching `…__slack_send_message` tool with `channel_id`, `thread_ts`, and `message` = the formatted report.
1. Return the posted message link to the user.

**If no Slack thread link is provided OR Slack MCP is unavailable:**

- Output the formatted message inside a code block so the user can copy-paste into Slack manually.
- If Slack MCP is unavailable but a thread link was provided, tell the user: "Slack MCP is not connected, so here's the message for you to copy-paste."

## Example Output

```
:hammer_and_wrench: *Weekly Fabric Surfaces Engineering Quality Metrics – Apr 6, 2026 to Apr 13, 2026*

Hey team! :wave: Here's this week's snapshot of our eng quality signals:

• *Breached Incidents (Missed SLA)*
    ◦ *MTTR*: None :large_green_circle:
    ◦ *MTTA*: None :large_green_circle:
• *Open Incidents*
    ◦ 2 currently open
        ▪︎ 1 SEV-2
        ▪︎ 1 SEV-4
    ◦ :link: *<https://apollopde.atlassian.net/issues/?filter=11702|Fabric Surfaces Open Production Incidents>*
• *About-to-Breach (next 7 days)*
    ◦ None :large_green_circle:

:blue_book: *MTTA Playbook Reminder* – How to keep our MTTA signal clean
• *Step 1:* Once you've reviewed the incident and confirmed it's valid, move it from `Reported` → `Triage in Progress`
    ◦ :stopwatch: This *stops the MTTA timer* — it tells the team you're actively looking into it. No need to wait until you're fixing it.
• *Step 2:* After triaging (i.e. you've assessed severity and scope), move it to `Prioritized`
    ◦ :spiral_calendar_pad: This means the issue is now queued or scheduled for resolution.

cc: <!subteam^S06M2L5DGDR> <@U02SQFD1F5J>
```

## Notes & Limitations

- **MTTA breach detection**: Uses Jira's `SLA MTTA Target Date` (computed by the Time to SLA plugin, linked by Bruno to SEV-2/3/4) compared against the changelog's most-recent `Reported → *` transition. This correctly handles clock restarts when a ticket is re-reported. Tickets where the field is null are skipped from automated counting and surfaced to the user for manual review.
- **MTTR breach detection**: Uses `"MTTR SLA" = "BREACHED"` which is computed by the Time to SLA plugin. Has a mild staleness issue (status only updates when a ticket is opened), but works reliably in practice since oncall engineers regularly open their tickets.
- **Alert Hygiene section**: Deliberately skipped — add it manually or extend the skill later.
- **Static content**: The MTTA Playbook Reminder block is intentionally identical every week.
