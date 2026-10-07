---
name: slow-query-triage
description: Manual-invocation only. Triage a Query Killer slow-query alert — prove shard fan-out, attribute the op to a user request or a hand-run script, correlate against deploys, and propose ranked fixes. Run via /apollo-eng-devops:slow-query-triage.
argument-hint: Sentry short-id, PagerDuty incident id, or paged alert text (e.g. RAILS-BACKEND-4FA7, Q25ND367948EA8) [--deep] [--html]
disable-model-invocation: true
---

# Slow Query Triage

[Query Killer Slow-Queries Playbook (Notion)](https://app.notion.com/p/apolloio/Runbook-Query-Killer-Slow-Queries-Playbook-1baab2b3b49680a98f84fce8f6b3e9af) · killer: `packs/mongo/app/public/mongo_query_killer.rb` (`MongoQueryKiller`) · sinks: `kill-slow-queries` in `config/environments/{production,staging}.rb` · alert service: `be-platform-low-priority`

A slow-query page asks two separate questions. **"Should this live op be killed?" is human-only — aborting a mid-flight write risks data corruption, so this skill never makes, scripts, or recommends auto-invoking that call.** This skill answers the other question: **why was the op slow, who or what ran it, and what should change so it stops paging.**

Three facts decide the answer, and the skill establishes each with evidence rather than assumption:

1. **Did it actually fan out?** Many shards over an hour can be sequential retries. Many shards *at the same instant* cannot. Only the second is proof.
1. **Who ran it?** A customer request, a queued worker, a cron, or an engineer in a console are four different problems with four different fixes. A hand-run backfill is usually not a product defect.
1. **Did a deploy cause it?** If onset follows a release that first introduced the issue, a revert may beat any query tuning.

`scripts/slow_query_report.py` computes all three deterministically so the agent never reads raw Sentry payloads. **[`references/triage-steps.md`](references/triage-steps.md)** is the source of truth for the calls, field tables, and evidence ladders; **[`references/remediation.md`](references/remediation.md)** is the fix menu.

## Modes

| Mode | Cost | What it adds | Use when |
| --- | --- | --- | --- |
| `triage` (default) | one script run, no subagents | Verdict, origin, deploy correlation, fan-out proof, proposed severity, kill-state facts, top 3 fixes | You are paged and need the call now |
| `deep` | adds shard-key + CODEOWNERS subagents | Full remediation ladder, per-shard evidence, drafted ticket, owning team, human-run observability commands | Post-incident review, a recurring pattern, or you are writing the ticket |

Start in `triage`. Escalate to `deep` only when the finding will turn into a ticket or the pattern repeats.

## Usage

```bash
/apollo-eng-devops:slow-query-triage RAILS-BACKEND-4FA7            # triage, markdown in-thread
/apollo-eng-devops:slow-query-triage Q25ND367948EA8 --deep         # full ladder + drafted ticket
/apollo-eng-devops:slow-query-triage RAILS-BACKEND-4FA7 --html     # same report as a standalone HTML file
```

## What this skill can and cannot touch

- **Sentry + PagerDuty** — creds are proxy-injected; the script fetches directly (org `apolloio`). Use the canonical `sentry.io` host — the regional `apolloio.sentry.io` subdomain is egress-denied from remote sessions. If the fetch fails, say so and ask for a bundle rather than inventing data.
- **Grafana / New Relic / Mongo shard reads** — usually egress-blocked. Emit these as exact human-run commands; **never claim to have run them.** Confirm a shard key via `apollo-eng-devops:mongo-specialist`, not by guessing.
- **Jira / Notion** — connectors unauthorized here. **Draft** the ticket as text; do not open one.

## Workflow

1. **Fetch and digest — [AUTO].** Run the script; it resolves the alert, pulls the issue, its events, its release deploys, and the PD incident, then prints a compact digest. Read only that digest. See references/triage-steps.md Step 1.
1. **Prove or disprove fan-out — [AUTO].** The digest reports `proven` (≥2 shards running the same signature at one instant), `likely` (multiple shards, no overlap), `single-shard`, or `unknown`. **Report the verdict you were given — do not upgrade it in prose.** See Step 2.
1. **Attribute the origin — [AUTO].** `user-request` / `background-job` / `scheduled` / `manual-console`, with a confidence and the signals behind it. This changes the fix, the severity, and whether it should page at all. See Step 3.
1. **Correlate deploys — [AUTO].** `deploy-correlated` / `deploy-adjacent` / `pre-existing` / `no-deploy-data`, with the nearest prior release and the lag. Correlated means check the diff before tuning anything. See Step 4.
1. **Confirm the shard key — [ADVISORY], delegate.** Until a real shard key is confirmed the digest says "multi-shard fan-out", not "scatter-gather", and marks severity provisional. Delegate confirmation to `apollo-eng-devops:mongo-specialist` and re-run with `--shard-key`. See Step 5.
1. **Kill decision — [HUMAN] only.** If a live op might be killed, stop and hand it over with runtime, shard, and `kill_attempted`/`kill_succeeded`. This skill has no kill path and must not grow one. See Step 6.
1. **Recommend and draft — [AUTO] draft, [HUMAN] files.** The digest ranks fixes from the ladder in references/remediation.md, gated on the facts actually established. In `deep`, add the drafted ticket and route via CODEOWNERS. A human files it. See Step 7.

## Keeping context small

The whole point of the script is that a 465-event Sentry issue never enters the conversation.

- **Never read the raw bundle.** Run the script and read its output. `--format json` if you need to branch on a field; `--format md` otherwise.
- **Delegate anything with a big payload to a subagent** and require a short return value:

| Work | Delegate to | Must return |
| --- | --- | --- |
| Fetch + digest when creds need shell setup | a subagent | the digest only, never the bundle |
| Shard-key confirmation | `apollo-eng-devops:mongo-specialist` | one line: key + how it was confirmed |
| Owning team | a subagent reading CODEOWNERS in `apolloio/leadgenie` | one line: team + path matched |
| Related incidents / prior tickets | a subagent | ≤5 rows: id, date, one-line outcome |

- If you cannot spawn a subagent, still run the script and read only its output — never `cat` the bundle into context.
- `--html` writes the report to a file. Return the path; never paste HTML into the thread.

## Gotchas

- **Never kill, never file, never reassign.** This skill reports, proposes, and drafts.
- **Do not say "scatter-gather" without a confirmed shard key.** Multi-shard execution plus an unconfirmed key is "multi-shard fan-out". The script enforces this; do not talk past it.
- **`kill_succeeded=true` is a second incident** — escalate a data-integrity check; never read a successful kill as "resolved".
- **A manually-run query is not automatically a bug.** Fix the runbook and the alert routing before opening a code ticket.
- **Deploy-correlated changes the order of operations** — read the diff before designing an index.
- **Urgency is not severity** — a fleet-wide structural pattern on the low-priority lane is still high severity.
- **One event ≠ single-account** — the digest reads scope across all sampled events; blast radius hides in the older ones.
