---
name: house-setup
description: Set up the house-manager agent and its local /hm skill, with optional `nest` (Nest thermostat access) and `notify` (Twilio SMS/call alerts) arguments. Run via /house:house-setup.
argument-hint: '[nest | notify]'
disable-model-invocation: true
---

# House Setup

Installs a household-admin agent that runs weekly: it scans email and calendar
for house items, optionally reads Nest thermostats, writes a digest into your
vault, adds backlog tasks, and can text or call you for urgent items.

Resolve bundled scripts relative to this skill directory (`scripts/`). Every
write step is dry-run first and needs an explicit yes. Never ask the user to
paste a secret into chat, and never put one in a command line.

## Arguments

- *(none)* — base setup: managed `/hm` skill, helper scripts, vault note, weekly schedule.
- **`nest`** — connect Nest thermostats through Google's Smart Device Management API. Runs after base setup (or standalone if `~/.config/adzuci-house/config.json` exists).
- **`notify`** — connect Twilio so the agent can text or call for urgent items.

## Base setup

1. **Pre-flight (read-only).** Run:

   ```bash
   python3 scripts/house_setup.py check --vault <vault>
   ```

   Report: macOS, `claude`/`codex`, `twilio`/`gcloud` CLIs, vault found, whether `/hm` is already installed.

2. **Connectors.** Gmail and Google Calendar connectors must be connected in the client. Google Drive is optional. If missing, point the user to the connector list; do not continue without Gmail and Calendar. The agent only ever uses their **read/search** tools.

3. **Ask** (one message): vault path (default: the configured vault from `~/.config/adzuci-productivity/config.json`), clients (auto), schedule (default Sunday 18:00 local, cron `0 18 * * 0`).

4. **Dry run, then apply:**

   ```bash
   python3 scripts/house_setup.py install --vault <vault>
   python3 scripts/house_setup.py install --vault <vault> --apply
   ```

   This copies helper scripts to `~/.config/adzuci-house/bin`, writes a mode-600 config (no secrets), installs a managed `hm` skill for each detected client, and creates `agents/house-manager.md` plus `house/README.md` and `house/digests/` in the vault. It refuses to overwrite an unmanaged skill and never touches `settings.json`, hooks, or launchd.

5. **Schedule** the weekly run with the client's native scheduler (for example the Claude desktop scheduled-tasks tool, or `/schedule`). The prompt must be self-contained: run `/hm`, use only read/search connector tools, write the digest to the vault, never send email. Confirm the cron and prompt with the user before creating it.

6. **Verify.** Run `/hm` once and confirm a digest appears in `house/digests/`.

## `nest` argument

Read-only access to thermostats (and other Nest devices the API supports; Nest Protect is not supported by the API). Requires a personal Google account that owns the devices. Walk the user through these steps; they perform the account actions, you run the scripts.

1. **Register** at `console.nest.google.com/device-access` and pay the one-time $5 fee (the user pays; do not do this for them).
2. **Google Cloud project:** create one, enable the *Smart Device Management API*, configure the OAuth consent screen (External, user as a test user), then create an **OAuth client ID** of type *Web application* with redirect URI `https://www.google.com`. Copy the **Client ID**. Set the consent screen to *In production* so refresh tokens do not expire after 7 days.
3. **Device Access project:** create a project with that Client ID (leave Events off), copy the **Project ID**, and confirm the project's OAuth client ID field shows the Client ID.
4. **Save the identifiers** (not secrets):

   ```bash
   python3 scripts/nest_auth.py configure --project-id <PROJECT_ID> --client-id <CLIENT_ID>
   ```

5. **Authorize:** run `python3 scripts/nest_auth.py url`, have the user open it, choose the home and devices, and approve. The browser lands on a Google page with `?code=...` in the address bar. The user keeps that to themselves.
6. **Exchange (user runs this in their own terminal, so secrets never enter chat):**

   ```bash
   python3 scripts/nest_auth.py exchange
   ```

   It prompts (input hidden) for the OAuth client secret on first use and for the redirect URL or code, then stores the secret and refresh token in the macOS Keychain. Nothing is printed or written to disk.
7. **Verify:** `python3 scripts/nest_auth.py status` prints a thermostat table; `check` reports what is configured as booleans only.

Do not run `exchange` yourself, and do not ask the user to paste the client secret, the code, or any token into chat. If asked to troubleshoot, work from `check` output and HTTP status codes.

## `notify` argument

Lets the agent text or call the user for urgent items only. SMS is the default; calls are one-way text-to-speech.

1. Install the Twilio CLI if missing (`npm install -g twilio-cli`; Homebrew requires trusting a third-party tap, so prefer npm). The user runs `twilio login` themselves with their Account SID and Auth Token or API key.
2. The user needs a Twilio phone number, and on a trial account must verify their own phone number as a Caller ID.
3. Record the numbers (E.164, not secrets):

   ```bash
   python3 scripts/house_setup.py install --vault <vault> --apply \
     --notify-to +1XXXXXXXXXX --twilio-from +1YYYYYYYYYY --twilio-profile <profile>
   ```

4. Test the dry run, then send one test only if the user asks:

   ```bash
   python3 scripts/notify.py sms --message "House manager test"
   python3 scripts/notify.py sms --message "House manager test" --send
   ```

   Quiet hours default to 22–7. `--ignore-quiet-hours` is for true emergencies only.

## Guardrails

- Read-only against email and calendar; never send, reply, forward, label, trash, or delete.
- No secrets in chat, config, the vault, or command lines. Keychain only.
- Alerts only for the urgent rules in the vault's `house/README.md`.
- Re-running is safe; `house_setup.py uninstall --apply` removes only what it installed.
