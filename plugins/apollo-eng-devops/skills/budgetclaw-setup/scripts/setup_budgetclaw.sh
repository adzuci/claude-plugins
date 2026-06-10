#!/usr/bin/env bash
set -euo pipefail

CAP="${1:-27}"
if ! [[ "$CAP" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
  echo "CAP must be a numeric USD value, got: $CAP" >&2
  exit 2
fi

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "budgetclaw-setup currently supports macOS only because it uses launchd + terminal-notifier." >&2
  exit 2
fi

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is required. Install Homebrew first, then rerun this script." >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BREW_PREFIX="$(brew --prefix)"
BUDGETCLAW_BIN="${BREW_PREFIX}/bin/budgetclaw"
BRIDGE_SRC="${SCRIPT_DIR}/notify_bridge.py"
BRIDGE_DIR="${HOME}/.local/share/budgetclaw"
BRIDGE_DST="${BRIDGE_DIR}/notify_bridge.py"
STATE_DIR="${HOME}/.local/state/budgetclaw"
CONFIG_DIR="${HOME}/.config/budgetclaw"
CONFIG_FILE="${CONFIG_DIR}/config.toml"
LAUNCH_AGENTS="${HOME}/Library/LaunchAgents"
WATCH_PLIST="${LAUNCH_AGENTS}/org.roninforge.budgetclaw.plist"
NOTIFY_PLIST="${LAUNCH_AGENTS}/org.roninforge.budgetclaw-notify.plist"

detect_iana_timezone() {
  local tz=""
  tz="$(readlink /etc/localtime 2>/dev/null | sed 's#.*/zoneinfo/##' || true)"
  case "$tz" in
    */*) printf '%s\n' "$tz" ;;
    *) printf '\n' ;;
  esac
}

write_config() {
  local timezone="$1"
  mkdir -p "$CONFIG_DIR"
  {
    echo "[general]"
    if [[ -n "$timezone" ]]; then
      printf '  timezone = "%s"\n' "$timezone"
    fi
    cat <<EOF

[alerts]
  [alerts.ntfy]
    server = "http://127.0.0.1:8410"
    topic = "budgetclaw-local"
    min_cost_usd = 0.5

[[limit]]
  project = "*"
  branch = "*"
  period = "daily"
  cap_usd = ${CAP}
  action = "warn"
EOF
  } >"$CONFIG_FILE"
}

write_plists() {
  mkdir -p "$LAUNCH_AGENTS" "$STATE_DIR"

  cat >"$NOTIFY_PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>org.roninforge.budgetclaw-notify</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>${BRIDGE_DST}</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>ProcessType</key>
  <string>Background</string>
  <key>StandardOutPath</key>
  <string>${STATE_DIR}/notify.out.log</string>
  <key>StandardErrorPath</key>
  <string>${STATE_DIR}/notify.err.log</string>
</dict>
</plist>
EOF

  cat >"$WATCH_PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>org.roninforge.budgetclaw</string>
  <key>ProgramArguments</key>
  <array>
    <string>${BUDGETCLAW_BIN}</string>
    <string>watch</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>ProcessType</key>
  <string>Background</string>
  <key>StandardOutPath</key>
  <string>${STATE_DIR}/watch.out.log</string>
  <key>StandardErrorPath</key>
  <string>${STATE_DIR}/watch.err.log</string>
</dict>
</plist>
EOF
}

reload_agent() {
  local plist="$1"
  launchctl unload "$plist" >/dev/null 2>&1 || true
  launchctl load "$plist"
}

echo "Installing budgetclaw and terminal-notifier..."
brew install roninforge/tap/budgetclaw terminal-notifier

echo "Initializing budgetclaw..."
"$BUDGETCLAW_BIN" init || true
"$BUDGETCLAW_BIN" backfill

timezone="$(detect_iana_timezone)"
if [[ -z "$timezone" ]]; then
  echo "Could not auto-detect an IANA timezone; budgetclaw will use UTC unless you edit ${CONFIG_FILE}."
else
  echo "Detected timezone: $timezone"
fi

echo "Writing config, bridge, and launchd agents..."
mkdir -p "$BRIDGE_DIR"
install -m 0755 "$BRIDGE_SRC" "$BRIDGE_DST"
write_config "$timezone"
write_plists

echo "Loading launchd agents..."
reload_agent "$NOTIFY_PLIST"
reload_agent "$WATCH_PLIST"

echo "Done. Verify with:"
echo "  launchctl list | grep budgetclaw"
echo "  lsof -nP -iTCP:8410 -sTCP:LISTEN"
echo "  budgetclaw status"
