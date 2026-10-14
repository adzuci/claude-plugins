# Variable Taxonomy

Use this as a checklist during Phase 2's LLM pass. Six categories, with examples drawn from real Claude Code skills. For each file you read, walk this list mentally — anything that fits a category is a candidate variable.

## 1. External IDs

Identifiers for resources in third-party systems. Almost always team-specific.

**Examples:**

- Notion database IDs: `collection://231ab2b3-b496-806b-9c96-000bb1145185`
- Notion page IDs: `1a6ab2b3-b496-8024-aff4-000bf73fdda3`
- Amplitude project IDs: `241072`
- Jira project keys: `CVR`, `GAX`, `EPD`
- Slack channel names: `#growth-conversion-pd`, `#eng-platform`
- Asana project / portfolio GIDs
- Google Drive folder IDs
- GitHub repo slugs: `apollo-io/main`
- Calendar IDs

**Suggested variable names:** `<system>_<resource>_<role>`, e.g., `notion_roadmap_db`, `jira_default_project`, `slack_status_channel`.

## 2. People

Anyone named in a way that wouldn't make sense for a different user.

**Examples:**

- Default assignees ("Sarah", "@jamie")
- Manager names
- Email addresses (`mw@mattwoods.io`, team distribution lists)
- @-handles in templates

**Suggested variable names:** `default_assignee`, `manager_name`, `user_email`, `team_lead_handle`.

Edge case: if the source skill says "use the assignee mentioned in the Granola transcript", that's *not* a variable — it's a runtime input. Only extract values that are static across runs.

## 3. Org Context

Names of teams, companies, products, fiscal calendars — anything that says "this user works at X."

**Examples:**

- Team name: `Growth Conversion`, `Pricing & Packaging`
- Company / product: `Apollo.io`, `Apollo plan`, `Apollo trial`
- Fiscal calendar: `FY27Q1`, `quarters run Feb-Apr...`
- Internal jargon: `M2A nudge`, `CVR pod`, `OKR cadence`

**Suggested variable names:** `team_name`, `company_name`, `product_name`, `fiscal_quarter_format`.

For fiscal calendar: this is often complex enough (start months, naming convention) that it's worth a single `fiscal_calendar_definition` variable that points at a doc, rather than trying to parameterize the whole calendar logic.

## 4. File Paths

Hardcoded paths that point inside a specific user's filesystem.

**Examples:**

- `~/code/notes/projects/...`
- `~/code/notes/personal/journal/...`
- `projects/references/voice-style-guide.md`
- `~/Documents/work/templates/...`

**Suggested variable names:** descriptive of what's at the path, not the path itself: `voice_style_guide_path`, `journal_directory`, `templates_directory`.

If the path points at something that's a *dependency* (a voice guide, another skill's output), classify under "Dependencies" in the review, not just "File paths."

## 5. URLs

Specific external links baked into prompts or templates.

**Examples:**

- Calendly: `https://calendly.com/your-name/feedback`
- Internal dashboards: `https://apollo.amplitude.com/...`
- Doc shortlinks: `go/team-roadmap`
- Help center / changelog URLs

**Suggested variable names:** `<purpose>_url`, e.g., `interview_booking_url`, `roadmap_dashboard_url`.

## 6. Dependencies (cross-skill / shared infra)

References to other skills, shared knowledge bases, or external tools that aren't config values per se but require the new user to wire something up.

**Examples:**

- "Read the voice style guide at `projects/references/voice-style-guide.md`"
- "Search qmd collection `brain` for prior context"
- "Use the `/journal` skill to capture..."
- "The MCP server `mcp__notion__*` must be configured"

**Suggested variable names:** `voice_style_guide_path`, `qmd_collection_name`, `required_mcp_servers`.

These get special treatment in Phase 4: the generalized SKILL.md should explicitly tell the new user how to point the dependency at their own equivalent, or what to do if they don't have one ("set this to an empty string and the skill will skip the voice-guide step").

### Bundling vs. extracting documentation dependencies

When a dependency is a **static document** (markdown / text / PDF) that the skill *reads* as guidance — voice guides, glossaries, rubrics, example libraries, taxonomies — there's a third option beyond "extract as variable" or "leave alone": **bundle it into the skill**. Phase 2's third pass surfaces these candidates and Phase 3 lets the user choose.

Rule of thumb:

- If the doc *defines how the skill behaves* (a voice guide that the skill must follow to produce correct output), default to **bundle**. New users get the same behavior the original author got, with no setup required.
- If the doc is *user-specific data* (a list of teammates, a personal journal, a private playbook), default to **extract as variable**. Each user supplies their own.
- If the doc is large, frequently changing, or contains private info, also lean toward **extract as variable** — bundling stale or sensitive content is worse than asking each user to point at their own copy.

A bundled doc moves into the new skill's `references/` folder and the SKILL.md path reference becomes `references/<filename>`. No config entry is created for it.

______________________________________________________________________

## What NOT to extract

These look like candidates but aren't. Leave them as literals.

- **Workflow conventions**: "keep titles under 80 chars", "always use Jira markdown", "leave effort blank" — these are the skill's opinions, not the user's config.
- **Banned phrases / style rules embedded in the skill**: if the skill says "never use em dashes", that's an instruction to the model, not a user variable.
- **Format strings**: a date format like `YYYY-MM-DD` is a convention, not a config.
- **Runtime inputs**: anything the user provides each time they invoke the skill (a meeting URL, a task description) is not a variable — it's an argument.
- **Generic terms**: "the user", "the team", "engineering" — these are already generic.

When in doubt: ask "would two different users at two different companies have different values for this?" If yes, extract. If no, leave alone.
