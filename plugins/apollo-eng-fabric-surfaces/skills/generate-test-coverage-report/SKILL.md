---
name: generate-test-coverage-report
description: Generate the Fabric Surfaces weekly test coverage Slack report. Activate when user asks to generate fabric surfaces weekly test report, fabric surfaces coverage report, or fabric surfaces test coverage.
---

# Fabric Surfaces Weekly Test Coverage Report

Generate a formatted Slack message with a 3-week snapshot of Fabric Surfaces test coverage (E2E/Playwright, Vitest, RSpec) using Grafana Prometheus data.

## Prerequisite: Grafana MCP Server (MANDATORY)

**Before doing anything else**, check if the Grafana MCP tools are available by looking for `mcp__grafana__query_prometheus` in the available tools list.

If the Grafana MCP tools are **NOT available**, stop immediately and show the user this message:

> :warning: **Grafana MCP is not connected.** This skill requires the Grafana MCP server to query test coverage metrics. Without it, the report cannot be generated.
>
> **To connect Grafana MCP, run this command in your terminal:**
>
> ```
> claude mcp add grafana https://grafana-mcp.ops-gcp.apollo.io/mcp --transport http --scope user
> ```
>
> Then restart Claude Code and run this skill again.

**Do NOT proceed with any further steps if Grafana MCP is not available. The skill cannot function without it.**

## When to Activate

- User asks to "generate weekly coverage report" or "weekly test coverage"
- User asks for "fabric surfaces coverage report" or "coverage slack post"
- User says "weekly coverage" or "coverage report for fabric surfaces"

---

## Data Source

- **Datasource UID**: `eeloo3k56g9vkd` (prometheus self-hosted mimir — span metrics)
- **Metric**: `team_coverage_overall_percentage`
- **Filter**: `team_name="fabric-surfaces"`, `branch="master"`
- **Frameworks**: `playwright` (E2E), `vitest` (FE Unit), `rspec` (BE)

## Execution Steps

### Step 1: Calculate Date Ranges

Use today's date to compute 3 weekly windows:

| Label           | From    | To      |
| --------------- | ------- | ------- |
| Week 1 (oldest) | now-21d | now-14d |
| Week 2 (middle) | now-14d | now-7d  |
| Week 3 (latest) | now-7d  | now     |

Compute the human-readable "Week of" dates:

- Week 1 date = today - 21 days
- Week 2 date = today - 14 days
- Week 3 date = today - 7 days

The report header date range = (today - 7 days) to today.

Format all dates as `Mon DD, YYYY` (e.g., `Mar 20, 2026`).

### Step 2: Query Grafana

For each of the 3 frameworks (`playwright`, `vitest`, `rspec`), query each weekly window using `mcp__grafana__query_prometheus`:

```
avg without (instance, exported_instance) (
  last_over_time(
    team_coverage_overall_percentage{
      framework="<FRAMEWORK>",
      team_name="fabric-surfaces",
      branch="master"
    }[7d]
  )
)
```

Use these parameters for each query:

- `datasourceUid`: `eeloo3k56g9vkd`
- `queryType`: `instant`
- `startTime`: the **end** of each weekly window (e.g., `now-14d` for Week 1, `now-7d` for Week 2, `now` for Week 3)

This gives you 9 queries total (3 frameworks x 3 weeks). Run all in parallel where possible.

### Step 3: Extract Values

From each query result, take the numeric value and round to 1 decimal place. If multiple series are returned (from different instances), average them.

### Step 4: Determine Indicators

**Trend arrows** — compare each week to the previous:

- If current week > previous week: `:arrow_up:`
- If current week < previous week: `:arrow_down:`
- If equal: `:left_right_arrow:`
- Week 1 (oldest) gets no arrow

**Status circle** — based on the overall trend from Week 1 to Week 3:

- `:large_green_circle:` if Week 3 >= Week 1 (net positive or flat)
- `:large_yellow_circle:` if Week 3 < Week 1 (net negative)

### Step 5: Format Output

Output the Slack message in this exact format:

Note: This message uses Slack mrkdwn formatting. Use `**text**` for bold and `_text_` for italic in Slack.
IMPORTANT: The Slack MCP rejects messages with 3+ consecutive hyphens on a line (e.g., `---`, `----`). Use exactly `--` (two hyphens) as a separator. Also avoid triple backticks for code blocks — they cause `invalid_blocks` errors.

```
:clipboard: FABRIC SURFACES Weekly Test Coverage Report (<start_date> - <end_date>)

_3 Week Snapshot_


**E2E ( PW ):** <status_circle>
• Week of <week1_date>: <pct>%
• Week of <week2_date>: <pct>%  <arrow>
• Week of <week3_date>: <pct>%  <arrow>




**Vitest:** <status_circle>
• Week of <week1_date>: <pct>%
• Week of <week2_date>: <pct>%  <arrow>
• Week of <week3_date>: <pct>%  <arrow>




**RSpec:** <status_circle>
• Week of <week1_date>: <pct>%
• Week of <week2_date>: <pct>%  <arrow>
• Week of <week3_date>: <pct>%  <arrow>


--
**<N> files with zero coverage**
- `path/to/file1.ts`
- `path/to/file2.tsx`
- `path/to/file3.ts`

cc: <!subteam^S06M2L5DGDR> <@U02SQFD1F5J>
```

Where:

- `<start_date>` = today - 7 days, formatted as `Mon DD, YYYY`
- `<end_date>` = today, formatted as `Mon DD, YYYY`
- `<week1_date>`, `<week2_date>`, `<week3_date>` = the "Week of" start dates
- `<pct>` = coverage percentage rounded to 1 decimal
- `<arrow>` = trend arrow emoji
- `<status_circle>` = green/yellow circle based on net trend

### Step 6: Post to Slack or Present to User

The user may optionally provide a Slack thread link when invoking this skill (e.g., `https://apolloio.slack.com/archives/CHANNEL_ID/pTIMESTAMP`).

**If a Slack thread link is provided AND the Slack MCP tools (`mcp__claude_ai_Slack__slack_send_message`) are available:**

1. Parse the channel ID and thread timestamp from the URL:
   - Channel ID: the segment after `/archives/` (e.g., `D08C3UHA4SY`)
   - Thread timestamp: the `p` prefix timestamp converted to Slack `ts` format (e.g., `p1774539593856959` → `1774539593.856959`)
2. Post the formatted message as a reply in that thread using `mcp__claude_ai_Slack__slack_send_message`
3. Return the message link to the user

**If a Slack thread link is provided but Slack MCP is NOT available:**

- Do NOT ask the user to set up Slack MCP
- Simply output the formatted message in a code block so the user can copy-paste it into Slack manually
- Tell the user: "Slack MCP is not connected, so here's the message for you to copy-paste."

**If no Slack thread link is provided:**

- Output the formatted message in a code block for the user to copy-paste

## 0% Coverage Files — Extraction Steps

### Step A: Download the HTML Report

Run this command using the Bash tool to download the coverage report from GCS:

```bash
gsutil cp gs://apollo-ops_gha_artifacts/apolloio/leadgenie/master/coverage/fe-missing-files-coverage-report.html /tmp/fe-coverage-report.html
```

If `gsutil` fails (not installed or not authenticated), skip the 0% coverage section entirely and add a note to the output:

> _Could not fetch 0% coverage files — `gsutil` is not configured. Run `gcloud auth login` to authenticate._

### Step B: Read the HTML and extract fabric-surfaces 0% coverage files

Read the downloaded HTML file at `/tmp/fe-coverage-report.html` using the Read tool.

The HTML structure is:

- Multiple tabs: `tab-0` (0% coverage), `tab-1` (1-20%), etc.
- Inside each tab, accordion sections per team: `<div class="owner-section">` with header `@apolloio/<team-name>`
- Inside each accordion, file entries: `<div class="file-name">path/to/file.ts</div>`

Find the **first** occurrence of `@apolloio/fabric-surfaces` in the file — this is the 0% tab's section. Read from that point until the next `<div class="owner-section">` starts (the next team). Extract all file paths from `<div class="file-name">` tags within that block.

The file may be large. Use the Grep tool to find the line number of the first `fabric-surfaces` occurrence, then use the Read tool with offset/limit to read just that section (~100 lines should be enough).

### Step C: Count and format

Count the extracted file paths (`<N>`) and format them as:

```
--
**<N> files with zero coverage**
- `path/to/file1.ts`
- `path/to/file2.tsx`
```

Append this section to the end of the Slack message (after the RSpec section). Wrap each file path in inline backticks.

### Step D: Handle edge cases

- If **no files** are found with 0% coverage for fabric-surfaces, append:
  ```
  --
  :tada: **0 files with zero coverage**
  ```
- If the HTML report download fails, skip this section and note it in the output.
