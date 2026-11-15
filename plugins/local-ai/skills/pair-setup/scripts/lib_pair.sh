#!/usr/bin/env bash

# Pure helpers and reviewed constants for the pair-setup skill.

# PAIR 1.0 and its auto-updater install as "NVIDIA PAIR.app"; 0.1.x was "PAIR.app".
if [ -z "${PAIR_APP:-}" ]; then
  if [ -d "/Applications/NVIDIA PAIR.app" ]; then
    PAIR_APP="/Applications/NVIDIA PAIR.app"
  else
    PAIR_APP="/Applications/PAIR.app"
  fi
fi
PAIR_VERSION="0.1.1"
PAIR_DMG_BASE="https://github.com/NVIDIA/Personal-AI-Router/releases/download/v${PAIR_VERSION}"
PAIR_EXPECT_ID="com.nvidia.nvpair"
PAIR_EXPECT_TEAM="6KR3T733EC"
PAIR_PROXY_PORT=11434
PAIR_ENGINE_PORT=11435
# Node-to-node pairing and discovery service (mDNS-advertised). Peers must reach
# this TCP port; ping and 11434/11435 are not valid peer checks.
PAIR_NODE_PORT=14318

# Map `uname -m` to the release asset architecture suffix.
pair_arch() {
  case "${1:-}" in
    arm64) echo arm64 ;;
    x86_64) echo x64 ;;
    *) return 1 ;;
  esac
}

# SHA-256 of the reviewed disk image for an asset architecture.
pair_dmg_sha256() {
  case "${1:-}" in
    arm64) echo "ee719fd699308c87e289f799cd780b799636343865638e8af65a57b953cb3f44" ;;
    x64) echo "fc1679d50fd94dab892b637ae3a5db482837b3c5d13861b22df88cd4bbf97fb4" ;;
    *) return 1 ;;
  esac
}

pair_dmg_url() {
  [ -n "${1:-}" ] || return 1
  echo "${PAIR_DMG_BASE}/NVPAIR-Setup-${PAIR_VERSION}-$1.dmg"
}

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
    ollama-proxy|nvpair-proxy) echo ok ;;
    ollama) echo bypassed ;;
    "") echo absent ;;
    *) echo foreign ;;
  esac
}
