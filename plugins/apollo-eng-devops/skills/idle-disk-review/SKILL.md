---
name: idle-disk-review
description: Review GCP Recommender idle persistent disks in a project, work out why they are stranded, and prepare a gated snapshot-then-delete runbook.
argument-hint: <gcp-project> [--zones us-central1-a,us-central1-b,us-central1-c] [--no-snapshot]
disable-model-invocation: true
---

# Idle Disk Review

Run as `/apollo-eng-devops:idle-disk-review <gcp-project> [--zones ...] [--no-snapshot]`.

Turns the Recommender's `SNAPSHOT_AND_DELETE_DISK` findings into an evidenced
inventory: which disks, what they cost, **why they are stranded**, who to ask,
and a snapshot-then-delete runbook. This skill is **read-only**. It prints the
destructive commands for the user to run and never runs them.

For spend trends and the wider cost sweep, use `gcp-cost-optimization-review`.
For capacity and IOPS sizing, use `disk-inventory`. This skill owns the idle-disk
drill-down only.

## Rules

- Read-only `gcloud` and `kubectl-readonly` only. Never run `disks delete`,
  `snapshots create`, or `kubectl` writes. Print them in separate fenced `bash`
  blocks, one command per block, so the user can run each one.
- Re-pull the Recommender before every report. Findings are refreshed daily, so
  an old manifest can list disks that have since been attached or deleted.
- `--no-snapshot` drops the safety net: the runbook deletes directly and the
  disks cannot be recovered. Default stays snapshot-first. Never infer the flag;
  use it only when the user passes it.
- Never delete on Recommender output alone. "Idle" means no attached VM, not
  "safe to delete". Establish the cause first (Step 3).
- Production projects are read-only unless the user explicitly says otherwise.

## Steps

1. **Pull findings.** Per zone in `--zones` (default: every zone with disks):

   ```bash
   gcloud recommender recommendations list --project=<p> --location=<zone> \
     --recommender=google.compute.disk.IdleResourceRecommender \
     --filter="stateInfo.state=ACTIVE AND recommenderSubtype=SNAPSHOT_AND_DELETE_DISK" \
     --format=json
   ```

   Cost is `primaryImpact.costProjection.cost` (negative = savings, per 30
   days). Note which projects the sweep did **not** cover: the Recommender API
   can be off or permission-denied, and an empty result is not a clean bill.

1. **Enrich.** `gcloud compute disks list --project=<p> --format=json`, joined
   on disk name. Capture size, type, `creationTimestamp`, `lastDetachTimestamp`,
   `users` (must be empty), `labels`, and the `description` JSON, which for
   PVC-backed disks holds `kubernetes.io/created-for/pvc/{namespace,name}`.

1. **Find why they are stranded.** Group disks by owner and look for the cause:

   - **Cluster gone.** Compare the disks' `goog-gke-cluster-id-base32` label to
     the live cluster's ID (`gcloud container clusters describe <c> --format='value(id)'`,
     hex to lowercase base32). A mismatch means the disks belong to a deleted
     cluster. GKE does not delete PD-CSI volumes when a cluster is deleted.
   - **Audit trail.** Confirm with
     `gcloud logging read 'protoPayload.methodName=~"DeleteCluster|CreateCluster" AND protoPayload.serviceName="container.googleapis.com"'`
     over the window around `lastDetachTimestamp`. This names who deleted it and when.
   - **PVC left behind.** For disks of a live cluster, check PV/PVC state with
     `kubectl-readonly get pv,pvc -A`. A `Released` PV, or a PVC with no pod,
     means a workload was scaled down or removed and the PVC outlived it.
   - **Unknown.** No labels and no PVC metadata: report "owner unknown" and
     keep the disk out of the delete batch.

   Private-endpoint clusters are unreachable without VPN. Say so and mark the
   PV check as open instead of working around it.

1. **Recheck attachment.** For every candidate, `gcloud compute disks describe <d> --zone=<z> --format='value(users)'` must be empty immediately before any
   delete. Also list disks that are detached but **not** Recommender-flagged;
   report them separately and do not include them in the batch.

1. **Find owners.** Name the person or team to confirm with: the actor on the
   cluster delete audit event, the PR that replaced the cluster
   (`git log`/Glean), and the owning team for the namespace.

1. **Report.** Output: a one-line BLUF (count, $/month, cause), a table
   grouped by cause with name, zone, size, type, detached date, cost and
   PVC, a "confirm first / safe / leave alone" split, and the open
   verifications. Keep the full per-disk list in a code block so it can be
   pasted into a Jira comment.

1. **Ticket.** Check Jira for an existing ticket before proposing one
   (`INFRA` project: search "idle disk", the project name, and the cluster name).
   If none exists, propose a ticket and link it to related snapshot or
   cost-cleanup tickets.

1. **Runbook.** Print the gated snapshot, verify, batched-delete, and rollback
   commands from [references/runbook.md](references/runbook.md), filled in with
   the project and manifest path. Delete only after the snapshots verify READY,
   the attachment recheck passes, and the owner has confirmed.

   With `--no-snapshot`, print the "No-snapshot variant" from the runbook
   instead: no snapshot or snapshot-verify phase, and the delete loop re-checks
   that `users` is empty per disk immediately before each delete and skips any
   attached disk. In the report, state in one line that rollback is lost (the
   disks cannot be recovered) and record the evidence being relied on (cluster
   gone, disks empty or disposable, owner ack). Suggest snapshotting only 2-3
   sample disks as a cheaper alternative. Still print every command in its own
   fenced `bash` block and never run it.

## Gotchas

- `lastDetachTimestamp` equal to `creationTimestamp` means the disk was never
  attached long enough to matter. Good candidates, but still check the cause.
- Disks created by a stateful workload may still be referenced by a `Retain`
  PV. Delete the PVC and PV first so Kubernetes is not left pointing at a
  missing disk.
- Snapshots cost money too. Use a single storage location and a retention
  window, and note both in the ticket.
- The Recommender can flag only some of a workload's detached disks.
  Unflagged detached disks are usually recent detaches, not safe ones.
