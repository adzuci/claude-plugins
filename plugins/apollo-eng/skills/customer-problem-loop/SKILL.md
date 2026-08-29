---
name: customer-problem-loop
description: Run a checkpointed customer problem loop with bounded repair and explicit human gates.
disable-model-invocation: true
argument-hint: '[problem description or intake link]'
---

# Customer-Problem Loop ("Loopbot")

Turn one customer problem into a reviewable artifact set. Work in preview or staging by default.
Automate deterministic steps, but pause at the authorization gates below.

## Usage

```text
/apollo-eng:customer-problem-loop Run a light local review of CVR-1643. First build a source-backed
problem brief, then inspect current behavior and recommend the smallest change and validation plan.
Do not implement, push, publish, merge, or contact the customer.
```

The invocation must name the problem or intake link, target environment, and requested deliverables.
If any are absent, collect them during intake instead of assuming broader authority.

## Intake

Ask for what is missing; do not infer identities, authorization, or production scope.

- **Customer reference:** an opaque ticket or approved lookup reference. Treat it as a pointer to
  the underlying request, not as the request itself. Read the full approved source and relevant
  linked evidence; never scope from only the identifier, title, or summary.
- **Problem understanding:** preserve the customer's words separately from the agent's
  interpretation. Determine whether the source describes a bug, feature request, usability gap,
  outcome gap, or a mixed/unclear problem. Capture observed behavior or requested outcome, expected
  behavior or user goal, affected user and surface, impact/frequency when supported, constraints,
  evidence, contradictions, and open questions. Do not force a classification when evidence is
  mixed.
- **Privacy:** keep raw name, email, and company only inside the access-controlled lookup flow; do
  not copy them into logs, PRs, evidence paths, product briefs, experiments, or handoffs. If no
  customer is named, use a staging team and say so.
- **Surface:** the affected product area. Confirm ownership through `surface-owners.yml`.
- **Outcome:** the smallest behavior change that would demonstrate the proposed solution.
- **Delivery:** whether the user wants only a plan, local code, a PR, a Notion page, or an
  experiment draft. If a Notion page is requested, confirm its parent page during intake. If no
  parent is confirmed, stage 7 must stop before publication.
- **Run mode:** attended or unattended. Unattended runs carry the most cost risk; see
  [Cost guards](#cost-guards).

Before proposing a solution, produce a source-backed problem brief that distinguishes confirmed
facts, customer language, interpretation, and unknowns. Resolve material ambiguity with targeted
questions or stop with an explicit research gap. Only then summarize the proposed scope, target
environment, planned writes, and success evidence. Get approval if the invocation did not already
authorize that scope.

## Required References

- Before completing stage 1, read
  [references/checkpoint-flow.md](references/checkpoint-flow.md) in full.
- Before completing stage 1, read
  [references/repair-contract.md](references/repair-contract.md) in full.
- Before stage 2, read [references/execution-playbook.md](references/execution-playbook.md) in full.
- Before pushing code in stage 3, read
  [references/pre-push-checks.md](references/pre-push-checks.md) in full.

## Authorization Gates

| Stage | Default | Gate |
| --- | --- | --- |
| 1. Understand and scope | Pause | Pass problem and approach review, then confirm the source-backed problem brief, material unknowns, selected approach, environment, and deliverables. |
| 2. Locate and inspect | Read-only | Resolve the staged identity; get explicit approval before impersonating anyone. |
| 3. Implement and open PR | Allowed within approved scope | Stop if the solution or side effects exceed the intake agreement. |
| 4. Deploy preview | Allowed for the approved PR | Verify the real deploy job and serving host. |
| 5. Capture before and change flag | Pause | Capture the genuine flag-off state, then confirm the exact environment, team id, flag, new value, and rollback before writing. |
| 6. Verify and capture after | Read-only beyond the stage-5 flag | Assert the changed behavior and capture after/interaction evidence. Do not spend credits or mutate customer data. Do not change any flag or permission that stage 5 did not approve. |
| 7. Publish product brief | Conditional write | Draft at the length the problem requires; publish only if Notion delivery was approved at intake or approved now. |
| 8. Create experiment | Conditional write | Create only if approved; never enable it. |
| 9. Ship decisions | Pause | Experiment enablement, PR merge, and customer contact each need separate approval. |

## Safety Invariants

- Treat production and real customer data as read-only. Never change a production flag, spend
  customer credits, seed production data, or perform a write while impersonating a customer.
- Limit flag changes to an explicitly confirmed preview or staging target. Record the prior value
  and rollback before writing.
- Keep impersonation read-only and time-bounded. If the staged customer copy is unavailable, use a
  representative staging team and disclose the substitution.
- Never enable an experiment, merge a PR, or contact a customer without a separate explicit request.
- Stop on missing evidence, permissions, or environment certainty. Do not convert an unverified
  assumption into an automated action.

## Checkpoint Flow

Use one primary agent to retain state and ownership across the attempt; reviewers inspect bounded
artifacts and return a verdict without replacing the primary agent or expanding scope. See
[references/checkpoint-flow.md](references/checkpoint-flow.md) for full detail on each checkpoint.

- **Problem checkpoint:** confirms the source-backed problem brief before solutioning; a failure
  blocks approach selection until the brief is repaired.
- **Approach checkpoint:** compares materially different approaches and, for difficult or high-risk
  work, requires an independent approach-review verdict before requesting human plan approval; do
  not manufacture alternatives for a trivial change with one evidence-backed implementation.
- **Human plan checkpoint:** binds approval to the plan revision, selected approach, environment,
  scope, side effects, and rollback; a material change to any binding invalidates prior approval and
  returns to this checkpoint.
- **Implementation and verification checkpoints:** code-quality and solution-quality checks must
  pass before progression. A failed checkpoint records the evidence and blocks downstream stages;
  repair under the bounded attempt contract, then rerun the earliest affected checkpoint and its
  downstream checks.
- **Final-quality checkpoint:** before handoff, report the problem-review, approach-review,
  code-quality, solution-quality, verification, and human-gate statuses, preserving unresolved
  disagreements and unknowns instead of averaging them into a pass.

## Attempt and Repair Contract

One invocation is one bounded attempt: one initial pass plus at most two repair rounds — a single
budget shared across problem, approach, and verification checkpoint repairs — within a 60-minute
wall-clock deadline. The branch, PR, preview host, and flag target bind once and are reused across
every repair. See [references/repair-contract.md](references/repair-contract.md) for the full
contract, including resume rules and when to hand off to stage 9.

## Cost Guards

Both guards are stop conditions. They target the two ways an agentic loop runs up cost: a run that
repeats itself while nobody is watching, and an expensive capture mode.

**Guard 1 — one invocation is one bounded attempt.**

- Do not restart at stage 1 or open a second PR for the same problem; see
  [references/repair-contract.md](references/repair-contract.md) for the repair-round cap and
  hand-off conditions.
- The loop cannot meter its own spend. These are agent-owned policy limits, not known runtime
  guarantees; never assume Operator, Pantheon, or another platform will enforce them.

**Guard 2 — bounded waits, screenshots only.**

- Screenshots are the stages 5–6 deliverable. Do not record video, parse frames, transcribe a session,
  or add a capture worker unless the invocation asked for it.
- Cap every wait; see the per-stage caps in
  [references/execution-playbook.md](references/execution-playbook.md).
- Pass screenshots by file path. Confirm each path exists and has non-zero size without reading the
  image back into model context.

## Execute the Loop

1. **Understand and scope:** read the underlying request and linked evidence, produce and review the
   source-backed problem brief, resolve material ambiguity, compare the required alternative
   approaches, obtain independent review when risk or difficulty requires it, then pass the human
   plan checkpoint for the selected flag-gated change and evidence needed to evaluate it.
1. **Locate:** resolve the staged user/team, then request the impersonation gate before opening a
   godmode session.
1. **Implement:** reuse shipped primitives, preserve flag-off behavior, test the change, open the PR,
   and request the preview environment according to repository conventions.
1. **Deploy:** watch the actual deploy job and confirm the preview host serves the changed revision.
1. **Capture before and enable in preview/staging:** prove the flag is genuinely off, capture the
   before state, then pass the flag gate, set the explicit target state, and retain rollback.
1. **Verify and capture after:** assert the changed behavior and its data-bearing calls, then produce
   real after and interaction evidence. Use only the flag state approved in stage 5; do not change
   another flag or permission during capture. On failure, follow the repair contract on the same PR.
1. **Document:** draft a right-sized cold-reader product brief with the relevant problem, evidence,
   behavior, risks, success metric, owner, rollout, open questions, and build notes. Do not force a
   one-page limit or pad a simple change. Publish only when authorized.
1. **Experiment:** prepare or create the Amplitude experiment if approved. Stop before enabling it.
1. **Handoff:** pass the final-quality checkpoint, then report links, test/deploy evidence,
   substitutions, remaining risks, rollback, every checkpoint and check status, and each pending
   human decision.

## Definition of Done

- The PR is current with its base branch and required checks pass.
- The preview host serves the reviewed revision.
- Before, after, and interaction evidence show a real difference without unsafe customer actions.
- The product brief is as long as the problem requires, is understandable to a cold reader, and
  names the relevant risks, success metrics, ownership, and rollout.
- Any experiment is created but disabled.
- Merge, experiment enablement, and customer communication remain pending until explicitly approved.
- The attempt used no more than two repair rounds. Each failure, change, and reverified check is in
  the handoff; anything a cap cut short remains explicitly incomplete.
- The handoff includes the problem-review, approach-review, code-quality, solution-quality,
  verification, and human-gate statuses without hiding unresolved disagreements or unknowns.
