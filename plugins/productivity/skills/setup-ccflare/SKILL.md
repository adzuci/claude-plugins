---
name: setup-ccflare
description: Install, verify, or troubleshoot public better-ccflare on macOS for a local Claude Code analytics dashboard and API routing. Use when the user asks to set up ccflare, better-ccflare, the ccflare dashboard, or ANTHROPIC_BASE_URL routing.
---

# ccflare Setup

Set up the public, MIT-licensed [tombii/better-ccflare](https://github.com/tombii/better-ccflare) image with a self-contained, idempotent MVP flow. This flow does not require Apollo GitHub, network, or employee access.

> **Test status:** The packaged `/setup-ccflare` flow (`/productivity:setup-ccflare` when installed as a plugin) has not yet been tested end to end from this repository location. Its script has received static checks only. State this before installation and report exactly what was verified.

Read [references/better-ccflare.md](references/better-ccflare.md) before making changes. better-ccflare is in the live request path. The helper disables request/response body storage, but the process still handles Claude traffic and keeps operational analytics locally. Explain that privacy boundary and the intended Docker and `~/.zshrc` changes, then ask once for confirmation before installation.

Make clear that ccflare is optional. The memory plugin already extracts per-model token totals from local transcripts without ccflare. Local variants may calculate session cost from BudgetClaw SQLite, transcript pricing, or `ccusage`; ccflare adds a dashboard, request-level analytics, and centralized routing, but is not authoritative billing.

## Preflight

1. Run the bundled helper in read-only mode:

   ```bash
   plugins/productivity/skills/setup-ccflare/scripts/setup_ccflare.sh --check
   ```

2. Stop with a precise blocker when:
   - the host is not macOS;
   - Docker or a running Docker daemon is missing;
   - `~/.zshrc` already contains another `ANTHROPIC_BASE_URL`; or
   - a container named `better-ccflare` uses a different image.
3. Never print credentials, request contents, response contents, or the analytics database.

## Install

Before execution, inspect the pinned public image and upstream release notes when practical. Summarize the image version, privacy boundary, and material writes. The public setup does not include Apollo's private Guard isolation layer: better-ccflare receives live requests directly. Do not describe this as equivalent to that hardened architecture.

After confirmation, run:

```bash
plugins/productivity/skills/setup-ccflare/scripts/setup_ccflare.sh
```

The helper:

1. pulls pinned public image `ghcr.io/tombii/better-ccflare:3.5.42`;
2. creates a persistent Docker volume when absent;
3. starts better-ccflare on host loopback only with request/response body storage disabled;
4. adds exactly one `export ANTHROPIC_BASE_URL=http://localhost:8080` line to `~/.zshrc`;
5. verifies health and opens the dashboard.

The helper does not configure an Anthropic account. Complete that interactive step in the local dashboard before starting a fresh Claude Code session. Do not send a paid test request without explicit permission.

## Verify

Run:

```bash
docker inspect better-ccflare
curl --fail --silent --show-error http://localhost:8080/health
```

Confirm that the container uses the pinned public image, publishes only `127.0.0.1:8080`, sets `STORE_PAYLOADS=false`, and that `ANTHROPIC_BASE_URL` resolves to the local URL in a fresh zsh shell.

Report the image, dashboard URL, persistence choice, account-configuration status, verification results, untested-location warning, and any skipped optional steps.

## Troubleshoot or remove

Use the public upstream documentation. Prefer reversible operations (`docker stop better-ccflare`) over deletion. Explain data-loss scope and ask for confirmation before deleting the container, the `better-ccflare-data` volume, or shell configuration.
