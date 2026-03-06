# apollo-eng

Shared engineering skills for Apollo engineers — PR descriptions, security reviews, and release communications.

## Skills

| Invoke command | Purpose |
|---|---|
| `/apollo-eng:pr-description` | Generate a PR title and description from the current branch's changes |
| `/apollo-eng:security-review` | Security audit of Ruby controllers for IDOR vulnerabilities |
| `/apollo-eng:bug-bash-generator` | Generate bug bash test cases from a Notion bug bash page |
| `/apollo-eng:product-ship-post` | Generate product ship room posts for Slack announcements |
| `/apollo-eng:learn-from-chat` | Save user corrections and preferences to Claude Code memory |

## What belongs in apollo-eng

Skills in this plugin are for **general engineering workflows that apply across any Apollo repo**: writing, reviewing, communicating about code. Good candidates:

- Workflow automation any engineer would use regardless of repo (PR descriptions, changelogs, ship posts)
- Code review patterns that apply repo-agnostically (security, performance, accessibility)
- Meta-skills about working with Claude (memory, learning, preferences)
- Anything you'd want available whether you're in `deployments`, `webapp`, or any other repo

## What does NOT belong in apollo-eng

- **Infra or ops skills** → use `apollo-ops` instead
- **Repo-specific knowledge** (e.g. a skill that knows a specific repo's domain model) → put it in that repo's `.claude/skills/` directory
- **Skills with heavy reference files that are only relevant in one context** — reference files load tokens at invocation time even when the skill isn't relevant to the current work
- **Skills that require credentials or services not available in all repos**

## Token efficiency and trigger discipline

`apollo-eng` is enabled by default in several Apollo repos (e.g. `deployments`). This means **every skill's `description` field is loaded into context on every Claude Code session** in those repos, whether or not the skill is relevant to the current task.

### What loads when

| When | What loads | Cost |
|---|---|---|
| Any Claude Code session in an enabled repo | All skill `description` fields | Always |
| User invokes a skill | Full skill body + any reference files | On demand |

### Keep descriptions short and trigger-specific

The description is always in context. A 3-sentence description costs tokens in every session across every Apollo repo that has this plugin enabled. A tight 1-sentence description with explicit trigger phrases costs almost nothing.

```
# Too vague — activates too broadly, wastes tokens on the skill body
description: Help with pull requests and code review.

# Good — triggers only when the user explicitly asks
description: Generate a clear PR title and description from the current branch's changes.
Use when the user asks to fill the PR template, generate a PR description, prepare a PR,
create a pull request, or before running gh pr create.
```

### Use explicit trigger phrases

Name the exact words or commands that should activate the skill. This prevents skills from firing on ambient context (e.g. a PR description skill activating every time someone mentions a pull request in passing) and keeps cost predictable.

### Keep reference files lean

Reference files load when a skill is invoked. A 500-line reference file in a high-frequency skill like `pr-description` adds real per-invocation cost. Prefer focused, actionable references over comprehensive documentation dumps.

### Prefer explicit invocation for heavy skills

Skills that do significant work (fetching external pages, reading many files, producing long outputs) should require the user to explicitly ask — not fire on passive context. This keeps cost predictable and avoids surprising the user.

### Rule of thumb

Before adding a skill to `apollo-eng`, ask: _if this skill's description loaded on every session in every Apollo repo, would that be acceptable?_ If no, either tighten the description, move the skill to a repo-specific `.claude/skills/` directory, or create a separate plugin that engineers opt into manually.
