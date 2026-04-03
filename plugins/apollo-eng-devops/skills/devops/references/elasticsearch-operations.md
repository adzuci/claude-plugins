# Elasticsearch Operations

Apollo ES cluster landscape, backup/restore workflows, and operational checklists.

______________________________________________________________________

## Cluster Landscape

### Production Clusters

GCP project: `indigo-lotus-415`, zone: `us-central1-c`.

| Cluster | Internal searcher URL | Key indices |
|---|---|---|
| `main` | `http://elasticsearch-main.us-central1-c.c.indigo-lotus-415.internal:9200` | Core search indices |
| `activities` | `http://elasticsearch-activities.us-central1-c.c.indigo-lotus-415.internal:9200` | Activity feed indices |
| `field-enrichment` | `http://elasticsearch-field-enrichment.us-central1-c.c.indigo-lotus-415.internal:9200` | Field enrichment pipeline indices |
| `custom-objects` | `http://elasticsearch-custom-objects.us-central1-c.c.indigo-lotus-415.internal:9200` | Custom object search indices |

### Staging Clusters

Same cluster names (`main`, `activities`, `field-enrichment`, `custom-objects`). Internal IPs in `10.129.x.x` range (same name scheme, different IPs).

### Sharding

- Some indices have 1–300 shards (contacts and accounts indices use one shard per Mongo shard)
- Shard count decisions owned by Search Platform; shard plan at `config/es_sharding_plan` in `leadgenie` repo
- Do not adjust shard counts without Search Platform sign-off

______________________________________________________________________

## Authentication

- All credentials via GitHub Secrets — no credentials in the repo
- Staging: workload identity federation (no static service account keys)
- Prod: GCP service accounts

______________________________________________________________________

## Backup Workflow

**Workflow file**: `prod-elasticsearch-backup.yml`
**Schedule**: `0 23 * * *` (23:00 UTC nightly)
**Scope**: All 4 production clusters (matrix job)
**Destination**: GCS (Google Cloud Storage snapshots)
**Failure alerting**: `#eng-infrastructure-alerts` + `@oncall-xfn-team-devops`

### What a healthy backup run looks like

- One job per cluster runs at 23:00 UTC
- Each job: registers GCS snapshot repository → creates snapshot → waits for completion
- Snapshots are named with a date suffix; old snapshots may be pruned per retention policy
- Successful run = 4 cluster snapshots written to GCS

### Diagnosing backup failures

- Check `#eng-infrastructure-alerts` for the failure message — it will identify which cluster failed
- A Saturday failure is expected noise if the weekly staging refresh is running (ES is mid-restore); verify by cross-referencing with staging refresh schedule
- Non-Saturday failures: check ES cluster health on the failing cluster first (`GET _cluster/health`)
- If cluster is yellow/red: snapshot API will refuse to run; resolve cluster health before retrying backup
- GCS auth failures: check service account permissions for the prod ES service account; do not store new credentials in repo

______________________________________________________________________

## Staging Refresh Workflow

**Workflow file**: `refresh-staging-databases.yml`
**Schedule**: `0 17 * * 6` (Saturday 17:00 UTC)
**Failure alerting**: `#eng-infrastructure-alerts`

### Refresh sequence (in order)

| Step | Action | Notes |
|---|---|---|
| 1 | Redis `FLUSHALL ASYNC` | Clears staging Redis; expected and intentional |
| 2 | Ansible: provision and configure staging DBs | Uses `ansible/` in devops repo |
| 3 | ES restore from last successful prod snapshot | All 4 clusters restored |
| 4 | ES index reset Kubernetes Job | Runs in `preview-master` namespace on staging cluster |
| 5 | Failure | Slack alert to `#eng-infrastructure-alerts` |

### Saturday noise rule

If the backup workflow fires a failure alert on **Saturday between 17:00–22:00 UTC**, check whether the staging refresh is mid-run before escalating. The refresh runs ES restores, which can cause snapshot operations to fail or timeout. This is expected. Wait for the refresh to complete and verify backup success on Sunday.

______________________________________________________________________

## Operational Checklists

### Before Any ES Index Operation

- [ ] Check cluster health: `GET _cluster/health` — must be `green` before proceeding; `yellow` = caution; `red` = stop
- [ ] Check pending tasks: `GET _cluster/pending_tasks` — long queue = cluster under stress, hold
- [ ] Check unassigned shards: `GET _cat/shards?v&h=index,shard,prirep,state,unassigned.reason` — unassigned shards indicate a degraded cluster
- [ ] Confirm which cluster you are targeting (prod vs staging; which of the 4 clusters)
- [ ] For shard count or mapping changes: get Search Platform or BE-Platform sign-off first
- [ ] Record cluster health state before the operation for post-op comparison

### Diagnosing ES Backup Failures

1. **Is it Saturday 17:00–22:00 UTC?** → likely staging refresh interference; check refresh status before escalating
1. **Which cluster failed?** → Check `#eng-infrastructure-alerts` for the cluster name
1. **Check cluster health** on the failing cluster: red/yellow = backup will not run
1. **Check GCS bucket accessibility** if cluster health is green: could be IAM or network issue
1. **Check prior context**: is there a known incident for this cluster in Slack or PagerDuty?
1. **Retry**: if cluster health resolves, manually trigger the backup workflow for the affected cluster
1. **Escalate to DevOps** if: cluster is red, GCS auth is broken, or same cluster fails 2+ consecutive nights

### ES Index Reset Job in `preview-master`

The ES index reset Kubernetes Job runs during the weekly staging refresh in the `preview-master` namespace on the staging GKE cluster.

**Expected**: Job appears and completes (status `Complete`) every Saturday during the refresh window.
**Unexpected**: Job fails (`status: Failed`), runs outside of Saturday, or appears in prod cluster namespaces.

If the job is stuck or failing on staging:

- Check job logs: `kubectl logs -n preview-master job/<job-name>`
- Verify the ES restore (Step 3) completed successfully before the job ran — the index reset depends on restored data
- If ES restore is still in progress, the job may have started too early; delete the failed job and re-run after restore

If a similar job appears in a prod namespace: treat as a potential incident; investigate before taking action.

### Ownership Decision Tree

Use this to determine who to contact for an ES issue:

```
ES issue
├── Cluster is red/yellow → DevOps (infra)
│   └── Node failures, disk full, out of memory
├── Backup failure → DevOps (infra)
│   └── Unless it's Saturday noise (see Saturday rule above)
├── Shard imbalance / hot shards → Search Platform
│   └── Shard plan at config/es_sharding_plan in leadgenie repo
├── Mapping errors / ingest pipeline failures → BE-Platform (Neil, Ken)
│   └── App-level ES concerns
├── Index count / shard count decision → Search Platform
│   └── Needs sign-off before any shard count change
└── Let's Encrypt / TLS on ES endpoints → Engagement team
```

### When to Escalate vs Self-Resolve

| Situation | Action |
|---|---|
| Cluster `yellow` with unassigned replicas only, no impact | Monitor; self-resolve if primaries are all assigned |
| Cluster `yellow` with unassigned primaries | Escalate to DevOps immediately |
| Cluster `red` | Escalate to DevOps immediately; declare incident if user impact |
| Backup failed on Saturday during refresh window | Wait; verify Sunday backup; escalate if Sunday also fails |
| Backup failed on non-Saturday | Investigate cluster health; escalate to DevOps if cluster issue |
| Index operation failed with 503/429 | Cluster under load; hold operation; do not retry in a loop |
| Staging ES slow/unavailable on Saturday | Expected during refresh; check refresh status before reporting |
