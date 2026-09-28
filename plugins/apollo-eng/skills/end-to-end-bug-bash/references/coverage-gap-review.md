# Coverage Gap Review

Read this during research and use it before presenting a new or revised bug-bash plan. The goal is
not to produce every possible permutation. The goal is to expose the feature's blast radius and
make every material risk either covered, explicitly out of scope, blocked, or knowingly accepted.

## Build the dependency and blast-radius map

Start from the customer journey, then map the systems that can change its outcome:

- entry points and surfaces: UI, API, mobile, extension, import/export, MCP, webhook, scheduled or
  background execution;
- upstream inputs and providers: files, forms, integrations, identity sources, enrichment or
  search providers;
- downstream consumers and destinations: persisted records, messages, sequences, CRM, analytics,
  exports, notifications, or other product areas;
- shared resources: credentials, mappings, custom fields, quotas, credits, rate limits, team
  settings, caches, schemas, and global configuration;
- identities and boundaries: roles, permissions, ownership, teams, tenants, visibility, deleted or
  hidden records, and impersonation/preview modes;
- durable state: legacy configurations, existing integrations, saved mappings, drafts, in-flight
  jobs, retries, migrations, and partially completed runs.

Use implementation diffs, schemas, discussions, bug history, existing tests, and current product
behavior to identify the map. Label inferences as QA hypotheses when the available sources do not
prove them.

## Run the coverage passes

Review every applicable pass. A pass may produce one journey case, several focused cases, or an
explicit out-of-scope entry. Skip a pass that is clearly irrelevant to the feature, but record that
decision in the ledger instead of silently omitting it.

1. **Primary journeys and rules:** happy paths, validation, cancellation, errors, recovery, and the
   final customer-visible outcome—not only request acceptance.
1. **State and lifecycle:** create, edit, copy, rename, delete, archive, restore, pause/resume,
   reconnect, retry, and reuse after source or destination drift. Include fresh, existing, legacy,
   stale, blank, partially configured, and partially successful state when relevant.
1. **Cross-functional intersections:** test the highest-risk intersections between the feature and
   adjacent products or shared primitives. Prioritize shared code, configuration, credentials,
   identity, data, billing, and irreversible downstream effects.
1. **Regression and non-interference:** prove existing customer configuration and unrelated product
   workflows still work. Include migrations/backward compatibility, preservation of existing
   records and mappings, and isolation of cleanup, limits, schemas, and object types.
1. **Surface and execution-context parity:** compare equivalent behavior across applicable UI, API,
   MCP, import, webhook, preview, queued, scheduled, and worker paths. Verify authorization,
   entitlement, timezone, team, filters, and final results—not merely response shapes.
1. **Integration and destination contracts:** cover representative provider and destination types,
   supported actions, authentication ownership, expiration/revocation, rate limits, duplicate or
   mixed deliveries, partial failure, retry, and recovery. Verify both sides of the contract.
1. **Identity, access, and data lifecycle:** roles, visibility, ownership transfer, tenant
   isolation, direct-resource access, hidden/deleted records, and permission changes during a run.
   Records that should be inaccessible must not be selected, revived, or leaked.
1. **Mapping, schema, and ambiguity:** every materially different supported data type; nested or
   similarly named fields; missing, blank, renamed, deleted, or type-changed fields; validation,
   conflicts, limits, remapping, and source-column drift. Do not allow ambiguous identity fields to
   auto-map silently.
1. **Concurrency, idempotency, and ordering:** two users, two surfaces, duplicate events, repeated
   clicks, overlapping jobs, retries, out-of-order delivery, and simultaneous edits where shared
   state can collide. Assert reservation, attribution, deduplication, and conflict behavior.
1. **Entitlements, billing, and capacity:** flags, plans, credits, quota, provider limits, team-wide
   consumption, exhaustion and recovery, and attribution when multiple surfaces act concurrently.
1. **Release-quality concerns:** browser/responsive behavior, accessibility, localization/timezone,
   performance at meaningful boundaries, analytics/audit events, observability, privacy/security,
   and actionable errors. Include only the dimensions material to the feature and launch risk.
1. **Safety and cleanup:** controlled recipients and destinations, dry-run or save-only paths,
   disposable artifacts, bounded spend, secret redaction, cleanup ownership, and restoration of
   fault controls or settings changed by the test.

## Select combinations without exploding the plan

Do not generate the full Cartesian product. Select combinations using risk-based pairwise coverage:

- always cover the critical customer journey and any combination tied to a known bug;
- add intersections that share mutable state, credentials, billing, identity, mappings, or code;
- add combinations with irreversible or externally visible effects;
- sample representative providers, destinations, data types, and roles, then justify the sample;
- convert low-risk equivalent permutations into a matrix inside one executable case when the setup
  and assertions remain unambiguous.

## Check existing coverage exactly

An existing test counts only when it exercises the same persona, state, entry point, execution
context, and final assertion. A component test, direct API setup, preview-only check, nearby happy
path, or assertion of a toast/status code is not equivalent to a customer-path regression.

For existing automated or manual coverage, record **Covered**, **Partial**, or **Missing**, plus the
exact missing path or assertion. A known open product bug should remain an expected failure until
fixed; a surprise pass requires validating the setup and code path before declaring coverage.

## Produce the coverage ledger

Before approval, publish a compact ledger alongside the proposed cases:

| Risk or dependency | Evidence/source | Planned case(s) | Status | Reason or residual risk |
| --- | --- | --- | --- | --- |
| [journey, shared system, or coverage pass] | [spec, diff, bug, test, or QA hypothesis] | [IDs] | Covered / Partial / Out of scope / Blocked / Missing | [why] |

There must be no silent blanks. Resolve every **Missing** entry by adding or changing a case,
explicitly scoping it out with a reason, or surfacing it to the user before plan approval. Do not
claim the plan is comprehensive when any material risk remains unaccounted for.

## Final anti-miss check

Before presenting the plan, ask:

- Did we test only the new happy path, one provider, one destination, one data type, one role, one
  user, one surface, fresh state, or success-only behavior?
- Could the feature pass while breaking an existing integration, mapping, global setting, customer
  record, cleanup process, or adjacent product?
- Could preview pass while saved, background, scheduled, webhook, or downstream execution fails?
- Could rename/delete/type drift, stale configuration, retries, partial success, duplicates,
  concurrency, quota, or revoked credentials change the result?
- Do the assertions prove the persisted and downstream customer outcome?
- Are every source item, known bug, discussion decision, existing test, and material dependency
  accounted for in the ledger?

If any answer exposes an untracked risk, update the map, ledger, and cases before asking for
approval.
