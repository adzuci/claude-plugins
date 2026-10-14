---
name: idea
description: Capture a rough product idea into a Notion ideas database, structured with problem framing, alternative approaches, open questions, and next steps to pitch.
disable-model-invocation: true
requires_config: true
---

# Idea Capture

Capture rough product ideas (screenshots, dictated thoughts, raw data) and structure them into your team's Notion ideas database. This sits at the front of the pipeline: ideas here are early-stage and exploratory.

Usage: `/apollo-growth:idea <rough idea, screenshot path, or URL> [--from "Person Name"]`

## Configuration

Before doing anything else, read `config.md` from this skill's directory. It contains a YAML frontmatter block of variables this skill depends on.

For every `{{placeholder}}` you encounter while running this skill, substitute the matching value from `config.md`'s frontmatter.

`config.md` ships with the skill, so treat it as **defaults and documentation, read-only**. A plugin update replaces it.

Your own answers live in `~/.claude/plugin-config/apollo-growth/idea.md`. Read that file first when it exists and let it override the shipped values, remembering that a saved empty string is a deliberate answer, not a missing one.

If a value is still `<UNSET>` after that merge, ask the user for it, then write the answer to `~/.claude/plugin-config/apollo-growth/idea.md` (creating the directory if needed). Never write answers back into the skill's own `config.md`; they'd be wiped on the next plugin update. Do this once per session and assume the values are stable after that.

If a `{{placeholder}}` has no matching key in `config.md`, that's a bug in this skill. Tell the user and proceed with a sensible default if you can.

**Target DB data source:** `{{notion_ideas_data_source}}`

## Workflow

Execute these steps **in order**.

### Step 1: Parse arguments

Check the arguments for any combination of:

- **Dictated text** — rough idea description, observations, raw thoughts
- **Screenshot paths** — images to read for context
- **URLs** — Notion pages, analytics charts, or other references
- **File references** — local markdown files or data
- **Person name** — who originated the idea (e.g. "from Pawel", "Dominika's idea")

If no arguments were given, ask:

> "What's the idea? I can work with:
>
> - **Rough description**: Dictate or type the idea, however messy
> - **Screenshots**: Paths to screenshots that show the problem or opportunity
> - **Links**: Notion pages, analytics charts, or other URLs for context
> - **Who surfaced it**: Name(s) of people involved (I'll default to you if not specified)"

### Step 2: Gather and synthesize context

1. **Read provided inputs** — screenshots, files, or URLs from arguments.
1. **Fetch linked Notion pages** — use `notion-fetch` for any Notion URLs.
1. **Auto-scan local context** — glob and read `{{team_context_dirs}}` for planning docs, idea drafts, team context, metrics, and roadmap. Skip this when the value is empty.
1. **Search existing ideas** — use `notion-search` to find related or duplicate ideas in the DB. If similar ideas exist, flag them:

> "I found a related existing idea: **[title]** ([link]). Want me to continue creating a new one, or would you rather update the existing idea?"

Report what context was found before drafting.

### Step 3: Structure the idea

#### A) DB properties

| Property | Value | Notes |
|----------|-------|-------|
| **{{idea_title_property}}** | Concise idea name | Title property |
| **Goal** | Best fit from options | Select, see valid values below |
| **Surface Area** | Best fit from options | Select, only if clearly applicable |
| **Status** | `{{idea_default_status}}` | Always default to this |
| **Impact** | 1-5 | Only if the user provides a score |
| **Effort** | 1-5 | Only if the user provides a score |
| **Confidence** | 1-5 | Only if the user provides a score |
| **Added by** | Resolved user ID | Person, see Step 3B |

**Valid Goal values:** {{idea_goal_options}}

**Valid Surface Area values:** {{idea_surface_area_options}}

If the live database offers options that aren't in those lists, follow the live schema and say so in the review. Select options drift.

#### B) Resolve "Added by"

1. Call `notion-get-users`.
1. If a team member name was provided in arguments, search for their Notion user ID and set it as "Added by".
1. If no match is found or no name was given, default to `{{default_notion_user_id}}`.
1. Regardless of who "Added by" resolves to, always include a **Contributors** line in the page content listing everyone involved.

#### C) Page content

Generate Notion-flavored markdown with these sections:

```text
**Contributors:** [Names of everyone involved in surfacing this idea]

# Problem / Opportunity

[What's the problem or opportunity? Include source attribution: who noticed it, where it came
from, what data or observation triggered it.]

# Proposed Approach

[The core idea. Be specific about who it affects, what changes, and where in the product.]

# Iterations & Alternatives

[2-3 variations or alternate approaches to explore. This is what makes this skill different from
a plain capture: we want the solution space, not just one approach.]

1. **[Variation name]** — [Brief description of this alternative]
2. **[Variation name]** — [Brief description of this alternative]
3. **[Variation name]** — [Brief description of this alternative]

# Open Questions

- [Things we don't know yet that would affect the approach]
- [Data we'd need to validate assumptions]
- [Feasibility unknowns]

# Next Steps to Pitch

- [ ] [Concrete action to upgrade this from rough idea to roadmap-ready pitch]
- [ ] [e.g. Size the opportunity with product analytics]
- [ ] [e.g. Get user research or qualitative signal]
- [ ] [e.g. Check feasibility with eng]
- [ ] [e.g. Review prior experiments in this area]
```

### Step 4: Review draft

Present the complete draft in chat. Show the properties table and the full page content, then ask:

> "Here's the draft idea. Review the properties and content before I create it in the Ideas DB. Let me know if anything needs adjusting."

Make any requested changes. Re-check that:

- No placeholders remain, ask if info is missing
- Contributors line is present and accurate
- Goal is a valid value from the list
- Status is `{{idea_default_status}}`
- Iterations section has real alternatives, not restatements

### Step 5: Create in Notion

After approval:

1. Call `notion-create-pages` with `parent.data_source_id` set to `{{notion_ideas_data_source}}`, the properties from Step 3A, and the content from Step 3C.
1. Confirm successful creation with the page URL.

### Step 6: Suggest next steps

> "Idea captured. When you're ready to formalize this into a roadmap item, use `/apollo-growth-product:experiment-pitch` to shape and pitch it."

If relevant, also suggest linking to related existing ideas found in Step 2, and name the specific open questions worth investigating first.

## MCP call reference

```javascript
notion-create-pages({
  parent: { data_source_id: "{{notion_ideas_data_source}}" },
  pages: [{
    properties: {
      "{{idea_title_property}}": "Idea title here",
      "Goal": "FTP",
      "Surface Area": "Feature Gates",
      "Status": "{{idea_default_status}}",
      "Added by": "[\"user-id-here\"]"
    },
    content: "**Contributors:** ...\n\n# Problem / Opportunity\n..."
  }]
})
```

Property format notes:

- `Added by`: JSON array of user IDs, `"[\"user-id\"]"`
- `Impact`, `Effort`, `Confidence`: numbers 1-5, omit if not provided
- `Goal`, `Surface Area`, `Status`: single-select strings

## Related skills

1. `/apollo-growth:ideation-capture` — batch-capture a whole brainstorm session
1. `/apollo-growth:idea` (this skill) — capture one idea with alternatives
1. `/apollo-growth-product:experiment-pitch` — pressure-test and pitch it to the roadmap
1. `/apollo-growth-product:experiment-writeup` — design the experiment
1. `/apollo-growth-product:experiment-record` — create the experiment tracker entry
1. `/apollo-growth-product:jira-task` — create the engineering ticket
1. `/apollo-growth-product:experiment-results` — record results

## Safety rules

- **Never fabricate data.** Only use information provided or found in context files.
- **Always show the draft** before creating in Notion.
- **Don't leave placeholders.** If information is missing, ask rather than using `[TBD]` or brackets.
- **Default to `{{idea_default_status}}`.** Never set a more advanced status on capture.
- **Flag duplicates.** If a similar idea already exists, surface it before creating a new entry.
- **Include real alternatives.** The Iterations section needs genuinely different approaches, not minor rewordings.
