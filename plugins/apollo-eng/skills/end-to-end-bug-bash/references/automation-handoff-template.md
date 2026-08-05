# Automation Handoff Format (Phase 5)

Write `E2E-AUTOMATION-HANDOFF.md` to `playwright/reports/ai_manual/` alongside `MASTER-SUMMARY.md`.
Structure lifted from the AI Sheets QA campaign's `E2E-AUTOMATION-HANDOFF.md` — a curated,
per-feature list of exactly which manually-verified test cases are ready to become real Playwright
specs now vs. which should wait. Point `playwright-testing` skill users here before they pick a manual
test case to automate.

## Structure

```markdown
# E2E Automation Handoff — [Campaign name]

For: [who this is for, e.g. "anyone picking up e2e automation from this campaign"]
Use with: `playwright-testing` skill
Source of truth: `MASTER-SUMMARY.md`, each feature's Notion Test Plan page (canonical test cases +
bugs), and the secondary local `bug-report-<feature>.md` in this same folder

## How to use this

- **Passed cleanly →** automate as-is.
- **Real bug found →** don't automate yet. Once fixed, write the spec to assert the *fixed* behavior —
  or, if the team wants a regression guard immediately, pin the *current* (broken) behavior explicitly
  and flag it for follow-up. Ask if unclear which the team wants.
- **Feature genuinely doesn't exist in the UI yet →** cannot automate, not a bug — note it and move on.
- **Ambiguous/product judgment call needed →** needs product input before writing any spec.

---

## [Feature Name]

- Existing coverage: [named spec files under playwright/src/e2e/ already covering this feature, if any]
- **Status:** [only if this feature was blocked/resolved mid-campaign — one line]
- **Automate these (passed):**
  - TC-[ID]: [one-line rationale/caveat, e.g. "straightforward — no flakiness observed across N reruns"]
- **Don't automate yet — bugs found:**
  - TC-[ID]: blocked by BUG-[ID] ([severity]) — [assert-fixed vs pin-current-behavior guidance]
- **Cannot automate — feature doesn't exist yet:**
  - TC-[ID]: [what's missing]
- **Inconclusive/needs product input:**
  - TC-[ID]: [what's ambiguous and why]

[Repeat per feature]

---

## Cross-cutting

[Bugs or patterns confirmed in 2+ features — e.g. a shared component bug — called out once here rather
than duplicated in every affected feature's section, with a pointer back to which features hit it.]
```

## Rules

- Categorize every test case from every feature's test plan — don't only list the interesting ones.
  A case with no listed category is an unaudited gap, not an implicit pass.
- Keep the automate-vs-wait rule itself in the "How to use this" intro rather than restating it per
  case — the per-case bullets should be terse (ID + one-line rationale), not a re-explanation of the
  taxonomy every time.
- Cross-reference bug IDs from each feature's `bug-report-<feature>.md`, don't restate the bug's full
  detail here — this file's job is the automate/wait decision, not the repro.
