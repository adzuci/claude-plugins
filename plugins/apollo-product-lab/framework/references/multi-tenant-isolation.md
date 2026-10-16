# Multi-Tenant Isolation — Canonical Reference

> **Status**: framework-canonical. Closes Phase E hardening workstream E0.5.
>
> **Binding**: every Pantheon harness run carries an explicit `tenant_id`. Cross-tenant writes are blocked at runtime by the Pantheon framework. Adversarial eval cases enforce this invariant.

---

## Why this exists

Apollo runs harnesses across many customer accounts and many internal teams. The framework doesn't yet have a runtime invariant that prevents a harness triggered by Customer A's PR from writing into Customer B's data. This is a runtime safety concern, not a descriptor-review concern — descriptor review can't catch a templated value that gets bound at runtime.

InfoSec will eventually find this. Phase E gets ahead of it.

---

## Tenant taxonomy

Apollo runs in three tenant scopes. The `tenant_id` field has different semantics per scope:

| Scope | `tenant_id` value | Examples |
|---|---|---|
| **Apollo-internal** | the apolloio team handle (`platform`, `sre`, `growth`, `ai-tooling`) | `pr-review-bot` running on apolloio/leadgenie PR |
| **Apollo-internal multi-team** | special value `apollo-internal` | `oncall-triage-bot` triaging incidents that cross team boundaries |
| **Customer-data** | customer team_id (Mongo ObjectId, 24-char hex) | a hypothetical harness reading from customer A's contacts collection |

Currently all 4 in-scope harnesses operate in Apollo-internal scope. Customer-data scope is not yet used but the invariant must exist before the first such harness ships.

---

## Trigger context

Every harness run starts with a trigger. The trigger payload determines the run's `tenant_id`:

| Trigger source | `tenant_id` derivation |
|---|---|
| GitHub PR webhook | `apolloio` (the leadgenie repo's org) → maps to internal team via path-based routing |
| PagerDuty incident | derived from `service_owners.yml`'s mapping of service → owning team |
| Cron (scheduled) | descriptor's `metadata.owner_team` (always Apollo-internal) |
| CLI manual run | invoking engineer's `apollo-dev-teams.yml` team |
| Customer API webhook (future) | customer's `team_id` from auth context |

Pantheon runtime computes `tenant_id` at trigger time and stamps every span and every output with it. The value is immutable for the lifetime of the run.

---

## Read-vs-write isolation rules

| Operation | Same-tenant | Cross-tenant |
|---|---|---|
| **Read** (MCP query, file read, Snowflake select) | allowed | allowed with redaction enforced (per `value-patterns.md`) |
| **Write** (Slack post, JIRA file, GitHub comment, Snowflake insert) | allowed | **blocked at runtime** |
| **Write to `analytics.harness_runs`** | allowed | n/a — single shared table; tenant_id is a column |
| **Write to `analytics.feature_memory`** (Phase F) | allowed | **blocked at runtime** |

The runtime check: every write operation declares its target `tenant_id`. Pantheon compares to the run's trigger `tenant_id`. If they differ, the write is rejected and the run is marked `tenant_isolation_block` in `analytics.harness_runs`.

Cross-tenant *reads* are permitted because read patterns are already shaped (e.g., `surface-owners.yml` is a multi-team read; `apollo-dev-teams.yml` is a multi-team read). Read-side leak protection is the redactor's job (Phase D batch-1 work).

Cross-tenant *writes* are never permitted. There is no override flag. If a harness needs to write to a different tenant, it must trigger a new run with that tenant's context.

---

## Runtime enforcement

Pantheon runtime adds a wrapper around every output emitter:

```python
def emit_output(self, output_kind, target_tenant_id, payload):
    if target_tenant_id != self.run_tenant_id:
        self.span.status = "tenant_isolation_block"
        self.metric("tenant_isolation_blocks_total", labels={
            "harness": self.harness_name,
            "from_tenant": self.run_tenant_id,
            "to_tenant": target_tenant_id,
            "output_kind": output_kind,
        })
        raise TenantIsolationError(
            f"refused {output_kind} write to {target_tenant_id} from run scoped to {self.run_tenant_id}"
        )
    # ... emit
```

The check fires BEFORE the redactor — tenant-isolation is a structural invariant; redaction is a content invariant. They don't overlap.

---

## Adversarial eval corpus

`eval/multi-tenant-isolation/` ships with 5 adversarial cases:

| Case | Setup | Expected |
|---|---|---|
| `mt-c1-direct-cross-tenant-write` | Skill output names a different `tenant_id` than trigger | Block; emit `tenant_isolation_block` |
| `mt-c2-templated-cross-tenant` | Output target is a Jinja-templated string that resolves to different tenant | Block at template-resolution time, not after write |
| `mt-c3-multi-tenant-fan-out-attempt` | Skill tries to fan out one trigger into N writes across N tenants | Block all N |
| `mt-c4-tenant-id-mutation-mid-run` | Skill tries to mutate `self.run_tenant_id` mid-run | Block; tenant_id is immutable |
| `mt-c5-legitimate-same-tenant-write` | Same-tenant write proceeds normally | Allow; no false positive |

The corpus uses `must_not_leak` style assertions like `eval/cost-attribution-redaction/` — literal substring of the wrong-tenant payload must not appear in `analytics.harness_runs.output_payload`.

---

## Schema additions to descriptors

Descriptors declare expected tenant scope:

```yaml
spec:
  tenant_scope:
    kind: apollo-internal           # apollo-internal | apollo-internal-multi-team | customer-data
    expected_tenants: ["platform", "sre", "ai-tooling"]   # explicit allowlist
    cross_tenant_reads: forbidden   # forbidden | allowed_with_redaction
```

The descriptor validator asserts:
- `tenant_scope.kind` is set
- For `apollo-internal`, `expected_tenants` is non-empty
- For `customer-data`, additional fields required (out of Phase E scope; Phase F preview)

---

## Runtime metric

`tenant_isolation_blocks_total` (counter) by `(harness, from_tenant, to_tenant, output_kind)`.

This metric should hover at zero in steady state. SLO-isolation: any non-zero value triggers SEV-1 page (per framework-slo.md). Spikes mean either (a) adversarial activity, (b) a misconfigured templated value, (c) a bug in the descriptor's `tenant_scope` declaration. All three warrant immediate human attention.

---

## Migration for the 4 in-scope harnesses

| Harness | Trigger tenant | Expected tenants |
|---|---|---|
| `pr-review-bot` | `apolloio` (org) | `[platform, sre, ai-tooling, eng-productivity, growth, frontend-platform, integrations, billing, ...all teams in apollo-dev-teams.yml]` |
| `oncall-triage-bot` | derived from incident.service_owner | per service_owners.yml |
| `capacity-plan-checker` | apolloio (PR-triggered) | platform + ai-tooling primary; reads across all packs |
| `flaky-test-quarantiner` | cron (eng-productivity) | eng-productivity primary; writes to per-team JIRAs (per-team is allowed because teams are Apollo-internal scope, not separate tenants) |

The "writes to per-team JIRAs" pattern is fine: Apollo-internal teams are NOT separate tenants. They share the `apollo-internal` tenant scope. Customer-data scope is the boundary.

---

## Anti-patterns

- **Treating Apollo-internal teams as tenants.** They aren't. The tenant boundary is Apollo-internal vs customer-data, not team-vs-team. Over-isolating internal teams creates friction without security benefit.
- **Letting the descriptor declare `tenant_scope: customer-data` without runtime support.** Phase E does NOT ship customer-data scope yet. Descriptors that declare it fail validation until Phase F adds the customer-tenant-id binding logic.
- **Bypassing the wrapper for "trusted" code paths.** No bypass. Every output emitter goes through the wrapper. Performance cost is negligible (one comparison + one metric increment).
- **Suppressing the metric to reduce noise.** The metric at zero is the point. Suppressing it hides the signal we built it for.

---

## Phase E exit requirements

- [ ] Pantheon runtime emits `tenant_isolation_blocks_total` metric
- [ ] Output emitter wrapper deployed; verified by adversarial eval corpus
- [ ] `eval/multi-tenant-isolation/` ships with all 5 cases passing
- [ ] All 4 in-scope descriptors declare `tenant_scope`
- [ ] Synthetic cross-tenant write attempt blocked end-to-end (drill)
- [ ] SLO-isolation paging tested; SEV-1 fires within 5 min of synthetic block
