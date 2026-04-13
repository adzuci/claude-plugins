# <TABLE_NAME>

> One-line description of what this table is.

## Overview

| Field | Value |
|---|---|
| **Full path** | `DATABASE.SCHEMA.TABLE_NAME` |
| **Grain** | <!-- One row per ___? --> |
| **Row count** | <!-- Approximate, with date checked --> |
| **Refresh cadence** | <!-- Hourly / Daily / Weekly / Event-triggered / Manual --> |
| **Coverage period** | <!-- "ongoing" for live tables, or "YYYY-MM-DD to YYYY-MM-DD" for bounded/historical tables --> |
| **Trust level** | <!-- Authoritative / Use with caution / Deprecated --> |
| **Owner** | <!-- Person or team --> |
| **DAG** | <!-- Airflow DAG name that builds/refreshes this table --> |

## Description

<!-- 2-5 sentences: What is this table? What business process does it represent? Who are the primary consumers? -->

## Upstream Sources

<!-- Where does the data come from? List source tables, APIs, or systems. -->

| Source | Relationship |
|---|---|
| | |

## Key Columns

<!-- Document the most important columns — not every column, just the ones people need to understand. -->

| Column | Type | Description | Notes |
|---|---|---|---|
| | | | |

## How It's Used

<!-- Real query patterns from query history. What do people actually do with this table? -->

### Common query patterns

### Key consumers

<!-- Teams, dashboards, downstream tables that depend on this -->

## Known Issues & Gotchas

<!-- Data quality issues, common mistakes, things that will bite you -->

-

## Slack Context

<!-- Notable Slack discussions about this table — link or summarize -->

-

## Business Terms

<!-- Domain-specific terms that appear in this table. Define them here, and add to glossary_entries.md -->

| Term | Definition |
|---|---|
| | |

## Change Log

<!-- Track significant changes to this table or its documentation -->

| Date | Change | Author |
|---|---|---|
| | Created context file | |
