---
name: experiment-record
description: Create a pre-launch experiment record in a Notion experiments database, with database properties and the pre-launch template sections filled in.
disable-model-invocation: true
requires_config: true
---

# Experiment Record Creator

Create a new experiment entry in your team's Notion experiments database, with all database properties and pre-launch template sections filled in. Used right before launching a test.

Usage: `/apollo-growth-product:experiment-record <description or Notion URL> [analytics/figma/jira links]`

## Configuration

Before doing anything else, read `config.md` from this skill's directory. It contains a YAML frontmatter block of variables this skill depends on.

For every `{{placeholder}}` you encounter while running this skill, substitute the matching value from `config.md`'s frontmatter.

`config.md` ships with the skill, so treat it as **defaults and documentation, read-only**. A plugin update replaces it.

Your own answers live in `~/.claude/plugin-config/apollo-growth-product/experiment-record.md`. Read that file first when it exists and let it override the shipped values, remembering that a saved empty string is a deliberate answer, not a missing one.

If a value is still `<UNSET>` after that merge, ask the user for it, then write the answer to `~/.claude/plugin-config/apollo-growth-product/experiment-record.md` (creating the directory if needed). Never write answers back into the skill's own `config.md`; they'd be wiped on the next plugin update. Do this once per session.

**Target DB data source:** `{{notion_experiments_data_source}}`

## Workflow

Execute these steps **in order**.

### Step 1: Parse arguments

Check the arguments for:

- **Experiment description** (e.g. "high-contrast CTA for bulk select feature gate")
- **Notion page URLs** for context (pitches, writeups, roadmap items)
- **Analytics links** for pulling metric baselines
- **Figma / Jira / project-tracker URLs** to set as link properties
- **Local file paths**
- **Property overrides**: team, surface, site section, ICE scores, test type, status

If no arguments were given, go to Step 2.

### Step 2: Gather context

Ask for anything not already provided:

> "What experiment are you recording? I need:
>
> - **What you're testing**: brief description or link to an existing writeup/pitch
> - **Surface**: {{experiment_surface_options}}
> - **Site Section**: where on the surface (e.g. Pricing Page, Homepage, Sign Up Page)
> - **Links**: Notion writeup, analytics charts, Figma designs, Jira ticket (any you have)
> - **ICE scores**: Impact (1-5), Confidence (1-5), Ease (1-5), or I can leave them blank
> - **Anything else**: estimated run time, test type, metric name"

Glob and read `{{team_context_dirs}}` for team context and prior pitches. Skip when empty. Report any relevant context found.

### Step 3: Fetch linked context

- **Notion URLs:** fetch page content (pitches, writeups, roadmap items). Extract experiment details, hypothesis, metrics, design info.
- **Analytics links:** pull current metric baselines for the metrics tables.
- **Local files:** read content from local markdown files.

Report what was found from each source. Note which metric baselines were found vs. which need manual input.

### Step 4: Resolve the lead

Look up the lead's Notion user ID with `notion-get-users` or `notion-search` (query type "user"). Default to `{{default_notion_user_id}}` when no lead is named.

### Step 5: Fill the template and draft

#### A) DB properties

| Property | Value | Notes |
|----------|-------|-------|
| **{{experiments_title_property}}** | Concise experiment name | Title property |
| **Status** | `{{experiment_default_status}}` | Default, override if specified |
| **Team** | Per `{{experiment_team_routing}}` | **Route off the experiment's audience, don't default.** Ask when the audience straddles two teams. |
| **Surface** | One of {{experiment_surface_options}} | Must be provided |
| **Test Type** | One or more of: Complex, Content Order, Copy, CTA, H1, New Imagery, Personalization, Social Proof, Subhed, UX Change, Videos | Multi-select |
| **Site Section** | From valid options in the live DB schema | Multi-select |
| **Metric** | Primary metric name | Text |
| **Impact** | 1-5 | Number, optional |
| **Confidence** | 1-5 | Number, optional |
| **Ease** | 1-5 | Number, optional |
| **Lead** | Resolved user ID | Person |
| **Summary: Description and Goal** | 2-3 sentence description + goal | Text |
| **Est. Run (Days)** | Estimated duration | Number, optional |
| **Amplitude Setup / Analysis** | Analytics URL | URL, optional |
| **Jira 🎫** | Jira ticket URL | URL, optional |
| \*\*Asana 🎫 \*\* | Asana task URL | URL, optional. Note the trailing space in the property name |
| **Figma 🎫** | Figma design URL | URL, optional |
| **Example Page** | URL of the page being tested | URL, optional |

**Do NOT set these properties.** They get filled post-experiment:

- `Summary: Results + Key Learnings`
- `[Post] Confidence / StatSig`
- `[Post] Est. Annual Impact -- Rollout Only`
- `Experiment Run Dates`
- `Shipped Date`

Property names in your database may differ, including emoji and trailing spaces. Read the live schema before the first write of a session and follow what it returns.

#### B) Page content

Generate Notion-flavored markdown filling the pre-launch sections:

```text
# 🔍 Problem
[User segment] [problem] [reason], tied to a metric.
Write a specific, measurable problem statement. Not generic.

# **🧪 Hypothesis**
Testable statement about what we believe and why.
Include the behavioral principle or user insight driving it.

## 📊 Supporting evidence
- Qualitative data (user research, surveys, support tickets)
- Metric analysis
- Learnings from prior experiments
- Competitor observations

# **🧪 Prediction**
If we [description of change], then we expect [metric] for [target audience] to
[increase/decrease] from [before] to [after] ([relative change %]).

# 🚨 Pre-Mortem Risk Notes
Known or anticipated risks to watch for and explore in the post-mortem.

# 📚 Cross-Team Learning Opportunities
Opportunities to share results and collaborate with other teams.

---
# 🎨 Experiment Design
**Target audience:**
**Audience size:**
**Estimated duration** (calculator: {{sample_size_calculator_url}}):

**Variant 1: default**
1. Baseline Conversion Rate: [rate with link to report]
2. # of samples needed
   Significance (α): 0.05
   MDE (%): 10%
   Total sample size:
3. Duration:

**Metrics:**
[Primary metric table, Notion <table> format with header-row]
[Supporting metrics table, Notion <table> format with header-row]

### Variants
[Use <columns> layout with Control and Treatment descriptions]
```

**Leave these sections EMPTY.** They get filled by `/apollo-growth-product:experiment-results`:

- `# 🧮 Analysis and results` — include the heading and empty results tables
- `# 💬 Discussion + Post-Mortem` — include the heading and empty summary structure

Notion-flavored markdown syntax to use:

- `<table header-row="true">` for metrics tables
- `<columns>` / `<column>` for control vs treatment
- `<empty-block/>` for intentional blank lines
- `<span color="gray">` for placeholder guidance text

### Step 6: Review the draft

Present the complete draft: the properties table and the full page content. Ask:

> "Here's the experiment record draft. Review the properties and page content before I create it in the Experiments DB. Let me know if anything needs adjusting."

Make any requested changes. Re-check that:

- All properties use exact names from the live DB schema, including emoji and trailing spaces
- No placeholders remain
- Metric baselines are filled where data was available
- Post-experiment sections are present but empty

### Step 7: Create in Notion

After approval:

1. Call `notion-create-pages` with `parent.data_source_id` set to `{{notion_experiments_data_source}}`, the properties from Step 5A, and the content from Step 5B.
1. Confirm successful creation with the page URL.
1. Suggest next steps: set up the experiment in your experimentation platform and add the link, create the engineering ticket with `/apollo-growth-product:jira-task`, and share with the team for review.

## MCP call reference

```javascript
notion-create-pages({
  parent: { data_source_id: "{{notion_experiments_data_source}}" },
  pages: [{
    properties: {
      "{{experiments_title_property}}": "Experiment title here",
      "Status": "{{experiment_default_status}}",
      "Team": "PD",
      "Surface": "www",
      "Test Type": "[\"UX Change\"]",
      "Site Section": "[\"Pricing Page\"]",
      "Metric": "Free-to-paid conversion rate",
      "Impact": 4,
      "Confidence": 3,
      "Ease": 4,
      "Lead": "[\"user-id-here\"]",
      "Summary: Description and Goal": "Description of what we're testing and why.",
      "Est. Run (Days)": 14,
      "Amplitude Setup / Analysis": "https://...",
      "Jira 🎫": "https://...",
      "Figma 🎫": "https://..."
    },
    content: "# 🔍 Problem\n..."
  }]
})
```

Property format notes:

- `Lead`: JSON array of user IDs, `"[\"user-id\"]"`
- `Test Type`, `Site Section`: JSON arrays of strings
- `Impact`, `Confidence`, `Ease`: numbers 1-5
- `Est. Run (Days)`: number
- Watch for property names with trailing spaces after an emoji. They're exact-match.

## Related skills

1. `/apollo-growth-product:experiment-pitch` — shape and pitch the initiative
1. `/apollo-growth-product:experiment-writeup` — design the experiment
1. `/apollo-growth-product:experiment-record` (this skill) — create the tracker entry
1. `/apollo-growth-product:jira-task` — create the engineering ticket
1. `/apollo-growth-product:experiment-results` — record results when it concludes

## Safety rules

- **Never fabricate metrics or baselines.** Only use data from analytics or provided context.
- **Always show the draft** before creating in Notion.
- **Don't leave placeholders.** If information is missing, ask rather than using `[TBD]`.
- **Use exact property names**, including emoji and trailing spaces. Read the live schema first.
- **Fill metric baselines** when data is available. Empty tables are a quality fail.
- **Leave post-experiment sections empty.** Analysis, Results, and Post-Mortem belong to the results skill.
- **Never set `[Post] Confidence / StatSig`.** That's set manually by the experiment owner.
