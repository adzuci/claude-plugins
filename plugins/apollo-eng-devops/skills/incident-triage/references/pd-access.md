# PagerDuty Read Access

`pd-reconcile` (and PD-linked rows in `triage`/`report`) need to read PD incident state and notes. There are two read paths — the MCP and the `pd` CLI — and three MCP states to detect first.

## Three MCP states

| State | Signal | Action |
| ----------------------- | --------------------------------------------------- | --------------------------------------------------------------- |
| Present + authorized | `get_incident` returns data | Use the MCP. |
| Present but auth-failing | `get_incident` returns HTTP `401` / `403` (e.g. deactivated key) | Treat as **unavailable**. Do **not** loop-retry — failure is per-key, not transient. Fall to the CLI. |
| Absent | `list_incidents` / `get_incident` not available | Fall to the CLI. |

## Prefer the `pd` CLI over re-adding the MCP

For the auth-failing or absent states, **check `command -v pd` before any MCP re-install dance.** The CLI is read-only-friendly, faster, and doesn't drop the session's live MCP tools:

```bash
pd rest get -e /incidents/<INCIDENT_ID>   # status, service, escalation_policy, assignments, acknowledgements
pd incident:notes -i <INCIDENT_ID>        # human notes (often the Slack link you need)
```

These are read-only GETs. Jira write-backs still go through the skill's per-row approval flow.

## MCP re-install is the last resort

Only if the `pd` CLI is absent, suggest installing it; offer MCP re-add last. Print once, then continue in degraded mode:

> Can't read PD state (no `pd` CLI, and the PagerDuty MCP is missing or its key is rejected). Install the read-only CLI:
>
> ```bash
> brew install pagerduty/pagerduty/pd  # then: pd login
> ```
>
> Re-adding the MCP (`claude mcp remove pagerduty && claude mcp add ...`) drops live tools mid-session and needs a manual `/mcp` OAuth reconnect — reach for the CLI first. Without either, I'll flag PD-linked tickets as "needs PD verification" instead of proposing an auto-close.
