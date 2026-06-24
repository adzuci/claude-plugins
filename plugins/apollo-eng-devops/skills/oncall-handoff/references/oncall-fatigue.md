# On-call Fatigue Telemetry

Use this reference when a handoff needs to assess on-call load, not just list incidents.

## Goal

Show enough weekly volume context for the on-call and manager to decide whether the rotation
is healthy, whether the handoff needs a process change, and what to do next.

Treat these numbers as operational telemetry:

- PagerDuty counts show interruption load.
- Slack counts show request and coordination load.
- Notion runbook updates show whether alerts are turning into durable learning.
- Skills or scripts added show whether repeated toil is becoming automation.

## Week Windows

Weekly fatigue reports use a Monday-start week in two shift calendars:

| Shift | Timezone | Default shift | Why |
| --- | --- | --- | --- |
| NAM | `America/New_York` | `10:00-22:00` | Adam's DevOps PagerDuty shift. |
| IST | `Asia/Kolkata` | `08:30-20:30` | India DevOps handoff window during US daylight savings. |

For each calendar, bucket PagerDuty alerts and Slack messages by local day and by shift
membership:

- `in_shift`: created/sent during that shift's local hours.
- `off_shift`: same local week but outside the shift hours.

If a different shift is explicitly supplied, use it and echo the override in the preflight.

## Slack Channels

The weekly fatigue read should count messages and threads in these channels first:

| Label | Channel | ID | Count as |
| --- | --- | --- | --- |
| xfn-devops | `#xfn-h-devops` / `#xfn-team-devops` | `C69FJ9NEM` | Incoming DevOps requests and support asks. |
| incident-response | `#incident-response-sev0-sev1` | `C0362RC2GR2` | Critical incident coordination. |
| devops-alerts | `#eng-infrastructure-alerts` / `#infrastructure-alerts` | `CCHSWB3DK` | DevOps alert stream; this is the current replacement for the informal `#devops-alerts` label. |

Use Slack CLI when available:

```bash
slack conversations history --channel <CHANNEL_ID> --oldest <unix_seconds> --latest <unix_seconds> --limit 200
```

The local Ruby Slack CLI uses `SLACK_API_TOKEN`. If live CLI access is missing, use the
Slack connector or a saved JSON export and mark the counts as degraded.

## PagerDuty Counts

Count DevOps-owned PagerDuty incidents from `devops-high-priority`, `devops-low-priority`,
or the Infrastructure escalation policy. For weekly fatigue, report:

- total PD alerts in the week;
- alerts by local day for NAM and IST calendars;
- in-shift versus off-shift counts for NAM and IST;
- active/unresolved count at report time;
- repeated alert titles if any title fires more than once.

## Notion Runbook Updates

For every alert pattern in the weekly report, search Notion/Glean for related runbooks and
ask whether a runbook or guideline was updated during the same week.

Examples:

- Cloudflare tunnel alerts -> `Cloudflare Tunnel Degradation Runbook` and related 5xx runbooks.
- ES disk alerts -> `Ops Manual: How to Increase MongoDB or Elasticsearch Disk Size`.
- Mongo index requests -> `DevOps / Infrastructure Oncall Guidelines`.
- Runner saturation or pipeline alerts -> deployment pipeline dashboards, runner runbooks,
  and any DevOps guidelines that mention `minRunner` or runner scale sets.

Report updated runbooks separately from referenced runbooks:

- `updated`: the page was updated during the weekly window and is related to an on-call alert/request.
- `referenced`: useful existing guidance was found but not updated during the window.
- `gap`: no useful runbook or guideline found.

## Fatigue Interpretation

Use the counts to say how to act:

- High PD count + low Slack discussion: likely alert noise or self-resolving pages; improve
  alert actionability, thresholds, grouping, or runbook links.
- Low PD count + high `#xfn-h-devops` volume: request load is the fatigue source; add routing
  guidance, ownership docs, templates, or lightweight triage scripts.
- Repeated incident-response messages: check if the same incident lacks a durable follow-up.
- Many off-shift alerts: check rotation coverage, alert urgency, and whether low-priority
  alerts should page outside business hours.
- Runbook updates without lower future alert volume: the doc may exist but not be linked
  from PD/Grafana/Jira where responders need it.

Keep the conclusion action-oriented: name the top 1-3 load drivers and the smallest
process or automation change that would reduce next week's fatigue.
