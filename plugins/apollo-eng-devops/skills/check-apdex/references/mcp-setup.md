# MCP Setup Reference

Use this reference when `/apollo-eng-devops:check-apdex` needs Snowflake or Grafana but the MCP is missing, unauthorized, or not visible to the current Claude/Codex session.

## Preflight Checks

For Claude Code:

```bash
claude mcp get apollo_snowflake
claude mcp get grafana
```

For Codex:

```bash
codex mcp list
```

If an MCP is configured but the tool is not visible inside the current session, restart Claude Code or Codex. MCP tool namespaces are loaded at session startup.

## Snowflake MCP

Snowflake is required for normal `check-apdex` execution. The expected local MCP name is:

```text
apollo_snowflake
```

The known Apollo setup uses a local Snowflake MCP server checkout and browser SSO. Personalize the checkout path and user before running:

```bash
claude mcp add --scope local apollo_snowflake -- /opt/homebrew/bin/uv --directory /Users/<you>/code/apolloio/mcp-snowflake-server run mcp_snowflake_server --account APOLLOORG-APOLLO --warehouse ELT_WH --user <your-email>@apollo.io --role DATACONSUMER_ROLE --database analytics_db --schema analytics_dataplatform --authenticator externalbrowser --exclude_tools write_query create_table
```

After adding it, restart Claude Code and verify:

```bash
claude mcp get apollo_snowflake
```

If browser auth prompts repeatedly, check whether the MCP server process is restarting. The local Snowflake MCP server also expires its in-memory session after 30 minutes, and `externalbrowser` auth may prompt again after that.

If Apollo policy allows it, key-pair auth is the durable way to reduce repeated browser prompts. Do not ask the user to paste secrets into the chat.

## Grafana MCP

Grafana is optional until a dip is detected or `--deep` is passed. The expected MCP name is:

```text
grafana
```

Setup:

```bash
claude mcp add --transport http --scope user grafana https://grafana-mcp.ops-gcp.apollo.io/mcp
```

Apollo VPN may be required for the Grafana MCP server.

After adding it, restart Claude Code and verify:

```bash
claude mcp get grafana
```

## Fallback Behavior

If Snowflake is unavailable and the user chooses SQL-only, print the SQL from `snowflake.md`, mark the result as not executed, and stop before claiming a verdict.

If Grafana is unavailable after a Snowflake dip, produce a Snowflake-only triage and include the Grafana setup command above.
