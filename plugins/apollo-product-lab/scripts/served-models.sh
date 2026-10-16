#!/usr/bin/env bash
# Report which model family served Claude Code requests in a time window, from the shunt log, and
# decide whether one lens can be credited with a cross-family review (doc 44 §2).
#
# The shunt log has no per-subagent id: sub-agents share the parent's session_id. A window can only be
# credited to one lens when that lens was the only one in flight that could request the expected model.
# Pass --sole to assert that (you dispatched it alone, or serially). Without --sole, a window that also
# carries other traffic is reported as ambiguous, not as served. For parallel cross-family lenses, use
# `codex exec` per lens instead; its stderr header names model, provider and effort for that run alone.
#
# Usage: served-models.sh [--since <UTC ISO-8601>] [--until <UTC ISO-8601>] [--session <id>]
#                         [--log <path>] [--expect <model>] [--provider <name>] [--effort <level>] [--sole]
# Example:
#   start=$(date -u +%Y-%m-%dT%H:%M:%SZ); <dispatch the lens alone>; end=$(date -u +%Y-%m-%dT%H:%M:%SZ)
#   served-models.sh --since "$start" --until "$end" --expect gpt-6-astra --effort xhigh --sole
# --provider defaults to codex for gpt-* models and anthropic for claude-* models; a hit must match it.
# --effort checks the expected model's route effort in the shunt config; a mismatch or a missing
# config fails the check.
# What this cannot prove: that the lens's final answer came from those requests rather than from
# another call in the same window. That is why --sole is an assertion, and why parallel cross-family
# lenses should use codex exec, whose header is per run.
# Exit codes (with --expect):
#   0 served: the expected model answered 2xx through the expected provider (and effort, if given) and
#     the window can be attributed (--sole)
#   3 not served: the window has requests but none for the expected model and provider with 2xx
#   5 effort mismatch: served, but the shunt config effort is not the --effort asked for (or unknown)
#   4 ambiguous: the expected model answered, but --sole was not given; tag independence: unknown
#   2 unknown: no log, or no requests at all in the window; tag independence: unknown
set -euo pipefail

since=""; until=""; session=""; expect=""; sole=0; provider=""; want_effort=""
log="${SHUNT_LOG:-}"
while [ $# -gt 0 ]; do
  case "$1" in
    --since) since="$2"; shift 2 ;;
    --until) until="$2"; shift 2 ;;
    --session) session="$2"; shift 2 ;;
    --log) log="$2"; shift 2 ;;
    --expect) expect="$2"; shift 2 ;;
    --sole) sole=1; shift ;;
    --provider) provider="$2"; shift 2 ;;
    --effort) want_effort="$2"; shift 2 ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

# Normalise a UTC timestamp to YYYY-MM-DDTHH:MM:SS.ffffff so string comparison is time comparison.
# $2 is the fraction used when none is given: 000000 for a start, 999999 for an end, so an end in whole
# seconds covers that whole second (date -u +%S truncates; a lens may still be answering in it).
norm() {
  local t="$1" pad="$2" base frac
  t="${t%Z}"; t="${t%+00:00}"
  case "$t" in *T*[+-][0-9][0-9]:[0-9][0-9]) echo "timestamps must be UTC (Z): $1" >&2; exit 2 ;; esac
  base="${t%%.*}"
  if [ "$base" != "$t" ]; then frac="${t#*.}000000"; frac="${frac:0:6}"; else frac="$pad"; fi
  [ "${#base}" -eq 16 ] && base="$base:00"
  echo "$base.$frac"
}
since="$(norm "${since:-1970-01-01T00:00:00}" 000000)"
until="$(norm "${until:-9999-12-31T23:59:59}" 999999)"

if [ -z "$log" ]; then
  for cand in "$(brew --prefix 2>/dev/null)/var/log/shunt.log" "$HOME/Library/Logs/shunt.log" "$HOME/.local/state/shunt/shunt.log"; do
    [ -f "$cand" ] && log="$cand" && break
  done
fi
if [ -z "$log" ] || [ ! -f "$log" ]; then
  echo "unknown: no shunt log found (set SHUNT_LOG or --log); tag the lens independence: unknown" >&2
  exit 2
fi

tmp="$(mktemp "${TMPDIR:-/tmp}/served-models.XXXXXX")"
trap 'rm -f "$tmp"' EXIT

sed 's/\x1b\[[0-9;]*m//g' "$log" \
  | awk -v s="$since" -v u="$until" -v sess="$session" '
      /proxy_request/ {
        ts = $1; sub(/Z$/, "", ts)
        if (index(ts, ".") == 0) ts = ts ".000000"
        ts = substr(ts "000000", 1, 26)
        if (ts < s || ts > u) next
        if (sess != "" && index($0, "session_id=\"" sess "\"") == 0) next
        m = ""; p = ""
        if (match($0, /gen_ai\.request\.model="[^"]*"/)) m = substr($0, RSTART + 22, RLENGTH - 23)
        if (match($0, /shunt\.provider="[^"]*"/)) p = substr($0, RSTART + 16, RLENGTH - 17)
        st = "?"
        if (match($0, /http\.response\.status_code=[0-9]+/)) st = substr($0, RSTART + 26, RLENGTH - 26)
        fam = (p == "anthropic") ? "anthropic" : (p == "codex" ? "openai" : p)
        key = fam "\t" m "\t" p "\t" st
        n[key]++
        if (!(key in first)) first[key] = $1
        last[key] = $1
      }
      END {
        printf "family\tmodel\tprovider\tstatus\trequests\tfirst\tlast\n"
        for (k in n) printf "%s\t%d\t%s\t%s\n", k, n[k], first[k], last[k]
      }' > "$tmp"

column -t -s $'\t' "$tmp"

conf="${SHUNT_CONFIG:-$HOME/.config/shunt/shunt.toml}"
effort=""
if [ -f "$conf" ]; then
  effort="$(awk -v wanted="$expect" '
    function value(line) { sub(/^[^=]*=[[:space:]]*"/, "", line); sub(/".*/, "", line); return line }
    function emit() { if (!done && route_model == wanted && route_effort != "") { print route_effort; done = 1 } }
    /^\[\[routes\]\]/ { emit(); in_route = 1; route_model = ""; route_effort = ""; next }
    /^\[/ { emit(); in_route = 0 }
    in_route && /^[[:space:]]*model[[:space:]]*=/ { route_model = value($0) }
    in_route && /^[[:space:]]*effort[[:space:]]*=/ { route_effort = value($0) }
    END { emit() }' "$conf")"
  echo "codex route effort (shunt config): ${effort:-not set}"
fi

[ -z "$expect" ] && exit 0
if [ -z "$provider" ]; then
  case "$expect" in gpt-*|o[0-9]*) provider="codex" ;; claude-*) provider="anthropic" ;; esac
fi

total="$(awk -F'\t' 'NR > 1 { t += $5 } END { print t + 0 }' "$tmp")"
hit="$(awk -F'\t' -v e="$expect" -v p="$provider" 'NR > 1 && $2 == e && (p == "" || $3 == p) && $4 ~ /^2/ { t += $5 } END { print t + 0 }' "$tmp")"
if [ "$total" -eq 0 ]; then
  echo "unknown: no requests in this window; tag the lens independence: unknown" >&2
  exit 2
fi
if [ "$hit" -eq 0 ]; then
  echo "NOT served: $expect via ${provider:-any provider} in this window; the lens was not answered by it" >&2
  exit 3
fi
if [ -n "$want_effort" ] && [ "$effort" != "$want_effort" ]; then
  echo "effort mismatch: asked for $want_effort, shunt config says ${effort:-unknown}; record the served effort, not the requested one" >&2
  exit 5
fi
if [ "$sole" -eq 1 ]; then
  echo "served: $expect ($hit of $total requests in the window)"
  exit 0
fi
echo "ambiguous: $expect answered $hit of $total requests; without --sole the window cannot be credited to one lens; tag independence: unknown" >&2
exit 4
