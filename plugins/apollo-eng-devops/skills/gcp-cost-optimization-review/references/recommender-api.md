# Pulling FinOps Hub Recommendations Headlessly (Recommender API)

## The short answer

**There is no `gcloud finops-hub` command.** The Console's FinOps Hub
(`console.cloud.google.com/billing/0174D0-6590F0-824CC0/optimize`) is a **presentation layer** over the
Recommender API. Its headline tiles — active recommendation count, potential monthly savings, CUD
optimization rate, FinOps maturity score — are computed **in the Console** and are not exposed by any
API or CLI.

What *is* available headlessly is the underlying recommendation corpus, via:

```
gcloud recommender recommendations list \
  --project=<PROJECT_ID> --location=<LOCATION> --recommender=<RECOMMENDER_ID> --format=json
```

To reproduce the Hub's "$X/mo potential savings" you must sweep the
**project × location × recommender** matrix yourself and sum
`primaryImpact.costProjection.cost`. That is what the script below does.

**Expect your sweep total to be lower than the Console's.** See "Known coverage gap" below.

______________________________________________________________________

## Verified state (2026-09-05, `indigo-lotus-415`)

| Check | Result |
| --- | --- |
| `recommender.googleapis.com` | **Enabled** ✅ |
| `google.compute.disk.IdleResourceRecommender` @ `us-central1-c` | Returns results ✅ |
| `google.compute.address.IdleResourceRecommender` @ `us-central1` | Returns results ✅ |
| `google.compute.instance.MachineTypeRecommender` @ `us-central1-b` | `Listed 0 items` |
| `google.compute.instance.IdleResourceRecommender` @ `us-central1-c` | `Listed 0 items` |
| `google.compute.commitment.UsageCommitmentRecommender` @ `us-central1` | `Listed 0 items` |
| `google.cloudbilling.commitment.SpendBasedCommitmentRecommender` @ billing-account/`global` | `Listed 0 items` |
| `google.cloudbilling.commitment.SpendBasedCommitmentRecommender` @ project/`global` | `INVALID_ARGUMENT` (wrong scope) |
| `google.cloudbilling.billingaccount.CostAnomalyInsight` @ billing-account/`global` | `INVALID_ARGUMENT` |
| `billingbudgets.googleapis.com` | **Not enabled** on `indigo-lotus-415` ❌ |

Sample confirmed results:

```
SNAPSHOT_AND_DELETE_DISK  P4  $2.99/mo   idle persistent disk 'pritunl-0-disk-23-01-2026'
DELETE_ADDRESS            P4  $5.98/mo   idle IP address 'prod-aplolinks-lb-ip'
```

`Listed 0 items` is a **success with no findings**, not an error — distinguish it from a non-zero
exit. The most common cause of a false zero is querying the wrong location scope.

______________________________________________________________________

## Location scope — the #1 source of false zeros

Each recommender is published at exactly one scope. Query the wrong one and you get a clean,
misleading `Listed 0 items`.

| Recommender | Scope | Locations to sweep |
| --- | --- | --- |
| `google.compute.disk.IdleResourceRecommender` | **zonal** | `us-central1-a/b/c/f`, `us-east1-b/c/d` |
| `google.compute.instance.IdleResourceRecommender` | **zonal** | same |
| `google.compute.instance.MachineTypeRecommender` | **zonal** | same |
| `google.compute.address.IdleResourceRecommender` | **regional** | `us-central1`, `us-east1` |
| `google.compute.commitment.UsageCommitmentRecommender` | **regional** | `us-central1`, `us-east1` |
| `google.cloudsql.instance.IdleRecommender` | **regional** | `us-central1`, `us-east1` |
| `google.compute.image.IdleResourceRecommender` | `global` | `global` |
| `google.cloudbilling.commitment.SpendBasedCommitmentRecommender` | **billing-account** + `global` | requires `--billing-account`, not `--project` |

Idle disks are zonal. A sweep that hits only `us-central1` finds none of them and reports "$0 of idle
disk savings" — which is wrong, not empty.

Full recommender catalogue: https://cloud.google.com/recommender/docs/recommenders

______________________________________________________________________

## Extracting the savings figure

`primaryImpact.costProjection.cost` is a `google.type.Money`:

```json
"costProjection": {
  "cost": { "currencyCode": "USD", "units": "-5", "nanos": -976000000 },
  "duration": "2592000s"
}
```

- **Negative means a saving.** Negate it for reporting.
- `units` + `nanos / 1e9` combine to the dollar amount (`-5` + `-0.976` = `-$5.976`).
- `units` arrives as a **string** — `tonumber` it in jq or it silently concatenates.
- `duration: 2592000s` = 30 days, so the value is already **monthly**. Do not re-scale it.
- `units` is absent (not `0`) when the amount is under $1 — the `// 0` defaults below handle this.

Working jq extraction (verified):

```bash
jq -r '.[]? | [
  .recommenderSubtype,
  .priority,
  ((((.primaryImpact.costProjection.cost.units // 0) | tonumber)
    + ((.primaryImpact.costProjection.cost.nanos // 0) / 1e9)) * -1 | tostring),
  .description
] | @tsv'
```

**jq gotcha:** `(x | tostring, .description)` parses as a stream and fails with
`Cannot index string with string "description"`. Keep `tostring` inside its own parenthesised
expression, as above.

______________________________________________________________________

## Sweep script (verified)

Save as `/tmp/gcp-rec-sweep.sh`, `chmod +x`, run. Read-only.

```bash
#!/usr/bin/env bash
# Read-only sweep of GCP Recommender cost recommendations.
# Output: TSV — project, location, recommender, subtype, priority, monthly_savings_usd, description
set -uo pipefail

PROJECTS="${PROJECTS:-indigo-lotus-415 apollo-ops stage-23704 apollo-data-platform-prod apollo-data-platform-stg apollo-cdc apollo-backup-007 apollo-ai-tooling}"
ZONES="${ZONES:-us-central1-a us-central1-b us-central1-c us-central1-f us-east1-b us-east1-c us-east1-d}"
REGIONS="${REGIONS:-us-central1 us-east1}"

ZONAL_RECS="google.compute.disk.IdleResourceRecommender
google.compute.instance.IdleResourceRecommender
google.compute.instance.MachineTypeRecommender"

REGIONAL_RECS="google.compute.address.IdleResourceRecommender
google.compute.commitment.UsageCommitmentRecommender
google.cloudsql.instance.IdleRecommender"

GLOBAL_RECS="google.compute.image.IdleResourceRecommender"

JQ_FMT='.[]? | [ $p, $l, ($r | split(".") | .[-2:] | join(".")), .recommenderSubtype, .priority,
  ((((.primaryImpact.costProjection.cost.units // 0) | tonumber)
    + ((.primaryImpact.costProjection.cost.nanos // 0) / 1e9)) * -1 | tostring),
  .description ] | @tsv'

fetch() {  # project location recommender
  local out err rc
  err=$(mktemp)
  out=$(timeout 60 gcloud recommender recommendations list \
        --project="$1" --location="$2" --recommender="$3" \
        --filter="stateInfo.state=ACTIVE" --format=json --quiet 2>"$err")
  rc=$?
  # --quiet suppresses gcloud's interactive "API not enabled, enable and retry? (y/N)" prompt.
  # Without it, a just-enabled (still propagating) or never-enabled API causes gcloud to block
  # on stdin with no TTY present, burning the full 60s timeout per call instead of failing in ~1s
  # with the real error. Confirmed this failure mode live against apollo-cdc (rc=124, prompt text
  # captured in $err) shortly after enabling recommender.googleapis.com there.
  if [ "$rc" -ne 0 ]; then
    # A real failure (permission denied, API disabled, timeout, network) — NOT a "0 items"
    # success. Emitting this on stderr with a SCANFAIL tag keeps stdout's TSV clean while
    # making the failure impossible to silently miss. Never treat this the same as an empty result.
    printf 'SCANFAIL\tproject=%s\tlocation=%s\trecommender=%s\trc=%s\treason=%s\n' \
      "$1" "$2" "$3" "$rc" "$(tr '\n' ' ' < "$err" | cut -c1-200)" >&2
    rm -f "$err"
    return 0
  fi
  rm -f "$err"
  [ -z "$out" ] || [ "$out" = "[]" ] && return 0  # genuine "0 items" — a real, trustworthy success
  echo "$out" | jq -r --arg p "$1" --arg l "$2" --arg r "$3" "$JQ_FMT" 2>/dev/null
}

printf 'PROJECT\tLOCATION\tRECOMMENDER\tSUBTYPE\tPRIORITY\tMONTHLY_USD\tDESCRIPTION\n'
for p in $PROJECTS; do
  for z in $ZONES;   do for r in $ZONAL_RECS;    do fetch "$p" "$z" "$r"; done; done
  for g in $REGIONS; do for r in $REGIONAL_RECS; do fetch "$p" "$g" "$r"; done; done
  for r in $GLOBAL_RECS; do fetch "$p" global "$r"; done
done
```

**Runtime:** ~3–6 minutes for 5 projects. Each call is an independent API round trip; the matrix is
large. Run it in the background (`run_in_background: true`) and continue with the BQ steps while it
completes rather than blocking on it.

**Totals:**

```bash
/tmp/gcp-rec-sweep.sh | tee /tmp/rec-sweep.tsv
tail -n +2 /tmp/rec-sweep.tsv | awk -F'\t' '{s+=$6} END {printf "Total addressable: $%.2f/mo\n", s}'
tail -n +2 /tmp/rec-sweep.tsv | awk -F'\t' '{s[$4]+=$6; n[$4]++} END {for (k in s) printf "%-32s %3d  $%.2f/mo\n", k, n[k], s[k]}' | sort -k3 -hr
```

A project the caller lacks `recommender.viewer` on fails silently (stderr suppressed, `return 0`).
Confirm coverage with `gcloud projects list` and note any project you could not read in the report,
so a permissions gap is not mistaken for a clean bill of health.

______________________________________________________________________

## Known coverage gap: CUD recommendations

`google.cloudbilling.commitment.SpendBasedCommitmentRecommender` returns `Listed 0 items` at
billing-account/`global` scope — accessible, but empty. This is the recommender behind the Console's
**"90% CUD optimization rate"** tile, so that specific figure **cannot currently be reproduced
headlessly**.

Two plausible causes, neither confirmed:

1. The caller lacks the billing-account-level role the recommender requires
   (`roles/recommender.cloudBillingSpendBasedCommitmentViewer` or
   `roles/billing.viewer` on the billing account), and the API returns empty rather than 403.
1. There genuinely are no spend-based CUD recommendations — plausible if resource-based CUDs already
   cover the estate, which matches the ~35–40% credit rate.

**Do not resolve this by granting yourself IAM** — that is a write action and out of scope for this
skill. Report it as a known gap. If the number is needed, read it off the Console manually and cite it
as Console-sourced.

Same story for `google.cloudbilling.billingaccount.CostAnomalyInsight`, which returns
`INVALID_ARGUMENT` at every scope tried. Combined with `billingbudgets.googleapis.com` being disabled,
**Apollo has no working headless native cost-anomaly signal** — which is why Q5/Q6 in
[bq-queries.md](bq-queries.md) exist and why re-checking this each run (SKILL.md Step 9b) matters.

______________________________________________________________________

## What the Console shows that the API does not

For context when a report figure does not match a screenshot. From the FinOps Hub, 2026-09:
136 active recommendations, $46K/mo potential savings, 90% CUD optimization rate, 4.2/5.0 FinOps
maturity score.

- **Active recommendation count** — approximately reproducible by counting sweep rows, but the Console
  includes recommenders outside this sweep (BigQuery, GCS, IAM, security) and may count non-cost
  categories.
- **Potential monthly savings** — the sweep total will be **lower**, because of the CUD gap above and
  any recommender not in the matrix. Report the sweep figure as *"addressable savings from the
  recommenders swept"*, never as *"GCP's potential savings"*.
- **CUD optimization rate** — Console-only (see gap above).
- **FinOps maturity score** — Console-only, a qualitative Google assessment with no API backing. Do
  not try to reproduce or approximate it.

When quoting a Hub tile in a report, label it **(Console, read manually YYYY-MM-DD)** so it is not
mistaken for a queried figure.
