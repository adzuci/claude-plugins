# Apollo Plugin Marketplace Review Rules

Review this repository for packaging defects that would make Claude Code, Codex, or Cowork unable to discover or install a plugin.

- Flag any `plugins/<plugin>/` directory with `skills/` but no `.claude-plugin/plugin.json` or `.codex-plugin/plugin.json`.
- Flag marketplace drift between `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json`.
- Flag a marketplace entry whose `source` path does not exist or whose manifest `name` does not match the plugin directory.
- Flag Codex manifests that omit `skills: "./skills/"` when a `skills/` directory exists, or include `mcpServers` when `.mcp.json` is absent.
- Do not request broad style rewrites. Focus comments on installability, validation, generated inventory drift, and missing tests for executable skill scripts.
