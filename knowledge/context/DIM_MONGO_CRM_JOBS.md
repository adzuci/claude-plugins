# DIM_MONGO_CRM_JOBS

> CRM sync job records from MongoDB — tracks CRM export/sync operations, statuses, and failures.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_CRM_JOBS` |
| **Grain** | One row per CRM_JOB_ID |
| **Refresh cadence** | Daily |
| **Coverage period** | Ongoing |
| **Trust level** | Source — raw MongoDB extract |
| **Owner** | Data Platform |

## Description

Dimension table of CRM sync jobs from MongoDB. Each row represents a CRM export/sync operation — includes job type, status, failure reasons, attempt counts, and timing. Used by Uwais Zaki and CRM integration analytics (443 queries/14d).

## Upstream Sources

| Source | Relationship |
|---|---|
| MongoDB crm_jobs collection | Direct extract |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| CRM_JOB_ID | TEXT | Primary key | |
| TEAM_ID | TEXT | Team that initiated the job | Join to DIM_TEAMS_DAILY on APOLLO_TEAM_ID |
| USER_ID | TEXT | User who triggered the job | |
| JOB_TYPE | TEXT | Type of CRM sync (e.g., export, import, sync) | |
| STATUS_CD | TEXT | Job status code (e.g., completed, failed, pending) | |
| FAILURE_REASON_CD | TEXT | Failure reason code if job failed | |
| ERROR_CODE | TEXT | Specific error code | |
| ATTEMPT_COUNT | NUMBER | Number of sync attempts | |
| EXPECTED_EXPORT_COST | NUMBER | Estimated credit cost of the export | |
| SYNC_START_AT_UTC | TIMESTAMP_NTZ | When sync started | |
| SYNC_END_AT_UTC | TIMESTAMP_NTZ | When sync completed | |
| RETRY_AT_UTC | TIMESTAMP_NTZ | Scheduled retry time if applicable | |
| EXCLUDE_FROM_UI | BOOLEAN | Whether this job is hidden from the UI | |
| CREATED_AT_UTC | TIMESTAMP_NTZ | Job creation timestamp | |
| LOAD_DATE | DATE | Snowflake load date | |

## How It's Used

### Common query patterns

- CRM sync success/failure rate analysis
- Failure reason distribution (FAILURE_REASON_CD, ERROR_CODE)
- Sync latency: SYNC_END - SYNC_START
- Credit cost estimation via EXPECTED_EXPORT_COST

### Key consumers

- Uwais Zaki (443 queries/14d)
- CRM integration health monitoring
- Credit pipeline analysis

## Known Issues & Gotchas

- TEAM_ID here maps to APOLLO_TEAM_ID in DIM_TEAMS_DAILY (not SFDC_TEAM_ID)
- CRM_JOB_NOTE column may contain large text — exclude from SELECT *
- Raw source table — job deduplication is by CRM_JOB_ID

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-10 | Created context file (from signal mining — uncataloged table scan) | Bridie Meredith |
