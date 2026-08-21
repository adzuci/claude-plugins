# Namespaces And Contexts

Guard rail for validating `-n <namespace>` before running anything. This table can drift — clusters gain and lose namespaces — so treat a miss as "confirm live," not "impossible."

## Contexts

| Env arg | kubectl context |
|---|---|
| `prod` | `gke_indigo-lotus-415_us-central1-c_prod` |
| `stage` | `gke_stage-23704_us-central1-c_staging` |

Context names vary per engineer's kubeconfig, so `scripts/preflight.sh` resolves them from `kubectl config get-contexts` rather than assuming these strings.

Contexts commonly present in an Apollo engineer's kubeconfig that are **not** valid targets for this skill — reject them:

- `gke_apollo-ops_us-central1-c_ops`
- `gke_apollo-cdc_us-central1-c_kafka-connect`
- `dev`
- `colima`

## Prod Namespaces

`leadgenie` is the main application namespace.

```text
airbyte            api-dev-portal     arc-runners-test   cdp-ingest
cert-manager       cloudflare         custom-metrics     default
discovery          gmp-public         gmp-system         keda
kodem              kube-node-lease    kube-public        kube-services
kube-system        kyverno            leadgenie          leadgenie-beta
marketing          mint-security      monitoring         nl-search
observability      opencost           orcasecurity       pricus
qpoint             resolve            security           tracking-tls
vendor-egress      web-scraper
```

Plus `gke-managed-*` system namespaces. There are no dynamic namespace patterns in prod.

## Staging Namespaces

Fixed:

```text
airbyte            cdp-ingest         cerebro            cert-manager
cloudflare         db-migration       default            fabric-core-docs
gcs-proxy          gpu-operator       helios-stage       infini
keda               kube-node-lease    kube-public        kube-services
kube-system        kyverno            leadgenie          monitoring
nginx-gateway      nl-search          observability      opencost
orcasecurity       pulse              qpoint             rajesh-test
staging            test-node-pool     tracking-tls       transcend
vendor-egress      web-scraper
```

Plus `gke-managed-*` system namespaces.

Dynamic patterns (staging only):

| Pattern | What it is | Scale at time of writing |
|---|---|---|
| `preview-*` | Per-PR preview environments, e.g. `preview-master`, `preview-acore-2372` | ~138 live |
| `fabric-studio-*` | Per-prototype Fabric Studio environments | ~55 live |

`preview-*` namespaces are ephemeral and get reaped when their PR closes or goes stale. Always confirm existence before use:

```bash
kubectl --context gke_stage-23704_us-central1-c_staging get ns <namespace>
```

A PR's preview namespace is commented on the PR by the `apolloio-ci` bot. If there is no comment, add the `Need_Preview_Env` label to the PR.

## Asymmetries To Watch

- `leadgenie` exists in **both** prod and staging. A namespace matching in one environment says nothing about which cluster you are pointed at — this is why the `stage|prod` argument is mandatory.
- `preview-*` and `fabric-studio-*` are **staging only**. One of these passed with `prod` means the operator confused environments. Reject and ask them to re-run against `stage`.
- Prod-only: `leadgenie-beta`, `marketing`, `pricus`, `resolve`, `discovery`.

## Do Not Enumerate Deployments

Prod `leadgenie` alone has over 750 Deployments. Listing them is expensive and useless as validation. Namespace-level validation is the right granularity; resolve deployment and pod existence live against the specific name the operator gave you.

## Refreshing This Table

```bash
kubectl --context <ctx> get ns
```

For staging, separate the fixed set from the dynamic patterns:

```bash
kubectl --context gke_stage-23704_us-central1-c_staging get ns -o name \
  | sed 's|namespace/||' \
  | grep -vE '^(preview-|fabric-studio-|gke-managed-)'
```
