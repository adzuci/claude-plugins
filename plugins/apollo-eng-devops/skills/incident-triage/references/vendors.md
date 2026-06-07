# Vendor Recognition Index

The fastest way to triage many INCIDENT tickets is to recognize the upstream system involved before doing any investigation. This file is the curated list of vendors and external systems Apollo connects to that have either generated INCIDENT tickets in the past six months or are commonly referenced in PD alerts / Sentry / trace data.

**Use this file for recognition, not investigation.** When a ticket mentions a vendor name, host, exception class, or characteristic error shape from below, jump to the entry and apply the routing + known-trap. Skip ahead in the workflow.

**Coverage scope**: ~mid-size. Not exhaustive — common-enough to recognize, narrow enough to keep accurate. If a recognition signal is missing, add an entry via `contributing.md` rather than guessing.

For internal Apollo tools (Pantheon, Apollo Agent, jira-bot, etc.), see [`internal-tooling.md`](internal-tooling.md). Those aren't vendors.

## Shifter.io

- **What**: residential proxy / VPN network used for outbound search-engine scraping (Google/Yahoo for LinkedIn profile/company lookups).
- **Recognize**: hosts `*.p.shifter.io` (`ares`, `cronos`, `epimetheus`, `hephaestus`, `prometheus`, `poseidon`, `atlas`, `apollo`, `pallas`, `zeus`, etc.) in `span.net.peer.name`. Exception text `"Something is wrong with VPN setup"` or `Net::HTTPClientException: 403 "Forbidden"`.
- **Code paths**: `packs/crawlers/app/workers/crawler/search_engine_linkedin_person_updater_worker.rb`, `packs/crawlers/app/workers/crawler/search_engine_linkedin_person_enqueuer.rb`, sibling `*_yelp_*` and `*_linkedin_*` workers.
- **Owner**: `@apolloio/native-data` (per CODEOWNERS `packs/crawlers`).
- **Known failure shapes**:
  - `403 Forbidden` on outbound. Code wraps as `RuntimeError("Something is wrong with VPN setup. 403 \"Forbidden\"")`. **The exception name is misleading** — the VPN setup is usually fine; the real cause is one of (a) Shifter blocked our IP rotation due to volume, (b) target site (Google/Yahoo/LinkedIn) blocked the residential IP and Shifter passed the 403 through, (c) Shifter account/quota hiccup.
  - Bursty error rates that self-recover in 10–30 minutes are the signature of (a) or (b).
- **Triage trap**: do not assume upstream outage before checking *our* outbound rate. Pull `rate({span.net.peer.name=~".*shifter\\.io"})` from Tempo for the incident window — if Apollo's rate is 10–100× baseline, we caused it. Baseline is roughly 3–7 req/s combined across all `*.p.shifter.io` hosts.
- **Past incidents**: INCIDENT-29534, 29054, 28316, 28094, 27737, 27761, 27762.

## Redis Cloud (Redis Enterprise)

- **What**: managed Redis cluster Apollo uses for cache + ratelimiter buckets.
- **Recognize**: cache keys like `remaining_<credit_type>s_<team_id>` (export credits guard), `ratelimit:*`, `slowlog` saturation alerts on the ratelimiter database. Metric prefix `bdb_*` (Database Status Dashboard in Grafana). Span attribute `db.system="redis"` with `db.redis.database_index` set.
- **Code paths**: `packs/billing/app/helpers/api_credit_helper.rb` (`Rails.cache.fetch` against the `remaining_export_credits_*` key family), `packs/util/lib/zp_redis/rate_limiter.rb`, `packs/util/lib/redis_connection.rb`, `packs/util/lib/redis_utils.rb`.
- **Owner**: `@apolloio/devops` owns the cluster + connection primitives (`redis_connection.rb`, `redis_utils.rb`). `@apolloio/be-platform` owns the rest of `packs/util/lib/zp_redis/*`. Note the CODEOWNERS entry for `rate_limiter.rb` → `@apolloio/native-data` is **stale** (no native-data engineer has touched it in 90+ days; recent commits are be-platform).
- **Known failure shapes**:
  - Slowlog saturation at the 12ms threshold rarely means an active problem — it's a fixed-size ring buffer and a single slow command can sit there for hours.
  - `INCRBY` latency >10ms typically indicates hot-key contention on a ratelimiter bucket (one tenant hammering the same key).
  - `remaining_export_credits` cache returning 0 with stale TTL → triggers `guard_for_sufficient_api_credits` 422s for an entire team for up to 1 hour.
- **Triage trap**: aggregate `redis_commands_latencies_usec_bucket` percentiles can look fine (μs range) even when the slowlog has 128 entries above 12ms. Look at p99.9 or p99.99 and the raw slowlog before concluding "Redis is healthy."
- **Dashboards**: `[Infra] Redis` folder in Grafana (`Zrko4CovK` Database Status, `UjCh-Ya4K` Cluster Status, `ADTcdjT4K` Node, `OLAsUMAVz` Shard).

## MongoDB Atlas (Apollo Mongo clusters)

- **What**: sharded MongoDB clusters for primary data — main, contacts, email, noncustomer, search-mongo-queries, etc.
- **Recognize**: hosts `mongos-<cluster>-N.us-central1-c.c.indigo-lotus-415.internal` in `span.net.peer.name` (e.g. `mongos-main-5`, `mongos-contacts-3`, `mongos-email-4`). Spans named `users.find`, `<collection>.aggregate`, etc. with `db.system="mongodb"`. Alerts shaped `[FIRING:N] Mongos to shards connection - health not okay [INFRA] MongoDB`.
- **Owner**: `@apolloio/devops` (cluster ops, sharding config, index management). Models live in many packs; the owning pack writes Mongoid schema, but **prod index lifecycle is DevOps**.
- **Known failure shapes**:
  - Index drift between code-declared `expire_after_seconds` (or other index options) and prod-applied values. Detected by `packs/mongo/spec/mongo_validations_spec.rb`, surfaces as a "[BE] Failed Test" ticket — the failure looks like a flaky test but is a real prod-vs-code mismatch.
  - "Mongos to shards connection — health not okay (empty means safe)" alert is recovery-shaped — it fires when the health array becomes non-empty, then resolves quickly when shards reconnect. Auto-resolves are normal.
  - 47ms `users.find` on a single shard is the auth/session lookup; if the session-auth path looks slow, look here.
- **Triage trap**: a `packs/mongo/spec/...` failed-test ticket is **not** flaky if the description quotes "X property does not match between code and production" — that's a real index drift; route to DevOps, close any Pantheon flaky-bot PR. See `internal-tooling.md`.
- **Past incidents**: INCIDENT-29537 (HabitActivationEvent TTL drift), 29450 (Mongos health alert).

## Cloudflare

- **What**: edge proxy, DNS, WAF for `app.apollo.io` and `api.apollo.io`.
- **Recognize**: alerts shaped `[FIRING:1] High 5XX error count [Infra] Cloudflare`, `Request Errors Count [Infra] Cloudflare`, `High Errors from Cloudflare Tunnel Pods`. `cf-ray` headers in trace data. `Cloudflare ray 9f...-CMH` references in incident comments.
- **Owner**: `@apolloio/devops`.
- **Known failure shapes**:
  - 5XX bursts from CF are usually downstream (Apollo origin) failing — start at our error rate, not CF status.
  - "Cloudflare Tunnel Pods" alerts are about Apollo's Argo Tunnel pods, not CF itself — these are DevOps-owned k8s workloads.
- **Past incidents**: INCIDENT-29126, 28888, 28847.

## PagerDuty

- **What**: incident response platform. Receives alerts from Grafana, Sentry, custom integrations.
- **Recognize**: any ticket reporter `PagerDuty` or URLs containing `pagerduty.com/incidents/`. Service IDs map to teams via `apollo-dev-teams.yml` `pagerduty.sentry_pd_service_id` and `pagerduty.pagerduty_high_priority.service_name`.
- **Owner**: cross-cutting — each team owns its own service config.
- **Tooling note**: PagerDuty MCP is **required** for `pd-reconcile` mode and strongly recommended otherwise. See `pd-alerts.md` for reconciliation rules.
- **Triage trap**: PD ack on Slack does **not** propagate to Jira assignee. Many tickets have PD responders but unassigned Jira — batch these and propose assignment in one round-trip. See SKILL workflow.

## Grafana Cloud (Prometheus / Tempo / Loki / Mimir)

- **What**: observability stack — metrics in Prometheus (`grafanacloud-prom`), traces in Tempo (`grafanacloud-traces`), logs in Loki (`grafanacloud-logs`), long-retention in Mimir.
- **Recognize**: alert ticket descriptions reference `apolloio.grafana.net` URLs (alert rule UID, silence link, dashboard, panel). Grafana folder tags in titles: `[Infra]`, `[Growth]`, `[Engagement]`, `[APM & Traces]`, etc.
- **Owner**: `@apolloio/devops` for the infra; alert ownership is per-team via `grafana_folder` label.
- **Tooling note**: Grafana MCP enables Tempo TraceQL queries, Prometheus metric queries, dashboard fetches, and Loki log queries. **The skill must check this at preflight** — many investigation paths collapse from "ask the user to look" → "fetch the rate inline" when Grafana is available.
- **Investigation cheap-vs-deep gate**:
  - Cheap (auto-fetch ok): `rate()` queries over a defined window, single histogram quantile, dashboard summary, single trace lookup by ID.
  - Deep (ask y/n first): multi-query trace searches, log scans, exemplar walking, Sift investigations.

## Sentry

- **What**: error tracking. Apollo has multiple Sentry projects (`rails-backend`, `sidekiq`, `react`).
- **Recognize**: `sentry_pagerduty_alert_projects` config in each team's `apollo-dev-teams.yml` entry. PD alerts created by Sentry integrations.
- **Owner**: per-team for project configuration; `@apolloio/devops` for the Sentry account itself.
- **Triage step**: if a PD alert routed to your team mentions Sentry but the ticket gives no Sentry URL, ask the reporter for the issue link — guessing on partial stack traces is rarely productive.

## Knapsack Pro

- **What**: RSpec test parallelization service.
- **Recognize**: `knapsack_pro` gem references, `.knapsack_pro_node_*.json` files, `Knapsack node N/M` in failure messages. Failed-test ticket descriptions reference `https://github.com/apolloio/leadgenie/actions/runs/<id>` and CI job names like `Rspec (34, 29)`.
- **Owner**: `@apolloio/be-platform` (test infra).
- **Known failure shape**: cross-spec pollution that only manifests on specific Knapsack node assignments (one spec mutates persisted state, a later spec asserts against it). The Pantheon flaky-bot is usually correct about these — look at its proposed diff before dismissing. See `internal-tooling.md`.

## MongoDB connection — Mongoid driver-side (separate from cluster)

- **What**: Mongoid ORM behavior in `packs/mongo/*`, validators, index management code paths.
- **Recognize**: spans named after Mongoid model methods, `Mongoid::*Error` exception classes, files in `packs/mongo/`.
- **Owner**: `@apolloio/be-platform` owns the `mongo` pack scaffolding. **But model files in `packs/<x>/app/models/` belong to the owning pack's team** (e.g. `HabitActivationEvent` lives in `packs/onboarding` → owned by onboarding team). When a model-specific issue surfaces, the model's pack owner is the right route, not be-platform.

## Customer.io / Slack webhooks (HMAC-signed inbound)

- **What**: third-party services that POST to Apollo endpoints with HMAC-signed payloads.
- **Recognize**: security findings mentioning "non-constant-time HMAC", paths like `packs/<x>/app/controllers/api/v1/<service>_webhook_controller.rb`.
- **Owner**: per-webhook — Customer.io webhook owned by Marketing/Comms BE, Slack workflow webhook owned by Apollo Intelligence team. Resolve via CODEOWNERS for the controller path.
- **Past incidents**: INCIDENT-28989 (Customer.io HMAC), 28990 (AI Assistant Slack signature), 28991 (Slack workflow webhook).

## Recall.ai / Zoom (conversation intelligence)

- **What**: Recall.ai is the meeting-recording / transcription vendor; Zoom is one of the calendar integrations.
- **Recognize**: Svix webhook signature paths, conversation-intelligence pack references, `recall_ai_*` or `zoom_*` integration code.
- **Owner**: `@apolloio/conversation-intelligence`.
- **Past incidents**: INCIDENT-28996 (Recall.ai/Zoom Svix webhook HMAC).

## Gong (Conversation Insights)

- **What**: third-party call recording / sales intelligence integration.
- **Recognize**: Gong API rate-limit errors (`Gong::RateLimitError`), `low priority sidekiq conversation-intelligence` queue alerts.
- **Owner**: `@apolloio/conversation-intelligence`.
- **Past incidents**: INCIDENT-28909.

## Salesforce SOAP/REST APIs

- **What**: outbound CRM sync.
- **Recognize**: tickets mentioning Salesforce SOAP API version (e.g. `v64`, `v66`), `Restforce::*` errors, paths in `packs/crm_integration/`.
- **Owner**: `@apolloio/integrations`.
- **Past incidents**: INCIDENT-29439 (SOAP version upgrade).

## Microsoft Dynamics / HubSpot

- **What**: other CRM integrations.
- **Recognize**: paths in `packs/crm_integration/`, integration class names.
- **Owner**: `@apolloio/integrations`.

## Intercom (inbound support tickets)

- **What**: Apollo's support stack — tickets created in Jira from Intercom conversations.
- **Recognize**: reporter `Service Account Jira Intercom`. Tickets are customer-facing reports, often missing technical detail.
- **Triage step**: treat as Customer-report class. If the description doesn't name a service or include repro, propose `ask-reporter` rather than guessing.

## Stripe

- **What**: billing / payments.
- **Recognize**: paths in `packs/billing/`, `Stripe::*` errors, customer reports about credit card / subscription flows.
- **Owner**: depends on the specific surface — `@apolloio/billing` for core, `@apolloio/growth-pricing-and-packaging-be` for upgrade flows, sometimes `@apolloio/deals-intelligence` (post-CRM-Platform merge) for invoicing-adjacent stuff.

## New Relic

- **What**: Apollo Data Platform uses New Relic alongside Grafana for some service alerts (`Data Platform Alert Policy` PD service).
- **Recognize**: PD service `Data Platform Service`, alert text mentioning New Relic integration IDs.
- **Owner**: `@apolloio/data-platform`.

## Glean

- **What**: enterprise search / knowledge platform (also an MCP this skill uses).
- **Recognize**: this skill consumes Glean MCP for runbook + Notion lookups. End-users don't usually file Glean-related INCIDENT tickets.
- **Tooling note**: required for the `triage` mode workflow (runbook + reachability checks).

## Notion

- **What**: Apollo's documentation. Most runbook URLs live here.
- **Recognize**: links to `apolloio/...` Notion pages.
- **Triage step**: when a Notion URL appears in a ticket description, do not paraphrase — cite it verbatim. If you can't fetch the page (no Notion MCP), say so and rely on the ticket text.

## What's NOT in this file

- **Pantheon, Apollo Agent, jira-bot, Apollo DevOps Bot** — internal Apollo tools. See [`internal-tooling.md`](internal-tooling.md).
- **Security scanners (Kodem, Orca, Bugcrowd, Panther, claude-security)** — see [`finding-sources.md`](finding-sources.md). They're not "vendors" in the sense this file uses; they're sources of security findings with their own routing rules.
- **GitHub, Atlassian (Jira/Confluence)** — assumed available, not failure-prone enough in this workflow to warrant entries.
