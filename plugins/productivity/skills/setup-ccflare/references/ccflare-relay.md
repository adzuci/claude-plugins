# ccflare-relay reference

## Source of truth

- Repository: <https://github.com/apolloio/ccflare-relay> (private Apollo access required)
- Installer: `scripts/install-ccflare.sh`
- Compose wrapper: `scripts/docker-compose.sh`
- Architecture: `guard/ARCHITECTURE.md`

Review the repository files before each install. The skill bundles only the stable MVP orchestration; Guard and better-ccflare remain sourced from the canonical private repository.

## Privacy and architecture

Guard is the client-facing reverse proxy. It sends the real request to Anthropic, returns the response, and asynchronously replays a cached copy to better-ccflare for local analytics. better-ccflare is isolated from outbound network access and is not in the live response path.

The stack still processes and persists sensitive Claude request and response content. Treat its SQLite data, Docker volume, logs, and exports as private. Do not expose the dashboard beyond localhost or copy analytics into a report unless the user explicitly requests it. The replay account does not need a real Anthropic key.

## Relationship to memory and cost data

ccflare is optional for the memory plugin. The repository's Claude `SessionEnd` hook computes per-model token totals directly from the archived transcript with `jq`, at zero API cost. It does not need ccflare. Some local variants calculate dollar cost from BudgetClaw SQLite with transcript-pricing fallback; `ccusage` can also calculate costs from local session data.

Use ccflare when the user wants a persistent dashboard, request-level latency and cost analytics, or one local routing endpoint. Treat its figures as operational analytics, not authoritative billing.

## MVP install effects

The bundled helper:

- clones the private repository and initializes its submodule;
- creates the external `better-ccflare-data` Docker volume;
- builds and starts Guard and better-ccflare;
- interactively creates `guard-replay` when absent;
- appends one managed `ANTHROPIC_BASE_URL=http://localhost:8080` export to `~/.zshrc` when no conflicting export exists; and
- opens the local dashboard.

It does not install Docker, Colima, Homebrew, or GitHub authentication. It does not pull an existing checkout, delete data, or overwrite a conflicting shell route.

## Operations

From the canonical checkout:

```bash
./scripts/docker-compose.sh ps
./scripts/docker-compose.sh up -d
./scripts/docker-compose.sh stop
./scripts/docker-compose.sh logs -f
```

Default URLs:

- Guard health: `http://localhost:8080/_guard/health`
- better-ccflare health: `http://localhost:8080/health`
- Dashboard: `http://localhost:8080/dashboard`
