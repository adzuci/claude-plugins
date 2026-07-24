#!/usr/bin/env bash
set -euo pipefail

readonly REPO_SLUG="apolloio/ccflare-relay"
readonly REPO_SSH_URL="git@github.com:${REPO_SLUG}.git"
readonly DEFAULT_REPO_DIR="${HOME}/.local/share/ccflare-relay"
readonly BASE_URL="http://localhost:8080"
readonly ZSHRC_LINE="export ANTHROPIC_BASE_URL=${BASE_URL}"

usage() {
  cat <<'EOF'
Usage: setup_ccflare.sh [--check] [--repo-dir PATH]

Install the private apolloio/ccflare-relay MVP on macOS. --check performs only
read-only prerequisite and repository-access checks.

Environment:
  CCFLARE_REPO_DIR  Override the default checkout path.
  CCFLARE_SKIP_OPEN Set to 1 to avoid opening the dashboard.
EOF
}

fail() {
  printf 'setup-ccflare: %s\n' "$*" >&2
  exit 1
}

mode="install"
repo_dir="${CCFLARE_REPO_DIR:-}"
repo_dir_explicit=0
[[ -n "$repo_dir" ]] && repo_dir_explicit=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check)
      mode="check"
      shift
      ;;
    --repo-dir)
      [[ $# -ge 2 ]] || fail "--repo-dir requires a path"
      repo_dir="$2"
      repo_dir_explicit=1
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "unknown argument: $1"
      ;;
  esac
done

if [[ "$repo_dir_explicit" == "0" ]]; then
  if [[ -d "$PWD/.git" ]] &&
     [[ -f "$PWD/docker-compose.build.yml" ]] &&
     [[ -f "$PWD/scripts/install-ccflare.sh" ]]; then
    repo_dir="$PWD"
  else
    repo_dir="$DEFAULT_REPO_DIR"
  fi
fi

[[ "$repo_dir" = /* ]] || fail "repository path must be absolute: $repo_dir"
[[ "$(uname -s)" == "Darwin" ]] || fail "this setup flow currently supports macOS only"
command -v git >/dev/null 2>&1 || fail "git is required"
command -v docker >/dev/null 2>&1 || fail "Docker is required"
docker compose version >/dev/null 2>&1 || fail "Docker Compose v2 is required"
docker info >/dev/null 2>&1 || fail "the Docker daemon is not running; start Docker Desktop or Colima"

validate_checkout() {
  local origin
  [[ -d "$repo_dir/.git" ]] || fail "$repo_dir exists but is not a git checkout"
  origin="$(git -C "$repo_dir" remote get-url origin 2>/dev/null || true)"
  case "$origin" in
    git@github.com:apolloio/ccflare-relay.git|https://github.com/apolloio/ccflare-relay.git|https://github.com/apolloio/ccflare-relay)
      ;;
    *)
      fail "$repo_dir is not an apolloio/ccflare-relay checkout (origin: ${origin:-missing})"
      ;;
  esac
}

can_access_repo() {
  if command -v gh >/dev/null 2>&1 &&
     gh auth status --hostname github.com >/dev/null 2>&1 &&
     gh repo view "$REPO_SLUG" --json nameWithOwner >/dev/null 2>&1; then
    return 0
  fi
  GIT_TERMINAL_PROMPT=0 git ls-remote "$REPO_SSH_URL" HEAD >/dev/null 2>&1
}

clone_repo() {
  if command -v gh >/dev/null 2>&1 &&
     gh auth status --hostname github.com >/dev/null 2>&1 &&
     gh repo view "$REPO_SLUG" --json nameWithOwner >/dev/null 2>&1; then
    gh repo clone "$REPO_SLUG" "$repo_dir" -- --recurse-submodules
  else
    git clone --recurse-submodules "$REPO_SSH_URL" "$repo_dir"
  fi
}

if [[ -e "$repo_dir" ]]; then
  validate_checkout
fi

if [[ "$mode" == "check" ]]; then
  printf 'macOS: ok\n'
  printf 'git: %s\n' "$(command -v git)"
  printf 'Docker: ok\n'
  printf 'Docker Compose v2: ok\n'
  if [[ -d "$repo_dir/.git" ]]; then
    printf 'checkout: %s\n' "$repo_dir"
    printf 'repository access: using existing canonical checkout\n'
  else
    printf 'checkout: not present (would clone to %s)\n' "$repo_dir"
    can_access_repo || fail "cannot access private repository $REPO_SLUG; authenticate with gh or GitHub SSH first"
    printf 'repository access: ok\n'
  fi
  exit 0
fi

if [[ ! -e "$repo_dir" ]]; then
  can_access_repo || fail "cannot access private repository $REPO_SLUG; authenticate with gh or GitHub SSH first"
  mkdir -p "$(dirname "$repo_dir")"
  clone_repo
fi

validate_checkout
git -C "$repo_dir" submodule update --init --recursive

readonly upstream_compose="$repo_dir/better-ccflare/docker-compose.yml"
readonly relay_compose="$repo_dir/docker-compose.build.yml"
[[ -f "$upstream_compose" ]] || fail "missing upstream Compose file: $upstream_compose"
[[ -f "$relay_compose" ]] || fail "missing relay Compose file: $relay_compose"
if [[ -f "$repo_dir/.env" ]]; then
  configured_port="$(grep -E '^[[:space:]]*CCFLARE_GUARD_HOST_PORT=' "$repo_dir/.env" | tail -1 | cut -d= -f2- | tr -d '[:space:]' || true)"
  [[ -z "$configured_port" || "$configured_port" == "8080" ]] ||
    fail "$repo_dir/.env configures Guard on port $configured_port; this MVP expects port 8080"
fi

compose() {
  docker compose \
    -f "$upstream_compose" \
    -f "$relay_compose" \
    --project-directory "$repo_dir" \
    "$@"
}

docker volume inspect better-ccflare-data >/dev/null 2>&1 ||
  docker volume create better-ccflare-data >/dev/null
compose up -d --build

account_list="$(compose exec -T better-ccflare better-ccflare --list 2>/dev/null || true)"
if ! printf '%s' "$account_list" | grep -Fq "guard-replay"; then
  [[ -t 0 && -t 1 ]] ||
    fail "replay-account setup needs a TTY; rerun this command interactively"
  printf '%s\n' \
    "Add the local replay account when prompted:" \
    "  API key: any local-only value of at least 10 characters" \
    "  Endpoint: http://guard:8081" \
    "  Mappings: 1 (defaults)"
  compose exec -it better-ccflare better-ccflare \
    --add-account guard-replay \
    --mode anthropic-compatible \
    --priority 0
else
  printf 'guard-replay account: already configured\n'
fi

zshrc="${HOME}/.zshrc"
if [[ -f "$zshrc" ]]; then
  matching_count="$(grep -Fxc "$ZSHRC_LINE" "$zshrc" || true)"
  conflicting_count="$(grep -Ec '^[[:space:]]*export[[:space:]]+ANTHROPIC_BASE_URL=' "$zshrc" || true)"
else
  matching_count=0
  conflicting_count=0
fi

if [[ "$matching_count" == "1" && "$conflicting_count" == "1" ]]; then
  printf 'ANTHROPIC_BASE_URL: already configured in %s\n' "$zshrc"
elif [[ "$conflicting_count" != "0" ]]; then
  fail "$zshrc already configures ANTHROPIC_BASE_URL; reconcile it manually before rerunning"
else
  touch "$zshrc"
  {
    printf '\n# Added by setup-ccflare\n'
    printf '%s\n' "$ZSHRC_LINE"
  } >> "$zshrc"
  printf 'ANTHROPIC_BASE_URL: added to %s\n' "$zshrc"
fi

for _attempt in $(seq 1 30); do
  if curl --fail --silent "${BASE_URL}/_guard/health" >/dev/null &&
     curl --fail --silent "${BASE_URL}/health" >/dev/null; then
    break
  fi
  sleep 1
done
curl --fail --silent --show-error "${BASE_URL}/_guard/health" >/dev/null ||
  fail "Guard health check failed at ${BASE_URL}/_guard/health"
curl --fail --silent --show-error "${BASE_URL}/health" >/dev/null ||
  fail "better-ccflare health check failed at ${BASE_URL}/health"

printf 'ccflare dashboard: %s/dashboard\n' "$BASE_URL"
if [[ "${CCFLARE_SKIP_OPEN:-0}" != "1" ]]; then
  open "${BASE_URL}/dashboard"
fi
