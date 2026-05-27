# APOLLO_INCIDENT_DATA

> PagerDuty incident tracking data. One row per incident.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.APOLLO_INCIDENT_DATA` |
| **Grain** | One row per incident (`INCIDENT_KEY`) |
| **Row count** | ~9K (2026-03-06) — small table |
| **Refresh cadence** | Daily (likely via external data ingestion) |
| **Trust level** | Authoritative (ANALYTICS_DATAPLATFORM) |
| **Owner** | Data Platform / DevOps |
| **DAG** | Not explicitly found. Likely part of external data ingestion pipeline (PagerDuty API). |

## Description

Incident tracking table (35 distinct users). Stores PagerDuty incidents with severity, status, MTTR, and resolution data. Used for engineering reliability dashboards, MTTR tracking, and quality/RCA reviews. Small but widely queried.

## Upstream Sources

| Source | Relationship |
|---|---|
| PagerDuty API | Primary source |

## Key Columns

Ranked by actual usage (90 days, distinct users):

| Column | Type | Users | Queries | Description | Notes |
|---|---|---|---|---|---|
| STATUS | TEXT | 36 | 4,842 | Incident status | triggered/acknowledged/resolved |
| TEAM | TEXT | 36 | 4,842 | Owning team | Engineering team responsible |
| RESOLVED_AT | TIMESTAMP | 36 | 4,842 | Resolution timestamp | Used for MTTR calculation |
| INCIDENT_KEY | TEXT | 36 | 4,842 | Unique incident ID | **Primary key** |
| CREATED_AT | TIMESTAMP | 36 | 4,842 | Incident creation time | |
| SEVERITY | TEXT | 36 | 4,842 | Incident severity level | |
| SUMMARY | TEXT | 36 | 4,842 | Incident description | |
| MTTR_STATUS | TEXT | 29 | 4,167 | MTTR classification | |
| ACKED_AT | TIMESTAMP | 1 | 4 | Acknowledgment timestamp | Rarely queried |
| INGESTED_AT | TIMESTAMP | 1 | 4 | Data ingestion time | |

## How It's Used

### Common query patterns
- **MTTR dashboards**: Time from CREATED_AT to RESOLVED_AT by TEAM and SEVERITY
- **Incident counts**: Per team, per severity, trending over time
- **Quality/RCA reviews**: Weekly incident review meetings

### Key consumers
- Engineering leadership (reliability metrics)
- #weekly-quality-rca-review channel
- DevOps team
- Looker engineering dashboards (alongside GITHUB_DEVELOPER_TEAMS, FCT_GITHUB_PR_TIMELINE)

## Known Issues & Gotchas

- Small table (~9K rows) — no performance concerns
- Most columns queried by same 36 users (dashboard-driven access pattern — likely a single Looker explore)
- ACKED_AT and INGESTED_AT rarely used (1 user each)
- PagerDuty integration can break — Metaplane alerts stopped after Karun left Apollo (#metaplane-apollo-shared)

## Slack Context

- **PagerDuty integration fragility**: Metaplane→PagerDuty alerts stopped after Karun (Data Platform) left; credentials were tied to his account (#metaplane-apollo-shared)
- **Weekly RCA review**: Jaspreet Anand runs weekly quality/RCA review using PagerDuty incident counts (#weekly-quality-rca-review)
- **Related to GITHUB_DEVELOPER_TEAMS**: Often joined for team-level eng metrics

## Business Terms

| Term | Definition |
|---|---|
| MTTR | Mean Time To Resolution — time from incident creation to resolution |
| Severity | Incident priority level (SEV1-SEV4 typical) |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-03-06 | Created context file from access history + Slack research | Brighid (via Claude) |
