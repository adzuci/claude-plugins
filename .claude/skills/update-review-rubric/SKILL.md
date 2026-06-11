---
name: update-review-rubric
description: Analyze recent PR review-bot output and propose concise improvements to Apollo's skill review rubric.
disable-model-invocation: true
---

# Update Review Rubric

Use this workflow in `apolloio/claude-plugins` when asked to improve `./skill-review-rubric.md` from recent PR evidence. Act like Apollo Review Bot maintenance: find concrete review misses or noisy patterns, propose targeted changes, then ask the caller which changes to implement.

## Workflow

1. Collect the last 10 relevant PRs unless the caller provides a different range.

   ```bash
   gh pr list --state all --limit 10 --json number,title,url,author,headRefName,mergedAt,closedAt,updatedAt
   ```

1. For each PR, collect evidence from review-bot output and final PR state.

   ```bash
   gh api repos/apolloio/claude-plugins/pulls/<pr-number>/reviews --paginate
   gh api repos/apolloio/claude-plugins/issues/<pr-number>/comments --paginate
   gh pr view <pr-number> --json files,commits,statusCheckRollup,reviewDecision,mergeStateStatus
   ```

   Prefer `Skill Review Bot`, Apollo Review Bot, CodeRabbit, and human review comments that mention skill quality, routing, manifests, CI, docs, or validation.

1. Compare bot comments to what happened after the comment.

   Look for:

   - Repeated false positives or comments later contradicted by repo guidance.
   - Repeated misses that humans fixed or discussed.
   - Suggestions that are technically true but too noisy for the rubric.
   - Validation gaps that CI now catches or should catch instead of review text.
   - Cases where `disable-model-invocation: true`, concise descriptions, arguments, manifests, or marketplace parity guidance was unclear.

1. Propose changes before editing.

   Output a short numbered list with:

   - `change`: the proposed rubric or workflow update.
   - `why`: the PR evidence behind it.
   - `where`: likely file(s), usually `./skill-review-rubric.md`, `./CLAUDE.md`, `./.github/workflows/skill-pr-review.yml`, or repo-local skills.
   - `risk`: what might get worse if adopted.

1. Ask the caller which suggestions to implement.

   Do not edit files until the caller chooses. If the caller says to apply all, keep the patch narrow and avoid adding new review categories without evidence.

1. After implementing selected changes, validate:

   ```bash
   mdformat ./skill-review-rubric.md ./CLAUDE.md ./.claude/skills/update-review-rubric/SKILL.md
   git diff --check
   ```

   Run broader validation only when the selected changes touch CI, tests, manifests, or marketplace files.

## Output

Lead with the recommended changes, ordered by impact. Keep the proposal concise and evidence-backed. Separate "implement now" suggestions from "watch for more evidence" ideas.
