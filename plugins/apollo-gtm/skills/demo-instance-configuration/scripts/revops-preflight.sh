#!/usr/bin/env bash
# Step Zero environment preflight for demo-instance-configuration (added 2026-09-24).
#
# Prints exactly one result line on stdout and exits with its code:
#   PREFLIGHT_OK                                  0   Claude Code, and both Apollo hosts answered as Apollo
#   PREFLIGHT_NOT_CLAUDE_CODE                     10  this shell was not spawned by Claude Code
#   PREFLIGHT_APOLLO_UNREACHABLE <host>:<reason>  20  Claude Code, but a host did not answer as Apollo
#
# Two unauthenticated GETs. Carries no credential, reads and writes no file outside a
# temp header dump, and creates nothing in Apollo.
set -uo pipefail

# Claude Code documents CLAUDECODE=1 in every Bash subprocess it spawns. Claude.ai Chat
# and Cowork shells were probed on 2026-09-24 and do not set it. Cowork does have the
# Agent tool and lists Democles, so this is the only check that tells it apart.
if [ "${CLAUDECODE:-}" != "1" ]; then
  echo "PREFLIGHT_NOT_CLAUDE_CODE"
  exit 10
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "PREFLIGHT_APOLLO_UNREACHABLE curl:missing"
  exit 20
fi

# Match on a positive Apollo answer, never on "any HTTP response". Sandbox egress
# proxies answer with real HTTP themselves: Chat's returned 403 text/plain with
# x-deny-reason and curl exit 0; Cowork's failed the CONNECT (exit 56, code 000) with
# X-Proxy-Error. Apollo answers an unauthenticated call with JSON. Exact status codes
# are deliberately not pinned - if Apollo changed one, every SC would be stopped.
check_host() {
  local host="$1" hdr result rc code ctype
  hdr="$(mktemp)"
  result="$(curl -s -m 10 -o /dev/null -D "$hdr" -w '%{http_code} %{content_type}' \
    "https://${host}/api/v1/users/api_profile")"
  rc=$?
  code="${result%% *}"
  ctype="${result#* }"
  if grep -qiE '^(x-deny-reason|x-proxy-error|x-[a-z-]*(deny|block)[a-z-]*):' "$hdr"; then
    rm -f "$hdr"; echo "${host}:proxy-blocked"; return 1
  fi
  rm -f "$hdr"
  if [ "$rc" -ne 0 ]; then
    echo "${host}:curl-exit-${rc}"; return 1
  fi
  if [ "$code" = "000" ] || [ "$code" = "407" ]; then
    echo "${host}:http-${code}"; return 1
  fi
  case "$ctype" in
    application/json*) return 0 ;;
    *) echo "${host}:non-apollo-response-${code}"; return 1 ;;
  esac
}

failures=""
for host in app.apollo.io api.apollo.io; do
  if ! reason="$(check_host "$host")"; then
    failures="${failures:+$failures }$reason"
  fi
done

if [ -n "$failures" ]; then
  echo "PREFLIGHT_APOLLO_UNREACHABLE $failures"
  exit 20
fi
echo "PREFLIGHT_OK"
exit 0
