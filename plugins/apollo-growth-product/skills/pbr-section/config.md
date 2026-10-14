---
pbr_output_dir: "<UNSET>"
debrief_dirs: ""
---

# Setup Guide

This file ships with the skill. Treat it as defaults and documentation: a plugin update replaces it,
so don't save your answers here.

Just run the skill. It prompts for anything still `<UNSET>` the first time and writes your answers to
`~/.claude/plugin-config/apollo-growth-product/pbr-section.md`, which survives updates. To set values up front, create
that file yourself with the same frontmatter keys.

An empty string is a real answer meaning "intentionally blank", not a missing one, so the skill won't
re-ask for keys you deliberately left empty.

## pbr_output_dir

The local directory weekly PBR sections get saved to, e.g. `areas/growth/pbr/updates`. Relative to
wherever you run Claude Code. The skill also globs this directory for your previous updates, which
is how it keeps tone and framing consistent week to week. Files land as
`pbr-{section-slug}-{YYYY-MM-DD}.md`.

## debrief_dirs

Optional. Comma-separated local directories holding team debrief reports, e.g.
`areas/growth/product-debriefs`. When a debrief is present, the skill prefers its numbers over
recollection and picks the one closest to (and not after) the PBR date. Debriefs saved as both
`.html` and `.md` are read as `.md`. Leave empty if you don't keep debriefs locally.
