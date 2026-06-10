# QA Contract

Before delivery, run browser QA and data integrity checks appropriate to the artifact. Store evidence in the output folder when generating the default dashboard shape.

## Required Checks

- Confirm `index.html` does not load external network resources.
- Confirm the browser reports no console errors or page errors.
- Confirm desktop width around 1440px has no horizontal overflow.
- Confirm mobile width around 390px has no horizontal overflow.
- Confirm Daily, Weekly, and Monthly controls change rendered counts and labels.
- Confirm the grid, trend, and breakdown table update when the timeframe control changes.
- Confirm selectable date controls use one unambiguous date language: visible month/range buttons plus explicit US-format (`MM/DD/YYYY`) `From`/`To` fields that filter all major views.
- Confirm there are no dropdown-only date selectors or duplicate native `type=date` inputs that can render in a different locale order from the US text fields.
- Confirm the default selected date range is the previous calendar month bounded by actual available measured data.
- Confirm daily burn renders as a Sunday-to-Saturday calendar with weekday headers and exposes full US dates on hover or accessible labels.
- Confirm top KPI labels match the agreed visible metrics.
- Confirm the third top KPI is `Runs`, not `Sessions`, and that it sums measured local runs. Claude subagent transcript files with usage should contribute to run counts while token totals remain deduped.
- Confirm no visible unverified chat estimate or not connected source appears as measured.
- Confirm source chips appear only for measured sources.
- Confirm source split cards, driver bars, trend totals, breakdown totals, and largest-row tables use only exact or measured rows.
- Confirm source-specific token columns appear in the breakdown table when multiple measured sources are included.
- Confirm `source-ledger.md` explains included, missing, and excluded sources.

## Data Integrity Checks

- Compare top KPI totals against `usage-data.json`.
- Verify source confidence values are one of: exact, measured, inferred, estimated, not connected.
- Verify inferred, estimated, and not connected rows are excluded from top KPI totals.
- Verify the dashboard date range comes from discovered data, not a hardcoded placeholder.
- Verify largest measured token rows and trend totals reconcile with the normalized session model.
- Verify daily calendar cells reconcile with the selected date range while preserving regular Sunday-to-Saturday calendar alignment, including leading/trailing empty days.
- For Claude, verify KPIs follow the Claude inclusion rule in `SKILL.md` Source Discovery, especially transcript cache token exclusion.
- For run counts, verify source ledger and `usage-data.json` distinguish deduped token rows from measured local runs when Claude transcript subagents are present.

## Evidence

For the default output shape, write:

- `evidence/browser-qa.json` with viewport, console, network, overflow, and interaction results.
- `evidence/dashboard-desktop-1440.png`.
- `evidence/dashboard-mobile-390.png`.

If a check cannot be run, state exactly why in the final response and in `browser-qa.json`.
