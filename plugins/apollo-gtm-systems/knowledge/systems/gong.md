---
last_reviewed: 2026-05-20
---

# Gong

## Role at Apollo

Gong serves three primary functions:

1. Pipeline hygiene and deal inspection: call activity and engagement signals used to assess deal health and rep coverage
2. Forecasting support: deal momentum signals consumed by RevOps and Sales leadership during forecast reviews
3. Call recording and coaching: recordings used for rep development, onboarding, and QBR prep

## Access

Gong requires a named seat. Employees in the RevOps and Sales orgs receive viewer access by default. To request a seat or an upgraded access level, file a JIRA RS ticket.

GTM Systems administers Gong org settings, library structure, and scorecards. Individual reps manage their own availability and notification preferences.

## Call recording requirements

Gong records calls only when the meeting is scheduled through one of these paths:
- The rep's Chili Piper personal meeting room URL
- A Chili Piper-routed scheduling link

A standard Zoom link sent directly via email will not trigger Gong recording. The meeting must flow through the Chili Piper layer for the recording bot to join.

For troubleshooting missing recordings, see `diagnostics/no-gong-recording.md`.

## Email alias matching

Chili Piper matches calendar invitations to a rep's profile by email address. If a rep has multiple work email aliases and not all are registered in their Chili Piper profile, some invitations will not be matched and Gong will not join those calls. Reps should verify their aliases in their Chili Piper profile.

## Gong data in Snowflake

Gong call and activity data is mirrored to Snowflake via Gong Data Cloud. Analytical queries (call volume by rep, engagement scores, pipeline coverage metrics) should use the Snowflake path, accessed via Jarvis or direct Snowflake query. Do not attempt to bulk-extract call data from the Gong UI for analytics purposes.

## Salesforce writeback

Gong writes call activity back to the Salesforce Activity object. The typical delay is ~15 minutes (SLA: under 1 hour). If an activity is missing in Salesforce shortly after a call, wait before filing a bug. If it is absent after 1 hour, escalate to GTM Systems.

## Documentation maintenance

GTM Systems runs a monthly scan of the Gong API and Gong Data Cloud schema in Snowflake. Changes to schema structure or call data fields are PRed to this file. Bump `last_reviewed` on every update.
