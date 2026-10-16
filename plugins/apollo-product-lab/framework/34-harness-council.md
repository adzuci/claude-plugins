# 34 — The council: every change reviewed as a team, on different model families, in parallel

> Why: on Ads M1 the product, UX, architecture, QA and research thinking arrived serially through one
> agent over 30+ hours. Decisions were good when a lens happened to be applied and wrong when it was
> not (a Google-shaped ERD passed two model reviews). The council makes the lenses structural: any
> change above a threshold is read by every role at once, each on a model family chosen for
> independence, each writing a snapshot, with one synthesizer and one human.

## 1. When it runs

- A new PRD or a PRD change (Stage C output)
- A new or changed design prototype (Stage D output)
- An ERD or architecture plan before its first human review (Stage E)
- A slice plan before BUILD; a PR before it leaves draft
- Any decision the router marks `pending human choice`

Below the threshold, a change with demonstrated low risk under doc 43 §6 (tests show the output is unchanged and no trigger applies), the router skips the council and says so. File count is not the test: a one-file index or behaviour change is medium.

## 2. Lenses and who plays them

| Lens | Agent (existing, reused) | Registry role | Reads | Writes |
|---|---|---|---|---|
| Product | `product-reviewer` | `decide.specify.analyst` | PRD, competitor evidence, metrics | gaps, options memo |
| Competitive | `product-reviewer` (competitor mode) on the Glean family + Sol second opinion | `find.research.competitive` | web + internal record: how the two or three named competitors solve this; our PRD or design | a comparison table (competitor vs us, per capability), pros and cons of each approach, options with a recommendation, and an explicit **go-ahead question** for the human. Runs on every prd and design kind, and on erd when the model shape is product-visible |
| AI opportunity | `product-reviewer` (AI-opportunity mode) on Opus, market examples from Glean, Sol second opinion | `find.opportunity.ai` | the PRD or design, the roadmap, the initiative's `domain/*.md` and data model, `knowledge/ai-opportunities.md` | the opportunity table of doc 42 (journey step, friction, assist type, data, value evidence, compliance touch, cost tier, roadmap fit, options) and one **now / next version / never** question per row. Runs with the competitive lens on prd and design, and on product-visible erd |
| Platform (conditional) | `product-reviewer` (platform mode) on Opus, internal record from Glean, Sol second opinion | `find.opportunity.platform` | the PRD, design or ERD, `surface-owners.yml`, the product repo for sibling capabilities, `knowledge/platform-opportunities.md` | the platform table of doc 47 (feature parity, shared flow, shared backend; where it exists with owning team, how it differs, proposed shape, cost now vs later, roadmap fit, options) and one **platformize now / do locally and record / never** question per row. Runs on prd and design only when the intake's quick sibling check found a sibling, on erd and plan for shared-backend rows; otherwise a recorded skip |
| Peer design | `product-reviewer` (peer-design mode) on Opus | `decide.design.peer` | the design artifact (or, on prd, the journey the PRD implies), the initiative's `domain/frontend.md`, the Fabric patterns already used for the same job | a designer's critique, not a constraint check: hierarchy and flow, information architecture, one alternative per weak screen with its trade-off, consistency with how Apollo already does the same job, and the states a peer would ask for. Runs on prd and design kinds; it never rules on constraint-register rows (that is the UX / Design lens) |
| UX research | `product-reviewer` (UX-research mode) with the doc 16 connectors | `decide.research.ux-evidence` | every user claim in the PRD or design (who the user is, what they struggle with, what they will do), the initiative's FIND snapshot (doc 16) | one row per claim: the evidence that supports or contradicts it (query, cohort, ticket, quote, survey answer; source, date, tier) or `no evidence`. Reuses the FIND snapshot first and queries a source only for a claim FIND did not cover; it never re-runs discovery. Runs on prd and design kinds |
| Engineering feasibility | the initiative's `<x>-architect`, `<x>-backend` and `<x>-frontend` owners, else `backend-reviewer` / `frontend-reviewer` with `explore-leadgenie` | `decide.feasibility.engineering` | the PRD or design, the codebase, `platform-rules.md`, `apollo-infra-patterns.md` | per requirement or screen: the existing models, APIs and components that can carry it (path), a size (S / M / L with the reason), what it needs that does not exist, and what to cut or stage to a later milestone, with one recommendation. Runs on prd and design kinds |
| UX / Design | initiative `<x>-frontend` with the prototype-first rule | `decide.design.checker` | the branch's `/storyboard` (all pages), `design-diff` inventory, required states, constrained copy | pass/fail per constraint, the five-bucket gap list |
| Architecture | initiative `<x>-architect` | `decide.architect.reviewer` | ERD, decision log | doc 17 §6.1 roadmap lens, scale posture |
| Infra (be-platform) | `infra-lens` (gpt-6-astra via shunt, with repo tools) | `review.infra` | ERD and its Load model (doc 17 §6.2), `apollo-infra-patterns.md`, `platform-rules.md`; for pr, the diff | one row per IP entry and per Load model row, `checked` / `failed` / `unverified`; a missing Load model is `failed`, and so is a hook row without the host-path numbers of doc 17 §6.2 (IP18). When a metrics connector (Grafana) is reachable in the session, the host peak and the shared resource's peak are queried, by the lens or by the main session into its brief; otherwise those cells are `unverified` and the memo opens a pre-merge human check naming the metrics. Runs on every erd, plan and pr kind that touches backend code |
| Backend | `backend-reviewer` + `db-perf` | `review.code.generic` | diff, models, indexes | findings |
| Frontend | `frontend-reviewer` | `review.code.generic` | diff, tests, i18n | findings |
| QA | `framework-qa-reviewer` | `verify.qa` | acceptance criteria, state list | derived tests, negative test per invariant |
| Research | `explore-leadgenie` + Glean | `find.research.codebase`, `corroborate.internal` | codebase, internal record | "does this exist / contradict our record" |
| Compliance | none: **human** | `review.compliance.judgment` | constraint register | verdicts, never by an agent |
| Adversary | `council-adversary` (Astra via shunt) for erd/plan; `/codex:adversarial-review` (Codex plugin, installed) for pr | `review.adversary` | everything above | the refutation, copied into `council.<slug>.adversary.md` |

Each lens writes `runs/<run>/council.<slug>.<lens>.md` (doc 33 template, `stage: council.<slug>`).

The **competitive lens is not optional** for a new product, and for a change to an existing one when users will see different behaviour (then as the one-page combined form in §2a): the memo carries a
"How competitors do this vs what we propose" table and the human is asked which direction to take before
any build stage fires. A build that starts without that answer is a router defect. The **AI opportunity lens**
(doc 42) runs beside it on the same kinds: the memo asks, per proposed assist, now / next version / never;
an accepted row becomes a requirement, a deferred or rejected one is written to `knowledge/ai-opportunities.md`,
and a slice that builds a `proposed` row is the same router defect. The **platform lens** (doc 47) is
conditional: it runs when the change adds or changes a capability, flow or backend service and the
intake's quick sibling check finds one elsewhere in Apollo, and is otherwise a recorded skip; a
cross-product slice built from a `proposed` row, or a cross-team row without the owning team's recorded
answer (doc 43 §5), is the same router defect.

The **pr kind is the existing `code-review` supervisor** (backend, frontend, security, db-perf sub-agents and
`pr-tech-lead-synthesizer`) plus the Codex adversary and `/apollo-eng:mongo-pr-guard`; do not redispatch those
lenses by hand. Which repo skill or marketplace plugin each lens may call is fixed in
[38-skill-reuse-map.md](./38-skill-reuse-map.md); a lens never calls a skill that has no **use** or **wrap** row there.

### 2a. Lens selection by what the change affects, and the medium/high default (doc 43)

- **Pick lenses by what the change affects**, not by the artifact kind alone and not by whether users
  see it: backend code adds the backend lens; a query, schema or index adds db-perf; a surface owned by
  a team other than the author's (`surface-owners.yml`, and `apollo-dev-teams.yml` sensitive files
  matched with `ApolloDevTeam.team_to_sensitive_files_hash`) adds an owning-team lens loaded with that
  team's rules from `platform-rules.md`. Ownership is detected at intake and again on the real diff.
- **Enhancements to an existing product** take product and UX lenses only when users will see
  different behaviour, one combined competitor and AI opportunity page (one page at most) only then,
  and research only when the area has no prior research. The full competitive and AI opportunity
  lenses above stay required for a new product.
- **Every design change gets Astra xhigh before acceptance** (doc 17 §6.3), whatever its size: a new
  ERD, a change to its design content, an architecture decision, or a PR change that alters the design.
  The memo names the `design_sha` reviewed, the served model and effort, and whether the review is
  independent of the author's recorded family (an OpenAI-authored design also gets a Fable reading).
  With no Astra review on record for the current `design_sha`, the memo cannot recommend acceptance; a
  same-family fallback needs a named human waiver.
- **Medium and high work** (doc 43 §6) get one consolidated cross-family review of the design artifact
  and one of the PR diff, before human review: one review per artifact, not one per lens. It reuses the
  adversary already in the council: for the design, Astra (gpt-6-astra, extra-high effort) through Codex
  or the `council-adversary` through shunt; for the PR, the existing `/codex:adversarial-review`.
  Independence follows §3 below. Record tokens and minutes in the ledger. It is advisory input to the
  human gate and never an approval. If no second family is reachable, the gate record says so.
- **Gate rows** in every lens and memo are `checked`, `failed`, `unverified` or `not applicable`.
  Models agreeing is not approval.

### 2b. Cross-role review matrix (2026-10-12)

Every artifact is read by the roles that have to live with it, not only by its author's peers. The rows
are the lenses each kind adds by default; §2a's change-driven lenses, the adversary and the size rules
still apply.

| Artifact (kind) | Reviewed by | Lenses | Peer of the author |
|---|---|---|---|
| PRD (`prd`) | design, engineering feasibility, UX research | Peer design (on the journey the PRD implies), Engineering feasibility, UX research; plus Product, Competitive, AI opportunity and, when triggered, Platform | Product lens (`product-reviewer`) is the peer PM |
| Design (`design`) | product, peer design, UX research, engineering feasibility | Product, Peer design, UX research, Engineering feasibility; plus UX / Design (constraints), Competitive, AI opportunity, QA and, when triggered, Platform | Peer design lens |
| ERD / plan (`erd`, `plan`) | product, design, QA | Product (does the model carry every requirement and acceptance criterion), UX / Design (can every required state and copy rule be represented), QA (is each invariant testable); plus Architecture, Infra, Backend, db-perf, Research | Architecture lens and the backend reviewers are the peer engineers |
| PR (`pr`) | product, design, QA | Product (built to the PRD), UX / Design (states and copy as designed; frontend diffs only), QA (`qa-steps-for-eng` rows); plus the `code-review` supervisor | `backend-reviewer` / `frontend-reviewer` (via `code-review`) are the peer engineers |

**Peer lenses, decided on value.** The peer PM is the Product lens and the peer engineers are the
architecture lens and the `backend-reviewer` / `frontend-reviewer` agents; adding separate peer PM or peer
engineering lenses would re-read the same artifact with the same questions. Design had no peer: the UX /
Design lens checks a design against required states and the constraint register, it does not critique it.
The peer design lens fills that gap.

**Pre-work briefs.** Before a role starts its artifact, the council skill (or intake, for the first
stage) hands it a short brief from the roles that will review it: what each of them needs from this
artifact, at most five lines per role, taken from their lens tables above and the initiative's domain files.

| Starting | Brief from | What the brief says |
|---|---|---|
| PRD | design, engineering, UX research | design: the journey and the states the design must cover; engineering: the existing models and APIs in this area and the requirements that are expensive; UX research: which user claims already have evidence (FIND snapshot) and which do not |
| Design | product, engineering, UX research | product: the requirements and acceptance criteria the design must satisfy; engineering: the components and data that exist and what is costly to build; UX research: the evidence on the user's task |
| ERD / plan | product, design, QA | product: the requirements and their priority; design: the states and copy the model must carry; QA: the invariants that need a negative test |
| PR | product, design, QA | product: the acceptance criteria this slice closes; design: the states and copy in this slice; QA: the test rows this slice must pass |

**Who runs the matrix rows on erd, plan and pr.** These are not code reviews by `product-reviewer` and not
`framework-qa-reviewer` (which reviews the framework):

- **Product on erd / plan**: `product-reviewer` maps each PRD requirement and acceptance criterion to the
  model, field or plan step that carries it, and lists the ones nothing carries. **On pr**: the same agent
  reads the PRD's acceptance criteria against the PR description and the QA rows, never the code, and
  lists criteria the slice claims to close without a test row.
- **Design on erd / plan**: the initiative's `<x>-frontend` owner checks that every required state and
  copy rule can be represented by the model. **On pr** (frontend diffs only): the same owner runs
  `design-diff` against the prototype.
- **QA on erd / plan**: the product QA workflow (`feature-qa-wizard`, run by the main session) derives a
  negative test per invariant and flags invariants the model cannot test. **On pr**: `qa-steps-for-eng`.

The brief is a section of the starting stage's input snapshot, not a separate page. It is written after
the previous artifact's `decide`, from the decided version, so a requirement the council cut is not in it. **Size rules still
apply** (§1, doc 40, doc 43 §6): a change the router skips for demonstrated low risk gets no council and
no matrix lenses (file count is not the test: a one-file index or behaviour change is medium);
an enhancement users will not see skips the product and design rows of the matrix with the reason recorded.

## 3. Independence, enforced at dispatch

Adversary route order (2026-09-22): OpenAI through shunt; the Codex plugin; **the Glean family** by
`glean_default.chat` with the brief and the artifact text (the main session saves the reply as the lens
snapshot, `produced_by: glean/glean-assistant`); then a same-family Anthropic fallback, tagged. Glean is a
route for prd and design only. For erd, plan and pr it is **not** an adversary: on the Ads data-model
review it found five of Astra's ten code-grounded defects, under-derived three, and raised two objections
that do not hold, because it sees only the excerpts the operator pastes and reads the repo through its
index at `master`. There the same-family Anthropic fallback is the adversary, tagged, and a Glean reply may
be appended as a labelled "second reading" that never counts as the lens. Its independence is `unknown` until the
registry's `glean.assistant_model` is confirmed from the Model Hub (it may be GPT-5, Gemini or Claude Sonnet),
and `unknown` never counts as independent; it still adds a second reading. Evidence:
`reviews/glean-adversary-probe-2026-09-22.md`.

The council skill reads `models/model-registry.yml` and assigns families so that:

- the adversary's family differs from the author's;
- the synthesizer's family differs from the majority of lens families when reachable;
- where independence cannot be achieved (only one family reachable), every affected snapshot is tagged
  `independence: same-family` and the human is told in the memo. The harness never blesses its own work
  silently.
- the author family is the *artifact's* author family, not the council caller's; unknown or mixed
  authorship is `independence: unknown`. The model recorded is the one served, not the one requested.
- one minimum, everywhere: reviewer family ≠ author family for the adversary; other lenses may share a
  family if they differ in model, and say so. A synthesizer on a second family is better synthesis,
  not a second independent observation (a "third family" is aspirational).

## 4. Rounds and efficiency

- **One dispatch, all lenses in parallel.** Sub-agents cannot talk to each other; they read the same
  input snapshot and write their own.
- **Synthesizer** (`pr-tech-lead-synthesizer` pattern) reads only the lens snapshots, not the
  conversation, and writes `council.<slug>.memo.md`: agreements, disagreements with both sides quoted,
  options with a recommendation, human gates to open.
- **At most two rounds.** Round two exists only to answer a synthesizer question with evidence, or to run
  cross-family pass 2 on the delta (doc 46 §4); a third
  round is an escalation to the human.
- **Hand-off depth stays at two** (doc 12): lens → synthesizer → human.
- **Cross-family review is two passes per artifact** (doc 46 §4): pass 1 on the full change, pass 2 on
  the delta only. The cross-family lenses of one round (the adversary and, on backend code, the infra
  lens) run in parallel and together are one pass; in pass 2 each reads only the delta. If pass 2 still has blockers, stop and give the human options; no pass 3 unless a
  human explicitly asks, and the snapshot records who.
- **Review prompts carry the diff, the question and file pointers** (doc 46 §5): no pasted file bodies,
  target 15,000 characters or fewer, prompt size and tokens logged in the ledger for each pass.
  Excerpt-only routes (Glean) are the exception and are tagged `excerpt-only`.

## 5. Entry points by role

| You are | Run | You get |
|---|---|---|
| Product manager | `/harness-council <initiative> prd "<what changed>"` | gap list, options memo, competitor evidence, acceptance criteria to sign |
| UX designer | `/harness-council <initiative> design "<prototype branch>"` | constraint pass/fail, state coverage, the port list the engineer will build from |
| Engineer | `/harness-council <initiative> erd\|plan\|pr "<ref>"` | roadmap-lens and scale-posture verdicts, code findings, negative tests to add |
| QA | `/harness-council <initiative> verify "<preview url>"` | derived test plan, a negative test per invariant, bug records routed to the producing stage |

The memo is the deliverable; the human chooses from its options. Nothing in the council approves anything.
