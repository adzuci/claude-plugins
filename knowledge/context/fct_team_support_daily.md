# FCT_TEAM_SUPPORT_DAILY

> Daily support conversation metrics per team, type, and AI participation flags. 24.5% team coverage due to Intercom bridge limitations.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.PLAYGROUND.FCT_TEAM_SUPPORT_DAILY` |
| **Grain** | One row per (team_id, ds, conversation_type, ai_agent_participated, ai_only_participated, ai_resolution_state) |
| **Grain columns** | `team_id`, `ds`, `conversation_type`, `ai_agent_participated`, `ai_only_participated`, `ai_resolution_state` |
| **Row count** | ~86K |
| **Refresh cadence** | Daily |
| **Coverage period** | Ongoing |
| **Trust level** | Canonical |
| **Owner** | Analytics (Bridie Meredith) |

## Description

Aggregates Intercom support conversations at the team × day × conversation type × AI flag grain. Exposes AI vs. human handling rates, first contact resolution, time-to-reply, CSAT, and cost-per-interaction. Only conversations where `APOLLO_TEAM_ID` is resolved are included — this covers ~24.5% of all conversations. For org-wide support metrics including unmatched conversations, query `DIM_SUPPORT_CONVERSATIONS` directly.

## Upstream Sources

| Source | Relationship |
|---|---|
| `ANALYTICS_DB.ANALYTICS.DIM_SUPPORT_CONVERSATIONS` | Direct aggregation — filtered to non-null `APOLLO_TEAM_ID` only |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| `team_id` | VARCHAR | Apollo team identifier | Resolved via Intercom contact → company → Apollo team bridge |
| `ds` | DATE | Conversation creation date | Cast from `CONVERSATION_CREATED_AT` |
| `conversation_type` | VARCHAR | Conversation category/type | Values from Intercom |
| `ai_agent_participated` | BOOLEAN | True if AI agent participated at any point | |
| `ai_only_participated` | BOOLEAN | True if only AI handled the conversation (no human) | |
| `ai_resolution_state` | VARCHAR | AI resolution outcome classification | |
| `conversation_count` | NUMBER | Total conversations for this grain combination | |
| `support_handled_count` | NUMBER | Conversations where a human support agent handled interaction | |
| `first_contact_resolution_count` | NUMBER | Conversations resolved on first contact | |
| `avg_time_to_reply_seconds` | FLOAT | Average seconds to first admin reply | |
| `avg_csat_rating` | FLOAT | Average customer satisfaction rating | Null when no rating provided |
| `avg_cost_per_interaction` | FLOAT | Average cost per support interaction | From `SUPPORT_DAILY_COST_PER_INTERACTION` on source |

## Known Issues

- **24.5% team coverage** — 75.5% of conversations have no `APOLLO_TEAM_ID` due to Intercom bridge resolution failures (anonymous users, unmatched contacts). This table is not representative of total support volume.
- For total support volume or unmatched conversation analysis, use `DIM_SUPPORT_CONVERSATIONS` directly.
- `avg_csat_rating` will be null for conversations without a rating — aggregations across the grain should handle nulls explicitly.

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-14 | Created context file from catalog metadata | Pepper (auto) |
