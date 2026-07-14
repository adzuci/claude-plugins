# Slack Channels

Channel names and ownership can drift. Verify with Slack search before publishing new
runbook instructions or major incident guidance.

| Channel | ID | Use |
| --- | --- | --- |
| `#eng-devops-mongo` | `C02AER97N82` | Dedicated Mongo/TapData coordination, shard/balancer/range-deleter work, slow-log review, consultant questions. |
| `#xfn-h-devops` | `C69FJ9NEM` | DevOps request coordination, including Mongo index requests and timing announcements. |
| `#eng-infrastructure-alerts` | `CCHSWB3DK` | PagerDuty/Grafana infrastructure alert stream; Mongo incident debugging often happens here. |
| `#incident-response-sev0-sev1` | `C0362RC2GR2` | Cross-functional SEV-0/SEV-1 coordination and incident command. |

## Routing guidance

- For routine index creation requests, use `#xfn-h-devops`.
- For deep Mongo cluster internals or TapData questions, use `#eng-devops-mongo`.
- For active pages, keep diagnosis in the alert or incident thread so context stays
  visible.
- For SEV-level customer impact, use the incident process and `#incident-response-sev0-sev1`.
