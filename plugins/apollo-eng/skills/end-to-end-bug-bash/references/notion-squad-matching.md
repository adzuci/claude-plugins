# Squad Matching (Phase 0.2)

Teams DB: `collection://2873c25d-ea13-4cea-bec7-72a7b77a9e02` (title property `Team`). Full ID table
in `notion-bug-bash-conventions.md`.

1. Ask for the squad name once per run (one squad per campaign by default; ask again only if a
   specific feature genuinely needs a different one).
1. Query the Teams DB for candidates matching the name (SQL `LIKE` or exact match on `Team`).
1. **Re-fetch this data source's schema fresh before filtering** to confirm its `Type` and
   `Status`-like property names — don't hardcode a guess, since it may have changed. Use those to
   exclude `[Archived]`, `(Archived)`, duplicates, and generic org-bucket rows (`G&A`, `GTM`, `CEO`,
   `ELT`, `R&D`, template placeholders).
1. **Exactly one clean match:** confirm it back in one line ("Using squad: X") and proceed.
1. **Zero or multiple candidates:** stop and ask for the exact name — never guess, never create a new
   Teams DB row as a shortcut.
1. Store the matched Team page URL — it becomes the Test Plan page's `Squad DB` relation in Phase 2.
   **Hard gate: Phase 2 cannot create the Test Plan page until this resolves.**
