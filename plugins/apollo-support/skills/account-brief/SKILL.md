---
name: account-brief
disable-model-invocation: true
description: Build a read-only account brief and daily support-ticket summary that flags red-flag signals for Account Managers. Run via /apollo-support:account-brief.
---

# Account Brief

Use this skill to give an Account Manager a lightweight, account-focused report:
current health, open support tickets, tiered red-flag signals, and recent
activity. It runs from an AM name/email, a domain, or an account id, and can
produce either a full brief (default) or a daily ticket summary (`--daily`).

It is strictly read-only. It never writes to Salesforce, Snowflake, or Intercom,
never edits or closes tickets, and never fabricates account state. Any value it
did not retrieve from a source it actually queried is rendered as
`unknown / needs checking`, and any value from a paste (not a live query) is
labeled Unverified.

## Usage

```text
/apollo-support:account-brief [target] [--daily] [--html]
```

- `target`: an AM (name or @apollo.io email), a domain, or an account id.
- `--daily`: daily ticket summary mode instead of the full brief.
- `--html`: render a self-contained HTML document instead of Markdown.

## Slack Is The Default Delivery

When this session answers into Slack (a Claude tag, a thread reply, or an
invocation from Slack), deliver a concise Slack summary as the message text plus
the rendered artifacts as attachments. **Never paste raw HTML or the full
Markdown brief into a Slack message.** Slack does not render HTML and does not
speak Markdown, so both arrive mangled.

Build every artifact in one call:

```bash
python3 scripts/render_account_brief.py --json <payload.json> --bundle ./brief-out
```

It writes Markdown, HTML, PNG, and the Slack summary, then prints a JSON
manifest. Post `slack_text` verbatim as the message and upload `attachments`
in order (PNG first, because Slack previews it inline). If the PNG could not be
rendered, `png` is `null` and `png_detail` says why: attach the HTML alone and
say the image failed.

Attachments are best-effort; the summary is the deliverable. `slack_text` is
written to stand alone, so if an upload fails or you cannot confirm it landed,
still post the summary, say the attachment did not upload, and give the local
file path. Never claim a file was attached without confirming it.

Full contract, including caveat placement and freshness rules:
`references/slack-delivery.md`.

Outside Slack (a terminal session), Markdown to stdout remains the default.

## Routing

Run `python3 scripts/check_dependencies.py --json` first when a mode depends on
live data or a source is missing. Every live source is OPTIONAL; continue with
pasted data and mark those fields Unverified when a source is unavailable.

Classify the target and get a read-only lookup plan:

```bash
python3 scripts/resolve_target.py "<target>" --json
```

`classify_target` returns `am`, `domain`, or `account_id`. `build_lookup_plan`
describes which sources to query. The script makes no network or MCP calls; the
agent executes the plan.

| Mode | Use | Required reference |
| --- | --- | --- |
| brief (default) | Full account brief for a target | `references/account-brief-mode.md` |
| `--daily` | Last ~24h support-ticket summary for the target or the AM's book | `references/daily-ticket-summary.md` |

Supporting references: `references/red-flag-signals.md` (tiered P0/P1/P2 catalog
and thresholds), `references/data-sources.md` (where each field comes from and
how to fetch it), `references/output-shapes.md` (paste-ready templates), and
`references/slack-delivery.md` (Slack message and attachment contract).

## Rendering

Assemble a JSON payload with only the fields you verified, then render:

```bash
python3 scripts/render_account_brief.py --json <payload.json> --bundle ./out   # all artifacts (Slack default)
python3 scripts/render_account_brief.py --json <payload.json>                  # Markdown
python3 scripts/render_account_brief.py --json <payload.json> --slack          # Slack mrkdwn summary
python3 scripts/render_account_brief.py --json <payload.json> --html           # HTML
python3 scripts/render_png.py --html <brief.html> --output <brief.png>         # PNG on its own
```

The renderer fills any missing field with `unknown / needs checking`, shows
literal empty-state lines when a section has no rows, and sorts red flags P0
first. It never invents rows.

Always populate `sources` and `caveats` in the payload, including the sources
that came back clean. The renderer puts data-coverage caveats at the top of
every format, above the numbers they qualify, and states plainly when no
coverage was recorded at all. See `references/output-shapes.md`.

PNG rendering needs Playwright or Chrome. When neither is installed the PNG is
skipped with a reason and the rest of the bundle still renders.

## Core Behavior

- Read-only. Query sources, never mutate them.
- Never fabricate account state, ticket counts, or red flags. Trace every flag to
  an explicit source value; if you cannot, mark it `unknown / needs checking`.
- Separate known facts, tool-backed findings, inferences, and unknowns.
- Label anything from a paste (not a live query) as Unverified.
- Lead with missing-source caveats, never bury them. If Salesforce, Snowflake,
  or Intercom was unreachable, that belongs above the numbers it affects.
- State the generation time and data window. When a lagging source lands after
  the run, render a new brief that supersedes the old one rather than restating
  earlier numbers as current.
- No em dashes in any output. Use a comma, colon, period, or parentheses.
- This skill is meant to run in the AM's own authenticated environment. A hosted
  or tagged Claude session cannot reach Snowflake, Salesforce, or the Intercom
  MCP; in that case, render from operator-pasted data and mark it Unverified.
