# Better Stack Uptime API Reference

Raw endpoint detail for the check-uptime skill. `scripts/check_uptime.py`
already implements all of this; use this file when you need to call the API by
hand or extend the script.

## Auth

All requests send the token from the `BETTERSTACK_API_TOKEN` environment
variable as a bearer token. Create it in the Better Stack dashboard under
**Uptime → API tokens**. Never print the token or paste it into a report.

```bash
Authorization: Bearer $BETTERSTACK_API_TOKEN
```

Apollo's public status page is [status.apollo.io](https://status.apollo.io),
backed by Better Stack team `t76664`.

## Basics

- Base URL: `https://uptime.betterstack.com/api/v2` (JSON:API format).
- Incidents live on **v3**: `https://uptime.betterstack.com/api/v3/incidents`.
  v3 is current; the v2 incidents endpoint is deprecated — don't "fix" it back.
- Responses are paginated. Follow `pagination.next` until it is null so no
  monitors, heartbeats, or incidents are missed.
- Durations (`total_downtime`, `longest_incident`, `average_incident`) are in
  **seconds** — convert to minutes/hours for the report.

## Monitors

```bash
curl -s -H "Authorization: Bearer $BETTERSTACK_API_TOKEN" \
  "https://uptime.betterstack.com/api/v2/monitors?per_page=50"
```

Each monitor has `url`, `pronounceable_name`, and `status` (`up`, `down`,
`paused`, `maintenance`). Follow `pagination.next` for every page.

## SLA / availability per monitor

```bash
curl -s -H "Authorization: Bearer $BETTERSTACK_API_TOKEN" \
  "https://uptime.betterstack.com/api/v2/monitors/{id}/sla?from={FROM_DATE}&to={TO_DATE}"
```

`{id}`, `{FROM_DATE}`, and `{TO_DATE}` are placeholders — substitute the monitor
id and the resolved window. The `attributes` payload includes `availability`
(percent), `total_downtime`, `number_of_incidents`, `longest_incident`, and
`average_incident` (durations in seconds).

## Incidents (v3)

```bash
curl -s -H "Authorization: Bearer $BETTERSTACK_API_TOKEN" \
  "https://uptime.betterstack.com/api/v3/incidents?per_page=50"
```

Use `name`, `started_at`, `resolved_at`, and the affected monitor. An incident
with no `resolved_at` is still open. Page through `pagination.next` and keep
incidents that overlap the window.

## Heartbeats

Heartbeats are scheduled-ping services; a missed ping counts as down. The skill
always classifies heartbeats as **background** severity.

```bash
curl -s -H "Authorization: Bearer $BETTERSTACK_API_TOKEN" \
  "https://uptime.betterstack.com/api/v2/heartbeats?per_page=50"
curl -s -H "Authorization: Bearer $BETTERSTACK_API_TOKEN" \
  "https://uptime.betterstack.com/api/v2/heartbeats/{id}/availability?from={FROM_DATE}&to={TO_DATE}"
```

Same placeholder rules apply. Include a heartbeats/background section only when
heartbeats exist.
