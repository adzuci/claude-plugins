---
name: skill-generalizer
description: Turn an existing skill into a shareable one by extracting team-specific values into a config.md sidecar and bundling the reference docs it depends on.
disable-model-invocation: true
---

# Skill Generalizer

Generalize an existing skill so other people on other teams can install and adapt it. The original skill stays untouched. The output is a new skill folder at a path you specify, with all team-specific values lifted into a `config.md` sidecar. The generalized skill, on first use by someone new, reads `config.md` for defaults, asks for any missing values, and saves them under `~/.claude/plugin-config/` so they survive plugin updates.

## When to use this skill

- "Help me generalize my jira-task skill so other PMs can use it"
- "Turn this skill into something I can share through a marketplace"
- "Extract the team-specific stuff out of [skill]"
- "Make [skill] team-agnostic" / "make this skill portable"
- "Prep this skill for sharing"

If the user is creating a new skill from scratch, point them at `skill-creator` instead. This skill is for taking something that already exists and lifting out the hardcoded bits.

## Why this matters

Most personal skills bake in dozens of context-specific values: a Notion database ID, a Slack channel, a Jira project key, a manager's name, the path to a voice/style guide, a fiscal calendar. Each of these is a small thing on its own, but in combination they make a skill unsharable. A new user can't just install and run; they have to grep the SKILL.md, find every hardcoded value, edit it, and pray they didn't miss one. This skill solves that by surfacing the variables, getting the user to confirm them, and producing a clean version that explicitly tells the next user what they need to fill in.

The persistence mechanism (config.md) matters too. Without it, every new user re-answers the same questions every session, and the friction kills adoption.

## Inputs you need from the user

Before starting, confirm:

1. **Source skill** — a name (looked up under `~/.claude/skills/<name>/`) or an absolute path to a skill folder.
1. **Output path** — where the generalized version should be saved. When you're working inside the `apolloio/claude-plugins` checkout, suggest `plugins/<plugin-name>/skills/<original-name>/` so the result is installable straight from the marketplace. Otherwise propose `~/Desktop/<original-name>-shareable/` and let them redirect.
1. **Whether to package** at the end (run `package_skill.py` to produce a `.skill` archive ready for marketplace upload).

## The 5-phase workflow

### Phase 1: Read the source skill

Read the source SKILL.md fully. Then read every file it references — scripts in `scripts/`, references in `references/`, assets it points at. Don't skim. The hardcoded values are often scattered across reference files and helper scripts, not just the main SKILL.md.

Build a mental list of every file you've read so you can rewrite all of them in Phase 4.

### Phase 2: Detect candidate variables and bundleable docs

Three passes:

1. **Pattern pass** — Run `scripts/detect_patterns.py` against the source skill folder. It catches the obvious mechanical stuff: Notion `collection://` IDs, hex UUIDs, email addresses, `#channel` names, `~/`-prefixed and `/Users/...` paths, Calendly URLs, Jira project keys in caps. Output is JSON shaped as `{unique_candidates: [{category, pattern_name, value, occurrences: [{file, line, context}]}], total_occurrences}`. Candidates are already collapsed by value, so each entry is one variable with every place it appears.

1. **LLM pass (you)** — Read each file yourself with the taxonomy in `references/variable-taxonomy.md` in mind. Catch the contextual stuff that regex can't: team names ("Growth Conversion"), product references ("Apollo plan"), fiscal calendars ("FY27Q1"), preferred-assignee names, default issue types, dashboard URLs, anything that's clearly *this user's* context and would be different for someone else.

Important judgment call: **don't extract conventions that are part of the skill's value**. If the source skill says "keep titles under 80 chars" or "always use Jira markdown formatting" or "leave effort blank for eng review", those are opinionated workflow rules — leave them as-is. The next user can override them by editing SKILL.md if they want, but they shouldn't be config variables. Extract things the user would *fill in*, not things they'd *change their mind about*.

For each candidate, capture:

- `current_value` — what's literally in the file

- `suggested_name` — canonical snake_case (e.g., `jira_project_key`, `team_name`, `voice_style_guide_path`)

- `category` — one of: external_id, person, org_context, file_path, url, dependency

- `suggested_description` — one sentence explaining what this is, in language a stranger would understand

- `occurrences` — list of `{file, line}` where this value (or close variants) appears

  Collapse duplicates: if a team name shows up in 8 places, that's one variable, not eight.

1. **Bundleable-doc pass** — A path-typed variable can mean two different things, and they need different treatment:

   - **The file is the user's own thing** (their team's roadmap database export, their local journal). Keep it as a config variable. The new user points it at their own equivalent.
   - **The file is reference documentation that informs how the skill behaves** (a voice/style guide, a glossary, a writing rubric, an example library, a checklist). The skill reads it for guidance, not for user-specific data. In that case, *ship the doc with the skill* — copy it into the new skill's `references/` folder so it installs as one unit and the new user gets the same behavior the original author got.

   To find these candidates, walk every file_path / dependency variable from passes 1 and 2 and ask:

   - Does the path point at a markdown / text / pdf file *outside* the source skill folder?
   - When the source SKILL.md references it, is the verb "read" / "follow" / "use as reference" / "consult" — i.e., the skill is consuming it as guidance, not writing to it?
   - If you actually open the file (use Read), does its content look like documentation/guidance (style rules, examples, taxonomy, prose) rather than user-specific data (a list of their teammates, their Notion DB schema, their personal journal)?

   If yes to all three, this is a **bundleable doc**. Capture it separately:

   - `source_path` — the absolute or `~/`-prefixed path
   - `current_size_lines` — so the user can decide if it's reasonable to ship inline
   - `suggested_bundle_filename` — what to call it inside the new skill's `references/` (default: the basename of the source file)
   - `referenced_at` — list of `{file, line}` in the source skill that point at it
   - `summary` — one sentence describing what the doc is, derived from skimming it

   Don't auto-bundle. Phase 3 asks the user per doc; some docs are private team artifacts the user wouldn't want to ship publicly.

### Phase 3: Review with the user

Present the candidates grouped by category. For small skills (under ~6 candidates total), do one consolidated review. For larger skills, split into 2-3 batches by category so each `AskUserQuestion` round is digestible.

For each candidate, the user needs to be able to:

- **Confirm or reject** the candidate (rejecting means leave the literal value in place)
- **Rename** the canonical variable
- **Edit the description** — this is what other users will see in the Setup Guide; clarity matters
- **Add a default value** — used when config.md leaves it as `<UNSET>`; useful for sensible fallbacks

Cross-skill / shared-infra references (qmd collections, voice style guides, other skills) get their own group called **Dependencies**. The user confirms a variable name and description for each. These get extra treatment in Phase 4: the generalized SKILL.md will include a paragraph telling the new user how to point the dependency at their own equivalent (or remove the reference if they don't have one).

#### Bundleable docs review

After the variable groups, present each bundleable-doc candidate from Phase 2's third pass. For each one, show:

- The doc's path, size in lines, and one-sentence summary
- Where in the source skill it's referenced (file + line)
- A preview snippet (first ~20 lines) so the user remembers what it is

Then ask which of three things to do with it:

- **Bundle into the skill (Recommended for guidance docs)** — Copy the file into the new skill's `references/<filename>` and rewrite every reference in SKILL.md to point at the bundled copy (`references/<filename>`). No config variable. New users get the doc automatically; the skill behaves the same out of the box as it did for the original author. Best for things like voice guides, glossaries, rubrics, taxonomies — content that defines *how* the skill works.

- **Extract as a config variable** — Path becomes a `{{var_name}}` placeholder, user supplies their own version (or empty string to skip). Best for things that should be team-specific: each team's own style guide, their own example library.

- **Leave as literal** — The path stays exactly as it was. Almost never the right answer for cross-machine references; only useful when the path is a generic system location every machine has (rare).

Default to recommending **Bundle** when the doc is short, looks like generic guidance, and the source skill clearly depends on its content for behavior. Default to **Extract as variable** when the doc looks team-specific, contains private info, or is large enough that bundling would bloat the skill.

If the user picks Bundle, also ask: keep the original filename, or rename? Renaming matters when the source path is buried (`projects/references/voice-style-guide.md` → just `voice-style-guide.md`).

### Phase 4: Rewrite into a generalized skill

Create the output folder. Copy the source structure. Then transform:

#### `config.md`

Use the template at `references/config-md-template.md`. YAML frontmatter at the top holds every variable as a key with `<UNSET>` as the value (or the user-specified default, if any). Markdown body below documents each variable with the description from Phase 3.

Example:

```markdown
---
team_name: "<UNSET>"
jira_project_key: "<UNSET>"
slack_channel: "<UNSET>"
notion_roadmap_db: "<UNSET>"
voice_style_guide_path: "<UNSET>"
preferred_assignees: []
---

# Setup Guide

This file ships with the skill: defaults and documentation, replaced on update.
Run the skill and it saves your answers to
`~/.claude/plugin-config/<plugin>/<skill>.md`, which survives updates.

## team_name
Your team name as it appears in status updates, e.g. "Growth Conversion".

## jira_project_key
The Jira project key new tickets default to, e.g. "CVR".

[...]

## Dependencies

### voice_style_guide_path
Path to a markdown file that defines your team's writing voice. The skill
reads this before drafting prose. If you don't have one, set this to an
empty string and the skill will skip the voice-guide step.
```

#### Generalized `SKILL.md`

Same body as the source, but every extracted value is replaced with `{{var_name}}`. Add a new "## Configuration" section at the very top (right after the frontmatter), using this exact wording so it's recognizable:

```markdown
## Configuration

Before doing anything else, read `config.md` from this skill's directory.
It contains a YAML frontmatter block of variables this skill depends on.

For every `{{placeholder}}` you encounter while running this skill,
substitute the matching value from `config.md`'s frontmatter.

`config.md` ships with the skill, so treat it as defaults and
documentation, read-only. A plugin update replaces it.

Your own answers live in `~/.claude/plugin-config/<plugin>/<skill>.md`.
Read that file first when it exists and let it override the shipped
values, remembering that a saved empty string is a deliberate answer,
not a missing one.

If a value is still `<UNSET>` after that merge, ask the user for it,
then write the answer to `~/.claude/plugin-config/<plugin>/<skill>.md`
(creating the directory if needed). Never write answers back into the
skill's own `config.md`; they'd be wiped on the next plugin update.
Do this once per session — assume the values are stable after that.

If a `{{placeholder}}` has no matching key in `config.md`, that's a bug
in the generalized skill; tell the user and proceed with a sensible
default if you can.
```

Update the frontmatter to add `requires_config: true` so future tooling can detect the pattern.

If the source skill's `description` names one team's context ("the Growth Conversion roadmap", "my preferred channel"), rewrite it so it still triggers for someone outside that team. The description is what fires the skill, and a new user's prompts won't use your team's vocabulary.

#### Bundled scripts

Same `{{var_name}}` treatment. For Python scripts that get *executed* (not just read by Claude), copy `references/config_loader.py` into the new skill's `scripts/` folder and add a 3-line stanza to the top of each script that imports it and loads config.md. Anywhere the script previously had a literal value, replace with the config lookup.

For scripts that Claude just reads to understand intent, leave the `{{var_name}}` placeholders inline — Claude will resolve them when it follows the SKILL.md's Configuration instructions.

#### Reference files in the source skill

Same approach. If a reference file has team-specific examples ("e.g., the Growth Conversion roadmap"), rewrite the example to be generic ("e.g., your team's roadmap database").

#### Bundled documentation (from Phase 3 bundle decisions)

For each doc the user chose to **Bundle**:

1. Read the source file completely.
1. Write it to `<output-skill>/references/<bundle_filename>` (the filename the user picked, defaulting to the source basename).
1. Find every reference to the original path in the new SKILL.md and any other files you've already rewritten, and replace them with the skill-relative path: `references/<bundle_filename>`.
1. Do **not** add a `{{var_name}}` placeholder for this path and do **not** add a config entry for it. The whole point of bundling is that the path is now stable inside the skill.
1. If the original SKILL.md had instructions like "read the voice style guide at [path] before drafting", confirm those instructions still parse with the new path. The simplest fix is to phrase the instruction in terms of the bundled location: "Read `references/voice-style-guide.md` before drafting."

For each doc the user chose to **Extract as a config variable**: handle it the same way as any other variable (config.md entry, `{{var_name}}` substitution).

For each doc the user chose to **Leave as literal**: do nothing.

Track which docs got bundled — you'll need the list for the README and for the Phase 5 file inventory.

#### `README-FOR-USERS.md`

Use the template at `references/readme-for-users-template.md`. Auto-fill it with:

- The skill's purpose (one paragraph paraphrased from SKILL.md)
- The list of config variables, grouped by category, with descriptions
- A "Dependencies" section listing any cross-skill / external-tool requirements with a one-liner each on what the user needs to bring
- A "Bundled documentation" section listing every doc that got bundled, where it lives in the skill (`references/<filename>`), and one sentence on why it's there. New users should know what extra content they're getting and whether they're free to swap it out for their team's equivalent.
- Install instructions
- A note about the secrets caveat: "If your config values include API tokens or other secrets, be aware that your answers are stored as plain text under `~/.claude/plugin-config/`. Don't share or commit that file. v1 of this skill format does not have first-class secret handling."
- For Claude.ai users: a note that persistence works in Claude Code; Claude.ai will re-prompt each session.

### Phase 5: Save and offer to package

Write everything to the output path. List the files created so the user can spot-check.

Then ask: "Want me to package this into a `.skill` file for marketplace upload?" If yes, run:

`skill-creator` ships as a plugin for most people, so its packaging script isn't at a fixed path.
Locate it before using it:

```bash
find ~/.claude -path '*skill-creator/scripts/package_skill.py' -print -quit
```

Run the path that returns. If nothing does, say so plainly and stop there: the generalized skill is
already complete on disk and installable by copying the folder. Don't invent a path.

That produces a `<skill-name>.skill` ZIP in the parent directory, ready to share.

## Quality checks before declaring done

After writing the output, do a final pass:

1. **No literals leaked through.** Grep the output for the original team-specific values (the user's email, their team name, the Jira project key, the database IDs). Anything that survived without being deliberately retained is a bug.
1. **All `{{var_name}}` placeholders resolve.** Every placeholder in any output file should have a matching key in `config.md`'s frontmatter. Mismatches are bugs.
1. **The Configuration section is at the top of SKILL.md.** Not buried — the very first thing after the frontmatter, so Claude reads it before doing anything else.
1. **Descriptions are written for strangers.** Re-read the config.md Setup Guide and the README-FOR-USERS.md as if you'd never seen this skill before. Are the variables explained in language someone outside the team would understand?
1. **The skill still triggers correctly.** Read the new `description` field. Did the rewrite (removing team-specific terms) accidentally make it too generic to fire? If so, tighten it.
1. **Bundled docs actually exist and are referenced correctly.** For each bundled doc: confirm the file exists at `<output-skill>/references/<filename>`, and grep SKILL.md for the original path — none of the original paths should survive. Every reference to a bundled doc should point at `references/<filename>`.

If any check fails, fix it before reporting back to the user.

## Reference files

- `references/variable-taxonomy.md` — The 6-category taxonomy with concrete examples from real skills, used as your guide during the LLM pass in Phase 2.
- `references/config-md-template.md` — Skeleton for the generated config.md.
- `references/readme-for-users-template.md` — Skeleton for the generated README.
- `references/config_loader.py` — Stdlib-only Python loader for parsing config.md frontmatter; copied into generalized skills that have executable Python scripts.
- `scripts/detect_patterns.py` — Regex-based first-pass scanner. Run early in Phase 2.
