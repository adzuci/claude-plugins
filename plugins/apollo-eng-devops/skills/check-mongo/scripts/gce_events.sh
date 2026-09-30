#!/usr/bin/env bash
# Read-only GCE context for /check-mongo --gce. Only three gcloud command prefixes are ever
# executed: `compute operations list`, `logging read`, `auth list`. No ssh, no serial-port
# output, no mongosh. Every call goes through gc(), which enforces the allowlist.
# Usage: gce_events.sh --cluster <cluster> --window 1h|6h|24h
# Test hook: gce_events.sh --probe-gc <gcloud args...> runs gc() directly.
set -euo pipefail

PROJECT="indigo-lotus-415"
CLUSTERS=" main accounts contacts custom-objects email emailermessages noncustomer "
DENY_RE='ssh|serial|delete|reset|stop|start|--command'
UTC_FMT="format='%Y-%m-%dT%H:%M:%SZ',tz=UTC"
cluster="main"
window="1h"
probe=0
probe_args=()

# Reject unless the command starts with an allowlisted prefix and no arg looks destructive.
guard() {
  case "$*" in
    "compute operations list"* | "logging read"* | "auth list"*) ;;
    *) echo "refused: gcloud command not in allowlist (compute operations list | logging read | auth list)" >&2; exit 3 ;;
  esac
  local a
  for a in "$@"; do
    if printf '%s' "$a" | grep -Eqi -- "$DENY_RE"; then
      echo "refused: gcloud argument '$a' matches a denied pattern" >&2; exit 3
    fi
  done
}

gc() {
  guard "$@"
  gcloud "$@"
}

while [ $# -gt 0 ]; do
  case "$1" in
    --cluster) cluster="${2:-}"; shift 2 ;;
    --window) window="${2:-}"; shift 2 ;;
    --probe-gc) probe=1; shift; probe_args=("$@"); break ;;
    *) echo "usage: $0 --cluster <cluster> --window 1h|6h|24h" >&2; exit 2 ;;
  esac
done

if [ "$probe" = 1 ]; then gc "${probe_args[@]}"; exit 0; fi

cluster="${cluster#mongo-}"
case "$CLUSTERS" in *" $cluster "*) ;; *) echo "error: unknown cluster; valid:$CLUSTERS" >&2; exit 2 ;; esac
case "$window" in
  1h) iso="PT1H" ;; 6h) iso="PT6H" ;; 24h) iso="PT24H" ;;
  *) echo "error: window must be 1h, 6h or 24h" >&2; exit 2 ;;
esac

if ! command -v gcloud >/dev/null 2>&1; then
  echo "gce: skipped (gcloud not installed)"; exit 0
fi
account="$(gc auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null || true)"
if [ -z "$account" ]; then
  echo "gce: skipped (gcloud not authenticated; run 'gcloud auth login')"; exit 0
fi

echo "## GCE operations (last $window, cluster $cluster)"
if ! gc compute operations list --project "$PROJECT" \
  --filter="targetLink~\"mongos?-$cluster-\" AND insertTime>-$iso" \
  --sort-by=~insertTime --limit 50 \
  --format="table(insertTime.date($UTC_FMT),targetLink.basename():label=VM,operationType:label=EVENT)" 2>/dev/null; then
  echo "gce: operations list failed (permissions?); skipped"
fi

echo "## OOM log entries (last $window, cluster $cluster)"
if ! gc logging read \
  "resource.type=gce_instance AND labels.\"compute.googleapis.com/resource_name\"=~\"^mongos?-$cluster-\" AND (textPayload:\"Out of memory\" OR textPayload:\"oom-kill\")" \
  --project "$PROJECT" --freshness "$iso" --limit 50 \
  --format="table(timestamp.date($UTC_FMT),labels.\"compute.googleapis.com/resource_name\":label=VM,severity:label=EVENT)" 2>/dev/null; then
  echo "gce: logging read failed (permissions?); skipped"
fi
