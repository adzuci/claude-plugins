---
id: ads-builder-erd-1
kind: retrospective
initiative: ads-builder
artifact: Audience Sync M1 ERD (data model)
owning_stage: E.review (architecture lens)
adjudicated_by: initiative EM
adjudicated_on: 2026-10-06
fix: platform-rules R1 to R5; worked examples in platform-rules.md
---

# Ads ERD: platform knowledge the architecture stage did not apply

Retrospective case, not replay. The council snapshots exist, but the instructions and model
settings for the review were not archived as a fixture.

## Finding

The ERD (the data model) passed its own council and a cross-family review. An EM and a staff
engineer then changed it a lot. Each change was Apollo platform knowledge:

1. Use the existing list and contact change paths to mark members for recheck, instead of a new
   recheck table. There is no general change feed. (platform-rules R1)
1. Keep background jobs short and resumable; split a sync run into small staged jobs (search read,
   database check, ad-platform send). (R2)
1. After a deploy, a new collection whose model declares a shard key is sharded once, and its
   declared indexes are created then only if no index already starts with the shard key. Later
   deploys do not create indexes through that path, so plan every index in the first schema PR and
   verify they exist. (R3)
1. Partial index filters cannot use `$ne`; an enum or boolean first index field needs a partial
   filter. (R4)
1. Secrets go through `CredentialsProvider`, not environment variables. A review bot caught this
   later; that bot finding is an escape too. (R5)
1. Choices specific to this product: explicit status fields instead of version counters; call-id
   marks on member rows instead of embedding up to 5,000 member ids in one document; a priced lock
   replaced by an Elasticsearch point-in-time. (worked examples, not rules)

## Owning stage

The architecture lens at ERD review. The sources for items 1 to 5 were in the repo at the time.

## Why it was missed

- **Missing knowledge** and **rule existed but was not applied**. The lens had no list of platform
  facts to check, and no requirement to produce a row per fact.
- A cross-family review did not help: the second model had the same missing facts. Cross-family
  review finds reasoning gaps, not unknown platform facts.

## Fix

- `framework/platform-rules.md` rows R1 to R5, each with its source and owner.
- doc 43 §3: lenses fill a row per applicable rule with evidence; reading the file is not a check.
- The product-specific choices are worked examples, so they do not become false alarms elsewhere.
