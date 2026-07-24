# better-ccflare reference

## Source of truth

- Repository: <https://github.com/tombii/better-ccflare> (public, MIT-licensed)
- Pinned image: `ghcr.io/tombii/better-ccflare:3.5.42`
- Dashboard and health endpoint: `http://localhost:8080`

No Apollo repository, GitHub organization membership, internal network, or Apollo credential is required. Review upstream release notes before changing the pinned image.

## Privacy and architecture

better-ccflare is the client-facing reverse proxy and is in the live request path. The helper binds the published port to host loopback and sets `STORE_PAYLOADS=false`, so prompt and response bodies should not be persisted while token counts, cost, model, status, and timing remain available.

It still processes sensitive Claude request and response content in memory and persists credentials plus operational analytics. Treat its SQLite data, Docker volume, logs, and exports as private. Do not expose the dashboard beyond localhost or copy analytics into a report unless the user explicitly requests it.

This public-only flow deliberately omits Apollo's private Guard isolation layer. Do not imply that the two architectures have the same security boundary.

## Test status

The packaged `/setup-ccflare` flow (`/productivity:setup-ccflare` when installed as a plugin) has not yet been tested end to end from this repository location. Static shell checks are not installation proof. Say this before running it and report the exact validation performed afterward.

## Relationship to memory and cost data

ccflare is optional for the memory plugin. The repository's Claude `SessionEnd` hook computes per-model token totals directly from the archived transcript with `jq`, at zero API cost. It does not need ccflare. Some local variants calculate dollar cost from BudgetClaw SQLite with transcript-pricing fallback; `ccusage` can also calculate costs from local session data.

Use ccflare when the user wants a persistent dashboard, request-level latency and cost analytics, or one local routing endpoint. Treat its figures as operational analytics, not authoritative billing.

## MVP install effects

The bundled helper:

- pulls the pinned public container image;
- creates the external `better-ccflare-data` Docker volume;
- starts better-ccflare with a loopback-only host port and body storage disabled;
- appends one managed `ANTHROPIC_BASE_URL=http://localhost:8080` export to `~/.zshrc` when no conflicting export exists; and
- opens the local dashboard.

It does not install Docker, Colima, Homebrew, GitHub authentication, or a provider account. It does not delete data or overwrite a conflicting shell route.

## Operations

Use Docker directly:

```bash
docker inspect better-ccflare
docker start better-ccflare
docker stop better-ccflare
docker logs -f better-ccflare
```

Default URLs:

- better-ccflare health: `http://localhost:8080/health`
- Dashboard: `http://localhost:8080/dashboard`
