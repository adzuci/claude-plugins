#!/usr/bin/env bash
set -euo pipefail
#
# posthealth.sh — post-exec health check for LeadGenie Sidekiq pods. Run this
# automatically after any `kubectl exec` / `rails runner` one-shot against a
# real pod, to confirm nothing broke (OOMKilled, Evicted, replica shortfall).
#
# Usage: posthealth.sh <stage|prod> -n <namespace> --pod <pod> \
#          [--deploy <deploy>] [--since 3m] [--baseline-restarts N]
#
# READ-ONLY GUARANTEE: same as preflight.sh — this script only ever runs
# `kubectl get`/`describe`/`top` and local `kubectl config` reads. It NEVER
# execs, deletes, patches, applies, scales, or switches the operator's kube
# context.
#
# Exit codes:
#   0  HEALTHY — no problems found
#   1  problem detected (verdict DEGRADED or INCIDENT: OOMKilled, Evicted,
#      pod missing, replica shortfall, restart-count regression, ...)
#   2  usage / argument error
#   3  INCONCLUSIVE — e.g. the events retention window (~1h default) had
#      likely already expired for the requested --since; absence of events
#      cannot be trusted as "clean" in that case
#
# Env vars:
#   K8S_SAFE_EXEC_SKIP_CLUSTER=1
#     Testing/dev escape hatch, same contract as preflight.sh: performs ONLY
#     local arg validation, then exits 0 before context resolution/match or
#     any other kubectl call. WHEN SET, THIS DOES SKIP THE CONTEXT-MATCH
#     SAFETY GATE — it is not a gate that survives the flag. The safety
#     property is entirely "this is never set in a real run," full stop.
#     NEVER set this outside the test suite — a real run needs the live
#     pod/events/replica data to mean anything anyway.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib_context.sh
source "${SCRIPT_DIR}/lib_context.sh"

readonly DEFAULT_SINCE="5m"
readonly KUBECTL_REQUEST_TIMEOUT="10s"
# Kubernetes' events API retains ~1h of history by default. A --since at or
# beyond this floor means an empty events result may mean "expired", not
# "clean" — this is a floor for that warning, not an exact retention pin.
readonly EVENTS_RETENTION_MINUTES=55

print_usage() {
  cat <<'EOF'
Usage: posthealth.sh <stage|prod> -n <namespace> --pod <pod> [--deploy <deploy>] [--since 3m] [--baseline-restarts N]

  stage|prod             Target environment (required, case-sensitive, no default).
  -n <namespace>         Namespace the pod lives in (required).
  --pod <pod>            Pod name to check (required).
  --deploy <deploy>      Owning Deployment name (optional; derived from the
                         pod's ownerReferences chain if omitted).
  --since <duration>     Events lookback window, e.g. 3m, 10m (default: 5m).
  --baseline-restarts N  Restart count observed before the risky command ran,
                         to compute a delta (optional; absolute count is
                         reported if omitted).

Exit codes: 0 healthy, 1 problem detected, 2 usage error, 3 inconclusive.
EOF
}

# since_to_minutes <duration>
# Parses a duration like "5m", "1h", "300s", or a bare integer (minutes).
# Prints the equivalent whole minutes, or nothing if unparseable.
since_to_minutes() {
  local s="$1"
  if [[ "$s" =~ ^([0-9]+)h$ ]]; then
    echo $((${BASH_REMATCH[1]} * 60))
  elif [[ "$s" =~ ^([0-9]+)m$ ]]; then
    echo "${BASH_REMATCH[1]}"
  elif [[ "$s" =~ ^([0-9]+)s$ ]]; then
    echo $((${BASH_REMATCH[1]} / 60))
  elif [[ "$s" =~ ^[0-9]+$ ]]; then
    echo "$s"
  fi
}

# --- arg validation ------------------------------------------------------------

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

NAMESPACE=""
POD=""
DEPLOY=""
SINCE="$DEFAULT_SINCE"
BASELINE_RESTARTS=""

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
    --pod)
      shift
      POD="${1:-}"
      if [[ -z "$POD" ]]; then
        echo "ERROR: --pod requires a value." >&2
        print_usage >&2
        exit 2
      fi
      shift
      ;;
    --deploy)
      shift
      DEPLOY="${1:-}"
      if [[ -z "$DEPLOY" ]]; then
        echo "ERROR: --deploy requires a value." >&2
        print_usage >&2
        exit 2
      fi
      shift
      ;;
    --since)
      shift
      SINCE="${1:-}"
      if [[ -z "$SINCE" ]]; then
        echo "ERROR: --since requires a value." >&2
        print_usage >&2
        exit 2
      fi
      shift
      ;;
    --baseline-restarts)
      shift
      BASELINE_RESTARTS="${1:-}"
      if ! [[ "$BASELINE_RESTARTS" =~ ^[0-9]+$ ]]; then
        echo "ERROR: --baseline-restarts must be a non-negative integer, got '${BASELINE_RESTARTS}'." >&2
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

if [[ -z "$NAMESPACE" ]]; then
  echo "ERROR: -n <namespace> is required." >&2
  print_usage >&2
  exit 2
fi

if [[ -z "$POD" ]]; then
  echo "ERROR: --pod <pod> is required." >&2
  print_usage >&2
  exit 2
fi

echo "PASS: arguments valid (env=${ENV}, namespace=${NAMESPACE}, pod=${POD}${DEPLOY:+, deploy=${DEPLOY}}, since=${SINCE}${BASELINE_RESTARTS:+, baseline-restarts=${BASELINE_RESTARTS}})"

if [[ "${K8S_SAFE_EXEC_SKIP_CLUSTER:-0}" == "1" ]]; then
  echo "WARN: K8S_SAFE_EXEC_SKIP_CLUSTER=1 set — skipping all live-cluster checks (test/dev mode only; never set this for a real health check)." >&2
  echo
  echo "== Summary (local validation only) =="
  echo "  env:       ${ENV}"
  echo "  namespace: ${NAMESPACE}"
  echo "  pod:       ${POD}"
  echo "  verdict:   SKIPPED — no cluster checks performed"
  exit 0
fi

# --- context resolution & match (shared with preflight.sh) -------------------

echo
echo "== Context match =="
if ! RESOLVED_CONTEXT="$(resolve_context "$ENV")"; then
  echo "FAIL: could not resolve context for env '${ENV}'. See details above." >&2
  exit 1
fi

if ! CURRENT_CONTEXT="$(kubectl config current-context 2>&1)"; then
  echo "FAIL: could not read current kubectl context: ${CURRENT_CONTEXT}" >&2
  exit 1
fi

if [[ "$CURRENT_CONTEXT" != "$RESOLVED_CONTEXT" ]]; then
  echo "FAIL: context mismatch: current-context is \"${CURRENT_CONTEXT}\" but env \"${ENV}\" resolves to \"${RESOLVED_CONTEXT}\"." >&2
  echo "  Fix: kubectl config use-context ${RESOLVED_CONTEXT}" >&2
  exit 1
fi
echo "PASS: kubectl context matches expected (${CURRENT_CONTEXT})"

SEVERE=0
MILD=0
INCONCLUSIVE=0
FINDINGS=()
add_finding() { FINDINGS+=("$1"); }

# --- pod status ----------------------------------------------------------------

echo
echo "== Pod status: ${NAMESPACE}/${POD} =="

POD_EXISTS=1
if ! PHASE="$(kubectl --context "$RESOLVED_CONTEXT" -n "$NAMESPACE" get pod "$POD" \
  --request-timeout="$KUBECTL_REQUEST_TIMEOUT" -o jsonpath='{.status.phase}' 2>&1)"; then
  if printf '%s' "$PHASE" | grep -qi "not found"; then
    POD_EXISTS=0
    PHASE=""
    echo "FINDING: pod ${NAMESPACE}/${POD} was NOT FOUND."
    echo "  This is expected after an eviction, but must be reported loudly — not treated as a clean pass."
    add_finding "pod not found (possible eviction/deletion)"
    SEVERE=1
  else
    echo "FAIL: could not query pod ${NAMESPACE}/${POD}: ${PHASE}" >&2
    exit 1
  fi
fi

DEPLOY_NAME="$DEPLOY"

if [[ "$POD_EXISTS" -eq 1 ]]; then
  # First container only — a reasonable approximation for a single-container
  # Sidekiq pod; multi-container pods may need a manual look at the others.
  READY="$(kubectl --context "$RESOLVED_CONTEXT" -n "$NAMESPACE" get pod "$POD" \
    -o jsonpath='{.status.containerStatuses[0].ready}' 2>/dev/null || echo "")"
  RESTARTS="$(kubectl --context "$RESOLVED_CONTEXT" -n "$NAMESPACE" get pod "$POD" \
    -o jsonpath='{.status.containerStatuses[0].restartCount}' 2>/dev/null || echo "")"
  LAST_REASON="$(kubectl --context "$RESOLVED_CONTEXT" -n "$NAMESPACE" get pod "$POD" \
    -o jsonpath='{.status.containerStatuses[0].lastState.terminated.reason}' 2>/dev/null || echo "")"
  LAST_EXIT_CODE="$(kubectl --context "$RESOLVED_CONTEXT" -n "$NAMESPACE" get pod "$POD" \
    -o jsonpath='{.status.containerStatuses[0].lastState.terminated.exitCode}' 2>/dev/null || echo "")"

  echo "  phase=${PHASE:-unknown} ready=${READY:-unknown} restarts=${RESTARTS:-unknown} lastStateReason=${LAST_REASON:-none} lastExitCode=${LAST_EXIT_CODE:-n/a}"

  if [[ "$PHASE" != "Running" ]]; then
    echo "FINDING: pod phase is \"${PHASE:-unknown}\", not Running."
    add_finding "pod phase=${PHASE:-unknown}"
    MILD=1
  fi

  if [[ -n "$READY" && "$READY" != "true" ]]; then
    echo "FINDING: container ready=false."
    add_finding "container not ready"
    MILD=1
  fi

  if [[ "$LAST_REASON" == "OOMKilled" ]]; then
    echo "FINDING: container was OOMKilled (exit code ${LAST_EXIT_CODE:-unknown})."
    add_finding "OOMKilled (exit code ${LAST_EXIT_CODE:-unknown})"
    SEVERE=1
  fi

  if [[ -n "$BASELINE_RESTARTS" && "$RESTARTS" =~ ^[0-9]+$ ]]; then
    delta=$((RESTARTS - BASELINE_RESTARTS))
    if ((delta > 0)); then
      echo "FINDING: restart count increased by ${delta} (baseline ${BASELINE_RESTARTS} -> now ${RESTARTS})."
      add_finding "restart-count regression: +${delta} (baseline ${BASELINE_RESTARTS} -> ${RESTARTS})"
      MILD=1
    else
      echo "PASS: restart count unchanged since baseline (${RESTARTS})."
    fi
  elif [[ -n "$RESTARTS" ]]; then
    echo "  restart count (absolute, no --baseline-restarts given): ${RESTARTS}"
  fi

  # --- owning workload ---------------------------------------------------------

  if [[ -z "$DEPLOY_NAME" ]]; then
    RS_NAME="$(kubectl --context "$RESOLVED_CONTEXT" -n "$NAMESPACE" get pod "$POD" \
      -o jsonpath='{.metadata.ownerReferences[0].name}' 2>/dev/null || echo "")"
    if [[ -n "$RS_NAME" ]]; then
      DEPLOY_NAME="$(kubectl --context "$RESOLVED_CONTEXT" -n "$NAMESPACE" get replicaset "$RS_NAME" \
        -o jsonpath='{.metadata.ownerReferences[0].name}' 2>/dev/null || echo "")"
    fi
  fi

  echo
  if [[ -n "$DEPLOY_NAME" ]]; then
    echo "== Owning workload: Deployment/${DEPLOY_NAME} =="
    if ! DESIRED="$(kubectl --context "$RESOLVED_CONTEXT" -n "$NAMESPACE" get deployment "$DEPLOY_NAME" \
      --request-timeout="$KUBECTL_REQUEST_TIMEOUT" -o jsonpath='{.spec.replicas}' 2>&1)"; then
      echo "WARN: could not read Deployment/${DEPLOY_NAME}: ${DESIRED}"
    else
      READY_REPLICAS="$(kubectl --context "$RESOLVED_CONTEXT" -n "$NAMESPACE" get deployment "$DEPLOY_NAME" \
        -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "")"
      AVAILABLE_REPLICAS="$(kubectl --context "$RESOLVED_CONTEXT" -n "$NAMESPACE" get deployment "$DEPLOY_NAME" \
        -o jsonpath='{.status.availableReplicas}' 2>/dev/null || echo "")"
      UPDATED_REPLICAS="$(kubectl --context "$RESOLVED_CONTEXT" -n "$NAMESPACE" get deployment "$DEPLOY_NAME" \
        -o jsonpath='{.status.updatedReplicas}' 2>/dev/null || echo "")"
      READY_REPLICAS="${READY_REPLICAS:-0}"

      echo "  desired=${DESIRED} ready=${READY_REPLICAS} available=${AVAILABLE_REPLICAS:-0} updated=${UPDATED_REPLICAS:-0}"

      if [[ "$DESIRED" =~ ^[0-9]+$ && "$READY_REPLICAS" =~ ^[0-9]+$ ]] && ((READY_REPLICAS < DESIRED)); then
        echo "FINDING: ready replicas (${READY_REPLICAS}) < desired (${DESIRED})."
        add_finding "replica shortfall: ready ${READY_REPLICAS} < desired ${DESIRED}"
        MILD=1
      fi
    fi
  else
    echo "WARN: could not derive owning Deployment (no --deploy given and the pod -> ReplicaSet -> Deployment ownerReferences chain didn't resolve)."
  fi

  # --- resource usage (best-effort; metrics-server may be missing) -----------

  echo
  echo "== Resource usage (kubectl top) =="
  if TOP_OUT="$(kubectl --context "$RESOLVED_CONTEXT" -n "$NAMESPACE" top pod "$POD" \
    --request-timeout="$KUBECTL_REQUEST_TIMEOUT" 2>&1)"; then
    printf '%s\n' "$TOP_OUT"
  else
    echo "WARN: kubectl top unavailable or failed (metrics-server may not be installed): ${TOP_OUT}"
  fi
else
  echo "  Skipping owning-workload and resource-usage checks — pod does not exist."
fi

# --- events ----------------------------------------------------------------

echo
echo "== Events (--since ${SINCE}) =="

EVENTS_A=""
if ! EVENTS_A="$(kubectl --context "$RESOLVED_CONTEXT" -n "$NAMESPACE" get events \
  --field-selector "involvedObject.name=${POD}" --sort-by=.lastTimestamp \
  --request-timeout="$KUBECTL_REQUEST_TIMEOUT" 2>&1)"; then
  echo "WARN: pod-scoped events query failed: ${EVENTS_A}"
  EVENTS_A=""
fi

# --field-selector only matches events keyed directly to the Pod object;
# events keyed to the ReplicaSet or Node (common for Evicted/OOM events) are
# missed, so also do a namespace-wide pass and grep for the pod name.
EVENTS_B=""
if ! EVENTS_B="$(kubectl --context "$RESOLVED_CONTEXT" -n "$NAMESPACE" get events \
  --sort-by=.lastTimestamp --request-timeout="$KUBECTL_REQUEST_TIMEOUT" 2>&1)"; then
  echo "WARN: namespace-wide events query failed: ${EVENTS_B}"
  EVENTS_B=""
fi
EVENTS_B_FILTERED="$(printf '%s\n' "$EVENTS_B" | grep -F "$POD" || true)"

ALL_EVENTS="$(printf '%s\n%s\n' "$EVENTS_A" "$EVENTS_B_FILTERED")"
MATCHED_EVENTS="$(printf '%s\n' "$ALL_EVENTS" | grep -E 'Evicted|OOMKilled|Killing|FailedScheduling|BackOff|Preempt' || true)"

if [[ -n "$MATCHED_EVENTS" ]]; then
  echo "FINDING: concerning events found:"
  printf '%s\n' "$MATCHED_EVENTS" | sed 's/^/    /'
  add_finding "concerning events matched (see above)"
  if printf '%s\n' "$MATCHED_EVENTS" | grep -qE 'Evicted|OOMKilled'; then
    SEVERE=1
  else
    MILD=1
  fi
else
  BOTH_EMPTY="$(printf '%s%s' "$EVENTS_A" "$EVENTS_B" | tr -d '[:space:]')"
  if [[ -z "$BOTH_EMPTY" ]]; then
    # Both queries came back empty. The events API only retains ~1h by
    # default, so an empty result on a late/long-window check can mean
    # "expired", not "clean" — do not report this as a clean pass.
    SINCE_MINUTES="$(since_to_minutes "$SINCE")"
    if [[ -n "$SINCE_MINUTES" ]] && ((SINCE_MINUTES >= EVENTS_RETENTION_MINUTES)); then
      echo "INCONCLUSIVE: no events found, but --since ${SINCE} (~${SINCE_MINUTES}m) is at/beyond the ~1h default events retention window. Cannot confirm clean vs. expired."
      INCONCLUSIVE=1
    else
      echo "PASS: no concerning events found for ${NAMESPACE}/${POD} (within retention window)."
    fi
  else
    echo "PASS: no concerning events found for ${NAMESPACE}/${POD}."
  fi
fi

# --- verdict -----------------------------------------------------------------

echo
echo "== Verdict =="

if [[ "$SEVERE" -eq 1 ]]; then
  VERDICT="INCIDENT"
elif [[ "$MILD" -eq 1 ]]; then
  VERDICT="DEGRADED"
elif [[ "$INCONCLUSIVE" -eq 1 ]]; then
  VERDICT="INCONCLUSIVE"
else
  VERDICT="HEALTHY"
fi

case "$VERDICT" in
  INCIDENT)
    echo "INCIDENT: problem(s) detected for ${NAMESPACE}/${POD}:"
    for f in "${FINDINGS[@]}"; do
      echo "  - $f"
    done
    echo "Next step: /apollo-eng-devops:kubernetes-specialist for triage."
    exit 1
    ;;
  DEGRADED)
    echo "DEGRADED: possible problem(s) detected for ${NAMESPACE}/${POD} (not a confirmed severe incident):"
    for f in "${FINDINGS[@]}"; do
      echo "  - $f"
    done
    echo "Next step: review the findings above; consider /apollo-eng-devops:kubernetes-specialist if unsure."
    exit 1
    ;;
  INCONCLUSIVE)
    echo "INCONCLUSIVE: no confirmed problems from pod/replica checks, but the events check could not be trusted (see above)."
    exit 3
    ;;
  HEALTHY)
    echo "HEALTHY: ${NAMESPACE}/${POD} looks fine — pod phase nominal, ready, no restart-count regression, replicas at desired count (where derivable), and no concerning events in the retention window."
    exit 0
    ;;
esac
