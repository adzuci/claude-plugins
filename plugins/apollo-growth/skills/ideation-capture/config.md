---
notion_ideas_data_source: "<UNSET>"
notion_docs_data_source: "<UNSET>"
idea_title_property: "Idea"
idea_default_status: "Backlog"
idea_goal_options: "<UNSET>"
idea_surface_area_options: "<UNSET>"
docs_title_property: "Writeup"
docs_author_property: "Author"
default_notion_user_id: "<UNSET>"
team_context_dirs: ""
---

# Setup Guide

This file ships with the skill. Treat it as defaults and documentation: a plugin update replaces it,
so don't save your answers here.

Just run the skill. It prompts for anything still `<UNSET>` the first time and writes your answers to
`~/.claude/plugin-config/apollo-growth/ideation-capture.md`, which survives updates. To set values up front, create
that file yourself with the same frontmatter keys.

An empty string is a real answer meaning "intentionally blank", not a missing one, so the skill won't
re-ask for keys you deliberately left empty.

## notion_ideas_data_source

The Notion data source ID for your team's ideas database, in the form
`collection://xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`. Individual ideas from the session are created
here, one page each.

## notion_docs_data_source

The Notion data source ID for your team's documents database. The session summary one-pager is
created here. Can be the same database you use with
`/apollo-growth-product:publish-growth-product-doc`.

## idea_title_property

The name of the title property on the ideas database. Often `Idea`, `Name`, or `Title`.

## idea_default_status

The status every captured idea gets. Defaults to `Backlog`.

## idea_goal_options

Comma-separated list of the valid `Goal` select options in your ideas database. Every idea in a
session shares one Goal, so this is the question asked up front. Set to an empty string if your
database has no Goal property.

## idea_surface_area_options

Comma-separated list of the valid `Surface Area` select options. Set to an empty string if your
database has no Surface Area property.

## docs_title_property

The name of the title property on the docs database. Often `Writeup`, `Name`, or `Title`.

## docs_author_property

The name of the person property on the docs database that records who wrote the summary. Often
`Author` or `Owner`.

## default_notion_user_id

Your Notion user ID. Used as the session summary's author, and as the fallback for any brainstorm
participant whose name can't be matched to a workspace user. Resolve it with `notion-get-users` and
take the `person` entry, not a bot.

## team_context_dirs

Optional. Comma-separated local directories the skill globs for related planning docs and prior
brainstorm outputs, e.g. `areas/growth/planning, resources/growth`. Leave empty to skip the local
scan.
