# Framework SLO Dashboard — Canonical Reference

> **Status**: framework-canonical. Closes Phase E hardening workstream E0.2.
>
> **Binding**: every Pantheon harness emits the spans defined below. Grafana dashboard `AI-Framework-SLO` is the single pane of glass for framework health.

---

## The 4 framework SLOs

| # | SLO | Target | Measurement window | Page on |
|---|---|---|---|---|
| **SLO-1** | p95 wall time per skill | ≤ skill's declared `max_wall_time_seconds` | rolling 1h | breach for ≥3 consecutive 5-min windows |
| **SLO-2** | MCP failure rate per server | ≤ 2% | rolling 24h | breach for ≥30 min |
| **SLO-3** | Eval-pass rate over time | ≤ 0.5 ppt week-over-week drop | weekly | drop ≥1 ppt week-over-week |
| **SLO-4** | Cost variance vs forecast | actual ≤ 1.3 × forecast | rolling 7d | actual ≥ 1.5 × forecast for ≥24h |

These are FRAMEWORK SLOs — they cover all harnesses uniformly. Per-skill thresholds (precision, recall, FPR, support) live in each skill's `replay_eval` block; those are quality gates, not SLOs.

---

## Required telemetry

Pantheon runtime emits one span per harness run, with sub-spans:

```
harness_run (root)
├─ skill_invocation
│  ├─ mcp_call (newrelic)
│  ├─ mcp_call (grafana)
│  └─ mcp_call (snowflake)
├─ sub_agent_invocation (db-perf)
│  └─ mcp_call (grafana)
└─ output_emission (slack | github | jira)
```

Each span has:
- `harness_name`, `skill_name`, `skill_version`, `tenant_id`, `trigger_id`, `rollout_phase`
- `started_at`, `ended_at`, `wall_time_ms`
- `status` ∈ `{ok, error, timeout, throttled, redacted}`
- `error_class` (if status != ok): `mcp_unreachable`, `mcp_timeout`, `eval_gate_fail`, `cost_cap_exceeded`, `tenant_isolation_block`, `redaction_drop`, `internal`

Spans land in `analytics.harness_spans` (companion to `analytics.harness_runs`).

---

## Dashboard layout (Grafana `AI-Framework-SLO`)

### Row 1 — health summary (single value panels)
- Active harnesses (count)
- Runs in last 24h
- Error rate last 24h (target ≤ 1%)
- Cost burn last 7d vs forecast (% of cap)

### Row 2 — SLO-1: latency
- p50 / p95 / p99 wall time per skill (time series, 1d window)
- Breach indicator per skill (red/green based on p95 ≤ declared budget)

### Row 3 — SLO-2: MCP reliability
- Failure rate per MCP server (newrelic, grafana, snowflake, github, datadog, pagerduty, glean)
- Timeout rate per MCP server
- Top 5 (skill, mcp) pairs by failure count

### Row 4 — SLO-3: eval-pass over time
- Per-skill precision over time (weekly aggregation from `analytics.eval_runs`)
- Per-skill FPR over time
- Per-skill support over time
- Trend arrows (last 4 weeks)

### Row 5 — SLO-4: cost variance
- Per-harness cost burn vs cost_forecast.p95 (stacked area)
- Per-harness cost variance % (rolling 7d)
- Top 5 cost-attribution tags by spend

### Row 6 — versioning + rollouts (Phase E E0.1 cross-cut)
- Skills currently in canary (count + list with canary_pct)
- Last 30d skill version transitions (table from `analytics.skill_versions`)
- Time-since-last-rollback drill per skill (target ≤ 90 days)

### Row 7 — security signals (cross-cut with E0.4 + E0.5)
- Credential age per MCP server (target ≤ 90 days, paged at 75)
- Tenant-isolation blocks count (last 7d) — should be ~0; spikes mean adversarial activity or misconfiguration
- Redaction-drop events by `explicit_drop_keys` matched (last 7d)

---

## Paging conditions

Paging integrates with existing AI-Tooling on-call rotation (PagerDuty `ai-tooling-oncall`).

| Condition | Severity | Page |
|---|---|---|
| SLO-1 breach for ≥3 consecutive 5-min windows | SEV-2 | yes |
| SLO-2 breach for ≥30 min on any MCP server | SEV-2 | yes |
| SLO-3: any skill drops ≥1 ppt precision week-over-week | SEV-3 | yes |
| SLO-4: actual ≥1.5 × forecast for ≥24h | SEV-2 | yes |
| Skill rollback drill not executed in ≥90 days | SEV-3 | weekly digest, not page |
| Credential age ≥75 days on any MCP server | SEV-3 | weekly digest |
| Credential age ≥90 days on any MCP server | SEV-2 | yes |
| Tenant-isolation block count >0 in any 1h window | SEV-1 | yes (security incident) |

The "page on SLO breach" pattern means: if no human is responding to the framework's degradation within 30 min, it's an AI-Tooling on-call issue. This is intentional — without paging, SLOs become vanity dashboards.

---

## Drill: synthetic SLO breach

Quarterly, AI-Tooling executes a synthetic SLO breach drill in staging:

1. Inject latency into one MCP server (e.g., NewRelic responds with 500ms artificial delay)
2. Run `pr-review-bot` against staging
3. Assert SLO-1 breach detected within 5 min
4. Assert page fires within 8 min
5. Assert on-call receives PagerDuty page with correct severity + runbook link
6. Restore + post-mortem if any step fails

Drill outcome lands in `analytics.slo_drill_runs`. Failed drills block Phase E exit.

---

## What's NOT an SLO

- **Per-skill quality gates** (precision, recall, FPR, support) — those are eval gates, declared per skill, not framework SLOs.
- **Adoption metrics** (skill installs, harnesses launched) — those are product metrics, tracked in the org showcase dashboard from Phase D.
- **User satisfaction** (skill-author NPS) — quarterly survey, not real-time SLO.
- **Cross-skill correlations** ("if skill A regresses, does skill B?") — useful, but Phase F territory.

---

## Phase E exit requirements

- [ ] Pantheon runtime emits all required spans (verified by querying `analytics.harness_spans`)
- [ ] Grafana dashboard `AI-Framework-SLO` live with all 7 rows
- [ ] PagerDuty integration tested (synthetic SEV-2 page acknowledged within 5 min)
- [ ] Synthetic SLO breach drill executed and passing
- [ ] On-call runbook published referencing this doc
