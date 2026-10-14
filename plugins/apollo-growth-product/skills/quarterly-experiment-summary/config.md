---
notion_experiments_data_source: "<UNSET>"
notion_docs_data_source: "<UNSET>"
team_doc_registry: "<UNSET>"
experiment_id_prefix: "<UNSET>"
fiscal_quarter_definition: "<UNSET>"
summary_output_dir: "<UNSET>"
---

# Setup Guide

This file ships with the skill. Treat it as defaults and documentation: a plugin update replaces it,
so don't save your answers here.

Just run the skill. It prompts for anything still `<UNSET>` the first time and writes your answers to
`~/.claude/plugin-config/apollo-growth-product/quarterly-experiment-summary.md`, which survives updates. To set values up front, create
that file yourself with the same frontmatter keys.

An empty string is a real answer meaning "intentionally blank", not a missing one, so the skill won't
re-ask for keys you deliberately left empty.

## notion_experiments_data_source

The Notion data source ID for your experiments database, in the form
`collection://xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`. Concluded experiments are pulled from here.

## notion_docs_data_source

The Notion data source ID for your team documents database. Only used when a team has no learnings
doc yet and you ask the skill to create one.

## team_doc_registry

A table mapping each team code in the experiments database to the team it means and the canonical
learnings doc it feeds. One doc per team. Write it as markdown the skill can read, for example:

```text
| Team | Team it means | Canonical doc |
|------|---------------|---------------|
| PD | Growth Conversion (free-to-paid, in-product) | https://notion.so/... (default) |
| P&P | Pricing & Packaging | none yet |
| EXP | Growth Expansion | none yet |
| ACT | Onboarding & Activation | none yet |
| CRO | Website / marketing-site CRO | none yet |
| LM | Lifecycle Marketing | none yet |
```

Mark one team as the default so the skill knows what to suggest first. Teams with `none yet` prompt
the skill to offer creating a doc.

## experiment_id_prefix

The prefix used when writing experiment IDs in the doc, e.g. `GA` so an experiment with `ExpID` 461
is written `GA-461`. This is also the dedupe key the skill greps for in the existing doc.

## fiscal_quarter_definition

How your fiscal quarters map to calendar dates, precise enough to assign an experiment by its run
start date, e.g.
`FY quarters run Feb-Apr, May-Jul, Aug-Oct, Nov-Jan. FY27Q2 is May 1 - Jul 31, 2026.`

## summary_output_dir

The local directory the draft is written to before pushing, e.g.
`areas/growth/experiments/quarterly-summaries`. Relative to wherever you run Claude Code. Files land
as `<team>-<quarter>-summary-draft.md`.
