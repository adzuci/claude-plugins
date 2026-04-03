---
name: eng-metrics
description: Summarize engineering metrics for a team or org. Activate when a manager asks for eng metrics, engineering health, developer productivity metrics, DORA metrics, or says "eng metrics".
---

# Engineering Metrics

Summarize engineering metrics for an engineering team, highlighting trends and areas that need attention.

## Step 0 — Check for Glean MCP

Follow the Glean MCP setup instructions in `references/data-sources.md` (section "Glean MCP Setup"). If the user declines installation, ask them to paste the metrics data manually and skip to Step 3.

## Step 1 — Identify scope

If the user already specified a team and time range, use them. Otherwise ask:

- Which team or org-level view?
- Time range (default: last 4 weeks)

## Step 2 — Read the metrics data

Engineering metrics live across multiple sources. Use Glean to find the most relevant data. Try these in order and use whichever returns data:

### Primary: Search for metrics documents

Use the Glean search queries from `references/data-sources.md` (section "Engineering Metrics") to find current metrics for the team.

### Secondary: Read known documents

Try `read_document` on known metrics URLs. Note: Glean may return spreadsheet data as CSV-like text in `snippets`, or may return empty results for large/unindexed documents.

- Global Engineering Metrics spreadsheet (org-wide delivery and quality data)
- Quarterly midterm metrics reports (team-level breakdowns)

### Tertiary: Glean chat synthesis

Use Glean `chat` to synthesize: "What are the recent engineering metrics for the <team> team including PR lead time, deploy frequency, uptime, and incidents?"

If no source returns usable data, ask the user to paste or link to their metrics.

### Data freshness

Note the last-updated date of each source you use. Different sources update on different cadences — flag any data older than 2 weeks.

## Step 3 — Generate the summary

### Header

- Team or scope
- Time range
- Report generated date
- Data sources used (with freshness dates)

### Delivery metrics

| Metric | Current | Prior Period | Trend |
| --- | --- | --- | --- |
| PR lead time (P50) | ... | ... | ... |
| Deploy frequency (PRs/engineer/month) | ... | ... | ... |
| Cross-team reviews | ... | ... | ... |

- Note anomalies (e.g. spikes in lead time, drops in deploy frequency)
- If the team is a heavy cross-team reviewer, flag this as a capacity factor

### Quality metrics

| Metric | Current | Target | Status |
| --- | --- | --- | --- |
| Uptime | ... | ... | ... |
| Open incidents (SEV0/1/2) | ... | ... | ... |
| Security vulnerabilities | ... | ... | ... |

- Include incident counts and severity breakdown if available
- Note: bug rate, regression rate, and test coverage are not tracked at team level in most Apollo metrics sources. Flag as a data gap rather than omitting the section.

### Capacity and flow

- Work in progress counts (if available from Jira or project board)
- Blocked items (if available)
- Sprint completion rate (if available)

Note: Sprint velocity tracking has been archived org-wide. WIP and blocked items are typically only available via Jira. If these metrics are not available, say so and move on.

### Trends and callouts

- Metrics trending in the wrong direction (flag clearly with magnitude of change)
- Metrics trending positively (acknowledge briefly)
- Data gaps — metrics that could not be found or are stale

## Formatting

- Use markdown tables for metric comparisons across periods
- Show percentage changes and directional indicators where data supports it
- Keep commentary factual — describe what the numbers show, flag anomalies, avoid subjective judgments about team performance
