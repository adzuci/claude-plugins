# ERD Proposed Delta Pass

Use during **Step 3 → ERD analysis** after reading the full ERD (existing + proposed models).

## Scope — schema & configuration (not runtime)

This pass covers **design-time / schema-level** behavior: proposed entities, config fields, guard definitions, validation rules, and setup/save flows.

Do **not** duplicate Section J (automation checklist) cases that test the same topic at **runtime** — e.g. here test that cycle detection **warns or blocks on save**; in the automation checklist test that a **live push chain** respects depth limits and does not run away.

## When to apply

Apply whenever the ERD documents **NEW or CHANGED** entities, fields, enums, guards, embedded configs, or write modes — not only the current/production model.

## Required analysis

For each proposed addition, extract:

- Entity purpose and attachment point in the existing model
- New fields, enums, and allowed values
- Guards, limits, and validation rules
- Write modes (create vs upsert, collision behavior)
- Relationships to other entities (including cross-entity graphs)

## Mandatory test cases to generate

Create at least **one focused atomic test case** per proposed addition. Cover:

| Area | What to test |
| ---- | ------------ |
| **Graph / cycles** | Config-time: invalid push graph rejected or warned **before save** (direct A↔B and indirect A→B→C→A) |
| **Keys & dedup** | Config-time: primary-key selection, merge-strategy options, invalid key rejected in setup UI/API |
| **Write semantics** | Config-time: upsert vs create mode; keep-existing vs apply-updates options defined in model |
| **Config drift** | Config-time: broken mapping/target detected when target column or sheet is deleted or inaccessible |
| **Guards & limits** | Config-time: guard fields present (max depth, cross-scope block); validation on save |
| **Markers & audit** | Schema-time: run-origin / trigger-type fields exist and are writable on records |

## Output rules

- Do **not** fold these into journey E2E cases only — each distinct failure mode needs its own testable case.
- Map cases to the Jira sub-task or ERD row when available (aids traceability).
- Mark stretch / not-yet-shipped proposed entities as **P2+** or note "skip if not shipped".
