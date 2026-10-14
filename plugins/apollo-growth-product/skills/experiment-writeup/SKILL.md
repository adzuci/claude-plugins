---
name: experiment-writeup
description: Create a detailed experiment design document, standalone or appended to an existing Notion roadmap item, with baselines pulled from analytics links.
disable-model-invocation: true
requires_config: true
---

# Experiment Writeup Creator

Create detailed experiment design documents that either stand alone or append to existing roadmap items with simple pitches.

Usage: `/apollo-growth-product:experiment-writeup <description or Notion URL> [analytics links] [figma links]`

## Configuration

Before doing anything else, read `config.md` from this skill's directory. It contains a YAML frontmatter block of variables this skill depends on.

For every `{{placeholder}}` you encounter while running this skill, substitute the matching value from `config.md`'s frontmatter.

`config.md` ships with the skill, so treat it as **defaults and documentation, read-only**. A plugin update replaces it.

Your own answers live in `~/.claude/plugin-config/apollo-growth-product/experiment-writeup.md`. Read that file first when it exists and let it override the shipped values, remembering that a saved empty string is a deliberate answer, not a missing one.

If a value is still `<UNSET>` after that merge, ask the user for it, then write the answer to `~/.claude/plugin-config/apollo-growth-product/experiment-writeup.md` (creating the directory if needed). Never write answers back into the skill's own `config.md`; they'd be wiped on the next plugin update. Do this once per session.

**Template sections:** 1-Liner, Context, Hypothesis, User Journey, Experiment Design, Metrics, Designs, Open Questions
**Output directory:** `{{writeup_output_dir}}`

## Workflow

Execute these steps **in order**.

### Step 1: Parse arguments and detect mode

Check the arguments for an experiment description, a Notion page URL, analytics links for baseline metrics, design links, and context file references.

**Detect mode:**

- **Append mode** (default when a Notion URL is provided): fetch the existing page. If it has content (a pitch or preliminary notes), preserve that content at the top, add a `---` separator, and append experiment design sections below.
- **New mode** (no Notion URL, or the page is empty): start fresh with all experiment design sections.

If no arguments were given, go to Step 2.

### Step 2: Gather context

Ask for anything not already provided:

> "What experiment are you designing? I need:
>
> - **What you're testing**: feature, change, or hypothesis
> - **Notion page URL**: existing roadmap item to append to (optional, I can create standalone)
> - **Analytics links**: for pulling baseline metrics (optional)
> - **Design links**: Figma, screenshots, mockups (optional)
> - **Additional context**: local files, Slack threads, prior experiments"

Glob and read `{{team_context_dirs}}` for planning docs, team context, and roadmap exports. Skip when empty. Report anything relevant.

### Step 3: Fetch existing content (append mode)

If a Notion URL was provided, fetch the current page content, review what's already there, and report: "Found existing content on the page. I'll preserve the pitch at the top and append experiment design sections below the separator."

If the page is empty, switch to new mode.

### Step 4: Pull baselines (if analytics links provided)

Query the analytics platform for current metric values and extract baseline measurements for the metrics tables. Report what baselines were found. If no links, note which baselines need manual input.

### Step 5: Fill the template

**Append mode** preserves the existing content, then `---`, then the sections. **New mode** starts directly with `## 1-Liner`.

Work through each section:

#### 1-Liner

Single sentence: what you're testing and why. Clear, specific, actionable.

Example: "Test whether showing credit expiration warnings 7 days early increases annual plan upgrades by leveraging loss aversion"

#### Context

Background on the problem and current state, why this experiment matters now, and supporting data or research.

#### Hypothesis

What you believe will happen and why. Include the behavioral principle or user insight driving it. Can include primary and secondary hypotheses.

#### User Journey (treatment variant)

Numbered step-by-step walkthrough of the treatment experience. Focus on user actions and what they see: actual screens, buttons, flows. Not generic "user sees a message."

#### Iterations to Consider

Future variations or follow-up tests. Different approaches to the same hypothesis.

#### Experiment Design

- **Audience**: specific user segments with sample size
- **Sample Size**: users per day or total, with a query link
- **Minimum detectable effect**: percentage with justification
- **Run Time**: duration needed, with a calculator link ({{sample_size_calculator_url}})
- **Variants**: control (current experience) and treatment (new experience) descriptions

#### Metrics

Fill baseline measurements when data is available. Don't leave empty cells.

Primary metric table columns: Primary metric | Baseline measurement | Report links

Supporting metrics table columns: Supporting metrics | Type | Baseline measurement | Report links

Types: Leading (early signals), Secondary (additional outcomes), Guardrail (shouldn't degrade).

#### Designs

Figma links with specific frame or page references, screenshots of key UX moments, control vs. treatment mockups.

#### Open Questions

Clear bullet list of unknowns. Answer known questions inline if possible. Focus on blockers or decisions needed before launch.

### Step 6: Quality checklist

Before presenting the draft, verify:

- All metric baselines filled, or explicitly noted as "TBD, pending data"
- Specific user journey steps, not generic descriptions
- MDE and runtime calculated with links to the calculator
- Designs linked or screenshots embedded
- Hypothesis explains the "why" (behavioral principle or user insight)
- Open questions are clear and actionable
- Append mode: existing content preserved correctly above the separator

Flag any gaps in the review step.

### Step 7: Review the draft

Present the complete writeup in chat.

**Append mode:** "Here's the experiment design. I've preserved the existing pitch at the top and appended the experiment sections below the separator. Would you like to adjust anything before I update the Notion page?"

**New mode with Notion:** "Here's the experiment design. Would you like to adjust anything before I push to Notion?"

**New mode local:** "Here's the experiment design. Would you like to adjust anything before I save it?"

Make any requested changes. Re-run the quality checklist after significant edits.

### Step 8: Push to Notion or save locally

After approval:

**If a Notion URL was provided:** use `notion-update-page` to push content, preserve existing page properties and metadata, and confirm with the page URL.

**If no Notion URL:** save to `{{writeup_output_dir}}/{experiment-slug}-{YYYY-MM-DD}.md` and confirm the path.

## Template

```markdown
## **1-Liner**

[One sentence describing what you're testing and why]

## **Context**

[Background on the problem, current state, and why this experiment matters]

## Hypothesis

1. [Primary hypothesis about what change will drive what outcome]
2. [Secondary hypothesis if applicable]

## User Journey (Treatment variant)

1. [Step 1 in the user experience]
2. [Step 2]
3. [Step 3]

## Iterations to consider

- [Future variations or follow-up tests to consider]

## **Experiment Design**

- **Audience**: [Number of users, segmentation criteria]
- **Sample Size**: [Users per day or total sample]
    - **Query**: [Link to the analytics query]
- **Minimum detectable effect**: [Percentage, e.g. 10%]
- **Run Time**: [Duration, e.g. 2 weeks]

### Variants

**Control**

[Description of current/control experience]

**Treatment**

[Description of treatment/variant experience]

### Metrics

**Primary Metric:**

| Primary metric | Baseline measurement | Report links |
|----------------|---------------------|--------------|
| [Metric name] | [Current rate] | [Link] |

**Supporting Metrics:**

| Supporting metrics | Type | Baseline measurement | Report links |
|-------------------|------|---------------------|--------------|
| [Metric 1] | Secondary | [Baseline] | [Link] |
| [Metric 2] | Guardrail | [Baseline] | [Link] |

---

## **Designs**

[Link to Figma, screenshots, or design mockups]

---

## **Open Questions**

- [Question 1]
- [Question 2]

## Links

- **Experiment tracker**: [Link]
- **Related experiments**: [Links]
- **Background research**: [Links]
```

## Related skills

1. `/apollo-growth-product:experiment-pitch` — shape and pitch the initiative first
1. `/apollo-growth-product:experiment-writeup` (this skill) — append the detailed design
1. `/apollo-growth-product:experiment-record` — create the experiment tracker entry
1. `/apollo-growth-product:jira-task` — create the engineering ticket
1. `/apollo-growth-product:experiment-results` — update the page with results when it concludes

## Safety rules

- **Never fabricate metrics or baselines.** Only use data from analytics or provided context.
- **Always show the draft** before pushing to Notion or saving.
- **Don't leave placeholders.** If information is missing, ask rather than using `[TBD]`.
- **Preserve existing Notion page content** in append mode. Never overwrite the pitch.
- **Fill metric baselines** when data is available. Empty tables are a quality fail.
- **Be specific about the user journey.** Actual screens, buttons, flows, not generic descriptions.
- **Link to resources.** Always include analytics queries, Figma designs, and calculator links when available.
