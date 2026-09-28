---
name: bug-bash-generator
description: Compatibility entrypoint for generating bug-bash test plans; routes generation-only requests to end-to-end-bug-bash without executing tests.
disable-model-invocation: true
---

# Bug Bash Generator

This command remains available for compatibility. The canonical workflow now lives in
`${CLAUDE_PLUGIN_ROOT}/skills/end-to-end-bug-bash/SKILL.md`.

1. Read that skill in full.
1. Select **Generate** mode.
1. Run Phases 0-2 only; never start browser execution unless the user subsequently asks to execute.
1. Deliver to Notion or local markdown according to the user's requested destination. If the user
   did not specify a destination, draft the cases in chat and ask once before the external write.

Accept whatever trustworthy sources the user provides. Do not require an exact Bug Bash URL or all
five ERD/PRD/Figma/Jira/GitHub source types; document gaps and stop only when a missing prerequisite
prevents a reliable plan.

The existing `references/` files remain canonical supporting material for generation and are also
used by `end-to-end-bug-bash`:

- `references/erd-proposed-delta-pass.md`
- `references/automation-risk-checklist.md`
- `references/notion-upload-format.md`
- `references/local-export-format.md`
