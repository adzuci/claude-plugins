# GKE Version + EOL Report

Exact commands, sample output, and EOL flag thresholds for the `--versions` mode of `scripts/gke_versions_report.py`. All commands in this file are read-only against GCP.

______________________________________________________________________

## Flow 1: Base Report

```bash
python3 scripts/gke_versions_report.py --versions
```

Reads the seed project list from `scripts/gke_clusters.json`, runs `gcloud container clusters list --project <P> --format=json` for each, and fetches Kubernetes minor-version EOL dates from `https://endoflife.date/api/v1/products/kubernetes/` (cached to disk for 24h). Prints a single markdown table, flagged clusters sorted first:

```
| Project | Cluster | Location | Master Version | Node Version | Status | EOL Date | Flag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| indigo-lotus-415 | prod-main | us-central1 | 1.30.5-gke.1443001 | 1.30.5-gke.1443001 | RUNNING | 2025-06-28 | 🔴 **PAST EOL** |
| apollo-ops | mimir | us-central1 | 1.33.2-gke.1240000 | 1.33.2-gke.1240000 | RUNNING | 2026-06-28 | 🟡 EOL soon |
| stage-23704 | staging | us-central1-c | 1.34.9-gke.1065000 | 1.34.8-gke.1278000 | RUNNING | 2026-10-27 |  |
```

### Flag thresholds

| Flag | Meaning |
|---|---|
| 🔴 **PAST EOL** | The cluster's minor version's `eolFrom` date is today or earlier — no more patches from upstream. |
| 🟡 EOL soon | `eolFrom` is within 60 days from now. |
| _(blank)_ | Minor version is supported (or not yet in the EOL dataset — e.g. a version newer than endoflife.date has published). |

To scope the report to one project instead of the seed list:

```bash
python3 scripts/gke_versions_report.py --versions --project <PROJECT_ID>
```

______________________________________________________________________

## Flow 2: Refresh the Seed Inventory (`--refresh`)

```bash
python3 scripts/gke_versions_report.py --versions --refresh
```

In addition to the base report, this probes every GCP project visible to the caller (`gcloud projects list`) for clusters not already in `scripts/gke_clusters.json`, and prints a diff section:

```
## --refresh: projects with GKE clusters not in gke_clusters.json

- `some-new-project`: cluster-a, cluster-b
```

This does **not** auto-write to `gke_clusters.json`. Review the diff, then add confirmed entries to the seed file by hand in a follow-up commit — this keeps the common case (`--versions` with no flags) fast instead of sweeping ~140 projects (most without GKE clusters) on every run.

______________________________________________________________________

## Flow 3: Deprecated API Scan (`--kubent`)

Run after the base report to check flagged clusters for use of Kubernetes APIs that will break on upgrade, using [kubent (kube-no-trouble)](https://github.com/doitintl/kube-no-trouble) — a read-only scanner.

Install once:

```bash
brew install kubent
```

Scan every 🔴/🟡 flagged cluster from the base report:

```bash
python3 scripts/gke_versions_report.py --versions --kubent
```

Scan a single cluster directly:

```bash
python3 scripts/gke_versions_report.py --kubent --project <PROJECT_ID> --cluster <CLUSTER_NAME> --location <LOCATION>
```

For each target, this runs:

```bash
gcloud container clusters get-credentials <cluster> --project <project> --location <location>
kubent --context gke_<project>_<location>_<cluster> -o json -e
```

`get-credentials` only switches the local kubeconfig context — it does not modify the cluster. `kubent` itself only reads API usage from the audit/discovery API; it never applies, deletes, or drains anything. Sample output per cluster:

```json
{
  "1.29": [
    {
      "ObjectName": "my-old-webhook",
      "ObjectNamespace": "default",
      "Kind": "MutatingWebhookConfiguration",
      "Deprecated": true,
      "RuleSet": {"ApiVersion": "admissionregistration.k8s.io/v1beta1"}
    }
  ]
}
```

If `kubent` isn't installed, the command prints an install hint instead of failing silently.
