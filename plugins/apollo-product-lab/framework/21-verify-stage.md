# 21 — VERIFY, in depth

> Deep dive on the fourth box of [10-harness-overview](./10-harness-overview.md). Stage G.
> Closes gap 2 in [18-requirement-traceability](./18-requirement-traceability.md).
> **Status: draft for review. Nothing binding.**

## 1. What VERIFY answers

The brief asked for two things and they are genuinely different:

| Question | Kind of testing |
|---|---|
| Does it do what the acceptance criteria say? | Functional |
| **Can a person actually complete the task?** | UX flow |

Plus two the brief implied: did we break something else (regression), and what did nobody think to check (exploratory bug bash).

Code review is **not** here — it happens on the diff in BUILD, via [19-adversarial-review](./19-adversarial-review.md). VERIFY tests the running thing.

## 2. The test plan is derived, not invented

The single most important property of this stage.

**Acceptance criteria (Stage C) plus the required-state list (Stage D) *are* the test plan.** VERIFY does not sit down and imagine what to test. It enumerates:

- One test per acceptance criterion
- One test per enumerated state
- One test per constraint that the design was checked against
- One negative test per invariant (§4)

Two consequences worth stating plainly:

**If the earlier stages did their job, this stage is largely mechanical.** That is the payoff for the discipline upstream.

**If they did not, VERIFY cannot compensate.** A PRD with no acceptance criteria produces a test plan with no tests. A design with no state list means the ~24 non-happy-path states are untested and nobody notices, because a test plan that was never written cannot be seen to be missing.

This mirrors an existing precedent: `bug-bash-generator` already hard-stops when its five source documents are absent, rather than proceeding on vibes. Same principle, applied to the whole stage.

## 3. The four passes

| Pass | Derived from | Deterministic? |
|---|---|---|
| **Functional** | Acceptance criteria | Mostly. A criterion that cannot be turned into an assertion was badly written |
| **UX flow** | The required-state list | Partly. State presence is objective; whether a person can *complete* the task is not |
| **Regression** | Existing test suite plus the blast-radius assessment | Yes |
| **Exploratory** | The bug bash — variation matrix over inputs, roles, plans, timing | No, and that is the point |

The exploratory pass is the only one that is *supposed* to be undirected. Its value is finding what nobody enumerated, so constraining it to a checklist defeats it. Bound it by time or by count, not by scope.

## 4. The negative space is where this stage earns its cost

Normal QA tests that things happen. **The expensive failures are things that should not happen and do, or should happen and silently do not.**

For a compliance-bearing feature that is the entire risk surface:

- A record that should have been excluded gets exported
- A removal that should have propagated silently does not
- A consent signal defaults to permissive when it is unknown
- A paused sync keeps adding
- An opt-out is honoured for one identifier but not another the same person used

None of these produce an error. Nothing turns red. A functional test suite passes completely.

So **every invariant gets a negative test**, and the test asserts absence: after this sequence, that record is *not* in the audience; after an opt-out, no subsequent run re-adds them. This is the same class of problem as BUILD's monitoring point — absence of activity is the real failure, and it is the hardest thing to detect.

**A feature whose invariants have no negative tests has not been verified**, however green the suite is.

## 5. Blocking and escalation

Same model as adversarial review, for the same reasons:

| Outcome | Condition | Human? |
|---|---|---|
| **Auto-block** | A functional test fails, a negative test fails, a regression appears | No — falsifiable |
| **Auto-pass** | All derived tests pass and no evidenced finding from the exploratory pass | No |
| **Escalate** | A usability judgement, or a finding that is real but not obviously a defect | Yes |

Findings carry evidence — a reproduction, a screenshot, a state — or they are dropped. A bug report that cannot be reproduced is a hypothesis.

## 6. Routing a bug is a diagnosis

A defect found here is routed by **what produced it**, not by where it surfaced:

| Bug class | Routes to | Also |
|---|---|---|
| Implementation defect | BUILD, owning slice | — |
| Spec gap — criterion was wrong or missing | SPECIFY | **FIND should have caught it. Eval-case candidate** |
| Design divergence — built ≠ designed | DESIGN | — |
| Missing state — nobody enumerated it | DESIGN | State list was incomplete |
| Constraint violation | Compliance checker, **human arbiter** | Never auto-resolved |

The middle rows matter most. A bug that is really a spec gap, filed as an implementation bug, gets fixed in code and stays wrong in the document — so the next feature inherits it.

## 7. What to compose

Nothing here needs building from scratch:

| Existing | Role |
|---|---|
| `end-to-end-bug-bash` | Reads PRD/ERD/Figma/Jira/PR, builds a variation matrix, logs to Notion. Already hard-stops on missing inputs |
| `bug-bash-generator` | The matrix generator |
| `manual-test-execution` | Drives a real browser, writes report plus screenshots and video, files bugs back. Sets **`AI Status`, never the human `Status`** |
| `playwright-testing` | Automated flows |
| `qa-steps-for-eng` / `-non-eng` | One diff-tracing engine, two audience contracts |
| `tdd-loop` | When tests need writing rather than running |

`manual-test-execution`'s `AI Status` convention is worth generalising: **an agent records its verdict in its own field and never overwrites a human's.**

## 8. The blocker, and it now costs two stages

UX flow testing needs a browser. Neither Playwright MCP nor `agent-browser` is installed.

That same absence blocks Design's side-by-side variant rendering. **Two stages, one missing tool** — which makes it the highest-leverage unblock in the whole framework and a much smaller task than anything else on the open-questions lists.

Until then VERIFY runs functional, regression and negative passes, and the UX flow pass is manual.

## 8b. Runtime verification is a gate

Specs passing is not verification: on a past Ads M1 build the specs were green while the preview failed
OAuth, and the first live upload showed copy that read as an Apollo failure. A change is verified only
when it was exercised in the running app or preview; "specs pass, not exercised at runtime" is the honest
report otherwise.

For a UI PR, run `scripts/preview-status.py --pr <number>` before marking it ready. It must find a
successful preview run for the current head sha. A failed, cancelled, missing or still-running current
deployment keeps the gate open, even when an older sha remains deployed.

Before reporting CI as evidence, run `scripts/ci-doctor.py --pr <number>`. Before verifying stacked PRs,
run `scripts/stack-sync.py --tip <top-branch>` and review them bottom-up. Before sending the VERIFY status
report to a human, run `scripts/verify-claims.py <report.md>` and support every completion claim it lists.
These scripts are advisory and install no hooks (doc 52).

## 8c. Re-check host-path cost against live metrics before merge

Every host-path row of the Load model (doc 17 §6.2, IP18) is re-checked before merge against live
metrics: the host path's current peak calls/s, the shared resource's current peak, and, where the change
is on a preview or behind a flag, the resource's load with it on. A row still `[assumed]` or `unverified`
at this point is a pre-merge human check with the metric named; the gate does not pass on the design's
numbers alone. On a past Ads backend build the hook cost surfaced only when the EM asked about latency at
merge time.

## 9. Gates

| Gate | Asks |
|---|---|
| **G5a — correctness** | Derived tests green, negative tests green, host-path rows re-checked against live metrics (§8c), no unresolved escalation |
| **G5b — ship** | Given what we know, do we turn it on? |

G5b is deliberately separate. Verified and shippable are different questions, and conflating them is how a technically-correct feature ships into a bad moment — mid-quarter, before a dependency lands, or without the rollout plan from G4b actually being ready.

## 10. What VERIFY must not do

- **Not invent acceptance criteria.** If they are missing that is a finding routed to SPECIFY, not a gap to fill helpfully. Filling it hides the real defect.
- **Not fix what it finds.** The tester is not the author; that separation is what makes the verdict worth anything.
- **Not overwrite a human's status field.**
- **Not pass a feature whose invariants have no negative tests.**
- **Not treat a green suite as verification** when the suite was derived from an empty spec.

## 11. Open questions

| # | Question | Owner | Blocking |
|---|---|---|---|
| Q-V1 | Install Playwright MCP or `agent-browser`. Blocks UX flow testing here and variant rendering in Design | AI Tooling | Two stages |
| Q-V2 | How is the exploratory pass bounded — time, finding count, or variation-matrix size? Unbounded exploration is expensive; over-bounded is pointless | author | Bug bash cost |
| Q-V3 | Negative tests for invariants need a way to assert absence over time (a removal that never re-appears across scheduled runs). That is a different test shape from a single assertion and may need fixture support | author | Compliance verification |
| Q-V4 | Who signs G5b? Correctness is checkable; ship-readiness is a product call, and it is not obvious it belongs to the same person | Eng leadership + PM | Ship gate |
| Q-V5 | Nothing in VERIFY has been exercised, and it depends on upstream artifacts (criteria, state list) that no run has produced yet | author | Everything here |
