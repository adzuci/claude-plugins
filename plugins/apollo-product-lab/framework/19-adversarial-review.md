# 19 — Adversarial review: agents may block, not bless

> Resolves the deviation flagged in [18-requirement-traceability](./18-requirement-traceability.md) #5/#10.
> **Status: draft for review. Nothing binding.**

## 1. The distinction that makes this work

Two things were being called "agent approval" and they behave completely differently.

| | A **finding** | An **approval** |
|---|---|---|
| What it is | "Line 47 does X, the spec says Y, here are both quotes" | "This looks good to me" |
| Can it be checked? | Yes — go read line 47 | No |
| What it does downstream | Adds information | **Degrades the next reviewer**, measurably |
| Wrong how often | Some findings are false; each is individually falsifiable | 83% of agent reviewer errors on good work are false *approvals* |

So the rule:

> **Agents may block. Agents may not bless.**

A reviewer that raises an evidenced objection is doing something useful and auditable. A reviewer that signs off is asserting something unfalsifiable, and that assertion then makes every downstream reviewer worse — labelling work as already-verified dropped detection by up to 93.5pp in one test.

This gives you what a PR review bot gives you: different models reading the same change and pushing back with what they found. It just never produces a green tick that anything else trusts.

## 2. Why agreement on findings is meaningful and agreement on approvals is not

This asymmetry is the reason the design works at all.

**Two models independently finding the same defect at the same location is strong evidence.** They each had to produce a positive claim with evidence, and they landed in the same place. Correlated priors make that *more* likely, not less — but the claim is still checkable, so a shared hallucination is caught by reading the line.

**Two models both saying "looks fine" is weak evidence.** It is an absence of findings, not a presence of verification. Shared blind spots produce exactly this, and there is nothing to check.

So: **count agreement on findings, never on silence.** A clean run means "nobody found anything," not "everybody verified it."

## 3. Three outcomes, and only one needs a human

This is where autonomy comes from.

| Outcome | Condition | Human needed? |
|---|---|---|
| **Auto-block** | A deterministic check fails — test red, schema invalid, policy string present, migration mixed with non-migration | **No.** It is falsifiable and the fix is obvious |
| **Auto-pass** | All deterministic checks pass, no model raised an evidenced finding, **and the evidence covers every boundary the claim crosses** (see below) | **No.** This is the autonomous path |
| **Escalate** | Models disagree, or a model raised an evidenced finding that is not deterministically checkable | **Yes** |

Most changes on a healthy codebase land in auto-block or auto-pass. **Escalation is the exception, and it is exactly the set where human judgment is actually worth something** — a real disagreement between independent reviewers, or a judgment call no rule can settle.

### Auto-pass needs a coverage assertion, and without it it is unsound

**Correction to an earlier draft.** "All checks green and no evidenced finding" is exactly the configuration that fails.

The counterexample: a rule function that was correct and fully unit-tested, while the route that should have called it never did. Fourteen green checks, a passing route test, feature broken. The defect was not in the code under test — it was that **part of the claimed behaviour lay outside the observation surface of its evidence.**

Green plus no finding is therefore not sufficient. Absent a coverage assertion, **auto-pass is a bless the harness emits on the agent's behalf** — arriving through a door §1 left open.

**The mechanism: a claim-to-proof matrix.** Decompose the claim into the boundaries it crosses, then require per boundary that some evidence's observation surface covers it. For a request-rejection claim that is three boundaries: the request reaches the rule, the route rejects it, and the store remains unchanged. A green unit test on the rule covers the first and neither of the others.

Two rules on top:

- **The matrix is immutable after a failure.** An agent that can rewrite it can define its way to green.
- **Deterministic-only checking cannot cover a timing or shared-state boundary at all.** Two correct reads of the same empty slot both produce correct decisions and jointly violate the invariant. So lean mode may **block** such a claim but may never **pass** it — those escalate the *cost mode*, not to a human.

### And Outcome needs one more distinction

> Exit code 0 is a stop reason masquerading as an outcome.

Add to the outcome taxonomy: **harness failed to observe** versus **product failed under observation.** Both are red, and only the first is our bug — a red verification route is frequently correct harness behaviour rather than a harness failure.

That is the shape of autonomy that does not require trusting an agent's opinion: the machine decides when the answer is checkable, and asks when it isn't.

## 4. How the review actually runs

1. **Fan out, blinded.** Each model gets the same artifact and the same criteria. None sees another's output, and none sees any upstream verdict. Different families where the dispatch path allows it (see [13-model-routing](./13-model-routing.md)).
2. **Findings only, never verdicts.** Each returns `{claim, location, evidence, severity}`. A reviewer that returns "approved" is returning nothing; drop it.
3. **Deduplicate by location and claim.** Same defect from two models becomes one finding with `confirmed_by: 2`.
4. **Classify.**
   - *Confirmed* — found independently by 2+ reviewers, with evidence
   - *Single-source* — one reviewer, with evidence. Still real, just weaker
   - *Disagreement* — one flagged it, another explicitly examined the same thing and did not. **This is the highest-value signal in the whole run** and always escalates
5. **One mandated adversary** whose instructions are to refute, not review. Soft dissent instructions measured no better than baseline; only a hard refute mandate moved the needle.
6. **Synthesize** via the existing `pr-tech-lead-synthesizer`, which already produces one verdict with explicit dissent.

Note what step 4 does: **disagreement is not resolved by voting.** Majority vote below ~0.5 per-item accuracy is worse than a single model, and correlated errors collapse the effective vote count. Disagreement is escalated intact, with both positions.

## 5. Controls specific to hallucination in this loop

Autonomy raises the cost of a hallucinated finding, so:

- **Evidence or drop.** A finding without a quotable location is deleted, not softened. This alone eliminates most hallucinated findings, because a fabricated defect cannot cite a real line that contains it.
- **The reviewer never sees the author's reasoning**, only the diff and the criteria. Reasoning is persuasive and contaminating.
- **Auto-block only on deterministic criteria.** A model's judgment never blocks unattended. It can escalate; it cannot stop the pipeline on its own opinion.
- **Cap findings per review.** A reviewer prompted to find gaps will find some even when work is sound. A run producing an unusually large number is itself a signal that the reviewer is over-reporting, not that the code is unusually bad.
- **Track false-positive rate per reviewer, per task class.** From the ledger. A reviewer whose findings are consistently rejected gets down-weighted, and eventually retired.
- **Silence is not success.** A clean run reports what was checked and found clean, so absence of findings is distinguishable from absence of checking.

## 6. What this does and does not achieve

**Achieves:** different models reading the same work and pushing back with checkable objections; autonomous pass/block for the common case; human attention concentrated where independent reviewers actually disagree; a false-positive rate that is measured rather than assumed.

**Does not achieve:** confidence that nothing was missed. Every mechanism here catches *findings that were made*. A defect no reviewer raises passes silently, and no amount of model diversity fixes that — which is why deterministic checks come first and why the human gates exist for the plan, not just the diff.

**And it is gated on one external thing.** Cross-family review needs the dispatch path plus a data-handling approval (M1/M2 in doc 13). Until that clears, this runs single-family — which still gives blinding, the adversary mandate, and the block-not-bless rule, but not genuine decorrelation. Worth running anyway; worth not pretending it is the full design.

## 7. Open questions

| # | Question | Owner | Blocking |
|---|---|---|---|
| Q-A1 | What is the auto-pass threshold in practice? "All deterministic checks pass and no evidenced findings" is clean in principle; the question is whether the deterministic check set is broad enough to carry that weight on a real diff | author | Autonomous pass |
| Q-A2 | How is "explicitly examined the same thing and did not flag it" detected? Distinguishing genuine disagreement from one reviewer simply not looking there requires reviewers to report coverage, not just findings | author | The disagreement signal |
| Q-A3 | Down-weighting a reviewer by false-positive rate needs enough volume per reviewer per task class to be meaningful. What is the minimum before acting on it? | author | Reviewer weighting |
| Q-A4 | Does auto-block need an appeal path? A deterministic check can be wrong (a bad lint rule, a flaky test), and an unappealable block trains people to disable the checker | author | Auto-block adoption |
