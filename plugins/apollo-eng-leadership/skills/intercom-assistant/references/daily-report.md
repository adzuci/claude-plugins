# Daily Report

Use this reference for `report` at the end of a support shift or day.

## Inputs

Accept Intercom links, Granola notes, transcript files, pasted notes, or a normalized JSON file of call records.

When `--html` is passed, run:

```bash
python3 scripts/render_daily_report.py --input <records.json> --date <YYYY-MM-DD> --output <report.html>
```

## Report Sections

- Verdict: one-sentence day summary.
- KPIs: calls/chats handled, resolved/partial/escalated counts, follow-ups, product signals.
- Per-call summaries: customer, issue, outcome, next action, escalation, product signal.
- Cross-call themes: customer pain, technical friction, escalation patterns, macro opportunities.
- Coaching opportunities: momentum, ownership, clarity, uncertainty handling, call framing.
- Open follow-ups: owner, next action, source link.
- Methodology: sources used, missing tools, and limitations.

## Rules

- Do not invent call counts or outcomes.
- Label missing source coverage clearly.
- Keep customer-identifying details minimal in HTML unless needed for handoff.
- Make Granola optional. A report from pasted notes is valid.
