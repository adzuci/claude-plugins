# FCT_CUSTOMER_IO_DELIVERY_METRICS

> Customer.io email delivery metrics — sent, delivered, opened, clicked, bounced, unsubscribed per delivery.

## Overview

| Field | Value |
|---|---|
| **Full path** | `ANALYTICS_DB.ANALYTICS.FCT_CUSTOMER_IO_DELIVERY_METRICS` |
| **Grain** | One row per DELIVERY_ID |
| **Refresh cadence** | Daily |
| **Coverage period** | Ongoing |
| **Trust level** | Standard — operational delivery data |
| **Owner** | Analytics / Marketing Ops |

## Description

Email delivery-level metrics from Customer.io. Each row tracks the full lifecycle of a single delivery: drafted, attempted, sent, delivered, opened, clicked, converted, unsubscribed, spammed, bounced, failed, and dropped — with first/last timestamps and counts for each event. Used by marketing/lifecycle team (678 queries/14d).

## Upstream Sources

| Source | Relationship |
|---|---|
| Customer.io webhooks/API | Delivery event data |

## Key Columns

| Column | Type | Description | Notes |
|---|---|---|---|
| DELIVERY_ID | TEXT | Primary key | |
| DELIVERY_TYPE | TEXT | Type of delivery (email, push, etc.) | |
| CIO_CUSTOMER_ID | TEXT | Customer.io customer ID | |
| CAMPAIGN_ID | NUMBER | Customer.io campaign | |
| NEWSLETTER_ID | NUMBER | Newsletter ID if applicable | |
| FIRST_SENT_AT / LAST_SENT_AT | TIMESTAMP_NTZ | Send timestamps | |
| SENT_COUNT | NUMBER | Number of sends | |
| DELIVERED_COUNT | NUMBER | Successful deliveries | |
| OPENED_COUNT | NUMBER | Open events | |
| CLICKED_COUNT | NUMBER | Click events | |
| CONVERTED_COUNT | NUMBER | Conversion events | |
| BOUNCED_COUNT | NUMBER | Bounce events | |
| UNSUBSCRIBED_COUNT | NUMBER | Unsubscribe events | |
| SPAMMED_COUNT | NUMBER | Spam complaint events | |
| FAILED_COUNT | NUMBER | Failed delivery attempts | |

## How It's Used

### Common query patterns

- Email delivery funnel: sent → delivered → opened → clicked → converted
- Bounce/spam rate monitoring
- Campaign performance (aggregate by CAMPAIGN_ID)
- Unsubscribe rate trends

### Key consumers

- Marketing/lifecycle team (678 queries/14d)
- Looker email performance dashboards

## Known Issues & Gotchas

- No direct APOLLO_TEAM_ID or APOLLO_USER_ID — need to join via CIO_CUSTOMER_ID mapping
- FIRST_*/LAST_* timestamps paired with *_COUNT for each event type — 51 columns total
- DELIVERY_TYPE determines the channel — filter if you only want email

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-04-10 | Created context file (from signal mining — uncataloged table scan) | Bridie Meredith |
