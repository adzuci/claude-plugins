# Pre-push checks

Read this reference before pushing stage 3 code. Use the commands and required checks from the
target repository when they differ from these observed frontend patterns.

## Frontend checks

- **Strict ESLint:** `no-nested-ternary` can fail files marked `// eslint-strict` even when the
  ordinary local lint path passes. Prefer explicit `if`/`else` and run the strict path.
- **Prettier:** run the repository's Prettier check on every touched frontend file. The CI formatter
  can differ from an ESLint fix pass.
- **TypeScript strict:** validate new production and test files. A new test-only type error can fail
  the generated strict-errors gate.
- **Coverage:** distinguish advisory `undercover-ci` warnings from enforced frontend coverage jobs.
  Satisfy the enforced checks without treating advisory output as a merge blocker.

## CI and toolchain traps

- Set `VOLTA_FEATURE_PNPM=1` when the repository's Volta configuration requires pnpm.
- Use the repository's documented heap size for large TypeScript or ESLint runs.
- Confirm the current semantics before using `PREPUSH_DEVOWNER_CHECK` or `SKIP_COVERAGE`; do not
  copy an old polarity or bypass required checks.
- Do not use a workflow rerun when repository consistency checks require a fresh commit event.
  Prefer a real fix and new commit; never create an empty commit merely to conceal an unchanged
  failure.
- Recheck branch freshness, image-build, and preview requirements against the current base branch
  before declaring the PR ready.
