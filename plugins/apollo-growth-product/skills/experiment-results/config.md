---
results_summary_property: "Summary: Results + Key Learnings"
run_dates_property: "Experiment Run Dates"
manual_confidence_property: "[Post] Confidence / StatSig"
---

# Setup Guide

This file ships with the skill. Treat it as defaults and documentation: a plugin update replaces it,
so don't save your answers here.

Just run the skill. It prompts for anything still `<UNSET>` the first time and writes your answers to
`~/.claude/plugin-config/apollo-growth-product/experiment-results.md`, which survives updates. To set values up front, create
that file yourself with the same frontmatter keys.

An empty string is a real answer meaning "intentionally blank", not a missing one, so the skill won't
re-ask for keys you deliberately left empty.

All three defaults match the common experiment-tracker layout. Change them only if your database
names these properties differently.

## results_summary_property

The text property holding the short results-and-learnings summary, e.g.
`Summary: Results + Key Learnings`. This is one of the three things the skill always updates.

## run_dates_property

The date-range property recording when the experiment actually ran, e.g. `Experiment Run Dates`.
The skill only touches this when it has real dates from the experimentation platform and they
differ from what Notion shows. The platform is the source of truth for the real window.

## manual_confidence_property

The property the skill must never write to, e.g. `[Post] Confidence / StatSig`. This is the owner's
own judgment call on the result, set by hand. Naming it here keeps the skill from overwriting it.
