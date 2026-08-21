# Memory Estimation And Headroom

`scripts/memcheck.sh` answers three questions before an exec: how much will this
command need, how much is actually free, and which pod has the most room. The first
answer is a **heuristic**. The other two are measured. Keep that distinction when
reporting to the operator.

## Why The Estimate Cannot Be Exact

Memory use is a property of the snippet, not the command shape. `rails runner` that
prints `Rails.env` and `rails runner` that instantiates 200k ActiveRecord objects are
the same command to any classifier and differ by gigabytes. Nothing can inspect a Ruby
string and know its peak RSS.

So the classes below are **priors**, useful for deciding whether to exec at all or reach
for an ephemeral pod. They are not predictions, and they must never be reported as
measurements.

## Calibration Data

Measured live against `leadgenie` in prod (`gke_indigo-lotus-415_us-central1-c_prod`):

| Pod | Limit | Request | Live usage | Headroom |
|---|---|---|---|---|
| `sidekiq-about-page-scraper-...-tsxf5` | 4Gi | 2560Mi | 2030Mi | ~2066Mi |
| `sidekiq-account-domain-fetcher-...-5r58x` | 4Gi | 3Gi | 2445Mi | ~1651Mi |
| `sidekiq-account-domain-fetcher-...-77trd` | 4Gi | 3Gi | 2162Mi | ~1934Mi |
| `sidekiq-account-domain-fetcher-...-9p28r` | 4Gi | 3Gi | 2293Mi | ~1803Mi |
| `sidekiq-account-domain-fetcher-...-d7bwg` | 4Gi | 3Gi | 2296Mi | ~1800Mi |
| `sidekiq-account-domain-fetcher-...-fm8q5` | 4Gi | 3Gi | 2361Mi | ~1735Mi |

Three things follow, and they drive the whole design:

1. **Headroom is thinner than the limit suggests.** A 4Gi limit sounds roomy; ~1.7–2.0Gi
   is what is actually free. A `rails-query`-class snippet (~1.5Gi) plus the 1.5× safety
   factor does not fit in most of these pods.
1. **Replicas are not interchangeable.** Across five replicas of one Deployment, free
   memory ranged 1651–1934Mi — a ~283Mi spread. Picking the roomiest replica is free and
   is sometimes the difference between fitting and OOMing.
1. **The pod is only half the story.** The incident's first attempt was a container
   OOMKill; the retry was a node-level eviction. Pod headroom said nothing about the
   second. Hence ranking on `min(pod headroom, node headroom)`.

## The Classes

| Class | Default | Reasoning |
|---|---|---|
| `trivial` | 32Mi | A shell and a small binary. Safe in essentially any pod. |
| `light` | 128Mi | Small interpreter or text processing on bounded input. |
| `rails-boot` | 768Mi | Loading the app: gems, initializers, AR schema cache. Paid before your code runs. |
| `rails-query` | 1536Mi | Boot plus result sets, HTTP client buffers, JSON parsing. |
| `heavy` | 3Gi | Bulk work. Assume it does not fit in a live pod; use an ephemeral pod. |

The `1.5` default safety factor exists because peak RSS is transient and `kubectl top`
samples on an interval — you are comparing a spiky number against a stale one. Raise it
when the target is a pod serving traffic.

## Getting A Real Number

When it matters, measure instead of estimating. Run the snippet in an **ephemeral pod in
staging** with an explicit limit and see whether it survives:

```bash
CTX=gke_stage-23704_us-central1-c_staging; NS=leadgenie
kubectl --context "$CTX" -n "$NS" run memprobe-$USER --rm -it --restart=Never \
  --image="$(kubectl --context "$CTX" -n "$NS" get deploy <deploy> \
    -o jsonpath='{.spec.template.spec.containers[0].image}')" \
  --overrides='{"spec":{"containers":[{"name":"probe","image":"IMAGE",
    "resources":{"limits":{"memory":"1Gi"}},
    "command":["bundle","exec","rails","runner","<snippet>"]}]}}'
```

Exit 137 means it needed more than the limit. Bisect the limit until it stops OOMing;
that number, plus a margin, is your real estimate. Do this in staging — the point is to
find the OOM boundary, which is not something to search for in prod.

For a running process, read RSS directly rather than trusting a class:

```bash
kubectl --context "$CTX" -n "$NS" exec <pod> -- ps -o rss=,comm= -p 1
```

## Reporting Rules

- Say "estimated ~768Mi (`rails-boot` heuristic)", never "will use 768Mi".
- Always pair the estimate with both measured numbers: chosen pod headroom and node headroom.
- `memcheck.sh` exit `3` means metrics were unavailable. Unknown usage is **not** zero
  usage — say headroom is undetermined and prefer the ephemeral pod.
- If no pod is viable, recommend the ephemeral pod. Never present the least-bad live pod
  as an option; that is how the retry became an eviction.
