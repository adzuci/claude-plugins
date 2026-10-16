#!/usr/bin/env bash
# Generate AGENTS.harness.md (Codex view) from the canonical Claude agent files.
# Usage: ${CLAUDE_PLUGIN_ROOT}/framework/scripts/gen-codex-agents.sh [out-file]
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
out="${1:-AGENTS.harness.md}"
{
  echo "# Harness agents (generated — do not edit; run ${CLAUDE_PLUGIN_ROOT}/framework/scripts/gen-codex-agents.sh)"
  echo
  echo "Model routing lives in ${CLAUDE_PLUGIN_ROOT}/framework/models/model-registry.yml. Snapshots: doc 33. Council: doc 34."
  echo
  for f in .claude/agents/*.md; do
    name=$(awk '/^name:/{sub(/^name: */,""); print; exit}' "$f")
    desc=$(awk '/^description:/{sub(/^description: */,""); print; exit}' "$f")
    echo "## ${name:-$(basename "$f" .md)}"
    echo
    echo "_${desc}_"
    echo
    echo "Source: \`$f\`"
    echo
    awk 'BEGIN{fm=0} /^---$/{fm++; next} fm>=2{print}' "$f"
    echo
  done
} > "$out"
echo "wrote $out ($(ls .claude/agents/*.md | wc -l | tr -d " ") agents)"
