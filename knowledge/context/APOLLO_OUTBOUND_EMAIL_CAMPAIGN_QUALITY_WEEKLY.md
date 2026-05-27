# APOLLO_OUTBOUND_EMAIL_CAMPAIGN_QUALITY_WEEKLY

> Weekly AI-scored quality assessment of Apollo's internal outbound email campaigns.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATASCIENCE.APOLLO_OUTBOUND_EMAIL_CAMPAIGN_QUALITY_WEEKLY` |
| **Grain** | One row per campaign + step + week (`campaign_week_step_key`) |
| **Refresh cadence** | Weekly (incremental, dbt Cloud) |
| **Trust level** | High (direct from dbt model, Cortex-scored) |
| **Owner** | Shyam SK (Analytics Engineering) |
| **Stakeholder** | Henry (SVP Revenue) |

## Description

Weekly quality assessment of outbound sequence emails sent by Apollo's internal team (`team_id = '551e3ef07261695147160000'`). Each week, the dbt model samples up to 25 emails per campaign per step, evaluates via Snowflake Cortex (Claude 3.7 Sonnet) on 5 criteria, and aggregates using worst-email-wins logic.

## Key Columns

| Column | Type | Description |
|---|---|---|
| `CAMPAIGN_WEEK_STEP_KEY` | TEXT | Surrogate key (week + campaign + step) |
| `WEEK_START` | DATE | Week start date |
| `EMAILER_CAMPAIGN_ID` | TEXT | Campaign ID |
| `SEQUENCE_NAME` | TEXT | Campaign/sequence name |
| `STEP_NUMBER` | INT | Step position in the sequence |
| `IS_FIRST_STEP` | BOOLEAN | Whether this is step 1 |
| `NUM_EMAILS_SENT` | INT | Total emails sent for this campaign+step in the week |
| `OVERALL_QUALITY` | TEXT | `good`, `needs_work`, `bad`, or `unknown` (worst-email-wins) |
| `NUM_EMAILS_SAMPLED` | INT | Number of emails evaluated (max 25) |
| `NUM_EMAILS_WITH_CLEAR_PITCH` | INT | Count with clear value prop |
| `NUM_EMAILS_WITH_CTA` | INT | Count with clear CTA |
| `NUM_EMAILS_WITH_BOOKING_LINK` | INT | Count with booking link |
| `NUM_EMAILS_WITH_GOOD_WRITING` | INT | Count with good grammar/spelling |
| `NUM_EMAILS_WITH_PERSONALIZATION` | INT | Count with personalization |
| `POTENTIAL_ISSUES` | ARRAY | Deduplicated list of issues across all sampled emails |
| `SUGGESTED_FIX` | TEXT | Single most impactful fix (from worst-quality email) |
