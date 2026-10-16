# 20 — BUILD, in depth

> Deep dive on the third box of [10-harness-overview](./10-harness-overview.md). Stage F, plus the deployment surface that was missing entirely (gap 1 in [18-requirement-traceability](./18-requirement-traceability.md)).
> **Status: draft for review. Nothing binding.**

## 1. What BUILD answers

Two questions, and the second one was absent from the design until now:

| Question | Covered by |
|---|---|
| Does the code exist and is it correct? | Slice owners, contract keeper, integrator |
| **Can it be safely turned on, and can someone else keep it running?** | **The deployment surface (§6)** |

A feature that merges but has no flag, no alert and no runbook is not built. It is a liability someone else discovers at 3am.

## 2. Slicing: the axis people get wrong

The most consequential decision in BUILD, made before any agent starts.

**The common mistake is slicing by discipline** — one frontend slice, one backend slice. That is not independence. Frontend and backend on the same feature share an API contract, which is the *tightest* possible coupling. Two agents on either side of one contract will each invent it, differently, and both will pass their own tests.

**Slice by dependency, into vertical pieces.** A good slice is a thin complete thing: it can be built, tested and merged without waiting on another slice's decisions. If two slices must agree on a data shape or an error semantic, they are one slice — or they need a contract written first.

Run `slice-fit` before partitioning. It tells you which slices an agent can own at all, on four axes: blast radius, precedent, verifiability and failure visibility. On the one real initiative it returned **~15% agent-ownable**, which was uncomfortable and correct.

## 3. How many agents

An earlier draft said "N = 2 for the pilot." **That was wrong, and the error is instructive.**

Two is the *human* number. It came from an estimate written in human-sized chunks — Phase 1, Phase 2, each three to seven days, because that is a sensible unit of work for a person. Inheriting that slicing for agents imports a constraint that does not apply to them.

**Agent parallelism is limited by semantic independence, not by coordination overhead.** Humans cannot be scaled onto a project freely because of communication cost, onboarding and context switching. Agents have none of those — they cannot talk to each other anyway. What still binds is whether two pieces of work must agree on something.

So: **re-slice at agent granularity rather than inheriting the human plan.** A six-day human phase like "sync foundation models" may contain four or five genuinely independent pieces — the model, the adapter interface, the gateway wrapper, status polling, error mapping — each of which one agent can own end to end. Decomposed that way, a project sized for two engineers can legitimately support ten agents.

### But finer is not free

Every additional slice adds a **seam**. More seams means more for the contract keeper to define up front and more for the integrator to reconcile at merge. The cost curve has a minimum, not a maximum:

- **Too coarse** — agents idle, wall-clock stays long, no benefit over the human plan
- **Too fine** — contract-definition overhead dominates, and the integrator drowns in semantic conflicts between pieces that should have been one slice

### The real ceiling is escalation rate, and it is measurable

Ten agents producing ten PRs still needs review. Review is itself agent-driven (see [19-adversarial-review](./19-adversarial-review.md)), so it scales — but **every escalation reaches a human**, and humans do not scale.

So the binding constraint is not agent capacity. It is:

> **How many escalations per hour can the DRI absorb?**

That makes autoscaling a measured decision rather than a guess. If the auto-pass rate is high, run more agents. If escalations are arriving faster than they are resolved, the answer is fewer agents *or* better deterministic checks — not more parallelism.

Both numbers already exist in the ledger: `outcome` gives auto-pass rate, and escalations are counted per gate. So the scaling rule is a query, not a judgement.

### What DECIDE should output

Slice planning belongs in DECIDE, not BUILD, because it is a planning decision that affects the estimate. Stage E should produce:

- A slice plan **at agent granularity**, not inherited human phases
- The seams between slices, so the contract keeper has work to do before anyone starts
- An expected file count per slice (target 15, cap 30, §8b); a slice expected to pass 15 is split now
- A predicted escalation rate per slice, from `slice-fit`'s axes — slices that fail on verifiability or failure-visibility will escalate more
- A starting agent count, to be adjusted against observed escalation rate

Hard bounds that still apply: the harness caps sub-agent depth at 2 and bounds width by budget with platform concurrency 20 as the hard stop (doc 51), so a slice owner running `auto-pr` (which itself fans out) must be a **separate run**, not a nested sub-agent.

## 4. The three roles

| Role | Does | Never does |
|---|---|---|
| **Slice owner** (N) | Runs the reuse scan first (doc 48 §1), then implements one slice end-to-end, as the `implementer` agent on Sonnet 5.5, or `implementer-complex` on Opus 5.5 when a doc 48 §2 trigger holds, in its own worktree with `tdd-loop`, `ci-speed-run`, `backend-quality`/`frontend-quality`, then `codeowners-split-prs` + `ship-it` (doc 38), inside the loop budget of doc 46 (§8d). `auto-pr` is a separate run outside the harness, never a slice owner | Touch another slice; edit a contract |
| **Contract keeper** | Owns any interface two or more slices share. Defines the seam before work starts; adjudicates change requests during | Implement a slice |
| **Integrator** | Serialises merges; hunts semantic conflict | Fix what it finds; merge to the default branch |

**Why the last two exist:** worktrees give *file* isolation, not *semantic* isolation. Two agents can produce the same abstraction under different names, opposite error handling for the same failure, or two migrations on one collection — and all of it compiles, lints and passes tests. Git will not tell you.

**Merges are serialised.** Merge one, rebase the next onto the result, review, repeat. Simultaneous merges compound conflicts and destroy the attribution you need when something breaks.

## 5. Apollo rules that constrain BUILD

These are not style preferences. They will reject a PR or break a deploy.

- **Migrations ship alone.** A PR mixing an added migration with anything else is rejected by DB Migration Review. Plan the split before writing, not at CI.
- **Sensitive files need the owning team's Slack approval**, enforced by policy-bot. **No agent can clear this.** If a slice touches one, that is a human gate inside BUILD, and the slice should be scoped to make it as small as possible.
- **Draft PRs only, no auto-merge**, until a track record exists.
- **Pack boundaries** — new code belongs in a pack, and anything crossing packs needs a public interface, not a reach-through.
- `# typed: strict` on new Ruby files; regenerate Sorbet types after model or gem changes.
- **Query plans**: `IXSCAN` not `COLLSCAN` on anything touching a significant collection. Verify, do not assume.
- **Never add `Tomb.log`** to new code, even when copying from code that has one.
- Specs: `SKIP_COVERAGE=1 bin/rspec`, `spec_helper` not `rails_helper`, FactoryBot, and beware that Mongo indexes are not created on every run.

## 6. The deployment surface — what was missing

The brief said "frontend, backend, **devops**." There was no devops anywhere: no surface, no reviewer, no step. This is that.

Five deliverables, none of them optional, all produced during BUILD rather than after:

### 6.1 Rollout plan

A named feature flag with an owner and an expiry. Apollo's flags live in `config/feature_flags/*.yml` and carry `expires_at` — a flag without an expiry becomes permanent dead config, which is why the field exists.

The plan states: flag name, ramp steps, what is measured at each step to decide whether to continue, and **the kill switch** — what turns it off, how fast, and whether turning it off is actually safe mid-operation. For anything with external side effects, "off" is not the same as "undone."

### 6.2 Migration sequencing

Which migration runs when, what cannot run concurrently, and whether the change is backwards-compatible during the window when old and new code both exist. A reindex on a live index is a separate plan with its own timing, not a line item.

### 6.3 Feature-specific monitoring

Not generic APM. **What does broken look like for this specific thing?** Generic dashboards will show a healthy service while a sync silently stops removing people.

Each new failure mode gets a detectable signal: a queue that stops draining, a success rate that drops, an external API returning a new error class, a job that stops running at all. Absence of activity is often the real failure and is the hardest to alert on.

### 6.4 Runbook

What the on-call engineer does when it breaks. First diagnostic, most likely cause, safe mitigation, who owns it, and what *not* to do — the last being the most valuable and the most often omitted.

### 6.5 Capacity and cost

New queries and their index coverage. New workers and which queue they land on. New external API quota — for the pilot that is concretely 100k requests/day and 300/minute on the Google project, shared across everything using it.

## 7. BUILD hands off to the on-call harness

This is the useful part, and it connects two systems that already exist separately.

There is already an on-call autopilot that consumes `oncall-config.yml`. **A feature is not done when it merges; it is done when on-call can handle it.** So BUILD's deployment deliverables are inputs to that system, not documentation:

| BUILD produces | On-call harness consumes |
|---|---|
| Alert definitions per failure mode | The signals it triages |
| Runbook | The first action it drafts |
| Ownership entry | Who it routes to |
| Flag name and kill switch | The mitigation it can propose |

That closes a real loop: the thing that builds a feature registers it with the thing that keeps it alive. Today a new feature arrives at on-call as a surprise.

### And the loop runs both ways

The handoff above is BUILD → on-call. The reverse is more valuable and costs nothing extra.

**The domain-owner agents built for a feature are the best on-call resource that feature will ever have.** `ads-backend` holds the enforcement points, the platform quirks, the rejected approaches and the decision log. When something breaks at 3am, that is precisely the context the triage worker needs and does not have.

So on-call triage should **consult the domain owner** for the affected surface, the same way a human on-call would ping the team that built it. The routing already exists — `surfaces:` and `initiative:` in agent frontmatter map an alert's affected area to its domain owner.

Concretely: `oncall-config.yml` gains a surface-to-domain-owner mapping, and triage reads the domain agent's knowledge file before drafting a first action. A feature that has been through this harness arrives at on-call with its own expert attached.

**Keeping it current is a BUILD obligation, not a one-time registration.** Every rollout, every new failure mode, every kill-switch change updates the config. A stale `oncall-config.yml` is worse than none, because it routes confidently to the wrong place.

## 8. Gates

Splitting G4, on the same principle as G0/G1a/G1b — cheap rejection first, and separate questions judged separately.

| Gate | Asks |
|---|---|
| **G4a — diff** | Is the code acceptable? Findings from adversarial review, deterministic checks green, a reuse table (doc 48 §1) with no duplicated candidate and no hand-built UI where Fabric fits (§1b), and every failing check and review comment read and classified (§1c) |
| **G4b — rollout readiness** | Is there a flag with an owner and an expiry, a working kill switch, an alert per failure mode, a runbook, and an ownership entry? |

G4b is mostly a checklist, which means it is mostly deterministic — the cheapest kind of gate. And it is the one that prevents the common failure where a well-reviewed feature ships with no way to turn it off.

## 8b. Pull-request hygiene (added 2026-09-21 after a 114-file frontend PR on Ads M1)

- **One PR, one purpose.** A slice is a PR. If a PR mixes a refactor with a feature, the integrator
  splits it before review; the split rule from the pilot (FE and BE in separate PRs, cross-linked) stays.
- **Small PRs: 15 files is the target, 30 is the cap.** Count every changed file, tests included
  (`gh pr diff <n> --name-only | wc -l`). The gate excludes lockfiles (`Gemfile.lock`,
  `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`), schema dumps (`schema.rb`, `structure.sql`), and
  files under `fixtures/`, `recorded_fixtures/`, or `__snapshots__/`. Keep each PR under ~1,500 changed lines
  too. The slice plan (§3, Stage E) gives each slice its expected file count, and a slice expected to
  pass 15 files is re-sliced before anyone builds it. Before a PR leaves draft the count is a check row:
  over 30 is `failed` and the PR is split. `scripts/pr-ready.py` enforces the cap before human handoff.
  The only exception is `size_waiver: {reason: <15+ characters>, approver: <named person>}` in the
  current-head review record (for example, a mechanical rename that cannot be split).
- **New product surfaces merge dark.** A new product (a new pack, package or route) lands behind a
  feature flag (Flipper on the backend, the promoted-product gate on the frontend) so every PR can merge
  to master without affecting existing products. The flag name and its cleanup ticket are in the slice
  contract. Features inside an existing product use the product's existing flag or none, by the slice
  owner's judgment, stated in the PR.
- **Reviewers see a sequence, not a pile.** Stacked PRs are fine; each carries its own description,
  tests and preview link. The build snapshot lists every PR with its purpose in one line.

## 8c. Stamp every harness PR (added 2026-10-06, doc 43 §2.2)

Every PR the harness opens or edits carries one line in its body, so the escape scan can find review
findings on it later:

```
Harness run: <initiative>/<run-id>
```

1. When creating the PR, put the line at the end of the body (`gh pr create --body-file`, or the
   body the PR-description skill drafts).
2. When editing an existing PR body (`gh pr edit`), keep the line; add it if it is missing.
3. Verify it landed: `gh pr view <n> --json body --jq .body | grep -F "Harness run: <initiative>/<run-id>"`.
   No match means the PR is not stamped: fix the body and check again before reporting the slice.
4. Record the PR number in the build snapshot's Artifacts written.

## 8d. Loop budget (added 2026-10-09, doc 46)

Every slice owner and every fix loop after review follows doc 46. In short:

1. Specs run in the already-running app container (`docker exec`), never a fresh container per run;
   indexes are rebuilt only when an index definition changed. Commands come from the target repo's
   `CLAUDE.md` and skills (leadgenie: `SKIP_COVERAGE=1 bin/rspec`, `RSPEC_CREATE_MONGO_INDEXES=1` only
   after an index change, `ci-speed-run` for affected specs).
2. While iterating, only affected specs run; the full relevant suite runs once before the commit that
   goes to review.
3. Mutation checks run once, at the end, on behaviour changes only, at most 10 mutants, each against its
   own spec file. After a fix, only mutants on code the fix changed are re-run.
4. Cross-family review is two passes at most: the full change, then the delta. Blockers after pass 2
   go to the human with options; no pass 3 unless a human asks.
5. The build snapshot carries the loop report line (doc 46 §6) with minutes for build, tests,
   mutation, review and fix loops.

## 8e. CI and git rules a past Ads M1 build paid for

- **Preflight every new artifact type against its hygiene spec before pushing** (a new queue, cron or
  index each failed one on first push): the queue registered where the repo requires (in leadgenie: both `values.yaml` and
  `cluster-owners.yaml`), a cron command in the repo's form (leadgenie: `<Worker>.perform_async`), no stored defaults, no boolean or enum leading index key without a partial filter.
- **Merge the base branch before calling a failure a flake.** CI may check out the PR head, not the merge
  ref, so a stale branch fails on specs the base already fixed and reruns cannot help; it is a flake only if
  the base fails too.
- **Know which jobs can be rerun.** A rerun that replays an empty test-split queue reports nothing; push a
  commit instead (in leadgenie: Frontend Tests; `--failed` is fine for Backend Tests). Exit code 124 after "0 failures" is the
  step timeout, not a failing spec.
- **Gate every push of a split branch on ancestry** (`git merge-base --is-ancestor <base> HEAD || exit 1`),
  run merges with the merge hook disabled when it is known to fail (leadgenie: `LEFTHOOK=0`), never pipe
  merge output through a filter that hides its exit code, and check `git diff --cached --stat`
  before each split commit; a masked merge failure once pushed a frontend branch without its backend.

## 8f. Optional: a px0 review link per PR (added 2026-10-08)

px0 (<https://px0.ai>) is a local, browser-based code review tool. It is **optional for every role, including engineers**; nothing in the gate or the build requires it. It is **opt-in**: onboarding only
offers it for personas that review code (doc 39), with Security sign-off before first use because it
is an external tool not yet in Apollo's approved tool directory. The install itself is pinned (Homebrew
if available, else fetch-and-verify against `framework/models/px0-pin.yml`); the unpinned
`curl ... | sh` form is never used. After a slice PR is opened and stamped (§8c), give the person a
viewer for it. Do not share the URL or hand the PR to a human until `scripts/pr-ready.py` passes for the
current head; preparing the local viewer may happen earlier:

1. Skip, and say so in one line, when px0 is absent, in no-repo mode, or on a cloud host (no
   localhost).

2. Reuse a px0 that is already serving this PR (its pid and url are in the build snapshot and the
   process is still alive). Otherwise start one, in the background, from the product repo root:

   ```bash
   mkdir -p "${TMPDIR:-/tmp}/harness-px0"
   log="${TMPDIR:-/tmp}/harness-px0/pr-<n>.log"
   nohup px0 -no-open -no-telemetry -no-update -port 0 -y <pr-url> > "$log" 2>&1 &
   echo $!
   ```

   px0 checks the PR head out into its **own temporary git worktree**, so the person's working tree
   is never touched and every PR is reviewed in isolation.

3. Wait up to 60 seconds for the `url:` line in the log (`grep -m1 'url:' "$log"`). No line: report
   the last 5 log lines and go on; a review link is help, not a gate.

4. After the current-head review gate passes, report one line per PR:
   `PR #<n> <title> (<files> files) · review in px0: <url>`. Record the pid,
   url and worktree path in the build snapshot's Artifacts written. The url is local to this laptop,
   so it never goes on a Notion page or in a PR body.

5. Stop a px0 with `kill -INT <pid>` (the same as Ctrl-C). px0 removes its worktree on that signal;
   any other way of stopping it leaves the worktree behind. When that happens, read the worktree
   path from the build snapshot's Artifacts written, confirm no uncommitted work is in it with
   `git -C <path> status --short`, then remove it with `git worktree remove <path>` (add `--force`
   only after confirming the status is clean) and finish with `git worktree prune` to drop the
   administrative entry. Stop them when the person says they are done reviewing, or when the PR
   merges or closes.

## 8g. One combined draft PR for manual testing (added 2026-10-08)

Small slice PRs are easy to review but cannot be tested together. Once every slice PR of the
feature is open, also open one **combined PR** that is only for manual testing on a preview
environment. It is never merged.

1. Rebuild `<feature-branch>-combined` from the current default branch and the current slice heads.
   Fetch them, record each slice head SHA, reset the combined branch to the default branch, then merge
   each recorded SHA in dependency order (the order the integrator gave):

   ```bash
   git fetch origin <default-branch> <slice-branch-1> <slice-branch-2>
   slice_1=$(git rev-parse origin/<slice-branch-1>)
   slice_2=$(git rev-parse origin/<slice-branch-2>)
   git switch -C <feature-branch>-combined origin/<default-branch>
   git merge --no-edit "$slice_1"
   git merge --no-edit "$slice_2"
   ```

   A merge conflict here is a
   seam problem: route it to the contract keeper, do not resolve it by hand in the combined branch.

2. Push it and open it as a **draft** with the `Need_Preview_Env` label, which deploys a preview
   environment in staging:

   ```bash
   gh pr create --draft --label Need_Preview_Env --base <default-branch> \
     --head <feature-branch>-combined --title "[Do not merge] <feature>: combined for manual testing" \
     --body-file <body>
   ```

   The body says in its first line that this PR is for manual testing only and must not be merged,
   lists every slice PR with its purpose in one line, and ends with the stamp line (§8c).

3. Verify the label landed: `gh pr view <n> --json labels,isDraft`. A missing label or a non-draft
   state is a `failed` check row.

4. When a slice PR changes, repeat step 1 from the default branch. Never merge a rewritten slice into
   the old combined history. Before pushing, compare every recorded SHA with the published PR head
   (`gh pr view <slice-pr> --json headRefOid --jq .headRefOid`) and abort on any mismatch. After pushing,
   verify the combined remote is the local rebuilt head (`git rev-parse HEAD` equals
   `git ls-remote origin refs/heads/<feature-branch>-combined | cut -f1`) before posting the preview.
   The combined PR is exempt from the file cap in §8b because nobody reviews it as a diff; review
   happens on the slices.

5. Report the combined PR url and, once the preview is up, its preview url. Stage G (doc 21) tests
   against that preview. Close the combined PR, and delete its branch, when the last slice merges.
Use the advisory scripts in doc 52 at the point where their answer changes the report:

- Before reporting CI, run `scripts/ci-doctor.py --pr <number>`. Report its classification and one next
  action per failing or pending check. Do not call CI green while it exits 1 or unknown while it exits 2.
- Before reviewing a stack, run `scripts/stack-sync.py --tip <top-branch>`. Sync bottom-up before review;
  `--apply` may merge locally, but the script never pushes.
- Before calling a UI PR ready, run `scripts/preview-status.py --pr <number>`. A successful deployment of
  an older sha does not pass.
- Before sending any build status report to a human, save it and run
  `scripts/verify-claims.py <report.md>`. Add evidence beside unsupported completion claims.

## 9. What BUILD must not do

- **Not merge to the default branch.** Draft PRs; a human merges. The combined PR (§8g) is never merged by anyone.
- **Not deploy.** Shipping is a human act with a human owner.
- **Not clear a sensitive-file approval.** That gate is a person, by design.
- **Not mix a migration with anything else.**
- **Not invent a contract.** A slice owner that needs a seam changed *requests* it; the keeper decides.
- **Not fan out beyond genuine independence.** More agents on coupled work produces more conflict, not more throughput.
- **Not skip the deployment deliverables because the code is done.** That is exactly when they get skipped.

## 10. Open questions

| # | Question | Owner | Blocking |
|---|---|---|---|
| Q-B1 | Slice owners must be separate runs, not nested sub-agents, because `auto-pr` itself fans out and would exceed depth 3. Needs Pantheon descriptors | AI Tooling | Fan-out beyond one slice |
| Q-B2 | Who writes the runbook — the slice owner who has the context, or a devops specialist who knows what on-call needs? Probably the owner drafts and the on-call config owner reviews, but that is asserted | author + SRE | §6.4 |
| Q-B3 | The `oncall-config.yml` handoff format is not specified. What exactly does a new feature register, and is there an existing schema to extend? | author + SRE | §7 |
| Q-B4 | Nothing in BUILD has been exercised. The contract keeper and integrator are written and unused; the deployment surface is new. First real use should be one slice, not a fan-out | author | Confidence in any of this |
| Q-B5 | Does the integrator run before or after adversarial review? Before means reviewers see the merged result; after means they review slices that may not compose. Probably before, but it doubles the review surface if the integrator finds problems | author | Ordering |
