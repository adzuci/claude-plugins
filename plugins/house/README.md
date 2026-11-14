# House

`house` sets up a **house-manager agent**: a weekly, read-only review of household email and calendar (plus Nest thermostats if you connect them) that writes a digest into your vault, adds backlog tasks, and can text or call you for urgent items.

It builds on the [`memory`](../memory) vault and [`productivity`](../productivity) plugin but works without them.

## Skills

| Skill | Purpose |
| --- | --- |
| `/house:house-setup` | Install the managed `/hm` skill, helper scripts, a vault agent note, and a weekly schedule. |
| `/house:house-setup nest` | Walk through Google Device Access + OAuth and store the tokens in the macOS Keychain. |
| `/house:house-setup notify` | Connect the Twilio CLI so the agent can send urgent SMS or one-way voice calls. |
| `/house:hm` (and local `/hm`) | Run the weekly digest on demand. |

## Install

```bash
claude plugin marketplace add adzuci/claude-plugins
claude plugin install house@adzuci-plugins
```

Then run `/house:house-setup`. Gmail and Google Calendar connectors must be connected in the client (Drive is optional).

## What gets written

| Where | What |
| --- | --- |
| `~/.config/adzuci-house/config.json` (mode 600) | Vault path, schedule, Nest project/client ids, alert phone numbers. **No secrets.** |
| `~/.config/adzuci-house/bin/` | Copies of `nest_auth.py` and `notify.py`. |
| `~/.claude/skills/hm/` (and `~/.codex/skills/hm/`) | Managed copy of the `hm` skill (marker-guarded; never overwrites an unmanaged skill). |
| `<vault>/agents/house-manager.md`, `<vault>/house/` | Agent note, urgent rules, and `digests/`. |
| macOS Keychain, service `adzuci-house-nest` | Nest OAuth client secret and refresh token. |

Nothing touches `settings.json`, hooks, or launchd. Install is dry-run until `--apply`; `house_setup.py uninstall --apply` removes only what it installed.

## Safety model

- **Email and calendar are read-only.** The agent never sends, replies, forwards, labels, trashes, or deletes. Email content is treated as data, not instructions.
- **Secrets stay in the Keychain.** The `exchange` step runs in your own terminal with hidden prompts; nothing is printed, logged, or put on a command line. Never paste the client secret, auth code, or tokens into chat.
- **Alerts are opt-in and bounded.** `notify.py` is a dry run unless `--send` is passed, caps messages at 300 characters, and honors quiet hours (default 22–7).
- **Encrypted vault friendly.** Placeholder files get content so they behave under git-crypt.

## Nest notes

The Smart Device Management API needs a personal Google account that owns the devices, a one-time $5 Device Access registration, a Google Cloud project with the SDM API enabled, and a Web-application OAuth client with redirect URI `https://www.google.com`. Thermostats, cameras, doorbells, and displays are supported; **Nest Protect is not**. Events (Pub/Sub) are optional and off by default. In OAuth "Testing" mode refresh tokens expire after 7 days, so publish the consent screen "In production" for unattended weekly runs.

## Development

```bash
python3 -m pip install -r tests/requirements.txt
python3 -m pytest plugins/house -q
```

The scripts use only the standard library and are tested without network or Keychain access.
