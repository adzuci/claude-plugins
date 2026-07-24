#!/usr/bin/env bash
set -euo pipefail

readonly IMAGE="ghcr.io/tombii/better-ccflare:3.5.42"
readonly CONTAINER_NAME="better-ccflare"
readonly VOLUME_NAME="better-ccflare-data"
readonly BASE_URL="http://localhost:8080"
readonly ZSHRC_LINE="export ANTHROPIC_BASE_URL=${BASE_URL}"

usage() {
  cat <<'EOF'
Usage: setup_ccflare.sh [--check]

Install the public tombii/better-ccflare Docker image on macOS. --check performs
only read-only prerequisite, shell-route, and container checks.

Environment:
  CCFLARE_SKIP_OPEN Set to 1 to avoid opening the dashboard.
EOF
}

fail() {
  printf 'setup-ccflare: %s\n' "$*" >&2
  exit 1
}

mode="install"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check)
      mode="check"
      shift
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

[[ "$(uname -s)" == "Darwin" ]] || fail "this setup flow currently supports macOS only"
command -v docker >/dev/null 2>&1 || fail "Docker is required"
docker info >/dev/null 2>&1 || fail "the Docker daemon is not running; start Docker Desktop or Colima"

zshrc="${HOME}/.zshrc"
if [[ -f "$zshrc" ]]; then
  matching_count="$(grep -Fxc "$ZSHRC_LINE" "$zshrc" || true)"
  conflicting_count="$(grep -Ec '^[[:space:]]*export[[:space:]]+ANTHROPIC_BASE_URL=' "$zshrc" || true)"
else
  matching_count=0
  conflicting_count=0
fi

if [[ "$conflicting_count" != "0" ]] &&
   ! [[ "$matching_count" == "1" && "$conflicting_count" == "1" ]]; then
  fail "$zshrc already configures ANTHROPIC_BASE_URL; reconcile it manually before rerunning"
fi

container_exists=0
if docker container inspect "$CONTAINER_NAME" >/dev/null 2>&1; then
  container_exists=1
  configured_image="$(docker container inspect --format '{{.Config.Image}}' "$CONTAINER_NAME")"
  [[ "$configured_image" == "$IMAGE" ]] ||
    fail "container $CONTAINER_NAME uses $configured_image, not pinned image $IMAGE"
  configured_host_ip="$(docker container inspect --format '{{(index (index .HostConfig.PortBindings "8080/tcp") 0).HostIp}}' "$CONTAINER_NAME" 2>/dev/null || true)"
  configured_host_port="$(docker container inspect --format '{{(index (index .HostConfig.PortBindings "8080/tcp") 0).HostPort}}' "$CONTAINER_NAME" 2>/dev/null || true)"
  [[ "$configured_host_ip" == "127.0.0.1" && "$configured_host_port" == "8080" ]] ||
    fail "container $CONTAINER_NAME is not bound only to 127.0.0.1:8080"
  configured_env="$(docker container inspect --format '{{range .Config.Env}}{{println .}}{{end}}' "$CONTAINER_NAME")"
  printf '%s\n' "$configured_env" | grep -Fxq "STORE_PAYLOADS=false" ||
    fail "container $CONTAINER_NAME does not disable request/response body storage"
  configured_volume="$(docker container inspect --format '{{range .Mounts}}{{if eq .Destination "/data"}}{{.Name}}{{end}}{{end}}' "$CONTAINER_NAME")"
  [[ "$configured_volume" == "$VOLUME_NAME" ]] ||
    fail "container $CONTAINER_NAME does not use the expected $VOLUME_NAME volume"
fi

if [[ "$mode" == "check" ]]; then
  printf 'macOS: ok\n'
  printf 'Docker: ok\n'
  printf 'image: %s (public; would pull during install)\n' "$IMAGE"
  if [[ "$container_exists" == "1" ]]; then
    printf 'container: existing canonical %s\n' "$CONTAINER_NAME"
  else
    printf 'container: absent (would create %s)\n' "$CONTAINER_NAME"
  fi
  if [[ "$matching_count" == "1" ]]; then
    printf 'ANTHROPIC_BASE_URL: already configured in %s\n' "$zshrc"
  else
    printf 'ANTHROPIC_BASE_URL: would add to %s\n' "$zshrc"
  fi
  exit 0
fi

if [[ "$container_exists" == "0" ]]; then
  docker pull "$IMAGE"
  docker volume inspect "$VOLUME_NAME" >/dev/null 2>&1 ||
    docker volume create "$VOLUME_NAME" >/dev/null
  docker run -d \
    --name "$CONTAINER_NAME" \
    --restart unless-stopped \
    -p 127.0.0.1:8080:8080 \
    -e BETTER_CCFLARE_HOST=0.0.0.0 \
    -e BETTER_CCFLARE_DB_PATH=/data/better-ccflare.db \
    -e XDG_CONFIG_HOME=/data \
    -e STORE_PAYLOADS=false \
    -v "${VOLUME_NAME}:/data" \
    "$IMAGE" >/dev/null
else
  docker start "$CONTAINER_NAME" >/dev/null
  printf 'container: reused %s\n' "$CONTAINER_NAME"
fi

if [[ "$matching_count" == "1" ]]; then
  printf 'ANTHROPIC_BASE_URL: already configured in %s\n' "$zshrc"
else
  touch "$zshrc"
  {
    printf '\n# Added by setup-ccflare\n'
    printf '%s\n' "$ZSHRC_LINE"
  } >> "$zshrc"
  printf 'ANTHROPIC_BASE_URL: added to %s\n' "$zshrc"
fi

for _attempt in $(seq 1 30); do
  if curl --fail --silent "${BASE_URL}/health" >/dev/null; then
    break
  fi
  sleep 1
done
curl --fail --silent --show-error "${BASE_URL}/health" >/dev/null ||
  fail "better-ccflare health check failed at ${BASE_URL}/health"

printf 'ccflare dashboard: %s/dashboard\n' "$BASE_URL"
printf '%s\n' \
  "Next: configure your provider account in the dashboard before starting a fresh Claude Code session." \
  "Test status: /setup-ccflare has not yet been tested end to end from this repository location."
if [[ "${CCFLARE_SKIP_OPEN:-0}" != "1" ]]; then
  open "${BASE_URL}/dashboard"
fi
