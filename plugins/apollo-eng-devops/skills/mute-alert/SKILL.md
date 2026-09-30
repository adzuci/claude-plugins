---
name: mute-alert
description: Create, verify, and expire a time-boxed Grafana alert silence for planned maintenance.
argument-hint: "create|list|expire|doctor|self-test [--matcher name=value] [--duration 90m] [--comment ...] [--ticket KEY]"
disable-model-invocation: true
---

# Mute Alert

Run as `/apollo-eng-devops:mute-alert <create|list|expire|doctor|self-test> [args]`.

Mutes a Grafana alert for a short, planned window (for example rolling router
restarts, where each restart pages via "MongoDB Host has restarted", rule uid
`cf32twnieez9ca`) and guarantees the mute ends. Uses one-off **silences**, not
`gcx alert mute-timings` (those are recurring schedule windows).

A silence stops **pages only**. Argus triage posts and auto-created INCIDENT
Jira tickets still happen, and it hides real failures (a router that fails to
restart). Keep verifying the work (`up == 1`, uptime) while muted.

## Requirements

Requires `gcx` (Grafana CLI), logged in; see `references/gcx-setup.md`. The
Grafana MCP `alerting_manage_silences` tool is **read-only** (list/get), so
writes go through `scripts/mute_alert.py` (stdlib only, Python 3.9+), which
calls `gcx api`. Never run `gcx config view` (may contain credentials).

## Step 0: Preflight

Run `/apollo-eng-devops:mute-alert doctor`.
If not ready, follow `references/gcx-setup.md` to help the user install and
authenticate gcx. Never run `gcx login` for them; they run it in their own
terminal.

## Usage

```text
/apollo-eng-devops:mute-alert create --matcher alertname="MongoDB Host has restarted" --matcher cluster=accounts --duration 90m --comment "planned router restarts" --ticket INFRA-2234 [--dry-run] [--yes]
/apollo-eng-devops:mute-alert list [--active]
/apollo-eng-devops:mute-alert expire <id>
/apollo-eng-devops:mute-alert doctor
/apollo-eng-devops:mute-alert self-test
```

Runs `scripts/mute_alert.py` with the same arguments; you can call the script
directly from the repo root if you are not using Claude.

| Flag | Default | Rule |
|---|---|---|
| `--matcher name=value` | required, repeatable | exact only; `alertname` required; regex/wildcards rejected |
| scoping label | required | at least one `cluster` or `instance`; `--allow-broad` overrides |
| `--duration` | `60m` | `30m`, `90m`, `1h`; max 4h, `--allow-long` up to 12h |
| `--comment` | required | why; `--ticket KEY` is appended |
| `createdBy` | from env | `MUTE_ALERT_CREATED_BY`, else `$USER` |

Exit codes: 0 ok, 2 bad input (validated before any network call), 3 API error.

## Flow

1. **Preview**: run `create ... --dry-run` to show the exact matchers and
   window. Use MCP `alerting_manage_rules` (`search_rule_name`) to confirm the
   alert exists and see which instances it covers.
1. **Approval**: show the matchers, endsAt, and comment to the user. Do not
   create until they explicitly say yes.
1. **Create**: `create ... --yes`. Report the silence id, `endsAt`, and the exact
   `expire` command from the output.
1. **Verify**: MCP `alerting_manage_silences` `list` (optionally with
   `matchers: [{name: alertname, value: ...}]`); confirm the id, matchers, and
   `endsAt`. Entries follow the Alertmanager v2 shape (`id`, `status.state`,
   `matchers`, `startsAt`, `endsAt`).
1. **Do the work.** A human runs production commands; agents cannot ssh.
1. **Undo**: `expire <id>` as soon as done, then MCP `list` and confirm the
   silence shows `state: expired`. If forgotten it expires itself at `endsAt`.

## Guardrails

- Keep the window as short as the work; never widen instead of re-creating.
- Only run `self-test` (2 minute silence on `__mute_alert_selftest__`, matches
  no real alert) to prove write access; expect `PASS`.
- On 401/403, fix auth (`gcx login` or a Grafana Editor/alerting-write role); do not retry blindly.

## See Also

`grafana-observability` (alert quality), `incident-triage` (PD alert tickets),
`incident-response` (comms), `mongo-specialist` (router restart runbook, once
merged).
