# Notion Connector Reference

Use this reference when the user wants the skill to create the Ideation Log entry in Notion, or when the observation context may live in meeting notes.

## Ideation Log Target

- Database URL: <https://app.notion.com/p/apolloio/76d67d55da054cb3b9b22a68e98cd44a?v=f627bb7835a5465fbb6c3e789c869ddf&source=copy_link>
- Data source ID, if already available from a prior fetch: `8687283d-1e9b-4ef4-a3af-f0cc72f112b2`

Always fetch the database before creating pages if the connector supports it. Use the returned schema as the source of truth for exact property names, allowed select values, and whether a property is single-select or multi-select.

## Creating the Entry

Use the Notion connector to create a page under the Ideation Log data source. If the connector is unavailable, draft the entry and recap with the database link so the user can paste it manually.

Set these defaults unless the user says otherwise:

- `Status`: `New`
- `Linked KR`: `KR 1.4 - Ideation Capture`
- `Escalated to Product?`: unchecked
- `Date`: today's date

Use a compact page body:

```markdown
## Observation
<what happened, with the specific customer/support evidence>

## Why it matters
<customer, support, product, or engineering impact>

## Suggested next step
<owner/team/action>
```

## Clarification Rule

If the observation lacks enough detail to choose core fields or make the entry actionable, ask one focused clarification question before creating the Notion page.

Ask for the missing field that most affects routing:

- Product area, if ownership is unclear.
- Observed customer/support behavior, if the evidence is vague.
- Impact, if prioritization is impossible.
- Likely owner or next step, if the entry cannot be routed.

## Granola MCP

Use Granola MCP only as an optional context source when available. Do not make it a dependency for the skill.

Use Granola when:

- The user says the observation came from meeting notes, Granola notes, support rotation debriefs, or a recorded discussion.
- The user asks you to find support-rotation ideas from recent notes.
- You need exact wording from a conversation before writing the observation.

Suggested Granola flow:

1. Use `query_granola_meetings` for open-ended searches across meeting notes.
1. Use `list_meetings` and `get_meetings` when the user gives a date range or likely meeting title.
1. Use `get_meeting_transcript` only when exact quotes or verbatim wording are needed.

When Granola returns citation links, preserve them in your reasoning and include the relevant source link in the recap when it helps the user verify the observation. Do not block entry creation if Granola is unavailable or returns no relevant notes; ask the user for the missing observation details instead.
