---
name: budgetclaw-setup
description: Manual-invocation only. Install and configure budgetclaw (a local Claude Code spend monitor) on macOS in monitor-only mode with private, fully-local Notification Center alerts. Run via /apollo-eng-devops:budgetclaw-setup.
argument-hint: optional daily cap in USD (default 27)
disable-model-invocation: true
---

# BudgetClaw Setup

Install [budgetclaw](https://github.com/RoninForge/budgetclaw) the safe way on
macOS: **monitor-only** (`warn`, never `kill`), **fully local** (`127.0.0.1`,
no ntfy.sh), with native Notification Center alerts that are debounced so one
budget breach cannot flood the user.

This is not an org-wide recommendation yet. budgetclaw is MIT/public and useful,
but it is still early, low-adoption, and single-maintainer. Treat this as an
opt-in local experiment for people who want a Claude Code spend guardrail.

## What Gets Installed

```text
Claude Code logs -> budgetclaw watch -> POST 127.0.0.1:8410 -> notify_bridge.py -> terminal-notifier
```

The setup script creates:

- `~/.config/budgetclaw/config.toml`
- `~/.local/share/budgetclaw/notify_bridge.py`
- `~/Library/LaunchAgents/org.roninforge.budgetclaw.plist`
- `~/Library/LaunchAgents/org.roninforge.budgetclaw-notify.plist`

## Usage

Let `CAP` be the optional daily cap in USD, defaulting to `27`.

```bash
plugins/apollo-eng-devops/skills/budgetclaw-setup/scripts/setup_budgetclaw.sh "${CAP:-27}"
```

The script is idempotent:

- Homebrew installs are safe to rerun.
- Config, bridge, plist, and log files are overwritten intentionally.
- Existing launchd agents are unloaded before being loaded again.
- Timezone detection only writes `timezone` when it finds an IANA `Region/City`
  value. It does not fall back to abbreviations such as `PST` or `CEST`.

## Verify

After setup, run:

```bash
launchctl list | grep budgetclaw
lsof -nP -iTCP:8410 -sTCP:LISTEN >/dev/null && echo "bridge up"
budgetclaw status
for i in 1 2 3 4 5; do
  curl -s -o /dev/null -H "Title: budgetclaw breach" --data "test $i" http://127.0.0.1:8410/budgetclaw-local
done
```

The first POST burst should raise one popup. A second burst with the same title
within 30 minutes should raise none. If no popup appears, approve notifications
in System Settings -> Notifications; the bridge posts as Terminal.

## Tunables

- Cap / timezone: `~/.config/budgetclaw/config.toml`
- Debounce window: `COOLDOWN_SECONDS` in
  `~/.local/share/budgetclaw/notify_bridge.py`, then reload the notify agent.

## Teardown

```bash
launchctl unload ~/Library/LaunchAgents/org.roninforge.budgetclaw.plist 2>/dev/null || true
launchctl unload ~/Library/LaunchAgents/org.roninforge.budgetclaw-notify.plist 2>/dev/null || true
rm ~/Library/LaunchAgents/org.roninforge.budgetclaw{,-notify}.plist
brew uninstall budgetclaw terminal-notifier
brew untap roninforge/tap
rm -rf ~/.config/budgetclaw ~/.local/state/budgetclaw ~/.local/share/budgetclaw ~/.cache/budgetclaw
```
