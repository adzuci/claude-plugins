---
name: resolve-review-comments
description: Fetch, categorize, and interactively resolve PR review comments. Groups related comments, explains each, and waits for your decision before fixing.
disable-model-invocation: true
---

Resolve unresolved PR review comments interactively.

## Inputs

- **PR link** (optional): A GitHub PR URL. If not provided, detect it from the current branch using `gh pr view --json url -q .url`.

## Step 0: Preflight — Verify `gh` Is Available

Run `command -v gh` silently. If it exits non-zero:

1. Tell the user: "`gh` (GitHub CLI) is not installed or not on PATH. This skill requires it to fetch review comments via the GitHub GraphQL API."
1. Suggest they install it (`brew install gh`) and authenticate (`gh auth login`).
1. If the `apollo-eng:gh-setup` skill is available, suggest running `/apollo-eng:gh-setup` instead.
1. **Stop here** — do not continue to Step 1.

Also run `gh auth status` to confirm authentication. If not authenticated, tell the user and suggest `gh auth login`. Stop.

Run `command -v jq` silently. If it exits non-zero, tell the user: "`jq` is not installed or not on PATH. The fetch script requires it to parse GitHub API responses." Suggest `brew install jq`. **Stop here.**

## Step 1: Fetch Review Comments

Determine the PR URL. If the user provided one, use it. Otherwise run:

```bash
gh pr view --json url -q .url
```

The fetch script is located at `plugins/apollo-eng/skills/resolve-review-comments/fetch-pr-reviews.sh` relative to the project root. Run it with the PR URL as the argument:

```bash
bash plugins/apollo-eng/skills/resolve-review-comments/fetch-pr-reviews.sh <PR_URL>
```

This fetches all unresolved review threads via the GitHub GraphQL API and writes a markdown checklist to `/tmp/pr-review-<PR_NUMBER>.md`.

Show the user the full command output including the file path. Tell them: **"Review comments saved to `/tmp/pr-review-<PR_NUMBER>.md` — open it in your editor to see the raw checklist."**

Read that file.

If there are no unresolved comments, report that and stop.

## Step 2: Analyze and Group

Read every comment. For each one:

1. Read the file and lines referenced to understand the current code state.
1. Determine whether the comment is still valid against the current code (it may already be fixed).
1. Identify related comments — comments that touch the same logical concern, even if on different files/lines. Group them together and treat them as one item.

## Step 3: Present the Categorized List

Present a numbered summary table with columns:

- **#**: Group number
- **Comments**: Which original comment numbers are in this group (e.g., "3, 5")
- **File(s)**: File and line references
- **Category**: One of: `correctness`, `style`, `performance`, `security`, `simplification`, `test-coverage`, `already-fixed`, `nit`
- **Summary**: One sentence describing the concern
- **Verdict**: Your assessment — `agree`, `disagree`, or `discuss` — with a one-line reason

Then wait for the user to decide. Do NOT start fixing anything yet.

## Step 4: Resolve One at a Time

For each group the user wants to fix, in the order they specify:

1. Explain what you're about to change and why.
1. Make the change.
1. Run relevant tests to verify.
1. Move to the next group.

If the user disagrees with a comment or your verdict, skip it and move on.

After all groups are resolved, summarize what was fixed and what was skipped.
