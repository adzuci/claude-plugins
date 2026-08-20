# Data Sources

Where each brief field comes from and how to fetch it at runtime. Every live
source below is OPTIONAL. If a CLI or MCP is not available, degrade gracefully:
ask the operator to paste the data, render from the pasted payload, and mark the
affected fields Unverified.

## Important: Where This Runs

This skill is meant to run in the AM's own authenticated environment, where the
Snowflake CLI, the Salesforce CLI, and the Intercom MCP are already connected.
Auth is ambient and connector-managed. Do not hardcode credentials, tokens, org
ids, report ids, or connection secrets anywhere. A Claude Tag or hosted session
cannot reach these live sources, so in that context you must fall back to pasted
data and label every tool-backed field Unverified.

Confirm availability first:

```bash
python3 scripts/check_dependencies.py --json
```

## Support Tickets (Snowflake)

- **Provides**: open tickets, ticket age, severity, status, owner, reopen count,
  ticket volume, CSAT responses.
- **How**: run read-only queries through the Snowflake CLI. Follow the same form
  the pr-metrics skill uses:
  ```bash
  snow sql --connection apollo --query "<your SELECT>"
  ```
  Auth is ambient (connector-managed) in the AM's own environment. Do not pass or
  hardcode credentials. Write SELECT-only queries; never INSERT, UPDATE, DELETE,
  or DDL.
- **Parameterize**: fill the account id, domain, or date window into the query at
  runtime. Do not commit real table names with embedded ids or secrets into this
  skill.
- **Fallback**: if `snow` is missing or the connection fails, ask the operator to
  paste a ticket export (CSV or table) and mark the ticket fields Unverified.

## Account And Health (Salesforce CLI)

- **Provides**: account identity (name, id, domain, owner/AM, CSM), plan, ARR,
  renewal date, renewal risk, and the AM's book of accounts.
- **How**: read-only REST calls through the Salesforce CLI against the
  `apollo-sfdc` org:
  ```bash
  sf api request rest --target-org apollo-sfdc "/services/data/vXX.X/sobjects/Account/<id>"
  sf api request rest --target-org apollo-sfdc "/services/data/vXX.X/query?q=<url-encoded SOQL>"
  ```
  Use GET requests only. Do not PATCH, POST, or DELETE. Auth is managed by the
  connected org; do not hardcode credentials.
- **Book resolution (AM target)**: resolve the AM to their owner id (by email or
  full name), then query accounts they own.
- **Fallback**: if `sf` is missing or the org is not connected, ask the operator
  to paste account and health fields and mark them Unverified.

## Company Context (Intercom MCP)

- **Provides**: company profile and recent conversation context, useful for
  cross-checking support signals and recent activity.
- **How**: use the Intercom MCP tools (`mcp__Intercom__*`) to look up a company by
  domain, then read recent conversations. Read-only: never send replies, add
  notes, tag, snooze, or close anything.
- **Fallback**: if the Intercom MCP is not connected, skip company context or use
  operator-pasted context, and mark those fields Unverified.

## Field-To-Source Map

| Brief field | Primary source | Fallback |
| --- | --- | --- |
| Account name, id, domain, AM, CSM | Salesforce | Pasted, Unverified |
| Plan, ARR, renewal date, renewal risk | Salesforce | Pasted, Unverified |
| Open tickets, age, severity, status, owner | Snowflake | Pasted, Unverified |
| CSAT, reopen count, ticket volume | Snowflake | Pasted, Unverified |
| Recent conversation context | Intercom MCP | Pasted, Unverified |

Whatever the source, keep the read-only discipline from
`references/account-brief-mode.md`: query, do not mutate, and never fabricate a
value you did not retrieve.
