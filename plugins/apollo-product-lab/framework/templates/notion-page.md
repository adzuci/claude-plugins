# {{Plain title a colleague would search for}}

> One sentence: what was decided or found, and what happens next. No stage names here.

**Status:** {{decided by <name> on <date> | waiting on <name> | in review}} · **Design / decision it belongs to:** {{link to the canonical Notion page, e.g. the ERD or decision log}}

<!-- No local file paths on a Notion page: readers have no repo checkout, so `.ai/...`, `.claude/...`, worktree names and snapshot paths mean nothing to them. The snapshot path and hash stay in the .md frontmatter; the Notion page links other Notion pages, PRs and Slack threads only. -->

## What this is about

Two or three sentences a new team member could follow. Say what the product does for the customer before
saying what the system does.

## What we found

- Bullet per finding, each with where it came from (a doc, a screen, a number). Plain words; gloss any term
  of art the first time ("the constraint register, our list of legal must-haves").

## Options

| Option | What it means for the customer | What it costs us | Recommendation |
|---|---|---|---|

## Who decides, by when

{{name}}, {{date}}. Record the decision with `/harness-council <initiative> decide ...`; this page is updated
with the outcome and the reason.

## If you want the detail

Link to the memo page, the decision page, the PR. Nobody has to read them to understand this page.

Harness run: {{initiative}}/{{run-id}} · artifact: {{snapshot file name, not a path}}

<!-- Before publishing: a fresh agent reads only this page and states the decision, what follows, and what the reader must do (doc 43 §9); rewrite until it can. Voice rules: lead with the answer; one idea per sentence; no stage or agent names without a gloss; no
em-dashes; numbers in tables, not prose; write as a person, not a process. -->
