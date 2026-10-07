#!/usr/bin/env bash
set -euo pipefail
#
# bq_preflight.sh — precondition gate for gcp-cost-optimization-review.
#
# Usage:
#   bq_preflight.sh --check     (default) verify gcloud, bq, jq are installed,
#                                an @apollo.io account is active, and a SELECT 1
#                                smoke query against the billing export succeeds.
#                                Read-only. Exits non-zero on any hard failure.
#   bq_preflight.sh --install   Also offer to install the Google Cloud SDK via
#                                Homebrew, after an explicit y/N prompt. Never
#                                runs brew without that prompt returning "y".
#                                Offered both when every check passes (upgrade)
#                                and when a check failed because gcloud or bq is
#                                missing — the case installing actually fixes.
#                                An auth or smoke-query failure still exits 1
#                                without prompting: brew cannot fix those.
#                                This is the ONLY write this script (or this
#                                skill) can perform, and only on explicit
#                                request — never as part of --check.
#
# Exit codes:
#   0  all clear
#   1  hard failure — do not proceed (missing tool, no active account, or the
#      smoke query failed)
#   2  usage error (unrecognized argument)
#
# Env vars:
#   BQ_PREFLIGHT_PROJECT   Override the job project used for the smoke query
#                          (default: indigo-lotus-415, the same job project
#                          every real query in SKILL.md uses; the billing
#                          export table itself is fully qualified).
#   BQ_PREFLIGHT_YES=1     Testing/non-interactive escape hatch for --install:
#                          treat the y/N prompt as answered "y" without
#                          reading stdin. NEVER set this for a real run —
#                          it exists so the test suite can exercise the
#                          "confirmed" branch hermetically with a stub brew.
#                          It does not skip the prompt for --check (--check
#                          never prompts at all).

PROJECT="${BQ_PREFLIGHT_PROJECT:-indigo-lotus-415}"   # job project, same as every real query in SKILL.md; the table is fully qualified
MODE="check"

print_usage() {
  cat <<'EOF'
Usage: bq_preflight.sh [--check|--install]

  --check    (default) Read-only: verify gcloud, bq, jq, active auth, and a
             SELECT 1 smoke query against the billing export.
  --install  Also offer (y/N prompt) to install the Google Cloud SDK via
             Homebrew, including when gcloud/bq are missing. This is the only
             write this script can perform, and only after the prompt is
             explicitly confirmed. Auth/smoke-query failures never prompt.

Exit codes: 0 all clear, 1 hard failure, 2 usage error.
EOF
}

case "${1:-}" in
  "" | --check)
    MODE="check"
    ;;
  --install)
    MODE="install"
    ;;
  -h | --help)
    print_usage
    exit 0
    ;;
  *)
    echo "ERROR: unrecognized argument '${1}'." >&2
    print_usage >&2
    exit 2
    ;;
esac

if [[ $# -gt 1 ]]; then
  echo "ERROR: unexpected extra arguments: ${*:2}" >&2
  print_usage >&2
  exit 2
fi

HARD_FAIL=0
MISSING_TOOL=0

pass() { printf 'PASS: %s\n' "$1"; }
fail() {
  printf 'FAIL: %s\n' "$1" >&2
  HARD_FAIL=1
}

remediate_gcloud() {
  cat >&2 <<'EOF'
  Remediation:
    brew install --cask gcloud-cli
    gcloud auth login
    gcloud auth application-default login
EOF
}

# --- optional: --install ------------------------------------------------------
#
# Reachable in two situations, both requiring --install:
#   * every check passed (upgrade path), and
#   * a check failed *because a tool is missing* — the one case installing
#     actually fixes. An auth or smoke-query failure is never a reason to run
#     brew, so those still exit 1 without prompting.

run_install_prompt() {
  echo
  echo "== Step: install (explicit request only) =="

  CONFIRM="n"
  if [[ "${BQ_PREFLIGHT_YES:-0}" == "1" ]]; then
    # Test-only escape hatch — never set in a real run. See header comment.
    CONFIRM="y"
    echo "BQ_PREFLIGHT_YES=1 set — treating install prompt as confirmed (test mode only)."
  elif ! read -r -p "Install/upgrade the Google Cloud SDK via Homebrew now? [y/N] " CONFIRM; then
    # No input available (closed/empty stdin, no TTY) — refuse rather than
    # assume consent. This is the safety property: silence means "no".
    echo
    echo "No confirmation received — refusing to install non-interactively."
    CONFIRM="n"
  fi

  case "$CONFIRM" in
    y | Y | yes | YES)
      if ! command -v brew >/dev/null 2>&1; then
        printf 'FAIL: %s\n' "Homebrew is not installed; cannot run 'brew install --cask gcloud-cli'. Install Homebrew first: https://brew.sh" >&2
        return 1
      fi
      echo "Running: brew install --cask gcloud-cli"
      if ! brew install --cask gcloud-cli; then
        printf 'FAIL: %s\n' "brew install --cask gcloud-cli failed." >&2
        return 1
      fi
      echo "Installed. Next: gcloud auth login && gcloud auth application-default login"
      ;;
    *)
      echo "Install declined — no changes made."
      ;;
  esac
  return 0
}

# --- step 1: required tools -------------------------------------------------

echo "== Step: required tools =="

if command -v gcloud >/dev/null 2>&1; then
  pass "gcloud is installed ($(command -v gcloud))"
else
  fail "gcloud is not installed."
  MISSING_TOOL=1
  remediate_gcloud
fi

if command -v bq >/dev/null 2>&1; then
  pass "bq is installed ($(command -v bq))"
else
  fail "bq is not installed (it ships with the Google Cloud SDK)."
  MISSING_TOOL=1
  remediate_gcloud
fi

if command -v jq >/dev/null 2>&1; then
  pass "jq is installed ($(command -v jq))"
else
  fail "jq is not installed."
  echo "  Remediation: brew install jq" >&2
fi

# If gcloud itself is missing, auth/smoke-query checks cannot run meaningfully.
if ! command -v gcloud >/dev/null 2>&1; then
  echo
  echo "== Summary =="
  echo "  verdict: FAIL — install missing tools above, then re-run --check"
  if [[ "$MODE" == "install" ]]; then
    run_install_prompt || true
    echo "Re-run 'bq_preflight.sh --check' once the SDK is on PATH."
  fi
  exit 1
fi

# --- step 2: active account -------------------------------------------------

echo
echo "== Step: active gcloud account =="

ACTIVE_ACCOUNT=""
if ACCOUNT_LIST="$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>&1)"; then
  ACTIVE_ACCOUNT="$(printf '%s\n' "$ACCOUNT_LIST" | head -1 | tr -d '[:space:]')"
else
  ACCOUNT_LIST=""
fi

if [[ -z "$ACTIVE_ACCOUNT" ]]; then
  fail "No active gcloud account. Run: gcloud auth login"
elif [[ "$ACTIVE_ACCOUNT" != *"@apollo.io" ]]; then
  fail "Active gcloud account '${ACTIVE_ACCOUNT}' is not an @apollo.io account. Run: gcloud auth login"
else
  pass "Active account: ${ACTIVE_ACCOUNT}"
fi

# --- step 3: BigQuery smoke query -------------------------------------------

echo
echo "== Step: BigQuery smoke query =="

SMOKE_SQL='SELECT 1 FROM `databricks-apolloio.billing_export.gcp_billing_export_v1_0174D0_6590F0_824CC0` LIMIT 1'

if ! command -v bq >/dev/null 2>&1; then
  fail "Skipping smoke query — bq is not installed."
elif SMOKE_OUT="$(bq query --use_legacy_sql=false --project_id="${PROJECT}" --format=csv --dry_run "${SMOKE_SQL}" 2>&1)"; then
  pass "bq query smoke test succeeded against project ${PROJECT} (dry run against the billing export table)."
else
  fail "bq query smoke test failed against project ${PROJECT}: ${SMOKE_OUT}"
  echo "  Remediation: gcloud auth application-default login" >&2
fi

# --- summary -----------------------------------------------------------------

echo
echo "== Summary =="
if [[ "$HARD_FAIL" -eq 1 ]]; then
  echo "  verdict: FAIL — do not proceed. Fix the FAIL lines above and re-run --check."
  if [[ "$MODE" == "install" && "$MISSING_TOOL" -eq 1 ]]; then
    run_install_prompt || true
    echo "Re-run 'bq_preflight.sh --check' once the SDK is on PATH."
  fi
  exit 1
fi
echo "  verdict: PASS — clear to proceed."

if [[ "$MODE" != "install" ]]; then
  exit 0
fi

if [[ "$MISSING_TOOL" -ne 1 ]]; then
  echo "nothing to install — gcloud and bq are already present."
  exit 0
fi

run_install_prompt || exit 1

exit 0
