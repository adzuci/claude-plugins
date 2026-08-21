#!/usr/bin/env bash
# lib_context.sh — shared, READ-ONLY helpers for the k8s-safe-exec skill's
# preflight.sh and posthealth.sh scripts.
#
# This file is meant to be `source`d, not executed directly. It never runs
# anything beyond local kubeconfig reads (`kubectl config ...`), which touch
# no live cluster. It NEVER execs, deletes, patches, applies, scales, or
# switches the operator's kube context.
#
# Context names vary per engineer, so contexts are always resolved dynamically
# from `kubectl config get-contexts -o name` — never hardcode a literal
# context string. Resolution strategy: filter the real context list by an
# env-distinguishing suffix (prod -> "_prod", stage -> "_staging"). Both
# failure modes are guarded: zero matches (tell the operator to run
# `gcloud container clusters get-credentials` and list what they DO have) and
# multiple matches (ambiguous — list candidates, refuse to pick, return 1).
# There is intentionally no fallback to "just use current-context": on at
# least one dev machine, current-context was already the prod context, so
# silently trusting it would be unsafe.

# usage_env_line: the canonical "valid values" text shared by both scripts'
# usage/error output.
usage_env_line() {
  echo "Valid environments: stage prod"
}

# validate_env <arg>
# Prints the normalized env ("stage" or "prod") to stdout on success.
# Returns 1 on anything else (missing, empty, wrong case, unknown value) —
# callers decide the exit code (both scripts use 2, a usage error).
validate_env() {
  local arg="${1:-}"
  case "$arg" in
    stage | prod)
      printf '%s\n' "$arg"
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

# resolve_context <env>
# Resolves the kubectl context name for the given env by filtering the real
# context list. Prints the resolved context name to stdout on success (exactly
# one match). On zero or multiple matches, prints a diagnostic to stderr and
# returns 1 — never guesses.
resolve_context() {
  local env="$1"
  local suffix=""
  case "$env" in
    prod) suffix="_prod" ;;
    stage) suffix="_staging" ;;
    *)
      echo "resolve_context: unknown env '${env}' (expected stage or prod)" >&2
      return 1
      ;;
  esac

  local all_contexts=""
  if ! all_contexts="$(kubectl config get-contexts -o name 2>&1)"; then
    echo "FAIL: could not list kubectl contexts (kubectl config get-contexts failed):" >&2
    echo "  ${all_contexts}" >&2
    return 1
  fi

  local matches=""
  matches="$(printf '%s\n' "$all_contexts" | grep -E "${suffix}\$" || true)"

  local match_count
  match_count="$(printf '%s\n' "$matches" | grep -c . || true)"

  if [[ -z "$matches" || "$match_count" -eq 0 ]]; then
    echo "FAIL: no kubectl context found ending in '${suffix}' for env '${env}'." >&2
    echo "  Run: gcloud container clusters get-credentials <cluster> --zone <zone> --project <project>" >&2
    echo "  Contexts currently available in your kubeconfig:" >&2
    printf '%s\n' "$all_contexts" | sed 's/^/    /' >&2
    return 1
  fi

  if [[ "$match_count" -gt 1 ]]; then
    echo "FAIL: ambiguous context resolution for env '${env}' — ${match_count} contexts end in '${suffix}':" >&2
    printf '%s\n' "$matches" | sed 's/^/    /' >&2
    echo "  Refusing to guess. Resolve manually (delete/rename the stale context) and rerun." >&2
    return 1
  fi

  printf '%s\n' "$matches"
  return 0
}
