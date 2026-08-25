# Function Registry — demo-instance-configuration ↔ Democles

This file is the single source of truth for what can be automated today, what exists in Apollo but isn't safely exposed yet, and who does what across the propose/execute split.

Read this file every run of demo-instance-configuration. It answers: which Layer 1 outputs map to a real function, what execution surface that function uses, and what the Democles agent needs to actually run it.

This file is the operational extract of that research — endpoint schemas, hosts, headers, and confirmed gotchas, kept current as the single source of truth for what's live.

**This is a function registry, not a build log.** It documents current, durable operational truth — schemas, endpoints, gotchas, status — not the history of how or when each fact was confirmed, and not the state of any one specific Apollo instance. Never name a specific deal, opportunity, company, or record ID in this file — this registry is read fresh against every new opportunity, and anything identifying a prior test run here reads as if that new opportunity had already been configured. Source-code citations (controller/model file paths, line numbers) are the exception — they're forward-useful for re-verifying a schema and don't identify any deal or instance.

______________________________________________________________________

## Every create in this registry is non-idempotent, and most duplicates are permanent

**Read this before running any `POST` documented below.** None of these endpoints deduplicate. Issuing the same create twice produces two records, not one — and for most of these objects there is no safe API cleanup path afterward:

| Function | Duplicate on repeat `POST`? | Cleanup if it happens |
|---|---|---|
| `stage_demo_sequence` | Yes | **UI only** — `DELETE` 404s, and `PUT {"archived": true}` can destroy steps (see that entry) |
| `stage_saved_search` | Yes | **UI only** — the `DELETE` endpoint is confirmed broken server-side |
| `configure_workflow` | Yes | Archive only, and only under the conditions in that entry |
| `configure_persona` | Yes — **and there is no list/index endpoint reachable by API key**, so a duplicate cannot even be detected programmatically | UI only |
| `push_context_center_product` | Yes (products are a list under one profile) | `DELETE /product/:id` exists |
| `push_context_center_profile` | Unlikely — one profile per team, so a repeat generally resolves to the same record | n/a |

**Two rules follow from this, and both have already been violated in a real incident:**

1. **Never re-issue a create to "check" what happened.** If a response can't be parsed, the answer is to re-read that response — not to repeat the write. Repeating it is how you turn one unclear result into two real records.
1. **A missing or `null` ID in a response body is not evidence that nothing was created.** Several of these endpoints nest the new ID under a wrapper key (see `stage_demo_sequence` and `push_context_center_product` in particular). Confirm where the ID actually lives for that specific function before concluding anything from its absence.

Where an entry documents a search-or-check step before its create, that step is part of the function, not an optional preamble — it is the only pre-flight guard against a duplicate that can't be cleaned up.

______________________________________________________________________

## Authentication, hosts, and headers

Every `direct_api` call needs all three headers:

```
X-Api-Key: <the demo instance's API key>
Content-Type: application/json
Cache-Control: no-cache
```

**Send exactly those three headers and nothing else — a leftover `Authorization` header will `401` an otherwise-valid `X-Api-Key` call.** This is the natural failure mode of this skill's own two-step flow, because the provisioning step immediately before these calls legitimately authenticates with `Authorization: Bearer <OAuth token>`, and any caller that reuses a header set or a shared curl template will carry that bearer forward. Apollo's auth resolves the API key and **then still validates the bearer token**, so a leftover bearer that is invalid, expired, or scoped to the provisioning user returns `401 {"error":"Access token is invalid","error_code":"INVALID_ACCESS_TOKEN"}` even when the `X-Api-Key` is valid and provably present on the wire. Clear the header explicitly before any `direct_api` call — in curl, `-H "Authorization:"` deletes it (note that `-H "Authorization;"` sends it *empty*, which is harmless but is not the same thing).

Tell this apart from the other auth failures by response body, since all of them surface as a bare `401`/`422` with no other distinguishing signal:

| Response body | What it means |
|---|---|
| `422 Api key required` | Neither header present — `X-Api-Key` missing or empty, and no `Authorization` either |
| `401 Invalid API key. See ...` | `X-Api-Key` present but malformed, truncated, or wrong |
| `401 Invalid access credentials.` | An `Authorization` header with no `X-Api-Key` at all |
| `401 Access token is invalid` / `INVALID_ACCESS_TOKEN` | **The leftover-bearer case** — a valid `X-Api-Key` poisoned by a bad `Authorization` header |

Confirmed live 2026-08-21 against a real demo sub-account, on both hosts and all six configuration endpoints below. A server-side request log is **not** sufficient to diagnose this: the persisted row's `access_mode` field only labels the request, and a poisoned call logs `access_mode: api_access_token` with `api_key_id: null` — indistinguishable from a call that never sent an API key at all, even though it did.

**This rule is duplicated in `agents/democles.md` on purpose, and the two must stay in sync.** Democles is the agent that actually builds these calls, and it cannot read this file — it works only from the per-function `registry_entry` inlined into its dispatch, which by definition never carries this shared auth section. A warning documented only here would guide planning and reach nothing at execution time, so `democles.md`'s Execution surfaces section carries its own copy. If you change the header contract, change it in both places.

**Host is per-object, not one global API host.** None of these four object types are on Apollo's public documented API reference, so none of them are guaranteed to share a host with each other or with the documented `api.apollo.io/v1/...` examples:

**Scope note: every function in this registry is `direct_api`, as of 2026-07-28.** The `apollo_cli` surface was retired — it authenticates via `apollo auth login`/`apollo auth whoami` as whatever account the operator's local session belongs to, which can never be the freshly provisioned sub-account a plan targets (see `stage_demo_sequence`'s command sequence and `agents/democles.md`'s Execution surfaces). Any function or step still described anywhere as CLI-based is unavailable, not an alternative to consider.

| Function / object | Host | Path prefix |
|---|---|---|
| `push_context_center_profile` (content_center) | `api.apollo.io` | `/api/v1/content_center/profile` |
| `push_context_center_product` (content_center) | `api.apollo.io` | `/api/v1/content_center/product` |
| `configure_persona` (personas) | `api.apollo.io` | `/api/v1/personas` |
| `stage_saved_search` (finder_views) | `app.apollo.io` | `/api/v1/finder_views` |
| `configure_workflow` (rule_configs) | `app.apollo.io` | `/api/v1/rule_configs` |
| `stage_demo_sequence` — sequence-creation step only (`sequences`/`emailer_campaigns`) | Confirmed working on **both** `app.apollo.io` and `api.apollo.io` | `/api/v1/sequences` (NOT `/api/v1/sequences/create` — that path 404s despite matching the CLI's own error-message text and the MCP tool config's `mcp_endpoint`) |

**Payload-wrapping warning, confirmed across three separate endpoints (`personas`, `finder_views`, and `rule_configs`/`sequences`):** do not trust a Rails-strong-params-style wrapper (`{"persona": {...}}`, `{"finder_view": {...}}`) just because it matches convention or matches what a controller's `params.require(:x)` line seems to imply. `personas` and `finder_views` both silently accept a wrapped request without erroring — `personas` creates an empty shell record with a real ID but null content; `finder_views` returns a real `422` claiming an empty name even when one was sent. Both actually require **flat, unwrapped params**. Confirm empirically before trusting a wrapper for any endpoint not already covered in this table.

If a new function gets added to this registry, confirm its host explicitly before assuming it matches a sibling function — don't extrapolate from this table.

______________________________________________________________________

## Live functions

### `push_context_center_profile`

| Field | Value |
|---|---|
| Endpoint | `POST /api/v1/content_center/profile` (create), `PUT /api/v1/content_center/profile/:id` (update) |
| Proposed by | demo-instance-configuration — builds the payload from demo-prep-intelligence's Context Center Field Mapping output, shows it, gets approval |
| Executed by | Democles (agent) |
| Execution surface | `direct_api` — no CLI or MCP coverage exists for content_center |
| Status | active |
| Approval gate | required |
| Auth | Standard Apollo API key, scoped to its own team (writes only into its own team's data). Requires `can_edit_ai_content_center` on the key's user. |

**Payload shape** (`POST`/`PUT /api/v1/content_center/profile`, real permitted params, sourced from `content_center_controller.rb`). demo-prep-intelligence's Overview / Key benefits & outcomes / Unique characteristics / Other details payload maps onto **`profile`**, not `product`:

```yaml
profile:
  domain: string                      # Overview — company domain
  company_or_product_name: string     # Overview — company name
  company_logo: string
  customer_profile: string            # Overview — who they sell to
  company_overview: string            # Overview — offering/what they do
  customer_pain_points: string        # Key benefits & outcomes
  value_proposition: string           # Key benefits & outcomes
  product_differentiators: string     # Unique characteristics
  primary_competitors: string         # Unique characteristics
  social_proof: string                # Unique characteristics (omit unless verifiable)
  call_to_action: string              # Other details
  additional_context: string
  icp_fit_criteria: string
  high_value_fit_criteria: string
  disqualification_criteria: string
  research_sources: string
  profile_name: string
```

**Scoping note:** there is no per-account scoping in this controller — every operation resolves to the current team's one Global CC (one profile per team). Check current record state before assuming a dispatch is a create — a team can have at most one profile; if one already exists (common on a previously-configured instance), a fresh dispatch should be a `PUT` to it, not a `POST`.

### `push_context_center_product`

| Field | Value |
|---|---|
| Endpoint | `POST /api/v1/content_center/product` (create), `PUT /api/v1/content_center/product/:id` (update) — a separate product/service card object, a list under the team's one profile |
| Proposed by | demo-instance-configuration — builds the payload from demo-prep-intelligence's Context Center Field Mapping output, shows it, gets approval |
| Executed by | Democles (agent) |
| Execution surface | `direct_api` — no CLI or MCP coverage exists for content_center |
| Status | active |
| Approval gate | required |
| Auth | Standard Apollo API key, scoped to its own team. Requires `can_edit_ai_content_center` on the key's user. |

**Whose product this represents — read this before building a payload.** This object is one specific product/service line from **the prospect's own business** — e.g., one item from the prospect's actual offering list ("SBA loans," "revenue advances," "fleet route optimization"). It is **not** an Apollo product card, an Apollo capability, and not a generic account-scoped notes field either. Source the payload from demo-prep-intelligence's Context Center Field Mapping "Offering" content (the prospect's own description of what they sell), never from Apollo's capabilities map or battlecard content. See `profile`'s entry above for the parallel whole-company object — `product` is one narrower line item under it, still describing the prospect, never Apollo.

**Payload shape** (`POST`/`PUT /api/v1/content_center/product`):

```yaml
product:
  product_or_service_name: string   # REQUIRED — omitting it 422s with PRODUCT_DATA_REQUIRED
  one_sentence_description: string
  product_content: string
  is_default: boolean
```

**Response-shape gotcha:** `POST /product` does not return just the created product — it returns the same shape as `GET /api/v1/content_center` (top-level `content_center_profile`, `notes`, and `products` array). Read the new product's ID from `products[-1].id` or match by `product_or_service_name`, not from a bare `id` on the response root.

**Scoping note:** there is no per-card scoping in this controller — a team can have multiple `product` entries under its one profile, with one marked `is_default`.

**Deletion confirmed live.** `DELETE /api/v1/content_center/product/:id` works — the product disappears from the `products` array on a follow-up `GET /api/v1/content_center`, and a repeat `DELETE` on the same ID correctly 404s (`{"error":"Product not found"}`). Unlike the profile itself, which has no delete route and must be blanked via `PUT`, a product can be removed outright.

### `configure_persona`

**Standing inclusion.** Unlike most functions in this registry, which are proposed only when the Recommended Demo Flow calls for them, `configure_persona` is a **default-consider function**: propose it on every run where a Context Center payload exists, per `SKILL.md`'s Workflow Step 2 standing rule. This reflects a product-showcase priority (Personas are a capability GTM Systems wants demoed on their own merits), not a deal-evidence-driven one — do not gate it behind the brief explicitly mentioning personas, and do not treat a `stage_saved_search` action targeting the same audience as already covering this need.

"Where possible" is a real condition, not a re-derive-it-each-time judgment call — it means exactly one of these two states, nothing looser:

- **Possible (Proposed):** a Context Center payload exists (Business Understanding Gate passed, `customer_profile` populated) and either maps directly to `PERMITTED_PERSONA_FILTERS` or maps via `generate_personas_fallback`.
- **Not possible (Blocked / Routed to roadmap):** no Context Center payload exists yet this run, **or** `customer_profile` is populated but too sparse to map even through the fallback (e.g. one vague sentence with no segment/title/industry signal to structure). There is no third state — if neither condition holds, this function is Proposed, full stop.

**Every `configure_persona` payload should be built via the Hybrid Persona Construction Procedure in `SKILL.md`, not assembled solely from Context Center prose.** A persona with populated `person_seniorities`/`organization_industry_tag_ids`/etc. that has no provenance tag on those fields is a process violation, not a stylistic gap — those fields have no non-AI source and must show where they came from.

| Field | Value |
|---|---|
| Endpoint | `POST /api/v1/personas` |
| Proposed by | demo-instance-configuration — builds the filter payload from demo-prep-intelligence's Context Center `customer_profile` field for deal-specific facts (titles, geography, company size), reconciled against `generate_personas_fallback`'s harvested taxonomy values for fields the brief can't populate (seniority, industry tags, department codes). See the Hybrid Persona Construction Procedure in `SKILL.md`. |
| Executed by | Democles (agent) |
| Execution surface | `direct_api` — no CLI or MCP coverage exists for personas |
| Status | active — live-verified (real personas created and persisted) |
| Approval gate | required |
| Auth | Standard Apollo API key. Gated on `current_user.permission_set.can_add_and_edit_persona` — check before assuming the key's user has it. |

**Real object/controller:** literally named `Persona` / `PersonasController`, confirmed via source — not `api/v1/ai_persona`, a name that doesn't exist anywhere in the codebase.

**Critical — payload must be FLAT, not wrapped.** A payload nested under a top-level `persona` key (standard Rails strong-params convention) is **wrong**. Sending it wrapped returns a real `200` with a real ID — but silently creates an empty shell record: `name`, `filters`, `titles`, and every other field come back `null`/`{}` in the response, with no error at all. This is a dangerous failure mode precisely because it looks like success. The correct payload sends `name`, `titles`, `seniorities`, `filters`, etc. as **top-level keys directly in the POST body, with no `persona` wrapper**. **Any spec built with a `persona:` wrapper must be corrected before dispatch — Democles should refuse a wrapped payload for this function rather than execute it, per Hard Rule 1.**

**Payload shape (flat)** — `filters` must be a subset of `PERMITTED_PERSONA_FILTERS` (confirmed from `personas_controller.rb` — 27 unique whitelisted keys; the source array has 28 entries with `person_department_or_subdepartments` listed twice):

```yaml
name: string
seniorities: [string]                  # top-level convenience field
titles: [string]                       # top-level convenience field
not_titles: [string]                   # top-level convenience field
department_or_subdepartments: [string] # top-level convenience field
filters:                               # must be a subset of PERMITTED_PERSONA_FILTERS
  person_titles: [string]
  person_not_titles: [string]
  person_seniorities: [string]
  person_locations: [string]
  organization_locations: [string]
  organization_num_employees_ranges: [string]
  organization_industry_tag_ids: [string]
  person_department_or_subdepartments: [string]
  # ...remaining permitted keys in personas_controller.rb; max 100 titles combined
  # (person_titles + person_not_titles) or the request 422s
# NO top-level "persona:" wrapper — send these keys directly in the request body.
```

**Deletion confirmed live:** `DELETE /api/v1/personas/:id` works and returns `{"persona":{"id":"...","deleted":true},"persona_delete_success":true}` — useful for cleaning up a mistaken create, though it doesn't help find one you've lost the ID for (see the no-list-endpoint note below).

**No list/index endpoint exists for personas.** `routes.rb` only declares `create`/`update`/`destroy` plus `recommended_personas` (AI suggestions, not existing records) and `generate_personas` (the fallback below) — there is no `GET /api/v1/personas` or equivalent. If Democles or a future session needs to find an existing persona's ID (e.g. to delete or reference one) without already having it on record, the only path found so far is indirect: personas appear as `person_persona_facets` entries (`{"value": "<id>", "display_name": "...", "count": N}`) inside `GET /api/v1/auth/additional_bootstrapped_data` — but that field only appears under browser session/cookie auth, not API-key auth (a fresh API-key call to the same endpoint returns no `personas`/`person_persona_facets` key at all). Absent that, the Apollo UI itself is the only reliable source — record the ID at creation time rather than relying on being able to look it up later.

### `generate_personas_fallback`

| Field | Value |
|---|---|
| Endpoint | `POST /api/v1/ai_setup/generate_personas` |
| Proposed by | demo-instance-configuration — called as a standard step for every `configure_persona` build, not a fallback reserved for unmappable prose. See the Hybrid Persona Construction Procedure in `SKILL.md`. |
| Executed by | Democles (agent) |
| Execution surface | `direct_api` |
| Status | active — live-verified. Does **not** persist anything itself; it only returns structured suggestions. `configure_persona` (`POST /api/v1/personas`) is the separate, required persistence step. |
| Approval gate | required (twice — once to accept the generated suggestions, once to approve the resulting `configure_persona` call) |

demo-prep-intelligence's Context Center payload outputs targeting-*adjacent* prose (`customer_profile` — "who they sell to: ICP, industries, segments, geographies, buyer personas," 1-3 sentences), not structured targeting criteria. Still requires the Company + Business Understanding Gate to have passed first (real, source-grounded business understanding exists) — there's no `company_offering` to call it with otherwise. Never use it to route around a failed gate — if the gate fails, that's still a Missing Business Context checklist, not a prompt to `generate_personas`.

**This is a standard sourcing step for every `configure_persona` build, not a fallback reserved for unmappable prose.** Its role is narrower than full persona generation — it supplies candidate values for fields a deal-specific brief structurally cannot populate (seniority, industry tags, employee ranges, department codes), never titles, geography, or company-size decisions, which the brief must originate. See `SKILL.md`'s Hybrid Persona Construction Procedure for the full harvest-and-reconcile workflow this feeds into.

**Payload shape:**

```yaml
company_offering: string     # required
company_name: string         # optional
company_description: string  # optional
```

Returns `{ recommended_personas: [...], summary: string }` — feed `recommended_personas` into a `configure_persona` approval draft rather than persisting it directly.

### `stage_saved_search`

| Field | Value |
|---|---|
| Endpoint | `POST /api/v1/finder_views` |
| Proposed by | demo-instance-configuration |
| Executed by | Democles (agent) |
| Execution surface | `direct_api` — no CLI or MCP coverage exists for finder_views |
| Status | active — live-verified: real persistence (`FinderView.save!`) and full filter round-trip confirmed. **Caveat:** persistence and filter content alone don't guarantee UI visibility — see the `modality`/`shared` gotchas below, found only after records saved cleanly but never appeared in the UI. |
| Approval gate | required |

**Note:** "Saved Search" is UI-only terminology — the real backend object and controller are literally named `FinderView` / `FinderViewsController`.

**Critical — request body must be FLAT, not wrapped.** Same bug as `configure_persona`: sending the payload wrapped in a top-level `finder_view:` key returns a real `422`: `{"error":"Please put in a non-empty name."}` — even with a genuinely non-empty name — because the server never sees the wrapped fields as top-level params. Sending the identical fields flat, with no wrapper, at the top level of the request body succeeds with a real `200`. **The response is still wrapped under `finder_view` either way** (see below) — the bug is specifically in what the *request* needs, not the response. Any spec with a `finder_view:`-wrapped request body must be corrected before dispatch.

**Payload shape (flat request)** (`finder_view_params`, from `finder_views_controller.rb`):

```yaml
name: string
signals: [string]
modality: string   # REQUIRED for UI visibility — see gotcha below (e.g. "people" for a people/contact search)
shared: boolean    # REQUIRED: true for team visibility — see gotcha below
last_accessed_at: datetime
alert_frequency: string
finder_table_layout_id: string
filter_version: "2"   # REQUIRED alongside filters_v2 — see gotcha below
filters_v2: object    # flat keys (e.g. person_titles, organization_num_employees_ranges)
                       # are valid "base params"; filter_expression is the nested-boolean-
                       # tree form for complex filters. Not schema-validated — stored as-is.
# enrichment_mode_enabled: boolean   # conditional, not always permitted
# NO top-level "finder_view:" wrapper on the REQUEST — send these keys directly.
```

**Gotcha: `filters_v2` is silently ignored** — stored as `null` with no error — unless `filter_version` is also sent as `"2"` in the same request (`finder_views_controller.rb`: `@finder_view.filters_v2 = ... if params.key?(:filters_v2) && params[:filter_version].to_s == '2'`). Omitting `filter_version` creates a real, persisted, but functionally empty saved search (name only, no filters). Always send both fields together in the Democles dispatch payload.

**Gotcha: `modality` required for UI visibility, no error if omitted.** Omitting `modality` (e.g. `"people"`) saves the record successfully with `modality: null` — the record is real and correctly filtered, but silently invisible on any modality-scoped page (e.g. "Find people"'s saved-search list). Confirmed via source (the normalization `#search` applies to `modality`) and live-tested: a `PUT` adding `modality: "people"` to an existing record made it appear. Always send `modality` explicitly, matching the page the saved search is meant for.

**Gotcha: `shared` required for team visibility, no error if omitted.** `shared` defaults to `false` when omitted, which sets `sharing_permission.visibility` to `"restricted"` — the record saves successfully but is completely invisible to anyone but the creating API key's own user. Confirmed via source (`FinderView`'s `shared` default and `SharingFunctionality`'s `"restricted"` default visibility) and live-tested: setting `shared: true` makes the record visible to the team. Always send `shared: true` explicitly for a demo saved search meant to be seen.

**Standing lesson for this API surface: a `200`/`201` with a real ID is necessary but not sufficient.** Several fields on this endpoint (`filter_version`, `modality`, `shared`) silently no-op or default to something wrong, with a clean success response and no error at all — the only symptom is "why can't I see this in the UI." Confirm new fields against the actual UI before trusting a live test as fully passing.

**Response shape:** wrapped under a top-level `finder_view` key (matches the `content_center` wrapping pattern) — this is the RESPONSE shape, unrelated to the request-flattening correction above.

**`breadcrumbs` mechanism.** `breadcrumbs` is not saved on the record at all — it's computed at serialization time by `EsSearcher::Breadcrumbs.generate`/`generate_salesforce_list_view_breadcrumbs` from the record's `signals`, and only included in the JSON response when the rendering view explicitly passes an `include_breadcrumbs: true` local to `api/v1/finder_views/_detail.json.jbuilder` (which defaults `include_breadcrumbs` to `false` otherwise). Confirmed by reading every jbuilder view that renders this partial: `show.json.jbuilder`, `update.json.jbuilder`, `load_more.json.jbuilder`, and `search.json.jbuilder` all pass `include_breadcrumbs: true` — **`create.json.jbuilder` (the response for `POST /api/v1/finder_views`, i.e. this function's own call) does not.** A fresh saved-search create response having no `breadcrumbs` key is expected, by-design behavior, not a bug. To actually confirm filters took via `breadcrumbs`, follow the create with a `GET /api/v1/finder_views/:id` (`show`) or a `PUT` (`update`) — either includes it; a `POST` create response never will, with or without any request-side fix.

**Live-confirmed shape:** `breadcrumbs` is an array of objects, not human-readable strings — each entry has `label`, `signal_field_name`, `value`, and `display_name` keys, e.g. `{"label": "Company Locations", "signal_field_name": "organization_locations", "value": "Australia", "display_name": "Australia"}`. If `stage_saved_search` or `demo-instance-configuration` ever needs to render a breadcrumb to the SC, use `display_name` (or build from `label`/`display_name` together) — not the raw `value`. **Multi-value filters produce one breadcrumb entry per value, not one per filter field** — e.g. a `person_titles` filter with 4 values produces 4 separate entries sharing the same `label`. Any future rendering logic must group by `label`/`signal_field_name` to present one chip per field rather than assuming a 1:1 mapping between `breadcrumbs` entries and filters.

**Deletion — confirmed via source, confirmed BROKEN live. Do not mark `active`, and do not re-dispatch expecting a different result.** `DELETE /api/v1/finder_views/:id` is real — routed in `config/routes.rb` (`resources :finder_views, only: [:show, :create, :update, :destroy]`) to `FinderViewsController#destroy`, which calls `@finder_view.destroy` (a genuine hard-delete, not an archive) after some side-effect cleanup (unstars the view for anyone who had it starred, reassigns another user's "selected view" pointer if it pointed at this record). Two real gotchas found in source:

- **Authorization:** gated by `cross_team_access` and a Pundit `authorize @finder_view` check (`authorize_finder_view`) — expect `403`/`Pundit::CustomNotAuthorizedError` if the API key's user doesn't have access to the specific record.
- **Two-step confirmation, conditional on local fields:** `validate_force_delete_fields_param` only fires if the finder_view references custom/private fields marked for deletion (`fetch_local_fields_marked_for_deletion`). If it does, the *first* `DELETE` fails with a `ConfirmationError` naming the affected fields and returning an MD5 hash (`force_delete_fields`); a *second* `DELETE` must include that exact hash as a `force_delete_fields` param to actually proceed.

**However, live dispatch against real records returned a different, undocumented server-side error** — not either predicted outcome above: a real `422`: `{"error":"Something's wrong with your API request. undefined method 'id' for nil"}`. Reads as an unhandled nil-object error somewhere in Apollo's own `destroy` path, not a `403` (authorization) or `404` (not found), and not something a retry would fix — do not retry or improvise around it. **Reproduction shape:** a plain `DELETE` against `https://app.apollo.io/api/v1/finder_views/:id`, no request body, the three documented auth headers — nothing about the request itself is malformed, ruling out a client-side mistake. This is a genuine Apollo-side bug, not a documentation gap — needs Apollo engineering to investigate; another dispatch attempt won't change the outcome. Not yet reported to Apollo eng.

### `configure_workflow`

| Field | Value |
|---|---|
| Endpoint | `POST /api/v1/rule_configs` |
| Proposed by | demo-instance-configuration — builds the trigger/action plan from demo-prep-intelligence's Recommended Demo Flow, or from an AI-generated draft via `get_ai_rule_config` |
| Executed by | Democles (agent) |
| Execution surface | `direct_api` — no CLI or MCP coverage exists for rule_configs |
| Status | active — live-verified (real `201`/`200`, persisted, `type`/`object_type`/`active`/`workflow_triggers`/`rule_action_configs`/`nodes` all round-tripped correctly) |
| Approval gate | required |
| Default state | `active: false` — never `true` unless the SC explicitly says so in the same approval turn |

**Note:** `get_ai_rule_config` (a separate action) never persists — it only ever builds a draft. `POST /api/v1/rule_configs` (the `create` action documented here) is the real, separate persist path that calls `.save!`.

**Critical required field: `type: "workflow"`.** Omitting it doesn't error — the record still saves — but it's a silent trap: `MongoSearcher::RuleConfigsSearcher` (the model backing the Apollo UI's Workflows list at `#/workflows`) hardcodes `allowed_type_codes = ['workflow']` and always filters to `type_cd: {'$in': ['workflow']}`, no matter what's queried. A workflow created without `type` is genuinely persisted (real `created_at`, real ID) but permanently invisible on that page. Always send `type: "workflow"` in the `configure_workflow` approval draft.

**Request shape:** send the payload flat, with no `rule_config:` wrapper — confirmed working this way, though (unlike `configure_persona`/`stage_saved_search`) not confirmed via a strict wrapped-vs-flat A/B test. Given both of those endpoints turned out to require flat params despite being documented with a wrapper, treat the flat shape below as the verified-safe default, and confirm before assuming a wrapped shape works if it's ever used.

**Payload shape (flat)** — simpler than it looks. `workflow_triggers` alone carries the trigger; `nodes`/`edges` only need the **action** side — no trigger node or trigger-side edge required in either array at all:

```yaml
name: string
description: string
type: "workflow"            # REQUIRED — see the critical-field note above; wrong/missing = invisible in the UI
object_type: string          # "Contact" or "Account". "Opportunity" is also valid but gated behind
                              # the can_access_opportunities flag. Confirmed via
                              # packs/plays/app/models/workflow/node.rb.
active: boolean               # default false — approval-gated before ever setting true
version: "v2"                 # required to route through the nodes/edges graph builder
filters: object                # search filters scoping who qualifies
workflow_triggers:
  - trigger_type: string       # e.g. "contact_created" — no id needed, server generates one
    constraints: object        # shape depends entirely on trigger_type — see "Trigger constraints by type" below; never guess this
rule_action_configs:           # legacy-format mirror of the action node(s) — required alongside nodes
  - type: string                # real, verified action-type whitelist (35 values), confirmed
                                 # via packs/plays/app/models/workflow/node.rb's
                                 # as_enum :action_type block — do not invent a value outside
                                 # this list. Includes add_contact_to_sequence (confirmed real,
                                 # not just illustrative), add_contact_labels,
                                 # send_email, create_contact_task, set_contact_field,
                                 # remove_contact_labels, stop_contact_sequences, enrich_fields,
                                 # outbound_webhook, exit, and more — see the source file for the
                                 # full list.
    params: object                # shape depends entirely on `type` — see "Action params by type" below; never guess this
nodes:                         # action nodes ONLY — do not include a trigger node, it isn't needed
  - id: string                  # any 24-char hex string; real ObjectIds not required at request time
    type: "action"
    position: {x: 0, y: 0}
    data: {type: string, params: object}   # same verified whitelist and params shapes as rule_action_configs above
edges:                          # edges between action nodes only — no trigger-side edge needed;
                                 # can be an empty array for a single-action-node workflow
  - id: string
    source_node_id: string
    destination_node_id: string
# NO top-level "rule_config:" wrapper — send these keys directly (see request shape note above).
```

**Trigger constraints by type** — sourced from `shared/configs/rules_engine_triggers.yml`, `packs/plays/app/models/workflow_trigger.rb` (`field :constraints, type: Hash, default: {}`), and evaluated in `packs/plays/lib/rules_engine/trigger_handler.rb`'s `evaluate_model_attributes_with_workflow_trigger`/`evaluate_model_attributes_with_constraint` (~lines 1282–1320):

| `trigger_type` | `constraints` shape |
|---|---|
| `contact_created` (and likely `account_created`) | `{}` — genuinely empty; no keys expected or validated. **Simplest, safest choice for a demo** unless the Recommended Demo Flow specifically calls for a different trigger. |
| `contact_updated` (and other `_updated` triggers) | `{field_name: string, new_value: any, previous_value: any, new_value_operator: {op: string}, previous_value_operator: {op: string}}` — dynamically keyed to the field being watched. |
| `contact_added_to_list` / `account_added_to_list` | `{label_ids: array \| "any"}` — list of Label IDs to scope to, or the literal string `"any"`. |
| `contact_added_to_sequence` / `contact_finished_sequence` / `contact_did_first_step_of_sequence` | `{emailer_campaign_ids: array \| "some"}` — list of sequence IDs, or the literal string `"some"`. |
| Any other trigger type | **Not sourced. Do not guess.** Route to the roadmap or ask the SC to confirm before proposing — per `demo-instance-configuration`'s no-placeholder rule (see its SKILL.md). |

**Action params by type** — sourced from `packs/plays/lib/rules_engine/action_handler.rb` (~lines 1345–1542, read via `@params.dig('fields')` / `@params.dig('job_change_options', ...)` / `@params.dig('field_options')`) and `packs/plays/lib/workflow/validators/action_nodes_validator.rb` (~lines 466–628):

- **`enrich_fields`:**

  ```yaml
  params:
    fields: [string]              # REQUIRED — e.g. ["email", "phone", "job_change"]
    job_change_options:           # REQUIRED only if "job_change" is in fields
      edit_preference: string     # REQUIRED — e.g. "CREATE"
      set_owner: string           # REQUIRED if edit_preference == "CREATE" — "new" or "existing"
      contact_stage_id: string    # REQUIRED if edit_preference == "CREATE" — target stage ObjectId
      owner_id: string            # REQUIRED if edit_preference == "CREATE" — ObjectId if set_owner == "new", else the literal "previous_owner_id"
    field_options:                 # optional, one entry per non-job_change field in `fields`
      <field_name>:
        data_writing_policy: string   # "AUTO_OVERWRITE" or "AUTO_FILL"
  ```

  Not yet live-tested for this project — validated against source only.

- **`add_contact_labels` / `add_account_labels` / `remove_contact_labels` / `remove_account_labels`:**

  ```yaml
  params:
    label_names: [string]   # REQUIRED
  ```

  `add_contact_labels` confirmed live; the other three share the same validator entry (`action_nodes_validator.rb` ~lines 147–151) but haven't been live-tested themselves.

- **`add_contact_to_sequence`:**

  ```yaml
  params:
    email_account_id: string           # REQUIRED — one of contact_owner_default / account_owner_default / account_custom_owner_default / contact_custom_owner_default / selected_users_default, or "<bson_id>***<email>"
    emailer_campaign_id: string        # REQUIRED — the sequence's ObjectId
    rotate_mailbox: boolean            # optional
    email_sending_policy: string       # optional, only meaningful if rotate_mailbox: true — "mailgun_only" or "direct_mailboxes_only"
    typed_custom_field_id: string      # required only if email_account_id is one of the *_custom_owner_default values
    fallback_email_account_id: string  # required only for the account_*_owner_default values when object_type is "Account"
    selected_user_ids: [string]        # optional
    selected_email_ids: [string]       # optional, only meaningful if rotate_mailbox: true
  ```

  Sourced from `validate_add_contact_to_sequence` (~lines 616–628). **Confirmed live** — a direct test dispatch (`email_account_id: "contact_owner_default"`) paired with a `stage_demo_sequence`-created sequence succeeded: real `200`, `rule_action_configs`/`nodes` correctly carrying `type: "add_contact_to_sequence"` and `params` round-tripped exactly as sent, `emailer_campaign_id` correctly referencing the paired sequence's ID. **Status: active** — not just source-confirmed. Note this is a separate object from `stage_demo_sequence`'s own sequence-creation flow above — this is a *workflow action* that enrolls a contact into a sequence as part of an automated rule, not the direct `POST /api/v1/sequences` call.

  **Also observed on the same test:** the created workflow's `filters` carried no `prospected_by_current_team` injection — confirms `approval_type: "manual"` actually bypasses the net-new restriction documented below, not just a source-level prediction.

- **Any other action type in the 35-value whitelist:** **Not sourced. Do not guess.** Route to the roadmap or ask the SC before proposing — this registry only documents params shapes confirmed via source; the remaining ~28 action types are unconfirmed until researched the same way.

**Expect this — not a Democles-side error if you see it: the server appends `"prospected_by_current_team": ["yes"]` to the saved `filters`, unrequested,** for a team that's bulk-selection-limited or non-paying (see the mechanism below). The same "server auto-associates something we didn't set" pattern is documented for `stage_demo_sequence`'s `product_profile_ids`. **This is a known, expected response shape, not a fresh anomaly to flag as unexplained each time.** Still report the actual `filters` content that came back (accurate reporting of what was created is always required).

**Mechanism, and a standing recommendation.** `rule_configs_controller.rb`'s `update_filter_params` (a `before_action` on `create`/`update`, ~line 1688) force-sets `filters['prospected_by_current_team'] = ['yes']` unless it's already present or `@rule_config.can_run_on_net_new?` is true. `can_run_on_net_new?` (`rule_config.rb:255`) is true only if the team isn't bulk-selection-limited or is paying (`RulesEngine::Utils.can_team_run_play_on_net_new?`), **or** the workflow has `approval_type: "manual"` (or `trial_run_in_progress`) set and isn't an account-based play with a people action (`is_manual_approval_enabled?`, `rule_config.rb:370`). What the filter itself does (`es_searcher/filters/prospected_by_filter.rb`): `"yes"` restricts the workflow's matching audience to records already in this team's own Contacts/Accounts, excluding anyone found only via a fresh, not-yet-imported search. **This applies whenever the target team is bulk-selection-limited or non-paying — check the team's plan tier rather than assuming either way.**

**On live-email safety:** `add_contact_to_sequence`'s send path (`action_functionality.rb:260`, `add_to_emailer_campaign`) must resolve a real, connected `EmailAccount` per contact before any send; with none connected, contacts route to `no_email_account_contacts` and are marked failed, and the actual send call (`deploy_contacts`) never fires. So no email reaches a real person on any instance with no connected mailbox — typical for a demo instance, but verify per-instance rather than assuming. What the `prospected_by_current_team` default *does* still cause regardless of email risk: a demo workflow using a non-email action (`enrich_fields`, `add_contact_labels`) can silently match zero people if the target audience isn't already saved as Contacts — a demo-completeness issue, not a safety one.

**Standing recommendation: include `approval_type: "manual"` in every `configure_workflow` payload this automation layer builds.** Confirmed as a legitimate, permitted `create`/`update` param (`rule_configs_controller.rb:1546`, plain string field, no other required companion field). Two independent benefits, not one: (1) satisfies `is_manual_approval_enabled?`, which bypasses the net-new restriction above — the workflow can show its real, fresh matching audience instead of narrowing to already-known Contacts; (2) confirmed via `action_handler.rb:2974` — with `approval_type == 'manual'`, every matched action (any type, not just email) routes to `RuleActionManualProcessingWorker`, a human-review queue, instead of `RuleActionAutomaticProcessingWorker` — nothing executes automatically on a real match, a genuine additional safety layer on top of `active: false` (already the default) and the no-connected-inbox gate. **One real caveat:** `is_manual_approval_enabled?` also requires the workflow is *not* an account-based play with a people-level action node (`prospected_object_type == 'Account'` with a people action) — for that specific combination, `approval_type: "manual"` has no effect regardless of what's set. Uncommon for a typical demo workflow, but don't assume this recommendation is universal without checking `object_type`/action shape first.

**What's still genuinely open — distinct question from "is this expected":** whether it's *safe* for demo purposes, i.e. whether it could narrow who the workflow actually scopes to (e.g. excluding contacts not already prospected by the team) in a way that wasn't part of the approved plan. Not yet root-caused via source beyond the mechanism above, and not yet confirmed against the Apollo UI. Until that's checked, `demo-instance-configuration`'s approval draft for `configure_workflow` should note that the saved scope may include this condition in addition to whatever `filters` was explicitly approved.

**Deletion is restricted.** `DELETE /api/v1/rule_configs/:id` only succeeds when the record has an `assistant_thread_id` and the request includes matching `call_from_assistant`/`assistant_thread_id` params (`rule_configs_controller.rb`'s `destroy` action). A workflow created via direct API (as `configure_workflow` does) has no `assistant_thread_id`, so `DELETE` on it always returns `422 {"error":"Unauthorized workflow deletion"}` — this is not a permissions bug to work around, it's how the endpoint is built. The only removal path available to Democles is `POST /api/v1/rule_configs/:id/archive`, which unlists it from the Apollo UI's `#/workflows` page but does not delete the underlying record.

**If a workflow needs to be renamed (e.g. to mark it for cleanup) before archiving, do not send a partial `{name: ...}` payload.** `PUT /api/v1/rule_configs/:id`'s non-partial update path unconditionally rebuilds `rule_action_configs` from `params[:rule_action_configs]`/`params[:manual_action_config]` (defaulting to `[]` if absent — no fallback to the existing value, unlike `filters` and `notification_config`, which do fall back) and unconditionally reassigns `workflow_triggers` from `params[:workflow_triggers]` via `MongoUtil.assign_embedded_model` (also no fallback). A bare `{name: "..."}` PUT will silently wipe both. The safe pattern: GET the full current record first, then PUT with `name` changed plus `rule_action_configs` and `workflow_triggers` round-tripped verbatim from that GET — and omit `nodes`/`edges`/`version` entirely so the `params.key?(:nodes)`-gated graph-rebuild branch never runs and those fields are left untouched.

### `stage_demo_sequence`

| Field | Value |
|---|---|
| Endpoint | `api/v1/emailer_campaigns` (sequence search only, via CLI), `POST /api/v1/sequences` (sequence creation, via direct API — see mixed-surface note below), `api/v1/contacts` (contact search + creation, via CLI) |
| Proposed by | demo-instance-configuration — builds the plan from demo-prep-intelligence's Recommended Demo Flow |
| Executed by | Democles (agent) |
| Execution surface | `direct_api` (revised 2026-07-28 — previously mixed; the `apollo_cli` portions are retired, see the command sequence below). Historically `direct_api` specifically for sequence creation. |
| Status | active — live-verified: sequence and contact creation both confirmed working. |
| Approval gate | required |
| Default state | Sequence created without `active: true` (never pass it) — stays in draft/inactive state, consistent with never escalating without explicit SC approval |

**Why this step is `direct_api` — formerly headed "Mixed execution surface," corrected 2026-08-03.** `apollo sequences create --steps-file ...` fails via the CLI with a real `403`: `{"error":"api/v1/sequences/create is not accessible with this access token","error_code":"API_INACCESSIBLE"}` — the CLI's OAuth-based session token lacks this scope, even though `apollo sequences search` and `apollo contacts create` both work fine via the same CLI session. The same person's raw API key, used as a `direct_api` call, does not have this restriction: `POST /api/v1/sequences` (not `/api/v1/sequences/create` — that literal path 404s; the real path is `POST /api/v1/sequences`, confirmed via `packs/email_messaging/app/services/sequences/unified/create_service.rb`) succeeds with a real `200` on **both** `app.apollo.io` and `api.apollo.io` — either host works for this specific call. Body: flat (no wrapper — see the pattern in `configure_persona`/`stage_saved_search` above), `{"name": string, "emailer_steps": [...]}`. **Practical implication for Democles:** dispatch this function's sequence-creation step as `direct_api` (`POST /api/v1/sequences`). This previously read "even though the rest of the function uses `apollo_cli`," which described the pre-retirement design — the function's CLI steps are retired rather than an alternative surface, so the whole function is `direct_api` and there is no mixed surface left to warn about. The `403` above is kept because it explains *why* the CLI could never have carried this step.

**Response-shape gotcha — the created sequence's ID is NOT at the root of the response.** `POST /api/v1/sequences` returns its result wrapped under a top-level `emailer_campaign` key: the new ID is at **`.emailer_campaign.id`**, and a bare `.id` at root is legitimately `null` on a fully successful create. **This has caused a real duplicate-write incident:** a create was piped through `jq -r '.id'`, returned `null`, was misread as "nothing was created," and the `POST` was re-issued — producing two identical sequences, only one of which was reported. Read the ID from `.emailer_campaign.id`, and never infer failure from a missing root `.id`. (Note the parallel with `push_context_center_product`'s own response-shape gotcha above — same class of trap, different nesting.)

**Side effect observed, not configured explicitly:** the newly created sequence's response includes `"product_profile_ids": ["<the team's default Content Center product ID>"]` — Apollo appears to auto-associate a new sequence with the team's default Content Center product. Not something this function's payload sets; worth knowing so it isn't mistaken for a bug.

**Cleanup danger — sequences have no confirmed hard-delete.** A `DELETE` attempt on a real sequence ID returns `404`. A bare `PUT` with `{"archived": true}` is **not** a safe archive path, despite looking like one. Like `configure_workflow`'s `rule_action_configs`/`workflow_triggers`, `PUT /api/v1/sequences/:id` unconditionally rebuilds `emailer_steps` from `params[:emailer_steps]` with no fallback to the existing value — omitting it defaults to `[]` and 422s (`"At least one step is required for the sequence."`), but the record can be mutated before that validation failure fires, genuinely losing steps. Round-tripping only the surviving step's summary fields (`id`, `position`, `wait_time`, `wait_mode`, `type`) also fails — `"At least one template is required for a sequence step"` — because a full step object needs its nested `emailer_touches`/`emailer_template` content too, not just the summary fields `GET /api/v1/emailer_campaigns/:id` conveniently shows. No safe partial-update path has been found; archiving a test sequence via the Apollo UI, not the API, is the current recommended cleanup path until someone round-trips the full step+template payload successfully.

**Does not enroll contacts into a sequence.** Enrollment (`apollo sequences add-contacts`, backed by `emailer_campaigns_controller.rb`'s `add_contact_ids` path) requires `send_email_from_email_account_id` unconditionally — confirmed via the real controller (`emailer_campaigns_controller.rb:590-597`): a real `422` (`"Please specify a emailer_campaign_id and send_email_from_email_account_id."`) with no bypass, even for paused enrollment. SC Tailored Demo environments typically do not connect a mailbox at all, so this requirement can't be satisfied in the normal case — a structural mismatch with how these environments actually work, not a data gap on any one instance. This function stops at creating the sequence and the contact, both fully live and independent of mailbox connectivity — confirmed by reading the real create actions (`emailer_campaigns_controller.rb:286-347` for sequences, `contacts_controller.rb:307-520+` for contacts): neither references email accounts or sending infrastructure in any way. This function never calls `add-contacts`.

**Content dependency.** `sequences create` requires an `emailer_steps` array of actual email step content, authored strictly from already-verified deal facts with no invented claims, metrics, or customer names — this is not a reusable template; every deal needs its own real step content sourced from that deal's own verified facts. The real `emailer_step` schema is verified against source (not guessed): `type` (`auto_email`/`manual_email`/`call`/`action_item`/LinkedIn variants — `emailer_step.rb` `TYPE_ENUM`), `wait_time`/`wait_mode` (`minute`/`hour`/`day`), and nested `emailer_touches` with `type` (`new_thread`/`reply_to_thread` — this, not a `thread_id` or `same_thread` field, is the real threading mechanism) and `emailer_template` (`subject`, `body_html`). Authoritative source: `packs/email_messaging/app/services/sequences/unified/create_service.rb` and `packs/email_messaging/app/controllers/concerns/sequences/emailer_steps_helper.rb`/`emailer_touches_helper.rb`, corroborated by a real spec file (`create_service_spec.rb`). Content this grounded satisfies the No-Invention Rule.

**Critical — `auto_email` steps require `wait_mode` even when `wait_time: 0`.** Sending `emailer_steps[0]` as `{"type": "auto_email", "wait_time": 0, "emailer_touches": [...]}` (no `wait_mode`) gets a real `422`: `{"error":"Wait time must not be empty"}` — despite `wait_time` genuinely being present and set to `0`. Adding `wait_mode: "minute"` alongside `wait_time: 0` on that same first step succeeds with a real `200`. `wait_time` and `wait_mode` must be sent together on every `emailer_step`, including the first/immediate step — `wait_time: 0` alone is not sufficient, and the server-side validation error text ("Wait time must not be empty") is misleading, since a `wait_time` value was in fact present.

**Command/call sequence — `direct_api` throughout, revised 2026-07-28 (the CLI surface was retired; see the note below):**

1. **Duplicate pre-check — required only when the target sub-account may already hold records** (Mode B/C reuse in `SKILL.md`'s Step 6, i.e. a plan configuring an account from an earlier run). Search existing sequences via `direct_api` using the batch's own `api_key` before creating. **Skip this step entirely in Mode A** (a freshly provisioned sub-account is empty by construction, so a pre-existing duplicate is impossible) — the duplicate risk in Mode A is a *retry within the same batch*, which `agents/democles.md` Hard Rule 5 forbids outright rather than guards against here. **Never attempt this check via `apollo sequences search`:** the CLI authenticates as whatever account the operator's local session belongs to, never the target sub-account, so it would query the wrong instance and report "not found" every time — false confidence, worse than no check.
1. Create: `POST https://app.apollo.io/api/v1/sequences` or `https://api.apollo.io/api/v1/sequences` (`direct_api`), flat body `{"name": "<sequence name>", "emailer_steps": [...]}`. Never send `"active": true`. Read the new ID from `.emailer_campaign.id` — see the response-shape gotcha above.
   3-4. **Contact search/create — unavailable as documented, 2026-07-28.** These steps were `apollo_cli` only (`apollo contacts search` / `apollo contacts create`), and the CLI surface is retired for the reason in step 1: it cannot authenticate against the target sub-account. They were already conditional and are skipped in the normal case anyway (the `configure_workflow` pairing below is the standard path, since Layer 1 rarely surfaces a contact matching the prospect's own outbound persona). **Treat a plan that genuinely requires a pre-enrolled named contact as Blocked** and surface it to the SC, rather than reaching for the CLI. A `direct_api` contact-create path is not yet documented here — if one is needed, source and verify it first, then add it.

**Sample-contact policy: no fake or placeholder contacts, ever.** Steps 3-4 need a real name/email/organization to populate. **Always use a real contact that matches one of the prospect's personas** — an existing deal contact, or another real stakeholder already surfaced in Layer 1 output whose role matches a persona built for this account. Never fabricate a name, email, or contact record, and never use a placeholder domain like `demo.contact@<prospect-domain>`. No separate PII-specific approval ask is needed beyond the normal approval draft review — the literal contact used is already part of what the SC sees and approves per Approval Gate Rule 2.

**If Layer 1 output doesn't surface a real contact matching any built persona, this is not a dead end — pair with `configure_workflow` instead of staying Blocked.** Sourcing a fresh, unrelated real person from Apollo's own database to satisfy steps 3-4 was considered and rejected — it would spend a real lead/export credit and commit a real stranger's PII to the demo instance merely to populate a step that (per the note above) was never actually enrolling anyone via the API anyway. The real fix: skip steps 3-4 entirely and propose a companion `configure_workflow` action instead — `filters` scoped to the same persona's own filter criteria (same taxonomy, reusable directly — confirmed via `searchSignalAllowedFilters.yml`/`validations.rb`), `object_type: "Contact"`, a `workflow_triggers` entry (e.g. `contact_created`, `constraints: {}` — the simplest, safest choice absent a Recommended-Demo-Flow-specific reason to pick another), and a `rule_action_configs`/`nodes` action of type `add_contact_to_sequence` (`emailer_campaign_id` = the sequence Democles already created in steps 1-2, `email_account_id` per that action's own documented required-field rules above) — plus the standing `type: "workflow"`, `active: false`, and `approval_type: "manual"` defaults every `configure_workflow` payload already carries. This mirrors Apollo's own documented account-based-sales-motion pattern (`knowledge.apollo.io` "Workflows Overview": *"automatically surface the right contacts and add them to sequences"*) — the workflow's own `filters` dynamically match whoever qualifies when it actually runs, so no specific contact needs to be pre-identified, no credit is spent, and no stranger's PII is committed at build time. Because `active: false` is already the standing default, this stays fully inert until the SC explicitly activates it — that's the SC's own choice and own credit spend, made live if they choose to demo it running, not something this automation layer decides during setup. **Confirmed live end to end** — see `add_contact_to_sequence`'s entry above for the full result. This pairing is a live-confirmed proposal, not just a source-grounded one. **Only fall back to Blocked** if the deal's Recommended Demo Flow specifically calls for a populated, ready-to-view sequence with a named contact already enrolled (something the workflow pairing cannot produce, since it stays inert by design) — that narrower case still has no real-contact-without-cost solution and should surface to the SC as a stated gap.

**On CLI vs. MCP — moot for execution as of 2026-07-28.** The KR2 one-pager's token-economics note (~8-30K tokens via CLI vs. ~70-200K via MCP for a 10-call workflow) is why the CLI was preferred over MCP originally, and it remains a real argument for CLI adoption generally. It no longer applies to this automation layer: Democles calls `direct_api` directly, which is cheaper than both and is the only surface that can authenticate against a freshly provisioned sub-account. The CLI-adoption proof point is still worth making in a demo — just not through this execution path.

**Contact deletion confirmed live.** The Apollo CLI's `contacts` command has no `delete`/`archive` subcommand (`create`, `update`, `search`, `bulk-create` only), but `DELETE /api/v1/contacts/:id` via `direct_api` works — real `200` with `{"contact":{"id":"...","deleted":true}}`. If a mistakenly created test contact needs removing and Democles is ever given `direct_api` scope for it, this is a real hard-delete, not an archive.

______________________________________________________________________

## Noted for future leverage — not required for the initial demo

### `generate_emailer_template_content` (not wired to Democles, not built)

| Field | Value |
|---|---|
| Endpoint | `POST /api/v1/generated_emailer_template_content` (create the generation request), `GET /api/v1/generated_emailer_template_content/:id` (fetch the result) |
| Proposed by | Not yet — a possible future fix for `stage_demo_sequence`'s email-step content gap |
| Executed by | Not yet wired to Democles |
| Execution surface | `direct_api` (presumed — not yet live-tested) |
| Status | **confirmed to exist via source only** (`leadgenie-master`, `packs/ai-messaging/app/controllers/api/v1/generated_emailer_template_content_controller.rb`) — not yet called live against any Apollo instance |
| Approval gate | would be required, same as every other function, if this ever gets built |

Apollo has no AI-Assistant-thread-based path for drafting full sequences from natural language — no backend endpoint generates multi-step sequence structure from prose. This endpoint is the real, narrower capability that exists instead: it generates a single email's `subject` + `body` from a prose prompt (`EmailTemplateGenerationPrompt`), the same draft-only pattern as `generate_personas_fallback` above — it returns a suggestion, it does not persist into a live sequence or send anything. Using it for `stage_demo_sequence` would mean one call per intended sequence step, each with its own prose description of that step's intent, then assembling the results into the `emailer_steps` array for the actual sequence-creation call — **`direct_api` `POST /api/v1/sequences`, not the CLI's `apollo sequences create`, which is confirmed broken for this identity** (a real `403`, see the mixed-execution-surface note above).

**Not a requirement for the initial demo.** Recorded here so it isn't lost, not as a build task. If picked up later: confirm the real request/response shape and async generation mechanics live before relying on it, the same way every other function in this registry was verified before being marked active — a source read confirms the endpoint exists, not that its exact contract matches what's assumed here.

______________________________________________________________________

## Exists in Apollo, not yet flag-exposed for partner use — commented out, not built

These are represented here so the architecture is honest about what's designed-in vs. actually live. Do not attempt to call these — they will fail or are not partner-safe yet.

```yaml
# create_or_get_sub_account_api_key:
#   endpoint: api/v1/api_keys
#   status: commented_out
#   blocker: godmode/impersonation restriction — a parent or internal user can't mint a
#            key in a child account. Needs the Apollo CLI multi-account/alias workstream
#            before this can be uncommented, not just a flag flip.
```

If `create_or_get_sub_account_api_key` gets flag-exposed, uncommenting is a quick edit here plus a matching addition to Democles's tool scope — not a redesign.

## No partner-safe endpoint exists at all — not represented as functions

**Sub-account creation itself is no longer in this category.** `api/v1/teams/create` is still `disallow: api` and remains genuinely inaccessible via that route, but a dedicated endpoint now exists and is confirmed live: `POST /api/v1/teams/provision_demo_account_with_api_key` creates a new demo sub-account and mints its API key in one call. It is deliberately **not** represented as a Democles-dispatchable function in this registry — by design, `demo-instance-configuration` calls it directly, via two bundled scripts, as its own final workflow step, before Democles is ever dispatched. See that skill's own `SKILL.md` (`Provisioning the Demo Sub-Account`) for the actual mechanism; this registry's scope stays limited to functions Democles executes.

The one item genuinely still in this category is **minting an API key for an already-existing sub-account, independent of creating one** — see `create_or_get_sub_account_api_key` in the section immediately above, still blocked by the godmode/impersonation restriction. That's a different capability from the provisioning endpoint above, which only ever mints a key for a team it creates in the same call.
