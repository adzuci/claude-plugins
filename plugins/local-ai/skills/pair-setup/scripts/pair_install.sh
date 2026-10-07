#!/usr/bin/env bash

# Safely install the reviewed NVIDIA PAIR release on Apple Silicon macOS.
# Usage: pair_install.sh [--check | --apply] [--dmg PATH] [--force]

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib_pair.sh
. "$HERE/lib_pair.sh"

DMG=""
CHECK=0
APPLY=0
FORCE=0
MOUNT_POINT=""
DEVICE=""
OWNED_TMP=""
STAGE=""
BACKUP=""

note() { printf '  %s\n' "$*"; }
die() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
usage() {
  printf '%s\n' "Usage: pair_install.sh [--check | --apply] [--dmg PATH] [--force]"
}

cleanup() {
  if [ -n "$DEVICE" ]; then
    hdiutil detach "$DEVICE" -quiet 2>/dev/null \
      || hdiutil detach "$DEVICE" -force -quiet 2>/dev/null \
      || true
  fi
  [ -n "$STAGE" ] && [ -d "$STAGE" ] && rm -rf -- "$STAGE"
  if [ -n "$BACKUP" ] && [ -d "$BACKUP" ] && [ ! -d "$PAIR_APP" ]; then
    mv "$BACKUP" "$PAIR_APP" 2>/dev/null \
      && printf '  restored previous installation\n' >&2
  fi
  [ -n "$BACKUP" ] && [ -d "$BACKUP" ] && rm -rf -- "$BACKUP"
  [ -n "$OWNED_TMP" ] && [ -d "$OWNED_TMP" ] && rm -rf -- "$OWNED_TMP"
  DEVICE=""
  STAGE=""
  BACKUP=""
  OWNED_TMP=""
}

trap cleanup EXIT
trap 'cleanup; exit 130' INT
trap 'cleanup; exit 143' TERM

bundle_valid() {
  codesign --verify --deep --strict "${1:-}" >/dev/null 2>&1
}

verify_digest() {
  local dmg="$1" actual
  actual="$(shasum -a 256 "$dmg" 2>/dev/null | awk '{print $1}')" || return 1
  [ "$actual" = "$PAIR_DMG_SHA256" ]
}

verify_bundle() {
  local app="$1" identifier team
  identifier="$(codesign -dv --verbose=4 "$app" 2>&1 \
    | sed -n 's/^Identifier=//p' | head -1)"
  team="$(codesign -dv --verbose=4 "$app" 2>&1 \
    | sed -n 's/^TeamIdentifier=//p' | head -1)"
  [ "$identifier" = "$PAIR_EXPECT_ID" ] \
    || { printf "identifier '%s' != %s\n" "$identifier" "$PAIR_EXPECT_ID"; return 1; }
  [ "$team" = "$PAIR_EXPECT_TEAM" ] \
    || { printf "team '%s' != %s\n" "$team" "$PAIR_EXPECT_TEAM"; return 1; }
  bundle_valid "$app" || { printf 'signature invalid\n'; return 1; }
  spctl -a -t install "$app" >/dev/null 2>&1 \
    || { printf 'Gatekeeper rejected the application\n'; return 1; }
}

preflight_platform() {
  [ "$(uname -s)" = "Darwin" ] || die "PAIR setup currently supports macOS only"
  [ "$(uname -m)" = "arm64" ] || die "this installer is pinned to the Apple Silicon release"
}

main() {
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --check) CHECK=1; shift ;;
      --apply) APPLY=1; shift ;;
      --dmg)
        [ "$#" -ge 2 ] && [ -n "${2:-}" ] \
          || { printf '%s\n' "--dmg requires a path" >&2; exit 2; }
        DMG="$2"
        shift 2
        ;;
      --force) FORCE=1; shift ;;
      -h|--help) usage; exit 0 ;;
      *) printf 'unknown argument: %s\n' "$1" >&2; exit 2 ;;
    esac
  done

  preflight_platform

  local current valid=0
  current="$(bundle_version "$PAIR_APP" || true)"
  if [ -n "$current" ]; then
    bundle_valid "$PAIR_APP" && valid=1
    note "installed: $PAIR_APP ($current, signature $([ "$valid" = 1 ] && echo valid || echo INVALID))"
  else
    note "installed: none"
  fi
  note "reviewed release: v$PAIR_VERSION"
  note "download: $PAIR_DMG_URL"
  note "sha256: $PAIR_DMG_SHA256"

  if [ "$CHECK" = "1" ] || [ "$APPLY" = "0" ]; then
    if [ -n "$current" ]; then
      spctl -a -t install "$PAIR_APP" >/dev/null 2>&1 \
        && note "gatekeeper: accepted" \
        || note "gatekeeper: rejected"
    fi
    [ "$CHECK" = "0" ] \
      && note "read-only default; rerun with --apply after confirmation"
    exit 0
  fi

  if [ -z "$DMG" ]; then
    OWNED_TMP="$(mktemp -d)" || die "could not create a temporary directory"
    DMG="$OWNED_TMP/NVPAIR.dmg"
    note "downloading PAIR v$PAIR_VERSION"
    curl -fsSL -o "$DMG" "$PAIR_DMG_URL" || die "download failed"
  fi
  [ -f "$DMG" ] || die "disk image not found: $DMG"

  verify_digest "$DMG" || die "disk image digest does not match the reviewed release"
  note "disk image digest verified"
  xcrun stapler validate "$DMG" >/dev/null 2>&1 \
    || die "notarization ticket missing or invalid"
  spctl -a -t open --context context:primary-signature "$DMG" >/dev/null 2>&1 \
    || die "Gatekeeper rejected the disk image"
  note "notarization and Gatekeeper checks passed"

  local plist json source candidate reason
  plist="$(hdiutil attach "$DMG" -nobrowse -readonly -plist 2>/dev/null)" \
    || die "could not attach the disk image"
  DEVICE="$(printf '%s' "$plist" \
    | sed -n 's:.*<string>\(/dev/disk[0-9]*\)</string>.*:\1:p' | head -1)"
  json="$(printf '%s' "$plist" | plutil -convert json -o - - 2>/dev/null)" \
    || die "could not parse disk image metadata"
  MOUNT_POINT="$(parse_mount_point "$json")" \
    || die "disk image metadata did not contain a mount point"
  [ -d "$MOUNT_POINT" ] || die "mount point does not exist: $MOUNT_POINT"

  source="$MOUNT_POINT/PAIR.app"
  [ -d "$source" ] || die "PAIR.app was not present in the disk image"
  candidate="$(bundle_version "$source" || echo unknown)"
  note "disk image version: $candidate"

  if [ "$(should_reinstall "$current" "$candidate" "$FORCE" "$valid")" = "no" ]; then
    note "$current is already installed and valid; use --force to reinstall"
    exit 0
  fi

  STAGE="$(dirname "$PAIR_APP")/.local-ai-pair-staging-$$.app"
  rm -rf -- "$STAGE"
  ditto "$source" "$STAGE" || die "could not stage the application"
  xattr -dr com.apple.quarantine "$STAGE" 2>/dev/null || true
  reason="$(verify_bundle "$STAGE")" \
    || die "staged application failed verification: $reason"

  if [ -d "$PAIR_APP" ]; then
    BACKUP="$(dirname "$PAIR_APP")/.local-ai-pair-backup-$$.app"
    mv "$PAIR_APP" "$BACKUP" || die "could not move the existing application aside"
  fi
  mv "$STAGE" "$PAIR_APP" || die "could not move the new application into place"
  STAGE=""
  [ -n "$BACKUP" ] && { rm -rf -- "$BACKUP"; BACKUP=""; }

  note "installed $candidate and verified its signature"
  note "next: launch PAIR and approve the privileged helper"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  main "$@"
fi
