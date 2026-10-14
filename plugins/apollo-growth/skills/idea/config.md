---
notion_ideas_data_source: "<UNSET>"
idea_title_property: "Idea"
idea_default_status: "Backlog"
idea_goal_options: "<UNSET>"
idea_surface_area_options: "<UNSET>"
default_notion_user_id: "<UNSET>"
team_context_dirs: ""
---

# Setup Guide

This file ships with the skill. Treat it as defaults and documentation: a plugin update replaces it,
so don't save your answers here.

Just run the skill. It prompts for anything still `<UNSET>` the first time and writes your answers to
`~/.claude/plugin-config/apollo-growth/idea.md`, which survives updates. To set values up front, create
that file yourself with the same frontmatter keys.

An empty string is a real answer meaning "intentionally blank", not a missing one, so the skill won't
re-ask for keys you deliberately left empty.

## notion_ideas_data_source

The Notion data source ID for your team's ideas database, in the form
`collection://xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`. Find it by opening the database in Notion and
copying the ID from the URL, or by asking Claude to `notion-search` for the database by name.

## idea_title_property

The name of the title property on that database. Often `Idea`, `Name`, or `Title`.

## idea_default_status

The status every newly captured idea gets. Defaults to `Backlog`. Use whatever your database calls
its unreviewed column so captures never jump the queue.

## idea_goal_options

Comma-separated list of the valid `Goal` select options in your ideas database, e.g.
`FTP, Monthly to Annual, Waterfall Enrichment, Other`. These are the business goals an idea can
ladder to. If your database has no Goal property, set this to an empty string.

## idea_surface_area_options

Comma-separated list of the valid `Surface Area` select options, e.g.
`Feature Gates, Free Trial, Referrals, Monetization`. These are the product surfaces an idea can
touch. If your database has no Surface Area property, set this to an empty string.

## default_notion_user_id

Your Notion user ID. Used for the `Added by` property when no other author is named, or when a
named author can't be resolved to a workspace user. Resolve it with `notion-get-users` and take the
`person` entry, not a bot.

## team_context_dirs

Optional. Comma-separated local directories the skill globs for related planning docs and team
context before drafting, e.g. `areas/growth/planning, resources/growth`. Leave empty to skip the
local scan entirely. Paths are relative to wherever you run Claude Code.
