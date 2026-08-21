#!/usr/bin/env bash
set -euo pipefail
#
# preflight.sh — safety gate for ad hoc `kubectl exec` / `rails runner`
# one-shots against LeadGenie Sidekiq pods. Run this BEFORE any risky
# one-shot command against a real pod.
#
# Usage: preflight.sh <stage|prod> [-n <namespace>]
#
# READ-ONLY GUARANTEE: this script only ever runs `gcloud version`,
# `kubectl version --client`, `kubectl config ...` (local kubeconfig reads),
# and `kubectl get ns` (a cheap read with an explicit timeout). It NEVER
# execs, deletes, patches, applies, scales, or switches the operator's kube
# context. On a context mismatch it prints the exact `kubectl config
# use-context <name>` command and stops — the operator runs that themselves.
#
# Exit codes:
#   0  all clear
#   1  hard stop — do not proceed (context mismatch, connectivity failure,
#      missing required tooling, unrecognized/invalid namespace)
#   2  usage / argument error
#   3  warnings only — operator should acknowledge before proceeding
#
# Env vars:
#   K8S_SAFE_EXEC_SKIP_CLUSTER=1
#     Testing/dev escape hatch. Skips every check that talks to a live
#     cluster (tool-version checks, context resolution, context-match,
#     connectivity, live namespace existence). Performs ONLY local, pure
#     validation: env-arg validation and namespace *pattern* validation.
#     This exists so the test suite can exercise validation logic
#     hermetically, without a real kubeconfig or network.
#     WHEN SET, THIS DOES SKIP THE CONTEXT-MATCH SAFETY GATE — it is not a
#     gate that survives the flag. The safety property is entirely "this is
#     never set in a real run," full stop. NEVER set this outside the test
#     suite.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib_context.sh
source "${SCRIPT_DIR}/lib_context.sh"

# --- named constants -------------------------------------------------------

# Floor, not a pin: kubectl supports N-2 skew vs. the server by policy.
# Anything older than 1.<MIN_KUBECTL_MINOR> is stale enough to nudge on.
readonly MIN_KUBECTL_MINOR=24
# Floor for the gcloud SDK's major version number (bump occasionally; this is
# a staleness floor, not an exact pin).
readonly MIN_GCLOUD_SDK_MAJOR=400
# Fail fast instead of hanging when VPN is down.
readonly KUBECTL_REQUEST_TIMEOUT="5s"

readonly PROD_FIXED_NAMESPACES="airbyte api-dev-portal arc-runners-test cdp-ingest cert-manager cloudflare custom-metrics default discovery gmp-public gmp-system keda kodem kube-node-lease kube-public kube-services kube-system kyverno leadgenie leadgenie-beta marketing mint-security monitoring nl-search observability opencost orcasecurity pricus qpoint resolve security tracking-tls vendor-egress web-scraper"
readonly STAGE_FIXED_NAMESPACES="airbyte cdp-ingest cerebro cert-manager cloudflare db-migration default fabric-core-docs gcs-proxy gpu-operator helios-stage infini keda kube-node-lease kube-public kube-services kube-system kyverno leadgenie monitoring nginx-gateway nl-search observability opencost orcasecurity pulse qpoint rajesh-test staging test-node-pool tracking-tls transcend vendor-egress web-scraper"

WARNED=0
RESOLVED_CONTEXT=""
NAMESPACE=""

# --- output helpers ----------------------------------------------------------

print_usage() {
  cat <<'EOF'
Usage: preflight.sh <stage|prod> [-n <namespace>]

  stage|prod   Target environment (required, case-sensitive, no default).
  -n <ns>      Optional namespace to validate against the env's fixed set
               and stage-only dynamic patterns (preview-*, fabric-studio-*).

Exit codes: 0 all clear, 1 hard stop, 2 usage error, 3 warnings only.
EOF
}

pass() { printf 'PASS: %s\n' "$1"; }
warn() {
  printf 'WARN: %s\n' "$1" >&2
  WARNED=1
}
print_summary() {
  local verdict="$1"
  echo
  echo "== Summary =="
  echo "  env:       ${ENV:-<unset>}"
  echo "  context:   ${RESOLVED_CONTEXT:-<not resolved>}"
  echo "  namespace: ${NAMESPACE:-<none>}"
  echo "  verdict:   ${verdict}"
}
hardfail() {
  printf 'FAIL: %s\n' "$1" >&2
  print_summary "FAIL — do not proceed"
  exit 1
}

# --- pure namespace classification (no kubectl calls) -----------------------

# classify_namespace <namespace> <env>
# Echoes one of: fixed | gke-managed | pattern-ok | pattern-wrong-env | unknown
classify_namespace() {
  local ns="$1" env="$2"
  local fixed_set=""
  case "$env" in
    prod) fixed_set="$PROD_FIXED_NAMESPACES" ;;
    stage) fixed_set="$STAGE_FIXED_NAMESPACES" ;;
  esac

  local n
  for n in $fixed_set; do
    if [[ "$ns" == "$n" ]]; then
      echo "fixed"
      return 0
    fi
  done

  case "$ns" in
    gke-managed-*)
      echo "gke-managed"
      ;;
    preview-* | fabric-studio-*)
      if [[ "$env" == "stage" ]]; then
        echo "pattern-ok"
      else
        echo "pattern-wrong-env"
      fi
      ;;
    *)
      echo "unknown"
      ;;
  esac
}

# closest_namespace_matches <namespace> <env>
# Best-effort suggestions for an unknown namespace: fixed-set entries that
# share a substring with what was typed.
closest_namespace_matches() {
  local ns="$1" env="$2"
  local fixed_set=""
  case "$env" in
    prod) fixed_set="$PROD_FIXED_NAMESPACES" ;;
    stage) fixed_set="$STAGE_FIXED_NAMESPACES" ;;
  esac

  local n out=""
  for n in $fixed_set; do
    case "$n" in
      *"$ns"* | "$ns"*)
        out="${out}${n} "
        ;;
    esac
  done
  if [[ -z "$out" ]]; then
    for n in $fixed_set; do
      case "$ns" in
        *"$n"*)
          out="${out}${n} "
          ;;
      esac
    done
  fi
  printf '%s' "${out% }"
}

# --- step 1: arg validation ---------------------------------------------------

if [[ $# -eq 0 ]]; then
  echo "ERROR: missing required <stage|prod> argument." >&2
  print_usage >&2
  exit 2
fi

case "$1" in
  -h | --help)
    print_usage
    exit 0
    ;;
esac

ENV_ARG="$1"
shift

if ! ENV="$(validate_env "$ENV_ARG")"; then
  echo "ERROR: invalid environment '${ENV_ARG}'. $(usage_env_line)" >&2
  print_usage >&2
  exit 2
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    -n)
      shift
      NAMESPACE="${1:-}"
      if [[ -z "$NAMESPACE" ]]; then
        echo "ERROR: -n requires a namespace argument." >&2
        print_usage >&2
        exit 2
      fi
      shift
      ;;
    *)
      echo "ERROR: unrecognized argument '$1'." >&2
      print_usage >&2
      exit 2
      ;;
  esac
done

pass "Arguments valid (env=${ENV}${NAMESPACE:+, namespace=${NAMESPACE}})"

SKIP_CLUSTER=0
if [[ "${K8S_SAFE_EXEC_SKIP_CLUSTER:-0}" == "1" ]]; then
  SKIP_CLUSTER=1
  warn "K8S_SAFE_EXEC_SKIP_CLUSTER=1 set — skipping tool-version checks, context resolution/match, connectivity, and live namespace existence (test/dev mode only; never set this for a real run)."
fi

# --- step 2: tool versions ----------------------------------------------------

if [[ "$SKIP_CLUSTER" -eq 0 ]]; then
  echo
  echo "== Step: tool versions =="

  if ! command -v kubectl >/dev/null 2>&1; then
    hardfail "kubectl is not installed. Install: https://kubernetes.io/docs/tasks/tools/ (macOS: brew install kubectl, or: gcloud components install kubectl)"
  fi

  kubectl_ver=""
  if kubectl_json="$(kubectl version --client -o json 2>/dev/null)"; then
    kubectl_ver="$(printf '%s' "$kubectl_json" \
      | grep -oE '"gitVersion"[[:space:]]*:[[:space:]]*"[^"]*"' \
      | head -1 \
      | sed -E 's/.*"gitVersion"[[:space:]]*:[[:space:]]*"([^"]*)".*/\1/' || true)"
  fi
  if [[ -z "$kubectl_ver" ]]; then
    kubectl_text="$(kubectl version --client 2>/dev/null || true)"
    kubectl_ver="$(printf '%s\n' "$kubectl_text" | grep -oE 'v[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)"
  fi

  if [[ -z "$kubectl_ver" ]]; then
    warn "Could not determine kubectl client version (unexpected output format); skipping staleness check."
  else
    kubectl_minor="$(printf '%s' "$kubectl_ver" | sed -E 's/^v[0-9]+\.([0-9]+)\..*/\1/')"
    if ! [[ "$kubectl_minor" =~ ^[0-9]+$ ]]; then
      warn "Could not parse kubectl minor version from '${kubectl_ver}'; skipping staleness check."
    elif ((kubectl_minor < MIN_KUBECTL_MINOR)); then
      warn "kubectl client ${kubectl_ver} is older than the recommended floor (1.${MIN_KUBECTL_MINOR}.x). Update: gcloud components update && gcloud components install kubectl (or: brew upgrade kubectl)."
    else
      pass "kubectl client ${kubectl_ver} (>= 1.${MIN_KUBECTL_MINOR} floor)"
    fi
  fi

  if ! command -v gcloud >/dev/null 2>&1; then
    hardfail "gcloud is not installed. Install: https://cloud.google.com/sdk/docs/install"
  fi

  if ! gcloud_text="$(gcloud version 2>&1)"; then
    warn "Could not run 'gcloud version' cleanly; skipping staleness check. Output: ${gcloud_text}"
  else
    gcloud_ver="$(printf '%s\n' "$gcloud_text" | grep -oE 'Google Cloud SDK [0-9]+\.[0-9]+\.[0-9]+' | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)"
    if [[ -z "$gcloud_ver" ]]; then
      warn "Could not parse gcloud SDK version from output; skipping staleness check."
    else
      gcloud_major="${gcloud_ver%%.*}"
      if ! [[ "$gcloud_major" =~ ^[0-9]+$ ]]; then
        warn "Could not parse gcloud major version from '${gcloud_ver}'; skipping staleness check."
      elif ((gcloud_major < MIN_GCLOUD_SDK_MAJOR)); then
        warn "gcloud SDK ${gcloud_ver} is older than the recommended floor (${MIN_GCLOUD_SDK_MAJOR}.x). Update: gcloud components update."
      else
        pass "gcloud SDK ${gcloud_ver} (>= ${MIN_GCLOUD_SDK_MAJOR} floor)"
      fi
    fi
  fi
fi

# --- step 3: context match ----------------------------------------------------

NS_LIST=""
if [[ "$SKIP_CLUSTER" -eq 0 ]]; then
  echo
  echo "== Step: context match =="

  if ! RESOLVED_CONTEXT="$(resolve_context "$ENV")"; then
    hardfail "Could not resolve a unique kubectl context for env '${ENV}'. See details above."
  fi
  pass "Resolved context for env '${ENV}': ${RESOLVED_CONTEXT}"

  if ! CURRENT_CONTEXT="$(kubectl config current-context 2>&1)"; then
    hardfail "Could not read current kubectl context: ${CURRENT_CONTEXT}"
  fi

  if [[ "$CURRENT_CONTEXT" != "$RESOLVED_CONTEXT" ]]; then
    hardfail "Context mismatch: current-context is \"${CURRENT_CONTEXT}\" but env \"${ENV}\" resolves to \"${RESOLVED_CONTEXT}\". Fix: kubectl config use-context ${RESOLVED_CONTEXT}"
  fi
  pass "Current kubectl context matches expected: ${CURRENT_CONTEXT}"

  # --- step 4: connectivity ---------------------------------------------------

  echo
  echo "== Step: connectivity =="
  if ! NS_LIST="$(kubectl --context "$RESOLVED_CONTEXT" get ns --request-timeout="$KUBECTL_REQUEST_TIMEOUT" -o name 2>&1)"; then
    hardfail "Could not reach cluster (kubectl get ns failed): ${NS_LIST}. Check VPN — stage and prod VPNs are SEPARATE; prod access is restricted to infra plus some senior engineers."
  fi
  pass "Connectivity OK (kubectl get ns succeeded against ${RESOLVED_CONTEXT})"
fi

# --- step 5: namespace validation ---------------------------------------------

if [[ -n "$NAMESPACE" ]]; then
  echo
  echo "== Step: namespace validation (namespace=${NAMESPACE}) =="
  CLASS="$(classify_namespace "$NAMESPACE" "$ENV")"
  case "$CLASS" in
    unknown)
      close="$(closest_namespace_matches "$NAMESPACE" "$ENV")"
      hardfail "Namespace \"${NAMESPACE}\" is not a recognized ${ENV} namespace and matches no allowed pattern. Closest known matches: ${close:-none found}"
      ;;
    pattern-wrong-env)
      hardfail "Namespace \"${NAMESPACE}\" matches the preview-*/fabric-studio-* pattern, which is stage-ONLY. You passed env=\"${ENV}\" — this looks like a confused environment. Rerun with env=stage, or pick a real ${ENV} namespace."
      ;;
    fixed | gke-managed | pattern-ok)
      pass "Namespace \"${NAMESPACE}\" is a recognized ${ENV} namespace (${CLASS})."
      if [[ "$SKIP_CLUSTER" -eq 1 ]]; then
        warn "Live existence not confirmed (K8S_SAFE_EXEC_SKIP_CLUSTER=1); pattern check only."
      else
        if printf '%s\n' "$NS_LIST" | grep -qx "namespace/${NAMESPACE}"; then
          pass "Namespace \"${NAMESPACE}\" confirmed to exist live in ${RESOLVED_CONTEXT}."
        elif [[ "$CLASS" == "pattern-ok" ]]; then
          warn "Namespace \"${NAMESPACE}\" matches the stage preview/fabric-studio pattern but does not currently exist live. Preview/prototype envs are ephemeral and get reaped — this may be expected."
        else
          hardfail "Namespace \"${NAMESPACE}\" is expected to exist (${CLASS}) but was not found live in ${RESOLVED_CONTEXT}. Double check the name."
        fi
      fi
      ;;
  esac
else
  echo
  echo "== Step: namespace validation =="
  pass "No -n namespace given; skipping namespace-scoped validation."
fi

# --- step 6: summary -----------------------------------------------------------

if [[ "$WARNED" -eq 1 ]]; then
  print_summary "WARN — review warnings above before proceeding"
  exit 3
fi

print_summary "PASS — clear to proceed"
exit 0
