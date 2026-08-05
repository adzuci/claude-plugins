# Notion Bug-Bash Conventions — Index

Confirmed by direct read-only inspection of the real workspace. Never create a new database, squad
entry, or property to work around a gap — ask the user instead.

## The four real Notion pieces

| Piece | data_source_id | Title property | Notes |
| --- | --- | --- | --- |
| **Test Plan DB** | `c9bc4007-0e7c-4de0-b345-928cdb95b7ee` | `Name` | One shared DB for all squads |
| **Teams DB (fka Squads DB)** | `2873c25d-ea13-4cea-bec7-72a7b77a9e02` | `Team` | Match target for a user-given squad name |
| **Test Case DB** | `a6e0a264-6253-4f7c-999e-d450b47d68bd` | `Name` | Same DB `bug-bash-generator` already writes to |
| **Bugs DB** | `87d4a43c-f949-4736-be96-87d37c57d2f5` | `Title` | "Bugs found" on every Test Plan page is a filtered view into this DB |
| **Test Plan page template** | `114ab2b3b49680a88ee8c67234af2fe6` | — | Apply via `template_id`, never hand-authored `content` |

There is **no per-squad database** — squads are scoped via one relation property (`Squad DB` on the
Test Plan DB) plus saved filtered views. "Confirming the squad DB" means confirming which Teams DB
row to relate to, not finding a squad-specific database.

## Where the actual conventions live

Read only the file for the phase you're on — each is self-contained and links back to the IDs above:

| Phase | File |
| --- | --- |
| 0.2 — Squad matching | `notion-squad-matching.md` |
| 2 — Test Plan page + Test Case DB rows | `notion-test-plan-and-cases.md` |
| 4.0 — Test Case status write-back | `notion-test-case-status.md` |
| 4.2 — Bugs DB rows + evidence attachment | `notion-bugs-and-evidence.md` |
| 4.3 — Jira link-back | `jira-filing-rules.md` (Jira filing is already opt-in-only, so the link-back lives there too) |
