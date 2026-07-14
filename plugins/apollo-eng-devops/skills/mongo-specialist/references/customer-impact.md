# Quantifying Customer Impact

Turn raw error metrics into a defensible impact statement for the IC, the status page,
and Support. Do the math against metrics, not narrative memory, and anchor the window to
metric/log epochs.

## Metrics to pull

Over the incident window (start → recovery), compared against a same-length baseline just
before onset:

- **Total excess failures**: `increase()` of edge 5xx / tunnel 500s over the window,
  minus the baseline rate extrapolated over the same duration.
- **% of total requests**: excess failures ÷ total requests in the window.
- **Split by tunnel**: break 5xx out **by tunnel** (app vs extension) — impact and
  audience differ, and aggregates hide a single affected surface.
- **Top-k affected transactions**: `topk(10, ...)` on the failing transactions to name
  what customers actually hit.

Example PromQL shapes (adjust metric/labels to the live dashboard):

```promql
# excess failures over the window, per tunnel
sum by (tunnel) (increase(cloudflared_tunnel_response_by_code{status=~"5.."}[$__range]))
# share of total requests
sum(increase(cloudflared_tunnel_response_by_code{status=~"5.."}[$__range]))
  / sum(increase(cloudflared_tunnel_response_by_code[$__range]))
# worst-hit transactions
topk(10, sum by (transaction) (increase(http_requests_total{status=~"5.."}[$__range])))
```

## Framing

- **Retries typically succeeded when only a subset of pods/mongos were affected** — raw
  5xx counts overstate user-visible impact when the client retried and the second
  attempt hit a healthy path. Say this explicitly so the number isn't misread as
  failed user actions.
- Distinguish **requests failed** from **users affected** and **actions lost** — a user
  hitting 5 failed requests that all retried successfully lost nothing.

## Support-ready summary format

Mirror the INCIDENT-31301 close-out summary:

> Between `<start>` and `<end>` (`<duration>`), roughly **`<N>` excess request failures**
> occurred (~`<X>`% of total traffic in the window), concentrated in `<tunnel/surface>`.
> Most retries succeeded, so user-visible impact was limited to `<who/what>`. No data
> loss. Root cause: `<one internal line — keep out of any customer-facing copy>`.

Reference figures from INCIDENT-31301 for calibration: ~23.6k excess failures, ~0.09% of
traffic — a small fraction of total volume, which is the point of quoting the percentage
alongside the raw count.

Keep the internal root-cause line out of status-page and Support-facing copy; see
[`status-page.md`](status-page.md) for customer-safe wording.
