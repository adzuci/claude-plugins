---
notion_docs_data_source: "<UNSET>"
docs_database_name: "<UNSET>"
docs_title_property: "Writeup"
docs_type_property: "Doc type"
docs_author_property: "Author"
docs_team_property: "Team"
docs_team_options: "<UNSET>"
docs_type_options: "Documentation, Analysis, Plan, Experiment, Research, Guidelines, Proposal, Strategy, Training, Report, Brainstorm, Playbook"
default_notion_user_id: "<UNSET>"
---

# Setup Guide

This file ships with the skill. Treat it as defaults and documentation: a plugin update replaces it,
so don't save your answers here.

Just run the skill. It prompts for anything still `<UNSET>` the first time and writes your answers to
`~/.claude/plugin-config/apollo-growth-product/publish-growth-product-doc.md`, which survives updates. To set values up front, create
that file yourself with the same frontmatter keys.

An empty string is a real answer meaning "intentionally blank", not a missing one, so the skill won't
re-ask for keys you deliberately left empty.

The skill re-reads the live Notion schema before every publish, so these values are a starting
point, not the last word. When the live schema disagrees, the skill follows the live version and
says so in the review.

## notion_docs_data_source

The Notion data source ID for your team's documents database, in the form
`collection://xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`. Every published page lands here.

## docs_database_name

The human-readable name of that database, e.g. `Growth Product Docs`. Only used so the review step
can name the destination out loud before anything is written.

## docs_title_property

The name of the title property on that database. Often `Writeup`, `Name`, or `Title`.

## docs_type_property

The multi-select property that classifies the document, e.g. `Doc type`. Set to an empty string if
your database has no such property.

## docs_author_property

The person property recording who wrote the doc, e.g. `Author` or `Owner`.

## docs_team_property

The select property naming which team the doc belongs to, e.g. `Team`. Set to an empty string if
your database has no such property.

## docs_team_options

Comma-separated valid options for the team property, e.g. `Conversion, Expansion, All`. The skill
leaves the property unset and flags it when a document's scope is ambiguous.

## docs_type_options

Comma-separated valid options for the doc type property. The default list covers the common set.
Replace it with your database's actual options.

## default_notion_user_id

Your Notion user ID, used for the author property. Resolve it with `notion-get-users` and take the
`person` entry, not a bot.
