---
notion_experiments_data_source: "<UNSET>"
experiments_title_property: "Short Name"
experiment_default_status: "In Development"
experiment_team_routing: "<UNSET>"
experiment_surface_options: "www, prod, email"
sample_size_calculator_url: "https://www.statsig.com/calculator"
default_notion_user_id: "<UNSET>"
team_context_dirs: ""
---

# Setup Guide

This file ships with the skill. Treat it as defaults and documentation: a plugin update replaces it,
so don't save your answers here.

Just run the skill. It prompts for anything still `<UNSET>` the first time and writes your answers to
`~/.claude/plugin-config/apollo-growth-product/experiment-record.md`, which survives updates. To set values up front, create
that file yourself with the same frontmatter keys.

An empty string is a real answer meaning "intentionally blank", not a missing one, so the skill won't
re-ask for keys you deliberately left empty.

## notion_experiments_data_source

The Notion data source ID for your experiments database, in the form
`collection://xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`. New experiment records are created here.

## experiments_title_property

The name of the title property on that database. Often `Short Name`, `Name`, or `Experiment`.

## experiment_default_status

The status every new record gets before launch, e.g. `In Development`.

## experiment_team_routing

How to set the `Team` property from the experiment's audience. Write this as a few lines the skill
can follow, naming the audience signal and the resulting team code. For example:

```text
Free / trial / not-yet-paying users -> PD (Growth Conversion).
Existing paid teams (add-on credits, seats, tier upgrades, expansion revenue) -> EXP
(Growth Expansion).
Other values in this DB: CRO, LM, ACT, P&P.
Ask when the audience straddles two teams.
```

If your database has a single team value, write one line naming it.

## experiment_surface_options

Comma-separated valid options for the `Surface` property, e.g. `www, prod, email`. These are the
broad places an experiment can run.

## sample_size_calculator_url

The sample size / runtime calculator your team uses, linked from the Experiment Design section.

## default_notion_user_id

Your Notion user ID, used for the `Lead` property when no other lead is named. Resolve it with
`notion-get-users` and take the `person` entry, not a bot.

## team_context_dirs

Optional. Comma-separated local directories the skill globs for team context and prior pitches,
e.g. `areas/growth/initiative-pitches, resources/growth`. Leave empty to skip the local scan.
