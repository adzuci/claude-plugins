# Test Case Status Write-Back (Phase 4.0, mandatory every run)

Test Case DB: `collection://a6e0a264-6253-4f7c-999e-d450b47d68bd`.

Every Test Case row is created at `AI Status: "Not started"` (its default). Without a write-back, a row
looks untouched forever even after this skill actually ran it. Close that loop for every case executed
in Phase 3, before Phase 4's bug logging:

Use `notion-update-page` (`update_properties`) on each executed row, setting **`AI Status`** — the
status field for AI-executed outcomes. Fetch the data source schema first and choose an existing option
(do not assume names). Map this run's real result:

- **Passed clean:** `AI Status: "Pass"`.
- **Failed (bug logged this run):** `AI Status: "Fail"`.
- **Mixed / non-critical gaps, or partially executed** (blocked partway by an environment issue, not a
  product bug): `AI Status: "Conditional Pass"`.
- **Could not execute at all** (environment/setup blocker): `AI Status: "Blocked"`.
- **Not applicable to this build** (out of scope, or skipped per §0.11): `AI Status: "Out of scope"`,
  or leave at `"Not started"` for rows that were never reached — don't touch rows that weren't actually
  executed.

Update every executed case, not only failures — a pass left at `"Not started"` is just as misleading.

**Never write the `Status` property.** `Status` is owned by humans: its options (`Fix Deployed`,
`Fix in review`, `Retest Required`, etc.) are dev/QA triage after a bug is filed, not this run's raw
execution outcome. AI must set `Status` only when the user explicitly asks for it in this run;
otherwise leave it untouched. (`AI-tested` is a legacy select that predates `AI Status`; prefer
`AI Status` — it carries the full option set, including `Conditional Pass`, `Blocked`, and
`Out of scope`.)
