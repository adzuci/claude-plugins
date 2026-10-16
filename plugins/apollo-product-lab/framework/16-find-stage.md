# 16 — FIND, in depth

> Deep dive on the first box of [10-harness-overview](./10-harness-overview.md). Stages A (Audit) and B (Research).
> **Status: draft for review. Nothing binding.**

## 1. FIND answers two questions

| Question | Stage | Needs |
|---|---|---|
| Is what we have written **internally consistent and complete**? | A — Audit | Artifacts to exist |
| Is what we believe **actually true**? | B — Research | Evidence to exist |

Everything below follows from those being different questions with different failure modes. A is cheap, deterministic, and catches contradiction. B is expensive, evidence-bound, and catches *being wrong about the world* — which A structurally cannot see, because a set of documents can agree perfectly and all be wrong together.

## 2. The hole: FIND assumed artifacts exist

Stage A is declared "always runs." On a genuinely new feature there is nothing to cross-check, so as written it runs and finds nothing — which reads as a clean bill of health.

**Two modes, and the order inverts between them.**

### Brownfield — artifacts exist

`A → B`. Audit first, because it is near-free and its findings tell Research what to investigate. The reference instance worked this way: the audit surfaced unpriced compliance requirements, and Research then answered whether the underlying infrastructure existed. Audit generated the question; Research answered it.

### Greenfield — little or nothing written

`B → (C) → A`. Research does the heavy lifting; Stage A's first meaningful run is against **what Specify produced**, not against a pre-existing set.

Stage A still has a job at the very start, but a different one: **artifact-set completeness** rather than content consistency. Not "do these documents agree" but "which documents that should exist, don't." For a high-compliance archetype with no constraint register, that absence *is* the first finding, and it is a good one.

That also gives the harness a useful recursive property: Stage A becomes the check on the harness's own output.

## 3. What Stage A covers

Deterministic phases first, because they are near-free and produced the highest-consequence findings on the one real run:

| Phase | Checks | Cost |
|---|---|---|
| 1 Resolve | Fetch everything; **record unreachable artifacts as findings** | ~0 |
| 2 Schema | Required sections present and non-empty, per artifact kind | ~0 |
| 2.5 Self-consistency | One document contradicting **itself** — pairwise edges cannot see this | ~0 |
| 3 Freshness | Lapsed dates against open status; recency from config `as_of`, never from the fetch | ~0 |
| 5 Coverage | Every gating constraint traced to estimated work; every decision to an owner | ~0 |
| 4 Contradiction | Pairwise, **declared edges only**, two-quote rule | ~78k tokens/pair |

**What it cannot do:** detect a defect no artifact contradicts. A plan that is coherent and wrong passes cleanly. That is the whole reason Stage B and the human gates exist.

## 4. Stage B: four evidence types, not three

The original decomposition had codebase-reality, external-source and precedent. **None of them answers what users actually need or do**, which for a product harness is a strange omission.

| Specialist | Answers | Verification handle |
|---|---|---|
| Codebase reality | Do we already have this? What would it really cost? | `file:line` and real field names. "Not found" means searched |
| **User evidence** | What do users do today, where do they struggle, what do they ask for? | Every claim traced to a query, a cohort, a ticket, or a replay ID |
| External / market | What does the platform, vendor or competitor actually say? | Primary sources, tiered `[P]`/`[S]`/`[U]`, dated |
| Precedent | How did we solve this before, and what happened? | Links to real PRs, incidents, RCAs |
| **Arbiter** | One answer set, **plus every question it could not answer, each with a named owner** | Unanswered-with-owner is a first-class output |

Codebase reality remains the highest-leverage on brownfield — it swung one estimate from "light" to "wrong." **On greenfield, user evidence is.**

## 5. UX research belongs in two places, and they are different activities

The question was whether UX research sits in FIND or Design. It is both, but they are not the same work, and conflating them is why PRDs get written before anyone checks what users do.

| | **Discovery research** | **Usability validation** |
|---|---|---|
| Stage | **B (FIND)** | **D (Design)** |
| Question | What is the problem, who has it, what do they do today? | Does this specific design work for them? |
| Evidence | Behavioural data, support conversations, churn reasons, existing usage | The design artifact plus a task |
| Feeds | The problem statement and the business case | Option elimination |
| Fails by | Confirming a problem nobody has | Confirming a design nobody can use |

**Discovery must precede Specify.** If user research lands only in Design, it runs *after* the PRD is written, which means the problem statement was never evidence-checked — it was asserted, then decorated. That is the failure this harness exists to catch in documents; putting research downstream reproduces it.

Usability validation genuinely belongs in Design, alongside the constraint-compliance and state-completeness specialists already defined there.

## 6. Evidence sources, and an asymmetry that matters

Checked 2026-09-06; Enterpret updated 2026-10-12.

**Reachable now:**

| Source | Gives |
|---|---|
| **Amplitude** | Behaviour: funnels, retention, cohorts, event segmentation. Plus **session replay** — search by event or cohort, interaction timelines, analytics timelines, and a player |
| **Intercom** | Support conversations, articles, contacts, companies |
| **Jira / Atlassian** | Bug reports, feature requests, incident history |
| **Glean** | Internal docs and Slack — where decisions and complaints actually live |
| **Notion** | PRDs, registers, research write-ups |
| **Enterpret** (Enterpret Wisdom MCP connector) | Aggregated user feedback with taxonomy: `get_graph_schema` for the schema, `search_graph_values` to resolve themes and values, `run_graph_query` for counts and records, `find_user_quote` for validated verbatim quotes |

**Not authenticated:** Gong (call transcripts), Sprig (in-product surveys), Listen Labs (AI interviews), G2 (reviews), Zendesk, Customer.io.

**The asymmetry: we can see what users *did*, not what they *said*.**

Amplitude and replay give behaviour in depth. Verbatim voice of customer comes from Intercom and, since 2026-10-12, Enterpret (aggregated feedback across channels, with `find_user_quote` for validated quotes). Support tickets are a biased sample: they over-represent breakage and under-represent quiet abandonment; Enterpret narrows that bias but in-product surveys (Sprig) remain unauthenticated.

So a discovery-research pass today can reliably establish **friction** (where users stall, drop, retry, rage-click) and can establish **motivation** (why they wanted it, what they'd trade for it) only where users wrote about it in feedback Enterpret aggregates; without that, weakly. It should say so rather than inferring intent from clickstream, which is the characteristic way behavioural-only research goes confidently wrong.

### Buyer voice is not user voice — a correction

An earlier draft called Gong the highest-value unblock for this stage. **That was wrong, and the distinction matters for B2B.**

Gong is revenue intelligence: sales calls, demos, QBRs, churn conversations. It captures the **buyer** — objections, competitive positioning, why deals stall, what procurement asked for. In B2B the buyer and the user are frequently different people with different problems, and a discovery pass built on sales calls will confidently describe an economic buyer's concerns as user needs.

So Gong is genuinely valuable, but **to Stage C, not Stage B**: it feeds the competitive-position and business-case specialists. Routing it into discovery would import exactly the bias discovery exists to avoid.

### Sources ranked by what they actually unlock

| Source | Voice | Feeds | Priority |
|---|---|---|---|
| **Enterpret** | Aggregated user feedback across channels, with taxonomy | Stage B discovery | **Highest.** Purpose-built for this question; reachable since 2026-10-12 |
| **Sprig** | In-product survey plus replay, captured at moment of use | Stage B discovery | **High.** Closest thing to user voice at the point of friction |
| Amplitude + replay | Behaviour | Stage B discovery | Available now |
| Intercom | Support conversations | Stage B, biased toward breakage | Available now |
| **Gong** | **Buyer**, not user | **Stage C** business case and competitive position | High for C, wrong input for B |
| **G2** | Market and competitive perception | **Stage C** competitive position | Medium, for C |
| Zendesk | Support, if it lives there rather than Intercom | Stage B | Only if it holds volume Intercom doesn't |

**Enterpret is now authenticated; Sprig is the next to add.** They answer the question discovery is actually asking. Gong is worth adding next, tagged for Stage C so nobody routes it into the problem statement.

## 7. FIND's output contract

One artifact, `.ai/<initiative>/find-<date>.md`:

1. **Findings table** — every one carrying evidence on both sides, ranked by consequence, adjudicable in under 15 minutes
2. **Problem statement** — with each claim traced to its evidence, and confidence marked where evidence is behavioural-only
3. **Open questions with named owners** — the arbiter's unanswered set. This is the fix for the failure mode where thirty register items sit pending against role lists instead of people
4. **Coverage note** — what was checked and found clean, what was not checked and why, including unreachable artifacts
5. **Dropped candidates** — findings considered and rejected, with the reason, so the false-positive discipline is auditable

## 7.1 Gates: smaller, and the harness asks before it assumes

G1 as a single gate was too coarse. A weak problem statement that clears it poisons every downstream stage, and by the time that shows up the expensive stages have already run.

**Split it, and order it so the cheap rejection comes first:**

| Gate | Asks | Why here |
|---|---|---|
| **G0 — scope** | Is this the right problem to be looking at, and is the artifact set complete? | Before any model spend. Catches "wrong initiative" and "missing constraint register" for free |
| **G1a — problem** | Is the problem statement supported by its evidence, and is friction-vs-motivation marked honestly? | A wrong problem invalidates everything after it, so it is judged on its own |
| **G1b — findings** | Are the individual findings real? Which are false positives? | Separable from the problem question, and it produces the false-positive rate |

### The ask-before-assume rule

**At entry to every stage, the harness may ask a bounded round of clarifying questions, and it should prefer asking to assuming.**

Constraints that keep this from becoming an interrogation:

- **Maximum three questions per stage entry.** More than that means the stage is under-specified and should stop rather than interview.
- **Only decision-relevant questions.** A question whose answer does not change what the stage does is noise. "Should I proceed?" is banned; "is this initiative scoped to Google only, or all three platforms?" is not.
- **Offer a default with each question.** An unanswered question then resolves to a stated default rather than blocking, and the default is recorded so it can be challenged later.
- **Never ask what an artifact already answers.** Ask the artifact first; asking the human something the PRD states is how a harness becomes tiring to use.

This is the counterweight to the habituation problem. Gates ask the human to *approve*, which degrades with repetition. Clarifying questions ask the human to *decide*, which does not degrade the same way, and moves the human's involvement earlier where it is cheaper.

The first real audit (a past Ads M1 build) ran at a 6.7% false-positive rate (1 of 15 findings), the
first measurement of a rate the design had only asserted; G1b keeps measuring it.

## 8. What FIND must not do

- **Not propose solutions.** That is Specify. A FIND output containing a solution has skipped the gate that tests whether the problem is real.
- **Not judge whether the product is worth building.** That is the business case in Stage C, and it needs the ROI model FIND does not build.
- **Not run usability tests.** That is Design, and it needs a design to test.
- **Not infer motivation from behaviour** without saying so. See §6.
- **Not fill a thin record.** "No evidence found" is a finding. Plausible-sounding domain knowledge is not evidence.

## 9. Open questions

| # | Question | Owner | Blocking |
|---|---|---|---|
| Q-F1 | **Revised; Enterpret done 2026-10-12** (Enterpret Wisdom connector). Authenticate **Sprig** for discovery next; Gong and G2 after, tagged for Stage C. Gong is buyer voice, not user voice, and routing it into discovery imports the bias discovery exists to avoid | author + IT | Motivation-level discovery findings |
| Q-F2 | **Answered: curate the event list up front, per initiative.** Amplitude returns an *empty chart* for an unrecognised event name rather than erroring, so a guessed name produces a confident "no signal here" finding that is actually a typo. Each initiative declares its events in `document-graph.yml`; the user-evidence specialist may only query declared events, and an undeclared event is a question for the human, not a guess | author + Analytics | Now unblocked |
| Q-F3 | What is the sampling rule for session replay? Watching ten replays chosen badly is worse than watching none, and cohort-filtered sampling is a real methodological choice | author | Replay-derived findings |
| Q-F4 | Greenfield mode has never been run. Both real runs so far were brownfield, so the `B → C → A` ordering is designed, not tested | author | Greenfield use |
| Q-F5 | Does discovery research need its own gate before Specify, or does G1 cover it? A weak problem statement that clears G1 poisons everything downstream, and G1 currently asks about findings first | author | Gate design |
