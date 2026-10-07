# Slow Query Triage — Steps

Companion to `SKILL.md`. Work top to bottom. Each step is tagged:

- **[AUTO]** — runs in this session. Sentry + PagerDuty creds are proxy-injected.
- **[ADVISORY]** — Grafana / New Relic / Mongo shard reads are usually egress-blocked here. Emit as human-run commands; mark any conclusion drawn from them unverified.
- **[HUMAN]** — judgement or a mutation this skill must never make on its own.

**Data-corruption guardrail:** the kill/no-kill call on a live op is **[HUMAN]** and must never be automated. `MongoQueryKiller` can abort a query mid-write. This skill only *reports* `kill_attempted` / `kill_succeeded` from metadata that already exists.

## Step 1 — Fetch and digest · [AUTO]

Input: a Sentry short-id (`RAILS-BACKEND-*`), a PD incident id (`Q...`), or pasted alert text.

```bash
python3 scripts/slow_query_report.py --fetch \
  --sentry-short-id RAILS-BACKEND-4FA7 --pd-incident Q25ND367948EA8 \
  --bundle-out /tmp/sq.json --mode triage
```

The script resolves the short-id via the shortids endpoint (a bare `?query=<short-id>` returns `[]`), pulls the issue's events and the deploys for its first release, fetches the PD incident, and prints the digest. It uses the canonical `sentry.io` host; the regional `apolloio.sentry.io` subdomain is egress-denied from remote sessions.

Re-run against the saved bundle instead of re-fetching:

```bash
python3 scripts/slow_query_report.py --bundle /tmp/sq.json --mode deep
python3 scripts/slow_query_report.py --bundle /tmp/sq.json --format html --out /tmp/report.html
```

If the fetch fails, the script says so and exits non-zero. **Say the fetch failed and ask for a bundle — never fill the gap with plausible-looking values.**

**Read the digest, not the bundle.** The bundle is megabytes; the digest is ~40 lines and already contains every field below.

### Op metadata

Source: the latest Sentry event's `context` object, emitted by `packs/mongo/app/public/mongo_query_killer.rb` (`MongoQueryKiller`; slow-query message built ~line 756). Event `tags` carry only `area` / `environment` / `server_name` — none of the op fields. Absent fields are reported as `absent`, never inferred.

| context key | example (2026-08-13) | why it matters |
| --- | --- | --- |
| `source` | `Api::V1::AccountsController/show` | where the op was issued — the primary origin signal |
| `collection` | `contacts` | what to check the shard key on |
| `filter` | `{"account_id":{"$in":["60c3755581a12e00019664bf"]}}` | compare its keys to the shard key |
| `signature` | `query:contacts:account_id` | groups events into one logical query |
| `secs_running` | `71.61684` | severity, and the op's start time (`sampled_at − secs_running`) |
| `opid` | `contacts-16:-819763575` | shard is the prefix before `:` — **no standalone `shard` field** |
| `plan_summary` | `IXSCAN { account_id: 1 }` | indexed but still fanning out — a mismatch, not a missing index |
| `kill_attempted` | `false` | did the killer act |
| `kill_succeeded` | `false` | data-corruption risk only if a kill ran |

## Step 2 — Prove or disprove fan-out · [AUTO]

The old failure mode was calling anything multi-shard a scatter-gather. Many shards *over an hour* can be sequential retries; many shards *at one instant* cannot be. The script reconstructs each op's window as `[sampled_at − secs_running, sampled_at]` and counts distinct shards live at the same moment.

| Verdict | Rule | How to report it |
| --- | --- | --- |
| `proven` | ≥2 distinct shards running the same `signature` at one instant | State the instant and the shard list — this is the evidence |
| `likely` | ≥2 distinct shards across events, no overlapping windows | Say fan-out is *likely*; sequential execution is not excluded |
| `single-shard` | every event on one shard | Not a fan-out. Look at volume, plan, and document size instead |
| `unknown` | no `opid` on any event | Say shard attribution was unavailable |

Never upgrade the verdict in prose. `likely` is not `proven`.

## Step 3 — Attribute the origin · [AUTO]

Who ran the query determines the fix. Signals are checked in priority order — `source` first, since it is the killer's own attribution — then `appName`, `transaction`, `server_name`, `client`.

| Origin | Signals | What it means | Where the fix lives |
| --- | --- | --- | --- |
| `user-request` | `*Controller#action`, `puma`, `web-*` host | A customer was waiting; timeout risk | Query shape, index, or move off the request path |
| `background-job` | `*Worker`, `*Job`, `sidekiq-*` host | Queue backup and retry storms, not user latency | Batching, concurrency limits, idempotency |
| `scheduled` | `Clockwork`, `*Cron*`, `Scheduler` | Predictable and repeatable | Move off-peak, chunk, or precompute |
| `manual-console` | `rails runner`, `rake`, `console`, `irb`, `mongosh` | A human ran it by hand — usually a backfill | **Runbook and alert routing, not necessarily code** |

Confidence: `high` when a second signal agrees, `low` when one contradicts the first, `medium` on a lone signal, `none` when nothing matches. Report the confidence and the signals — a `low`-confidence origin should not drive a ticket on its own.

**The manual-console case matters most.** A hand-run backfill that pages on-call is an alerting and process problem. Opening a code bug against the controller is the wrong outcome.

## Step 4 — Correlate deploys · [AUTO]

The script compares the issue's `firstSeen` against the deploys for its release (Sentry `/releases/<version>/deploys/`), inside a 120-minute window, and splits event volume across the deploy boundary.

| Verdict | Rule | What to do |
| --- | --- | --- |
| `deploy-correlated` | Onset within the window **and** the issue's first release *is* that deploy | Read the diff first; a revert may beat tuning. Raises proposed severity |
| `deploy-adjacent` | Onset within the window, release provenance unknown | Timing only — worth a look, not a conclusion |
| `pre-existing` | Issue first appeared in an earlier release, or onset is outside the window | Not a regression. A structural fix is the path |
| `no-deploy-data` | No deploy records | Say deploy correlation was not evaluated |

## Step 5 — Confirm the shard key · [ADVISORY], delegate

Until a real shard key is confirmed, the digest reports the pattern as **`multi-shard fan-out`** with `provisional` confidence and marks severity provisional. It only says **`scatter-gather`** when a confirmed shard key is absent from the filter *and* fan-out is `proven` or `likely`.

Delegate to `apollo-eng-devops:mongo-specialist`, or emit for a human:

```javascript
// human-run in a Mongo shell against the config db — read-only
sh.status()
db.getSiblingDB("config").collections.findOne({ _id: /contacts$/ }, { key: 1 })
```

Then re-run so the classification upgrades on evidence, not on prose:

```bash
python3 scripts/slow_query_report.py --bundle /tmp/sq.json \
  --shard-key team --shard-key-source mongo-specialist --mode deep
```

`--shard-key-source unconfirmed` or `assumed` keeps the finding provisional on purpose.

### Severity matrix

| Classification | Proposed severity |
| --- | --- |
| fleet + recurring + structural | high |
| single-account + recurring + structural | medium |
| single-account + one-window + structural | low |
| no structural cause established | low |

Modifiers: `kill_succeeded=true` raises one level and flags a data-integrity check · `deploy-correlated` raises one level · a `manual-console` one-off on a single account floors at low and is tagged an alert-tuning candidate. Provisional whenever the shard key is unconfirmed. Urgency is not severity.

## Step 6 — Kill decision · [HUMAN] only

Never automate. If a live op might be killed, surface the facts and hand off:

```text
Live op still running?  runtime=<s>  shard=<shard>  kill_attempted=<bool>  kill_succeeded=<bool>
Killing a mid-flight write can corrupt data. Human decision only.
Playbook: https://app.notion.com/p/apolloio/Runbook-Query-Killer-Slow-Queries-Playbook-1baab2b3b49680a98f84fce8f6b3e9af
```

## Step 7 — Recommend, draft, route · [AUTO] draft, [HUMAN] files

The digest ranks fixes from [`remediation.md`](remediation.md), emitting only the tiers whose preconditions actually hold. Read that file before arguing with the ranking.

In `deep` mode the script also drafts the ticket. Route it by delegating a CODEOWNERS read for the `<Controller>` path in `apolloio/leadgenie` and naming the owning team. A human files and reassigns.

### Human-run observability · [ADVISORY] (usually egress-blocked)

Hand these back verbatim; do not claim to have run them.

- Grafana: slow-query / Mongos dashboards for the shard and time window.
- New Relic: transaction trace for the controller action over the burst window.
- Log router: the `SampleMainMongosSlowQuery` sink (`apolloio/devops` → `terraform/gcp/prod/log-router.tf`) for raw slow-query samples.

## Ground-truth example (2026-08-13)

> The IDs below (account `60c3755581a12e00019664bf`, PagerDuty `#889201` / `Q25ND367948EA8`, Sentry `RAILS-BACKEND-4FA7`) are REAL historical values from the 2026-08-13 production incident — not synthetic or anonymized — so a future maintainer can safely update or remove them. `tests/fixtures/incident-2026-08-13.json` reconstructs per-event timing to that shape for tests and demos, and labels itself as reconstructed.

`Q25ND367948EA8` (#889201, `be-platform-low-priority`, Low urgency) → Sentry `RAILS-BACKEND-4FA7` (numeric issue `7670017484`). 465 events, `14:18:08Z`–`15:26:58Z`. A `contacts` lookup from `Api::V1::AccountsController/show` (`signature: query:contacts:account_id`), scoped to one account, `71.6s`, latest event on `contacts-16`, fanning across `contacts-16/19/27/28`, `plan_summary: IXSCAN { account_id: 1 }`, `kill_attempted=false`, `kill_succeeded=false` → no data-integrity risk.

Digest output: origin **user-request** (high — `source` and `server_name` agree), deploy **pre-existing** (the issue's first release predates the deploy that preceded onset), fan-out **proven** (4 shards on the same signature at one instant), pattern **multi-shard fan-out / provisional** until `--shard-key team` is supplied, then **scatter-gather / high**. Proposed severity **low** — one large tenant, one window. Ticket: log the anti-pattern against `Api::V1::AccountsController#show`, propose a team-scoped filter, route to CODEOWNERS, file by hand.
