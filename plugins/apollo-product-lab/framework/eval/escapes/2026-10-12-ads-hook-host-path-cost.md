---
id: ads-builder-hook-cost-1
kind: retrospective
initiative: ads-builder
artifact: PR 107058 (Ads change hooks on host write paths)
owning_stage: E.review (infra lens, Load model)
adjudicated_by: initiative EM
adjudicated_on: 2026-10-12
fix: apollo-infra-patterns IP18; doc 17 §6.2 host-path columns; templates/erd.md §5; doc 34 infra lens; doc 21 §8c
---

# Ads change hooks: a per-call cost nobody multiplied by the host's rate

Retrospective case, not replay. The original ERD review prompts and model settings were not archived.

## Finding

Ads added change hooks to Apollo's contact upsert, replies, sequences, lists, stages and unsubscribes.
Every call made two Redis lookups on the shared rate-limiter Redis, for every team, including the teams
that never use Ads, each with a 0.1 s timeout on the write path. Live numbers from Grafana: contact
upsert peaks at about 5.1K calls/s; the rate-limiter Redis peaks at about 41K commands/s and 0.74 of its
single core. The hooks added about 12K commands/s at peak (+30%), pushing that store, which every rate
limiter in the app shares, close to one core. It surfaced only at merge time, when the EM asked about
latency.

The shipped fix gates each hook first on an in-process set of teams that have ever connected, refreshed
from one Redis set once a minute, so a team that does not use Ads costs zero Redis or Mongo calls.

## Owning stage

The infra lens at design review, against the ERD's Load model. The Load model had a hook row ("one Redis
lookup"), IP5 held (Redis as a cache), and the lens passed it. The host rate and the shared store's load
were available in Grafana.

## Why it was missed

- **No lens for this.** All seventeen infra patterns were about the feature's own efficiency; none
  priced the cost the feature imposed on other teams' hot paths.
- **Rule existed but was not applied** in spirit: the Load model asked for numbers, but a per-call count
  without the host's rate is not a load number.

## Fix

- IP18: a hook on a host write path costs nothing for a team that does not use the feature; gate before
  any I/O on an in-process answer, and price any per-call I/O as host peak x calls per call against the
  shared store's measured peak.
- doc 17 §6.2 and `templates/erd.md` §5: host-path columns are required for every hook or call on another
  team's path; `[assumed]` only with a named metric to check before merge.
- doc 34 infra lens: a hook row without those numbers is `failed`; with Grafana reachable the numbers are
  queried, otherwise `unverified` with a pre-merge human check.
- doc 21 §8c: verify re-checks the host-path rows against live metrics before merge.
