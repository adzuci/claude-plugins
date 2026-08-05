# Automation & Scheduled Workflow Risk Checklist

## Scope — runtime & execution (not schema)

This checklist covers **live automation behavior**: scheduled runs, worker execution, retries, concurrency, batch outcomes, and observability during operation.

Do **not** duplicate ERD pass cases for the same topic at **config/schema** level — e.g. here test that a configured push chain **executes within depth limits**; in the ERD pass test that an invalid graph is **blocked or warned on save**.

## When to apply

Use during **Step 3** when the feature involves any of:

- Schedules or cron-like execution
- Background runs, workers, or async pipelines
- Push/sync between entities (e.g. sheet-to-sheet, record upsert)
- Dedup, primary keys, or merge strategies
- Downstream actions (sequence, list, CRM sync, webhooks)

Skip rows that are genuinely out of scope for the release — note "out of scope" in the Step 4 gap self-review.

## Checklist

| Risk area | Example tests to consider |
| --------- | ------------------------- |
| **Idempotency** | Retry after failure does not double-write, double-push, or double-enroll |
| **Concurrency** | Manual run + scheduled run in the same window does not duplicate rows or lose edits |
| **Partial failure** | Batch operations show progress/final status; failed rows are not silently mixed with successes |
| **Guards & limits** | Runtime: executing chain stops at depth limit; cross-scope push blocked during run (not just on save) |
| **Key integrity** | Runtime: invalid/empty keys during import/sync do not merge unrelated records on live runs |
| **Granular triggers** | Only dependents of the changed subfield/value re-run (not whole-object fan-out) |
| **Downstream actions** | Each in-scope action type has at least one automated-run case |
| **Observability** | Scheduled vs manual runs, failure reasons, last/next run visibility |
| **Scale** | Large batch behavior within acceptable time; no hung runs |

## Priority guidance

| Risk area | Typical priority |
| --------- | ---------------- |
| Idempotency, key integrity, guards | P0 |
| Concurrency, partial failure, downstream actions | P0–P1 |
| Observability, granular triggers | P1 |
| Scale (unless launch-blocking) | P2 |
