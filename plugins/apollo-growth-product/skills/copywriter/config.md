---
legal_review_channels: "<UNSET>"
copy_output_dir: "<UNSET>"
---

# Setup Guide

This file ships with the skill. Treat it as defaults and documentation: a plugin update replaces it,
so don't save your answers here.

Just run the skill. It prompts for anything still `<UNSET>` the first time and writes your answers to
`~/.claude/plugin-config/apollo-growth-product/copywriter.md`, which survives updates. To set values up front, create
that file yourself with the same frontmatter keys.

An empty string is a real answer meaning "intentionally blank", not a missing one, so the skill won't
re-ask for keys you deliberately left empty.

The surface guidelines and style references ship with the skill, so there's nothing to configure
for those. Swap the files in `surfaces/` and `references/` if your team's surfaces or rules differ.

## legal_review_channels

Where to send a high-risk draft for legal review, e.g.
`#legal-product-collab or #xfn-legal-marketing`. Only surfaced when the 3-factor test scores High.

## copy_output_dir

The local directory finished copy drafts get saved to, e.g. `areas/growth/copy`. Relative to
wherever you run Claude Code. Files land as `{feature-slug}-{surface-slug}-{YYYY-MM-DD}.md`.
