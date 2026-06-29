# Connector Setup

Share these instructions only when setup help is needed.

Before I can create or fetch Ideation Log entries directly, I need the Notion connector enabled.

## Required

| Connector | What This Skill Uses It For |
| --- | --- |
| Notion | Fetch the Ideation Log schema, create support-rotation ideas, and fetch rows for reports |

## Optional

| Connector | What This Skill Uses It For |
| --- | --- |
| Glean | Find related ERDs, Product context, Jira/PRD references, and possible duplicate ideas |
| Granola | Pull context from support rotation debriefs, meeting notes, and transcripts |

## Claude Connector Setup

1. Open <https://claude.ai/customize/connectors>.
1. Enable **Notion**.
1. If prompted, authenticate with your `@apollo.io` account and choose the Apollo workspace.
1. Enable **Glean** or **Granola** only if you want this skill to search those sources.
1. Return to this chat and type `ready`.

## Codex Desktop Notion Setup

If you are using Codex Desktop and Notion tools are not available, check that the Notion MCP server is configured with both the URL and OAuth resource:

```bash
codex mcp add notion --url https://mcp.notion.com/mcp --oauth-resource https://mcp.notion.com
codex mcp get notion
/Applications/Codex.app/Contents/Resources/codex --strict-config doctor --summary --ascii
```

After authenticating, restart or open a new Codex session if the Notion tools do not hot-load.

## Manual Fallback

If connector setup is blocked, continue with one of these:

- For add idea mode, paste the support observation and I will draft a Notion-ready entry for manual creation.
- For report mode, export or paste Ideation Log rows as JSON and I will render the report locally.
