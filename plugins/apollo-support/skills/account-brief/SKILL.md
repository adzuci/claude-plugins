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
how to fetch it), and `references/output-shapes.md` (paste-ready templates).

## Rendering

Assemble a JSON payload with only the fields you verified, then render:

```bash
python3 scripts/render_account_brief.py --json <payload.json>          # Markdown
python3 scripts/render_account_brief.py --json <payload.json> --html   # HTML
```

The renderer fills any missing field with `unknown / needs checking`, shows
literal empty-state lines when a section has no rows, and sorts red flags P0
first. It never invents rows.

## Core Behavior

- Read-only. Query sources, never mutate them.
- Never fabricate account state, ticket counts, or red flags. Trace every flag to
  an explicit source value; if you cannot, mark it `unknown / needs checking`.
- Separate known facts, tool-backed findings, inferences, and unknowns.
- Label anything from a paste (not a live query) as Unverified.
- No em dashes in any output. Use a comma, colon, period, or parentheses.
- This skill is meant to run in the AM's own authenticated environment. A hosted
  or tagged Claude session cannot reach Snowflake, Salesforce, or the Intercom
  MCP; in that case, render from operator-pasted data and mark it Unverified.
