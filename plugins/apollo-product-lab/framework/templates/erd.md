---
stage: E.design
initiative: <slug>
title: <feature> data model and architecture
version: <n>
design_sha: <sha256 of sections 1 to 7>   # the review binds to this; editing §8 or the frontmatter does not change it (doc 17 §6.3)
author_family: <anthropic | openai | unknown>   # from produced_by, not from the host
produced_by: <family/model>
reviewed_by:            # filled by the cross-family review, never by the author
  - { family: openai, model: gpt-6-astra, effort: xhigh, served_by: <codex header or served-models.sh>, design_sha: <sha>, date: <yyyy-mm-dd>, verdict_file: <path> }
status: draft | in review | accepted
---

# <Feature>: data model and architecture

## 1. What this builds

Two or three sentences. Link the PRD and the decision log.

## 2. Current behaviour map

For a change to existing behaviour (doc 43 §4): the real path end to end with file:line, the specs that
cover it, and every protection it applies that this design must keep. "Not applicable: new product" is
allowed only for a new product.

## 3. Collections

One subsection per collection. Each has: why it is a table and what was considered instead (doc 17
§6.1 check 2), the field table (name, type, who writes it, **who reads it** with file or planned
method), the shard key, and every index with the query (method name) that uses it. A field with no
reader is cut or gets one (IP13).

## 4. Jobs, hooks and endpoints

One row each: trigger, what it reads and writes, args (ids only, IP4), lock, retry and idempotency,
and the states it moves (every state needs an exit, IP16).

## 5. Load model (required; the design fails review without it)

One row per collection, job, hook and endpoint. Numbers, not adjectives: "small" is not a cell value.
Give the source of each number (a Snowflake or Grafana query, a team's real list size, a stated
assumption marked `[assumed]`).

| Component | Kind | Max per team | Max total | Queries per batch | Writes per batch | Batch size | Fan-out (jobs per trigger) | Largest job arg | Redis use (cache / lock / rate limit; rebuild path) | When Redis is down | When ES is down | When the outside API is down or rate-limits | Concurrency per team / global (what holds it) | Patterns checked (IP ids) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `<collection>` | collection | | | n/a | n/a | n/a | n/a | n/a | | | | | | IP11, IP12, IP13 |
| `<Worker>` | job | | | | | | | | | | | | | IP1 to IP9 |
| `<hook>` | hook | | | | | | | | | | | | | IP1, IP2, IP6 |
| `GET /api/v1/...` | endpoint | | | | | | | | | | | | | IP7, IP16 |

**Host-path rows (IP18).** Every hook or call the design adds to another team's path also fills this table.
`[assumed]` is allowed only with the named metric to check before merge.

| Hook or call | Host path (owning team) | Host peak calls/s (metric query) | I/O per host call: team not using the feature | I/O per host call: team using it | Shared resource touched | Its measured peak (metric query) | Projected increase at host peak |
|---|---|---|---|---|---|---|---|
| `<hook>` | contact upsert (`<team>`) | | 0 (in-process gate) | | rate-limiter Redis | | |

Rules the table must satisfy (the infra lens marks each `checked` or `failed`):

- Queries and writes per batch do not grow with the batch size (IP1, IP2). If they do, say why.
- Fan-out is pluck plus bulk enqueue or `WorkerHelper::Fraction` (IP3).
- No job arg grows with a list or team past about 100 ids (IP4).
- No Redis key is the only copy of a number the product enforces (IP5).
- Concurrency is bounded per team; a global single slot names the shared resource (IP9).
- Every request path reads at most a few hundred documents and calls no outside API per item (IP16).
- Every hook on another team's path has a host-path row with both measured peaks, costs zero I/O for a team not using the feature, and its projected increase leaves the shared resource headroom (IP18); the increases of all rows on one shared
  resource are summed at coincident host peaks and checked as one total.

## 6. Failure modes

Partial failure, retry, revoked credentials, mid-run state change, dependency down (doc 17 §6 table).

## 7. Decisions and alternatives rejected

Each decision with why, alternatives rejected and consequences. Pointers to the decision log.

## 8. Cross-family review record (required before `status: accepted`)

| design_sha | Reviewer (family, model, effort) | Served by (evidence) | Independent of the author? | Date | Blockers | Fixed in design_sha | Fallback / waiver |
|---|---|---|---|---|---|---|---|
| <sha> | openai, gpt-6-astra, xhigh | <codex header / served-models.sh> | yes / no (author is openai: add fable) / unknown | | | | none |

A design change (doc 17 §6.3) is not accepted until the current `design_sha` has an Astra xhigh row and,
when the author family is OpenAI, an Anthropic row. A same-family fallback row leaves the design `in
review` unless a waiver names who accepted it, when, why, and when Astra re-runs.
