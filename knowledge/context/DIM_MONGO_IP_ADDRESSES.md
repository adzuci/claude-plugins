# DIM_MONGO_IP_ADDRESSES

> IP address dimension from MongoDB — block status across scraping targets, geolocation, and ISP data.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS_DATAPLATFORM.DIM_MONGO_IP_ADDRESSES` |
| **Grain** | One row per ADDRESS (IP address) |
| **Refresh cadence** | Daily |
| **Coverage period** | Ongoing |
| **Trust level** | Source — raw MongoDB extract |
| **Owner** | Data Platform / Infrastructure |

## Description

IP address dimension tracking block status across multiple scraping/enrichment targets (LinkedIn, Google, Bing, AngelList, etc.), geolocation, hostname, and ISP data. Used by Gaspard/Bret and the infrastructure/enrichment team (337 queries/14d) to monitor IP health and rotation needs.

## Upstream Sources

| Source | Relationship |
|---|---|
| MongoDB ip_addresses collection | Direct extract |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| ADDRESS | TEXT | IP address (primary key) | |
| HOSTNAME | TEXT | Resolved hostname | |
| *_BLOCKED_AT | TIMESTAMP_NTZ | Block timestamps per target | LINKEDIN_, GOOGLE_, BING_, ANGELLIST_, etc. |
| CITY | TEXT | Geolocation city | |
| STATE | TEXT | Geolocation state | |
| COUNTRY | TEXT | Geolocation country | |
| ISP | TEXT | Internet service provider | |
| ADDRESS_SOURCE | TEXT | Where this IP came from | |
| PRICING_VARIANT | TEXT | Pricing tier/variant for this IP | |
| RESOLVE_NOT_FOUND | BOOLEAN | Whether DNS resolution failed | |
| LOAD_DATE | DATE | Snowflake load date | |

## How It's Used

### Common query patterns

- Monitor IP block rates by target (LinkedIn, Google, etc.)
- Geographic distribution of IP pool
- ISP concentration analysis
- Block rate trends over time

### Key consumers

- Gaspard/Bret (infrastructure — 337 queries/14d)
- Enrichment pipeline monitoring

## Known Issues & Gotchas

- 10+ *_BLOCKED_AT timestamp columns — one per scraping target. NULL means not blocked.
- RANDOM column (FLOAT) exists — likely used for sampling/rotation, not analytical
- No team or user linkage — this is infrastructure-level data

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-10 | Created context file (from signal mining — uncataloged table scan) | Bridie Meredith |
