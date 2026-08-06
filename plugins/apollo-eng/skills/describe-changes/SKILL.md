---
name: describe-changes
description: Describe what git changes accomplish and why, for a chosen audience (non-technical by default, or technical / re-implementation brief). Covers a branch vs master, uncommitted work, or a stash.
argument-hint: '[scope: branch|uncommitted|stash] [--audience non-technical|technical|reimplementation]'
disable-model-invocation: true
---

Produce a plain-English summary of git changes that captures *what* the changes accomplish and *why they exist*, not the technical implementation. The output should read like something you'd paste into a Slack message, a hand-off note, or a re-implementation brief.

## Determine the scope

Parse the user's request and pick the right git commands:

| Request | What to diff |
|---|---|
| `/describe-changes` (no args) | Fallback chain — see **Default scope resolution** below |
| "uncommitted" / "working changes" / "unstaged" | `git diff HEAD` (unstaged) and `git diff --cached` (staged) |
| "stash" / "stashed changes" | `git stash show -p stash@{0}` |
| "stash@{N}" | `git stash show -p stash@{N}` |
| "everything" / "branch + uncommitted" | Combine: `git diff origin/master...HEAD` + `git diff HEAD` + `git diff --cached` |

If the scope is ambiguous, infer it rather than asking.

### Default scope resolution (no args)

With no arguments, describe the most work-in-progress thing that's actually relevant. Check in this order and use the first that applies:

1. **Staged files** — if `git diff --cached` is non-empty, describe the staged changes. They're staged because they're the unit of work the user is about to commit.
1. **Uncommitted changes** — otherwise, if `git diff HEAD` is non-empty *and* the changed files are significant to the current branch/PR (they touch the same feature area as the branch's commits, not just stray edits like local config tweaks, debug leftovers, or unrelated files), describe those. If the uncommitted changes are clearly incidental noise, skip to the next step.
1. **Current branch/PR** — otherwise, if the branch has commits beyond `origin/master`, describe `git diff origin/master...HEAD`.
1. **Last commit** — otherwise (clean tree, no branch delta — e.g. sitting on master or a just-merged branch), describe `git show HEAD`.

Mention in one opening clause which scope you ended up describing (e.g. "Your staged changes…", "This branch…", "Your latest commit…") so the user knows what they're reading about.

## Determine the audience

Pick a mode from an explicit argument (`--audience=technical`, "technical version", "for the PM", "for someone rebuilding this in Go") or infer it from context. Default to **non-technical**.

- **non-technical** (default) — a PM, stakeholder, or future teammate skimming Slack. No jargon, no implementation vocabulary. Focus on the problem solved and what's different day-to-day.
- **technical** — a peer engineer who doesn't know this codebase. Architecture-level terms are fine (queue, retry, cache, API endpoint), but still describe behavior and design decisions, not files and functions. What would you tell them in a hallway before they open the PR?
- **reimplementation** — someone rebuilding the same feature in a different stack. Describe the behavior contract: inputs, outputs, edge cases handled, invariants preserved, ordering/timing guarantees, and any deliberate trade-offs. Stack-agnostic — name concepts, not libraries, unless the library *is* the decision. This mode may run longer than the others; completeness beats brevity here.

## Understand the intent (before writing anything)

The diff shows *what* changed; the *why* usually lives elsewhere. Work through these sources in order, and stop once you can state the purpose of the change set in one confident sentence:

1. **Full commit messages** — `git log origin/master...HEAD` (not `--oneline`; the bodies are where authors explain why). For stash/uncommitted scopes, check recent commits anyway — the working changes are usually a continuation of them.
1. **Branch name and ticket references** — a branch like `fix/APOLLO-1234-retry-timeouts` or a `Closes #456` in a commit is a direct statement of intent. Mention the ticket in the output when one exists.
1. **The PR, if one exists** — `gh pr view --json title,body,comments` (ignore errors if there's no PR). PR descriptions and review threads often contain the clearest why.
1. **Changed tests** — tests encode intended behavior. A new test named for an edge case tells you exactly which failure the change prevents.
1. **Changed docs, config, and workflow files** — these state intent more plainly than code.

If after all that the purpose is still fuzzy, go deeper into the code — there is no reading budget; a correct description of intent is worth more than saved tokens:

- Read the **full contents of changed files**, not just the diff hunks — the surrounding code often explains what role the changed part plays.
- **Trace usage**: grep for changed function/class names to see who calls them and in what situation the new behavior kicks in.
- Read **adjacent unchanged code** (the module, the caller, the error handler around the change) when a hunk's purpose is unclear in isolation.

**Stated vs. inferred intent.** When a commit message, ticket, or PR says why, report it as fact. When you deduced the why from code alone, either verify it with more reading or soften it slightly ("this appears to be aimed at…"). Never present a guess in the confident voice of a stated fact — a hand-off note that's confidently wrong is worse than one that's honest about a gap.

## Output format

Write 4–6 short paragraphs in plain prose (reimplementation mode may need more). Lead each paragraph with a bolded phrase that signals its role, like **What this is:**, **What it does:**, **How it's triggered:**, **Guardrails:**, **The practical benefit:**. Roughly cover:

1. What this change set is for — the problem it solves or the goal it achieves. If there's a ticket or PR, anchor to it.
1. What it does from an operator/user/developer perspective
1. When or how it activates, or how someone would use it
1. Any guardrails, constraints, or limits (omit if there aren't meaningful ones)
1. The day-to-day impact — what's concretely different for someone working with this

### Quality bar

- **Contrast before and after.** The fastest way to make a change legible is "it used to X; now it Y". If you can't articulate the before-state, you haven't understood the intent yet — go back and read more.

- **Concrete beats abstract.** Every claim should survive the question "what would I actually observe?". Empty-calorie adjectives — "robust", "streamlined", "enhanced", "improved reliability" — are banned unless immediately followed by the observable difference.

  Weak: *"This makes the nightly sync more robust."*
  Strong: *"The nightly sync used to silently skip repositories it couldn't reach, so gaps in the metrics went unnoticed for days. Now it retries twice and posts a summary of anything it still couldn't fetch."*

- **One idea per paragraph.** If a paragraph needs "also" twice, split or cut.

- **Name what a person will notice.** If any behavior visible to users, operators, or CI changed, say exactly what they'll see differently.

### Avoid

- File names, function names, or line numbers (in reimplementation mode, naming key *concepts* and data shapes is encouraged — just not this codebase's identifiers)
- Implementation details — algorithms, data structures, library names — unless they're the point of the change or the audience is technical
- Jargon like "middleware", "webhook", "YAML", "stdout" in non-technical mode
- Bullet lists or headers beyond the bolded lead phrases

Aim for roughly the length and density of a thoughtful Slack message — complete but not exhaustive, readable in under a minute (reimplementation mode excepted).
