---
name: review
description: Review Apollo skills marketplace changes before push or PR. Use when /review is called or when asked to review skill, plugin, marketplace, rubric, or repo-guidance changes in apolloio/claude-plugins.
disable-model-invocation: true
---

# Review

Review the current change set using this repo's skill-review rules. Keep the review findings-first and focused on actionable issues.

## Workflow

1. Load `./skill-review-rubric.md` before reviewing skill or plugin changes.

1. Detect the review scope:

   - If the user provides files, a commit, branch, or PR, review that scope.
   - Otherwise check unstaged changes with `git diff`.
   - If there are no unstaged changes, check staged changes with `git diff --cached`.
   - If there are no staged changes, check the branch diff with `git diff origin/main...HEAD`.
   - If there is still no diff, ask for a PR number, commit hash, branch, or file path.

1. Review diffs, not whole files, unless the user explicitly asks for a broader audit.

1. For skill and plugin changes, apply `./skill-review-rubric.md`:

   - Frontmatter correctness and routing boundaries.
   - `disable-model-invocation: true` for direct-only skills.
   - Token efficiency and progressive disclosure.
   - Manifest and marketplace consistency.
   - Validation and test coverage for scripts.

1. Scale review depth to change complexity.

   - For small docs or metadata edits, keep the review short.
   - For large or complex skills, do the full rubric pass before push.

## Output

Lead with findings ordered by severity and include file/line references when available. If there are no findings, say that clearly and mention any validation or residual risk.
