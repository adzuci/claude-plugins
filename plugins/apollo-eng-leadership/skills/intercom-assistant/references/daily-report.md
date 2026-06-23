# Daily Report

Use this reference for `report` at the end of a support shift or day.

## Inputs

Accept Intercom links, Granola notes, transcript files, pasted notes, or a normalized JSON file of call records.

### Go Faster

- If a transcript or pasted chat/call log is already provided, treat it as the source of truth. Do not re-fetch the same conversation from Intercom or Granola just to confirm what the transcript already shows.
- Only run live lookups (Intercom, Granola, Glean) for facts the transcript does not contain (account state, escalation status, follow-up owners).
- Do not hand-summarize each transcript line. Pass the raw transcript (or pre-split entries) into the `transcript`/`timeline` field and let the renderer build the collapsible timeline mechanically. Spend model effort only on the summary fields.

### Per-Call Fields

Each `calls[]` record may include a verbatim conversation for the collapsible timeline:

- `transcript`: raw string. Lines shaped like `[00:00:02] Speaker 1: "text"` are parsed into time/speaker/text automatically; other lines are kept verbatim so nothing is dropped. Works for both call transcripts and chat logs.
- `timeline`: pre-structured list of `{time, speaker, text}` entries. Use when you already have clean turns (e.g. Intercom chat parts). Takes precedence over `transcript`.
- `timeline_label` (optional): heading for the collapsible section. Defaults to "Full chat & call timeline".

When `--html` is passed, run:

```bash
python3 scripts/render_daily_report.py --input <records.json> --date <YYYY-MM-DD> --output <report.html>
```

## Report Sections

- Verdict: one-sentence day summary.
- KPIs: calls/chats handled, resolved/partial/escalated counts, follow-ups, product signals.
- Per-call summaries: customer, issue, outcome, next action, escalation, product signal.
- Full chat & call timeline: collapsed by default, rendered from `transcript`/`timeline` so reviewers can expand the verbatim conversation without bloating the summary.
- Cross-call themes: customer pain, technical friction, escalation patterns, macro opportunities.
- Coaching opportunities: momentum, ownership, clarity, uncertainty handling, call framing.
- Open follow-ups: owner, next action, source link.
- Methodology: sources used, missing tools, and limitations.

## Rules

- Do not invent call counts or outcomes.
- Label missing source coverage clearly.
- Keep customer-identifying details minimal in HTML unless needed for handoff.
- Make Granola optional. A report from pasted notes is valid.
