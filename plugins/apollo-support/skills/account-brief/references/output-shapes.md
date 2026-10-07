# Output Shapes

Paste-ready templates. The renderer produces a Slack summary (`--slack`),
Markdown (default), HTML (`--html`), or every artifact at once (`--bundle DIR`)
from a JSON payload. Fields you did not verify render as
`unknown / needs checking`. No em dashes in any output.

## Full Brief Payload (default)

```json
{
  "mode": "brief",
  "data_window": "<window this brief covers, for example last 24h from 2026-08-19 09:00 PT>",
  "sources": [
    {"name": "Salesforce", "status": "ok"},
    {"name": "Snowflake", "status": "unavailable", "impact": "<which fields are unverified as a result>"},
    {"name": "Intercom", "status": "partial", "impact": "<what was and was not read>"}
  ],
  "caveats": [
    "<freshness or scope note, for example: Intercom pulled at 09:00 PT. Conversations after that are not included.>"
  ],
  "account": {
    "name": "<account name>",
    "id": "<account id>",
    "domain": "<domain>",
    "am": "<account manager>",
    "csm": "<csm>",
    "plan": "<plan>",
    "arr": "<arr>",
    "renewal_date": "<YYYY-MM-DD>"
  },
  "health": {
    "status": "<green/yellow/red or short label>",
    "renewal_risk": "<risk label>",
    "csat": "<recent csat>",
    "usage_trend": "<trend label>",
    "notes": "<short note>"
  },
  "open_tickets": [
    {"id": "<id>", "subject": "<subject>", "severity": "<P0/P1/P2>", "status": "<status>", "age_days": 0, "owner": "<owner>"}
  ],
  "red_flags": [
    {"tier": "P0", "signal": "<signal name>", "detail": "<value that crossed threshold>", "source": "<query or field>"}
  ],
  "recent_activity": [
    {"when": "<when>", "summary": "<what happened>", "source": "<source>"}
  ]
}
```

Rendered Markdown sections, in order: a `# Account Brief: <name>` header with the
account metadata as a bullet list, `## Data Coverage And Caveats`,
`## Health Summary` (status, renewal risk, CSAT, usage trend, notes),
`## Open Support Tickets` (a table of id, subject, severity, status, age,
owner), `## Red-Flag Signals` (bullets sorted P0 first, each as
`**[P0] <signal>**: <detail> (source: <source>)`), and `## Recent Activity`
(bullets of `**<when>:** <summary> (source: <source>)`).

## Sources And Caveats

`sources` and `caveats` drive the coverage block that opens every format.

- `status` of `ok`, `available`, or `verified` counts as clean. Anything else
  (`unavailable`, `partial`, `not_queried`, or a free-text status) raises a
  caveat and a `:warning:` marker in Slack.
- List every source you consulted, including the clean ones. That is what lets
  the renderer say "all 3 data sources returned" instead of staying silent,
  which reads as full coverage whether or not it was.
- `impact` should name the fields a reader should not trust, not restate the
  failure. "plan, ARR, renewal date are unverified" beats "query failed".
- Use `caveats` for anything a status cannot carry, most often freshness: when a
  source was pulled and what a later arrival would change.
- Omitting `sources` entirely is not neutral. The renderer says coverage was not
  recorded and tells the reader to treat every field as unverified.

## Daily Ticket Summary (`--daily`)

Use the same payload with `"mode": "daily"`. The heading becomes
`# Daily Ticket Summary: <account name>`. Scope `open_tickets` to the window,
put counts by severity and status plus the net-new vs aging breakdown in
`health.notes`, and list net-new tickets and status changes in
`recent_activity`. State the exact window (for example, "last 24h from
2026-08-19 09:00 PT") in `health.status`.

## Empty States

Literal placeholders, never replaced with invented rows:

- No open tickets: `No open support tickets recorded.`
- No red flags: `No red-flag signals recorded.`
- No recent activity: `No recent activity recorded.`

An empty state means the source returned nothing (or was not queried), not that
you should guess.

## HTML

Add `--html` to any render for a self-contained HTML document with the same
sections and tier-colored red flags. It embeds no external assets.

## Slack

Add `--slack` for a concise Slack mrkdwn summary, or `--bundle DIR` to write
Markdown, HTML, PNG, and the Slack summary at once and print a manifest. The
Slack summary is deliberately shorter than the brief: it carries the coverage
caveats, health, top red flags, and top open tickets, capping long lists with a
`+N more in the attached brief` line. Use `--attach NAME` (repeatable) to name
the files cited in its footer.

Slack uses mrkdwn, not Markdown: `*bold*` rather than `**bold**`, no `#`
headers, and no pipe tables. Post the `--slack` output as the message text and
attach the artifacts. Never paste the HTML or the full Markdown brief into a
Slack message. See `references/slack-delivery.md`.
