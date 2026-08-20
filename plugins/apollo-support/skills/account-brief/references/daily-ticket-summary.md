# Daily Ticket Summary Mode

Run this with `--daily`. It summarizes the last ~24 hours of support tickets for
the target, grouped by severity and status, surfacing net-new and aging tickets.
When the target is an AM, summarize their whole book; when it is a domain or an
account id, scope to that one account.

## Scope

- Default window is the last 24 hours, measured from now in the operator's
  timezone. State the exact window you used at the top of the summary.
- "Net-new" means a ticket created inside the window. "Aging" means an open
  ticket whose age crosses a threshold in `references/red-flag-signals.md`.
- This mode is read-only and follows the same four-bucket and no-em-dash rules as
  `references/account-brief-mode.md`.

## Steps

1. Classify the target and build the plan:
   ```bash
   python3 scripts/resolve_target.py "<target>" --json
   ```
1. Pull tickets from Snowflake for the window (see `references/data-sources.md`).
   For an AM target, resolve the book in Salesforce first, then query tickets for
   the book's account ids. If Snowflake is unavailable, ask the operator to paste
   the ticket export and mark the summary Unverified.
1. Group the tickets:
   - by severity (P0, P1, P2, and lower), and
   - by status (new, open, pending, resolved-in-window).
1. Separate net-new tickets from carried-over open tickets, and flag any aging
   past SLA against `references/red-flag-signals.md`.
1. Assemble the payload with `"mode": "daily"` and render:
   ```bash
   python3 scripts/render_account_brief.py --json <payload.json>          # Markdown
   python3 scripts/render_account_brief.py --json <payload.json> --html   # HTML
   ```

## What To Surface

- Counts by severity and by status, with the window stated.
- Net-new tickets opened in the window, highest severity first.
- Aging tickets that crossed an SLA threshold since the last check.
- Any account whose ticket volume spiked versus its recent baseline (call out the
  baseline you compared against, or mark the comparison Unverified).
- A short "nothing net-new" line when the window is genuinely empty. Never state
  zero tickets unless you actually queried the source or the operator confirmed a
  complete paste.

See `references/output-shapes.md` for the paste-ready daily template.
