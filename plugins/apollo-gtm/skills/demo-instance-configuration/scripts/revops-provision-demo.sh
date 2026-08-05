#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 3 ] || [ "$#" -gt 5 ]; then
  echo "Usage: $0 EMAIL USER_NAME TEAM_NAME [MASTER_TEAM_USER_EMAIL] [MASTER_TEAM_ID]" >&2
  echo "  MASTER_TEAM_USER_EMAIL defaults to the dedicated provisioning service user;" >&2
  echo "  pass it only to deliberately attribute creation to a different Testbox user." >&2
  exit 2
fi

# Fail early and clearly on a missing dependency, rather than mid-provisioning
# with an opaque error (jq is used for both the expiry check and payload build).
missing=""
for tool in jq curl; do
  command -v "$tool" >/dev/null 2>&1 || missing="$missing $tool"
done
if [ -n "$missing" ]; then
  echo "Missing required tool(s):$missing" >&2
  echo "This script needs: jq, curl. The OAuth helper additionally needs: openssl, python3." >&2
  exit 3
fi

OWNER_EMAIL="$1"
USER_NAME="$2"
TEAM_NAME="$3"
# Dedicated provisioning service user in the Testbox instance — decided 2026-07-30
# (Jared + Andrew 1:1). Every demo sub-account is attributed to this one identity
# rather than to the individual SC. Per-SC attribution isn't lost in any meaningful
# way: the pre-existing placeholder users gave no real audit trail either, and any
# *manual* change to a demo instance requires God mode, which is attributed to the
# real person. Interim by agreement — revisit if infosec objects, or once TestBox
# provides unique per-user identities (Andrew is setting that expectation with them).
MASTER_TEAM_USER_EMAIL="${4:-tailored-demo-sub-accounts@apollo.io}"
MASTER_TEAM_ID="${5:-}"
CONFIG_DIR="$HOME/.config/apollo-provision"
CREDENTIALS_FILE="$CONFIG_DIR/credentials"
OAUTH_HELPER="$(cd -- "$(dirname -- "$0")" && pwd)/revops-oauth-login.sh"
ENDPOINT="https://app.apollo.io/api/v1/teams/provision_demo_account_with_api_key"

# Apollo's token response uses `created_at` (epoch seconds) + `expires_in` (seconds).
# It does NOT return `expires_at` — an earlier version of this check tested that field,
# so it was always null, every cached token read as valid forever, and expiry was only
# ever discovered via a 401 on the provisioning call itself.
# A 60s safety margin avoids racing an expiry mid-request.
load_access_token() {
  [ -r "$CREDENTIALS_FILE" ] || return 1
  jq -e '.access_token and .created_at and .expires_in
         and ((.created_at + .expires_in) > (now + 60))' \
     "$CREDENTIALS_FILE" >/dev/null 2>&1 || return 1
  ACCESS_TOKEN="$(jq -r '.access_token' "$CREDENTIALS_FILE")"
}

# Apollo returns a refresh_token; use it before falling back to the interactive
# browser flow. Silent refresh matters here — the interactive consent step is the
# one part of provisioning that needs a live human, so avoiding it when possible
# keeps this usable inside an automated run.
refresh_access_token() {
  [ -r "$CREDENTIALS_FILE" ] || return 1
  local refresh_token response
  refresh_token="$(jq -r '.refresh_token // empty' "$CREDENTIALS_FILE")"
  [ -n "$refresh_token" ] || return 1

  response="$(curl -sS -X POST "https://app.apollo.io/api/v1/oauth/token" \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    --data-urlencode grant_type=refresh_token \
    --data-urlencode "refresh_token=$refresh_token" \
    --data-urlencode "client_id=${APOLLO_OAUTH_CLIENT_ID:-nflLVHGuyXB2sdh6F8dp7hO4aECHcewPl-pOygNDi7w}" 2>/dev/null)" || return 1

  printf '%s' "$response" | jq -e '.access_token' >/dev/null 2>&1 || return 1
  mkdir -p "$CONFIG_DIR"; chmod 700 "$CONFIG_DIR"
  printf '%s' "$response" > "$CREDENTIALS_FILE"
  chmod 600 "$CREDENTIALS_FILE"
  load_access_token
}

authenticate() {
  # Try a silent refresh first; only open a browser if that isn't possible.
  if refresh_access_token; then
    echo "Access token refreshed silently (no browser needed)."
    return 0
  fi
  bash "$OAUTH_HELPER"
  load_access_token || { echo "OAuth completed but no usable credential was saved" >&2; exit 1; }
}

build_payload() {
  jq -n \
    --arg email "$OWNER_EMAIL" \
    --arg user_name "$USER_NAME" \
    --arg name "$TEAM_NAME" \
    --arg acting_user "$MASTER_TEAM_USER_EMAIL" \
    --arg master_team_id "$MASTER_TEAM_ID" \
    '{
      email: $email,
      user_name: $user_name,
      name: $name,
      revops_sandbox_master_team_user_email: $acting_user
    } + (if $master_team_id == "" then {} else {revops_sandbox_master_team_id: $master_team_id} end)'
}

provision() {
  local response_file status
  response_file="$(mktemp)"

  status="$(curl -sS -o "$response_file" -w '%{http_code}' -X POST "$ENDPOINT" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H 'Content-Type: application/json' \
    --data "$(build_payload)")"

  if [ "$status" = "201" ]; then
    cat "$response_file"
    rm -f "$response_file"
    return 0
  fi

  if [ "$status" = "401" ]; then
    rm -f "$response_file"
    return 10
  fi

  echo "Provisioning failed (HTTP $status):" >&2
  cat "$response_file" >&2
  rm -f "$response_file"
  return 1
}

if [ "${APOLLO_FORCE_OAUTH:-false}" = "true" ] || ! load_access_token; then
  authenticate
fi

set +e
provision
status=$?
set -e
if [ "$status" -eq 10 ]; then
  authenticate
  provision
elif [ "$status" -ne 0 ]; then
  exit "$status"
fi
