---
name: cookie-header-alert-investigate
description: Investigates the "P99 leadgenie cookie header size" Grafana/PagerDuty alert — checks whether it's a real threshold breach or a stale NoData/KeepLast artifact, and if real, checks the large-cookie-by-name diagnostic metric to say whether it's one oversized cookie or aggregate bloat from many small ones. Use whenever the user pastes a Slack/PagerDuty/Grafana link for this alert, or asks things like "what's this cookie alert about", "is the cookie header alert real", "TLDR the leadgenie cookie alert", or "why did the cookie size alert fire again".
---

# Cookie Header Alert Investigate

Run this skill as `/apollo-eng-devops:cookie-header-alert-investigate`, or just paste a link to the alert — natural-language activation is intentional here since the whole point is to catch this alert before someone re-derives its history from scratch. Don't trust "12 KiB" or "stale = scrape gap" from memory — both are wrong in ways that have already leaked into past summaries of this alert; read Background before Step 3.

This alert is noisy for two different reasons — don't conflate them. **It has fired for real:** a 2026-09-21 investigation found P99 crossing the rule's actual **12000-byte** threshold in real spikes going back to Sep 7 ("13-16KiB" is a loose past description, not a measured byte count — see Background for why). **It also had a false-positive *mode*:** the rule's own PromQL bakes the threshold into the query (`... > 12000`), so a below-threshold evaluation returns no series, which Grafana reads as NoData — that's the rule's normal recovery path, not a scrape gap. With `no_data_state: KeepLast`, that meant a NoData read couldn't clear an existing Alerting state, so it could get stuck firing indefinitely (stuck 2026-09-21 through at least 2026-09-23). **That was fixed 2026-09-24** (`no_data_state`: `KeepLast` → `OK`) — a below-threshold read now cleanly resolves to `Normal (NoData)`, this alert's ordinary healthy steady state. **The fix has already regressed silently twice before** (2026-08-31, then again within one day on 2026-09-07) — always read the live value (Step 2), don't assume it holds.

This skill exists so you don't have to re-derive any of this context from old Slack threads every time the alert fires — see the [runbook](https://app.notion.com/p/apolloio/Runbook-P99-leadgenie-Cookie-Header-Size-Alert-3c3ab2b3b496817f8c99c8a88834083f) for the human-maintained version, and `apolloio/argus` → `runbooks/cookie-header-size.md` for Argus's own automated version of this same logic (kept in sync with this skill) — Argus auto-investigates this alert on every firing and posts to `#eng-infrastructure-alerts`; this skill is the manual/ad-hoc counterpart for looking into it directly in Claude Code.

## Background: two metrics, and what the numbers actually mean

- **`leadgenie_http_cookie_header_size_bytes_bucket`** — what the alert actually fires on. Measures the size of the **entire** cookie header. No `name` label (it's been asked for before; there's nothing to add — see below).
- **`leadgenie_http_large_cookie_size_bytes_{bucket,count,sum}`** — diagnostic, carries a `name` label, only emits when a single cookie entry is **>512 bytes**. (Not `http_large_cookie_size_bytes` without the prefix/suffix — that name doesn't exist and returns nothing; a real Grafana dashboard panel for this alert has this exact bug.) Adaptive Metrics has dropped this metric's `pod` label, so a bare selector errors — always wrap it in `sum by (name)(...)`.

The alerting metric's logic is: record total cookie size → if the total is large, walk each entry → emit the diagnostic metric only for entries >512B. So a firing alert with **nothing** on the diagnostic metric means the header is bloated by many small cookies, not one big one — there's no single name to hand anyone in that case. This is not a bug in the alert, it's expected given what's being measured.

**Threshold is 12000 (raw bytes), not "~12 KiB"** — 12000 vs true KiB (12288) differ by ~2.3%; every past investigation of this alert has quoted "12 KiB" loosely. The alerting metric's histogram buckets are `2000/4000/8000/12000/16000/+Inf`, and `histogram_quantile` interpolates *within* a bucket — so a steady ~7,900-7,950B reading is interpolation, not a literal measurement, and a flat `16000` reading is the ceiling returned whenever the quantile lands in the `+Inf` bucket (means "≥1% of requests exceeded 16000 bytes," not "a cookie was exactly 16000 bytes"). Don't quote either as a measured size.

## Step 1: Find the alert

If given a Slack link, read it with `slack_read_thread` (get `channel_id` and `message_ts` from the URL: the path segment `pXXXXXXXXXX` converted to `<10 digits>.<6 digits>`, and `thread_ts` from the query string if present — that's the parent message to pass as `message_ts`). Follow one hop of "Forwarded message" links if the real content is in a linked PagerDuty/Grafana alert thread rather than the message itself.

If given a PagerDuty/Grafana link directly, or just asked about the alert in general, skip straight to Step 2.

## Step 2: Check current alert state

Use `mcp__grafana__alerting_manage_rules` with `operation: "list"` to find the rule UID for "P99 leadgenie cookie header size", then call `operation: "get"` on that UID. **Don't stop at the top-level `state` field from `list`** — it's been observed reporting `"firing"` even when the real cause was stale NoData.

**Read `no_data_state` and `exec_err_state` directly from the top level of the `get` result** — don't infer either. It should read `"OK"` post-fix; if it reads `"KeepLast"`, the fix has regressed (it's done so silently twice before). `exec_err_state` is still `"KeepLast"` on this rule — an evaluation *error* can get stuck the same way NoData used to; if you see an `"Error"` or `"(Error, KeepLast)"` state, don't assume it's the known stale pattern, flag it separately.

Drill into `alerts[].state` on the `get` result. A healthy read is plain `"Normal"` or `"Normal (NoData)"` (the latter is this alert's ordinary steady state now, not a transient gap) — no action needed either way. The **historical** stale-alert tell (from before the fix) is either:

- the literal string `"(NoData, KeepLast)"`, or
- a sentinel `value` of `-1e+00`

If you see either, treat it the same as the old stale mode, and check `no_data_state` per above for a possible regression. If instead you see a genuine `"Alerting"` state, don't assume it's noise — this alert has had confirmed real breaches before (Background).

**Note:** `activeAt` on an alert instance is not a firing time — for a Normal/`Normal (NoData)` instance it's just when that instance entered its current state, and it resets on its own (observed doing so with no breach at all). Don't cite it as when a breach happened.

## Step 3: Query the actual metric

Use `mcp__grafana__query_prometheus` against datasource `grafanacloud-prom`, matching the rule's own window:

```promql
histogram_quantile(0.99, sum by (le) (rate(leadgenie_http_cookie_header_size_bytes_bucket{environment="production", cluster="prod"}[10m])))
```

Keep the `{environment="production", cluster="prod"}` label filter. Window it on the incident's actual timestamp if you have one (a PagerDuty page's own time, not `activeAt`), not just "last 24h from now." Also run a `[1m]`-window pass over the same period — the `[10m]` window can miss a real spike shorter than that entirely.

**Sustained** means 2+ consecutive rule-grain (`[10m]`-window, ~300s-step) evaluations over 12000 — that's what this rule's `for: 5m0s` actually requires to page. Anything less (a single evaluation, or a spike only visible in the `[1m]` pass) is isolated, not sustained.

## Step 4: Check the diagnostic metric

**Don't rely on the Grafana dashboard's own "large cookie by name" panel (panel 6 on dashboard `f066713b-614f-47dd-829f-9b365d4dc28e`)** — its saved query targets the wrong metric name (see Background) and always renders empty regardless of reality. Query the real metric directly:

```promql
sum by (name) (increase(leadgenie_http_large_cookie_size_bytes_count{environment="production", cluster="prod"}[6h]))
```

Window it on the incident's own timeframe. A `name` series present (even at 0) means that cookie tripped the diagnostic path recently; nothing at all is a legitimate "aggregate bloat" outcome, not a broken check.

Also note: the alert rule's own annotation links to `panelId: 5` on that dashboard — that's a different panel too, not the by-name breakdown. Don't trust either deep link; use the PromQL above.

## Step 5: Classify and report

Use this decision logic:

| Alert state | P99 vs threshold | Diagnostic metric | Classification |
|---|---|---|---|
| Normal (incl. `Normal (NoData)`), no page context | below 12000 | — | **Healthy** — no action needed |
| Page received, but now reads Normal/`Normal (NoData)` | real breach inside the page's window | — | **Real, self-resolved** — this is the most likely shape of a genuine post-fix firing (breaches are short, self-clear fast); name the actual breach values/timestamps, still check Step 4 |
| NoData/KeepLast (historical pre-fix pattern) | below 12000 | — | **Stale** — ack/resolve/silence; also report the live `no_data_state` value, and if it's back to `KeepLast`, say the fix has regressed and recommend reverting to `OK` |
| `"Error"` / `"(Error, KeepLast)"` | — | — | **Unrecognized** — don't classify as the known stale pattern; flag for a human to check why the rule is erroring |
| Firing | sustained breach | has entries | **Real, single cookie** — route the named cookie(s) to FE Platform |
| Firing | sustained breach | empty | **Real, aggregate bloat** — many small cookies adding up; not a single-owner fix, needs broader cookie audit |
| Firing (or page received) | isolated points only | — | **Possibly real** — this alert has confirmed genuine crossings before (Background); don't default to "noise," name the values and let Step 4 inform whether it's worth a closer look |

Report format:

```
**TLDR:** {one-line classification and why}

**Evidence:**
- Alert state: {state} (no_data_state: {value}, exec_err_state: {value})
- Current P99: {value} vs threshold 12000 bytes (timestamps if checking a past incident)
- Diagnostic metric (by name): {entries found, or "none"}

**Recommended action:** {no action | ack/silence + regression note if applicable | route to FE Platform with cookie name(s) | needs cookie audit | flag for human on Error state | monitor}

Runbook: https://app.notion.com/p/apolloio/Runbook-P99-leadgenie-Cookie-Header-Size-Alert-3c3ab2b3b496817f8c99c8a88834083f
```

This skill only investigates and reports — it doesn't silence the alert, change alert config, page anyone, or send Slack messages on its own. If the recommended action involves notifying another team, draft the message and ask before sending it.
