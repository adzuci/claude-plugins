---
name: okr-report
description: Generate an engineering team OKR status report from Google Drive/Glean data and optional Jira evidence, with optional HTML output. Activate when a manager asks for an OKR report, OKR status, quarterly progress, key results update, HTML OKR report, or says "okr report".
---

# OKR Report

Generate a structured OKR status report for an engineering team by reading the company OKR tracker and, when available, cross-checking related Jira work.

## Arguments

- `html`, `--html`, `format=html`, or "HTML version": generate a standalone HTML version of the report after the evidence audit passes. If the user provides a path, write the HTML there. If no path is provided, create `okr-report-<team>-<period>.html` in the current working directory when file writes are appropriate; otherwise return the HTML in a fenced `html` block.

## Step 0 -- Check Data Access

Check for OKR data access in this order:

1. Google Drive/Sheets tools, if available, for direct spreadsheet reads.
1. Glean MCP tools (`search`, `read_document`, and optionally `chat`). Tool namespace prefixes vary by environment, so match on the tool names rather than an exact MCP namespace.
1. Manual paste from the user.

If no Drive/Sheets or Glean tools are available, ask the user to paste the relevant OKR rows and continue from Step 3. Do not stop solely because Glean is unavailable.

Also check whether Jira/Atlassian tools are available (`searchJiraIssuesUsingJql`, `getJiraIssue`) or whether a `jira` CLI exists. Jira is useful but optional: if it is unavailable, produce a tracker-only report and clearly mark Jira evidence as unavailable.

For operational teams such as DevOps, IT, infrastructure, or support engineering, also check `references/metrics-sources.md` for operational metric sources. These are optional supporting signals; do not block the OKR report if metric sources require access you do not have.

## Step 1 -- Identify Scope

If the user already specified a team, use it. Otherwise ask which team they want a report for.

If the user provided a Google Drive sheet URL, inspect its title, visible quarter, tab name, and last-updated context before using it. Do not use a sheet as the current-period source when its title, tab, or contents indicate a previous quarter; ask for or search for the current-period tracker instead. Then check `references/okr-sources.md` for known current tracker links before running a broader search. If a known source matches the requested team or function and period, use that URL; otherwise search for the team's OKR tracker with queries like:

- `"<team name>" OKR`
- `"<team name>" objectives key results`
- `"<team name>" OKR <current year>`
- `"<team name>" OKR <current quarter>`

If multiple plausible sheets are found, list the top 3-5 with titles and URLs and ask which one to use. If none are found, ask for a direct URL or pasted rows.

## Step 2 -- Read the OKR Tracker

Use the best available source:

1. **Google Drive/Sheets tools** -- Prefer structured spreadsheet reads when available.
1. **Glean `read_document`** -- Try the known tracker URL or the selected search result. Glean may return spreadsheet data as CSV-like text in snippets rather than structured rows; parse carefully because headers and row alignment can be inconsistent.
1. **Glean `search`** -- Use when direct reads return empty or unusable data.
1. **Glean `chat`** -- Last resort for synthesis: "What are the current OKR key results and status for the <team> team?"
1. **Manual paste** -- Use if connector reads fail or access is missing.

### Filtering to the team

OKRs are organized by objective, not by team. To filter:

- Look for key results where the team or a team member is listed as DRI (Directly Responsible Individual).
- Include the parent objective for context even if the team only owns some KRs under it.
- Clearly label which KRs the team directly owns vs. related KRs under the same objective.

### Determining the current quarter

Look for the quarter in the spreadsheet title (e.g. "FY27Q1"), sheet headers, tab names, or column date ranges. Do not assume -- derive it from the data. If the sheet has multiple tabs, choose the tab matching the requested or current period; if ambiguous, list the tab names and ask the user which one to use.

If a linked Jira ticket, document, or search result points to a tracker from an earlier quarter, treat that tracker as historical context only. Do not generate the status report from old OKR rows unless the user explicitly asks for a historical report for that period.

## Step 3 -- Extract Jira Signals

Skip this step if Jira is unavailable, but state that the report is based only on tracker data.

Determine a Jira project key before running project-scoped JQL:

1. Use a project key explicitly provided by the user.
1. Extract the key from ticket IDs in the OKR tracker, such as `AITOOL-123` or `ENG-456`.
1. If a team name suggests a likely project key, ask the user to confirm it.
1. If still unknown, ask: "What Jira project key should I use for this team? For example, `ENG` or `AITOOL`."

For each key result, gather only enough Jira context to validate status:

- If the KR references a specific ticket or epic, fetch it directly.
- Otherwise, run up to 3 JQL searches per KR:
  - `project = <PROJECT> AND summary ~ "<key result keywords>" ORDER BY updated DESC`
  - `project = <PROJECT> AND labels = "okr" AND summary ~ "<objective keywords>"`
  - `project = <PROJECT> AND type = Epic AND summary ~ "<key result keywords>"`
- Collect related epics/tickets, statuses, completion counts, blockers, and last activity dates.

For Atlassian MCP, use the available `searchJiraIssuesUsingJql` tool for JQL and `getJiraIssue` for exact ticket keys. For `jira` CLI environments, use equivalent JQL search and issue-view commands; for the common `jira-cli`, this is typically `jira issue list -q "<JQL>"` and `jira issue view <KEY>`. If the installed CLI uses different syntax, check `jira --help` briefly or skip Jira with a clear note.

If no matching Jira work is found, write "No linked Jira work found" rather than inventing a link.

## Step 4 -- Check Operational Metrics

For DevOps, IT, infrastructure, reliability, or support-oriented OKRs, use `references/metrics-sources.md` to look for supporting evidence such as:

- app apdex for `app.apollo.io` from Apollo admin performance monitoring
- component-specific uptime for `app.apollo.io` from `status.apollo.io`
- customer-visible `status.apollo.io` incidents affecting `app.apollo.io` with visible duration greater than 10 minutes during the reporting period

Use operational metrics only when they map clearly to a KR. Cite the source URL, component/service, metric window, and retrieval date. If a metric source is unavailable or requires internal access, mark operational metrics as unavailable or partially available rather than guessing.

Do not let operational metrics override the OKR tracker by themselves. Treat them as supporting evidence for KRs about reliability, performance, incident reduction, or service quality.

Exclude scheduled maintenance from incident counts unless the KR explicitly includes scheduled maintenance or customer-visible maintenance windows.

## Step 5 -- Determine Status

Assign each KR one of these statuses:

| Status | Criteria |
| --- | --- |
| Complete | Target is met or all clearly linked work is done. |
| On Track | Progress is at or ahead of the period pace, and most related work is in progress or done. |
| At Risk | Progress is slightly behind, blockers exist, or related work is stale for 2+ weeks. |
| Behind | Progress is significantly behind, or key work is blocked/not started. |
| Not Started | No progress is recorded and no related work is active. |
| Needs Review | Data is insufficient or contradictory. |

When the period has clear start/end dates, compare percent of period elapsed with percent of KR progress. If the fiscal calendar is unclear, avoid precise pace claims and explain the missing date context.

Do not mark a KR Behind only because Jira evidence is missing. Many KRs are measured outside Jira; use Needs Review when tracker progress is unclear and no execution evidence is available.

## Step 6 -- Evidence Audit

Before producing the final report, double-check the claims that could mislead a reader:

- Verify the source period matches the requested/current reporting period. If a source is stale or historical, exclude it from current status claims and list it as historical context only.
- Re-check each objective, KR, owner, target, current value, progress percentage, Jira status, and operational metric against the source where it came from.
- For each status call, confirm the evidence supports the label. If the tracker and Jira/metrics disagree, use Needs Review and explain the conflict.
- Do not present snippets, search results, linked historical sheets, or Jira descriptions as the source of truth when a current tracker is unavailable.
- Do not report exact numeric values, incident counts, apdex, uptime, or dates unless they were directly observed. Use "unavailable", "not visible", or "not verified" instead of estimating.
- Keep an internal source map while drafting: claim -> source URL/tool result -> retrieval date -> confidence. Surface only meaningful data gaps in the final report.

## Step 7 -- Generate the Report

### Header

- Team name
- Reporting period (quarter derived from data)
- Report generated date
- Data freshness: note when the OKR data was last updated if visible
- Source: link to the OKR tracker or say "manual paste"
- Jira evidence: available / unavailable / partially available
- Operational metrics evidence: available / unavailable / partially available

### For each Objective

- **Objective**: The objective text
- **Overall status**: Complete / On Track / At Risk / Behind / Needs Review
- **Key Results** (as a table):

| KR | Owner | Target | Current | Progress | Status | Jira | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| KR1.1 | ... | ... | ... | ...% | On Track | AITOOL-123 | ... |

- Separate team-owned KRs from related KRs under the same objective

### Summary

- Total KRs complete / on track / at risk / behind / needs review
- Top risks: KRs most behind or trending down
- Highlights: KRs ahead of pace
- Data gaps: missing owners, targets, current values, stale tracker data, missing Jira evidence, or missing operational metrics

### Operational Metrics

Include this section only when operational metrics support one or more KRs:

| Metric | Window | Value / Count | Source | Notes |
| --- | --- | --- | --- | --- |
| app.apollo.io uptime | ... | ... | status.apollo.io | ... |

### Risks and Recommendations

Include a short table only when there are meaningful risks:

| KR | Risk/Blocker | Impact | Recommendation |
| --- | --- | --- | --- |
| KR1.2 | ... | High/Medium/Low | ... |

### HTML Output

When the `html` argument is requested, generate a complete standalone HTML document with:

- `<!doctype html>`, `<html>`, `<head>`, responsive CSS, and semantic sections for header, summary, objectives, operational metrics, risks, and data gaps.
- The same facts, statuses, caveats, and source links as the audited Markdown report.
- Escaped text for tracker/Jira/source content; do not add JavaScript or external assets.
- A visible "Source Audit" or "Data Gaps" section when any evidence is partial, stale, single-source, unavailable, or contradictory.

If both Markdown and HTML are useful, provide the Markdown summary in chat and link to the generated HTML file path. Do not let the HTML version contain claims that were removed or caveated in the Markdown report.

## Formatting

- Use markdown tables for key results within each objective
- Keep commentary factual -- summarize what the data shows, don't editorialize
- If data is missing or ambiguous, flag it rather than guessing
- Note any data that appears stale or inconsistently formatted
- Cite source sheet URLs and Jira ticket URLs when available
- Do not write files or create artifacts unless the user explicitly asks

## Example

See `references/example-report.md` for a complete example report.

## Known Sources

See `references/okr-sources.md` for known OKR tracker links and `references/metrics-sources.md` for optional operational metric sources. Verify access and freshness at run time before treating any source as current.
