# {{PRODUCT_NAME}} — {{SURFACE}} domain knowledge

Knowledge base for `{{INITIATIVE}}-{{SURFACE}}`. Append-only.

**Maturity: {{MATURITY}}.** State this honestly at the top and keep it current. A reader needs to know whether this file is authoritative or aspirational before they trust a line of it.

---

## Invariants (binding, not decisions)

Constraints inherited from law, platform policy, or an architectural commitment already made. They cannot be traded away by preference. **Each is written so it can be checked in code review** — a prose obligation that cannot be checked will not be enforced.

| # | Invariant | Source | Status |
|---|---|---|---|
| I1 | | | settled / pending |

Seed these from the initiative's constraint register if one exists, via the invariant-extraction pass. **Never fabricate one.** A wrong invariant is worse than a missing one, because it will be enforced in review and nobody will re-check it.

## Decisions NOT yet made

Usually the most useful section in a new domain. Each of these will be decided by whoever writes the first slice that touches it, so the point is to make that visible in advance.

| # | Open decision | Why it matters | Blocked on |
|---|---|---|---|
| D-A | | | |

## Rejected and blocked approaches

Recorded so nobody spends a week rediscovering them. Include the reason; a bare "we don't do X" gets re-proposed.

- **{{APPROACH}}** — rejected because {{REASON}}. Source: {{SOURCE}}, {{DATE}}.

## {{SURFACE_SPECIFIC_SECTION}}

For a **backend** surface, this is the **enforcement points** table: every check a write path must pass, where it runs, and whether it is currently implementable. This is the highest-value backend artifact — a generic reviewer cannot infer it.

For a **frontend** surface, this is **required states** (enumerated per screen; absence is objective, not a matter of taste), **constrained copy and controls** (anything where law or platform policy dictates wording or default state, with the source), and the **Design source** block:

| Field | Value |
|---|---|
| Figma file / node | url + node id of the canonical design, or `none` |
| Figma approved revision | version or date the designer signed off; `pending` |
| Fabric Studio branch | `prototype/{owner}-{initiative}` |
| Prototype approved revision | commit sha the designer marked reviewable; `pending` |
| Module path | `src/prototypes/{id}/` |
| Preview | `fabric-studio-{branch-slug}.staging.apollo-forge.io` (VPN) |
| Storyboard | `<preview>/storyboard` — every page on one screen; reviewers start here |
| Gap list | `.ai/{{INITIATIVE}}/design-gap-<date>.md` from `/design-diff` |
| Components in scope | |
| Designer | |

The frontend agent reads the prototype before any UI change (prototype-first rule, seeded by `product-harness-init` step 5b). What the prototype never supplies and the surface must: i18n messages, state management, real API calls, tests, constrained copy the prototype softened, React 18 compatibility.

For an **architect** surface, this is **consequences worth knowing** — what current decisions make hard later.

For a **data** surface, this is **provenance, retention and licence terms** per source.

## Adjacent infrastructure: what exists and what does not

Populate from a codebase-reality research pass. **Cite `file:line` and real field names.** "Not found" means searched and not found, not inferred from adjacent code.

| Need | Reality | File |
|---|---|---|

This section prevents the most expensive class of estimate error: assuming infrastructure exists because it sounds like it should.

## External knowledge

Do not inline it. External facts live in `.ai/{{INITIATIVE}}/domain/external/` with their own tiering and decay rules, because their sourcing standard is different from everything above. Link the relevant file and the specific claims this surface depends on.

## Standing rules for this domain

Short list of things a contributor must do every time. Keep it under ten items — a longer list is not read.

## Log

*No entries yet.*

Required fields per entry: date · decision (imperative, one sentence) · why · alternatives rejected and why · consequences · source.
