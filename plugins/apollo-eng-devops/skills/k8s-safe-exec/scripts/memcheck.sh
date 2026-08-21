#!/usr/bin/env bash
set -euo pipefail
#
# memcheck.sh — pre-exec memory-headroom check for the k8s-safe-exec skill.
#
# Before an ad hoc `kubectl exec` / `rails runner` one-shot runs inside a live
# Sidekiq pod, this estimates how much memory the intended command will need,
# reports what memory is actually available across the candidate pods for a
# Deployment/pod/label-selector, and RECOMMENDS THE ROOMIEST POD — instead of
# whichever one an operator happened to pick.
#
# Why this exists: a one-shot `rails runner` inside a live prod Sidekiq pod
# OOM-killed the container; the retry pushed the node over its memory
# threshold and the pod came back node-level `Evicted`. Replicas of the same
# Deployment were observed to differ by ~283Mi of headroom in prod
# (leadgenie's sidekiq-account-domain-fetcher), which is exactly why picking
# the roomiest replica — not an arbitrary one — matters.
#
# Usage:
#   memcheck.sh <stage|prod> -n <namespace> \
#     [--deploy <deploy> | --pod <pod> | --selector <k=v>] \
#     [--estimate <class|size>] [--safety-factor <float>] [--top N] [--json]
#
# Exactly one of --deploy / --pod / --selector is required.
#
# --estimate accepts either a named class or an explicit size (e.g. 900Mi,
# 1.5Gi). The named classes below are HEURISTICS calibrated against memory
# actually observed on leadgenie Sidekiq pods in prod (steady-state usage
# ~2.0-2.4Gi against 4Gi limits) — they are NOT a measurement of whatever
# snippet the operator is about to run. Never present an --estimate as a
# measurement; it is a starting guess the operator should sanity-check
# against what their command actually does.
#
#   Class         Default   Meaning
#   trivial        32Mi     shell builtins, cat, env, ls, ps
#   light         128Mi     small script, jq/awk on small input, redis-cli ping
#   rails-boot    768Mi     rails runner/console — full app boot, gems, AR schema cache
#   rails-query  1536Mi     rails runner doing DB queries/many rows, external API calls, JSON parsing
#   heavy        3072Mi     bulk backfill, large payload parsing, mass AR instantiation
#
# A candidate pod is viable only when its effective headroom (see below) is
# at least --estimate * --safety-factor (default 1.5). Effective headroom is
# min(pod_headroom, node_headroom) — a pod with plenty of its own headroom on
# a node that is itself nearly full is NOT a good candidate, and this is the
# exact node-pressure axis that caused the original eviction.
#
# READ-ONLY GUARANTEE: this script only ever runs `kubectl get`/`top`/
# `describe` and local `kubectl config` reads (via lib_context.sh). It NEVER
# execs, deletes, patches, applies, scales, or switches the operator's kube
# context. Every live kubectl call passes --context explicitly (never relies
# on ambient current-context) and an explicit --request-timeout so a VPN-down
# case fails fast rather than hanging.
#
# Exit codes:
#   0  at least one viable candidate (verdict OK or TIGHT) found; recommendation printed
#   1  no viable candidate (all NO), OR a hard failure — namespace/Deployment/pod not found
#   2  usage / argument error
#   3  inconclusive — kubectl top (metrics-server) unavailable; limits/requests
#      printed, but headroom could not be computed, so no recommendation is made
#
# Env vars:
#   K8S_SAFE_EXEC_SKIP_CLUSTER=1
#     Testing/dev escape hatch, same contract as preflight.sh/posthealth.sh:
#     performs ONLY local arg/size/estimate validation, then exits 0 before
#     any kubectl call. NEVER set this outside the test suite.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib_context.sh
source "${SCRIPT_DIR}/lib_context.sh"

readonly KUBECTL_REQUEST_TIMEOUT="10s"
readonly DEFAULT_SAFETY_FACTOR="1.5"
readonly DEFAULT_TOP=5
readonly DEFAULT_ESTIMATE_CLASS="rails-boot"

# --- output helpers ------------------------------------------------------------

print_usage() {
  cat <<'EOF'
Usage: memcheck.sh <stage|prod> -n <namespace>
                    [--deploy <deploy> | --pod <pod> | --selector <k=v>]
                    [--estimate <class|size>] [--safety-factor <float>]
                    [--top N] [--json]

  stage|prod            Target environment (required, case-sensitive, no default).
  -n <namespace>        Namespace to search (required).
  --deploy <deploy>     Candidate pods = live Running pods of this Deployment.
  --pod <pod>           Candidate = this single pod.
  --selector <k=v>      Candidate pods = live Running pods matching this label selector.
                        Exactly one of --deploy / --pod / --selector is required.
  --estimate <val>      Named class (trivial, light, rails-boot, rails-query, heavy)
                        or an explicit size (e.g. 900Mi, 1.5Gi). Default: rails-boot (768Mi).
  --safety-factor <f>   Viable only when headroom >= estimate * f. Default: 1.5.
  --top N               Max candidate rows to print. Default: 5.
  --json                Emit machine-readable JSON instead of the human table.

Exit codes: 0 viable candidate found, 1 no viable candidate / not found,
            2 usage error, 3 inconclusive (metrics unavailable).
EOF
}

pass() {
  # In --json mode stdout must stay pure JSON, so progress goes to stderr.
  if [[ "${JSON_MODE:-0}" -eq 1 ]]; then printf 'PASS: %s\n' "$1" >&2; else printf 'PASS: %s\n' "$1"; fi
}
section() {
  if [[ "${JSON_MODE:-0}" -eq 1 ]]; then printf '\n== %s ==\n' "$1" >&2; else printf '\n== %s ==\n' "$1"; fi
}
warn() { printf 'WARN: %s\n' "$1" >&2; }
fail() {
  printf 'FAIL: %s\n' "$1" >&2
}

# --- size / number parsing (bash 3.2: integers only, no bc, no floats) --------

# _split_decimal <str>
# On success (str is [0-9]+(\.[0-9]+)?), sets globals DEC_INT, DEC_FRAC,
# DEC_LEN ("" frac -> DEC_FRAC=0, DEC_LEN=0). Returns 1 on non-decimal input.
_split_decimal() {
  local s="$1"
  if [[ "$s" =~ ^([0-9]+)(\.([0-9]+))?$ ]]; then
    DEC_INT="${BASH_REMATCH[1]}"
    DEC_FRAC="${BASH_REMATCH[3]}"
    if [[ -z "$DEC_FRAC" ]]; then
      DEC_FRAC="0"
      DEC_LEN=0
    else
      DEC_LEN=${#DEC_FRAC}
    fi
    return 0
  fi
  return 1
}

# parse_size_mib <size>
# Accepts Ki/Mi/Gi (binary), K/M/G (decimal), or bare bytes; decimals allowed
# (e.g. "1.5Gi"). Prints the size rounded to the nearest whole MiB. Returns 1
# on unparseable input.
parse_size_mib() {
  local s="$1"
  local int_part frac_part unit
  if [[ "$s" =~ ^([0-9]+)(\.([0-9]+))?(Ki|Mi|Gi|K|M|G)?$ ]]; then
    int_part="${BASH_REMATCH[1]}"
    frac_part="${BASH_REMATCH[3]}"
    unit="${BASH_REMATCH[4]}"
  else
    return 1
  fi

  local frac_len=0 pow=1 frac_digits=0
  if [[ -n "$frac_part" ]]; then
    frac_len=${#frac_part}
    frac_digits=$((10#$frac_part))
    local i
    for ((i = 0; i < frac_len; i++)); do
      pow=$((pow * 10))
    done
  fi
  # X == (value expressed in the given unit) * pow, as an integer.
  local X=$((int_part * pow + frac_digits))

  local mib
  case "$unit" in
    Gi)
      mib=$(((X * 1024 + pow / 2) / pow))
      ;;
    Mi)
      mib=$(((X + pow / 2) / pow))
      ;;
    Ki)
      mib=$(((X + (pow * 1024) / 2) / (pow * 1024)))
      ;;
    G)
      mib=$(((X * 1000000000 + (pow * 1048576) / 2) / (pow * 1048576)))
      ;;
    M)
      mib=$(((X * 1000000 + (pow * 1048576) / 2) / (pow * 1048576)))
      ;;
    K)
      mib=$(((X * 1000 + (pow * 1048576) / 2) / (pow * 1048576)))
      ;;
    "")
      mib=$(((X + (pow * 1048576) / 2) / (pow * 1048576)))
      ;;
    *)
      return 1
      ;;
  esac
  printf '%s\n' "$mib"
  return 0
}

# parse_safety_factor_x100 <float>
# Prints the value scaled by 100 as an integer (e.g. "1.5" -> 150). Returns 1
# on unparseable input. Scaling by 100 keeps all downstream comparisons in
# pure integer arithmetic (no bc, no bash floats).
parse_safety_factor_x100() {
  local s="$1"
  if ! _split_decimal "$s"; then
    return 1
  fi
  local pow=1 i
  for ((i = 0; i < DEC_LEN; i++)); do
    pow=$((pow * 10))
  done
  local frac_digits=0
  [[ "$DEC_LEN" -gt 0 ]] && frac_digits=$((10#$DEC_FRAC))
  local X=$((DEC_INT * pow + frac_digits))
  printf '%s\n' "$(((X * 100 + pow / 2) / pow))"
  return 0
}

# class_to_mib <name> — prints the default MiB for a named estimate class.
class_to_mib() {
  case "$1" in
    trivial) echo 32 ;;
    light) echo 128 ;;
    rails-boot) echo 768 ;;
    rails-query) echo 1536 ;;
    heavy) echo 3072 ;;
    *) return 1 ;;
  esac
}

fmt_mib() { printf '%sMi' "$1"; }

# --- step 1: arg parsing (pure — no kubectl calls) ----------------------------

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
DEPLOY_ARG=""
POD_ARG=""
SELECTOR_ARG=""
ESTIMATE_ARG="$DEFAULT_ESTIMATE_CLASS"
SAFETY_FACTOR_ARG="$DEFAULT_SAFETY_FACTOR"
TOP_ARG="$DEFAULT_TOP"
JSON_MODE=0

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
    --deploy)
      shift
      DEPLOY_ARG="${1:-}"
      if [[ -z "$DEPLOY_ARG" ]]; then
        echo "ERROR: --deploy requires a value." >&2
        print_usage >&2
        exit 2
      fi
      shift
      ;;
    --pod)
      shift
      POD_ARG="${1:-}"
      if [[ -z "$POD_ARG" ]]; then
        echo "ERROR: --pod requires a value." >&2
        print_usage >&2
        exit 2
      fi
      shift
      ;;
    --selector)
      shift
      SELECTOR_ARG="${1:-}"
      if [[ -z "$SELECTOR_ARG" ]]; then
        echo "ERROR: --selector requires a value (e.g. app=foo)." >&2
        print_usage >&2
        exit 2
      fi
      shift
      ;;
    --estimate)
      shift
      ESTIMATE_ARG="${1:-}"
      if [[ -z "$ESTIMATE_ARG" ]]; then
        echo "ERROR: --estimate requires a value." >&2
        print_usage >&2
        exit 2
      fi
      shift
      ;;
    --safety-factor)
      shift
      SAFETY_FACTOR_ARG="${1:-}"
      if [[ -z "$SAFETY_FACTOR_ARG" ]]; then
        echo "ERROR: --safety-factor requires a value." >&2
        print_usage >&2
        exit 2
      fi
      shift
      ;;
    --top)
      shift
      TOP_ARG="${1:-}"
      if [[ -z "$TOP_ARG" ]]; then
        echo "ERROR: --top requires a value." >&2
        print_usage >&2
        exit 2
      fi
      shift
      ;;
    --json)
      JSON_MODE=1
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

TARGET_COUNT=0
[[ -n "$DEPLOY_ARG" ]] && TARGET_COUNT=$((TARGET_COUNT + 1))
[[ -n "$POD_ARG" ]] && TARGET_COUNT=$((TARGET_COUNT + 1))
[[ -n "$SELECTOR_ARG" ]] && TARGET_COUNT=$((TARGET_COUNT + 1))
if [[ "$TARGET_COUNT" -ne 1 ]]; then
  echo "ERROR: exactly one of --deploy, --pod, --selector is required (got ${TARGET_COUNT})." >&2
  print_usage >&2
  exit 2
fi

if class_to_mib "$ESTIMATE_ARG" >/dev/null 2>&1; then
  ESTIMATE_LABEL="$ESTIMATE_ARG"
  ESTIMATE_MIB="$(class_to_mib "$ESTIMATE_ARG")"
elif ESTIMATE_MIB="$(parse_size_mib "$ESTIMATE_ARG" 2>/dev/null)"; then
  ESTIMATE_LABEL="explicit:${ESTIMATE_ARG}"
else
  echo "ERROR: --estimate value '${ESTIMATE_ARG}' is not a recognized class (trivial, light, rails-boot, rails-query, heavy) or a parseable size (e.g. 900Mi, 1.5Gi, 1048576)." >&2
  print_usage >&2
  exit 2
fi

if ! SAFETY_FACTOR_X100="$(parse_safety_factor_x100 "$SAFETY_FACTOR_ARG")"; then
  echo "ERROR: --safety-factor '${SAFETY_FACTOR_ARG}' is not a valid non-negative number (e.g. 1.5)." >&2
  print_usage >&2
  exit 2
fi

if ! [[ "$TOP_ARG" =~ ^[0-9]+$ ]] || [[ "$TOP_ARG" -lt 1 ]]; then
  echo "ERROR: --top must be a positive integer, got '${TOP_ARG}'." >&2
  print_usage >&2
  exit 2
fi
TOP_N="$TOP_ARG"

if [[ -n "$DEPLOY_ARG" ]]; then
  TARGET_DESC="deploy:${DEPLOY_ARG}"
elif [[ -n "$POD_ARG" ]]; then
  TARGET_DESC="pod:${POD_ARG}"
else
  TARGET_DESC="selector:${SELECTOR_ARG}"
fi

pass "arguments valid (env=${ENV}, namespace=${NAMESPACE}, target=${TARGET_DESC}, estimate=${ESTIMATE_LABEL} ($(fmt_mib "$ESTIMATE_MIB")), safety_factor=${SAFETY_FACTOR_ARG} (x100=${SAFETY_FACTOR_X100}), top=${TOP_N}, json=${JSON_MODE})"

if [[ "${K8S_SAFE_EXEC_SKIP_CLUSTER:-0}" == "1" ]]; then
  echo "WARN: K8S_SAFE_EXEC_SKIP_CLUSTER=1 set — skipping all live-cluster checks (test/dev mode only; never set this for a real check)." >&2
  section "Summary (local validation only)"
  echo "  env:       ${ENV}"
  echo "  namespace: ${NAMESPACE}"
  echo "  target:    ${TARGET_DESC}"
  echo "  estimate:  ${ESTIMATE_LABEL} = $(fmt_mib "$ESTIMATE_MIB")"
  echo "  verdict:   SKIPPED — no cluster checks performed"
  exit 0
fi

# --- step 2: context resolution -----------------------------------------------
# Every live kubectl call below passes --context explicitly, so (unlike
# preflight.sh) we do not need to also gate on ambient current-context — we
# never rely on it. resolve_context() still guarantees the context name is
# real and unambiguous in the operator's kubeconfig.

section "Context resolution"
if ! RESOLVED_CONTEXT="$(resolve_context "$ENV")"; then
  fail "Could not resolve a unique kubectl context for env '${ENV}'. See details above."
  exit 1
fi
pass "Resolved context for env '${ENV}': ${RESOLVED_CONTEXT}"

KCTL=(kubectl --context "$RESOLVED_CONTEXT" -n "$NAMESPACE" --request-timeout="$KUBECTL_REQUEST_TIMEOUT")

# --- step 3: resolve the candidate pod list -----------------------------------

SELECTOR=""
GET_FILTER=()
TOP_FILTER=()

if [[ -n "$POD_ARG" ]]; then
  GET_FILTER=(--field-selector "metadata.name=${POD_ARG}")
  TOP_FILTER=("$POD_ARG")
elif [[ -n "$DEPLOY_ARG" ]]; then
  if ! command -v jq >/dev/null 2>&1; then
    fail "jq is required to resolve --deploy's label selector but is not installed."
    exit 1
  fi
  section "Resolving Deployment/${DEPLOY_ARG}"
  if ! DEPLOY_JSON="$("${KCTL[@]}" get deploy "$DEPLOY_ARG" -o json 2>&1)"; then
    fail "Deployment '${DEPLOY_ARG}' not found in ${NAMESPACE}/${RESOLVED_CONTEXT}: ${DEPLOY_JSON}"
    exit 1
  fi
  SELECTOR="$(printf '%s' "$DEPLOY_JSON" | jq -r '.spec.selector.matchLabels // {} | to_entries | map("\(.key)=\(.value)") | join(",")' 2>&1 || true)"
  if [[ -z "$SELECTOR" || "$SELECTOR" == "null" ]]; then
    fail "Could not derive a label selector from Deployment/${DEPLOY_ARG}'s spec.selector.matchLabels."
    exit 1
  fi
  pass "Derived selector from Deployment/${DEPLOY_ARG}: ${SELECTOR}"
  GET_FILTER=(-l "$SELECTOR" --field-selector "status.phase=Running")
  TOP_FILTER=(-l "$SELECTOR")
else
  SELECTOR="$SELECTOR_ARG"
  GET_FILTER=(-l "$SELECTOR" --field-selector "status.phase=Running")
  TOP_FILTER=(-l "$SELECTOR")
fi

section "Candidate pods (${NAMESPACE}, ${TARGET_DESC})"

FIELDS_RAW=""
if ! FIELDS_RAW="$("${KCTL[@]}" get pods "${GET_FILTER[@]}" \
  -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[0].resources.limits.memory}{"\t"}{.spec.containers[0].resources.requests.memory}{"\t"}{.spec.nodeName}{"\n"}{end}' 2>&1)"; then
  fail "Could not list candidate pods: ${FIELDS_RAW}"
  exit 1
fi

if [[ -z "$(printf '%s' "$FIELDS_RAW" | tr -d '[:space:]')" ]]; then
  if [[ -n "$POD_ARG" ]]; then
    fail "Pod '${POD_ARG}' not found (or not Running) in ${NAMESPACE}/${RESOLVED_CONTEXT}."
  else
    fail "No Running pods matched ${TARGET_DESC} in ${NAMESPACE}/${RESOLVED_CONTEXT}."
  fi
  exit 1
fi

POD_NAMES=()
POD_LIMIT_RAW=()
POD_REQUEST_RAW=()
POD_NODE=()
while IFS=$'\t' read -r p_name p_limit p_request p_node; do
  [[ -z "$p_name" ]] && continue
  POD_NAMES+=("$p_name")
  POD_LIMIT_RAW+=("$p_limit")
  POD_REQUEST_RAW+=("$p_request")
  POD_NODE+=("$p_node")
done <<<"$FIELDS_RAW"

pass "Found ${#POD_NAMES[@]} candidate pod(s)."

# --- step 4: live usage (kubectl top pod) — best-effort, metrics-server can be down ---

METRICS_DOWN=0
TOP_NAMES=()
TOP_USAGE_RAW=()

section "Resource usage (kubectl top pod)"
if TOP_OUT="$("${KCTL[@]}" top pod "${TOP_FILTER[@]}" --no-headers 2>&1)"; then
  while read -r t_name t_cpu t_mem; do
    [[ -z "$t_name" ]] && continue
    TOP_NAMES+=("$t_name")
    TOP_USAGE_RAW+=("$t_mem")
  done <<<"$TOP_OUT"
  pass "kubectl top pod succeeded (${#TOP_NAMES[@]} row(s))."
else
  METRICS_DOWN=1
  warn "kubectl top pod unavailable or failed (metrics-server may not be installed): ${TOP_OUT}"
fi

usage_raw_for_pod() {
  local target="$1" i
  for ((i = 0; i < ${#TOP_NAMES[@]}; i++)); do
    if [[ "${TOP_NAMES[$i]}" == "$target" ]]; then
      printf '%s\n' "${TOP_USAGE_RAW[$i]}"
      return 0
    fi
  done
  return 1
}

# --- step 5: node allocatable + usage (cached per unique node) ---------------

NODE_NAMES=()
NODE_ALLOC_MIB=()
NODE_USAGE_MIB=()

node_index_for() {
  local target="$1" i
  for ((i = 0; i < ${#NODE_NAMES[@]}; i++)); do
    if [[ "${NODE_NAMES[$i]}" == "$target" ]]; then
      printf '%s\n' "$i"
      return 0
    fi
  done
  return 1
}

ensure_node_data() {
  # Sets global LAST_NODE_IDX and returns 0 on success. Deliberately NOT
  # invoked via command substitution: `x="$(ensure_node_data ...)"` would run
  # this function in a subshell, and its NODE_NAMES/NODE_ALLOC_MIB/
  # NODE_USAGE_MIB += appends would then vanish the instant that subshell
  # exits, leaving the caller's arrays empty (and, under `set -u`, an
  # "unbound variable" error on the next lookup). Call it as a plain
  # statement (`if ensure_node_data "$node"; then ...`) so the array
  # mutations happen in — and persist in — the current shell.
  local node="$1"
  LAST_NODE_IDX=-1
  if [[ -z "$node" ]]; then
    return 1
  fi
  local idx
  if idx="$(node_index_for "$node")"; then
    LAST_NODE_IDX="$idx"
    return 0
  fi

  local alloc_mib=-1 usage_mib=-1 alloc_raw=""
  if alloc_raw="$(kubectl --context "$RESOLVED_CONTEXT" --request-timeout="$KUBECTL_REQUEST_TIMEOUT" \
    get node "$node" -o jsonpath='{.status.allocatable.memory}' 2>&1)"; then
    alloc_mib="$(parse_size_mib "$alloc_raw" 2>/dev/null || echo -1)"
  else
    warn "Could not read allocatable memory for node ${node}: ${alloc_raw}"
  fi

  if [[ "$METRICS_DOWN" -eq 0 ]]; then
    local node_top_out
    if node_top_out="$(kubectl --context "$RESOLVED_CONTEXT" --request-timeout="$KUBECTL_REQUEST_TIMEOUT" \
      top node "$node" --no-headers 2>&1)"; then
      local n_name n_cpu n_cpupct n_mem n_mempct
      read -r n_name n_cpu n_cpupct n_mem n_mempct <<<"$node_top_out"
      usage_mib="$(parse_size_mib "$n_mem" 2>/dev/null || echo -1)"
    else
      warn "kubectl top node failed for ${node}: ${node_top_out}"
    fi
  fi

  NODE_NAMES+=("$node")
  NODE_ALLOC_MIB+=("$alloc_mib")
  NODE_USAGE_MIB+=("$usage_mib")
  LAST_NODE_IDX=$((${#NODE_NAMES[@]} - 1))
  return 0
}

# --- step 6: per-candidate computation ---------------------------------------

section "Node headroom"

RANK_LINES=()   # "effective_sort_key\tarray_index"
CAND_LIMIT_MIB=()
CAND_LIMIT_DISPLAY=()
CAND_USAGE_MIB=()
CAND_USAGE_DISPLAY=()
CAND_POD_HEADROOM_DISPLAY=()
CAND_NODE_DISPLAY=()
CAND_NODE_HEADROOM_DISPLAY=()
CAND_EFFECTIVE_MIB=()
CAND_EFFECTIVE_DISPLAY=()
CAND_VERDICT=()

for ((i = 0; i < ${#POD_NAMES[@]}; i++)); do
  name="${POD_NAMES[$i]}"
  limit_raw="${POD_LIMIT_RAW[$i]}"
  node="${POD_NODE[$i]}"

  limit_mib=-1
  limit_display="no-limit"
  if [[ -n "$limit_raw" ]]; then
    if limit_mib="$(parse_size_mib "$limit_raw" 2>/dev/null)"; then
      limit_display="$(fmt_mib "$limit_mib")"
    else
      warn "Could not parse limit '${limit_raw}' for pod ${name}; treating as no-limit."
      limit_mib=-1
    fi
  fi

  usage_mib=-1
  usage_display="unknown"
  usage_raw=""
  if [[ "$METRICS_DOWN" -eq 0 ]] && usage_raw="$(usage_raw_for_pod "$name")"; then
    if usage_mib="$(parse_size_mib "$usage_raw" 2>/dev/null)"; then
      usage_display="$(fmt_mib "$usage_mib")"
    else
      usage_mib=-1
    fi
  fi

  node_alloc_mib=-1
  node_usage_mib=-1
  if [[ "$METRICS_DOWN" -eq 0 ]] && ensure_node_data "$node"; then
    node_idx="$LAST_NODE_IDX"
    node_alloc_mib="${NODE_ALLOC_MIB[$node_idx]}"
    node_usage_mib="${NODE_USAGE_MIB[$node_idx]}"
  fi

  node_headroom_mib=-1
  node_headroom_display="unknown"
  if [[ "$node_alloc_mib" -ge 0 && "$node_usage_mib" -ge 0 ]]; then
    node_headroom_mib=$((node_alloc_mib - node_usage_mib))
    node_headroom_display="$(fmt_mib "$node_headroom_mib")"
  fi

  pod_headroom_display="unknown"
  pod_headroom_mib=-1
  if [[ "$limit_mib" -ge 0 && "$usage_mib" -ge 0 ]]; then
    pod_headroom_mib=$((limit_mib - usage_mib))
    pod_headroom_display="$(fmt_mib "$pod_headroom_mib")"
  elif [[ "$limit_mib" -lt 0 ]]; then
    pod_headroom_display="no-limit"
  fi

  # effective = min(pod_headroom, node_headroom); if the pod has no limit,
  # fall back to node headroom alone (no-limit is NOT infinite headroom).
  have_pod_headroom=0
  [[ "$limit_mib" -ge 0 && "$usage_mib" -ge 0 ]] && have_pod_headroom=1
  have_node_headroom=0
  [[ "$node_headroom_mib" -ge 0 ]] && have_node_headroom=1

  effective_mib=-1
  effective_display="unknown"
  verdict="N/A"

  if [[ "$have_pod_headroom" -eq 1 && "$have_node_headroom" -eq 1 ]]; then
    if [[ "$pod_headroom_mib" -le "$node_headroom_mib" ]]; then
      effective_mib="$pod_headroom_mib"
    else
      effective_mib="$node_headroom_mib"
    fi
  elif [[ "$have_node_headroom" -eq 1 && "$limit_mib" -lt 0 ]]; then
    # no-limit: fall back to node headroom alone
    effective_mib="$node_headroom_mib"
  elif [[ "$have_pod_headroom" -eq 1 && "$have_node_headroom" -eq 0 ]]; then
    # node data unavailable (shouldn't happen unless a single node's `top`
    # call failed while metrics-server is otherwise up) — be conservative,
    # do not claim a verdict without node-pressure visibility.
    effective_mib=-1
  fi

  if [[ "$effective_mib" -ge 0 ]]; then
    effective_display="$(fmt_mib "$effective_mib")"
    if (((effective_mib * 100) >= (ESTIMATE_MIB * SAFETY_FACTOR_X100))); then
      verdict="OK"
    elif ((effective_mib >= ESTIMATE_MIB)); then
      verdict="TIGHT"
    else
      verdict="NO"
    fi
  fi

  CAND_LIMIT_MIB+=("$limit_mib")
  CAND_LIMIT_DISPLAY+=("$limit_display")
  CAND_USAGE_MIB+=("$usage_mib")
  CAND_USAGE_DISPLAY+=("$usage_display")
  CAND_POD_HEADROOM_DISPLAY+=("$pod_headroom_display")
  CAND_NODE_DISPLAY+=("${node:-unknown}")
  CAND_NODE_HEADROOM_DISPLAY+=("$node_headroom_display")
  CAND_EFFECTIVE_MIB+=("$effective_mib")
  CAND_EFFECTIVE_DISPLAY+=("$effective_display")
  CAND_VERDICT+=("$verdict")

  sort_key="$effective_mib"
  [[ "$sort_key" -lt 0 ]] && sort_key=-999999
  RANK_LINES+=("$(printf '%d\t%d' "$sort_key" "$i")")
done

if [[ "$METRICS_DOWN" -eq 1 ]]; then
  section "Candidates (limits/requests only — usage unavailable)"
  printf '%-50s %-10s %-10s\n' "POD" "LIMIT" "REQUEST"
  n_printed=0
  for ((i = 0; i < ${#POD_NAMES[@]}; i++)); do
    [[ "$n_printed" -ge "$TOP_N" ]] && break
    req_display="unknown"
    if [[ -n "${POD_REQUEST_RAW[$i]}" ]]; then
      req_mib="$(parse_size_mib "${POD_REQUEST_RAW[$i]}" 2>/dev/null || echo "")"
      [[ -n "$req_mib" ]] && req_display="$(fmt_mib "$req_mib")"
    fi
    printf '%-50s %-10s %-10s\n' "${POD_NAMES[$i]}" "${CAND_LIMIT_DISPLAY[$i]}" "$req_display"
    n_printed=$((n_printed + 1))
  done
  echo
  echo "INCONCLUSIVE: kubectl top (metrics-server) is unavailable, so live usage and headroom cannot be computed. Do not treat unknown usage as zero. No recommendation can be made from this run — retry once metrics-server is healthy, or fall back to manual inspection."
  exit 3
fi

# Sort candidates by effective headroom descending.
SORTED="$(printf '%s\n' "${RANK_LINES[@]}" | sort -t $'\t' -k1,1nr)"

echo
if [[ "$JSON_MODE" -eq 1 ]]; then
  json_items=""
  n_printed=0
  first=1
  while IFS=$'\t' read -r _key idx; do
    [[ -z "$idx" ]] && continue
    [[ "$n_printed" -ge "$TOP_N" ]] && break
    n_printed=$((n_printed + 1))
    [[ "$first" -eq 0 ]] && json_items="${json_items},"
    first=0
    json_items="${json_items}{\"pod\":\"${POD_NAMES[$idx]}\",\"limit\":\"${CAND_LIMIT_DISPLAY[$idx]}\",\"usage\":\"${CAND_USAGE_DISPLAY[$idx]}\",\"pod_headroom\":\"${CAND_POD_HEADROOM_DISPLAY[$idx]}\",\"node\":\"${CAND_NODE_DISPLAY[$idx]}\",\"node_headroom\":\"${CAND_NODE_HEADROOM_DISPLAY[$idx]}\",\"effective\":\"${CAND_EFFECTIVE_DISPLAY[$idx]}\",\"verdict\":\"${CAND_VERDICT[$idx]}\"}"
  done <<<"$SORTED"

  top_key_idx="$(printf '%s\n' "$SORTED" | head -1)"
  top_idx="${top_key_idx##*$'\t'}"
  recommendation="null"
  exit_code=1
  if [[ -n "$top_idx" ]]; then
    top_verdict="${CAND_VERDICT[$top_idx]}"
    if [[ "$top_verdict" == "OK" || "$top_verdict" == "TIGHT" ]]; then
      recommendation="{\"pod\":\"${POD_NAMES[$top_idx]}\",\"verdict\":\"${top_verdict}\",\"effective\":\"${CAND_EFFECTIVE_DISPLAY[$top_idx]}\"}"
      exit_code=0
    fi
  fi

  printf '{"env":"%s","namespace":"%s","target":"%s","estimate":{"label":"%s","mib":%s},"safety_factor":%s,"candidates":[%s],"recommendation":%s,"exit_code":%s}\n' \
    "$ENV" "$NAMESPACE" "$TARGET_DESC" "$ESTIMATE_LABEL" "$ESTIMATE_MIB" "$SAFETY_FACTOR_ARG" "$json_items" "$recommendation" "$exit_code"
  exit "$exit_code"
fi

section "Candidates (top ${TOP_N} of ${#POD_NAMES[@]}, ranked by effective headroom)"
printf '%-50s %-8s %-8s %-14s %-46s %-14s %-10s %-8s\n' \
  "POD" "LIMIT" "USAGE" "POD_HEADROOM" "NODE" "NODE_HEADROOM" "EFFECTIVE" "VERDICT"

n_printed=0
TOP_IDX=""
while IFS=$'\t' read -r _key idx; do
  [[ -z "$idx" ]] && continue
  [[ "$n_printed" -ge "$TOP_N" ]] && break
  [[ -z "$TOP_IDX" ]] && TOP_IDX="$idx"
  printf '%-50s %-8s %-8s %-14s %-46s %-14s %-10s %-8s\n' \
    "${POD_NAMES[$idx]}" "${CAND_LIMIT_DISPLAY[$idx]}" "${CAND_USAGE_DISPLAY[$idx]}" \
    "${CAND_POD_HEADROOM_DISPLAY[$idx]}" "${CAND_NODE_DISPLAY[$idx]}" "${CAND_NODE_HEADROOM_DISPLAY[$idx]}" \
    "${CAND_EFFECTIVE_DISPLAY[$idx]}" "${CAND_VERDICT[$idx]}"
  n_printed=$((n_printed + 1))
done <<<"$SORTED"

section "Recommendation"

if [[ -z "$TOP_IDX" ]]; then
  fail "No candidates were evaluated."
  exit 1
fi

TOP_VERDICT="${CAND_VERDICT[$TOP_IDX]}"
if [[ "$TOP_VERDICT" == "OK" || "$TOP_VERDICT" == "TIGHT" ]]; then
  echo "Best candidate: ${POD_NAMES[$TOP_IDX]} (verdict ${TOP_VERDICT}, effective headroom ${CAND_EFFECTIVE_DISPLAY[$TOP_IDX]} vs. estimate $(fmt_mib "$ESTIMATE_MIB") x ${SAFETY_FACTOR_ARG})."
  echo "Use: --pod ${POD_NAMES[$TOP_IDX]}"
  if [[ "$TOP_VERDICT" == "TIGHT" ]]; then
    echo "NOTE: TIGHT means headroom covers the estimate but not the full safety factor — proceed with extra caution, and re-run posthealth.sh promptly after."
  fi
  exit 0
else
  echo "NO viable pod: every candidate's effective headroom is below the estimate ($(fmt_mib "$ESTIMATE_MIB")), even before applying the ${SAFETY_FACTOR_ARG}x safety factor."
  echo "Do not exec into any of these pods. Use the ephemeral-pod path instead (see SKILL.md section 6) — it runs in its own cgroup with its own memory limit, so an OOM only kills the throwaway pod, never one of these serving/queue-draining pods."
  exit 1
fi
