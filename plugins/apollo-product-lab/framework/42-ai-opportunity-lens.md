# 42 — The AI opportunity lens: where AI should make the user's journey easier

> Decision 2026-09-22 (Akansh). A PRD and a competitive comparison tell us what to build and how others
> built it. Neither asks where an assistant, a score, a suggestion or an automation would remove work
> for the user. The harness has to ask that itself, from the product and the roadmap, and then wait for
> a human go-ahead. Nothing here is built on the lens's say-so.

## 1. What the lens does

For a new product or a product-visible change it walks the user's journey step by step and asks, at each
step, "what does the user have to know, decide or type here that the product already has enough data to do
for them?" Every answer becomes one **opportunity** row:

| Column | Meaning |
|---|---|
| Journey step | the screen or moment, named as the design or PRD names it |
| Friction today | what the user must know, gather, decide or repeat; cite the PRD, design or domain file |
| AI assist type | one of: **suggest** (rank or propose), **score** (a number with a reason), **explain** (turn a state into plain language), **generate** (draft content or a configuration), **converse** (a chat or natural-language entry point), **automate** (act without asking, with an undo) |
| Data it needs | the fields, events or records it would read; say whether they exist today or come later on the roadmap |
| Value evidence | why the user cares: a research quote, an Amplitude number, a support theme, a competitor doing it; no evidence, no row |
| Compliance touch | which constraint-register invariants or copy rules it would have to respect; anything that touches consent, provenance, a provider or a legal claim is flagged for the human compliance lens |
| Cost tier | which registry tier would run it in production and roughly how often; a suggestion computed once per page view is not an assistant running per keystroke |
| Roadmap fit | now (this milestone), next (a named later milestone), or later (no home yet) |
| Options | do it now / next version / never, with one recommendation |

The lens is **not** allowed to invent data the product does not and will not have, to claim a metric the
constraint register forbids (Ads: a match rate before the platform confirms it), or to recommend "add a
chat assistant" without naming the step it shortens.

## 2. Where it runs

- **Stage B, after research and the competitive lens, before the PRD is authored** (doc 17 §2.1). The PRD
  author then sees accepted opportunities as requirements and deferred ones as "not in this version".
- **Council `prd` and `design` kinds**, as a standing lens beside competitive (doc 34 §2). On `erd` it runs
  when the model shape is product-visible, because a field the data model lacks is the usual reason an
  opportunity is "later".
- **Every intake** re-reads the initiative's `knowledge/ai-opportunities.md` and re-surfaces deferred rows
  whose "needs" the current work now provides. That is how "keep it for a future version" actually returns.

Registry role `find.opportunity.ai`: primary Anthropic Opus (it has to read the data model and the design),
market examples from the Glean family, Sol medium as the second opinion on value claims. Played by
`product-reviewer` in AI-opportunity mode.

## 3. The go-ahead, and what happens either way

The lens never decides. The memo carries the opportunity table and one question per row:

> "Opportunity 3, suggest which list to sync: do it now, next version, or never?"

- **Now** → the row becomes a PRD requirement (or a PRD delta), gets a metric in the metrics spec, and is
  sized into a slice like any other. `harness-council decide` records who chose it.
- **Next version** → the row is written to `knowledge/ai-opportunities.md` with `status: deferred`, the
  milestone it waits for, and what it needs. Intake re-surfaces it when that milestone or that data arrives.
- **Never** → same file, `status: rejected`, with the reason, so nobody proposes it again without new evidence.
- **No answer** → the row stays `proposed`. The orchestrator does not staff a build for it; an F-stage slice
  that implements a `proposed` opportunity is a router defect, the same as building before the competitive
  go-ahead.

The record is the file above plus the council memo; the Notion page for the memo carries the table in the
human voice (doc 33). Ledger event `B.ai-opportunity` for the scan, and the decision ledger event for each
answer.

## 4. Worked example: Ads Audience Sync

Read from `.ai/ads-builder/` on 2026-09-22; the rows are illustrations of the method, not decisions.

| Journey step | Friction | Assist | Data | Compliance touch | Fit |
|---|---|---|---|---|---|
| Choose a list to sync | user does not know which list will actually be exportable or large enough | **suggest**: rank lists by exportable share (first-party, consented, jurisdiction known), size against the platform minimum, and freshness | list membership, per-identifier provenance and consent, platform minimum | I1, I3, I9 decide exportability; the rank must not be presented as a predicted match rate (C5) | now: all data exists in M1 |
| Eligibility preview | "why can't I sync these 340 contacts?" | **explain**: group ineligible records by reason in plain words with the fix the user can make | eligibility ladder output | copy rules; never "consented"/"matched" | now |
| Build an audience | filters are fiddly; users describe audiences in words | **converse**: natural-language audience builder that maps to filters, then runs the same eligibility preview and attestation gate | filter vocabulary, saved searches | C1/C2: the assistant cannot pre-check or bypass attestation; I9 blocks global-database contacts | next: needs the filter mapping the M2 surfaces bring |
| Pick who to target | users sync who they have, not who is showing intent | **suggest**: propose an audience from Website Visitors intent ("visited pricing twice this month") | visitor intent events, attribution join | consent and jurisdiction gate per identifier; first-party only | next: M2 attribution |
| After sync | drift and silent removals go unnoticed | **automate**: health check that proposes a re-sync or flags removal failures, with a one-click action and an undo | sync operations, removal outcomes | C6/I7: failures visible, never only logged | now for the flag, later for the action |

Each row ends with the same question to the PM and Legal: now, next version, or never.

## 5. Why a lens and not a PRD section

A PRD section is written once by one person under deadline. A lens runs on every change, reads the roadmap
and the data model as they are today, and re-surfaces what was deferred. The point is the same as the
competitive lens: the harness carries the question so the humans only have to carry the answer.
