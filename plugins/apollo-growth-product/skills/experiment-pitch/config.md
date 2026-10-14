---
notion_roadmap_data_source: "<UNSET>"
roadmap_database_name: "<UNSET>"
roadmap_goal_options: "<UNSET>"
roadmap_new_pitch_stage: "Needs review"
team_routing_rules: "<UNSET>"
fiscal_quarter_definition: "<UNSET>"
pitch_output_dir: "<UNSET>"
team_context_dirs: ""
---

# Setup Guide

This file ships with the skill. Treat it as defaults and documentation: a plugin update replaces it,
so don't save your answers here.

Just run the skill. It prompts for anything still `<UNSET>` the first time and writes your answers to
`~/.claude/plugin-config/apollo-growth-product/experiment-pitch.md`, which survives updates. To set values up front, create
that file yourself with the same frontmatter keys.

An empty string is a real answer meaning "intentionally blank", not a missing one, so the skill won't
re-ask for keys you deliberately left empty.

## notion_roadmap_data_source

The Notion data source ID for your roadmap database, in the form
`collection://xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`. Finished pitches are created here as new pages.

## roadmap_database_name

The human-readable name of that database, e.g. `EPD Roadmap :: Growth & Acquisition`. Used so the
review step can name the destination out loud.

## roadmap_goal_options

Comma-separated valid options for the roadmap's `Goal` property, e.g.
`FTP, Monthly to Annual, Credit upgrades, Seat upgrades, Tier upgrades, Retention`. The skill picks
the best fit and shows its pick in the review.

## roadmap_new_pitch_stage

The `Stage` value every new pitch gets, e.g. `Needs review`. This should be whatever your roadmap
calls "not yet triaged" so pitches don't jump the queue.

## team_routing_rules

How to route a pitch's team fields off the experiment's audience. Write this as a few lines the
skill can follow, naming the audience signal and the resulting `Area`, `Delivery team`, `Track`, and
`KR` values. For example:

```text
Free / trial / not-yet-paying users -> Area = Product - Conversion, Delivery team = Conversion,
Track = FTP (or M2A for annual work), KR = a Conversion KR.

Existing paid teams (add-on credits, seats, tier upgrades, expansion revenue) -> Area =
Product - Expansion, Delivery team = Expansion, Track = Expansion, KR = an Expansion KR.

Tell-tale signal: a Goal of Credit upgrades / Seat upgrades / Tier upgrades means Expansion. A Goal
of FTP means Conversion. When the audience straddles both, ask.
```

If you only own one team, write a single line naming its fixed values.

## fiscal_quarter_definition

How your fiscal quarters map to calendar months, so the skill can parse a quarter out of the
arguments, e.g. `FY27 quarters: Q1 = Feb-Apr, Q2 = May-Jul, Q3 = Aug-Oct, Q4 = Nov-Jan`.

## pitch_output_dir

The local directory a copy of each pitch gets saved to, e.g. `areas/growth/initiative-pitches`.
Relative to wherever you run Claude Code. Files land as
`experiment-{slug}-{YYYY-MM-DD}.md`.

## team_context_dirs

Optional. Comma-separated local directories the skill globs for planning docs, prior pitches, and
roadmap exports before drafting, e.g. `areas/growth/planning, resources/growth`. Leave empty to skip
the local scan.
