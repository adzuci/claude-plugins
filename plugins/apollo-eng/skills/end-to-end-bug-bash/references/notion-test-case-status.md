# Test Case Status Write-Back (Phase 4.0, mandatory every run)

Test Case DB: `collection://a6e0a264-6253-4f7c-999e-d450b47d68bd`.

Every Test Case row is created at `Status: "Not started"` and `AI-tested: "Not tested"` (its
default). Without a write-back, a row looks untouched forever even after this skill actually ran it.
Close that loop for every case executed in Phase 3, before Phase 4's bug logging:

Use `notion-update-page` (`update_properties`) on each executed row, setting **`AI-tested`** — the
field built for exactly this (`Not tested` | `Partially pass` | `Pass` | `Fail`). Never `Status` for
this: its options (`Fix Deployed`, `Fix in review`, `Retest Required`, etc.) belong to human/dev
triage after a bug is filed, not to this run's raw execution outcome.

- **Passed clean:** `AI-tested: "Pass"`.
- **Failed (bug logged this run):** `AI-tested: "Fail"`.
- **Partially executed** (blocked partway by an environment issue, not a product bug): `AI-tested: "Partially pass"`.
- **Never reached this run** (out of scope, or skipped per §0.11): leave at `"Not tested"` — don't
  touch rows that weren't actually executed.

Update every executed case, not only failures — a pass left at `"Not tested"` is just as misleading.
