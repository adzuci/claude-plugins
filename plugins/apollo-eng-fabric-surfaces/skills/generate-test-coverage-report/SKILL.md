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

### Step 6: Post to Slack

Post the formatted message directly to `#internal-squad-fabric-surfaces` (channel ID: `C06HG89A6S2`) as a top-level message.

**If Slack MCP (`mcp__claude_ai_Slack__slack_send_message`) is available:**

1. Call `mcp__claude_ai_Slack__slack_send_message` with:
   - `channel_id`: `C06HG89A6S2`
   - `message`: the formatted message
   - Do NOT set `thread_ts` — this is a top-level post
2. Return the message link to the user

**If Slack MCP is NOT available:**

- Do NOT ask the user to set up Slack MCP
- Output the formatted message in a code block for the user to copy-paste
- Tell the user: "Slack MCP is not connected, here's the message to copy-paste."

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

The file is large. First find the exact line boundaries of tab-0 and tab-1 using the Bash tool:

```bash
grep -n 'id="tab-0"\|id="tab-1"' /tmp/fe-coverage-report.html | head -2
```

Extract `tab0_line` and `tab1_line` from the output. If `id="tab-1"` is not present, set `tab1_line` to the total number of lines + 1:

```bash
wc -l /tmp/fe-coverage-report.html
```

Then search for `@apolloio/fabric-surfaces` **only within those line numbers** (tab-0 start to tab-1 start):

```bash
awk 'NR>=<tab0_line> && NR<tab1_line' /tmp/fe-coverage-report.html | grep -n "fabric-surfaces"
```

If fabric-surfaces is **not found** within tab-0, the team has 0 files with 0% coverage — skip directly to Step D (zero files case).

If found, the relative grep line number is 1-based within the awk slice. Compute the absolute line number as `tab0_line + relative_offset - 1`, then use the Read tool at that offset for ~100 lines and extract all `<div class="file-name">` entries until the next `<div class="owner-section">`.

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
