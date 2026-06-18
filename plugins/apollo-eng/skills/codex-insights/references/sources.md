# Sources

Use these links when the skill updates the Obsidian token-efficiency project.

## Local Sources

- `~/.codex/sessions/` - active Codex rollout logs.
- `~/.codex/archived_sessions/` - archived Codex rollout logs.
- `~/.codex/session_index.jsonl` - thread id to thread name mapping.
- `~/.codex/config.toml` - model, memory, plugin, MCP, and desktop settings.
- `codex debug prompt-input "codex-insights baseline"` - model-visible prompt input shape.
- `codex doctor` - Codex health, MCP count, and connectivity.
- `ccusage codex daily|weekly|session --json` - optional cross-check if available.

## Notion and Team References

- Token Efficiency Assessment DB: https://www.notion.so/apolloio/32fab2b3b496806a8be7cfc6ab5142f0?v=32fab2b3b496803d8f65000ca2f041f4
- Claude Code Efficiency Guide: https://www.notion.so/apolloio/The-Claude-Code-Efficiency-Guide-Spend-Less-Get-More-bd57d3e370c64243a9c428529db0882f
- ccflare relay: https://github.com/apolloio/ccflare-relay
- Slack: `#claude-token-enablement`

## Public Prior Art

- `ccusage` supports Codex, Claude Code, and other coding-agent sources with daily, weekly, monthly, session, JSON, model breakdown, and offline modes.
- Claude Code cost guidance emphasizes context management, model choice, MCP overhead reduction, hooks/skills, and moving specialized instructions out of always-loaded context.
- Claude Code Usage Monitor contributes the live burn-rate/session-window framing; this skill uses the framing but stays report-first and local.
