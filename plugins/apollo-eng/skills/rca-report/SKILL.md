---
name: rca-report
description: Status report over Apollo's RCA (Post Mortems) database in Notion, with optional surface filter. Run via /apollo-eng:rca-report.
disable-model-invocation: true
---

# RCA Report

Produce a Slack-friendly status report over Apollo's RCA (Post Mortems) database in Notion: what's new, what was presented, and what needs attention. Optionally filter to one surface: `/apollo-eng:rca-report DevOps`. This is a database-wide report — for reviewing a single document's quality, use `/apollo-eng:rca-doc-review <url>` instead.

## Workflow

1. **Locate the database.** The Post-Mortems database is `collection://f959018e-ffab-4ede-ab7b-0b9d125a033f`. Use whatever Notion access the session has (Notion MCP connector, or the Notion REST API at api.notion.com with an integration token). If neither is available, stop and tell the user exactly that. Never fabricate results.

1. **Schema** (verified 2026-07-07 — no runtime discovery needed):

   - **`Surface`** — Relation to Teams DB (`collection://2873c25d-ea13-4cea-bec7-72a7b77a9e02`). Filter by page ID of the target team.
   - **`Status`** — Select: `Drafting`, `Written Complete`, `Complete`, `Action Items Pending`.
   - **`Presented`** — Checkbox (`__YES__` / `__NO__`).
   - **`Meeting / Review Date`** — Date (presentation date).
   - **`Created time`** — Built-in Notion timestamp (use for age calculation).
   - **`Author`** — Person (owner/DRI).

   Known surface → Teams DB page ID mappings:

   - `Eng - Infra + SRE/DevOps` → `bc8fedb3e96e467492047be66740df91`

   If a requested surface isn't listed above, query the Teams DB to find the matching page ID at runtime and proceed — do not attempt to modify this file.

1. **Query and bucket.** Default the reporting window to the last 7 days (accept an explicit window if the user gives one). Bucket RCAs into:

   - **New**: created within the window.
   - **Presented**: reached a presented/closed/done state within the window (or, for a checkbox/date property, presented within the window).
   - **Needs attention**: not yet presented and older than 14 days; or missing an owner; or clearly a stub (empty/near-empty page); or has open/overdue action items if the schema exposes them. Give each item a one-line reason.

1. **Apply the surface filter** (if an argument was given). Match the surface property case-insensitively in every bucket, including multi-select membership. If the discovered surface property has no matching option, list the valid options and ask the user to pick one — do not return an empty report.

1. **Output the report.** Compact Slack-friendly markdown:

   - Header with the reporting window and surface filter (if any).
   - The three sections with counts. For **New** and **Presented**, each item as plain text: `title · owner · age`. For **Needs Attention**, each item as a Notion page link: `<notion-page-url|title> · owner · age` (Slack link syntax), followed by a one-line reason on the same bullet.
   - An explicit "No new RCAs this week"-style line for any empty section.
   - If Slack access is available, add a section **"Incident threads that may warrant an RCA"** listing recent incidents from `#incident-response-sev0-sev1` that have no matching RCA in the database. Only surface incidents where the surface's team members were clearly active responders or the incident was explicitly routed to the team (a passing mention or a brief heads-up does not qualify). Omit low-signal items: infra-adjacent issues where the team was consulted rather than owning the incident, cert/DNS issues resolved same-day without customer impact, and anything still actively in the response phase. One line per incident: date · title · why it may need an RCA · Slack thread link.
   - Suggest `/apollo-eng:rca-doc-review <url>` wherever a quality review would help — attach a one-line suggestion to new RCAs that haven't been reviewed yet, to needs-attention items flagged for quality or completeness (stub, missing sections, weak action items), and to any RCA about to be presented; or roll these into a single "Suggested next steps" line at the end.
   - End with a "Test in Slack" line: `_Paste the above into Slack to verify formatting renders correctly._` This reminds the user to spot-check link rendering and markdown before sharing the report.

## Workflow Contract

- **Deterministic (this skill provides)**: bucket definitions, default 7-day window, 14-day needs-attention threshold, report structure, surface-matching rules.
- **Agent judgment**: stub detection, needs-attention reasons, window interpretation when the user gives one, surface → page ID lookup for unmapped surfaces.
- **Human (report reader)**: follows up on flagged RCAs, decides what action each needs-attention item gets.

## Safety

Read-only. Never create, edit, archive, or comment on Notion pages or databases — this skill only queries and reports. If Notion access is missing or a query fails, say so plainly instead of inventing data.

## Checklist

- [ ] Every needs-attention item has a one-line reason and a Slack-linked Notion page URL
- [ ] Empty sections say so explicitly
- [ ] "Test in Slack" reminder included at end of output
- [ ] No Notion pages were modified

## Further Reading

- `/apollo-eng:rca-doc-review` — single-document RCA quality review, the follow-up the report suggests for unreviewed, flagged, or soon-to-be-presented RCAs
- `/apollo-eng:create-rca` — draft a missing RCA into the Post Mortems database from Slack thread(s), a Zoom transcript, and the Jira incident
- [Notion API: query a database](https://developers.notion.com/reference/post-database-query)
