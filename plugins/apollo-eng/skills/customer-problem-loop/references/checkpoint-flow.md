# Checkpoint Flow

Read this reference during stage 1. It defines the artifacts, checks, and repair routes that make
the quality flow observable. The primary agent owns the stateful attempt; each reviewer receives
only the bounded artifact and evidence needed for its checkpoint.

## 1. Problem Recognition

Create a problem brief before proposing code or a product solution. It must separate:

- customer or reporter language;
- confirmed source facts and cited evidence;
- interpretation and classification;
- current repository or product behavior, or an explicit statement that it is unverified;
- contradictions; and
- unknowns that could change scope or the validation plan.

The problem check verifies source comprehension, bug/feature/usability/outcome/mixed classification,
current-behavior grounding, contradictions, unknowns, and unsupported claims. Its verdict is `pass`,
`repair`, or `blocked`, with concrete evidence for every failure. Repair routes back to the problem
brief; blocked stops downstream work when a required source or safe verification path is missing. A
`repair` verdict here draws one round from the single repair-round budget shared with the approach
and verification checkpoints (see [repair-contract.md](repair-contract.md)).

## 2. Generate and Compare Approaches

For non-trivial work, generate at least two materially different approaches. When one or more
complexity triggers apply, seek up to four useful approaches: uncertain root cause, multiple
affected systems, hard-to-reverse or migration work, security or permission effects, materially
different viable scopes, or leading approaches whose evidence-backed comparison is too close to
call. Fewer than four are acceptable when the remaining alternatives would be cosmetic or
unsupported and the independent reviewer agrees the set is sufficient.

An approach is materially different only when it changes mechanism, ownership boundary, rollout,
or risk profile. Renaming the same implementation or varying syntax does not count.

Compare each approach using the same dimensions:

| Dimension | Question |
| --- | --- |
| Problem fit | Which confirmed facts and user outcomes does it address? |
| Repository grounding | Does current implementation evidence support the mechanism? |
| Assumptions | What must be true but remains unverified? |
| Blast radius | Which users, systems, data, and workflows could change? |
| Reversibility | Can the change be disabled or rolled back safely? |
| Testability | Can pre-change, post-change, regression, and failure behavior be proven? |
| Operational risk | What can fail during deploy, flagging, migration, or recovery? |

Recommend one approach or state that evidence is insufficient. For difficult or high-risk work, an
independent reviewer receives the problem brief, alternatives, and comparison, then returns
`approve`, `repair`, or `escalate` with cited reasons. The reviewer does not rewrite the artifacts. A
`repair` verdict here draws from that same shared repair-round budget as the problem and
verification checkpoints.

## 3. Human Plan Approval

Present the reviewed problem brief, alternatives, comparison, recommendation, intended scope,
validation plan, and material unknowns. Preserve the human's raw response and normalize it to
`approve`, `revise`, `stop`, or `ambiguous`; ask one concise clarification only when the response is
ambiguous. Bind an approval to the plan revision, selected approach id, environment, scope, side
effects, and rollback. If later evidence materially changes a binding, invalidate the prior approval
and return here before implementation continues. An implementation-only repair inside every binding
continues without another prompt.

## 4. Implementation and Verification

Run repository-defined checks plus two distinct quality checks:

- The code-quality check verifies correctness, regressions, maintainability, test coverage,
  security/privacy, performance, and repository conventions against the exact PR head.
- The solution-quality check verifies whether the implemented behavior actually solves the approved
  problem, remains within scope, preserves required unchanged behavior, and has credible before,
  after, interaction, rollback, and failure evidence.

Each check returns `pass`, `repair`, or `blocked` with concrete evidence. A failure blocks later
stages. Repair the same branch and PR under the attempt limits, then rerun the earliest affected
checkpoint and every downstream check whose evidence may have changed. A changed PR head requires
fresh revision binding and affected code-quality evidence.

## 5. Final Quality Review

Before the stage-9 handoff, summarize each checkpoint without rewriting its original verdict:

| Checkpoint | Required handoff evidence |
| --- | --- |
| Problem review | Verdict, failures repaired, remaining contradictions and unknowns |
| Approach review | Alternatives considered, comparison, recommendation, independent verdict when required |
| Human plan gate | Approved approach and scope, or pending decision |
| Code quality | Exact revision, checks, verdict, unresolved findings |
| Solution quality | Behavior and evidence verdict, regressions, rollback status |
| Verification | Before/after/interaction evidence, substitutions, inconclusive checks |
| Shipping gates | PR merge, experiment enablement, customer contact, and any other pending authorization |

The final reviewer may identify a missed issue and return the attempt to the earliest affected
checkpoint while repair budget and authorization remain. It cannot convert missing evidence,
unresolved disagreement, or a blocked checkpoint into a pass.

This document specifies agent behavior and observable artifacts. It does not prove that Operator,
Pantheon, a harness, or any other runtime enforces state persistence, reviewer isolation, repair
routing, or human gates.

For maintainers changing this workflow, use the separate
[HarnessBench evaluation package](harnessbench-evals.md); it is not a runtime stage.
