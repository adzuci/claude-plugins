---
name: artifact-audit
description: Audit a product initiative's document set (PRDs, estimates, legal/constraint registers, design, Jira) for internal contradictions, missing required sections, stale claims, unestimated requirements, and unowned decisions. Reads a document-graph config, runs deterministic schema and freshness checks first, then constrained pairwise contradiction detection along declared edges only. Every finding carries verbatim quotes from both sides. Activate when the user says "audit the docs for INITIATIVE", "are these specs consistent", "check the PRD against legal", "what contradicts what", or runs `/artifact-audit`. Stage A of the product-building harness (see ${CLAUDE_PLUGIN_ROOT}/framework/12-product-harness.md).
---

# Artifact Audit

You are auditing an initiative's document set for internal inconsistency. You are **not** reviewing quality, giving product advice, or improving the docs. You find and evidence contradictions. Someone else decides what to do about them.

## The two failure modes, and which one to fear

A reviewer prompted to find gaps will usually report some, even when the work is sound. Over-reporting is as damaging as under-reporting here, because it trains the reader to skim, and habituation is measurable (approval rate rises, inline comments fall).

So the hard rule below is not stylistic. It is the mechanism that keeps this skill trustworthy.

> **Every finding must quote verbatim from at least two artifacts (or from one artifact and one deterministic check result). A finding without quotable evidence on both sides is dropped, not softened.**

If you find nothing, say you found nothing. That is a valid and expected outcome.

**Storage first** (doc 45 §2). Before any read or write of the record, resolve the mode: a session with no Bash and no Write tool is `notion`; otherwise run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/storage.py" detect` (with `--surface` from the profile's `surface:`, and `--profile <file>` when the profile came from Notion) and print its `say` line once. In `notion` mode every `.ai/<initiative>/...` path in this file names a record page under the initiative's records root (doc 45 §3): write with `storage.py to-notion` and the `notion-create-pages` call it prints, read with `notion-fetch` then `storage.py from-notion`, append ledger events with `storage.py ledger-entry`, and skip git, gh, local `shasum` and `record-sync.sh` (Notion is already shared). In `local` mode the rest of this file applies unchanged; on claude.ai/code, where the profile came from Notion, export `HARNESS_PROFILE=<the fetched profile file>` before any `record-sync.sh` call so team sync sees it (doc 45 §4). In notion mode the document graph is the `document-graph.yml` record page, and artifacts are fetched from their URLs.

**Repo state (local mode only; in notion mode use the `document-graph.yml` record page, and if the records root has none, ask for the document list).** Resolve the repo root first with `git rev-parse --show-toplevel` (doc 43 §10); every `.ai/` path is relative to that root, not to the current subfolder. If there is no git repo, or no `.ai/` at its root, and the person gave no document-graph path, say "give me the document list or a document-graph file to audit" in one line and stop. Do not run git or gh. With a list of Notion or Jira links, run the phases on those and write findings in chat instead of `.ai/`.

## Input

A document-graph config. Default lookup order:

1. A path the user gave you.
2. `.ai/<initiative>/document-graph.yml`
3. Ask. Do not guess at an artifact set.

See `templates/document-graph.yml` for the schema. Read `references/artifact-schemas.md` for the required sections per `kind`, and `references/contradiction-classes.md` for the finding taxonomy.

## Process

Run the phases in order. **Phases 1-3 and 5 are deterministic — no model judgment.** Do those first; they are near-free and they catch the highest-confidence problems.

### Phase 1 — Resolve

Fetch every artifact in the config.

- Record every fetch failure **explicitly as a finding** of class `unreachable-artifact`. Do not silently skip. An artifact nobody can read is itself a problem (a design prototype behind session auth has never been validated against anything).
- Record `last_edited` for each artifact. You need it in Phase 3.

### Phase 2 — Schema check (deterministic)

For each artifact, check the required sections for its `kind` against `references/artifact-schemas.md`.

Emit `missing-required-section` per absent section. Quote the surrounding headings to prove absence is real and not a naming variant. Check for synonyms before declaring absence (a "Goals" section may satisfy a required "Success metrics" if it contains numbers; a section that exists but is empty still counts as missing).

### Phase 2.5 — Self-consistency pass (deterministic, per artifact)

Check each artifact against **itself** before comparing it to anything else. Pairwise edges structurally cannot catch a document that contradicts its own other section, and a summary that faithfully copies one of two conflicting internal figures will look correct on every edge.

Look for: the same quantity stated with two different values in different sections; a total that does not equal the sum of its parts; a headcount or parallelism assumption that differs between a table and the prose beneath it; a scope item listed as both in and out.

Emit as `mutually-exclusive-claim` with both locations **inside the same artifact**. The two-quote rule still applies; both quotes just come from one document.

This phase exists because of a real case: an estimate doc stated "≈ 3 sprints + 1 week buffer (~3.5 sprints total)" in its summary table and "~3.5 sprints + 1 week buffer" in its timeline section, a one-week difference. The rollup that summarised it copied the first version verbatim, so every edge audit reported clean.

### Phase 3 — Freshness and lapsed-date check (deterministic)

- Any date field in the past while the artifact's status is not shipped/closed → `lapsed-date`. Quote the date and the status together.
- For each edge, compare recency across the pair. Note which side is older. **Do not conclude anything yet** — this is input to Phase 4, not a finding on its own.

**Recency comes from the config, not from the fetch.** The Notion fetch path returns only a retrieval timestamp, not `last_edited_time`, so recency cannot be established automatically. Each artifact therefore carries an explicit `as_of` field in the document graph, and it is the config author's job to keep it current. If an artifact has no `as_of`, say so in the Phase 6 coverage note and make no staleness determination for any edge touching it — do not substitute the retrieval timestamp, which is always "now" and would rank every artifact equally fresh.

For a `constraint-register`, `as_of` should be its own stated verification date, which is frequently older than the document's last edit and is the figure that actually matters.

### Phase 4 — Contradiction detection (the only model-judgment phase)

**Only compare pairs declared in the config's `edges`.** Never all-pairs: it is quadratic in cost and produces noise between artifacts that were never meant to agree.

For each edge, dispatch one sub-agent. Give it exactly the two artifacts and the edge's `reason`. Require it to return, per candidate contradiction:

- a verbatim quote from side A, with its location
- a verbatim quote from side B, with its location
- why they cannot both be true
- which side is presumed stale, and on what basis

Cap each sub-agent's return at ~1,500 tokens. Discard any candidate that arrives without both quotes.

**Authority does not beat recency.** A config may mark a constraint register as higher `authority` than a plan, but a plan edited later may reflect a decision the register has not absorbed. When authority and recency disagree, report both facts and let the human adjudicate. Never silently pick a winner.

This rule exists because of a real case: a legal register said a platform question was "not yet requested" while the PRD encoded that platform's actual written answer. The register was authoritative and four days stale. The PRD was right.

### Phase 5 — Coverage check (deterministic)

- Every entry in a `constraint-register` that gates a milestone must appear in a `plan` or `estimate` artifact. Absent → `unestimated-requirement`. This is the class most likely to represent real schedule risk.
- Every decision or open question must have a named owner. Absent → `unowned-decision`.
- Every requirement asserted in a `prd` must be traceable to an estimate line. Absent → `unestimated-requirement`.

### Phase 6 — Emit

One table, ranked by consequence, not by class. Then a short "no findings in" list naming what you checked and found clean, so the reader can see coverage rather than inferring it.

| # | Class | Artifacts | Evidence | Why it matters |
|---|---|---|---|---|

Rules for the output:

- Rank by consequence: something that invalidates a plan outranks a missing section.
- State what you did **not** check and why (unreachable artifacts, edges not declared in the config, artifact kinds with no schema defined).
- No recommendations, no prioritisation advice, no "consider doing X". Findings only.
- Target: adjudicable in under 15 minutes by the initiative's owner. If the table exceeds ~15 rows, you are almost certainly over-reporting. Re-apply the two-quote rule and cut.

## Cost discipline

- Phases 1-3 and 5 use no sub-agents.
- Phase 4 uses one sub-agent per declared edge, under doc 51's guards (`${CLAUDE_PLUGIN_ROOT}/framework/51-sub-agents.md`: each brief starts with its depth line, edge agents never spawn, one retry). The per-edge fan-out is council-shaped, so it reuses the profile's `council_budget` as its token budget. Platform concurrency 20 is the non-overridable hard stop: a config with more than 20 edges must be split into waves, regardless of any go-ahead. Before dispatching, estimate the per-edge brief tokens with the one estimate rule of `harness-council` step 3b and sum them: if the total goes over `council_budget`, report the count, the estimate and the reason, and ask the person before proceeding.
- Prefer Haiku for Phases 1-3 mechanical passes; reserve the stronger model for Phase 4.
- Never load an artifact twice. Resolve once in Phase 1 and pass content to sub-agents.

## Output persistence

Write findings to `.ai/<initiative>/audit-<YYYY-MM-DD>.md` so successive runs are diffable, then `bash "${CLAUDE_PLUGIN_ROOT}/scripts/record-sync.sh" push <initiative> "<initiative>: audit"` (no-op for solo). A finding that persists across runs without being addressed is itself signal, and Stage H (learning) needs the history.

Do **not** write findings back to the source documents or to Jira. This skill reports; it does not mutate the artifacts it audits.
