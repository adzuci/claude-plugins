#!/usr/bin/env bash
# Shares the initiative record with the team (doc 41 §3). No-op when the harness profile is not
# `collaboration: team`, so every harness skill can call it unconditionally.
# Runs only when a harness skill calls it at a stage boundary. No hook calls it.
# A pull never replaces locally edited records: it refuses while .ai/<initiative>/ has local changes.
#
#   record-sync.sh pull <initiative>            before reading any snapshot, ledger or decision record
#   record-sync.sh push <initiative> "<message>" after writing one
#
# Exit codes: 0 synced or solo; 2 push/pull failed (the stage is not done; report it, never --force).
set -u
mode="${1:-}"; initiative="${2:-}"; message="${3:-}"
[ -n "$mode" ] && [ -n "$initiative" ] || { echo "usage: record-sync.sh pull|push <initiative> [message]" >&2; exit 1; }
root="${HARNESS_REPO_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$root" || exit 1
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "[record-sync] no-repo mode: $root is not a git repo; nothing to sync"; exit 0
fi
if [ ! -d .ai ]; then
  echo "[record-sync] harness not initialised in $root (no .ai/ at the repo root); nothing to sync"; exit 0
fi
profile=""
# HARNESS_PROFILE: a profile fetched from Notion into a temp file (cloud session with storage: local, doc 45 §4).
for p in "${HARNESS_PROFILE:-}" ".ai/harness-profile.yml" ".ai/$initiative/harness-profile.yml" "$HOME/.claude/harness-profile.yml"; do
  [ -n "$p" ] && [ -f "$p" ] && { profile="$p"; break; }
done
[ -z "$profile" ] || python3 "$script_dir/storage.py" validate-profile "$profile" >/dev/null || exit 2
tracker=$([ -n "$profile" ] && awk '
  /^updates:[[:space:]]*$/ { in_updates=1; next }
  in_updates && /^[^[:space:]]/ { in_updates=0 }
  in_updates && /^[[:space:]]+tracker:/ { sub(/^[[:space:]]*tracker:[[:space:]]*/, ""); sub(/[[:space:]]*#.*/, ""); print; exit }
' "$profile")
persona=$([ -n "$profile" ] && awk -F': ' '/^persona:/{print $2}' "$profile" | head -1 | awk '{print $1}')
snapshot_root=".ai/$initiative/runs"
current_snapshots() {
  python3 - "$1" <<'PY'
import os, re, sys
latest = {}
for parent, _, names in os.walk(sys.argv[1]):
    for name in names:
        match = re.fullmatch(r"(.+\.snapshot)(?:\.([0-9]+))?\.md", name)
        if not match:
            continue
        key = os.path.join(parent, match.group(1))
        candidate = (int(match.group(2) or 1), os.path.join(parent, name))
        if key not in latest or candidate[0] > latest[key][0]:
            latest[key] = candidate
for _, path in sorted(latest.values(), key=lambda item: item[1]):
    print(path)
PY
}
if [ "$mode" = "push" ]; then
  if [ "$tracker" = "jira" ] || [ "$tracker" = "both" ]; then
    bad_jira=""
    while IFS= read -r snapshot; do
      grep -Eq '^jira: ([A-Z][A-Z0-9_]*-[0-9]+|blocked:.+)$' "$snapshot" || bad_jira="${bad_jira}${snapshot}\n"
    done < <(current_snapshots "$snapshot_root")
    if [ -n "$bad_jira" ]; then
      echo "[record-sync] refusing to push: Jira or both profiles require every stage snapshot to have jira: <KEY-123> or jira: blocked:<reason>:" >&2
      printf '%b' "$bad_jira" | sed 's/^/[record-sync]   /' >&2
      exit 2
    fi
  fi
  while IFS= read -r context; do
    if grep -Eq '^stage:[[:space:]]*A\.context([[:space:]]|$)' "$context"; then
      context_persona=$(awk -F': ' '/^persona:/{print $2; exit}' "$context" | awk '{print $1}')
      python3 "$script_dir/grill-check.py" "$context" --persona "${context_persona:-$persona}" || exit 2
    fi
  done < <(current_snapshots "$snapshot_root")
fi
collab=$([ -n "$profile" ] && awk -F': ' '/^collaboration:/{print $2}' "$profile" | head -1 | awk '{print $1}')
if [ "$collab" != "team" ]; then echo "[record-sync] solo profile; nothing to sync"; exit 0; fi
branch=$(git branch --show-current)
case "$branch" in ""|master|main) echo "[record-sync] refusing to sync .ai/ on '$branch'; use the feature branch or <ticket>/harness-artifacts (doc 41 §3.5)" >&2; exit 2;; esac
if [ -z "$(git ls-files ".ai/$initiative" | head -1)" ] || git check-ignore -q ".ai/$initiative"; then
  echo "[record-sync] nothing under .ai/$initiative is tracked (or it is ignored); commit it once by hand on the feature branch before team sync" >&2; exit 2
fi
case "$mode" in
  pull)
    if [ -n "$(git status --porcelain -- ".ai/$initiative")" ]; then
      echo "[record-sync] refusing to pull: .ai/$initiative has local changes that a pull could replace. Push them first (record-sync.sh push $initiative), or keep working on the local copy." >&2
      git status --short -- ".ai/$initiative" | head -10 | sed 's/^/[record-sync]   /' >&2
      exit 2
    fi
    git pull --rebase --autostash -q 2>&1 | sed 's/^/[record-sync] /'
    rc=${PIPESTATUS[0]}
    if [ "$rc" -ne 0 ]; then
      if git diff --name-only --diff-filter=U | grep -q "\.ai/$initiative/ledger.jsonl"; then
        echo "[record-sync] ledger conflict: keep both sides in timestamp order (doc 41 §3.3), then git rebase --continue" >&2
      fi
      exit 2
    fi
    echo "[record-sync] pulled; newest record on disk is the record"
    ;;
  push)
    [ -n "$message" ] || message="$initiative: harness record"
    stray=$(git diff --cached --name-only -- . ":(exclude).ai/$initiative")
    if [ -n "$stray" ]; then
      echo "[record-sync] refusing to push: files outside .ai/$initiative are staged and would ride along in the record commit. Unstage them (git restore --staged <file>) and push again:" >&2
      echo "$stray" | head -10 | sed 's/^/[record-sync]   /' >&2
      exit 2
    fi
    missing=$(grep -L -E '^notion: (https://|blocked:)' $(ls .ai/$initiative/runs/*/*.snapshot.md .ai/$initiative/runs/*/council.*.memo.md .ai/$initiative/runs/*/council.*.decision.md 2>/dev/null) 2>/dev/null || true)
    if [ -n "$missing" ]; then echo "[record-sync] WARNING: human-facing records without a Notion page (doc 33; publish before the stage is called done):" >&2; echo "$missing" | sed 's/^/[record-sync]   /' >&2; fi
    git add ".ai/$initiative"
    if ! git diff --cached --quiet; then
      git commit -q -m "$message" || exit 2
    fi
    git pull --rebase --autostash -q 2>&1 | sed 's/^/[record-sync] /'
    if [ "${PIPESTATUS[0]}" -ne 0 ]; then echo "[record-sync] rebase failed; resolve then run record-sync.sh push again" >&2; exit 2; fi
    git push -q 2>&1 | sed 's/^/[record-sync] /'
    if [ "${PIPESTATUS[0]}" -ne 0 ]; then echo "[record-sync] push failed; the stage is not done until the record is shared" >&2; exit 2; fi
    echo "[record-sync] pushed $(git rev-parse --short HEAD) on $branch"
    ;;
  *) echo "usage: record-sync.sh pull|push <initiative> [message]" >&2; exit 1;;
esac
