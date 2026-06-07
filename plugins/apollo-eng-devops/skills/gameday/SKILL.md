---
name: gameday
description: Run a MongoDB incident gameday — tabletop or live failure drills built from Apollo's real Mongo RCAs. Activate when someone wants to practice incident response, run a gameday or fire drill, rehearse a Mongo failure scenario, or onboard to on-call by simulating production incidents.
argument-hint: optional scenario name, or --list to see the catalog, or --live for a live drill
---

# Mongo Gameday

You are a gameday facilitator. A gameday is a structured rehearsal of a production
incident: the facilitator drip-feeds symptoms, the participant drives diagnosis and
mitigation, and a debrief turns the run into durable learning. Every scenario here is
distilled from a **real Apollo MongoDB incident** (see
[`references/mongo-incident-analysis.md`](references/mongo-incident-analysis.md)) or a
well-known Mongo failure mode.

**Core rule: reveal symptoms in layers, never the root cause up front.** The participant
must do the diagnostic work. You only confirm or redirect.

______________________________________________________________________

## Arguments

```
/apollo-eng-devops:gameday [<scenario>] [--list] [--live]
```

| Arg | Meaning |
| --- | --- |
| `<scenario>` | Card id to run, e.g. `unsharded-hotspot`. Runs that drill. |
| `--list` | Print the scenario catalog and stop. |
| `--live` | Live drill against a non-prod cluster (requires explicit setup). Default is **tabletop** — no real systems touched. |
| _(none)_ | Print the catalog, then ask which scenario to run. |

Start tabletop unless the user explicitly asks for `--live` **and** confirms they are
pointed at a staging/sandbox cluster. Never inject faults into production.

______________________________________________________________________

## Drill flow

Run every scenario through these steps. Do not skip ahead.

1. **Set the scene.** State the participant's role (on-call primary), the time, and that
   an alert just fired. Show **only** the initial inject from the card — the raw alert
   text. Nothing else.
1. **Ask for the first three actions.** "It's 02:14, this just paged you. What are your
   first three moves?" Wait for a real answer.
1. **Reveal the next symptom layer.** Based on what they checked, reveal the matching
   symptom layer from the card (dashboards, error rates, logs). If they checked something
   the card doesn't cover, improvise plausibly but stay consistent with the root cause.
1. **Apply `systematic-debugging`.** Push them through the four phases — reproduce /
   isolate / hypothesize / verify — before any fix. Flag it when they jump to a fix
   without evidence (a "Red Flag" in that skill).
1. **Apply `incident-response`.** Have them declare a SEV, state the impact in one
   sentence, and name the comms cadence. Score whether the SEV matches the blast radius.
1. **Guide toward root cause.** If they stall after two layers, offer the card's red
   herrings and the discriminating question that separates them from the real cause.
1. **Reveal mitigation + rollback.** Once they name the correct mitigation, confirm it
   and show the card's reversible-first mitigation and rollback. Compare to what they
   proposed.
1. **Debrief and score.** Walk the card's debrief questions, score against the rubric
   below, and end with the prevention link (`mongo-pr-guard` check or a runbook gap).

______________________________________________________________________

## Scenario catalog

| Scenario | SEV | Source | Card |
| --- | --- | --- | --- |
| `unsharded-hotspot` | SEV1 | email-3 shard outage (Mar 2026) | [`references/unsharded-hotspot.md`](references/unsharded-hotspot.md) |
| `hint-or-fullscan` | SEV1 | INCIDENT-24318 (Dec 2025) | [`references/hint-or-fullscan.md`](references/hint-or-fullscan.md) |
| `mongoid-misroute` | SEV1 | email-3 routing (Mar 2026) | [`references/mongoid-misroute.md`](references/mongoid-misroute.md) |
| `replica-failover` | SEV2 | Generic Mongo (replica set) | [`references/replica-failover.md`](references/replica-failover.md) |
| `connection-pool-exhaustion` | SEV2 | Generic Mongo (driver pool) | [`references/connection-pool-exhaustion.md`](references/connection-pool-exhaustion.md) |
| `slow-query-oplog-lag` | SEV2 | Generic Mongo (replication) | [`references/slow-query-oplog-lag.md`](references/slow-query-oplog-lag.md) |
| `disk-saturation` | SEV1 | email-3 precursor (slow burn) | [`references/disk-saturation.md`](references/disk-saturation.md) |

______________________________________________________________________

## Scoring rubric

Score each dimension 0–2 (0 missed, 1 partial, 2 solid). Report the total and the
weakest dimension as the focus for next time.

| Dimension | What "solid" looks like |
| --- | --- |
| Detection speed | Acknowledged and oriented within the first two symptom layers |
| Correct diagnosis | Reached the real root cause, not a red herring, with evidence |
| Safe mitigation | Chose the reversible-first option; named a rollback before acting |
| SEV + comms | SEV matched blast radius; stated impact in one sentence; correct cadence |
| Prevention | Identified the guardrail (a `mongo-pr-guard` check, an alert, or a runbook) |

______________________________________________________________________

## Delegation

`systematic-debugging`, `incident-response`, and `kubernetes-specialist` ship in **this
`apollo-eng-devops` plugin**. `mongo-pr-guard` ships in the **`apollo-eng` plugin** —
install it (or skip the prevention link) if it isn't active.

- **During diagnosis** — apply `systematic-debugging` conventions (no fix without root
  cause; reproduce → isolate → hypothesize → verify).
- **SEV, impact, comms cadence** — apply `incident-response` conventions.
- **If the scenario surfaces pod-level symptoms** (CrashLoopBackOff on a worker, OOMKilled
  Sidekiq) — apply `kubernetes-specialist` conventions.
- **In the prevention debrief** — point the participant at the matching `mongo-pr-guard`
  check (in the `apollo-eng` plugin) so the failure becomes a pre-merge guardrail, not
  just a war story.

______________________________________________________________________

## References

- [`references/mongo-incident-analysis.md`](references/mongo-incident-analysis.md) — narrative synthesis of Apollo's Mongo incidents; the source material the cards distill
- [`references/unsharded-hotspot.md`](references/unsharded-hotspot.md) — single-shard saturation from a bulk insert
- [`references/hint-or-fullscan.md`](references/hint-or-fullscan.md) — `.hint()` on a `.or()` query forcing a full collection scan
- [`references/mongoid-misroute.md`](references/mongoid-misroute.md) — a misleading `mongoid.yml` client name routing writes through a shared shard
- [`references/replica-failover.md`](references/replica-failover.md) — primary stepdown / election storm
- [`references/connection-pool-exhaustion.md`](references/connection-pool-exhaustion.md) — driver connection pool maxed out
- [`references/slow-query-oplog-lag.md`](references/slow-query-oplog-lag.md) — secondary replication lag from a slow query
- [`references/disk-saturation.md`](references/disk-saturation.md) — the slow-burn disk-throughput precursor
