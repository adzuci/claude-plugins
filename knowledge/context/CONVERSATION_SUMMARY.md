# CONVERSATION_SUMMARY

> AI-generated summaries and tags for support conversations.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_COMMON.CONVERSATION_SUMMARY` |
| **Grain** | One row per CONVERSATION_ID |
| **Refresh cadence** | Daily |
| **Coverage period** | Ongoing |
| **Trust level** | Use with caution — AI-generated content |
| **Owner** | Data Platform / Support Analytics |

## Description

Compact AI-generated summary table for support conversations. Each row contains a conversation's generated summary, AI tags, and full transcript text. Joins to DIM_SUPPORT_CONVERSATIONS on CONVERSATION_ID. Lighter-weight alternative to SUPPORT_CONVERSATIONS_AI_ANALYSIS (which has 50+ AI-extracted fields). Used by support analytics (316 queries/14d).

## Upstream Sources

| Source | Relationship |
|---|---|
| DIM_SUPPORT_CONVERSATIONS | Parent conversation metadata |
| AI/LLM pipeline | Generates summaries and tags |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| CONVERSATION_ID | TEXT | Primary key — links to DIM_SUPPORT_CONVERSATIONS | |
| GENERATED_SUMMARY | TEXT | AI-generated conversation summary | Can be large |
| AI_TAGS | VARIANT | AI-generated tags for categorization | Use LATERAL FLATTEN |
| FULL_TEXT | TEXT | Complete conversation transcript | Very large — exclude from SELECT * |

## How It's Used

### Common query patterns

- Join to DIM_SUPPORT_CONVERSATIONS for conversation metadata + summary
- Search GENERATED_SUMMARY for topic-specific support patterns
- Aggregate AI_TAGS for support topic distribution

### Key consumers

- Support analytics (316 queries/14d)
- AI Transformation Squad

## Known Issues & Gotchas

- Only 4 columns — minimal table. For richer AI analysis, use SUPPORT_CONVERSATIONS_AI_ANALYSIS
- FULL_TEXT contains entire conversation transcripts — very large column, always exclude from SELECT *
- AI_TAGS is VARIANT — use LATERAL FLATTEN to query individual tags
- AI-generated content — accuracy varies, use for directional analysis

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-10 | Created context file (from signal mining — uncataloged table scan) | Bridie Meredith |
