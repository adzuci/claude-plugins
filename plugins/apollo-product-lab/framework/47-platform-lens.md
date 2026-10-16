# 47 — The platform lens: build it once for every product that needs it

> Decision 2026-10-12 (Akansh). Apollo keeps building the same capability twice: a check one product gets
> and its sibling lacks, a flow that exists in three near-same forms, a backend service written again
> next to one that already does the job. The competitive lens asks how others built it and the AI
> opportunity lens (doc 42) asks where AI would remove work; neither asks whether the thing already
> exists, or should exist once, elsewhere in Apollo. The platform lens asks that, proposes the
> platform-level shape, and waits for a human go-ahead. Nothing cross-product is built on its say-so.

## 1. When it runs (conditional)

The code-level twin of this lens, the reuse scan, is not conditional: it runs on every slice and design
(doc 48 §1), and opens this lens when it finds a near-same capability another product owns.

The lens is **not** a standing lens on every change. It runs when both hold:

1. the change adds or changes a **user capability**, a **user flow**, or a **backend service or model**;
   and
1. the **quick sibling check** finds the same or a near-same capability elsewhere in Apollo: an `rg` over
   the product repo for the capability's nouns and verbs, `surface-owners.yml` for products that own a
   similar surface, the seeds in §3 and the initiative's `knowledge/platform-opportunities.md`. Without a
   checkout, Glean `code_search` and `search` stand in, and what no tool could open is `unverified`.

A one-file fix, a copy change, an internal refactor, or a capability with no sibling found skips it. The
skip is recorded, never silent: one row in the intake snapshot's lens table, `platform lens: skipped`,
with the reason (`fix-size`, `copy only`, `internal refactor`, or `no sibling: <what the quick check searched>`). A later stage that finds a sibling reopens the lens and says so in its snapshot.

## 2. What the lens writes

Every finding is one **platform row**:

| Column | Meaning |
|---|---|
| Kind | **feature parity**, **shared flow** or **shared backend** (§3) |
| Capability | the capability, flow or service, named as the PRD, design or ERD names it |
| Where it exists | path or page, and the owning team from `surface-owners.yml`; `unverified` when nobody opened it |
| How it differs | steps, copy, states, limits, data model: what an entry point would gain or lose by sharing it |
| Proposed platform shape | one reusable flow or service, the entry points it serves, the owning team, the migration order |
| Cost now vs later | what sharing costs in this change, and what doing it later costs (a second migration, a parity backlog) |
| Roadmap fit | now (this milestone), next (a named later milestone), or later (no home yet) |
| Options | **platformize now** / **do locally now and record the follow-up** / **never**, with one recommendation |
| Owning-team question | the question the other team must answer; a cross-team row carries it to that team, not only to the author's PM |

The lens is **not** allowed to claim a sibling it did not open, to propose moving another team's surface
without naming that team, or to recommend "make it a platform" without the entry points the shape serves.

## 3. The three kinds of row

The seeds are examples to verify, never facts: each was true when written and must be re-checked.

- **Feature parity.** A capability added to one surface that sibling surfaces lack, or one the change is
  adding that a sibling already has. Seed: the image spam check built for Broadcast, which Sequences does
  not run. The row asks whether the capability should be one check every sending surface calls.
- **Shared flow.** A user flow that exists in near-same form elsewhere. Seeds: segments in Subscribers next
  to Lists and Saved searches; add to list; recipient and subscriber pickers; CSV import (in leadgenie on
  2026-10-09 at least `assets/common/components/common-csv-imports`, `assets/common/components/csv-import-modal`,
  the AI Sheets `ImportCsvDialog` and `packages/accounts/src/account-imports`). The row proposes one flow,
  the UX-parity rows each current entry point must keep or gain, and the Fabric components it is built from.
- **Shared backend.** A new service or model that duplicates, or could ride, an existing platform backend.
  Seed: Automated campaigns on the AI Sheets backend. The row names the pack boundary, the owning team, the
  ERD or plan change it implies, and what the existing backend would need to carry the new load.

## 4. What each role gets

- **PM**: scope and roadmap. Parity gaps and shared flows become PRD scope lines (in this version, deferred
  with a reason, or rejected), and a cross-product row names the roadmap it lands on.
- **Designer**: one flow. The shared-flow rows give the single flow, the UX-parity rows per entry point, and
  the Fabric components to reuse (`@apolloio/fabric-core` first, then `@apolloio/fabric`).
- **Engineering**: shared backend. The shared-backend rows give the service or model to reuse or extract,
  the pack boundary, the owning team, and the ERD or plan delta.

## 5. Where it runs

- **Intake**: the quick sibling check of §1 decides whether the lens runs, and its result is a lens row.
  Intake also re-reads `knowledge/platform-opportunities.md` and re-surfaces deferred rows (§6).
- **Stage B, after the competitive lens and the AI opportunity lens, before the PRD is authored**
  (doc 17 §2.1), when §1 triggers.
- **Council `prd` and `design` kinds**, as a conditional standing lens: on when §1 triggers, with the skip
  row otherwise (doc 34 §2).
- **Council `erd` and `plan` kinds**, for **shared-backend** rows only, when the model or service has a
  sibling backend (doc 34 §2).

Registry role `find.opportunity.platform`: primary Anthropic Opus (it has to read the repo, the design and
the data model), internal record from the Glean family, Sol medium as the second opinion on cost claims.
Played by `product-reviewer` in platform mode, which generalises its earlier platformization mode.

## 6. The go-ahead, and what happens either way

The lens never decides. The memo carries the platform table and one question per row:

> "Platform row 2, segments in Subscribers next to Lists and Saved searches: platformize now, do it
> locally now and record the follow-up, or never?"

- **Platformize now** → `status: accepted`; the row becomes a PRD requirement or an ERD/plan change and is sized into slices.
  `harness-council decide` records who chose it.
- **Do locally now, record the follow-up** → the row is written to `knowledge/platform-opportunities.md`
  (template `templates/platform-opportunities.md`) with `status: deferred`, the milestone or condition it
  waits for, and the follow-up owner. Intake re-surfaces it when that arrives.
- **Never** → same file, `status: rejected`, with the reason, so nobody proposes it again without new
  evidence.
- **No answer** → the row stays `proposed`. The orchestrator does not staff a cross-product build for it; an
  F-stage slice that builds a cross-product change from a `proposed` row is a router defect.

A **cross-team row** (the sibling or the proposed owner is a team other than the author's) also needs the
owning team's recorded answer before the shared change is built, in the owning-team lens's words (doc 43
§5): `approved`, `changed` or `not needed`, with who and when. Posting the proposal in a channel is not a
review.

The record is the file above plus the council memo; the Notion page for the memo carries the table in the
human voice (doc 33). Ledger event `B.platform-opportunity` for the scan, and the decision ledger event for
each answer.
