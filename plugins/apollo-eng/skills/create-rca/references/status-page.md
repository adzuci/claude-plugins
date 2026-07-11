# Apollo Status Page and RCAs

Pointer on Apollo's status page process and how RCAs should reference it. Grounded in Slack as of July 2026.

## The Process

- Apollo's customer-facing status page is <https://status.apollo.io>, hosted on Better Stack.
- During an active incident, the **call commander** creates and updates the status-page incident; the infra team sets scheduled-maintenance notices. Not every incident gets a post — quickly-mitigated, contained incidents (e.g. downgraded to SEV-2) may skip it, and the commander notes that in the incident thread.
- An in-app Site Status Banner mirrors the status page: Better Stack incident webhooks drive it automatically for degradations/outages.

## What the RCA Should Do

- If the incident had a status-page post, **link the status-page incident in the RCA** and **align the RCA's stated impact window/outage minutes with what the status page communicated** — RCA reviews have specifically corrected drafts to match the status page (e.g. a "55 min significant impact" window). If they legitimately differ (internal impact vs. customer-visible impact), say so explicitly.
- If no status-page post exists for the incident, note that in the timeline if the sources say why (e.g. "mitigated before customer impact warranted a post"); otherwise use the standard missing-information placeholder.
- Drafting new status-page copy is out of scope for this skill — that is the `/apollo-eng:status-page-post` skill (not yet available on `main`).

## Delayed Status Page Posting

When the status page incident was created significantly later than the actual incident start (>30 min gap), the RCA must document:

- **The gap explicitly** — e.g. "BetterStack incident formally published ~4h48m after impact start (15:03 UTC monitoring alert → 19:51 UTC first post)."
- **Informal vs. formal:** Distinguish between informal status updates (quick notes posted during investigation) and a formal BetterStack incident (the structured record with title, timeline, and resolution). The two can have different timestamps; do not conflate them as "first public acknowledgment."
- **The reason for the gap** — e.g. "Incident initially localized to background jobs (non-user-facing); call commander not engaged until 19:32 UTC; investigation remained in #eng-infrastructure-alerts without formal escalation to the incident response channel."
- **Where it goes**: Contributing Factors — this is a process gap, not a technical cause.

**Systematic risk pattern:** When an incident initially appears scoped to a single non-user-facing component (background jobs, a specific queue, a worker service), there is elevated risk of delayed call commander engagement and delayed status page posting. The RCA should explicitly call this out in Contributing Factors rather than only noting the timestamp discrepancy — it is a recurring process failure mode worth naming directly.
