# Daily Report

Use this reference for `report` at the end of a support shift or day.

## Inputs

Accept Intercom links, Granola notes, transcript files, pasted notes, or a normalized JSON file of call records.

### Source Coverage

For `report`, do both a Granola pass and an Intercom MCP pass before deciding the day is complete. Granola often has call notes and coaching context; Intercom is the source for chats, voice interactions, assignee state, call summaries, and conversations that were never recorded in Granola.

1. Resolve the exact report date or shift window first. If the user says "today" or "yesterday", convert that to an absolute date in the user's timezone.
1. Granola pass:
   - Use `mcp__Granola__list_meetings` or `mcp__Granola__query_granola_meetings` for the date window.
   - Fetch relevant details with `mcp__Granola__get_meetings` and transcripts with `mcp__Granola__get_meeting_transcript` when available.
   - Treat missing Granola meetings as missing call-note coverage only, not as proof there were zero support interactions.
1. Intercom MCP pass:
   - Use `mcp__Intercom__get_conversation` for any provided Intercom URL or conversation ID.
   - If an Intercom search/list tool is available, search the date window for assigned, participated, closed, snoozed, and open conversations before finalizing counts.
   - Extract customer/company, assignee, created/updated/closed times, state, tags, `statistics`, `source.url`, `conversation_parts`, and any `call_summary` parts.
   - Treat `call_summary` as an AI-generated summary, not a verbatim transcript. If a downloadable transcript link is visible, surface it in methodology or follow-ups.
1. Merge and deduplicate records by Intercom conversation ID/URL first, then customer/account plus time when no ID is available. Prefer Intercom for conversation counts/status and Granola for call coaching/transcript detail.
1. If either Granola or Intercom is unavailable, say exactly which source is missing in Methodology and do not state a zero-interaction verdict unless all required sources were checked or the user provided a complete normalized input.

### Go Faster

- If a transcript or pasted chat/call log is already provided, treat it as the source of truth. Do not re-fetch the same conversation from Intercom or Granola just to confirm what the transcript already shows.
- Only run live lookups (Intercom, Granola, Glean) for facts the transcript does not contain (account state, escalation status, follow-up owners).
- Do not hand-summarize each transcript line. Pass the raw transcript (or pre-split entries) into the `transcript`/`timeline` field and let the renderer build the collapsible timeline mechanically. Spend model effort only on the summary fields.

### Per-Call Fields

Each `calls[]` record may include a verbatim conversation for the collapsible timeline:

- `transcript`: raw string. Lines shaped like `[00:00:02] Speaker 1: "text"` are parsed into time/speaker/text automatically; other lines are kept verbatim so nothing is dropped. Works for both call transcripts and chat logs.
- `timeline`: pre-structured list of `{time, speaker, text}` entries. Use when you already have clean turns (e.g. Intercom chat parts). Takes precedence over `transcript`.
- `timeline_label` (optional): heading for the collapsible section. Defaults to "Full chat & call timeline".
- `channel` (optional): `call`, `chat`, `screenshare`, `shadow`, or another short source label.
- `start_time` / `end_time` (optional): local report-window clock labels such as `09:30` or `2:05 PM`.
- `duration_minutes` or `duration_label` (optional): call/chat duration for visual activity summaries.
- `included_call` (optional): boolean that marks whether the record included a customer call. Use this to distinguish chat-only conversations from voice/screenshare calls.
- `csat` (optional): score/rating object or short label. Leave empty when CSAT was unavailable rather than treating it as zero.

### Day-Level Fields

The normalized JSON may include these optional report-level fields:

- `shift`: `{start, end, timezone, label}`. Render this even when exact interaction times are partial, and label inferred shift bounds in Methodology.
- `activity_timeline`: list of `{label, customer, channel, start_time, end_time, duration_minutes, duration_label, status, included_call, csat}` entries. If omitted, the renderer derives a timeline from `calls[]` metadata.
- `cx_metrics`: list of teammate metric rows with `chats_started`, `calls_started`, `screenshare_offered`, `avg_handle_time`, `avg_call_duration`, `avg_frt`, `max_frt`, `csat_score`, `csat_rated`, and `csat_total`. Use explicit missing labels such as `Not captured` when Intercom/CX exports are unavailable.
- `csat_summary`: `{score, rated, total, label}` or a short string for CSAT/survey score. Use `label: "Not captured"` when unavailable.
- `cx_score_summary`: `{score, rated, total, label}` or a short string for Intercom's `CX Score rating`; keep separate from CSAT.
- `shadow_info`: separate observation/shadowing/coaching records. These do not increase the handled-interactions count unless the user actually owned the customer conversation.
- `ideas_generated`: product, process, docs, or skill ideas produced during the shift. Include source/context and next action when known.

When `--html` is passed, run:

```bash
python3 scripts/render_daily_report.py --input <records.json> --date <YYYY-MM-DD> --output <report.html>
```

## Report Sections

- Verdict: one-sentence day summary.
- Shift window: start/end/timezone, with inferred bounds labeled in Methodology.
- KPIs: calls/chats handled, resolved/partial/escalated counts, follow-ups, product signals, calls included, and CSAT coverage.
- Activity timeline: visual sequence of conversations/chats/calls with call inclusion and duration when known.
- CX metrics: chats started, calls started, screenshares offered, Handle Time vs. Call Time, Avg FRT / Max FRT, and CSAT.
- Per-call summaries: customer, issue, outcome, next action, escalation, product signal, channel, duration, and CSAT when available.
- Full chat & call timeline: collapsed by default, rendered from `transcript`/`timeline` so reviewers can expand the verbatim conversation without bloating the summary.
- Shadow info: separate section for shadowing, observation, training, and coaching context.
- Ideas generated: separate section for product, process, docs, and skill ideas created during the shift.
- Cross-call themes: customer pain, technical friction, escalation patterns, macro opportunities.
- Coaching opportunities: momentum, ownership, clarity, uncertainty handling, call framing.
- Open follow-ups: owner, next action, source link.
- Methodology: sources used, missing tools, inferred times, and limitations.

## Rules

- Do not invent call counts or outcomes.
- Never conclude "no interactions" from Granola alone. Check Intercom MCP coverage or label Intercom as unavailable.
- Label missing source coverage clearly.
- Keep customer-identifying details minimal in HTML unless needed for handoff.
- A report from pasted notes or normalized JSON is valid when the user says it is complete; otherwise list missing Granola/Intercom coverage in Methodology.
