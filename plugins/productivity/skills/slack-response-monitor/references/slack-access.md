# Slack Access

Choose one access path that can both discover candidates and verify full thread context. Prefer a native Slack MCP connector when available; use a CLI only when it is already installed, authenticated, and authorized for the user's workspace.

## MCP Connector

Confirm that the connector can:

1. resolve the authenticated user's Slack member ID;
1. search direct messages, mentions, and channel messages within a time window;
1. read a complete thread, including replies after the candidate message;
1. return or construct a stable message ID and Slack permalink.

Use structured timestamps and IDs from tool results. Do not treat search snippets as proof that an ask remains unresolved; read the thread before classification.

## CLI

An acceptable CLI path may be a workspace-provided Slack search CLI or an authenticated enterprise-search CLI that indexes Slack. Before using it, verify that it can search a bounded time window and retrieve enough thread context to determine whether the user responded.

Do not assume that the official Slack developer CLI can search workspace messages; it is primarily an app-development tool. Do not install a CLI, request new scopes, scrape the Slack UI, or copy credentials as part of a monitoring run.

Use machine-readable output when supported. Keep commands bounded by timestamp, result count, channel, or conversation, and avoid printing unrelated message bodies into logs.

If the CLI returns only snippets, stale index entries, or results without thread replies, access is incomplete. Report the run as blocked rather than claiming that no responses are needed.

## Capability Result

Record these facts before scanning:

- identity resolution: available or unavailable;
- bounded message search: available or unavailable;
- full thread reads: available or unavailable;
- stable IDs/permalinks: available or unavailable.

Identity, search, and thread reads are required. Permalinks are required for digest items; if a tool cannot return them directly, construct them only from verified workspace, channel, and message identifiers.
