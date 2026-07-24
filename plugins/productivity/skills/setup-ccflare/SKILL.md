---
name: setup-ccflare
description: Install, verify, or troubleshoot the private ccflare-relay stack on macOS for a local Claude Code analytics dashboard and centralized API routing. Use when the user asks to set up ccflare, better-ccflare, the ccflare dashboard, Guard, or ANTHROPIC_BASE_URL routing.
---

# ccflare Setup

Set up the hardened [Apollo ccflare-relay](https://github.com/apolloio/ccflare-relay) stack with a self-contained, idempotent MVP flow.

Read [references/ccflare-relay.md](references/ccflare-relay.md) before making changes. The relay can store Claude request and response content locally for analytics. Explain that privacy boundary and the intended git, Docker, and `~/.zshrc` changes, then ask once for confirmation before installation.

Make clear that ccflare is optional. The memory plugin already extracts per-model token totals from local transcripts without ccflare. Local variants may calculate session cost from BudgetClaw SQLite, transcript pricing, or `ccusage`; ccflare adds a dashboard, request-level analytics, and centralized routing, but is not authoritative billing.

## Preflight

1. Run the bundled helper in read-only mode:

   ```bash
   plugins/productivity/skills/setup-ccflare/scripts/setup_ccflare.sh --check
   ```

2. Stop with a precise blocker when:
   - the host is not macOS;
   - `git`, Docker with Compose v2, or a running Docker daemon is missing;
   - GitHub access to the private `apolloio/ccflare-relay` repository is unavailable; or
   - the requested target directory contains another repository.
3. Never print credentials, request contents, response contents, or the analytics database.

## Install

Before execution, inspect the resolved checkout's `README.md`, `guard/ARCHITECTURE.md`, `better-ccflare/docker-compose.yml`, and `docker-compose.build.yml`. Summarize the current commit, privacy boundary, and material writes. Do not proceed when those files differ materially from this reference until the user accepts the updated plan.

After confirmation, run:

```bash
plugins/productivity/skills/setup-ccflare/scripts/setup_ccflare.sh
```

Use `--repo-dir PATH` when the user specifies a checkout. Otherwise the helper reuses `CCFLARE_REPO_DIR`, recognizes a canonical checkout in the current directory, or defaults to `~/.local/share/ccflare-relay`.

The helper:

1. clones `apolloio/ccflare-relay` with submodules, or reuses a canonical checkout;
2. creates the external analytics volume when absent;
3. starts Guard and better-ccflare from the two canonical Compose files;
4. adds `guard-replay` in `anthropic-compatible` mode at priority `0` when absent;
5. adds exactly one `export ANTHROPIC_BASE_URL=http://localhost:8080` line to `~/.zshrc`; and
6. verifies health and opens the dashboard.

Run it in a PTY because first-time replay-account setup is interactive. At the prompts use an arbitrary local-only API key of at least 10 characters, endpoint `http://guard:8081`, and default mappings (`1`). Never use or display a real Anthropic credential for the replay account.

## Verify

Run:

```bash
REPO_DIR="${CCFLARE_REPO_DIR:-$HOME/.local/share/ccflare-relay}"
docker compose \
  -f "$REPO_DIR/better-ccflare/docker-compose.yml" \
  -f "$REPO_DIR/docker-compose.build.yml" \
  --project-directory "$REPO_DIR" ps
curl --fail --silent --show-error http://localhost:8080/_guard/health
curl --fail --silent --show-error http://localhost:8080/health
```

Confirm that `ANTHROPIC_BASE_URL` resolves to the Guard URL in a fresh zsh shell, but do not send a paid test request without explicit permission.

Report the checkout path, Guard URL, dashboard URL, persistence choice, verification results, and any skipped optional steps.

## Troubleshoot or remove

Use the canonical checkout's README and Compose files. Prefer reversible operations (`stop`) over deletion (`down`, volume deletion, or removing the checkout). Explain data-loss scope and ask for confirmation before deleting containers, the `better-ccflare-data` volume, shell configuration, or the repository.
