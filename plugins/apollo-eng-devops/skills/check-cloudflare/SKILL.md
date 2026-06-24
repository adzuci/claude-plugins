---
name: check-cloudflare
description: Check Cloudflare edge health, bot/challenge signals, throughput/errors, Workers, and tunnel health.
disable-model-invocation: true
---

# Check Cloudflare

Run this skill as `/apollo-eng-devops:check-cloudflare [args]`.

Use this skill to check Apollo's Cloudflare health from Grafana data and, when available, Cloudflare Observability MCP data. Use [`grafana-observability`](../grafana-observability/SKILL.md) alongside this skill when the task includes dashboard design, alert tuning, alert actionability, or SLO/runbook quality.

Provenance only; do not navigate during execution: [Grafana Assistant Check Cloudflare skill](https://apolloio.grafana.net/a/grafana-assistant-app/settings/skills/99b87b15-0bf4-4e9b-9f5e-6b4e1f5aaa8e/view).

## Mode Selection

Start by choosing one mode:

- **Incident mode**: use when the prompt includes an incident or alert thread, endpoint, host, CF-RAY, status code, tunnel, Worker, customer report, time window, or impact.
- **General mode**: use when no incident context is provided.

If the context is ambiguous, proceed in general mode and say which missing details would sharpen the check.

## Tool Priority

Use the source that matches the question. Grafana is primary for edge, challenge, and tunnel metrics. Cloudflare Observability MCP is primary only for Cloudflare Worker inventory/configuration, Worker source, and Cloudflare product documentation.

1. For edge throughput/errors, challenge behavior, and cloudflared tunnel pod health, use Grafana MCP or the dashboards below first.
1. If Cloudflare Observability MCP tools are available, use them for Worker-specific or Cloudflare product questions:
   - `workers_list`: enumerate deployed Workers and status.
   - `workers_get_worker`: inspect Worker configuration, bindings, and cron schedules.
   - `workers_get_worker_code`: inspect Worker source only when debugging named Worker routing or Worker logic.
   - `search_cloudflare_documentation`: answer Cloudflare product questions about tunnels, Zero Trust, CDN behavior, caching rules, firewall, or related features.
1. If MCP tools are unavailable, provide dashboard links, the exact time windows to inspect, and the expected signals to compare.

Worker source/config access is read-only and exceptional. Do not paste Worker source, bindings, routes, internal URLs, secret names, cron details, or detailed rule logic into responses. Summarize only the relevant behavior and redact sensitive details.

## Grafana Sources

Use the smallest useful set of dashboards for the question:

- [CloudFlare Zone Analytics](https://apolloio.grafana.net/d/mWxtnz5Mz/cloudflare-zone-analytics) for edge throughput, bandwidth, non-2xx, 5xx, 522/530, top hosts, top paths, and country signals.
- [Cloudflare Tunnels](https://apolloio.grafana.net/d/V1SL92dVo/cloudflare-tunnels) for cloudflared tunnel request count, response status rate, request errors, HA connections, concurrent requests, pod CPU, and pod memory.
- [[BE Platform] Cloudflare Challenges](https://apolloio.grafana.net/d/aei9p69hd0s8wd/be-platform-cloudflare-challenges) for challenge volume, challenge reason, low bot score traffic, blocked requests, and route/host challenge activity.

## Request-Level Evidence

If the prompt includes a CF-RAY, customer report, single user, specific request, or "blocked/challenged" symptom, do not rely on aggregate dashboards alone.

Use a request-level evidence path when available:

- Cloudflare Security Events, HTTP request logs, Logpush logs, or any Grafana/Loki source that can filter by CF-RAY, host, path, status, action, bot score, or challenge outcome.
- Search available Cloudflare Security Events, HTTP request logs, Logpush, and Grafana/Loki sources before concluding request-level evidence is unavailable.
- If request-level logs are not available in the current tools, say that explicitly and give the dashboard-level evidence as incomplete.
- Redact query strings, tokens, emails, customer IDs, account IDs, IP addresses, and other request-derived identifiers before posting. Prefer aggregate route patterns over exact full URLs.

## Incident Mode

Use the thread or prompt context first. Identify any affected host, endpoint/path, status code, tunnel, Worker, CF-RAY, approximate start time, and customer/user impact.

Check only the diagnostic signals needed for the incident:

- Edge throughput/errors: requests/sec, bandwidth/sec, non-2xx, 5xx, 522/530 spikes, top hosts, and top paths.
- Cloudflared tunnel pods: tunnel request count, response status rate, request errors, HA connections, concurrent requests, pod CPU, and pod memory.
- Bot/challenge behavior: challenge status by route/reason, low bot score requests, blocked requests, and maybe-challenge logs.

Return a compact incident update:

```text
Summary: <one or two sentences>
Impact: <known customer/user impact, or "not confirmed">
Evidence: <strongest metrics/logs, with exact times and values>
Ruled out: <signals checked that did not show a problem>
Likely cause: <supported hypothesis, or "not enough evidence yet">
Recommended next steps: <concrete checks or owner actions>
Owner/escalation: <team/person if clear, or "needs owner">
Confidence: <high|medium|low and why>
```

Omit fields that do not apply if they would make the update noisy.

Do not claim Cloudflare is the root cause unless the data supports it. If the data points to an upstream app issue, tunnel capacity issue, bot/challenge rule behavior, Worker behavior, or vendor issue, say that plainly.

## General Mode

Use default windows unless the user asks for a narrower period:

- Throughput and tunnel health: last 1 hour.
- Bot/challenge behavior: last 24 hours.

Report the key health areas:

- `Bot detection`: challenge volume, challenge reasons, routes/hosts with challenge activity, low bot score traffic, and blocked requests.
- `Throughput`: request rate, bandwidth rate, non-2xx/5xx trends, unusual status codes, top hosts/paths/countries when relevant.
- `Cloudflare Workers and cloudflared tunnel pods`: Worker inventory/config only when relevant; cloudflared HA connections, request errors, concurrent requests, response status rates, pod CPU, and pod memory pressure.

End with a short offer to check a specific route, CF-RAY, customer report, tunnel, Worker, status code, bot/challenge reason, or Cloudflare vendor status.

## Baselines and Rates

Normalize non-tunnel signals before calling them abnormal.

- Report edge errors as rates or deltas over the selected window, not raw cumulative counters.
- Compare status codes, challenge volume, low bot score traffic, and blocked requests against request volume.
- Prefer same-hour prior-day or recent same-window baseline when available. If no baseline is available, say the result is current-window-only.
- Require impact corroboration before calling bot/challenge activity an incident: customer report, route-specific failure, error-rate increase, unusual traffic mix, or matching request-level log evidence.
- Treat top hosts, paths, routes, and countries as directional diagnostics. Redact or aggregate sensitive paths before sharing.

Example: "500s increased from 0.002% to 0.015% of requests for `apollo.io` during 16:00-17:00 UTC, with most increase on the `prod-app` tunnel" is actionable. "500 count is high" is not.

## Tunnel Normalization

Normalize tunnel metrics before flagging anything as elevated or abnormal. Raw totals are misleading at Apollo scale.

- HA connections are normally `4 x pod count`. For example, 10 pods means 40 HA connections is expected.
- Verify the current expected HA connection behavior against the Cloudflare Tunnels dashboard and active pod count before treating this baseline as invariant.
- Only flag HA connections if the per-pod rate deviates from 4, total connections drop, or connections spike sharply without a corresponding pod scale-up.
- Compare request errors and concurrent requests as per-pod rates and relative to current traffic, not as raw totals.
- Require at least one corroborating signal, such as edge error rate increase, latency spike, customer report, tunnel disconnect, or pod health issue, before surfacing a potential incident concern.

Ask: "Is this consistent with the pod count and current traffic?" before calling out a tunnel metric.

## Graph and Link Limit

Include at most **3** graphs or Explore/dashboard links total in any response. Fewer is better when text is enough.

Pick at most one link per diagnostic area:

1. Bot/challenge signal from `[BE Platform] Cloudflare Challenges`.
1. Throughput or edge error signal from `CloudFlare Zone Analytics`.
1. Worker/tunnel signal from `Cloudflare Tunnels`.

Do not include duplicate graphs. If including a graph or link, explain in one sentence why it matters.

## Guardrails

- Keep the answer short enough to paste into Slack during an incident.
- Include exact times, windows, metric names, redacted host/path/status labels, and datasource/dashboard links when available.
- Do not expose detailed security rule configuration, WAF logic, bot rule thresholds, bypass criteria, Worker source, bindings, internal URLs, or sensitive request identifiers in broadly visible Slack or customer-facing language.
- Do not recommend disabling Cloudflare protections. Prefer scoped rule changes, allowlist/skip rules, or configuration fixes only with named Security/Network approval, incident commander signoff, a time box, clear rollback criteria, and a narrow affected route/customer scope.
- Do not recommend Worker or tunnel capacity changes unless the data supports it and the action owner is clear.
- Do not write Jira tickets, incident notes, or Slack replies without explicit user approval.
- If the output reveals a stale query, missing dashboard, or runbook gap, say exactly what should be updated and where.
