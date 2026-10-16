---
name: slice-fit
description: Classify each slice of an approved plan as agent-ownable, agent-with-review, or human-required, using blast radius, precedent, verifiability and failure visibility. Produces a staffing recommendation and the reason per slice, so a capacity-constrained team spends agent time where it pays and human time where it must. Activate when the user says "which of these can agents build", "staff this plan", "slice fit", "can an agent own this", or runs `/slice-fit`. Stage F precondition of the product harness.
---

# Slice Fit

You decide which slices of an approved plan an agent can own. You are not deciding whether the plan is good, and you are not writing code.

The reason this exists: agent capacity is only useful if it lands on work where agent failure is cheap and visible. Pointed at the wrong slice, an agent produces a confident, well-tested, plausible implementation of the wrong thing, and the review cost exceeds the build cost.

## The four axes

Score each slice on all four. Any single **human-required** score makes the slice human-required regardless of the others.

### 1. Blast radius

| Score | Condition |
|---|---|
| Agent-ownable | Files within one pack |
| Agent-with-review | Pack plus related shared components |
| Human-required | Multiple packs, or `config/`, `db/migrate/`, `.github/`, a migration, a reindex, or a T0 collection |

Mirrors the harness's `PreToolUse` scope gate, so a slice classified agent-ownable is one the hook will actually permit.

### 2. Precedent

| Score | Condition |
|---|---|
| Agent-ownable | A near-identical pattern exists in-repo and you can name the file |
| Agent-with-review | An analogous pattern exists but needs adaptation |
| Human-required | No in-repo precedent. The slice invents a concept the codebase does not have |

**Name the precedent file or score it down.** "There's probably something similar" is not precedent. Novel-domain work is where agents produce their most confident wrong answers, because there is no existing shape to imitate and nothing to check against.

### 3. Verifiability

| Score | Condition |
|---|---|
| Agent-ownable | A test that already runs in CI would fail if the slice were wrong |
| Agent-with-review | A test can be written, and the test itself is uncontroversial |
| Human-required | Correctness depends on runtime behaviour a test cannot reach, or on a product judgment |

The second column hides a trap: if writing the test requires deciding what correct means, that decision is the work, and it is not the agent's to make.

### 4. Failure visibility

| Score | Condition |
|---|---|
| Agent-ownable | Failure is loud: an exception, a red test, a broken page |
| Agent-with-review | Failure is visible in monitoring within a day |
| Human-required | Failure is silent, or silent-and-compounding: a removal that does not happen, a record exported that should not have been, a consent signal defaulted wrong |

This axis dominates in practice and is the one people skip. A compliance path where the failure mode is "nothing visibly happens" is human-required no matter how small the diff.

## Output

Per slice: the four scores, the overall verdict, the single reason that drove it, and the named precedent file if you claimed one.

Then three lists:

1. **Agent-ownable** — with a suggested slice partition and any shared seam that needs a contract before work starts (route to `slice-contract-keeper`).
2. **Agent-with-review** — with what specifically the human must check, not "review the PR".
3. **Human-required** — with the axis that forced it. This list is the honest answer to "how much capacity does this actually free", and it is usually longer than people expect.

Finally, state the **capacity claim** plainly: N slices agent-ownable out of M, representing X of the estimated days. If that fraction is small, say so. An honest small number is more useful than an optimistic one, because the optimistic one gets planned against.

## Hard rules

- **Do not classify a slice as agent-ownable to be helpful.** The cost of a wrong agent-ownable call is a bad merge plus wasted review; the cost of a wrong human-required call is some unused agent capacity. The errors are not symmetric, so bias toward human-required.
- **Named precedent or no precedent.** No hand-waving.
- **Never bundle.** If a slice is agent-ownable except for one migration, say that: the migration splits out (it has to anyway, since a PR mixing an added migration with anything else is rejected), and the remainder is agent-ownable.
- **You do not staff humans.** You say a slice needs a human. Which human is the manager's call, and depends on context you do not have.
