---
name: experiment-exposure-design-beta
description: >-
  BETA. Plans, reviews, and helps fix the exposure and audience-targeting design
  of a leadgenie experiment: where exposure fires, whether both arms reach it the
  same way, where eligibility lives, and whether an A/A dry run is warranted.
  Runs at planning, setup or PR review, or a scope change. Hands over chat
  findings and offers setup or fixes as a draft PR. Not for sizing
  (experiment-pre-analysis-beta), event ordering in a diff
  (experiment-exposure-order), or interpreting results.
disable-model-invocation: true
metadata:
  lifecycle-stage: Execution
---

# Experiment Exposure Design

Lifecycle stage: **Execution**. Follow
`${CLAUDE_PLUGIN_ROOT}/references/experiment-lifecycle-conventions.md` for how to
open, check tools, collect inputs, teach, hand over, review, and close. This file
holds only what is specific to exposure design.

Exposure logic decides *who* is counted in an experiment and *when*. When it is
wrong, the experiment is wrong no matter how good the treatment is, and the
failure shows up as a skewed split or a confusing readout weeks later, after the
data is lost. This skill is a first-pass checklist and thinking partner: it helps
plan, review, and fix exposure implementation.

## Invocation

```text
/apollo-eng-experimentation:experiment-exposure-design-beta [flag key | PR | branch]
```

The argument is optional; intake asks for anything not passed.

## Open

- **Produces:** a placement plan (nothing in code yet) or a review of where
  exposure fires and who reaches it (code or PR), with the A/A decision recorded
  and setup or fixes offered as a draft PR.
- **Does not:** size or power the experiment (`experiment-pre-analysis-beta`);
  check exposure-before-metric ordering in a diff (`experiment-exposure-order`);
  verify a running A/A's data (`experiment-aa-run-verification-beta`); interpret
  results.

## Preflight

- **leadgenie checkout**, required for Stages B and C and for any setup or fix.
  With no repo, offer Stage A planning only and say so.
- **Amplitude MCP** for the flag config, and to create the experiment if Stage A
  ends in setup. Without it, the user pastes or describes the config (bucketing
  unit, targeting, allocation, rollout, variants); say the config side is on
  their word.
- **GitHub CLI** authenticated, if setup or fixes may be offered as a draft PR.
- Read `references/leadgenie-mechanics.md` before any stage: how experiments are
  wired in this repo (registry, hooks, backend relay, team-level assignment
  cache, dedup, god mode, nil variant), with grep starters.

## Inputs

Ask, in one message, which stage the user is at:

> (a) planning, nothing in code yet · (b) exposure or eligibility already in
> code or a PR, including the PR that adds the treatment render · (c) scope or
> eligibility changed mid-build.

Then collect: flag key(s) (A/A and A/B if both), PR or branch, context docs, and
for any stage after (a) the prior stage's hand-over if the user has one. Read it
first as the *prior* understanding, still confirming nothing changed; none
existing is fine.

Before reading code, get the experiment into the user's own words with the
"Always" questions in `references/coaching-questions.md`: hypothesis, treatment
happy path, **first visible divergence** (as the user perceives it, not where the
code branches; that is the candidate exposure point), eligibility and whether it
is knowable at assignment time, and entry routes per arm. Pick the three to five
that matter, one or two per message. Restate in four to six lines and get a yes.
If linked docs contradict it, name the discrepancy and ask which is current.

## How to work

- **The user's current understanding is the source of truth, not the docs.**
  Use linked docs for context and to spot discrepancies.
- **Invert the burden of proof on dry runs, kindly.** Ask "why do you *not* need
  an A/A?" The only clean skip is unchanged eligibility *and* unchanged exposure
  point on an already-trusted path. Respect the team's call; record the decision
  and reasoning either way.
- **Verify in code; never invent a finding.** If you can read the code path, read
  it. If you cannot, say so and present it as a question with how to verify.
- **Explain placement, do not just name it.** Whenever you propose an exposure
  point or recommend moving one, say in chat why that spot: why it cannot fire
  while the UI is loading, empty, or hidden; which render branches reach it; and
  any window where it is imprecise, with whether that imprecision is the same
  for both arms. The reader needs to defend the placement in review.
- Frame misses as placement errors, not blame: one plain sentence on what could
  go wrong, at most one real Apollo example from
  `references/pitfall-catalog.md`, then the fix.

## Stage A: planning (nothing in code yet)

Goal: a concrete placement plan, an A/A decision, and, if the user wants it, the
setup in a draft PR.

1. Explore the codebase around the named surface(s): where the first visible
   divergence would render, every route into it, conditionals above that point
   that could block treatment, and any experiment hooks already on the surface.
1. Propose, in plain terms with file paths and the why:
   - **Exposure point(s)**: the same moment for both arms. With two candidate
     moments (renders vs hover), fire at whichever happens first, in *both* arms.
     Prefer a small composed component owning the hook so exposure cannot fire
     while the UI is hidden.
   - **Eligibility gate**: one check, one place, same for every arm, using only
     data available at assignment time. Say what lives in Amplitude targeting vs
     code, and why.
   - **Variant reads**: ask how the treatment code will read the variant. The
     invariant is that treatment never renders where exposure did not fire, and
     never for a team the exposure gate would exclude. The simplest way to keep
     it is for every read to go through the same hook and eligibility check as
     the exposure call, the pattern most leadgenie teams already use. If the
     team does it differently, make sure the invariant still holds and say how.
   - **Treatment isolation**: net-new component(s) over conditionals threaded
     through shared code, where practical, so nothing above the exposure point
     blocks one arm.
1. Walk `references/aa-dry-run-guide.md` with them; record the A/A decision and
   reasoning.
1. Offer to set it up. If the experiment does not exist yet in Amplitude or the
   registry, run `/apollo-eng-experimentation:create-amplitude-experiment` (for
   an A/A, named as the dry-run guide says). Then write the exposure component,
   hook wiring, and eligibility gate from the plan, show the diff, and offer a
   draft PR under the same rule as fixes.
1. Hand over (see *Hand over*).

## Stage B: review existing setup (code or PR; dry run, real A/B, or both)

Goal: find exposure and eligibility mistakes before production traffic does, and
say how sure you are.

1. Locate everything for the flag key(s): registry entry, every variant read
   site, every exposure path, backend usage, routing or selectors reading the
   variant, Amplitude config (see *Amplitude config*). If the diff also adds or
   reorders **metric events**, run `/apollo-eng-experimentation:experiment-exposure-order`;
   whether exposure is *recorded before* the metric is that skill's job. This one
   owns *where* exposure fires and *who* reaches it.
1. Trace the code path of **each arm separately**, entry route(s) to exposure
   call. Work the pitfall catalog's quick check: per pitfall, present, not
   present, or could not tell, with file and line. A variant read whose
   eligibility differs from the exposure call's, or that can render treatment
   where exposure never fires, is a finding.
1. **Treatment render PR, or flipping the key to the real A/B**: exposure code
   should not have changed since the A/A. Check that every treatment render
   path reads the variant through the gated hook, that the registry `variants`
   match Amplitude for the real key, and ask (not verifiable from code) whether
   the A/A result was reviewed: exposures balanced, volume near the DS
   estimate, guardrails flat. If not, point at
   `experiment-aa-run-verification-beta`. Whether the treatment itself is right
   is not this skill's job.
1. Know how sure each finding is: traced both arms end to end; traced with a
   named assumption; or unresolved. Unresolved findings are written as
   questions with a concrete way to verify, for example reproduce locally and
   watch the `experiment.expose` dev log and the `/experiments/expose` network
   call. The words carry the confidence; the hand-over carries no grades.
1. Recommend: ship as-is, fix then ship, or fix and (re)run the A/A. Record the
   A/A decision.
1. Offer the fixes, then hand over. For a launch, end with the launch-day
   checklist: both arms firing on first load, split watched for 48 to 72 hours.
   That checklist is for the engineer; this skill does not run it.

## Stage C: re-verify on scope change

Mid-build eligibility or exposure changes are how one experiment quietly becomes
three populations.

1. Read the prior hand-over if there is one; ask what changed and why, in one
   message.
1. Diff: eligibility, exposure point(s), surfaces and routes, variants, flag key,
   concurrent experiments. Call out changes they did not mention.
1. If eligibility or the exposure point changed: the DS volume estimate is stale
   (flag it) and the A/A decision must be re-made; a clean A/A does not cover a
   new population. If already live: targeting changes mid-run are not supported
   (bucketing locks; a new key is the clean path). Route to DS.
1. Re-run the relevant Stage B checks on the changed paths only. Hand over,
   saying what changed and what it replaces.

## Amplitude config

Code is only half the setup; check it against the Amplitude side using
`references/amplitude-config-checks.md`. With the MCP: `use_amp_flags` (action
`get`) accepts flag **keys** directly; for experiment-level detail resolve the
numeric ID with `search_amp_entities` (`entityTypes: ["EXPERIMENT"]`) and use
`use_amp_experiments` (action `get`). If a needed field is not returned, ask the
user to read it off the Amplitude UI.

## Hand over

One chat block, the same shape every stage, issued after any setup or fixes
have landed. It is the record of the session: what was identified, what was
done, and when to come back.

```text
**Exposure review: <flag key> · <planning | setup review | scope change>**
Recommendation: <ship as-is / fix then ship / fix and (re)run the A/A / re-scope>, because <one line>.
<Scope change only: what changed, and which earlier hand-over this replaces.>

<Planning: the placement plan. Exposure point(s), eligibility gate, variant
reads, each with file paths and the one-line why.>
<Setup review or scope change: the findings table.>
| # | What could go wrong | Where (file:line) | How sure | Suggested fix |
|---|---|---|---|---|

A/A dry run: <run / skip>, because <reasoning>.
Done this session: <experiment created, files changed, draft PR link, or "nothing applied">
Still open: <questions, each with an owner>
Next: <when to come back: the PR for review, a re-check if scope changes, the A/A result to experiment-aa-run-verification-beta>
```

**Setup or fixes as a draft PR** (any stage). Show each diff in chat. On an
explicit yes, apply it to the leadgenie checkout and ask: "want me to open a
draft PR in leadgenie with these changes?" On a second yes, commit on a branch
named `<user>/<flag key>-exposure` and open the PR with `gh pr create --draft`.
Never apply, commit, or push without those answers.

## Review

The conventions' silent review, plus:

- Every confident finding's file and line re-opened and confirmed.
- Every pitfall marked not present was actually checked, not skipped.
- Unresolved items are written as questions with a concrete way to verify.
- The A/A decision and its reasoning are recorded, whichever way it went.
- Every proposed or moved exposure point comes with its why.
- A scope-change hand-over says what changed and what it replaces.

## Never

- Apply or push code without a shown diff and a yes.
- Compute a split check or read results; route to the A/A verification sibling.
- Decide the A/A for the team; record their decision and reasoning.

## Reference files

Paths relative to this skill's folder.

- `references/leadgenie-mechanics.md`: repo wiring, verified facts, grep starters
  (all stages).
- `references/pitfall-catalog.md`: pitfalls, code signals, real Apollo examples
  (Stages B and C).
- `references/coaching-questions.md`: guided questions (all stages).
- `references/aa-dry-run-guide.md`: when a dry run is worth it and how to set it
  up (the A/A decision).
- `references/amplitude-config-checks.md`: Amplitude-vs-code checks.
- `references/glossary.md`: plain-English definitions to reuse inline.
- `references/sources.md`: internal and external sources for deeper dives.
