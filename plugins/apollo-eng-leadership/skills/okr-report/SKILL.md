---
name: okr-report
description: Generate an OKR status report for an engineering team. Activate when a manager asks for an OKR report, OKR status, quarterly progress, key results update, or says "okr report".
---

# OKR Report

Generate a structured OKR status report for a given engineering team by reading the company OKR tracker.

## Step 0 — Check for Glean MCP

Follow the Glean MCP setup instructions in `references/data-sources.md` (section "Glean MCP Setup"). If the user declines installation, ask them to paste the OKR data manually and skip to Step 3.

## Step 1 — Identify the team

If the user already specified a team, use it. Otherwise ask which team they want a report for.

## Step 2 — Read the OKR tracker

Use Glean to fetch OKR data. Try these approaches in order:

1. **`read_document`** — Try the OKR tracker spreadsheet URL from `references/data-sources.md`. Glean returns spreadsheet data as CSV-like text in the `snippets` field, not as structured rows. Parse carefully — column headers and row alignment may be inconsistent.

1. **`search`** — If `read_document` returns empty or unusable data, search using the Glean query from `references/data-sources.md` (section "OKR Tracker").

1. **`chat`** — As a last resort, ask Glean to synthesize: "What are the current OKR key results and status for the <team> team?"

1. If none of these return usable data, ask the user to paste the relevant rows.

### Filtering to the team

OKRs are organized by objective, not by team. To filter:

- Look for key results where the team or a team member is listed as DRI (Directly Responsible Individual).
- Include the parent objective for context even if the team only owns some KRs under it.
- Clearly label which KRs the team directly owns vs. related KRs under the same objective.

### Determining the current quarter

Look for the quarter in the spreadsheet title (e.g. "FY27Q1"), sheet headers, or column date ranges. Do not assume — derive it from the data.

## Step 3 — Generate the report

### Header

- Team name
- Reporting period (quarter derived from data)
- Report generated date
- Data freshness: note when the OKR data was last updated if visible

### For each Objective

- **Objective**: The objective text
- **Overall status**: On Track / At Risk / Off Track (based on key result progress)
- **Key Results** (as a table):

| KR | Description | Target | Current | Progress | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| KR1.1 | ... | ... | ... | ...% | On Track | ... |

- Separate team-owned KRs from related KRs under the same objective

### Summary

- Total KRs on track / at risk / off track
- Top risks: KRs most behind or trending down
- Highlights: KRs ahead of pace

## Formatting

- Use markdown tables for key results within each objective
- Keep commentary factual — summarize what the data shows, don't editorialize
- If data is missing or ambiguous, flag it rather than guessing
- Note any data that appears stale or inconsistently formatted
