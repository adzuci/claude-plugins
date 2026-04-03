---
name: sprint-planning
description: Help prepare for sprint planning by summarizing carry-over work, team capacity, and suggested priorities. Activate when a manager asks to prepare for sprint planning, plan the next sprint, sprint prep, or says "sprint planning".
---

# Sprint Planning Prep

Help an engineering manager prepare for sprint planning by pulling together carry-over work, capacity signals, and priority recommendations.

## Step 0 — Check for Glean MCP

Follow the Glean MCP setup instructions in `references/data-sources.md` (section "Glean MCP Setup"). If the user declines installation, the skill can still work with Jira/GitHub data and manual input. Note which data sources are unavailable and continue.

## Step 1 — Identify the team and sprint

If the user already provided this context, use it. Otherwise ask:

1. Which team?
1. What sprint or iteration are they planning for? (default: next sprint)
1. Where is their backlog? (Jira project, Linear team, GitHub project, etc.)

## Step 2 — Gather context

Pull data from available sources. Use whichever are accessible and note which sources were unavailable.

### From the backlog (Jira / Linear / GitHub Issues)

If a Jira MCP, GitHub CLI, or other project tool is available:

- Incomplete items from the current sprint (carry-overs)
- Items in the backlog prioritized for next sprint
- Items flagged as blocked

**If Jira MCP is not available**, fall back to Glean:

- Search for `"<team> sprint" OR "<team> planning"` with `app: jira` to find recent sprint-related items
- Search for `"<team> planning"` with `app: gdrive` to find planning spreadsheets or docs

### From the OKR tracker (via Glean)

Use the OKR tracker URL and search queries from `references/data-sources.md` (section "OKR Tracker"). Try `read_document` first, fall back to `search`.

Identify at-risk KRs that should inform sprint priorities. Note: OKRs are organized by objective, not team — filter by DRI.

### From engineering metrics (via Glean)

Use the engineering metrics search queries from `references/data-sources.md` (section "Engineering Metrics") to find recent metrics for capacity estimation.

Extract velocity/throughput signals (PRs/engineer/month, lead time trends). Note: sprint-level velocity tracking is archived org-wide — use PR throughput as a proxy.

### Data freshness

Note the last-updated date of each source. Flag any data older than 2 weeks.

## Step 3 — Generate the planning brief

### Carry-over from current sprint

| Title | Jira/Link | Assignee | Status | Notes |
| --- | --- | --- | --- | --- |
| ... | ... | ... | ... | Why it carried over (blocked, descoped, started late) |

### Capacity signals

- Team size and any known absences (PTO, on-call rotation)
- Last sprint's throughput (PRs merged, items completed)
- Carry-over load that reduces available capacity
- If velocity data is not available, note this and suggest the team start tracking it

### Suggested priorities

Based on OKR alignment and backlog priority:

1. **Must do**: Items directly tied to at-risk OKRs or hard deadlines
1. **Should do**: Items tied to on-track OKRs or high-priority backlog items
1. **Could do**: Nice-to-haves if capacity allows

For each item: title, link, rough size if available, and why it's in that tier.

### Risks and dependencies

- Cross-team dependencies that could block work
- Items that need design, product, or infra input before they can start
- Any known technical risks
- Unassigned items that need owners during planning

### Data source availability

| Source | Status | Notes |
| --- | --- | --- |
| OKR Tracker | Available / Unavailable | Freshness date |
| Eng Metrics | Available / Unavailable | Freshness date |
| Jira | Available / Unavailable | ... |

## Formatting

- Use markdown tables for carry-over and priority lists
- Keep the brief scannable — managers use this as a pre-read or live reference during planning
- Link to source tickets/issues wherever possible
