# Metrics Sources

Optional operational metrics for DevOps, IT, infrastructure, reliability, and support-oriented OKR reports. Use these as supporting evidence only when the metric clearly maps to a key result.

| Signal | Source | Use For | Notes |
| --- | --- | --- | --- |
| App apdex for `app.apollo.io` | [Apollo admin performance monitoring](https://app.apollo.io/#/admin/performance-monitoring) | Page performance, user experience, latency, and reliability KRs | Requires internal Apollo admin access. Record the selected time window, apdex value, and retrieval date. |
| Component-specific uptime for `app.apollo.io` | [Apollo status page](https://status.apollo.io) | Uptime, availability, reliability, and customer-impact KRs | Public source. Use the `app.apollo.io` component rather than overall page status when possible. Record the reporting window shown by the status page. |
| Customer-visible `app.apollo.io` incidents longer than 10 minutes | [Apollo status incidents](https://status.apollo.io/incidents) | Incident reduction, customer-impact, and operational excellence KRs | Count incidents affecting `app.apollo.io` in the requested reporting period whose visible duration is greater than 10 minutes. Include incident links when available. Exclude scheduled maintenance unless the KR explicitly includes it. |

If the metric source is unavailable, behind auth, or does not expose the requested period, mark the evidence as unavailable or partial. Do not estimate apdex, uptime, or incident duration without viewing the source.

## Team-Specific Metric Notes

KR targets and metric mappings are team-specific and change every period. They live in the team files under `weekly-teams/` (for example `weekly-teams/devops.md`) with the period label and the date they were recorded. Treat them as last-known values and verify against the current OKR tracker before a status call. In OKR trackers, a "Baseline" or second target column is the prior period's baseline, never current status.
