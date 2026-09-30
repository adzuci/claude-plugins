# gcx setup (install, log in)

`gcx` is Grafana's CLI; `mute_alert.py` requires it. Never run
`gcx config view` (may show credentials). The user runs `gcx login` in their
own terminal, not the agent.

## 1. Check

```text
/apollo-eng-devops:mute-alert doctor
```

Or by hand: `command -v gcx`, `gcx version`, `gcx config check` (should pass),
`gcx config current-context` (should be the apolloio context).

## 2. Install (macOS, Homebrew; verified with `brew info gcx`, tap `grafana/grafana`)

```bash
brew install grafana/grafana/gcx
```

Use the full name: plain `gcx` also matches a different `homebrew/core` formula.

## 3. Log in (user runs this)

```bash
gcx login --server https://apolloio.grafana.net --oauth
```

Approve in the browser (SSO), then re-run `doctor`: `gcx config check` must pass.

## 4. Logged in but `create` returns 401/403

Ask a Grafana admin for Editor/alerting-write on your user, or use another
account/context (`gcx config use-context <name>`).

## Troubleshooting

- Wrong context: `gcx config list-contexts`, then `gcx config use-context <name>`.
- Expired login: re-run `gcx login` (step 3).
- Timeouts or SSO loops: connect the corp VPN, retry in a normal browser.
