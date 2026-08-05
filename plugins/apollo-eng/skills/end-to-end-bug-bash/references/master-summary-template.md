# Campaign Rollup Format (Phase 5)

Write `MASTER-SUMMARY.md` to `playwright/reports/ai_manual/` once every in-scope feature has been
through Phases 1-4. This structure is lifted directly from the AI Sheets QA campaign's
`MASTER-SUMMARY.md` — it's what let a reader who wasn't in the session understand the whole campaign
in one pass. Update it incrementally in campaign mode (append per-feature rows as each feature
finishes) rather than writing it only at the very end, so a partial campaign still has a useful summary.

## Structure

```markdown
# [Campaign name] — Master Summary

[Only if applicable: a "RESOLVED — <blocker>" callout section at the top for any environment/access
blocker that got fixed mid-campaign and materially affected multiple features — root cause, fix,
what's still worth fixing about the *surfacing* of that blocker even though the blocker itself is gone.]

**Environment:** [base URL]
**Scope:** [where the feature list came from — e.g. a named Notion board, a single bug-bash page —
and the inclusion/exclusion rule used, e.g. "status Done or Implementing"]

**Status:** [N features accounted for — X fully tested, Y excluded as out-of-methodology-scope with
reasons, Z still blocked]

**For anyone picking up e2e automation from this campaign:** see `E2E-AUTOMATION-HANDOFF.md` in this
same folder.

---

## Cross-cutting findings (apply across multiple features)

1. **Access/environment blockers found:** [one bullet per blocker, resolved or not, with what unblocked
   it and what re-testing confirmed]
2. **Repeated bug/UI patterns:** [a bug or pattern independently confirmed in 2+ features is a strong
   signal of a shared root cause — call this out explicitly, don't let it read as two unrelated bugs]
3. **Ticket-status vs. reality:** [any case where Jira/Notion status didn't match what was actually
   observed in the product — these are individually load-bearing findings, list them]
4. **Environment/tooling issues found and fixed (or documented) for future runs:** [anything about the
   test environment itself worth flagging for the next person running this skill]

---

## Per-feature results

| Feature | Status | Result | Bugs found |
|---|---|---|---|
| [name] | [✅ Done / 🚧 Blocked / N/A] | [short pass/fail summary] | [count + severities, or "—"] |

### Notable individual findings (highest signal first)

- [One bullet per standout finding across all features, ranked by severity/signal — not grouped by
  feature. Positive surprises belong here too (things that turned out to work despite a "known bug" or
  "cancelled" ticket status) — don't only report bad news.]

---

## Recommended next steps

1. [Ranked list — fix-worthy bugs first, then remaining access gaps, then process/tooling
   recommendations. Reference bug IDs, not just prose descriptions.]

**[Closing status line — e.g. "every feature in scope has been fully tested" or an honest statement of
what's still incomplete and why.]**

## Bugs logged to Notion

[Default section, always present: total genuine-bug count logged this campaign, a link back to the
squad's Test Plan view in Notion, and — if any environment/access issues were found and resolved
mid-campaign rather than logged as bugs (flag enabled, credential reconnected, plan upgraded, etc.) —
list those explicitly as deliberately-not-logged, with what fixed them.]

## Jira tickets filed (only if Jira filing was explicitly requested this campaign — omit section otherwise)

[If, and only if, Jira filing was actually requested and performed: list the ticket IDs, which epic
they went under, and confirm each is linked back to its source Notion bug row (per
`jira-filing-rules.md`'s link-back step). If Jira was never requested, omit this section entirely —
don't include an empty "Jira tickets filed: none" placeholder, since Jira being untouched is the
default, not a gap needing explanation.]

Canonical test plans and bugs live in Notion (see the squad's Test Plan view, linked above). Local
`bug-report-<feature>.md` files and raw evidence (screenshots/video/trace) live in
`playwright/reports/ai_manual/` as secondary/companion artifacts (per `bug-report-template.md`) — not
the primary record.
```

## Rules

- Don't bury the lede: if one environment blocker (a quota, a disabled flag, a broken credential)
  affected many features, it goes in its own callout at the very top, not mixed into the numbered
  cross-cutting list.
- "Notable findings" is ranked by signal, not chronology or feature order — the P0 silent-data-loss bug
  goes above a minor UX nit regardless of which feature was tested first.
- Always report positive surprises (things that work despite a ticket saying otherwise) — a summary
  that's all bad news undersells the campaign and under-corrects stale ticket status.
- Keep the per-feature table scannable — one row per feature, detail lives in that feature's own
  test-plan/bug-report files, not inline here.
