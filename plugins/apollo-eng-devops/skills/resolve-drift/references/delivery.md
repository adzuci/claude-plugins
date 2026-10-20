# Delivery (headless)

The report is the script's stdout. Post it once, unchanged. Never add a summary.

| Runtime | How to deliver |
| --- | --- |
| Local Claude Code routine with Slack MCP | `slack_send_message` to the requester's DM (or the channel in the routine prompt) |
| Local routine with a bot token | add `--post-channel <id>` to the script; it posts with `SLACK_BOT_TOKEN` |
| Apollo Operator | reply in the triggering Slack thread or the channel the job names. **Blocked today:** see below |
| No Slack at all | print the report; the routine log is the record |

Rules:

- One post per run. If posting fails, print the error and the report; do not retry more than once.
- `error` rows must stay in the post; they mean "unknown", not "fine".
- Suggested schedule: Mondays 06:00 ET (off-hours, before standups).

## Routine prompt

```text
/apollo-eng-devops:resolve-drift --headless
Deliver to: <slack user or channel id>
```

`Deliver to:` is routine context for the invoking agent; the skill does not parse it.

## Token

A TFC **team** token with `plan` (not `write`/`admin`) on the workspaces in
`workspaces.json`. Locally the `terraform login` user token also works. For Apollo
Operator store it as the `TFE_TOKEN` secret. Rotate on the team's normal cadence.

## Apollo Operator: not yet runnable

Operator's Claude runner is credential-free and a UID firewall blocks public egress from
Bash, so `drift_check.py` can't reach `app.terraform.io` and has no `TFE_TOKEN` to use.
For headless use under Operator, one of these is needed first (owner: Agent Core):

1. An egress allowlist for `app.terraform.io`, with the token injected by the credential proxy, or
1. A TFC MCP in the proxy sidecar, so the token never enters the runner.

Until one of those exists, run the routine locally. In Operator, if the script fails with a
network error or a missing token, report that error row; it is not drift.
