# OWASP-Backed Ranking

Use OWASP Top 10 (2021) as a stable taxonomy for bucketing findings and ranking them when multiple compete for sprint attention. Ranking is **not** routing — ownership still flows through `team-lookup.md`.

## How to bucket a finding

1. Read the source-extracted CWE if present (Kodem and Orca both expose it).
1. Map CWE → OWASP category using the table below.
1. If no CWE, infer from the finding's verb (e.g. "cross-tenant write" → A01, "shared secret" → A02, "response splitting" → A03).
1. Record the bucket in the routing table's `Reason` column as `OWASP:Axx`.

## The buckets (Apollo flavor)

Each entry: category, common Apollo finding pattern, default severity floor, and where in the codebase to look first.

### A01 — Broken Access Control

The single highest-frequency class in the recent INCIDENT queue. IDOR, missing `authorize`, unscoped `Model.find(params[:id])` followed by an action that doesn't gate on `current_user.team_id`. Pundit policies that exist but are bypassed.

- **Apollo examples:** INCIDENT-28885 (IDOR in `TeamsController` catchall actions), SEC-3319 (cross-team `bulk_set_custom_field`), SEC-2802 (subdomain default without permission), SEC-2375 (BAC on `update_assistant_setting`).
- **Severity floor:** P2. Cross-tenant write IDOR with deliverability/billing impact is P1.
- **Look in:** `packs/iam/app/controllers/`, `packs/crm_platform/app/controllers/`, anywhere `before_action :set_*` loads a record from params.
- **Default ranking priority:** highest. Pen-test reproducible exploit + cross-tenant data = sprint-top.

### A02 — Cryptographic Failures

Shared/duplicated secrets across environments, weak `secret_key_base`, cookies signed with a key that exists in non-prod, predictable tokens.

- **Apollo examples:** INCIDENT-27148 (same `secret_key_base` in staging and prod), related findings about `remember_token_leadgenie_v2` reuse.
- **Severity floor:** P2. Staging-prod secret parity that enables cross-env session forging is P1.
- **Look in:** Vault/secret-manager configs, Rails credentials files, `*_KEY_BASE` env vars per environment.
- **Default ranking priority:** high. Hard to detect post-exploit, so prefer fixing fast even when no exploit has landed.

### A03 — Injection

HTTP response splitting, SQL injection, command injection, SSRF-adjacent injection, `eval`/`send`-with-user-input. RCE belongs here when it's via injection (most are).

- **Apollo examples:** INCIDENT-28083 (Axios HTTP Response Splitting CVE-2026-40175 in `leadgenie/scripts/`), INFOSEC-12136 (RCE via `Criteria#eval` on CRM endpoint — active exploitation).
- **Severity floor:** P1 in prod serving paths. **P3-P4 in CI scripts and dev tooling** even when the CVSS is 10.0 — see CVSS context adjustment in `cve-triage.md`.
- **Look in:** controllers/services that take a `params[:expression]`-style input, anywhere `eval`/`instance_eval`/`send` runs on user data, libraries with known injection CVEs.
- **Default ranking priority:** highest for prod serving code. Drops sharply for non-serving paths.

### A04 — Insecure Design

Missing redirect_uri allowlists, OAuth scope confusion, missing rate limits on auth-sensitive endpoints, design-level gaps that no amount of input validation fixes.

- **Apollo examples:** SEC-3321 (Gong MCP missing `redirect_uri` allowlist at `/authorize`), ITBS-1300 (corp-eng-mcp missing body limits + HTTP timeouts).
- **Severity floor:** P2.
- **Look in:** OAuth integrations, MCP server endpoints, any handler with a "design assumption" comment.
- **Default ranking priority:** medium-high. These are slow burns but expensive to fix once shipped.

### A05 — Security Misconfiguration

The bread-and-butter of Orca findings. Public IPs on EC2, open Cloud Run ingress, GKE workloads with privileged service accounts, IAM bindings that grant too much.

- **Apollo examples:** SEC-3287 (EC2 public IP on Tailscale relay — accepted risk after review), ITBS-1296 (Cloud Run ingress not restricted), SEC-2563 / SEC-2348 (GKE Security Command Center findings).
- **Severity floor:** P3 in non-prod accounts, P1 in prod accounts.
- **Look in:** Terraform under `terraform/`, GKE manifests, IAM bindings.
- **Default ranking priority:** medium — high volume, but most are accepted risks or easy IaC PRs.

### A06 — Vulnerable and Outdated Components

Dependency CVEs. The reachability check is everything — see `cve-triage.md`.

- **Apollo examples:** INCIDENT-28083 (Axios; CVSS 10.0 but path was CI-only), INCIDENT-28083-class gem CVEs in `leadgenie` and adjacent repos.
- **Severity floor:** P3 by default; promote to P1 only with reachability evidence.
- **Look in:** `Gemfile.lock`, `package-lock.json`, `go.sum`, container base images.
- **Default ranking priority:** **start low, promote on evidence.** The skill should not be tricked by raw CVSS.

### A07 — Identification and Authentication Failures

Session token reuse across envs (also overlaps A02), MFA bypass, broken auth flow in OAuth/SSO.

- **Apollo examples:** the `remember_token_leadgenie_v2` cross-env reuse referenced in INCIDENT-27148 / INCIDENT-26828.
- **Severity floor:** P2.
- **Look in:** `packs/auth/`, session middleware, SSO/OAuth integration code.

### A08 — Software and Data Integrity Failures

Supply-chain (compromised dep, unsigned artifact), deserialization, CI pipeline tampering.

- **Apollo examples:** none surfaced in the recent queue, but watch for findings labeled `kodem` that flag dynamic loading or `Marshal.load`/`YAML.load` with user input.
- **Severity floor:** P2.

### A09 — Security Logging and Monitoring Failures

Detection gaps, missing audit trails (the catchall IDOR in INCIDENT-28885 forged a `UserAction` audit row — that's both A01 and A09).

- **Apollo examples:** Panther rule gaps; missing UserAction coverage on sensitive mutations.
- **Severity floor:** P3.

### A10 — Server-Side Request Forgery

LLM/MCP integrations that fetch user-supplied URLs, webhook handlers, image/file fetchers.

- **Apollo examples:** Watch the MCP servers (`corp-eng-mcp`, Gong MCP) — they're SSRF-shaped surfaces.
- **Severity floor:** P2.

## Ranking when multiple findings compete

When you have to pick which to surface first in the urgent skim:

1. **Active exploitation > everything.** If a Panther alert or Bugcrowd submission references in-the-wild exploitation, it's P0 regardless of category.
1. **A01 cross-tenant > A03 injection in non-serving > A05 in prod > A02 > A06 unreachable.** This is a heuristic, not a rule — use judgement.
1. **Tie-break on blast radius.** Multi-tenant > single-tenant. Production account > dev. Customer-data > internal.
1. **Tie-break on MTTR remaining.** A P2 with 3 days left to SLA outranks a P1 with 25 days left.
