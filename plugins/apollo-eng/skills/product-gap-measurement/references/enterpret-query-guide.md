# Enterpret Query Guide

Use this reference before running Enterpret queries for product-gap measurement.

Enterpret uses Cypher, not SQL. `SELECT/FROM` will fail with a "missing RETURN clause" error.

Node label: `NaturalLanguageInteraction`. Topic join path:

```cypher
(nli:NaturalLanguageInteraction)-[:SUMMARIZED_BY]->(fi:FeedbackInsight)
-[:HAS_TAGS]->(cft:CustomerFeedbackTags)-[:BELONGS_TO_L1]->(l1:L1)
```

For L2 breakdown add: `MATCH (cft)-[:BELONGS_TO_L2]->(l2:L2)`
For theme breakdown add: `MATCH (cft)-[:HAS_THEME]->(t:Theme)`

Rules that break silently if violated:

- Source filter: `nli.source CONTAINS 'Intercom'` — not `=` and not lowercase.
- Date field: `nli.record_timestamp` — use `toDateTime('YYYY-MM-DD')`.
- Email filter: `nli.intercom_author_email IN ['a@b.com', ...]` — regular `IN` works; `NOT IN` does not.
- Always filter MISC: `l1.type != 'MISC'`, `l2.type != 'MISC'`, `t.type != 'MISC'`.
- Always `COUNT(DISTINCT nli.record_id)` — never `COUNT(*)` because graph fan-out multiplies rows.
- Alias aggregates as `total`, not `count` because `count` is a reserved keyword.

Amplitude to Enterpret join, when no direct page context exists in Intercom:

1. Query Amplitude for `Contextual Sidebar Event` where `type = click`, `cta = Talk to support`, `resourceType = intercom`, plus a `pageLocation` filter, then extract `user_id` values.
1. Resolve each `user_id` to email through the available Amplitude user-profile lookup. Use parallel calls and scope to a single day if the cohort exceeds about 25 users.
1. Query Enterpret with `nli.intercom_author_email IN [resolved emails]`.

Example L1 topic query:

```cypher
MATCH (nli:NaturalLanguageInteraction)-[:SUMMARIZED_BY]->(fi:FeedbackInsight)
-[:HAS_TAGS]->(cft:CustomerFeedbackTags)-[:BELONGS_TO_L1]->(l1:L1)
WHERE nli.source CONTAINS 'Intercom'
AND nli.intercom_author_email IN ['user@example.com']
AND nli.record_timestamp >= toDateTime('2025-01-01')
AND nli.record_timestamp < toDateTime('2025-01-08')
AND l1.type != 'MISC'
RETURN l1.name AS topic, COUNT(DISTINCT nli.record_id) AS total
ORDER BY total DESC
```
