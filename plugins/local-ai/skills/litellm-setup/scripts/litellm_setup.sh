#!/usr/bin/env bash

# Create a local LiteLLM configuration and optionally install an isolated copy.
# Usage: litellm_setup.sh [--check] [--apply] [--install] [--dir DIR]
#                          [--venv DIR] [--model MODEL]

set -uo pipefail

LITELLM_VERSION="1.101.0"
CONFIG_DIR="${HOME}/.config/local-ai/litellm"
VENV_DIR="${HOME}/.local/share/local-ai/litellm-${LITELLM_VERSION}"
MODEL="qwen3-coder:30b"
APPLY=0
INSTALL=0

usage() {
  printf '%s\n' \
    "Usage: litellm_setup.sh [--check] [--apply] [--install] [--dir DIR]" \
    "                         [--venv DIR] [--model MODEL]"
}

main() {
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --check) shift ;;
      --apply) APPLY=1; shift ;;
      --install) INSTALL=1; shift ;;
      --dir)
        [ "$#" -ge 2 ] && [ -n "${2:-}" ] \
          || { printf '%s\n' "--dir requires a path" >&2; exit 2; }
        CONFIG_DIR="$2"
        shift 2
        ;;
      --venv)
        [ "$#" -ge 2 ] && [ -n "${2:-}" ] \
          || { printf '%s\n' "--venv requires a path" >&2; exit 2; }
        VENV_DIR="$2"
        shift 2
        ;;
      --model)
        [ "$#" -ge 2 ] && [ -n "${2:-}" ] \
          || { printf '%s\n' "--model requires a model name" >&2; exit 2; }
        MODEL="$2"
        shift 2
        ;;
      -h|--help) usage; exit 0 ;;
      *) printf 'unknown argument: %s\n' "$1" >&2; exit 2 ;;
    esac
  done

  [ -n "$CONFIG_DIR" ] || { printf '%s\n' "--dir cannot be empty" >&2; exit 2; }
  [ -n "$VENV_DIR" ] || { printf '%s\n' "--venv cannot be empty" >&2; exit 2; }
  [ -n "$MODEL" ] || { printf '%s\n' "--model cannot be empty" >&2; exit 2; }
  [ "$INSTALL" = "0" ] || [ "$APPLY" = "1" ] \
    || { printf '%s\n' "--install requires --apply" >&2; exit 2; }

  local config="$CONFIG_DIR/config.yaml"
  printf '  pinned LiteLLM version: %s\n' "$LITELLM_VERSION"
  printf '  configuration: %s\n' "$config"
  printf '  isolated environment: %s\n' "$VENV_DIR"
  printf '  local route: %s -> http://127.0.0.1:11434/v1\n' "$MODEL"
  printf '  required environment: LOCAL_AI_PROXY_KEY, LITELLM_MASTER_KEY\n'

  if [ "$APPLY" = "0" ]; then
    [ -f "$config" ] \
      && printf '%s\n' "  status: configuration exists" \
      || printf '%s\n' "  status: configuration missing"
    [ -x "$VENV_DIR/bin/litellm" ] \
      && printf '%s\n' "  status: isolated LiteLLM exists" \
      || printf '%s\n' "  status: isolated LiteLLM missing"
    exit 0
  fi

  umask 077
  mkdir -p "$CONFIG_DIR"
  if [ -e "$config" ]; then
    printf '  %s already exists; leaving it unchanged\n' "$config"
  else
    {
      printf '%s\n' "# Local AI starter route. Values remain in environment variables."
      printf '%s\n' "model_list:"
      printf '%s\n' "  - model_name: local-pair"
      printf '%s\n' "    litellm_params:"
      printf '      model: openai/%s\n' "$MODEL"
      printf '%s\n' "      api_base: http://127.0.0.1:11434/v1"
      printf '%s\n' "      api_key: os.environ/LOCAL_AI_PROXY_KEY"
      printf '%s\n' "general_settings:"
      printf '%s\n' "  master_key: os.environ/LITELLM_MASTER_KEY"
      printf '%s\n' "litellm_settings:"
      printf '%s\n' "  drop_params: true"
    } > "$config"
    chmod 600 "$config"
    printf '  wrote %s\n' "$config"
  fi

  if [ "$INSTALL" = "1" ]; then
    command -v python3 >/dev/null 2>&1 \
      || { printf '%s\n' "FAIL: python3 not found" >&2; exit 1; }
    python3 -c 'import sys; sys.exit(0 if (3, 10) <= sys.version_info < (3, 15) else 1)' \
      || { printf '%s\n' "FAIL: LiteLLM requires Python 3.10 through 3.14" >&2; exit 1; }
    if [ ! -x "$VENV_DIR/bin/python" ]; then
      mkdir -p "$(dirname "$VENV_DIR")"
      python3 -m venv "$VENV_DIR" \
        || { printf '%s\n' "FAIL: could not create virtual environment" >&2; exit 1; }
    fi
    "$VENV_DIR/bin/python" -m pip install --quiet \
      "litellm[proxy]==${LITELLM_VERSION}" \
      || { printf '%s\n' "FAIL: LiteLLM installation failed" >&2; exit 1; }
    printf '  installed LiteLLM %s in %s\n' "$LITELLM_VERSION" "$VENV_DIR"
  fi

  printf '%s\n' "  next: set both environment variables and bind LiteLLM to 127.0.0.1"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  main "$@"
fi
