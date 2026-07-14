# MCP Setup for Incident Triage

Enable these MCPs before or early in an incident so diagnostics and watchers work.
All commands are for Claude Code; MCP tool namespaces load at session startup, so
**restart the session** after adding one. Verify with `claude mcp get <name>`.

Apollo VPN / corp network may be required for the internal MCP endpoints.

## Grafana (metrics, the primary live signal)

Canonical setup lives in
[`../check-apdex/references/mcp-setup.md`](../check-apdex/references/mcp-setup.md).
Short form:

```bash
claude mcp add --transport http --scope user grafana https://grafana-mcp.ops-gcp.apollo.io/mcp
```

Restart, then `claude mcp get grafana`. Provides `query_prometheus`, per-instance
label queries, dashboard/panel image export, and Tempo trace search — the tools the
live-incident decision-tree queries depend on.

## Glean (Slack + docs search for thread deltas)

```bash
claude mcp add --transport http --scope user glean_default https://<company>-be.glean.com/mcp/default
```

Confirm the exact endpoint against Apollo's Glean admin/onboarding docs before adding;
the host is org-specific. Glean's Slack index **lags minutes to an hour**, so treat it
as a delta feed for a `slack-watch` subagent, not a real-time incident channel. For
real-time, read the Slack thread directly.

## Granola (incident Zoom transcript follow-along)

If the incident is being run on a Zoom/Meet with Granola capturing it, the Granola MCP
lets a watcher poll the live transcript. Setup is via Granola's own MCP install flow
(app settings → MCP / API); there is no fixed Apollo endpoint. Once connected, verify
`claude mcp get granola`. Usage is in
[`live-incident-mode.md`](live-incident-mode.md) §5. Mark any Granola-derived context as
"if Granola MCP available" — do not assume it is connected.

## PagerDuty

Prefer the `pd` CLI over the MCP for pulling incidents; see
[`../incident-triage/references/pd-access.md`](../incident-triage/references/pd-access.md).
