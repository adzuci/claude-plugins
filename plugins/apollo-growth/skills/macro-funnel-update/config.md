---
notion_roadmap_data_source: "<UNSET>"
notion_app_base_url: "https://app.notion.com"
default_teams: "<UNSET>"
macro_funnel_output_dir: "<UNSET>"
---

# Setup Guide

This file ships with the skill. Treat it as defaults and documentation: a plugin update replaces it,
so don't save your answers here.

Just run the skill. It prompts for anything still `<UNSET>` the first time and writes your answers to
`~/.claude/plugin-config/apollo-growth/macro-funnel-update.md`, which survives updates. To set values up front, create
that file yourself with the same frontmatter keys.

An empty string is a real answer meaning "intentionally blank", not a missing one, so the skill won't
re-ask for keys you deliberately left empty.

The team-to-roadmap-filter mapping lives in SKILL.md rather than here, because it's a shared table
every growth team reads the same way. Edit it directly if your roadmap uses different team names or
properties.

## notion_roadmap_data_source

The Notion data source ID for your roadmap database, in the form
`collection://xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`. This is the single source the skill queries for
candidate items.

## notion_app_base_url

The base URL for Notion page links, normally `https://app.notion.com`. Only change this if your
workspace uses a different host. Note the skill rebuilds every page URL with a `/p/` segment,
because the raw `url` returned by a data-source query 404s without it.

## default_teams

The team or teams to draft for when the user doesn't name any, e.g. `Growth Conversion`. The skill
still asks whether they want the others. Must match a row in SKILL.md's team mapping table.

## macro_funnel_output_dir

The local directory weekly drafts get saved to, e.g. `areas/growth/macro-funnel`. Relative to
wherever you run Claude Code. The skill also globs this directory to load last week's draft, which
is how it catches items that were "Coming Up" and never resolved.
