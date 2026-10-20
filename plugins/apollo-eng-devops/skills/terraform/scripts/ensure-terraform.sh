#!/usr/bin/env bash
# Ensure the terraform CLI is on PATH. Install order: tfenv, Homebrew, HashiCorp binary.
# Usage: ensure-terraform.sh [--dry-run] [--version X.Y.Z]
set -euo pipefail

DRY_RUN=0
VERSION=""
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --version) VERSION="${2:?--version needs a value}"; shift ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
  shift
done

if command -v terraform >/dev/null 2>&1; then
  echo "terraform already installed: $(terraform version | head -1)"
  exit 0
fi

run() {
  if [ "$DRY_RUN" = 1 ]; then echo "[dry-run] $*"; else "$@"; fi
}

if command -v tfenv >/dev/null 2>&1; then
  run tfenv install "${VERSION:-latest}"
  run tfenv use "${VERSION:-latest}"
elif command -v brew >/dev/null 2>&1; then
  run brew tap hashicorp/tap
  run brew install hashicorp/tap/terraform
else
  os="$(uname -s | tr '[:upper:]' '[:lower:]')"
  case "$(uname -m)" in
    x86_64|amd64) arch=amd64 ;;
    arm64|aarch64) arch=arm64 ;;
    *) echo "unsupported arch: $(uname -m)" >&2; exit 1 ;;
  esac
  if [ -z "$VERSION" ] && [ "$DRY_RUN" = 0 ]; then
    VERSION="$(curl -fsS https://checkpoint-api.hashicorp.com/v1/check/terraform | python3 -c 'import json,sys; print(json.load(sys.stdin)["current_version"])')"
  fi
  VERSION="${VERSION:-latest}"
  base="https://releases.hashicorp.com/terraform/${VERSION}"
  zip="terraform_${VERSION}_${os}_${arch}.zip"
  dest="${HOME}/.local/bin"
  if [ "$DRY_RUN" = 1 ]; then
    echo "[dry-run] download ${base}/${zip}, verify against ${base}/terraform_${VERSION}_SHA256SUMS, unzip to ${dest}"
    exit 0
  fi
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  curl -fsSL -o "$tmp/$zip" "${base}/${zip}"
  curl -fsSL -o "$tmp/SHA256SUMS" "${base}/terraform_${VERSION}_SHA256SUMS"
  (cd "$tmp" && grep " ${zip}\$" SHA256SUMS | shasum -a 256 -c -)
  mkdir -p "$dest"
  unzip -o -q "$tmp/$zip" terraform -d "$dest"
  case ":$PATH:" in *":$dest:"*) ;; *) echo "add $dest to PATH" ;; esac
fi

[ "$DRY_RUN" = 1 ] && exit 0
terraform version | head -1
