---
name: experiment-results
description: Close out a completed experiment by writing its results, analysis, and post-mortem to the Notion page from analytics data.
disable-model-invocation: true
requires_config: true
---

# Experiment Results Updater

Update a Notion experiment page with results, analysis, and a post-mortem summary. Reads results from analytics PDFs, screenshots, or verbal summaries, then pushes structured updates to the experiment page.

Usage: `/apollo-growth-product:experiment-results <notion page URL> [results PDF/screenshot path]`

## Configuration

Before doing anything else, read `config.md` from this skill's directory. It contains a YAML frontmatter block of variables this skill depends on.

For every `{{placeholder}}` you encounter while running this skill, substitute the matching value from `config.md`'s frontmatter.

`config.md` ships with the skill, so treat it as **defaults and documentation, read-only**. A plugin update replaces it.

Your own answers live in `~/.claude/plugin-config/apollo-growth-product/experiment-results.md`. Read that file first when it exists and let it override the shipped values, remembering that a saved empty string is a deliberate answer, not a missing one.

If a value is still `<UNSET>` after that merge, ask the user for it, then write the answer to `~/.claude/plugin-config/apollo-growth-product/experiment-results.md` (creating the directory if needed). Never write answers back into the skill's own `config.md`; they'd be wiped on the next plugin update. Do this once per session.

## Workflow

Execute these steps **in order**.

### Step 1: Parse arguments

Check the arguments for:

- **Notion experiment page URL**
- **Results data source**: path to an analytics PDF, screenshot, or a verbal description
- **Team coordination notes**: cross-team context to reference (optional)

If no arguments were given, go to Step 2.

### Step 2: Gather context

> "Which experiment are you closing out? I need:
>
> - **Notion page URL**: the experiment page to update
> - **Results data**: analytics PDF, screenshot path, or tell me the numbers verbally
> - **Cross-team notes**: any collaboration context to mention in future experiments (optional)"

### Step 3: Fetch the existing page

Fetch the current experiment page and review the existing content to understand the setup (hypothesis, variants, metrics, audience), which primary and supporting metrics were defined, and the current property values. Report what was found.

### Step 4: Analyze the results data

**If a PDF or screenshot path**: read the file and extract metrics. **If a verbal description**: parse the numbers provided.

Extract for each metric: control rate/value, treatment rate/value, relative lift (delta), p-value / statistical significance, sample size, and experiment duration.

**Also extract the actual run window** (start and end date) if available:

- If the results export shows the experiment's start and end dates, capture them.
- If you have the experiment ID (or can find it on the page) and the experimentation platform is connected, pull the actual start and end dates directly from the completed experiment.
- This is best-effort. If no run-date context is available, skip the run-dates update entirely. Don't guess or fabricate dates.

### Step 5: Draft updates

Draft updates for three sections, plus a conditional run-dates property.

#### a) "{{results_summary_property}}" property

Brief 2-3 sentence summary covering the statistical result (significant or not), sample size and duration, the recommendation (ship / rollback / iterate), and the key insight.

Example: "Experiment showed no statistical significance. Treatment failed to improve FTP conversion (-0.94% relative lift, p=0.66) over 15 days with 439,931 users. Recommend rollback. Persistent banner likely suffered from banner blindness."

#### b) "Analysis and Results" section

- **Experiment overview**: dates, sample size, variants, primary metric
- **Primary metric table**: Metric | Control | Treatment | Delta | p-value | Significant?
- **Supporting metrics table**: Metric | Type | Control | Treatment | Delta | p-value
- **Statistical interpretation**: explain significance (or its absence), and what the p-value means in context
- **Recommendation**: Ship / Rollback / Iterate, with clear reasoning

#### c) "Post-Mortem Summary" section

- **What we tested**: brief description of the hypothesis
- **What we found**: key results and metrics
- **Decision**: Ship / Rollback / Iterate
- **Reason**: why this decision was made
- **Why it worked or didn't**: user behavior insights and beliefs established
- **Ideas for future experiments**: next iterations, cross-team opportunities
- **Additional thoughts**: optional context, learnings, collaboration notes

#### d) "{{run_dates_property}}" property (conditional)

Only if you extracted actual start and end dates in Step 4:

1. Compare the actual run window against the current value of the property on the Notion page.
1. **If they differ**, draft an update to match what the experiment platform shows. The platform is the source of truth for the real run window.
1. **If they already match**, or no date context is available, skip this update and say no change is needed.

Show both values so the discrepancy is clear:

> "Run dates: Notion shows Feb 3 – Feb 18, the platform shows Feb 3 – Feb 20. Will update to Feb 3 – Feb 20."

### Step 6: Review the draft

Present the complete draft of all three sections (and the run-dates change, if any). Ask:

> "Here's the draft results update. Review the summary property, analysis section, and post-mortem before I update the Notion page. Let me know if anything needs adjusting."

Make any requested changes.

### Step 7: Update Notion

After approval:

1. Update the "{{results_summary_property}}" property.
1. Update the page content with the Analysis and Results and Post-Mortem sections.
1. If applicable, update "{{run_dates_property}}" to match the actual run window.
1. Confirm the successful update.

## Critical rules

**NEVER auto-update "{{manual_confidence_property}}".** That's set manually by the experiment owner. Don't touch it.

**ALWAYS update these three things:**

1. The "{{results_summary_property}}" property
1. The "Analysis and Results" section content
1. The "Post-Mortem Summary" section content

**CONDITIONALLY update "{{run_dates_property}}"** only when actual start and end dates from the completed experiment are available, and only if they differ from the current Notion value. Never guess or fabricate dates.

**ALWAYS review with the user** before pushing any updates to Notion.

## Writing style

- Be concise and scannable
- Use tables for metrics
- Bold key decisions and outcomes
- Use bullet points for lists of insights
- Include specific numbers: percentages, p-values, sample sizes, duration
- Always compare to the p < 0.05 significance threshold
- State relative lift as a positive or negative percentage
- Make a clear recommendation with reasoning

## Statistical interpretation guide

- **p < 0.05**: statistically significant, the result is unlikely due to chance
- **p >= 0.05**: not statistically significant, you can't conclude treatment differs from control
- **Positive lift + significant**: recommend ship
- **Negative lift + significant**: recommend rollback, treatment actively hurts
- **Not significant (either direction)**: recommend rollback (no evidence of improvement), consider iterate if the directional signal is promising
- Always note sample size and duration. Small samples or short runs reduce confidence.

## Related skills

1. `/apollo-growth-product:experiment-record` — create the tracker entry before launch
1. `/apollo-growth-product:experiment-results` (this skill) — close out one experiment
1. `/apollo-growth-product:quarterly-experiment-summary` — roll concluded experiments into the learnings doc

## Safety rules

- **NEVER update "{{manual_confidence_property}}".** That's set manually.
- **Always show the draft** before updating Notion.
- **Never fabricate metrics.** Only use data from the provided results.
- **Never fabricate run dates.** Only set them from actual platform data, and only if they differ from the current Notion value.
- **Include specific numbers** in every update: percentages, p-values, sample sizes.
- **Preserve existing page content.** Only add or update the specified sections.
- **State significance clearly.** Never leave ambiguity about whether a result is significant.
