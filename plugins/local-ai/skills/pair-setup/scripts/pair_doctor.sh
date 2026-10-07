#!/usr/bin/env bash

# Read-only health check for one PAIR node.
# Usage: pair_doctor.sh --role host|client [--probe]

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib_pair.sh
. "$HERE/lib_pair.sh"

ROLE=""
PROBE=0
FAILURES=0
WARNINGS=0

pass() { printf '  PASS  %s\n' "$*"; }
warn() { printf '  WARN  %s\n' "$*"; WARNINGS=$((WARNINGS + 1)); }
fail() { printf '  FAIL  %s\n' "$*"; FAILURES=$((FAILURES + 1)); }
info() { printf '        %s\n' "$*"; }
heading() { printf '\n%s\n' "$*"; }
usage() { printf '%s\n' "Usage: pair_doctor.sh --role host|client [--probe]"; }

listener() {
  local pid command
  pid="$(lsof -nP -iTCP:"$1" -sTCP:LISTEN -Fp 2>/dev/null \
    | sed -n 's/^p//p' | head -1)"
  [ -n "$pid" ] || return 0
  command="$(ps -p "$pid" -o comm= 2>/dev/null | awk 'NR == 1 {print $1}')"
  [ -n "$command" ] && basename "$command"
}

main() {
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --role)
        [ "$#" -ge 2 ] && [ -n "${2:-}" ] \
          || { printf '%s\n' "--role requires host or client" >&2; exit 2; }
        ROLE="$2"
        shift 2
        ;;
      --probe) PROBE=1; shift ;;
      -h|--help) usage; exit 0 ;;
      *) printf 'unknown argument: %s\n' "$1" >&2; exit 2 ;;
    esac
  done

  ROLE="$(validate_role "$ROLE")" \
    || { printf '%s\n' "--role must be host or client" >&2; exit 2; }
  [ "$(uname -s)" = "Darwin" ] \
    || { printf '%s\n' "PAIR doctor currently supports macOS only" >&2; exit 2; }

  heading "Machine"
  info "$(sw_vers -productName) $(sw_vers -productVersion) ($(uname -m))"
  info "role: $ROLE (declared)"
  info "memory: $(( $(sysctl -n hw.memsize) / 1073741824 )) GB"

  heading "PAIR installation"
  if [ ! -d "$PAIR_APP" ]; then
    fail "$PAIR_APP not found"
  else
    pass "$PAIR_APP present ($(bundle_version "$PAIR_APP" || echo '?'))"
    local identifier team
    identifier="$(codesign -dv --verbose=4 "$PAIR_APP" 2>&1 \
      | sed -n 's/^Identifier=//p' | head -1)"
    team="$(codesign -dv --verbose=4 "$PAIR_APP" 2>&1 \
      | sed -n 's/^TeamIdentifier=//p' | head -1)"
    [ "$identifier" = "$PAIR_EXPECT_ID" ] \
      && pass "bundle identifier $identifier" \
      || fail "unexpected bundle identifier '$identifier'"
    [ "$team" = "$PAIR_EXPECT_TEAM" ] \
      && pass "signing team $team" \
      || fail "unexpected signing team '$team'"
    codesign --verify --deep --strict "$PAIR_APP" >/dev/null 2>&1 \
      && pass "application signature valid" \
      || fail "application signature invalid"
  fi

  heading "Ports"
  case "$(classify_listener "$(listener "$PAIR_PROXY_PORT")")" in
    ok) pass "$PAIR_PROXY_PORT is owned by ollama-proxy" ;;
    bypassed) fail "$PAIR_PROXY_PORT is owned by bare Ollama; PAIR is bypassed" ;;
    absent) fail "$PAIR_PROXY_PORT has no listener" ;;
    foreign) fail "$PAIR_PROXY_PORT is owned by an unexpected process" ;;
  esac

  if [ "$ROLE" = "host" ]; then
    [ -n "$(listener "$PAIR_ENGINE_PORT")" ] \
      && pass "$PAIR_ENGINE_PORT has an engine listener" \
      || warn "$PAIR_ENGINE_PORT has no engine listener"
  else
    [ -n "$(listener "$PAIR_ENGINE_PORT")" ] \
      && warn "client has a local engine and may serve requests locally" \
      || pass "client has no local engine"
  fi

  if [ "$ROLE" = "host" ]; then
    heading "Host readiness"
    local sleep_value
    sleep_value="$(pmset -g custom 2>/dev/null \
      | awk '/^AC Power/,/^Battery/' \
      | awk '$1 == "sleep" {print $2; exit}')"
    [ "${sleep_value:-}" = "0" ] \
      && pass "AC sleep disabled" \
      || warn "AC sleep is '${sleep_value:-unknown}'"
  fi

  if [ "$PROBE" = "1" ]; then
    heading "Local endpoint probe (not routing proof)"
    local response
    response="$(curl -s --max-time 10 \
      "http://127.0.0.1:$PAIR_PROXY_PORT/v1/models" 2>/dev/null)"
    if printf '%s' "$response" | python3 -c '
import json
import sys

data = json.load(sys.stdin)
sys.exit(0 if isinstance(data.get("data"), list) else 1)
' 2>/dev/null; then
      pass "endpoint returned a model list"
    else
      fail "endpoint did not return a usable model list"
    fi
    info "Bare Ollama can answer this probe. Confirm PAIR's Jobs view says"
    info "'Ran on <peer name>' before reporting remote routing as verified."
  fi

  heading "Verdict"
  printf '  %s failure(s), %s warning(s)\n' "$FAILURES" "$WARNINGS"
  [ "$FAILURES" -eq 0 ]
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  main "$@"
fi
