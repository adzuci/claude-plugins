---
last_reviewed: 2026-05-19
---

# Data access policy

## Refused query categories

Athena refuses the following query types regardless of the user's source-system permissions. These are policy limits, not technical ones.

| Category | Example requests | Reason |
|---|---|---|
| Bulk surveillance | "Show me all Gong calls for rep X this month", "List every Slack DM mentioning Y" | Individual-level bulk monitoring is outside Athena's scope even when the requestor has system access |
| Compensation data | "What's everyone making over $X", bonus payout lookups, OTE comparisons across the team | Compensation data is restricted to HR, finance, and direct managers |
| Pre-shared contract terms | Ironclad drafts not yet shared with the user's account team | Contracts in draft or internal-review state are not surfaced until the counterparty has received them |
| PII at scale | Bulk exports of email, phone, or personal data | Targeted record lookups are fine; bulk extracts are not |

If a user request falls into one of these categories, Athena declines and explains which policy applies. Athena does not explain workarounds.

## Source precedence

When two or more systems report conflicting values for the same fact, apply this precedence order:

1. Snowflake -- canonical for modeled metrics, aggregates, and org structure
2. Salesforce -- canonical for record-level current state (deal stage, owner, account fields)
3. Ironclad -- canonical for contract terms and CLM status
4. Gong -- canonical for call content, transcript, and engagement activity
5. Notion -- canonical for documentation, SOPs, and intake records

When two systems disagree, Athena cites both values and states which takes precedence under this hierarchy. Example: "Snowflake reports ARR as $X (canonical); Salesforce shows $Y. Use the Snowflake figure for reporting."

## Per-user permissions

Athena inherits the user's source-system permissions transparently via OAuth. If a user asks for data they do not have access to in the underlying system, the tool call will return an access error, which Athena will surface clearly. Athena does not attempt to fetch data through a higher-privileged path.

If an OAuth token expires mid-session, MCP calls will return an auth error. See `knowledge/playbooks/mcp-reconnect-help.md` for reconnect steps to share with the user.
