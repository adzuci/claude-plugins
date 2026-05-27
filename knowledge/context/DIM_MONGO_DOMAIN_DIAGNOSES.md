# DIM_MONGO_DOMAIN_DIAGNOSES

> Domain authentication and health diagnosis records. One row per domain diagnosis.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_DOMAIN_DIAGNOSES` |
| **Grain** | One row per domain diagnosis |
| **Row count** | ~726K (as of 2026-03-26) |
| **Refresh cadence** | Daily (assumed — ANALYTICS_DATAPLATFORM standard) |
| **Trust level** | High — ANALYTICS_DATAPLATFORM schema |
| **Owner** | Data Platform |
| **DAG** | <!-- TODO: check airflow-dags --> |

## Description

Diagnosis records for email sending domains. Tracks SPF, DKIM, and DMARC authentication status per domain per team, plus overall diagnosis status and email sending policy. Use for deliverability health monitoring, authentication compliance reporting, and identifying teams with misconfigured email domains.

## Upstream Sources

| Source | Relationship |
|---|---|
| MongoDB `domain_diagnoses` collection (assumed) | Raw source — replicated to Snowflake by Data Platform |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| DOMAIN_DIAGNOSIS_ID | TEXT | Unique identifier | Primary key |
| TEAM_ID | TEXT | Team that owns this domain | Join to DIM_MONGO_TEAMS |
| DOMAIN | TEXT | Domain name being diagnosed | |
| SPF_STATUS_CD | TEXT | SPF authentication status: pending/error/good/warning | Key deliverability signal |
| DKIM_STATUS_CD | TEXT | DKIM authentication status: pending/error/good/warning | Key deliverability signal |
| DMARC_STATUS_CD | TEXT | DMARC authentication status: pending/error/good/warning | Key deliverability signal |
| STATUS_CD | TEXT | Overall diagnosis status: pending/done/failed/partially_done | |
| EMAIL_SENDING_POLICY_CD | TEXT | Sending policy: default/sendgrid/mailgun | |
| HEALTH_CHECK_EMAIL_CD | TEXT | Health check email status: sent/pending/disabled/failed | |
| DOMAIN_CREATED_ON | TIMESTAMP_NTZ | When the domain was created | |
| AUTHENTICATION_STATUS_UPDATED_AT | TIMESTAMP_NTZ | Last authentication check timestamp | |
| CREATED_AT_UTC | TIMESTAMP_NTZ | Record creation timestamp | |
| UPDATED_AT_UTC | TIMESTAMP_NTZ | Last updated timestamp | |
| LOAD_DATE | DATE | Snowflake load date | |

## Common Query Patterns

```sql
-- Domain authentication compliance by team
SELECT
    TEAM_ID,
    COUNT(*) AS total_domains,
    SUM(CASE WHEN SPF_STATUS_CD = 'good' THEN 1 ELSE 0 END) AS spf_good,
    SUM(CASE WHEN DKIM_STATUS_CD = 'good' THEN 1 ELSE 0 END) AS dkim_good,
    SUM(CASE WHEN DMARC_STATUS_CD = 'good' THEN 1 ELSE 0 END) AS dmarc_good
FROM ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_DOMAIN_DIAGNOSES
WHERE STATUS_CD = 'done'
GROUP BY 1;
```

## Related Tables

| Table | Relationship |
|---|---|
| `DIM_MONGO_TRACKING_DOMAINS` | Join on TEAM_ID + DOMAIN for tracking domain context |
| `DIM_MONGO_EMAIL_ACCOUNTS` | Join on TEAM_ID for account-level email config |
| `FCT_MONGO_EMAILER_MESSAGES` | Join on team for message volume from diagnosed domains |

## Business Terms

| Term | Definition |
|---|---|
| SPF | Sender Policy Framework — email authentication that specifies which mail servers can send on behalf of a domain |
| DKIM | DomainKeys Identified Mail — email authentication using cryptographic signatures |
| DMARC | Domain-based Message Authentication, Reporting & Conformance — policy layer on top of SPF and DKIM |

## Known Issues & Gotchas

- **Status enum values are well-documented** in column comments — pending/error/good/warning for auth fields, pending/done/failed/partially_done for overall STATUS_CD.
- **One diagnosis per domain per team** — if a team has multiple domains, expect multiple rows.

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-26 | Created context file from Snowflake schema | Anvitha (via Jarvis) |
