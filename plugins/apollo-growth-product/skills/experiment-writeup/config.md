---
writeup_output_dir: "<UNSET>"
sample_size_calculator_url: "https://www.statsig.com/calculator"
team_context_dirs: ""
---

# Setup Guide

This file ships with the skill. Treat it as defaults and documentation: a plugin update replaces it,
so don't save your answers here.

Just run the skill. It prompts for anything still `<UNSET>` the first time and writes your answers to
`~/.claude/plugin-config/apollo-growth-product/experiment-writeup.md`, which survives updates. To set values up front, create
that file yourself with the same frontmatter keys.

An empty string is a real answer meaning "intentionally blank", not a missing one, so the skill won't
re-ask for keys you deliberately left empty.

## writeup_output_dir

The local directory standalone writeups get saved to, e.g. `areas/growth/initiative-pitches`.
Relative to wherever you run Claude Code. Only used when no Notion URL is provided. Files land as
`{experiment-slug}-{YYYY-MM-DD}.md`.

## sample_size_calculator_url

The sample size / runtime calculator your team uses. Linked from the Experiment Design section so a
reader can check the math. Defaults to the Statsig calculator.

## team_context_dirs

Optional. Comma-separated local directories the skill globs for planning docs and team context
before drafting, e.g. `areas/growth/planning, resources/growth`. Leave empty to skip the local scan.
