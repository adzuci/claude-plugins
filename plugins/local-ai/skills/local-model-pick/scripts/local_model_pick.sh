#!/usr/bin/env bash

# Recommend an Ollama model from total and currently available memory.
# Usage: local_model_pick.sh [--pull]

set -uo pipefail

usage() { printf '%s\n' "Usage: local_model_pick.sh [--pull]"; }

model_for_ram() {
  local total_gb="${1:-0}"
  if [ "$total_gb" -ge 64 ]; then
    echo "qwen3-coder:30b"
  elif [ "$total_gb" -ge 48 ]; then
    echo "gpt-oss:20b"
  elif [ "$total_gb" -ge 32 ]; then
    echo "qwen3:14b"
  else
    echo "qwen3:8b"
  fi
}

model_size_gb() {
  case "${1:-}" in
    qwen3-coder:30b) echo "19" ;;
    gpt-oss:20b) echo "14" ;;
    qwen3:14b) echo "9.3" ;;
    qwen3:8b) echo "5.2" ;;
    *) echo "0" ;;
  esac
}

model_headroom_gb() {
  case "${1:-}" in
    qwen3-coder:30b) echo "24" ;;
    gpt-oss:20b) echo "18" ;;
    qwen3:14b) echo "12" ;;
    qwen3:8b) echo "8" ;;
    *) echo "0" ;;
  esac
}

main() {
  local pull=0
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --pull) pull=1; shift ;;
      -h|--help) usage; exit 0 ;;
      *) printf 'unknown argument: %s\n' "$1" >&2; exit 2 ;;
    esac
  done

  [ "$(uname -s)" = "Darwin" ] \
    || { printf '%s\n' "local-model-pick currently supports macOS only" >&2; exit 2; }
  [ "$(uname -m)" = "arm64" ] \
    || { printf '%s\n' "local-model-pick currently targets Apple Silicon" >&2; exit 2; }

  local total model size need available
  total=$(( $(sysctl -n hw.memsize) / 1073741824 ))
  model="$(model_for_ram "$total")"
  size="$(model_size_gb "$model")"
  need="$(model_headroom_gb "$model")"
  available="$(vm_stat | awk '
/Pages free/ {free_pages=$3}
/Pages inactive/ {inactive_pages=$3}
END {
  gsub(/\./, "", free_pages)
  gsub(/\./, "", inactive_pages)
  printf "%d", (free_pages + inactive_pages) * 16384 / 1073741824
}')"

  printf '  total memory:      %s GB\n' "$total"
  printf '  available now:     %s GB\n' "$available"
  printf '  recommended model: %s\n' "$model"
  printf '  download size:     %s GB\n' "$size"
  printf '  target headroom:   %s GB\n' "$need"
  printf '%s\n' "  NOTE: download size is not peak resident memory."
  [ "$available" -lt "$need" ] \
    && printf '%s\n' "  WARN: current available memory is below the target headroom."

  if [ "$pull" = "1" ]; then
    command -v ollama >/dev/null 2>&1 \
      || { printf '%s\n' "FAIL: ollama is not installed" >&2; exit 1; }
    printf '  pulling %s ...\n' "$model"
    ollama pull "$model"
  else
    printf '  after confirmation: ollama pull %s\n' "$model"
  fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  main "$@"
fi
