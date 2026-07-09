# Apollo Status Page House Style

Distilled from real status.apollo.io incidents, recovered from the live page in July 2026; the examples span April-May 2026 and earlier.

## Style Rules

- Each update is 1-3 short sentences. First-person plural ("we", "our engineering team"). Plain declarative sentences.
- Stage openers:
  - **Investigating**: "We are currently investigating reports of..."
  - **Identified**: "We have identified..."
  - **Monitoring**: state that things have stabilized, then "We are continuing to monitor."
  - **Resolved**: "The issue has been resolved." Often extended with "...and all products should be operating normally" or feature-specific wording ("X are now processing normally").
- Hedge impact and describe symptoms, not systems: "some users may notice...", "a small subset of users", plus concrete user-visible symptoms (slower page load times, stale data in search results, delays in email-finding results, longer processing times for background jobs). Note what is NOT affected when possible.
- Name features by product surface: "Apollo web app", "background jobs", "email enrichment", "search results", "app.apollo.io". NEVER internal details — no Redis, Mongo, Sidekiq, pool sizes, org or customer names, Jira ticket IDs, or internal service names.
- Reassure about automatic recovery where true: "jobs queued during the affected window will be retried/completed automatically." Verify any no-data-loss claim with the incident owner before publishing.
- No apologies in incident updates. "We apologize for any inconvenience" belongs only in scheduled-maintenance notices.
- Vendor-caused incidents attribute the cause plainly: "caused by unscheduled maintenance from an upstream vendor".

## Components

Tag the affected component(s) from the page's known labels: app.apollo.io, www.apollo.io, Background Jobs Latency, Email Sending Latency, Email Request Fulfillment Latency, Mobile Number Fulfillment Latency, Payment Gateway.

## Titles

Short (2-7 words) and symptom-first. Real examples: "Degraded Performance", "Background Jobs Delayed", "Email Delays", "Search and queue degradation".

## Real Past Posts (Examples)

Actual posts, kept here as style examples; the date next to each title is when the incident occurred.

- **"Search and queue degradation"** (May 2026)

  - Investigating: "Apollo's queue infrastructure is degraded"
  - Monitoring: "The cluster has been stabilized and queues are catching up"
  - Resolved: "The issue has been resolved and all products should be operating normally."

- **"Degraded Performance"** (May 2026)

  - Investigating: "We are currently investigating reports of degraded performance affecting some users, including slower page load times across the Apollo platform"
  - Monitoring: mitigation "identified and rolled out", team "continuing to monitor"

- **"Email enrichment requests are delayed"** (May 2026)

  - Resolved: "Email enrichment requests are now processing normally, and any jobs that failed during the window will be automatically retried and completed."
  - Root cause: "Earlier degraded performance with email enrichment was caused by unscheduled maintenance from an upstream vendor, which has since been resolved."

- **"Data indexing delayed"**: "Our background jobs are delayed and users may see stale data in the search results."

- **"Slowness observed in background jobs"**: "Search results may show outdated data due to indexing delays."
