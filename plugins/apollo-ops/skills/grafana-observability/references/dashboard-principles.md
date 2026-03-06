# Dashboard Design Principles

Guidelines for building Grafana dashboards that are useful during normal operation and invaluable during incidents.

---

## Framework Selection

### USE Method — for infrastructure resources

Apply USE to anything that is a resource (CPU, memory, disk, network, connection pools).

- **Utilization**: percentage of capacity being used (e.g., CPU at 70%)
- **Saturation**: work queued or waiting because resource is fully utilized (e.g., CPU run queue)
- **Errors**: error events from the resource (e.g., disk I/O errors, network drops)

USE panels belong in: node dashboards, database dashboards, connection pool dashboards.

### RED Method — for services

Apply RED to anything that processes requests or jobs.

- **Rate**: requests or jobs per second
- **Errors**: error count or error rate (%)
- **Duration**: latency (show p50 and p99)

RED panels belong in: HTTP service dashboards, Sidekiq dashboards, consumer dashboards.

---

## Dashboard Layout

**Above the fold (immediately visible)**:
1. Service health indicator (green/yellow/red status panel)
2. RED metrics: request rate, error rate, p99 latency
3. Active alerts panel (if using Grafana alerting)

**Middle (scroll to reach)**:
4. Saturation metrics: CPU, memory, queue depth
5. Dependency health: downstream service error rates

**Below the fold (drill-down only)**:
6. Internal state metrics: JVM heap, connection pool stats, shard counts
7. Debug panels: raw log volume, specific error breakdowns

The above-the-fold zone should answer "is this service healthy right now?" in under 10 seconds.

---

## Time Range Defaults

Set default time ranges that match how the dashboard is used:

| Use case | Default time range | Reason |
|----------|-------------------|--------|
| Service health overview | Last 1 hour | Shows recent changes clearly |
| Incident triage | Last 5 minutes | Tight zoom on current state |
| Trend / capacity planning | Last 7 days or 30 days | Long-range view |
| Weekly review | Last 7 days | Aligned with sprint cadence |

Set `auto-refresh` to off by default on historical dashboards, on for live incident dashboards (15s or 30s refresh).

---

## Annotation Overlays

Deploy annotations are required on all service dashboards. They allow instant visual correlation between a deploy and a metric change — the most common incident root cause.

**Configure Grafana annotations datasource** to pull from your deployment event stream. Each annotation should include:
- Deploy time
- Service name and version
- Deployer name (for follow-up)

During incidents, look at the annotation overlay before hypothesizing a root cause. If the metric change correlates with a deploy annotation, rollback is the first mitigation to consider.

---

## Variable Templates

Use dashboard variables to avoid duplicating dashboards across environments:

```
$env        = production | staging
$cluster    = <GKE cluster name>
$namespace  = <Kubernetes namespace>
$service    = <service name>
$region     = <GCP region>
```

Variables should cascade: selecting `$env=staging` should filter `$cluster` to staging clusters only.

---

## Apollo-Specific Panel Guidance

### Elasticsearch dashboards

Essential panels for each ES cluster (`main`, `activities`, `field-enrichment`, `custom-objects`):

| Panel | Metric | Alert threshold |
|-------|--------|-----------------|
| Cluster health | `elasticsearch_cluster_health_status` | Yellow = P2, Red = P1 |
| Shard health | Unassigned shard count | > 0 for > 5 min = P2 |
| Indexing rate | `elasticsearch_indices_indexing_index_total` rate | Dashboard only |
| Query latency p99 | `elasticsearch_indices_search_query_time_seconds` | > 2s = P2 |
| JVM heap usage | `elasticsearch_jvm_memory_used_bytes` / max | > 85% = P2 dashboard panel |
| Search rejected | `elasticsearch_thread_pool_search_rejected` | > 0 = P2 |
| Bulk rejected | `elasticsearch_thread_pool_bulk_rejected` | > 0 = P2 |

JVM heap is a cause-based metric — it belongs in the dashboard as a diagnostic panel, not as a P1 alert.

### MongoDB dashboards

| Panel | Metric | Notes |
|-------|--------|-------|
| Operation counters | `mongodb_ss_opcounters` | Rate per operation type |
| Query latency | `mongodb_ss_opLatencies_reads_latency` | p99, microseconds |
| Write latency | `mongodb_ss_opLatencies_writes_latency` | p99, microseconds |
| Replication lag | `mongodb_rs_members_optimeDate` delta | Alert if > 60s |
| Connections | `mongodb_ss_connections_current` | Dashboard panel |
| Cache ratio | WiredTiger cache read ratio | Dashboard panel |

### Sidekiq dashboards

| Panel | Metric | Alert threshold |
|-------|--------|-----------------|
| Queue depth | Per-queue enqueued count | Alert on growth rate, not absolute |
| Job latency | Time in queue before processing | p99 > 2x baseline = P2 |
| Job failure rate | Failed job count rate | > baseline = P2 |
| Retry queue depth | Retries count | Growing = P2 |
| Dead queue depth | Dead jobs count | > 0 = P2 (jobs are permanently failing) |
| Worker utilization | Busy workers / total workers | > 90% sustained = P2 |

### Redpanda / Kafka consumer dashboards

| Panel | Metric | Alert threshold |
|-------|--------|-----------------|
| Consumer lag | Per consumer group, per topic | Growing for > 10 min = P2 |
| Throughput | Messages consumed per second | Dashboard only |
| Producer throughput | Messages produced per second | Dashboard only |
| Consumer group offset | Current offset vs log end offset | Feeds lag calculation |

Show consumer lag as a time-series panel, not just a current value — the trend (growing, stable, recovering) is more diagnostic than the current number.
