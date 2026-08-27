---
name: customer-problem-loop
description: Run the end-to-end customer problem loop with a PR, preview, evidence, Notion, and an optional experiment.
disable-model-invocation: true
argument-hint: '[problem description or intake link]'
---

# Customer-Problem Loop ("loopbot")

Turn one customer problem into a reviewable artifact set. Work in preview or staging by default.
Automate deterministic steps, but pause at the authorization gates below.

## Usage

Invoke with a problem description or intake link:
`/apollo-eng:customer-problem-loop <problem description or intake link>`

## Intake

Ask for what is missing; do not infer identities, authorization, or production scope.

- **Problem:** the complaint or gap in the customer's words, with a source link when available.
- **Customer:** name, email, and company. If no customer is named, use a staging team and say so.
- **Surface:** the affected product area. Confirm ownership through `surface-owners.yml`.
- **Outcome:** the smallest behavior change that would demonstrate the proposed solution.
- **Delivery:** whether the user wants only a plan, local code, a PR, a Notion page, or an
  experiment draft. If a Notion page is wanted, confirm which parent page it should be created
  under.
- **Run mode:** attended or unattended. Unattended runs carry the most cost risk; see
  [Cost guards](#cost-guards).

Before implementation, summarize the problem, proposed scope, target environment, planned writes,
and success evidence. Get approval if the user's invocation did not already authorize that scope.

## Required references

- Before stage 2, read [references/execution-playbook.md](references/execution-playbook.md) in full.
- Before pushing code in stage 3, read
  [references/pre-push-checks.md](references/pre-push-checks.md) in full.

## Authorization gates

| Stage | Default | Gate |
| --- | --- | --- |
| 1. Intake and scope | Pause | Confirm the problem, smallest change, environment, and deliverables. |
| 2. Locate and inspect | Read-only | Resolve the staged identity; get explicit approval before impersonating anyone. |
| 3. Implement and open PR | Allowed within approved scope | Stop if the solution or side effects exceed the intake agreement. |
| 4. Deploy preview | Allowed for the approved PR | Verify the real deploy job and serving host. |
| 5. Change feature flag | Pause | Confirm the exact preview/staging environment, team id, flag, new value, and rollback. |
| 6. Capture evidence | Read-only for anything beyond the stage 5 flag | Screenshots only. Do not spend credits, mutate customer data, fake a before state, or flip any flag/permission that stage 5 did not already approve. |
| 7. Publish 1-pager | Conditional write | Draft locally unless Notion delivery was approved at intake or approved now. |
| 8. Create experiment | Conditional write | Create only if approved; never enable it. |
| 9. Ship decisions | Pause | Experiment enablement, PR merge, and customer contact each need separate approval. |

## Safety invariants

- Treat production and real customer data as read-only. Never change a production flag, spend
  customer credits, seed production data, or perform a write while impersonating a customer.
- Limit flag changes to an explicitly confirmed preview or staging target. Record the prior value
  and rollback before writing.
- Keep impersonation read-only and time-bounded. If the staged customer copy is unavailable, use a
  representative staging team and disclose the substitution.
- Never enable an experiment, merge a PR, or contact a customer without a separate explicit request.
- Stop on missing evidence, permissions, or environment certainty. Do not convert an unverified
  assumption into an automated action.
- Keep the customer's raw name, email, and company out of PRs, screenshots, experiment metadata,
  Notion pages, handoffs, and logs. Refer to them by the staged team/user id instead; keep any
  mapping back to their real identity in the intake conversation, not in a generated artifact.

## Cost guards

Both guards are stop conditions. They target the two ways an agentic loop runs up cost: a run that
repeats itself while nobody is watching, and an expensive capture mode.

**Guard 1 — one invocation is one attempt.**

- Do not restart at stage 1, open a second PR for the same problem, or retry a stage that failed.
- Stop a failed or inconclusive run and hand off per stage 9.
- The loop cannot meter its own spend, and Apollo's Claude budgets are monthly per-user limits, not
  per-run governors. Nothing halts one expensive unattended run mid-flight, so these caps are the
  only limit that applies during it.

**Guard 2 — bounded waits, screenshots only.**

- Screenshots are the stage 6 deliverable. Do not record video, parse frames, transcribe a session,
  or add a capture worker unless the invocation asked for it.
- Cap every wait, not only stage 4's deploy poll: give flag propagation, Notion writes, and
  Amplitude calls a bounded timeout too, and hand off rather than waiting indefinitely on any of
  them.
- Pass screenshots by file path. Confirm each file exists and is non-empty; do not read captures
  back into context to confirm they worked.

## Execute the loop

1. **Intake:** agree on the smallest flag-gated change and the evidence needed to evaluate it.
1. **Locate:** resolve the staged user/team, then request the impersonation gate before opening a
   godmode session.
1. **Implement:** reuse shipped primitives, preserve flag-off behavior, test the change, open the PR,
   and request the preview environment according to repository conventions.
1. **Deploy:** watch the actual deploy job and confirm the preview host serves the changed revision.
1. **Enable in preview/staging:** after the flag gate, set the explicit target state and retain the
   prior value for rollback.
1. **Capture:** produce real before, after, and interaction evidence. Assert the changed element and
   resulting interaction are present before taking screenshots.
1. **Document:** draft a cold-reader 1-pager with the problem, evidence, behavior, risks, success
   metric, owner, rollout, open questions, and build notes. Publish only when authorized.
1. **Experiment:** prepare or create the Amplitude experiment if approved. Stop before enabling it.
1. **Handoff:** report links, test/deploy evidence, substitutions, remaining risks, rollback, and each
   pending human decision.

## Definition of done

- The PR is current with its base branch and required checks pass.
- The preview host serves the reviewed revision.
- Before, after, and interaction evidence show a real difference without unsafe customer actions.
- The 1-pager is understandable to a cold reader and names risks, success metrics, ownership, and
  rollout.
- Any experiment is created but disabled.
- Merge, experiment enablement, and customer communication remain pending until explicitly approved.
- The run made one attempt. Anything a cap cut short is handed off, not retried.
