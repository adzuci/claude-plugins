# Account Brief Mode

This is the default workflow. It produces a lightweight, account-focused brief
for an Account Manager: current health, open support tickets, red-flag signals,
and recent activity for one account (or a book of accounts when the target is an
AM).

## Read-Only Discipline

- Never mutate any source. No writes to Salesforce, Snowflake, or Intercom. No
  ticket edits, no field updates, no closing or reassigning anything.
- Never fabricate account state. If a value is not in a source you actually
  queried, render it as `unknown / needs checking`.
- Separate what you know into four buckets and keep them distinct in output:
  known facts (given by the operator), tool-backed findings (returned by a live
  source this run), inferences (your reasoning, labeled as such), and unknowns.
- No em dashes in any output. Use a comma, colon, period, or parentheses.
- Trace every claim to its source. A ticket count, a renewal risk, or a red flag
  must point to the field or query it came from, or be marked Unverified.

## Steps

1. Classify the target and build the read-only lookup plan:
   ```bash
   python3 scripts/resolve_target.py "<target>" --json
   ```
   The classifier returns `am`, `domain`, or `account_id`, and the plan lists
   which OPTIONAL sources to query and in what order.
1. Check which live sources are reachable in this environment:
   ```bash
   python3 scripts/check_dependencies.py --json
   ```
   Every source is optional. When one is missing, keep going and mark the fields
   it would have supplied as Unverified.
1. Pull sources per the plan (see `references/data-sources.md`):
   - Salesforce for account identity and health fields (and the AM's book when
     the target is an AM).
   - Snowflake for support tickets (open and recent).
   - Intercom MCP for company-level conversation context, when available.
1. Assemble a single JSON payload with the fields you actually retrieved. Leave
   out anything you did not verify; the renderer fills gaps with
   `unknown / needs checking` rather than inventing values.
1. Score red-flag signals against `references/red-flag-signals.md`. Only raise a
   flag when a concrete source value crosses its documented threshold.
1. Render the brief:
   ```bash
   python3 scripts/render_account_brief.py --json <payload.json>          # Markdown
   python3 scripts/render_account_brief.py --json <payload.json> --html   # HTML
   ```

## Payload Shape

See `references/output-shapes.md` for the paste-ready templates. In short:

```json
{
  "mode": "brief",
  "account": {"name": "", "id": "", "domain": "", "am": "", "csm": "", "plan": "", "arr": "", "renewal_date": ""},
  "health": {"status": "", "renewal_risk": "", "csat": "", "usage_trend": "", "notes": ""},
  "open_tickets": [{"id": "", "subject": "", "severity": "", "status": "", "age_days": 0, "owner": ""}],
  "red_flags": [{"tier": "P0", "signal": "", "detail": "", "source": ""}],
  "recent_activity": [{"when": "", "summary": "", "source": ""}]
}
```

When the target is an AM with a book of accounts, produce one payload per account
and render a brief for each, or lead with the accounts carrying the highest-tier
red flags. Say plainly which accounts you covered and which you could not reach.

## Environment Note

This skill is meant to run in the AM's own authenticated environment, where the
Snowflake and Salesforce CLIs and the Intercom MCP are connected. A hosted or
tagged Claude session cannot reach those live sources. In that case, ask the
operator to paste the data, render from the pasted payload, and mark every
tool-backed field Unverified.
