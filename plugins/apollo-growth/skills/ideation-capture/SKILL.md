---
name: ideation-capture
description: Batch-process a brainstorm session (FigJam CSV, bullet list, or transcript) into individual Notion idea pages plus a session summary one-pager.
disable-model-invocation: true
requires_config: true
---

# Ideation Session Capture

Batch-process ideas from a brainstorming session (FigJam voting CSV, bullet lists, or dictated notes) into individual pages in your team's Notion ideas database, then create a session summary one-pager in your team docs database.

This sits *before* `/apollo-growth:idea` in the pipeline. It captures the raw output of a group brainstorm as lightweight entries that can be expanded later.

Usage: `/apollo-growth:ideation-capture <csv-path-or-bullets> [--goal "Goal Name"] [--transcript <path>]`

## Configuration

Before doing anything else, read `config.md` from this skill's directory. It contains a YAML frontmatter block of variables this skill depends on.

For every `{{placeholder}}` you encounter while running this skill, substitute the matching value from `config.md`'s frontmatter.

`config.md` ships with the skill, so treat it as **defaults and documentation, read-only**. A plugin update replaces it.

Your own answers live in `~/.claude/plugin-config/apollo-growth/ideation-capture.md`. Read that file first when it exists and let it override the shipped values, remembering that a saved empty string is a deliberate answer, not a missing one.

If a value is still `<UNSET>` after that merge, ask the user for it, then write the answer to `~/.claude/plugin-config/apollo-growth/ideation-capture.md` (creating the directory if needed). Never write answers back into the skill's own `config.md`; they'd be wiped on the next plugin update. Do this once per session.

If a `{{placeholder}}` has no matching key in `config.md`, that's a bug in this skill. Tell the user and proceed with a sensible default if you can.

**Ideas DB data source:** `{{notion_ideas_data_source}}`
**Team docs DB data source:** `{{notion_docs_data_source}}`

## Workflow

Execute these steps **in order**.

### Step 1: Parse arguments

Check the arguments for any combination of:

- **CSV file path** — a FigJam voting export (columns: Votes, Content, Created by)
- **Bullet-point ideas** — inline list, each optionally prefixed with vote count and author
- **Transcript file path** — a meeting transcript for session context and enriched idea summaries
- **Session goal** — the Goal property value applied to every idea in the session
- **Surface Area override** — a default Surface Area when it clearly applies
- **Notion URLs or file paths** — additional context references

If no arguments were given, ask:

> "What brainstorming session am I capturing? I need:
>
> - **Ideas input**: Path to a FigJam CSV export, or paste the ideas as a bullet list (include author names and vote counts if available)
> - **Session goal**: Which Goal does this map to? Valid values: {{idea_goal_options}}
> - **Transcript** (optional): Path to a meeting recording transcript for additional context
> - **Surface Area** (optional): Default Surface Area if most ideas share one"

### Step 2: Gather context and build the user map

#### A) Read input data

1. **CSV file**: read the file and parse each row into `{votes, content, author}`.

   - First row is always the header, skip it
   - Content may contain commas and newlines, handle quoted CSV fields
   - Sort ideas by vote count descending
   - Include ideas with 0 votes, there's no minimum threshold

1. **Bullet list**: parse each bullet into an idea. Look for patterns like `(3 votes)`, `(N)`, `- Author Name`, or `[Author]` to extract metadata.

1. **Transcript**: if provided, read it and extract the session topic and framing, discussion highlights that enrich specific ideas, the full participant list, key themes or tensions, and what's been tried before.

#### B) Build the Notion user map

1. Call `notion-get-users` to retrieve workspace users.
1. Build a lookup map, normalizing each display name to lowercase.
1. For each unique author name from the input, try exact match (case-insensitive), then first-name match, then last-name match.
1. If no match is found, flag as **unresolved**, default to `{{default_notion_user_id}}`, and note it for the review step.
1. Report resolved and unresolved mappings.

#### C) Auto-scan local context

Glob and read `{{team_context_dirs}}` for planning docs, prior brainstorm outputs, and team context. Skip this when the value is empty. Report anything relevant.

#### D) Check for duplicates

Use `notion-search` with the session goal as a query to surface existing ideas that may overlap. Flag potential duplicates for the review step, don't block on them.

### Step 3: Structure all ideas

#### A) DB properties

| Property | Value | Notes |
|----------|-------|-------|
| **{{idea_title_property}}** | Concise idea title | Rewrite raw content into a clear, scannable title (5-12 words). Imperative or noun-phrase style. |
| **Goal** | Session goal value | Same for all ideas in the session |
| **Surface Area** | Best fit if obvious | Only set when clearly applicable, omit if ambiguous |
| **Status** | `{{idea_default_status}}` | Always |
| **Added by** | Resolved user ID | From the user map, flagged if unresolved |

**Valid Goal values:** {{idea_goal_options}}

**Valid Surface Area values:** {{idea_surface_area_options}}

**Do NOT set** Impact, Effort, or Confidence. Those need individual assessment, not batch defaults.

#### B) Page content (lightweight)

For each idea, generate concise Notion-flavored markdown:

```text
**Session:** [Session topic] ([date])
**Votes:** [N] | **Submitted by:** [Author name]

[1-3 sentence summary. Be specific about what changes, who it affects, and where in the product.
If the transcript has discussion about this idea (what was said, why it resonated, concerns
raised), weave that in naturally. Don't pad or repeat the raw content verbatim.]
```

This is intentionally lightweight. Quick, scannable entries for batch capture. Individual ideas get expanded later.

**Title quality matters more than content length.** A good title lets someone scan the database and understand each idea without clicking in.

Good titles:

- "Move annual decision to onboarding survey"
- "Show per-month price instead of annual total"
- "Lifecycle upgrade trigger at 75% credit usage"

Bad titles:

- "Better pricing" (too vague)
- "Move the decision earlier in the journey so users pick annual during onboarding" (too long, save detail for content)

### Step 4: Review parsed ideas (REVIEW GATE 1)

Present ALL parsed ideas in a table sorted by votes descending:

```text
## Parsed Ideas — [Session Topic] ([Date])

[N] ideas parsed from [source type]. [M] authors resolved, [K] unresolved.

| # | Idea Title | Votes | Author | Goal | Surface Area | Added by (Notion) |
|---|-----------|-------|--------|------|-------------|------------------|
```

List potential duplicates and unresolved authors underneath, then ask:

> "Here are the [N] ideas I parsed from the session. Review the titles, author mappings, and property assignments before I create them in the Ideas DB.
>
> You can edit titles or properties, remove ideas, resolve author mappings, or flag duplicates to skip.
>
> Confirm when ready to proceed."

Make any requested changes. Re-check that titles are concise and scannable, Goal is a valid value, Status is `{{idea_default_status}}` for all, unresolved authors are acknowledged, and no obvious duplicates are being created.

### Step 5: Create idea pages in Notion

After approval, call `notion-create-pages` with `parent.data_source_id` set to `{{notion_ideas_data_source}}` and an array of all approved ideas. Confirm the count created.

### Step 6: Draft the session summary (REVIEW GATE 2)

Using all gathered context, draft a session summary one-pager.

#### A) Summary DB properties

| Property | Value | Notes |
|----------|-------|-------|
| **{{docs_title_property}}** | "[Session Topic] Brainstorm — [Date]" | Title property |
| **{{docs_author_property}}** | `{{default_notion_user_id}}` | Person |
| **Description** | "Session summary: [topic] brainstorm with [N] ideas from [M] participants" | Text |

#### B) Summary page content

```text
# [Session Topic] Brainstorm Summary

**Date:** [Session date]
**Participants:** [All unique authors/participants from CSV and transcript]
**Ideas captured:** [N] (linked to the ideas database)

## Top Themes

### [Theme Name] ([N] ideas, [total votes] votes)

[2-3 sentences synthesizing the theme. What's the underlying insight? Why did it resonate? What
prior evidence supports or challenges it?]

**Top ideas:**
- [Idea title] ([votes] votes) — [one-line summary]

[Repeat for 3-5 themes, ordered by combined resonance]

## Most Actionable Next Steps

- [ ] [Concrete next action, referencing specific ideas or themes]

## Key Session Context

[If a transcript was provided: distill the most important context shared during the session. What's
been tried, what's working, key constraints that inform how to evaluate these ideas. This helps
someone who wasn't in the meeting. Omit this section when there's no transcript.]
```

Group ideas by resonance, weighing both vote count AND discussion depth. An idea with 2 votes that sparked a rich 5-minute discussion may be more resonant than one with 3 votes nobody discussed.

Present the summary and ask:

> "Here's the session summary one-pager. Review the themes, next steps, and overall framing before I create it. Let me know if anything needs adjusting."

### Step 7: Create the session summary in Notion

After approval, call `notion-create-pages` with `parent.data_source_id` set to `{{notion_docs_data_source}}` and the page from Step 6. Confirm with the page URL.

### Step 8: Suggest next steps

> "Session captured. [N] ideas added to the idea tracker and a summary doc created.
>
> Suggested next steps:
>
> - Use `/apollo-growth:idea` to expand promising ideas into full writeups with iterations and open questions
> - Use `/apollo-growth-product:experiment-pitch` to formalize top-voted ideas into roadmap pitches
> - Share the summary doc with the team for async feedback"

Call out specific high-vote or heavily discussed ideas by name.

## CSV parsing reference

### FigJam export format

```csv
Votes,Content,Created by
4,"Move the decision earlier in the journey...",Manuela Moncayo
3,"instead of reducing price, include inbound...",Piotr Pawlik
```

Parsing rules:

- First row is always the header, skip it
- Content may contain commas, newlines, and quotes, handle standard CSV quoting
- "Created by" maps to the author name for Notion user resolution
- Votes of 0 are still captured
- Sort by vote count descending when presenting

### Bullet list format

```text
- Move annual decision earlier in journey (4 votes, Manuela)
- Bundle inbound credits as annual-only perk (3 votes, Piotr)
```

Look for `(N votes)` or `(N)` patterns for vote counts, and author names after the last comma or in parentheses. If no votes or authors are found, ask the user to clarify the format.

## Safety rules

- **Never fabricate ideas or context.** Only use what's in the provided input.
- **Always show BOTH review gates.** The parsed ideas table and the session summary each need approval before any Notion write.
- **Don't leave placeholders.** Ask rather than using `[TBD]`.
- **Default to `{{idea_default_status}}`.** Never set a more advanced status.
- **Don't set Impact/Effort/Confidence.** Those need individual assessment.
- **Handle unresolved authors gracefully.** Flag them clearly, default to `{{default_notion_user_id}}`, and always include the original author name in page content regardless.
- **Sort by votes** so the most resonant ideas surface first.
- **Keep page content lightweight.** Resist expanding into full idea format. These are batch captures meant for scanning.
- **Flag potential duplicates** before creating new entries.
