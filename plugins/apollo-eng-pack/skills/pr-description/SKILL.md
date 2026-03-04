---
name: pr-description
description: Generate a clear PR title and description from the current branch's changes. Use when the user asks to fill the PR template, generate a PR description, prepare a PR, create a pull request, or before running gh pr create.
---

# PR Description

Generate a PR description from the current branch's code changes using the repo's PR template when one exists.

## When to Activate

- User asks to "fill PR template" or "generate PR description"
- User wants to "prepare PR" or "create pull request"
- User mentions PR description or pull request template
- User asks to "commit & create PR" or "push and create PR" or "submit PR"
- **CRITICAL**: Before running `gh pr create` — invoke this skill first to populate the description

## Commit-Only Requests

When the user only asks to commit (without PR creation):

- Promote **atomic commits** — each commit should represent a single logical change
- If there are multiple unrelated changes, suggest splitting into separate commits
- Use clear, descriptive commit messages; if the repo uses ticket prefixes (e.g. JIRA), include the ticket ID

## Important

**ALWAYS read the repo's PR template first when it exists.** Common locations:

- `pull_request_template.md` (repository root)
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/PULL_REQUEST_TEMPLATE/` (directory with multiple templates)

Never assume a hardcoded template — read the current file(s) for the repo you're in.

## Steps

### 1. Read the PR Template

If the repo has a PR template, read it to get the current format and required sections:

```bash
# Try common paths (adjust per repo)
cat pull_request_template.md 2>/dev/null || cat .github/PULL_REQUEST_TEMPLATE.md 2>/dev/null || true
```

### 2. Analyze Code Changes

Determine the compare branch (often `origin/main` or `origin/master`), then:

```bash
# Replace MAIN_OR_MASTER with the repo's default branch
git diff origin/main...HEAD --name-only
git diff origin/main...HEAD --stat
git log origin/main...HEAD --oneline
```

Use `origin/master` if that is the repo's default branch.

### 3. Identify Change Types

- File additions, deletions, modifications
- Change categories (feature, bugfix, refactor, chore, etc.)
- If the repo uses ticket IDs (e.g. JIRA), try to extract from branch name or commit messages

### 4. Fill All Template Sections

If the repo has a PR template, fill **every** section with accurate content. If there is no template, produce a clear description that includes:

- Brief context or motivation
- What changed and why
- Guidance for reviewers (key areas to focus on)
- Testing performed (manual and/or automated)
- Any checklists or follow-ups the repo expects

**User-input sections:** If the template includes sections that require user input (e.g. impact scores, self-assessment), ask the user for those values instead of auto-filling.

### 5. Show Draft for Review

Before creating the PR, show the user a draft and ask for confirmation:

```
Here's the draft PR description:

[Show full PR body]

Would you like me to create the PR with this description, or would you like to make any changes?
```

Wait for user approval before running `gh pr create`.

### 6. Create PR with gh CLI

Only after user approval. If a ticket ID was identified, prefix the title with `[TICKET-###]`; otherwise use a convention appropriate to the repo (e.g. `NOTICKET` or no prefix):

```bash
# With ticket:
gh pr create --title "[TICKET-###] PR Title" --body "$(cat <<'EOF'
[Full PR body]
EOF
)"

# Without ticket (if repo uses NOTICKET):
gh pr create --title "NOTICKET PR Title" --body "$(cat <<'EOF'
[Full PR body]
EOF
)"
```

To update an existing PR:

```bash
gh pr edit <PR_NUMBER> --body "$(cat <<'EOF'
[Full PR body]
EOF
)"
```

## Tips

- Keep the summary concise but informative
- Focus on "why" not just "what"
- List key files or areas changed for reviewer context
- Highlight any areas needing special attention
- Note dependencies or deployment steps when relevant
- For template sections that ask for subjective input (e.g. AI usage), ask the user — don't assume
- Reference related PRs or tickets when applicable
