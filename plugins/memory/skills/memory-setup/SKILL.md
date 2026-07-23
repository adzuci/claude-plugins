---
name: memory-setup
description: Set up a git-backed Obsidian vault with Claude SessionEnd hook for session-memory capture, plus optional Codex and Antigravity importers.
disable-model-invocation: true
---

# Memory Setup

Onboards a developer or knowledge worker to a local knowledge-capture system: a git-backed Obsidian vault, the `claudian` and `obsidian-git` Obsidian plugins, a Claude Code `SessionEnd` hook that writes concise session notes, and scheduled git sync so multiple machines stay converged. Codex and Antigravity are supported as compatibility paths that append to the same vault when the skill is invoked from those clients.

## Arguments

- **`crypt`** — enable git-crypt encryption for sensitive vault directories. Works three ways, auto-detected by `scripts/setup_crypt.py`:
  - during a fresh setup (runs as Step 4.5 after scaffolding),
  - standalone against an existing vault (seamless migration — run Steps 1, 4.5, and 11 only),
  - on a second machine with a locked clone (unlock flow in Step 4.5).

  Read `references/encryption.md` before running the crypt flow. When invoked WITHOUT `crypt`, skip Step 4.5 entirely and never mention encryption.

## Client Mode

Choose the mode before running any write step:

- **Claude Code** — primary and default. Run the Claude hook and `CLAUDE.md` steps.
- **Codex** — compatibility mode when invoked from Codex or explicitly requested. Read `references/codex.md`; do not write `~/.claude` files.
- **Antigravity** — compatibility mode when invoked from Antigravity/Gemini or explicitly requested. Read `references/antigravity.md`; do not write `~/.claude` files unless the user explicitly asks for Claude sharing too.
- **All / shared** — scaffold the vault and Obsidian plugins once, then run the Claude path first unless the user asked for only another client.

If the client is unclear, ask one concise question before Step 0.

Follow the steps below in order. Each gate must receive explicit user approval before proceeding. In Claude Code, use AskUserQuestion when available. In Codex or Antigravity, ask a concise question in chat and wait for the answer.

## Step 0: Explain First (Gate)

Read `references/cost-benefit.md` and present a concise summary covering:

- What installs for the selected mode (shared vault scaffold and two Obsidian plugins, plus the Claude hook/`CLAUDE.md` in the primary path; Codex or Antigravity importers only when that compatibility mode is selected)
- Anticipated token cost per substantive session (Claude Haiku summary ~1¢ warm / ~4¢ cold; Codex token line is free because it reads local JSONL; Antigravity local token totals are unavailable unless the installed version exposes them; vault reads are on-demand and bounded)
- Why it is worth it vs the alternative (see cost-benefit.md for the full comparison)

**Tip:** This setup works best in Auto mode, which lets Claude run all install steps without pausing for approval on each tool call. If you're not already in Auto mode, type `/auto` in the Claude Code prompt before selecting Proceed. You can disable it after setup with `/auto` again.

Then ask for one of three choices: **Proceed**, **Explain more**, **Cancel**.

Do nothing else until the user selects Proceed.

## Step 1: Pre-Flight (Read-Only)

Run both commands below. They are read-only and make no changes.

```bash
python3 scripts/check_env.py --vault-candidate <proposed-path>
```

```bash
python3 scripts/detect_memory_tooling.py
```

Render the results as a markdown table with columns: Item, Status. Rows:

| Item | Status |
|------|--------|
| macOS | yes / no |
| Homebrew | found / missing |
| Homebrew /usr/local/share/info writable | yes / no |
| Obsidian | found / missing |
| git | found / missing |
| gh (GitHub CLI) | found / missing |
| node | found / missing |
| npm | found / missing |
| claude (CLI) | found / missing |
| codex (CLI) | found / missing |
| jq | found / missing |
| git-crypt | found / missing (only relevant with `crypt`) |
| op (1Password CLI) | found / missing (only relevant with `crypt`) |
| Codex sessions | found / missing |
| Codex session index | found / missing |
| Antigravity brain | found / missing |
| Antigravity hooks | found / missing |
| Vault candidate | exists (non-empty) / clear / not checked |
| Vault has .git | yes / no / not checked |
| claude-mem | detected / not detected |
| Unknown memory tooling | list names, or "none" |

If any names appear in the `unknown` list, point the user to `references/extending-detection.md` before continuing. Do not block on this — note it and proceed.

## Step 2: Gather Inputs (Gate)

Ask the user the following in one message:

1. **Vault name** — will become `<name>-vault` on disk (e.g., `work` → `work-vault`)
1. **Parent directory** — where to create the vault (default: `~/code`)
1. **Git remote** — choose one:
   - **A) Create a private GitHub repo for me** (requires `gh` CLI — Claude will create `<name>-vault` on GitHub and set the HTTPS remote automatically)
   - **B) I'll provide an existing URL** — paste your HTTPS or SSH remote URL
   - **C) Local-only for now** — no remote; you can add one later with `git remote add origin <URL>`

   If the user picks A, Claude will create the repo in Step 2.5. Default to HTTPS remotes; only use SSH if the user explicitly provides an SSH URL (ssh:// or git@).
1. **Obsidian install** — if Obsidian was not found in Step 1, confirm whether to install it automatically (macOS: direct DMG download from GitHub; Linux/Windows: manual download path).

Echo the resolved plan as a short bullet list (vault path, remote choice, Obsidian action). Ask for a final go-ahead before continuing.

## Step 2.5: Install Prerequisites (If Missing)

Run this step only if `gh` or `jq` was reported missing in Step 1, or if the user selected option A in Step 2 (GitHub repo creation).

### Fix Homebrew permission (if /usr/local/share/info not writable)

If `brew_info_writable` is false and Homebrew is needed for anything, fix the permission first:

```bash
sudo chown -R $(whoami) /usr/local/share/info
```

Tell the user: "Run `! sudo chown -R $(whoami) /usr/local/share/info` in the terminal prompt to fix a Homebrew permission issue before continuing."

### Install jq (if missing)

Install `jq` directly from GitHub releases — do not use `brew` to avoid shallow-clone issues:

```bash
# Detect arch
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then JQ_ASSET="jq-macos-arm64"; else JQ_ASSET="jq-macos-amd64"; fi

# Get latest release download URL
JQ_URL=$(curl -s https://api.github.com/repos/jqlang/jq/releases/latest \
  | python3 -c "import sys,json; assets=[a for a in json.load(sys.stdin)['assets'] if a['name']=='$JQ_ASSET']; print(assets[0]['browser_download_url'])")

# Download to /usr/local/bin/jq (or ~/.local/bin/jq if not writable)
if [ -w /usr/local/bin ]; then
  curl -L "$JQ_URL" -o /usr/local/bin/jq && chmod +x /usr/local/bin/jq
else
  mkdir -p ~/.local/bin
  curl -L "$JQ_URL" -o ~/.local/bin/jq && chmod +x ~/.local/bin/jq
  echo "jq installed to ~/.local/bin/jq — add ~/.local/bin to your PATH if not already present"
fi
```

### Install gh CLI (if missing)

Install `gh` directly from GitHub releases — do not use `brew`:

```bash
# Detect arch
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then GH_ARCH="arm64"; else GH_ARCH="amd64"; fi

# Get latest version
GH_VERSION=$(curl -s https://api.github.com/repos/cli/cli/releases/latest \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['tag_name'].lstrip('v'))")

GH_ZIP="gh_${GH_VERSION}_macOS_${GH_ARCH}.zip"
GH_URL="https://github.com/cli/cli/releases/download/v${GH_VERSION}/${GH_ZIP}"

# Download and extract
curl -L "$GH_URL" -o /tmp/gh.zip
unzip -q /tmp/gh.zip -d /tmp/gh-extract

# Install binary
if [ -w /usr/local/bin ]; then
  cp /tmp/gh-extract/gh_${GH_VERSION}_macOS_${GH_ARCH}/bin/gh /usr/local/bin/gh
else
  mkdir -p ~/.local/bin
  cp /tmp/gh-extract/gh_${GH_VERSION}_macOS_${GH_ARCH}/bin/gh ~/.local/bin/gh
  echo "gh installed to ~/.local/bin/gh — add ~/.local/bin to your PATH if not already present"
fi
rm -rf /tmp/gh.zip /tmp/gh-extract
```

After installing `gh`, authenticate:

Tell the user: "Run `! gh auth login` in the terminal prompt and complete the browser flow, then come back and confirm."

Wait for the user to confirm login succeeded before continuing.

Then wire HTTPS credentials:

```bash
gh auth setup-git
```

### Create GitHub repo (if user chose option A in Step 2)

After `gh auth setup-git`, create the private repo and capture the remote URL:

```bash
GH_USER=$(gh api user --jq .login)
gh repo create ${GH_USER}/<name>-vault --private --description "Personal knowledge vault"
REMOTE_URL="https://github.com/${GH_USER}/<name>-vault.git"
```

Use `$REMOTE_URL` as the `--remote` argument in Step 4.

## Step 3: Install Obsidian (If Missing)

If Obsidian was detected in Step 1, skip this step.

**Do NOT use `brew install --cask obsidian`.** Homebrew casks for Obsidian are frequently stale and the install fails due to SHA256 mismatches. Use the direct GitHub release download instead.

### macOS: direct DMG install

Ask for approval, then run:

```bash
# Detect arch (Obsidian ships a universal DMG — this selects the right asset name)
ARCH=$(uname -m)

# Get latest release metadata
OBSIDIAN_META=$(curl -s https://api.github.com/repos/obsidianmd/obsidian-releases/releases/latest)

# Find the macOS DMG URL (the .dmg asset without AppImage/.apk/.exe suffix)
OBSIDIAN_DMG_URL=$(echo "$OBSIDIAN_META" \
  | python3 -c "
import sys, json
assets = json.load(sys.stdin)['assets']
dmg = [a for a in assets if a['name'].endswith('.dmg') and not any(x in a['name'] for x in ['arm64','aarch64','AppImage','.apk','.exe'])]
print(dmg[0]['browser_download_url'])
")

# Download
curl -L "$OBSIDIAN_DMG_URL" -o /tmp/Obsidian.dmg

# Mount, copy, unmount
hdiutil attach /tmp/Obsidian.dmg -nobrowse -quiet
cp -R /Volumes/Obsidian/Obsidian.app /Applications/
hdiutil detach /Volumes/Obsidian -quiet
rm /tmp/Obsidian.dmg
```

If the mount point name differs from `/Volumes/Obsidian`, check `hdiutil attach` output for the actual mount path before copying.

### Linux or Windows

Print the download URL and continue without blocking:

> Download: <https://obsidian.md/download> — install manually, then open the vault folder when prompted in Step 9.

This workflow has been tested on macOS. Treat Linux and Windows paths as best-effort until contributors add and validate native install support.

## Step 4: Scaffold Vault

```bash
python3 scripts/scaffold_vault.py --name <name> --parent <parent> [--remote <URL>]
```

The vault directory will be `<parent>/<name>-vault`.

If the command exits nonzero (existing non-empty directory), **STOP** and ask the user:

- **Reuse** — proceed with the existing directory as-is (skip scaffold, continue from Step 5). First ensure the directory has its own git repo:
  ```bash
  [ -d <vault>/.git ] || git init <vault>
  ```
  Check the `vault_has_git` field in the error JSON — if false, run `git init <vault>` before continuing.
- **New name** — go back to Step 2 with a different name or parent
- **Abort** — stop the installation

If the scaffold output contains a `parent_repo_warning`, show it to the user so they know the vault lives inside another git repo and to double-check remotes.

### Fix GitHub host key (safe to re-run)

After git init and remote add, and before any push attempt, always run:

```bash
# Remove any stale github.com entry (GitHub rotated RSA key in March 2023)
ssh-keygen -R github.com 2>/dev/null || true
# Add the current ed25519 host key
ssh-keyscan -t ed25519 github.com >> ~/.ssh/known_hosts 2>/dev/null
```

This prevents "REMOTE HOST IDENTIFICATION HAS CHANGED" errors on machines set up before March 2023.

Do not auto-push. If `initial_commit` is true, tell the user: "Initial commit created. Push when ready: `git -C <vault> push -u origin main`". If `initial_commit` is false, tell the user the vault was scaffolded but the initial commit failed, show `initial_commit_error`, and suggest configuring git identity with `git config --global user.name` and `git config --global user.email` before rerunning `git -C <vault> commit --allow-empty -m "chore: initial vault scaffold"`.

## Step 4.5: Encryption (`crypt` Argument Only — Gate)

Skip this step unless the skill was invoked with the `crypt` argument. Read `references/encryption.md` first. Keep every user-facing message here to a few short lines — this flow takes the user at most two interactions. If git-crypt is missing (Step 1), install it first: `brew install git-crypt` (macOS).

1. **Detect and gate.** Run the dry-run and show a 3-line summary — detected mode (`fresh` / `migrate` / `unlock` / `noop`), the dirs to be encrypted, and (migrate only) the caveat that older commits keep plaintext:

   ```bash
   python3 scripts/setup_crypt.py --vault <vaultpath>
   ```

   Ask **Proceed** / **Cancel**. On `noop`, say encryption is already active and continue.

2. **Apply** — `python3 scripts/setup_crypt.py --vault <vaultpath> --apply`, then hand off the key (`key_out` in the JSON; surface `key_location_warning` if present). If `op` (1Password CLI) was found in Step 1, offer `op document create <key_out> --title "<name>-vault git-crypt key"`; otherwise tell the user: "Save `<key_out>` in 1Password (or your password manager) as a document — it's the only way to read the encrypted files." Once the user confirms it's saved, `rm <key_out>`. Do not proceed until confirmed.

   For **unlock** (second machine): ask the user to download the key from their password manager to a temporary path, then `python3 scripts/setup_crypt.py --vault <vaultpath> --unlock <keyfile> --apply && rm <keyfile>`.

3. **Verify:** `git -C <vaultpath> crypt status | head` shows `encrypted:` for the sensitive dirs. Do not auto-push; the push guidance from Step 4 applies.

## Step 5: Install Plugins

```bash
python3 scripts/install_plugins.py --vault <vaultpath>
```

This installs two community plugins:

- `realclaudian` (YishenTu/claudian) — Claudian sidebar for vault-aware context (plugin manifest ID is `realclaudian`)
- `obsidian-git` (Vinzent03/obsidian-git) — Git sync from within Obsidian

Optional flags: `--pin-claudian <TAG>` and `--pin-git <TAG>` to lock to specific release tags. `--dry-run` to preview without downloading.

If the command exits nonzero, show the manual fallback steps from `references/plugin-gui-fallback.md` and continue (plugin install failure is not fatal for the hook and CLAUDE.md steps).

## Step 5.5: Scheduled Sync (Gate)

Ask one question: "Enable automatic vault sync (pull + commit + push) every 15 minutes? (yes / no / custom interval)". If no, skip. Otherwise:

```bash
python3 scripts/install_sync.py --vault <vaultpath> --interval <seconds>
```

This configures both sync layers:

- **obsidian-git settings** (`<vault>/.obsidian/plugins/obsidian-git/data.json`, backed up first) — auto commit/pull every 10 minutes while Obsidian is open. Note: re-running re-enforces the sync keys listed in the JSON output (`enforced_settings`), overwriting manual changes to those specific keys; all other settings are preserved.
- **launchd agent** (macOS) — `~/.claude/hooks/vault-sync.sh` on the chosen interval, covering headless writes like the SessionEnd hook. The script is safe by construction: it skips when there's no remote, when a rebase/merge is in progress, or when a git-crypt checkout is locked. On Linux/Windows the JSON output includes a `cron_line` to add with `crontab -e` instead.

Requires a git remote to be useful — if the user chose local-only in Step 2, note that sync will silently no-op until they add a remote. Rollback: `python3 scripts/install_sync.py --uninstall`.

## Step 6: Install Hook and Register in Settings

Run this step only in **Claude Code** mode.

```bash
python3 scripts/install_hook.py --vault <vaultpath>
```

This renders `templates/session-end.sh.tmpl` with the vault path substituted, writes it to `~/.claude/hooks/session-end.sh` (chmod 755), and registers a `SessionEnd` hook entry in `~/.claude/settings.json`. A timestamped backup of `settings.json` is created before writing.

If the command exits nonzero with a malformed-JSON error, **STOP**. The script backed up the file automatically. Tell the user: "settings.json was malformed. Backed up to the path shown above. Fix the JSON manually (validate with `python3 -m json.tool ~/.claude/settings.json`), then re-run Step 6."

## Step 7: Merge CLAUDE.md Block

Run this step only in **Claude Code** mode.

```bash
python3 scripts/merge_claude_md.py --vault <vaultpath>
```

This upserts a managed block (bounded by `<!-- BEGIN memory-setup (memory) -->` / `<!-- END memory-setup (memory) -->`) into `~/.claude/CLAUDE.md`. The block teaches future Claude sessions where the vault is and how to navigate it. A timestamped backup of CLAUDE.md is created before writing.

Re-running is safe — the upsert is idempotent when the block is unchanged.

## Step 8: Handle claude-mem (Only If Detected — Gate)

Run this step only in **Claude Code** mode.

Skip this step if `claude_mem: false` was reported in Step 1.

If claude-mem was detected, explain the cost trade-off (reference `references/cost-benefit.md`) and ask the user:

- **Disable claude-mem** (reversible — settings.json backed up before any write)
- **Keep claude-mem** (both systems will run; expect higher token costs)
- **Decide later**

If the user chooses Disable:

1. Preview the plan (dry-run):

```bash
python3 scripts/cleanup_claude_mem.py
```

2. Show the plan output. Confirm with AskUserQuestion.
1. Apply:

```bash
python3 scripts/cleanup_claude_mem.py --apply
```

4. Print the rollback note from the output (restore `settings.json.bak-<timestamp>`).

## Step 9: Codex Session Capture (Compatibility)

Run this step only in **Codex** or **All / shared** mode.

Read `references/codex.md`, then run the importer path the installed Codex version supports:

- Prefer the scheduled pull importer against `~/.codex/sessions` when no true session-end hook is available:

```bash
python3 scripts/codex_session_importer.py --vault <vaultpath> --limit 3 --dry-run
```

- If this Codex version exposes a notify/session lifecycle, wire the importer there instead.
- Require `--dry-run --limit 3` output before any write.
- Track ingested ids in `~/.codex/.vault-ingested`.
- Append entries tagged `source: codex`; never write into `~/.claude` from this mode.

Verification:

- [ ] `~/.codex/sessions` exists or the user confirmed no local rollout history yet
- [ ] Dry-run shows the last 3 candidate sessions without transcript prose or secrets
- [ ] First real run appends a `(codex)` entry to `<vault>/sessions/<today>.md`
- [ ] Re-running skips already-ingested session ids

## Step 10: Antigravity Session Capture (Compatibility)

Run this step only in **Antigravity** or **All / shared** mode.

Read `references/antigravity.md`, then run the Antigravity path the installed version supports:

- Prefer `~/.gemini/config/hooks.json` when it has `SessionEnd`; install an idempotent importer hook:

```bash
python3 scripts/install_antigravity_hook.py --vault <vaultpath>
```

- Otherwise use the scheduled pull importer against `~/.gemini/antigravity/brain`:

```bash
python3 scripts/antigravity_session_importer.py --vault <vaultpath> --limit 3 --dry-run
```

- Require a dry-run preview before any write.
- Track ingested conversation ids in `~/.gemini/antigravity/.vault-ingested`.
- Append entries tagged `source: antigravity`; do not invent token totals.

Verification:

- [ ] `~/.gemini/antigravity/brain` exists or the user confirmed no local Antigravity history yet
- [ ] `~/.gemini/config/hooks.json` was inspected when present
- [ ] Dry-run shows candidate conversations without transcript prose or secrets
- [ ] First real run appends an `(antigravity)` entry to `<vault>/sessions/<today>.md`
- [ ] Re-running skips already-ingested conversation ids

## Step 11: Verify and Record Setup Notes

Print the following verification checklist for the user to work through:

**Checklist:**

- [ ] Shared vault exists at `<vault>` and has `index.md`
- [ ] `VAULT` env variable in Claude hook script matches the vault path: check `~/.claude/hooks/session-end.sh` line 15 (Claude mode only)
- [ ] `~/.claude/settings.json` has a `SessionEnd` entry with command `~/.claude/hooks/session-end.sh` (Claude mode only)
- [ ] `<vault>/.obsidian/community-plugins.json` lists both `realclaudian` and `obsidian-git`
- [ ] Open Obsidian → open the vault folder → trust and enable both plugins → confirm Claudian sidebar appears and Git commands are available in the command palette
- [ ] Run a session/import for the selected client, then check `<vault>/sessions/<today>.md` — should contain a metadata stub and a client-tagged entry
- [ ] `grep "memory-setup" ~/.claude/CLAUDE.md` returns the managed block (Claude mode only)
- [ ] (`crypt` only) `git -C <vault> crypt status | head` shows `encrypted:` for the sensitive dirs, and the key file is in the password manager with the local copy deleted
- [ ] (sync only) `launchctl list | grep vault-sync` shows the agent (macOS), and after the first interval `git -C <vault> log --oneline -1` shows a `chore(sync)` commit when there were pending changes

**Setup log:**

Append one short entry to `<vault>/setup-log.md` so the user can see what changed later:

- **Name:** `<name> setup`
- **Date:** today's date in ISO format
- **Client mode:** Claude Code, Codex, Antigravity, or shared
- **Issues hit:** bullet list of any problems encountered during this run, or "none"

Use `references/setup-tracking.md` for the recommended entry format. If the user has a preferred tracker (Notion, Linear, GitHub Issues, a team wiki), offer to translate the same entry there, but do not require an external service for the setup to be complete.

## Idempotency and Safety

Re-running this skill is safe:

- `install_hook.py` checks for an existing hook command and is a no-op if already registered; `settings.json` is backed up before every write
- `install_plugins.py` skips already-installed plugins unless `--force` is passed
- `merge_claude_md.py` replaces the managed block in place; surrounding content is preserved; CLAUDE.md is backed up before every write
- `scaffold_vault.py` exits nonzero on a non-empty existing directory — it never overwrites
- `cleanup_claude_mem.py` is dry-run by default and requires `--apply` to make changes
- `setup_crypt.py` is dry-run by default and requires `--apply`; it refuses to export the key inside the vault, is a no-op when encryption is already active, and never prints key material
- `install_sync.py` re-renders the same files in place (reload is idempotent), backs up `data.json` before writing, and `--uninstall` removes everything it installed
- Codex and Antigravity importers must use state files and dry-run previews before appending to the vault
- No git force-push is ever issued

## Scope

Shared setup writes only to:

- `<parent>/<name>-vault/` — the new vault directory

Claude Code mode may also write to:

- `~/.claude/hooks/session-end.sh` — the hook script
- `~/.claude/settings.json` — hook registration (backed up first)
- `~/.claude/CLAUDE.md` — memory block upsert (backed up first)

The `crypt` argument may also write to:

- `<vault>/.gitattributes` — managed git-crypt block (upserted in place)
- `<vault-parent>/<name>-vault.gitcrypt.key` — exported key (user deletes after saving to a password manager)

The scheduled-sync step may also write to:

- `<vault>/.obsidian/plugins/obsidian-git/data.json` — sync settings (backed up first; gitignored)
- `~/.claude/hooks/vault-sync.sh` and `~/.claude/logs/vault-sync.log` — sync script and its log
- `~/Library/LaunchAgents/com.<user>.vault-sync.plist` — launchd agent (macOS)

## Multi-Machine Quickstart

Setting up a second machine against an existing encrypted vault:

1. Install the plugin, then run `/memory:memory-setup crypt`.
2. In Step 2, choose **B** and give the existing remote URL. **Skip Step 4's scaffold entirely** — on a machine where the vault path doesn't exist yet, scaffolding would create a fresh empty vault instead of erroring. Clone instead: `git clone <remote> <vault>`.
3. Step 4.5 detects `unlock` mode — download the key from your password manager, unlock, delete the key file.
4. Continue with Steps 5–7 (plugins, hook) and 5.5 (sync) as normal. The scheduled sync keeps both machines converged via pull-rebase/commit/push.

Codex mode may also write to:

- `~/.codex/.vault-ingested` — ingested session id state

Antigravity mode may also write to:

- `~/.gemini/config/hooks.json` and a sidecar hook script — only when wiring a supported `SessionEnd` hook, backed up first
- `~/.gemini/antigravity/.vault-ingested` — ingested conversation id state
