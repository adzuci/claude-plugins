# HTML Report Reference

Use this reference only when `/apollo-eng-devops:renewal-radar --html` is passed.

## Output Contract

Always print the terminal digest from step 5 first. Then write a local static HTML report and print its absolute path.

Default path pattern:

```text
/tmp/renewal-radar-report-YYYYMMDD-HHMMSS.html
```

If the environment cannot write to `/tmp`, write to the current working directory and say why.

## Content

The HTML report must contain the same information as the terminal digest — this is a rendering of the same data, not a different or expanded report:

- Title: `Renewal Radar — <resolved department path>`
- Generated timestamp
- Window (start → end, N days) and status filter
- The `Contractors:` filter state, including any dropped-row count and names
- Every bucket the terminal digest showed (`Act now`, `Plan`, `Watch`), as a table: vendor, agreement (linked), amount, end date, days remaining, renewal status, owner, department
- The `†` vendor-sweep-recovered marker and its footnote, when any row carries one
- The "unconfirmed — other departments" table, visually distinct (e.g. a muted panel), when the permission-denied fallback ran
- The "PO-only renewals (no visible Agreement record)" table, visually distinct from the Agreement tables above it, when step 3.3 found one
- The "tracked vendors with no visible agreement" list from the vendor sweep, when it ran
- The scope caveat
- The notice-deadline caveat
- A one-line note on whether department read was `ok` or `denied` for this run

Do not add data, totals, or commentary that isn't in the terminal digest. If a bucket was empty and its heading was omitted from the terminal output, omit it from the HTML too.

## Format

Keep the report dependency-free, matching this plugin's other `--html` skills (see `check-apdex/references/html-report.md`):

- Plain HTML and inline CSS only
- No external assets, no JavaScript required
- Escape all dynamic text (vendor names, agreement names, department paths) before writing it into HTML — this data comes from Zip records other people filed, not from the caller
- Compact operational styling: readable tables, restrained colors, no marketing/hero layout
- Urgency buckets may use a light background tint (e.g. amber for "Act now") but keep it subtle — this is an operational report, not a dashboard

## Privacy

The same guardrails from `SKILL.md` apply to the HTML file on disk: no vendor tax IDs, bank/remittance details, or personal contact information, and no commercial free text (descriptions, business cases, PO memos). A file written to `/tmp` can outlive the conversation — do not write anything into it that the terminal digest itself wouldn't show.
