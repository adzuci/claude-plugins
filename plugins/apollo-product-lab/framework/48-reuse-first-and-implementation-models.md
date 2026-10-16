# 48 — Reuse first, and the model that implements

> Decision 2026-10-14 (Akansh). Three gaps showed up in one Ads build. The enrichment walk hand-wrote
> waterfall permission, consent and credit checks that `EnrichmentValidationHelper.validate_enrich`
> already runs for the rules engine's scheduled missing-email enrichment, which starts the same job type.
> Nobody looked at the job's other callers. The wizard's enrichment step hand-built radio cards from a raw
> `<button>` where Fabric has the component, and a reviewer had to ask "why not our DS button component?".
> And every line of implementation ran on the session's base
> model (Opus): doc 44 routes review lenses by role, but nothing routed implementation, so the registry's
> `build.slice-owner: sonnet` was never applied. Reuse is the default; the platform lens (doc 47) asks the
> same question one level up, across products.

## 1. Reuse scan: on by default

Before new code is written in a slice or a design, the author (the `implementer` agent in BUILD, the
architect in DECIDE) runs a reuse scan. It is not conditional the way the platform lens is: it runs on
every slice and every design. The only skip is a one-line fix, recorded as `reuse scan: skipped (one-line fix)`.

**Where to look, in order:**

1. **Other callers of what the change calls.** For each job type, service, model method or endpoint the
   change uses, `rg` its other callers and read how they prepare and check the call. They are the most
   likely place the needed pre-flight, mapping or guard already lives. This is the step the Ads run missed.
1. **Public surfaces of the owning pack.** Its `INTERFACE.md`, `app/public/`, and names ending in
   `Helper`, `Validator`, `Service`, `Util`, `Builder`. Frontend: `@apolloio/fabric-core` docs, then
   `@apolloio/fabric`, then the product package's `docs/base.md`.
1. **The platform record.** Doc 47 rows and the initiative's `knowledge/platform-opportunities.md`.
1. **No checkout.** Glean `code_search` stands in; what no tool opened is `unverified`.

**What it writes.** One reuse table in the slice snapshot and in the PR description's reviewer guidance:

| Need | Existing candidate (path) | Decision | Reason |
|---|---|---|---|
| one row per function, check, query, validator or component the change needs | the closest thing that exists, or `none found: <what was searched>` | reused / extended / not reused | for "not reused", a reason a reviewer can check |

**What counts as a defect.** Code that duplicates a candidate the scan found, or would have found by step 1,
is a `major` in review (category `repo_convention`). The reviewer cites the candidate's path. A
candidate that does part of the job is extended or composed, and the new code covers only the rest. For
example, `validate_enrich` returns pass or fail and does not size a page to the credits left, so the Ads
walk keeps its own page sizing and calls the helper for the rest.

**Relation to doc 47.** The platform lens asks whether a *capability* should exist once across products, and
it waits for a human. The reuse scan asks whether *code* already exists, and the author acts on it
directly. When the scan finds a near-same capability owned by another product, it opens the doc 47 lens
rather than deciding alone.

## 1b. Frontend: Fabric components, strictly

Frontend UI is built from the design system, not next to it. This is a gate, not a preference.

1. **Order.** `@apolloio/fabric-core` first (read `node_modules/@apolloio/fabric-core/component-docs.md`,
   then the component's own doc under `docs/`), then the local `@apolloio/fabric` public entry points
   (`@apolloio/fabric`, `/patterns`, `/tables`), then the product package's existing components. Custom UI
   only when none of the three has it.
1. **What counts as hand-built.** A raw `<button>`, `<input>`, `<select>`, `<table>`, a radio or checkbox made
   from a `div` or `button` with an ARIA role, `className="text-*"` typography where a Fabric text component
   exists, or SCSS that re-creates a component's look. Importing one Fabric primitive inside a hand-built
   structure still counts.
1. **The record.** Every frontend slice adds Fabric rows to its reuse table: need | Fabric component used |
   or `none fits` with the docs checked. A `none fits` row names the closest component and what it lacks;
   that row is what the frontend owner reviews, and it may open a request to the design-system team.
1. **In review.** Hand-built UI where a Fabric component fits is a `major` (category `repo_convention`),
   with the component's doc path. In leadgenie this is the frontend reviewer's F21.

## 1c. Read every check before saying a PR is ready

A PR is not reported ready, to a human or in a snapshot, until every failing or pending check has been
read, not just the test jobs. For each one, write a line: check | failing because | fixable by us /
human gate (who) / flake (with the base-branch run that proves it). In leadgenie the ones that hide are
`verify-job-runs-on-sensitive-files-approval` (a file under another team's `sensitive_files` needs that
team's approval: name the team and the Slack channel), `policy-bot` (an approval or a requested change),
`coverage`, and `affected-unit-tests` on files outside the package the PR changed (a shared flow that
opens the changed component). Review comments, human and bot, are part of this read.

## 2. Which model implements

| Role | Agent | Model | When |
|---|---|---|---|
| `build.implement` | `implementer` | Sonnet 5.5 | the default for every slice |
| `build.implement.complex` | `implementer-complex` | Opus 5.5 | any trigger below holds |

The main session plans, writes the brief, reviews what comes back and owns every outward action (commit,
push, PR, posts). It does not write the slice itself unless the slice is a few lines.

**Base plans, cheaper models execute.** The main session (the base model) writes one plan file per build,
`runs/<run-id>/builds/<id>/plan.md`: the exact files, the edits, the specs to run in order, and the commit
message. Everything that executes the plan runs on a cheaper model:

| Work | Model |
|---|---|
| Mechanical edits, sweeps, reading logs and CI output | Haiku 4.5 |
| Code to a written plan | Sonnet 5.5, or `gpt-5.6-sol` at medium effort |
| Reviews | the lens models in doc 44 (Astra at xhigh for the cross-family lens) |
| Verification before any push: read the diff, run the specs, `srb tc`, rubocop | the base model, always |

A builder's report is never evidence; verification is a small share of the tokens and catches what the
report hides. Two ways to run `gpt-5.6-sol`: an agent with `model: gpt-5.6-sol` in a session started with
`ANTHROPIC_BASE_URL` pointing at shunt, or `codex exec -m gpt-5.6-sol -c model_reasoning_effort="medium"`.
Set reasoning effort per route in `shunt.toml` (`[[routes]] effort = ...`), never on `[providers.codex]`:
shunt resolves effort route, then provider, then the request's effort, then thinking enabled (high), then a
model-name suffix, then medium; set effort on each route, since a provider-level value applies to every route
that does not set its own. See [Effort & Context](https://shunt.sh/guides/effort-and-context/).

**Escalate to Opus 5.5 when any of these holds:**

1. **Unknown runtime behaviour across packs.** The change depends on something no spec or doc states: what
   a job's "done" means, how retries reach a worker, what another team's model guarantees. (On Ads,
   "the job finished" meant "the page was sent to the vendor", and persisted jobs never reach the worker's
   retries-exhausted hook. Both were found by reading the code end to end.)
1. **A concurrency, idempotency or crash-recovery design** the plan does not already spell out.
1. **Money, credits, consent or deletion** logic beyond what the plan states.
1. **A design, data model or public contract change.**
1. **Two failed attempts** by `implementer` at the same failing check, or an `escalate:` in its report.

Mechanical work stays on Sonnet even inside a complex initiative: specs to a stated plan, mutation runs,
rebases, PR description edits, renames, copy.

**Brief.** Doc 46 §4 applies: the goal, the files the agent may touch, the specs that must pass, the checks
to run in order, and pointers to the code, not pasted file bodies. The reuse scan is part of every brief.

**Evidence.** Record the agent and model that served the slice in its snapshot (`produced_by`). A slice the
main session wrote itself says so and gives the reason (`few lines`, or the trigger it hit).

## 3. Until the agents load

Agent files load at session start (doc 44 §1 rule 3). In a session started before `implementer` existed,
dispatch `general-purpose` with an explicit `model: sonnet` (or `opus`) and the implementer brief, and
record that in the snapshot. Unlike lenses, an implementer does not need an independent family, only the
right model.
