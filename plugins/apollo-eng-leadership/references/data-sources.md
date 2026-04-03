# Leadership Data Sources

Internal URLs and search queries used by leadership skills. Update this file
when documents move or fiscal year rolls over.

## OKR Tracker

- **Google Sheet:** `https://docs.google.com/spreadsheets/d/1VdsO-mQ54zrYZQNUhV4OkmqhZxunT4rubzrjErsxWUg/edit?gid=1405873114#gid=1405873114`
- **Glean search query:** `"OKR tracker FY27"`
- **Fiscal year:** FY27 (update when fiscal year changes)

## Engineering Metrics

- **Glean search query:** `"engineering metrics <team name>"` (app: gdrive)
- **Additional queries:**
  - `"<team name> lead time analysis"` — PR velocity and review data
  - `"engineering midterm metrics report"` — Quarterly team-level metrics

## Glean MCP Setup

If the Glean MCP server (`glean_default`) is not available:

1. Tell the user the skill uses Glean and it is not currently installed.
1. Offer to install it (requires VPN):
   ```
   claude mcp add glean_default https://apollo-io-be.glean.com/mcp/default --transport http --scope user
   ```
1. If installation succeeds but connection fails, remind the user to check VPN.
1. If the user declines, ask them to paste the data manually.
