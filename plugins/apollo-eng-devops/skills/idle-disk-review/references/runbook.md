# Idle Disk Snapshot and Delete Runbook

Print these for the user to run. Do not run them from the skill. Replace
`<project>`, `<ticket>` and the manifest path. The manifest is `name,zone` per
line, built from the reviewed inventory (never from the raw Recommender output).

Preconditions: owner confirmed, attachment recheck clean, PV/PVC check done (or
explicitly waived because the owning cluster is deleted), peer review recorded
on the ticket.

1. Confirm no disk is attached (expect `0`):

   ```bash
   while IFS=, read -r d z; do gcloud compute disks describe "$d" --zone="$z" --project=<project> --format='value(users)'; done < manifest.csv | grep -c .
   ```

1. Snapshot every disk. Reversible. Skips any disk that is now attached:

   ```bash
   while IFS=, read -r d z; do [ -z "$(gcloud compute disks describe "$d" --zone="$z" --project=<project> --format='value(users)')" ] || { echo "ATTACHED, SKIP: $d"; continue; }; gcloud compute disks snapshot "$d" --zone="$z" --project=<project> --snapshot-names="idle-$d" --storage-location=us --labels=ticket=<ticket>; done < manifest.csv
   ```

1. Verify the count equals the manifest length:

   ```bash
   gcloud compute snapshots list --project=<project> --filter="name~^idle- AND status=READY AND labels.ticket=<ticket>" --format="value(name)" | wc -l
   ```

1. Delete the first batch of 10. **Destructive.** Run only after step 3 matches:

   ```bash
   head -10 manifest.csv | while IFS=, read -r d z; do gcloud compute disks delete "$d" --zone="$z" --project=<project> --quiet; done
   ```

   Later batches: replace `head -10` with `sed -n '11,20p'`, then `'21,30p'`, and so on.

1. Verify the disks are gone and no delete operation is failing:

   ```bash
   gcloud compute operations list --project=<project> --filter="operationType=delete AND status!=DONE" --format="table(name,operationType,status,error.errors[].message)"
   ```

## No-snapshot variant

Used only with `--no-snapshot`. Skips steps 2 and 3. **Rollback is lost: the
Rollback section below does not apply**, and deleted disks cannot be recovered.
Run step 1 first. The loop re-checks `users` per disk right before each delete
and skips any attached disk.

Delete the first batch of 10. **Destructive.**

```bash
head -10 manifest.csv | while IFS=, read -r d z; do [ -z "$(gcloud compute disks describe "$d" --zone="$z" --project=<project> --format='value(users)')" ] || { echo "ATTACHED, SKIP: $d"; continue; }; gcloud compute disks delete "$d" --zone="$z" --project=<project> --quiet; done
```

Later batches: replace `head -10` with `sed -n '11,20p'`, then `'21,30p'`, and so on.

Verify no delete operation is failing:

```bash
gcloud compute operations list --project=<project> --filter="operationType=delete AND status!=DONE" --format="table(name,operationType,status,error.errors[].message)"
```

## Rollback

Snapshot-first runbook only.

Recreate a disk from its snapshot:

```bash
gcloud compute disks create <disk> --source-snapshot=idle-<disk> --zone=<zone> --type=pd-ssd --project=<project>
```

Delete the `idle-` snapshots after the agreed retention window.
