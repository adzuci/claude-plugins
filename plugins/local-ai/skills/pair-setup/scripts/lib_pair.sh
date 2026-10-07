#!/usr/bin/env bash

# Pure helpers and reviewed constants for the pair-setup skill.

PAIR_APP="${PAIR_APP:-/Applications/PAIR.app}"
PAIR_VERSION="0.1.1"
PAIR_DMG_URL="https://github.com/NVIDIA/Personal-AI-Router/releases/download/v${PAIR_VERSION}/NVPAIR-Setup-${PAIR_VERSION}-arm64.dmg"
PAIR_DMG_SHA256="ee719fd699308c87e289f799cd780b799636343865638e8af65a57b953cb3f44"
PAIR_EXPECT_ID="com.nvidia.nvpair"
PAIR_EXPECT_TEAM="6KR3T733EC"
PAIR_PROXY_PORT=11434
PAIR_ENGINE_PORT=11435

parse_mount_point() {
  printf '%s' "${1:-}" | python3 -c '
import json
import sys

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(1)

entities = data.get("system-entities", data) if isinstance(data, dict) else data
if not isinstance(entities, list):
    sys.exit(1)
for entity in entities:
    if isinstance(entity, dict) and entity.get("mount-point"):
        print(entity["mount-point"])
        sys.exit(0)
sys.exit(1)
' 2>/dev/null
}

bundle_version() {
  local app="${1:-}"
  [ -n "$app" ] && [ -f "$app/Contents/Info.plist" ] || return 1
  /usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' \
    "$app/Contents/Info.plist" 2>/dev/null
}

should_reinstall() {
  local current="${1:-}" candidate="${2:-}" force="${3:-0}" valid="${4:-0}"
  [ "$force" = "1" ] && { echo yes; return; }
  [ -z "$current" ] && { echo yes; return; }
  [ "$valid" != "1" ] && { echo yes; return; }
  [ "$current" != "$candidate" ] && { echo yes; return; }
  echo no
}

validate_role() {
  case "${1:-}" in
    host|client) printf '%s' "$1" ;;
    *) return 1 ;;
  esac
}

classify_listener() {
  case "${1:-}" in
    ollama-proxy) echo ok ;;
    ollama) echo bypassed ;;
    "") echo absent ;;
    *) echo foreign ;;
  esac
}
