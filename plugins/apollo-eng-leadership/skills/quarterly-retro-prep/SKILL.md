---
name: quarterly-retro-prep
description: Prepare for quarterly retrospectives by surfacing data-driven insights from Jira, Slack, GitHub, and past retro notes. Activate when the user asks for retrospective prep, a retrospective doc, retro agenda, sprint analysis, team health check, quarterly review, or what went well / what could improve.
---

# Quarterly Retro Prep

Gather data from Jira, Slack, GitHub, and past retro notes to produce a structured, data-driven retrospective preparation document for a team's quarterly review.

## Inputs

Ask the user for:

- **Team name** (required) -- e.g. "AI Tooling", "Platform", "Growth"
- **Date range** (optional) -- defaults to the previous calendar quarter. If today is in Q2, the default range is Q1 (Jan 1 -- Mar 31). Use ISO `YYYY-MM-DD` dates internally.
- **GitHub org/repos** (optional) -- defaults to `apolloio` org; ask which repos to include if unclear.
- **Jira project key(s)** (optional) -- ask if not obvious from the team name.

Resolve the date range before proceeding:

```
Q1: Jan 1 -- Mar 31
Q2: Apr 1 -- Jun 30
Q3: Jul 1 -- Sep 30
Q4: Oct 1 -- Dec 31
```

## Steps

### 1. Gather Jira Data

Use the Jira MCP to pull sprint and ticket data for the team's project(s) within the date range.

**Metrics to collect:**

- Total tickets created vs. completed
- Sprint velocity trend (story points completed per sprint)
- Carry-over rate (tickets not completed in their assigned sprint)
- Bug vs. feature vs. chore ratio
- Average ticket cycle time (created to done)
- Top 5 longest-lived tickets still open

**Queries:**

```
# Completed tickets in date range
project = <KEY> AND status = Done AND resolved >= "<start>" AND resolved <= "<end>"

# Created tickets in date range
project = <KEY> AND created >= "<start>" AND created <= "<end>"

# First, list the team's board sprints and record the sprint IDs whose end dates fall inside the target quarter

# Carry-over: only use sprint IDs from the target quarter, not all closed sprints.
# `statusCategory != Done` is safer than `status != Done` because it treats custom done-status names consistently.
project = <KEY> AND sprint in (<comma-separated quarter sprint ids, e.g. 123, 456, 789>) AND statusCategory != Done AND updated >= "<start>" AND updated <= "<end>"

# Bugs specifically
project = <KEY> AND type = Bug AND created >= "<start>" AND created <= "<end>"
```

**If Jira MCP is unavailable:** Tell the user Jira data could not be retrieved and ask them to provide sprint reports or velocity data manually. Skip to the next step.

### 2. Gather GitHub Data

Use the `gh` CLI to pull PR and CI metrics for the team's repositories.

**Metrics to collect:**

- Total PRs merged
- Average time from PR open to merge
- Average review turnaround (first review request to first review)
- CI failure rate (failed runs / total runs on the default branch)
- Top 10 most-changed files ("hotspot" files)
- Contributors ranked by PR count

**Commands:**

```bash
# PRs merged in date range
# $START and $END must use ISO `YYYY-MM-DD` format like 2026-01-01
gh pr list --repo <org>/<repo> --state merged --search "merged:>=$START merged:<=$END" --limit 200 --json number,title,author,createdAt,mergedAt,additions,deletions,changedFiles

# CI workflow runs on default branch
gh run list --repo <org>/<repo> --branch main --limit 200 --json status,conclusion,createdAt,updatedAt

# Hotspot files (most-changed files across merged PRs)
# `gh pr list` does not support `--json files`, so inspect a capped sample of merged PRs individually.
# Run this loop sequentially; if you hit 403/429 responses, reduce the sample size further before retrying.
gh pr list --repo <org>/<repo> --state merged --search "merged:>=$START merged:<=$END" --limit 25 --json number --jq '.[].number' | while read pr; do
  gh pr view "$pr" --repo <org>/<repo> --json files --jq '.files[].path'
done
```

Aggregate across all specified repos. Calculate:

- Merge time = `mergedAt - createdAt` (median and p90)
- CI failure rate = count of `conclusion=failure` / total runs in date range
- Hotspots = files appearing most frequently across the sampled PRs

Use bulk queries where possible. Cap Jira queries to a few broad JQL searches and cap hotspot PR inspection to a manageable sample unless the user explicitly asks for a deeper dive.
If the per-PR hotspot loop is too slow or hits API limits, reduce the sample size further before retrying.

**If `gh` is not authenticated:** Tell the user and skip this section.

### 3. Gather Slack Data (Optional)

Use the Slack MCP to search team channels for sentiment signals within the date range.

**Search queries:**

```
# Wins and celebrations
in:<team-channel> after:<start> before:<end> (shipped OR launched OR merged OR deployed OR "great job" OR "shoutout" OR ":tada:" OR ":rocket:")

# Pain points and frustrations
in:<team-channel> after:<start> before:<end> (blocked OR broken OR frustrated OR "tech debt" OR flaky OR "keeps failing" OR incident OR outage)

# Retro-related discussions
in:<team-channel> after:<start> before:<end> (retro OR retrospective OR "action item" OR improvement)
```

Extract and summarize:

- Top recurring themes (group by topic)
- Notable wins mentioned by the team
- Recurring frustrations or blockers
- Any shoutouts or recognition

If the Slack MCP does not support `after:` / `before:` filters, broaden the search and filter the returned messages by timestamp before summarizing (for example, keep only messages where `timestamp >= <start>` and `timestamp <= <end>`).

**If Slack MCP is unavailable:** Note that Slack data was skipped and suggest the user manually review their team channel for themes. Continue to the next step.

### 4. Look Up Previous Retro Notes (Optional)

Use Glean MCP or Notion MCP to search for the team's previous retrospective notes.

**Search queries:**

```
# Glean
"<team name> retrospective" OR "<team name> retro" -- filter to last 6 months

# Notion
Search for pages titled "retro" or "retrospective" in the team's workspace
```

**Extract from previous retros:**

- Action items that were committed to
- Owners assigned to each action item
- Any themes that recurred across multiple retros

**If neither Glean nor Notion MCP is available:** Note that previous retro data was skipped. Suggest the user paste in prior action items manually if they have them.

### 5. Analyze Patterns and Synthesize

With data from all available sources, identify:

- **Velocity trends**: Compare average story points completed per sprint and, if there are 3+ sprints, note the slope across the quarter.
- **Quality signals**: Calculate bug ratio as `bugs created / total tickets created`; compare that with CI failure rate direction and flaky test indicators.
- **Flow efficiency**: Calculate carry-over rate as `tickets not done by sprint end / tickets assigned to that sprint`; use median and p90 PR merge time to spot review bottlenecks.
- **Team sentiment**: Positive vs. negative signal ratio from Slack.
- **Recurring themes**: Issues that appear in multiple data sources (e.g., a file that is both a hotspot and mentioned in Slack as problematic).

### 6. Generate the Retro Prep Document

Output a structured Markdown document with the following sections. Use actual data and specific numbers wherever available. When a data source was unavailable, note it and mark the section as incomplete.

```markdown
# Quarterly Retrospective Prep: <Team Name>
## <Quarter> <Year> (<start date> -- <end date>)

> Generated on <today's date> using data from: <list sources that were available>

---

## Metrics Dashboard

| Metric | This Quarter | Last Quarter | Trend |
|--------|-------------|-------------|-------|
| Tickets completed | N | N | +/-N% |
| Sprint velocity (avg pts) | N | N | +/-N% |
| Carry-over rate | N% | N% | +/-N% |
| Bug : Feature ratio | N:N | N:N | -- |
| PRs merged | N | N | +/-N% |
| Median PR merge time | Nh | Nh | +/-N% |
| Median review turnaround | Nh | Nh | +/-N% |
| CI failure rate | N% | N% | +/-N% |

> "Last Quarter" data requires running this skill for the prior quarter. If unavailable, fill those cells with `--` and mark the trend as `N/A`.

---

## What Went Well

- <Data-backed win with specific numbers>
- <Another win>
- <Team shoutouts from Slack if available>

---

## What Could Improve

- <Pain point with evidence from data>
- <Another area with supporting metrics>
- <Recurring themes from Slack if available>

---

## Follow-Up on Last Quarter

| Action Item | Owner | Status |
|------------|-------|--------|
| <item from previous retro> | <name> | Done / In Progress / Not Started |

> If previous retro notes were unavailable, note that here and ask the team to review manually.

---

## Suggested Discussion Topics

Based on the data patterns, consider discussing:

1. <Topic with rationale and supporting data>
2. <Topic>
3. <Topic>

---

## Code Hotspots

Files with the most churn this quarter (candidates for refactoring or ownership review):

| File | PRs Touching It | Key Contributors |
|------|----------------|-----------------|
| <path> | N | <names> |

---

## Raw Data Summary

<Collapsed details with the underlying numbers for anyone who wants to drill deeper>
```

### 7. Present and Iterate

Show the generated document to the user and ask:

- Does this cover the right scope?
- Are there additional repos, channels, or Jira projects to include?
- Should any section be expanded or removed?
- Would you like this exported to a Notion page?

If the user wants to export to Notion, use the Notion MCP to create a page in the team's workspace with the retro prep content.

## Tips

- Run this skill 2-3 days before the actual retro so there is time to review and adjust
- If the team spans multiple Jira projects, pass all project keys for a complete picture
- For large teams with many repos, focus on the 3-5 most active repositories to keep the output manageable
- Quarter-over-quarter trends are most valuable -- suggest running for the prior quarter too if comparison data is needed
- The document is a conversation starter, not a final verdict -- frame findings as discussion prompts, not conclusions
