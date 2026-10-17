---
name: eol-calendar
description: Refresh Apollo's support-windows (EOL) calendar Google Sheet for OS, GKE, databases, languages, and tooling.
argument-hint: '[--status] [--push SHEET_ID [--impersonate SA] [--dry-run]]'
disable-model-invocation: true
---

# EOL Calendar

Run this skill as `/apollo-eng-devops:eol-calendar [args]`.

Draws a month-by-month bar calendar of support/EOL windows for the stack
DevOps runs, plus an `Apollo Status` tab that flags what is already past EOL.
Adapted from
[openedx/repo-tools barcalendar.py](https://github.com/openedx/repo-tools/blob/master/barcalendar.py).
Dates come from [endoflife.date](https://endoflife.date); `products.yaml` (next
to this file) says which versions Apollo runs, and can override any date.

## Refresh Workflow

1. Check `products.yaml` against reality. Re-verify anything you suspect changed
   (GKE from `kubectl-readonly`/the cluster inventory, Mongo/Postgres/Redis from
   their consoles or Terraform, Ruby/Node from leadgenie `.ruby-version` and
   `.nvmrc`). Set `running: true` for versions in prod/stage, `planned: true`
   for committed upgrade targets, `unverified: true` when the version is not
   recorded anywhere (shows on the status tab only). Never guess a version.

1. Run the script from this skill's directory (needs `requests`, `pyyaml`).
   Warnings, including drift between `products.yaml` and endoflife.date, go to
   stderr:

   ```bash
   python scripts/eol_calendar.py --status      # markdown table of running/planned versions
   python scripts/eol_calendar.py > support_windows.gs
   ```

1. Apply it to the Sheet, either way:

   - **Paste (no auth):** Sheet → Extensions → Apps Script → paste
     `support_windows.gs` → run `makeApolloSupportWindows`. If the Sheet is a
     copy of the Open edX original, run `removeOpenEdxTabs` once afterward.
   - **Push (Sheets API):** `python scripts/eol_calendar.py --push SHEET_ID --dry-run`
     first, then drop `--dry-run`. Add `--drop-openedx-tabs` once for an Open
     edX copy. Auth setup is in [references/sheets-auth.md](references/sheets-auth.md);
     a plain API key cannot write to a Sheet.

1. Report: how many running versions are past EOL or within 6 months, what
   changed since the last run, and any `unverified` rows still open.

## Output

- `Support Windows` tab: bars per version; running versions bold and outlined,
  planned versions in the solid color, other supported versions lighter, a
  dashed line at today's month.
- `Apollo Status` tab: product, version, running/planned, EOL date, state
  (`SUPPORTED`, `EOL < 6 MO`, `EOL PASSED`, `ROLLING`, `LIKELY EOL`, `UNKNOWN`),
  note, source.

## Rules

- `--push` overwrites the `Support Windows` and `Apollo Status` tabs. Use
  `--dry-run` first and confirm the Sheet ID is the intended one.
- `--drop-openedx-tabs` deletes tabs by name; only pass it for an Open edX copy.
- Never print or commit credentials. Impersonation (no key file) is the
  supported path.
- State which rows came from endoflife.date and which are manual or unverified.

Development validation is in [references/development.md](references/development.md).
