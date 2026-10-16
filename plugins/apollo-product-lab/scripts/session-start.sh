#!/usr/bin/env bash
# Prints harness state at session start. State only: it never asks the model to do work.
# Bounded local reads only: no git pull, and no network call except a 1-second local shunt probe
# for personas that write code. Never fails the session; never reads secrets.
PROFILE="$HOME/.claude/harness-profile.yml"
ROOT="${CLAUDE_PLUGIN_ROOT:-${CLAUDE_PLUGIN_DIR:-$(cd "$(dirname "$0")/.." 2>/dev/null && pwd)}}"
version=$(sed -n 's/.*"version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$ROOT/.claude-plugin/plugin.json" 2>/dev/null | head -1)
# Build revision: the plugin checkout's short sha, else the BUILD file the zip build writes.
build=""
if command -v git >/dev/null && git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  build=$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null)
elif [ -f "$ROOT/BUILD" ]; then
  build=$(head -c 40 "$ROOT/BUILD" | tr -d '\n')
fi
tag="[apollo-product-lab ${version:-version unknown}${build:+ build $build}]"
# SessionStart fires after startup, resume, clear and compaction; the hook input names which.
SOURCE=""
if [ ! -t 0 ]; then SOURCE=$(python3 -c "import json,sys;print(json.load(sys.stdin).get('source',''))" 2>/dev/null || true); fi
if [ ! -f "$PROFILE" ]; then
  case "${CLAUDE_CODE_REMOTE:-}" in
    true|1) echo "$tag Cloud session: storage: notion. Your harness profile lives on your private Notion page \"Harness profile\" (doc 45); the harness skills read it from there. No page yet: /apollo-product-lab:harness-onboard creates it.";;
    *) echo "$tag No harness profile yet. /apollo-product-lab:harness-onboard sets one up (about ten minutes).";;
  esac
  exit 0
fi
if ! profile_check=$(python3 "$ROOT/scripts/storage.py" validate-profile "$PROFILE" 2>&1); then
  echo "$tag ERROR: $profile_check"
  exit 0
fi
field() { awk -F': ' -v k="$1" '$1==k{print $2; exit}' "$PROFILE" | awk '{print $1}'; }
persona=$(field persona)
run=$(field default_run)
collab=$(field collaboration)
base=$(field base_model)
second=$(awk -F': ' '$1=="second_family"{print $2; exit}' "$PROFILE")
storage=$(field storage)
msg="$tag profile: ${persona:-?} · default run: ${run:-none}"
[ -n "$storage" ] && msg="$msg · storage: $storage"
[ -n "$base" ] && msg="$msg · base model: $base"
# Three states, resolved from the repo root (not the current subfolder):
#   none = not a git repo (no-repo mode); bare = git repo with no .ai/ at its root; harness = .ai/ at the root.
top=""
command -v git >/dev/null && top=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$top" ]; then repo_state=none
elif [ -d "$top/.ai" ]; then repo_state=harness
else repo_state=bare; fi
case "$persona" in
  designer|ux*|researcher)
    # Design work needs no second family. Probe only if the person said they also write code.
    case "$second" in installed*) probe=yes;; *) probe=no;; esac;;
  *) probe=yes;;
esac
if [ "$probe" = yes ]; then
  case "$second" in
    declined*) msg="$msg · second family: declined at onboarding (council memos are tagged same-family)";;
    n/a-cloud*) msg="$msg · second family: not available on a cloud host";;
    *)
      if command -v curl >/dev/null && curl -s --max-time 1 -o /dev/null -w '%{http_code}' http://127.0.0.1:3001/ 2>/dev/null | grep -q '^200$'; then
        routed="${ANTHROPIC_BASE_URL:-}"
        [ -z "$routed" ] && routed=$(sed -n 's/.*"ANTHROPIC_BASE_URL"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$HOME/.claude/settings.json" 2>/dev/null | head -1)
        if [ -n "$routed" ]; then msg="$msg · second family: routed through shunt"
        else msg="$msg · second family: shunt running, this session not routed"; fi
      else
        msg="$msg · second family: shunt not running (council memos will be tagged same-family)"
      fi;;
  esac
fi
case "$repo_state" in
  none) msg="$msg · no-repo mode: this folder is not in a git repo, so repo, git, gh and .ai steps are skipped";;
  bare) msg="$msg · harness not initialised in this repo (no .ai/ at its root); intake can bootstrap one";;
  harness)
    [ "$collab" = "team" ] && msg="$msg · team mode: the record syncs only when a harness skill runs record-sync.sh"
    inits=$(cd "$top" && ls -d .ai/*/harness-manifest.md 2>/dev/null | awk -F/ '{print $2}' | tr '\n' ' ')
    [ -n "$inits" ] && msg="$msg · initiatives here: $inits";;
esac
# After compaction, print the bound run's record pointers, but only when that run lives under this
# repo's .ai/. Header plus at most 15 lines.
if [ "$SOURCE" = "compact" ] && [ "$repo_state" = harness ] && [ -n "$run" ]; then
  cd "$top" || exit 0
  idx=$(ls -d .ai/*/runs/"$run"/index.md 2>/dev/null | head -1)
  if [ -n "$idx" ]; then
    rundir=$(dirname "$idx")
    echo "$tag Context was compacted. Run $run is bound to this repo; the record on disk is authoritative (doc 37 §3b)."
    {
      echo "record: $rundir/"
      latest=$(ls -t "$rundir"/*.snapshot.md 2>/dev/null | head -1)
      if [ -n "$latest" ]; then
        echo "newest snapshot: $latest"
        grep -m1 '^stage:' "$latest"
        grep -m1 '^human_gate:' "$latest"
        grep -m1 '^gate_status:' "$latest"
        grep -m1 '^notion:' "$latest"
        awk '/^## /{keep = ($0 ~ /[Gg]ate|Checks/)} keep && /^\|/ && !/^\|[-| ]*\|$/' "$latest" | head -8
      else
        echo "newest snapshot: none yet"
      fi
    } | head -15
    exit 0
  fi
fi
echo "$msg"
exit 0
