---
name: publish-growth-product-doc
description: Publish a finished writeup, analysis, proposal, or report as a new page in a team documents database in Notion.
disable-model-invocation: true
requires_config: true
---

# Publish Growth Product Doc

Turn supplied material into one reader-first Notion page, show the exact draft, publish after approval, and verify the write.

Usage: `/apollo-growth-product:publish-growth-product-doc <text, file path, or Notion URL>`

Use this for publishing a new document. Don't use it for editing an existing page, or for roadmap, Jira, or experiment-tracker records.

## Configuration

Before doing anything else, read `config.md` from this skill's directory. It contains a YAML frontmatter block of variables this skill depends on.

For every `{{placeholder}}` you encounter while running this skill, substitute the matching value from `config.md`'s frontmatter.

`config.md` ships with the skill, so treat it as **defaults and documentation, read-only**. A plugin update replaces it.

Your own answers live in `~/.claude/plugin-config/apollo-growth-product/publish-growth-product-doc.md`. Read that file first when it exists and let it override the shipped values, remembering that a saved empty string is a deliberate answer, not a missing one.

If a value is still `<UNSET>` after that merge, ask the user for it, then write the answer to `~/.claude/plugin-config/apollo-growth-product/publish-growth-product-doc.md` (creating the directory if needed). Never write answers back into the skill's own `config.md`; they'd be wiped on the next plugin update. Do this once per session.

**Destination:** `{{docs_database_name}}`
**Data source:** `{{notion_docs_data_source}}`

## 1. Gather the source

Use whatever was supplied: text in the request, a document produced earlier in this conversation, a local file path, or a Notion URL (fetch it). Reach for a repo search only when related context probably exists but you don't know the path.

Keep the requested slice intact. A narrow summary stays narrow even when its source file contains a broader audit or working notes. The user's most recent edits win over anything earlier.

Never invent metrics, decisions, owners, dates, or links. If the source is too thin to publish, ask for the one missing piece rather than filling the gap yourself.

## 2. Read the live schema

Fetch `{{notion_docs_data_source}}` before every publish. The schema changes without warning, and a stale property name or select option gets the write rejected. If what you see differs from the reference below, follow the live version and say so in the review.

Reference schema:

| Property | Type | Value |
|---|---|---|
| `{{docs_title_property}}` | title | Page title |
| `{{docs_type_property}}` | multi-select | Pick one. JSON array: `"[\"Report\"]"` |
| `{{docs_author_property}}` | person | JSON array of user IDs: `"[\"{{default_notion_user_id}}\"]"` |
| `{{docs_team_property}}` | select | One of {{docs_team_options}} |
| `Description` | text | 1-2 sentences |

`Created on` and `Last edited time` are system-managed. Leave them alone.

If a create fails on the author property, re-resolve the user ID with `notion-get-users` and take the `person` entry, not the bot.

Reference `{{docs_type_property}}` options: {{docs_type_options}}. Follow the live list when it differs.

## 3. Shape the page

Write for whoever opens it and whatever they need to do next. Use the simplest structure that scans well. If the supplied document already has a clear shape, keep it. Don't bolt a template onto it.

- Title goes in `{{docs_title_property}}`. Don't repeat it as an H1 in the body.
- `Description` says what's inside and why someone would click. Concrete, not a category label.
- `{{docs_type_property}}`: one option, chosen by the document's primary job. Results recap or general summary → `Report`. Evidence-backed interpretation → `Analysis`. Recommended change → `Proposal`. Show your pick in the review so it can be overridden.
- `{{docs_team_property}}`: set it only when the source clearly points at one team. Leave it unset when scope is ambiguous, and flag that in the review.
- Cross-functional audience: push source lists, query breadcrumbs, and methodology notes to the bottom.
- Keep leading indicators separate from business outcomes. Label weak or incomplete evidence plainly.

Follow `references/voice-style-guide.md` for any prose you write or substantially rewrite. When the user supplies final text and asks to publish it as-is, preserve their wording exactly.

For body formatting, read `notion://docs/enhanced-markdown-spec` via `notion-fetch` before creating the page. If that resource is unavailable, stick to headings, paragraphs, lists, links, and code blocks, which are safe everywhere.

## 4. Review before writing

Show the complete draft before touching Notion:

1. Every property and its proposed value, including any intentionally unset team.
1. The full page body.
1. Assumptions, evidence gaps, and any live-schema differences.
1. The destination database.

Then ask for approval or adjustments.

"push it", "publish this", or "approved" counts as approval when it points at the draft you displayed or at exact text the user supplied. A general "help me publish this" does not authorize creating a page they haven't seen.

## 5. Create and verify

After approval:

1. Create exactly one page with `notion-create-pages`, `parent.data_source_id: "{{notion_docs_data_source}}"`.
1. Send only approved properties and body. Preserve links exactly.
1. Fetch the created page back.
1. Compare title, properties, opening, section headings, links, and ending against the approved draft.
1. If the gap is an encoding or formatting glitch, fix it once and re-fetch. If content would need a substantive change, or the second write fails, stop and report.

Return the page URL and name anything left unset or needing manual follow-up. Create nothing else: no other Notion page, no Jira issue, no local file.

### Call shape

```javascript
notion-create-pages({
  parent: { data_source_id: "{{notion_docs_data_source}}" },
  pages: [{
    properties: {
      "{{docs_title_property}}": "Page title here",
      "{{docs_type_property}}": "[\"Report\"]",
      "{{docs_author_property}}": "[\"{{default_notion_user_id}}\"]",
      "{{docs_team_property}}": "Conversion",
      "Description": "What this page contains and why someone would open it."
    },
    content: "## First section\n..."
  }]
})
```

## Failure handling

- Notion unreachable: return the complete ready-to-publish draft and name the blocked step.
- Create rejected: re-fetch the data source, diff the rejected properties against the live schema, and retry only if the fix preserves approved content.
- A destination link that resolves to a page *inside* the database: publish to its parent data source, not as a child of that page.
- Never guess a database ID, select option, user ID, or Notion markdown shape.

## Bundled references

- `references/voice-style-guide.md` — the voice rules for any prose you write. Swap in your team's guide if you have one.
