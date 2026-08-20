# Output Shapes

Paste-ready templates. The renderer produces Markdown (default) or HTML
(`--html`) from a JSON payload. Fields you did not verify render as
`unknown / needs checking`. No em dashes in any output.

## Full Brief Payload (default)

```json
{
  "mode": "brief",
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
account metadata as a bullet list, `## Health Summary` (status, renewal risk,
CSAT, usage trend, notes), `## Open Support Tickets` (a table of id, subject,
severity, status, age, owner), `## Red-Flag Signals` (bullets sorted P0 first,
each as `**[P0] <signal>**: <detail> (source: <source>)`), and
`## Recent Activity` (bullets of `**<when>:** <summary> (source: <source>)`).

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
