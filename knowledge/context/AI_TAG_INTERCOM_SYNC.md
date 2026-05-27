# AI_TAG_INTERCOM_SYNC

> Tracks the sync status of AI-generated tags being pushed back to Intercom conversations.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_COMMON.AI_TAG_INTERCOM_SYNC` |
| **Grain** | One row per CONVERSATION_ID |
| **Refresh cadence** | Continuous (event-driven) |
| **Coverage period** | Ongoing |
| **Trust level** | Authoritative — operational sync tracking |
| **Owner** | Data Platform / Support Analytics |

## Description

Operational table tracking whether AI-generated tags have been successfully synced back to Intercom for each support conversation. Used heavily by automated pipelines (45,650 queries/14d). Joins to DIM_SUPPORT_CONVERSATIONS on CONVERSATION_ID.

## Upstream Sources

| Source | Relationship |
|---|---|
| AI tagging pipeline | Generates tags from conversation transcripts |
| Intercom API | Target system for tag sync |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| CONVERSATION_ID | TEXT | Primary key — links to DIM_SUPPORT_CONVERSATIONS | NOT NULL |
| AI_TAGS | TEXT | The AI-generated tags for this conversation | NOT NULL — text, not VARIANT |
| SYNCED_AT | TIMESTAMP_NTZ | When tags were synced to Intercom | NULL if not yet synced |
| SYNC_STATUS | TEXT | Current sync state (e.g., success, failed, pending) | |
| SYNC_ATTEMPTS | NUMBER | How many sync attempts have been made | |
| CREATED_AT | TIMESTAMP_NTZ | When the record was created | |
| UPDATED_AT | TIMESTAMP_NTZ | Last update timestamp | |

## How It's Used

### Common query patterns

- Monitor sync success rate: COUNT where SYNC_STATUS = 'success' / total
- Find failed syncs for retry: WHERE SYNC_STATUS = 'failed'
- Join to DIM_SUPPORT_CONVERSATIONS for conversation context

### Key consumers

- Automated sync pipelines (45,650 queries in 14 days — overwhelmingly machine-driven)
- Support analytics team

## Known Issues & Gotchas

- AI_TAGS is TEXT, not VARIANT — if you need individual tags, you'll need to parse the string
- Very high query volume is from automated pipelines, not humans
- Only 7 columns — purely operational, not analytical

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-10 | Created context file (from signal mining — uncataloged table scan) | Bridie Meredith |
