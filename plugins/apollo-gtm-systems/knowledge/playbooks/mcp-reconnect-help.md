---
last_reviewed: 2026-05-20
---

# Playbook: reconnecting an MCP tool in Claude

Use this when a GTM tool that Claude uses (Salesforce, Jira, Gong, etc.) shows an authorization error or returns empty results.

## Symptoms

- "Not connected" or "Authorization failed" when Claude tries to use a tool
- Claude reports it cannot access Salesforce, Gong, Jira, or another system
- A tool that worked in a previous session now returns empty results or errors without a clear reason

## Generic reconnect steps

**Claude Code:**
1. Type `/mcp` to open the MCP connection manager
2. Find the disconnected tool in the list and select "Reconnect" or "Re-authorize"
3. Follow the OAuth flow for that tool (you will typically be redirected to the tool's login page in your browser)
4. Return to Claude and test by asking a question that uses the reconnected tool

**Claude Desktop:**
1. Click "Customize" in the left sidebar
2. Scroll to the MCPs section
3. Find the disconnected tool and select "Reconnect"
4. Follow the OAuth flow in the browser window that opens
5. Return to Claude and test

## Tool-specific notes

**Salesforce**
Apollo's Salesforce production org: https://apolloio.my.salesforce.com/

Uses Okta SSO — authenticate via Okta, not a username and password. During the OAuth flow, confirm you are logging into the production org. If you are redirected to `test.salesforce.com`, the connection is pointed at a sandbox and will need to be reconfigured.

**Gong**
Uses Okta SSO. You will be redirected to Gong's authorization page via Okta. After authorizing, return to Claude and confirm with a simple query (e.g., "check my recent Gong calls").

**Jira / Confluence**
Uses Google (via Okta) for authentication. If your Atlassian account has access to multiple organizations, select the Apollo.io org during the authorization step. Selecting the wrong org results in empty results rather than an error.

**Snowflake**
Uses Google (via Okta) for authentication. Snowflake sessions can expire if inactive. If a simple reconnect does not work, provisioned credentials may need to be refreshed. File an RS JIRA ticket with the error message.

## If reconnect fails

File an RS JIRA ticket (https://apollopde.atlassian.net/servicedesk/customer/portal/8) with:
- The tool name
- The exact error message from Claude
- The date and time the issue started (if known)

GTM Systems will determine whether it is a credential expiry, an org-level config issue, or an MCP proxy problem.
