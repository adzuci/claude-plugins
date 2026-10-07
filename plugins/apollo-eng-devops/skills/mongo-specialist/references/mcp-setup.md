# MCP Setup for Incident Triage

Enable these MCPs before or early in an incident so diagnostics and watchers work.
All commands are for Claude Code; MCP tool namespaces load at session startup, so
**restart the session** after adding one. Verify with `claude mcp get <name>`.

Apollo VPN / corp network may be required for the internal MCP endpoints.

## Readiness check

Run this first. Report what is ready and what is not before starting triage.

| Dependency | Kind | Verify | Needed for |
| --- | --- | --- | --- |
| `grafana` | MCP | `mcp__grafana__query_prometheus` in the tool list; `claude mcp get grafana` | All metric and log triage. Hard requirement |
| `gcloud` | CLI | `command -v gcloud && gcloud auth list` | GCE events, VM forensics, `check-mongo --gce` |
| `gcx` | CLI | `command -v gcx && gcx config check` | Muting an alert (`mute-alert`). Not needed for read-only triage |
| `glean_default` | MCP | `claude mcp get glean_default` | Prior-incident and Slack context. Optional |

Two failure modes look alike and are not:

- **Not installed or not connected.** Fix with the setup below, then restart the session.
- **Installed but refused** by a permission prompt or the auto-mode classifier. Nothing
  to install. Name the exact call and the settings rule that would allow it, for example
  `mcp__grafana__query_prometheus` or `Bash(gcloud compute ssh mongo-email-shard-16-b:*)`
  in `~/.claude/settings.json` under `permissions.allow`, then let the user add it.

Never run `gcloud auth login` or `gcx login` on the user's behalf. Print the command.

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

### Loki cost guardrail

`query_loki_logs` bills on bytes **scanned**, and only the stream selector plus the time
range decide that. Line filters (`|=`) and parsers (`| json`) cut what comes back, not
what is read. A permission rule cannot enforce any of this (allow entries match tool
names, not arguments), so it is on the operator:

- Run `query_loki_stats` on the selector first. Every time, before the logs query.
- Scope to a service, pod or role label. Never query a whole namespace: one unscoped 24h
  query against `leadgenie` was estimated at 327 GB against a roughly 3.7 GB guardrail.
- Open with the narrowest window that can answer the question, then widen. Do not start
  at 24h or 30d to be safe.
- `grafanacloud-logs` is allowlist-blocked at Apollo. Use the Loki datasource UID.
- Known-good scoped selector for this cluster: `{cluster="email", role="mongos"}`. mongod
  and host logs do **not** reach Loki, only `auth.log` does.

If the volume still looks large after scoping, say so and ask before running it rather
than trimming the question to fit.

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

## gcx (Grafana CLI)

Not an MCP, but the same class of dependency and the usual blocker for the mute step at
the end of a triage. Install and login live in
[`../../mute-alert/references/gcx-setup.md`](../../mute-alert/references/gcx-setup.md).
Never run `gcx config view` (may show credentials).
