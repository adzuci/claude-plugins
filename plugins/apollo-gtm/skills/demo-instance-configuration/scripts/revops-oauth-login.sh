#!/usr/bin/env bash
set -euo pipefail

# Fixed public PKCE OAuth client for demo-instance-configuration's provisioning step
# ("Internal RevOps Demo Provisioning", registered via developer.apollo.io, migration-enabled
# by Debanjan 2026-07-27). Public client, no secret — safe to embed the client ID here.
missing=""
for tool in openssl curl python3; do
  command -v "$tool" >/dev/null 2>&1 || missing="$missing $tool"
done
if [ -n "$missing" ]; then
  echo "Missing required tool(s):$missing" >&2
  echo "The OAuth flow needs: openssl (PKCE challenge), curl (token exchange), python3 (localhost callback listener)." >&2
  exit 3
fi

CLIENT_ID="${APOLLO_OAUTH_CLIENT_ID:-nflLVHGuyXB2sdh6F8dp7hO4aECHcewPl-pOygNDi7w}"
AUTH_BASE_URL="${AUTH_BASE_URL:-https://mcp.apollo.io}"
API_BASE_URL="${API_BASE_URL:-https://app.apollo.io}"
REDIRECT_URI="http://localhost:3421/callback"
STATE="$(openssl rand -hex 16)"
VERIFIER="$(openssl rand -base64 32 | tr '+/' '-_' | tr -d '=\n')"
CHALLENGE="$(printf '%s' "$VERIFIER" | openssl dgst -sha256 -binary | base64 | tr '+/' '-_' | tr -d '=\n')"

TMP_DIR=""
trap '[ -z "$TMP_DIR" ] || rm -rf "$TMP_DIR"' EXIT

start_python_callback_listener() {
  TMP_DIR="$(mktemp -d)"
  python3 - "$TMP_DIR/callback" <<'PY' &
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

output = sys.argv[1]

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        with open(output, "w") as f:
            f.write("http://localhost:3421" + self.path)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Authorization complete. You can close this tab.")
        threading.Thread(target=self.server.shutdown, daemon=True).start()

    def log_message(self, *_):
        pass

HTTPServer(("127.0.0.1", 3421), Handler).serve_forever()
PY
  SERVER_PID=$!
}

wait_for_python_callback() {
  while [ ! -s "$TMP_DIR/callback" ]; do
    kill -0 "$SERVER_PID" 2>/dev/null || return 1
    sleep 0.1
  done
  wait "$SERVER_PID" || true
  CALLBACK_URL="$(cat "$TMP_DIR/callback")"
}

AUTH_URL="$AUTH_BASE_URL/mcp/oauth_metadata/redirect_to_authorize?client_id=$CLIENT_ID&redirect_uri=http%3A%2F%2Flocalhost%3A3421%2Fcallback&response_type=code&scope=revops_demo_provision&code_challenge=$CHALLENGE&code_challenge_method=S256&state=$STATE"

USE_PYTHON=0
if command -v python3 >/dev/null 2>&1; then
  USE_PYTHON=1
  start_python_callback_listener
fi

if command -v open >/dev/null 2>&1; then
  open "$AUTH_URL"
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$AUTH_URL" >/dev/null 2>&1
else
  echo "Open this URL in your browser:"
  echo "$AUTH_URL"
fi

if [ "$USE_PYTHON" = 1 ]; then
  wait_for_python_callback || { echo "OAuth callback listener failed" >&2; exit 1; }
else
  echo
  echo "Python 3 is not installed. After login, paste the full registered loopback callback URL."
  read -r -p '> ' CALLBACK_URL
fi

RETURNED_STATE="$(printf '%s' "$CALLBACK_URL" | sed -n 's/.*[?&]state=\([^&]*\).*/\1/p')"
CODE="$(printf '%s' "$CALLBACK_URL" | sed -n 's/.*[?&]code=\([^&]*\).*/\1/p')"
[ "$RETURNED_STATE" = "$STATE" ] || { echo "OAuth state mismatch" >&2; exit 1; }
[ -n "$CODE" ] || { echo "No authorization code received" >&2; exit 1; }

TOKEN_RESPONSE="$(curl -sS -X POST "$API_BASE_URL/api/v1/oauth/token" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode grant_type=authorization_code \
  --data-urlencode "code=$CODE" \
  --data-urlencode "client_id=$CLIENT_ID" \
  --data-urlencode "redirect_uri=$REDIRECT_URI" \
  --data-urlencode "code_verifier=$VERIFIER")"

ACCESS_TOKEN="$(printf '%s' "$TOKEN_RESPONSE" | sed -n 's/.*"access_token"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')"
[ -n "$ACCESS_TOKEN" ] || { echo "Token exchange failed: $TOKEN_RESPONSE" >&2; exit 1; }

APOLLO_PROVISION_CONFIG_DIR="$HOME/.config/apollo-provision"
mkdir -p "$APOLLO_PROVISION_CONFIG_DIR"
chmod 700 "$APOLLO_PROVISION_CONFIG_DIR"
printf '%s' "$TOKEN_RESPONSE" > "$APOLLO_PROVISION_CONFIG_DIR/credentials"
chmod 600 "$APOLLO_PROVISION_CONFIG_DIR/credentials"
echo "Credentials saved to $APOLLO_PROVISION_CONFIG_DIR/credentials"
