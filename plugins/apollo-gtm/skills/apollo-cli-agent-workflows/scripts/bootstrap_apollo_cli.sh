#!/usr/bin/env bash
set -euo pipefail

echo "== Apollo CLI bootstrap =="

install_with_homebrew() {
  echo "STATUS: INSTALLING_WITH_HOMEBREW"
  brew install apolloio/apollo-io-cli/apollo-io-cli
}

install_with_binary() {
  local os arch asset install_dir tmp_file
  os="$(uname -s)"
  arch="$(uname -m)"
  install_dir="${APOLLO_CLI_INSTALL_DIR:-$HOME/.local/bin}"

  case "$os:$arch" in
    Darwin:arm64) asset="apollo-macos-arm64" ;;
    Darwin:x86_64) asset="apollo-macos-x64" ;;
    Linux:x86_64) asset="apollo-linux-x64" ;;
    *)
      echo "STATUS: UNSUPPORTED_BINARY_PLATFORM"
      echo "Use the official Apollo CLI releases page for this platform."
      exit 1
      ;;
  esac

  mkdir -p "$install_dir"
  tmp_file="$(mktemp)"
  echo "STATUS: INSTALLING_BINARY"
  curl -L -o "$tmp_file" "https://github.com/apolloio/apollo-io-cli/releases/latest/download/$asset"
  chmod +x "$tmp_file"
  mv "$tmp_file" "$install_dir/apollo"
  if [[ "$os" == "Darwin" ]]; then
    xattr -d com.apple.quarantine "$install_dir/apollo" 2>/dev/null || true
  fi
  export PATH="$install_dir:$PATH"

  if ! command -v apollo >/dev/null 2>&1; then
    echo "STATUS: PATH_UPDATE_REQUIRED"
    echo "Add $install_dir to PATH, then open a fresh terminal."
    exit 1
  fi
}

if command -v apollo >/dev/null 2>&1; then
  echo "STATUS: FOUND"
else
  echo "STATUS: MISSING"
  if command -v brew >/dev/null 2>&1; then
    install_with_homebrew
  else
    install_with_binary
  fi
fi

echo "VERSION: $(apollo --version 2>/dev/null || echo UNKNOWN)"

echo
echo "== Auth =="
if apollo auth whoami >/dev/null 2>&1; then
  echo "PASS: auth whoami"
else
  echo "STATUS: AUTH_REQUIRED"
  apollo auth login
  apollo auth whoami
  echo "PASS: auth whoami"
fi

echo
echo "RESULT: READY_FOR_READ_ONLY_TEST"
