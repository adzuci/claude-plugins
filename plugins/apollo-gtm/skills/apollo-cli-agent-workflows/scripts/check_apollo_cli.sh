#!/usr/bin/env bash
set -euo pipefail

echo "== Apollo CLI smoke check =="

if ! command -v apollo >/dev/null 2>&1; then
  echo "STATUS: MISSING"
  echo "apollo command not found. Install the native Apollo CLI from the official Apollo-provided source before continuing."
  exit 1
fi

echo "STATUS: FOUND"
echo "VERSION: $(apollo --version 2>/dev/null || echo UNKNOWN)"

echo
echo "== Root help =="
apollo --help >/dev/null
echo "PASS: apollo --help"

echo
echo "== Auth =="
whoami_output="$(mktemp)"
trap 'rm -f "$whoami_output"' EXIT
if apollo auth whoami >"$whoami_output" 2>&1; then
  echo "PASS: auth whoami"
else
  cat "$whoami_output" || true
  echo "STATUS: AUTH_REQUIRED"
  echo "Run apollo auth login in the approved assistant environment."
  exit 2
fi

echo
echo "== Safe command help checks =="
commands=(
  "users profile"
  "usage credits"
  "email-accounts list"
  "people search"
  "companies search"
  "contacts search"
  "sequences search"
  "tasks search"
  "analytics report"
)

for cmd in "${commands[@]}"; do
  read -r -a cmd_parts <<<"$cmd"
  apollo "${cmd_parts[@]}" --help >/dev/null
  echo "PASS: apollo ${cmd} --help"
done

echo
echo "RESULT: READY_FOR_READ_ONLY_TEST"
