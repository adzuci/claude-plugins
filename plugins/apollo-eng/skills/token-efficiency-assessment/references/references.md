# Token Efficiency Assessment — References

## Notion Database

- **Database ID:** `32fab2b3b496806a8be7cfc6ab5142f0`
- **Data source ID:** `collection://32fab2b3-b496-8093-baff-000b2b9ad4e1`
- **URL:** <https://www.notion.so/apolloio/32fab2b3b496806a8be7cfc6ab5142f0?v=32fab2b3b496803d8f65000ca2f041f4>

## Guides & Docs

- **Claude Code Efficiency Guide:** <https://www.notion.so/apolloio/The-Claude-Code-Efficiency-Guide-Spend-Less-Get-More-bd57d3e370c64243a9c428529db0882f>
- **ccflare Dashboard (token usage monitoring):** <https://github.com/apolloio/ccflare-relay>
- **Anthropic Course — Claude Code in Action:** <https://anthropic.skilljar.com/claude-code-in-action>
- **Slack channel:** #claude-token-enablement

## Origin

- Eng-leadership questionnaire from Griffin Brodman / Piotr Dyba
- [Slack thread](https://apolloio.slack.com/archives/C0469GJ8281/p1773933687939499?thread_ts=1773933419.150089&cid=C0469GJ8281)

## Installing the Notion MCP Server

If the Notion MCP is not available, results are saved locally to `~/.claude/token-efficiency-assessments/`. To install the Notion MCP and push results later:

1. Get a Notion API token from <https://www.notion.so/my-integrations>
   - Create an internal integration with "Read content", "Insert content", and "Update content" capabilities
   - Copy the token (starts with `ntn_`)
1. Share the assessment database with your integration (open the DB in Notion → "..." menu → "Connections" → add your integration)
1. Add the MCP server to your Claude Code settings:

```bash
claude mcp add notion -- npx -y @anthropic-ai/notion-mcp-server
```

1. Set the token as an environment variable in `~/.claude/settings.json`:

```json
{
  "env": {
    "NOTION_TOKEN": "ntn_your_token_here"
  }
}
```

> **Security note:** `~/.claude/settings.json` is plain text. Ensure the file has restrictive permissions (`chmod 600`) and is not committed to any repository. Alternatively, export `NOTION_TOKEN` as a shell environment variable in your `.zshrc`/`.bashrc` instead.

1. Restart Claude Code and run `/apollo-eng:token-efficiency-assessment` again — it will detect the MCP and push your saved results to Notion.

## Pushing Saved Results to Notion After Installing MCP

If you previously ran the assessment without the Notion MCP, your results are in `~/.claude/token-efficiency-assessments/`. To push them:

1. Ask Claude Code: "Push my saved token efficiency assessment to Notion"
1. Claude will read the JSON file and create a page in the database using the Notion MCP
