---
name: design-diff
description: Diff a Fabric Studio prototype against the production package it specifies and write the gap list the frontend surface owner and the designer both work from. Deterministic inventory first (routes, components, fabric-core imports, copy), then judgment per gap (port / constraint wins / prototype missing / out of scope). Activate on "design diff", "gap list against the prototype", "what did the designer change", "compare prototype to production", or /design-diff INITIATIVE [--prototype PATH] [--production PATH].
---

# Design diff

Read the initiative's `domain/frontend.md` **Design source** block first: it names the Fabric Studio
branch, module path and preview. The prototype is the spec; production is what shipped; the
constraint register wins over both. This skill writes the gap list; it does not code the port.

**Storage first** (doc 45 §2). Before any read or write of the record, resolve the mode: a session with no Bash and no Write tool is `notion`; otherwise run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/storage.py" detect` (with `--surface` from the profile's `surface:`, and `--profile <file>` when the profile came from Notion) and print its `say` line once. In `notion` mode every `.ai/<initiative>/...` path in this file names a record page under the initiative's records root (doc 45 §3): write with `storage.py to-notion` and the `notion-create-pages` call it prints, read with `notion-fetch` then `storage.py from-notion`, append ledger events with `storage.py ledger-entry`, and skip git, gh, local `shasum` and `record-sync.sh` (Notion is already shared). In `local` mode the rest of this file applies unchanged; on claude.ai/code, where the profile came from Notion, export `HARNESS_PROFILE=<the fetched profile file>` before any `record-sync.sh` call so team sync sees it (doc 45 §4). The inventory script still needs both checkouts; on a surface without them (claude.ai chat) say so and stop, as below.

**Repo state.** This skill needs a local Fabric Studio clone and the product repo. Resolve the repo root first with `git rev-parse --show-toplevel` (doc 43 §10); every `.ai/` path is relative to that root, not to the current subfolder. No git repo (for example Claude Desktop with no checkout): say so in one line and skip steps 1, 2 and 5 and every git, gh and `record-sync.sh` call. Offer only step 3, a visual comparison of the Storyboard and the preview, with every observation marked `unverified` and the result given in chat. The gap-list file and its snapshot are written only inside a harness run (doc 43 §10).

## Steps

1. **Resolve inputs, and prove them.** Prototype module = local Fabric Studio clone checked out on
   the branch in the Design source block; production = the package `src/` the block's initiative
   owns. The inventory script records branch, commit and dirty state for both and fails on a missing
   directory or a branch mismatch (`--expect-branch`). A dirty tree is reported in the gap list, not
   hidden. Identify the revision running at the Storyboard preview (`git ls-remote origin <branch>`
   vs the deployed commit) and at the production preview; if either cannot be identified, every
   rendered observation is marked `unverified`. If the clone is missing, stop and point at
   `/apollo-rnd:setup-fabric-studio`; never diff from memory of the prototype.
1. **Run the inventory** (no model involved):
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/design-diff/scripts/inventory.py <prototype-module> <production-src> --expect-branch <branch> [--exclude <path>]... --out <run>/D.design-diff.inventory.md`.
   Exclusions come only from the owning package's `docs/base.md` scope statement, are passed
   explicitly, and are printed in the report; the script infers none. It lists routes, both component
   trees with fabric-core imports, name-based pairing *candidates* (nothing is dropped from the
   production list until a human confirms the pair), and a regex sample of copy. It says what it does
   not cover.
1. **Look at the pages, not only the files.** Open the prototype's Storyboard
   (`<preview>/storyboard`, or `npm run dev` then `/storyboard`) and production's equivalent
   screens on the preview environment. The storyboard is the all-pages view; a gap that is only
   visible when a page is rendered (state, spacing, empty states) does not show in the inventory.
1. **Build the state matrix, then classify.** The completion criterion is the initiative's required
   states (knowledge file) × screens: each cell gets a render or interaction method (Storyboard,
   preview click-through, Playwright, keyboard path) and evidence, or `unverified`. A page visible on
   the Storyboard proves the happy path only; disconnected, partial-failure, permission-denied and
   keyboard states need their own evidence. Constrained copy is read from the component or messages
   file verbatim, never from the regex sample. Then classify every pairing row into exactly one
   bucket, with a size (S/M/L) for ports:
   - **Port to production**: prototype does it, production lacks it, no constraint objects.
   - **Keep production (constraint wins)**: name the invariant (C1–C6 style id) from the
     knowledge file. This is the bucket the designer must hear about first.
   - **Prototype is missing**: production has a state or control the prototype never drew.
   - **Out of scope**: demo scaffolding named as such in the package's `docs/base.md`.
   - **Engineering note**: React 19-only API, a design-system bypass (direct `@ariakit/react`),
     a token production lacks.
1. **Write** `.ai/<initiative>/design-gap-<date>.md` in the shape of
   `.ai/ads-builder/design-gap-2026-09-18.md`: header with prototype branch@sha, production
   branch@sha, Figma file/node reference from the Design source block, both preview revisions; the
   five buckets; the state matrix; a **Designer disposition** column per gap (`accepted` /
   `revised in prototype @sha` / `disputed`, empty until the designer fills it); and "Feedback to
   send the designer" (drafted, a human sends). Write `D.design-diff.snapshot.md` (doc 33 template)
   whose inputs carry both shas and the exclusions. Append one ledger event, then `bash "${CLAUDE_PLUGIN_ROOT}/scripts/record-sync.sh" push <initiative> "<initiative>: design diff"`
   so the designer and the frontend owner read the same gap list (no-op for solo).
1. **Close the loop, do not just hand off.** The port list goes to the `<initiative>-frontend` owner
   as F-stage slices. The constraint bucket goes to the designer through the council `design` kind.
   The gap list is *open* until every row has a disposition; a constraint override that changes the
   design reopens gate G2b. Writing the survivor back to Figma is a human-authorized step (doc 17
   Q-D3): the skill drafts the change list, a designer applies it or approves the agent's write, and
   the read-back (Figma version or node id) is recorded in the Design source block.

## Hard rules

- A clean inventory is not "constraints passed": only the state matrix and verbatim copy checks are.
- The prototype never becomes a second production, and production never becomes a second design
  source. A gap is closed on one side or the other, recorded in the knowledge file log.
- Constrained copy is compared verbatim. "Softened" is a fail, not a nuance.
- Do not invent a production counterpart: **none** in the pairing table stays **none** until a
  human maps it.
