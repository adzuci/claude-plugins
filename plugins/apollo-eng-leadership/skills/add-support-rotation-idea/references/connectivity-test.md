# Connectivity Test

Use this reference before a workflow reads external context, fetches Ideation Log rows, or creates an Ideation Log entry.

## Connector Requirements

| Connector | Requirement | Used For |
| --- | --- | --- |
| Notion | Required for create and report modes | Fetch Ideation Log schema, create entries, fetch report rows |
| Glean | Optional, required only for research-heavy classification | Find existing ERDs, Product context, Jira/PRD/decision docs, duplicate signals |
| Granola | Optional, required only for meeting-note context | Find support-rotation debriefs, recorded discussions, exact meeting wording |

If a required connector is unavailable, continue with the best manual fallback. If an optional connector is unavailable, skip it and say what context was not checked.

## Minimal Checks

Run only the checks needed for the mode.

### Notion

Before create or report mode, make one lightweight request against the Ideation Log database target from `notion-connector.md`:

- Prefer fetching the database or data source schema.
- If schema fetch is unavailable but Notion search exists, search for the Ideation Log database title or database URL.
- If Notion tools are not exposed in the current session, mark Notion unavailable.

### Glean

Before using `research-and-erd.md`, run one small search with the product area or core problem terms. If Glean CLI or MCP access is unavailable, skip Glean and ask one focused clarification question instead of broadening blind.

### Granola

Before relying on meeting notes, run one targeted query using the support rotation, debrief, or caller-provided meeting terms. If Granola is unavailable, ask the user to paste meeting notes or continue without them.

## Status Report

After the checks, report the connector state briefly:

```text
Connector check:
- Notion: connected - Ideation Log schema reachable
- Glean: connected - research available
- Granola: optional unavailable - meeting notes skipped
```

Use these status labels:

- `connected` when the check succeeds.
- `connected, no results` when the connector responds but the target query is empty.
- `optional unavailable` when an optional connector is missing or fails.
- `required unavailable` when Notion is missing or fails for create/report mode.

## Fallbacks

- Add idea mode without Notion: draft the entry in Notion-ready Markdown, include the Ideation Log database link, and offer connector setup help.
- Report mode without Notion: ask the user for exported or pasted Ideation Log JSON, then render with `render_ideas_report.py`.
- Research without Glean: ask one clarification question for the missing classification, owner, duplicate, or ERD signal.
- Meeting-note context without Granola: ask for pasted notes, transcript text, or a meeting link the user can summarize.

Read `connector-setup.md` only when a connector failure blocks the requested workflow or the user asks how to enable connectors.
