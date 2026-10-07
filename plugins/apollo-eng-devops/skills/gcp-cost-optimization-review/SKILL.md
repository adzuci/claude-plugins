---
name: gcp-cost-optimization-review
description: Recurring, read-only GCP cost review (spend trends, anomalies, right-sizing, workload attribution) producing one combined exec + technical report.
disable-model-invocation: true
---

# GCP Cost Optimization Review

Recurring, read-only cost review for Apollo's GCP estate. Produces **one combined report**: an
exec-oriented summary at the top (plain language, key numbers, 3–4 recommendations) with full
technical detail underneath in collapsible sections.

Built on the durable billing-export reference:
[GCP Billing Export to BigQuery: Reference & Common Queries](https://app.notion.com/p/3d0ab2b3b496816b8161d2e9743d81ee).
Read that page if you need schema background this skill does not cover.

______________________________________________________________________

## ⚠️ CRITICAL: Read-Only Analysis Mode

**THIS SKILL MUST NEVER APPLY ANY CHANGE, TAKE ANY WRITE ACTION, OR ASK FOR PERMISSION TO EXECUTE ONE.**

**Allowed:**

- ✅ `bq query` (SELECT only) against the billing export
- ✅ `gcloud ... list` / `describe` (read-only)
- ✅ `gcloud recommender recommendations list` / `insights list` (read-only)
- ✅ Writing the report to a local file

**Forbidden — no exceptions, no "with approval" path:**

- ❌ Creating, editing, transitioning, or commenting on Jira tickets
- ❌ `gcloud ... create/delete/update/resize/set-*`, `terraform apply`, `kubectl apply`
- ❌ Deleting disks, snapshots, addresses, images, or VMs the report flags
- ❌ Enabling APIs, changing IAM, modifying budgets or anomaly-detection settings
- ❌ Posting to Slack, Notion, or any external system
- ❌ Committing or pushing to git

The output is **findings and recommendations only**, for the engineer to act on manually.
If a check requires a write to work (e.g. enabling an API), report the blocker — do not perform it.

This differs from `gcp-commitment-review`, which does create Jira tickets with approval.
**This skill never does.**

`scripts/bq_preflight.sh --install` is the only write this skill can perform, and only on
explicit request.

______________________________________________________________________

## Relationship to Other Skills — When to Defer

This skill is a **broad weekly pulse-check**. It deliberately runs light versions of three deeper
analyses. When a light check trips a threshold, **stop and point the user at the deep-dive skill**
rather than reimplementing it here.

| Signal in this review | Defer to | Why |
| --- | --- | --- |
| Commitment coverage looks off (< 85% or > 110% on any family), or a CUD expires within 90 days | **`gcp-commitment-review`** | That skill does the full CUD/reservation vs per-VM actual-usage cross-check, the user cross-check gate, and the three-report breakdown. Step 6 here is a one-query pulse only. |
| Material N2 (or C3) on-demand footprint still running, or a family migration is implied | **`gcp-vms-migration-advisor`** | That skill owns the N2→C3/C3D/C4/C4D decision matrix, rolling-upgrade mechanics, and migration plan template. Step 5 here only counts the footprint. |
| Disk spend is a top mover, or unattached/oversized disk detail is needed | **`disk-inventory`** | That skill owns capacity + IOPS/throughput math, boot-vs-data classification, and PD→Hyperdisk comparisons. Step 4 here only lists Recommender-flagged idle disks. |

State the deferral explicitly in the report (e.g. "C3D coverage is 78% — run
`gcp-commitment-review` for the full analysis"). Do not duplicate their output.

______________________________________________________________________

## Invocation & Arguments

| Argument | Effect |
| --- | --- |
| *(none)* | Markdown report (default). Exec summary first, `## Technical Detail` section after. |
| `html` | Self-contained HTML report rendered by `scripts/render_html.py` from a JSON bundle you write (schema: [references/report-bundle.md](references/report-bundle.md)). KPI strip, findings, ranked actions, collapsible detail, inline sparklines, accuracy disclaimer. No JavaScript. Published as an artifact when the Artifact tool is available; the `.html` and `.bundle.json` stay on disk either way. |
| `weeks=N` | Override the trend lookback (default: 8 weeks of weekly points). |
| `workload=<infra_workload>[/<infra_cluster>]` | Runs Step 2b filtered to one workload (and optionally one cluster within it) and enables Step 2c. Steps 1–7 stay account-wide by design — the workload scope is read in context alongside the account-wide numbers, not substituted for them. Valid values are the label vocabulary listed in [Step 2b](#step-2b-workload-attribution); an unknown value prints a warning and continues unscoped rather than failing. |
| `commitments` | Pointer only — prints "Commitment coverage is owned by gcp-commitment-review; run `/gcp-commitment-review` with the same project or workload scope" and stops. That skill lives in `apolloio/devops/.claude/skills/gcp-commitment-review`, is not part of this plugin, and creates Jira tickets with approval, so **this skill never invokes it**: the user runs it themselves. No SQL or `gcloud compute commitments` logic is duplicated here; Step 6 below is the same one-line pointer. |
| `install-bq` | Runs the Google Cloud SDK install path in `scripts/bq_preflight.sh --install` (interactive y/N prompt). Default behavior is check-only; only pass this when the user explicitly asks to install. |

**Manual trigger only.** Do not create cron jobs, scheduled tasks, or GitHub Actions for this.
The user runs it when they want it, typically weekly.

**Output path:** write to `./gcp-cost-review-YYYY-MM-DD.md` (or `.html` plus its
`.bundle.json`) in the current working directory. Never overwrite an existing dated report — if one
exists, append `-2`, `-3`, etc. Keeping prior dated reports on disk is what makes the week-over-week
narrative work; read the most recent prior report (or bundle) at Step 0 and carry forward "what we
said last time".

______________________________________________________________________

## Preconditions

```bash
bash scripts/bq_preflight.sh --check
```

This verifies `gcloud`, `bq`, and `jq` are installed, an `@apollo.io` account is active, and a
`SELECT 1` smoke query against the billing export succeeds. It prints remediation steps and exits
non-zero on any hard failure — do not proceed past a hard failure. Pass `--install` only on
explicit user request (see `install-bq` above); it is the only write this script can perform.

**Billing export table:** `databricks-apolloio.billing_export.gcp_billing_export_v1_0174D0_6590F0_824CC0`
**Query from:** `--project_id=indigo-lotus-415`
**Billing account:** `0174D0-6590F0-824CC0`

**Project name → ID** (BQ returns `project.name`, gcloud needs the ID):

| BQ `project.name` | gcloud project ID |
| --- | --- |
| production | `indigo-lotus-415` |
| devops | `apollo-ops` |
| staging | `stage-23704` |
| data-platform-production | `apollo-data-platform-prod` |
| data-platform-stg | `apollo-data-platform-stg` |
| apollo-cdc | `apollo-cdc` |
| apollo-backup | `apollo-backup-007` |
| apollo-ai-tooling | `apollo-ai-tooling` |

______________________________________________________________________

## 🚨 Net vs Gross Cost — Read This Before Quoting Any Number

**The single most common error in this analysis.** The `cost` column is **gross**, before credits.
Apollo's credits (mostly CUD payouts) run **~35–40% of gross**, so a naive `SUM(cost)` overstates the
bill by roughly a third and will not match the Console, the invoice, or any figure leadership has seen.

Verified example (Aug 2026): gross `$2,885,548`, credits `-$1,040,173`, **net `$1,845,374`**.
The net figure is the one that reconciles with the $1.89M cited in the INFRA-2173 investigation.

**Always compute net:**

```sql
SUM(cost) + SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)) AS net_cost
```

Use this correlated-subquery form, **not** a top-level `, UNNEST(credits) AS credit` join — the
top-level join fans out rows and double-counts `cost`. (Notion query (f) uses the join form
correctly because it selects *only* credit amounts, never `cost`, in the same query.)

**Every dollar figure in the exec summary must be net.** Show gross and credits only in the technical
detail, so the CUD payout is visible.

______________________________________________________________________

## Known Caveats — Carry These Into the Report

Restate these in the report's methodology note. They are not blockers, but an unqualified number
here will get challenged.

1. **Billing period ≠ calendar month.** The Console reports by GCP billing period (28–32 days
   observed); this skill queries calendar months. Small gaps are expected.
1. **24–48h finalization lag.** Exclude the last 2 days from any trend. Every query in this skill
   already does (`< DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)` or tighter) — do not widen it.
1. **Unexplained Console/BQ reconciliation gap** exists beyond (1) and (2) and is not fully
   characterized. Spot-check any figure against the Console before quoting it externally.
1. **No `sku.category` field.** Resource-type splits are pattern-matched on `sku.description` and are
   approximate.
1. **Label propagation gaps.** Label-based breakdowns undercount — which is exactly why Step 9a
   measures label coverage as a first-class governance check.

______________________________________________________________________

## Workflow

Run Steps 1–9, then assemble the report in Step 10. Steps 1–3 are the exec-summary backbone and are
mandatory. Steps 4–9 feed the technical detail; if one fails (permissions, API disabled), record the
failure in the report and continue — **do not abort the review, and do not try to fix it.**

Full verified SQL for every step is in **[references/bq-queries.md](references/bq-queries.md)**.
Recommender sweep mechanics are in **[references/recommender-api.md](references/recommender-api.md)**.

### Step 0: Load Prior Context

Look for the most recent `gcp-cost-review-*.md` / `.html` in the working directory. If found, read its
exec summary and recommendations so this run can say what changed and whether prior recommendations
moved. If none exists, note "first run — no prior baseline" in the report.

### Step 1: Spend Summary — Net, Gross, Credits by Month

Query **[Q1](references/bq-queries.md#q1)**. Last 6 complete months plus month-to-date.

Produce: net monthly totals, MoM % change, and the credit rate (`credits / gross`). A falling credit
rate with flat gross means commitment coverage is slipping — cross-reference Step 6.

### Step 2: What Moved — MoM by Service, Project, and SKU

Three queries, all net:

- **[Q2](references/bq-queries.md#q2)** — MoM by service (builds on Notion query (a))
- **[Q3](references/bq-queries.md#q3)** — MoM by project (builds on Notion query (e)); **this is the
  "which specific projects are increasing" answer**
- **[Q4](references/bq-queries.md#q4)** — MoM by service + SKU, ranked by absolute dollar delta; this
  is what actually names the driver

Rank by **absolute dollar delta**, not percent. A 300% jump on a $40 SKU is noise; a 7% rise on
`SSD backed PD Capacity` is real money.

### Step 2b: Workload Attribution

Runs always; filtered to one `infra_workload[/infra_cluster]` when `workload=` is given. Reuses
the net-cost expression verbatim.

- **[Q12](references/bq-queries.md#q12)** — MoM net by `infra_workload` × `infra_cluster` × project.
  Rows with no `infra_workload` label roll up into a first-class `(unlabeled)` row rather than being
  dropped — that row is itself a governance signal (see Step 9a).
- **[Q13](references/bq-queries.md#q13)** — WoW net by `infra_workload`. Flag as an anomaly when
  **both**: relative change > 20% **and** absolute delta > $2,000/week. Use `scripts/workload_report.py`
  `flag_wow()` for this threshold logic rather than eyeballing the CSV.

Valid `infra_workload` / `infra_cluster` values and the unknown-value behavior are in
**[references/workload-labels.md](references/workload-labels.md)** (canonical list, mirrored by
`VALID_CLUSTERS` in `scripts/workload_report.py`).

### Step 2c: Workload Decomposition

> **Known gap (verified 2026-09-14):** persistent disks and snapshots do not carry `infra_workload`
> or `infra_cluster` labels, so Q18's `pd-ssd`, `pd-balanced`, and `snapshots` categories read zero
> for every workload. Say so in the report rather than reporting zero disk cost. CUD charges do carry
> the labels and appear under `commitments`. Until disk labels are backfilled, get provisioned GB from
> `gcloud compute disks list` (see Step 2c; needs `/cluster`) and price it from the account-wide PD rate.

Only runs when `workload=` is given.

- **[Q18](references/bq-queries.md#q18)** — splits that workload's net cost into cores, RAM,
  `pd-ssd`, `pd-balanced`, snapshots, NAT, and egress via `sku.description LIKE` patterns, over 8
  weekly points.
- Only when `/cluster` is given: `gcloud compute disks list --filter="name~^gke-<cluster>-"` (disks carry
  no infra labels, so filter by anchored name prefix) for provisioned GB, to sanity check the
  `pd-ssd`/`pd-balanced` split. Short cluster names (`main`, `ops`, `production`) can still match
  other workloads' disks, so list the matched names first and report the GB as approximate. With no
  `/cluster`, skip this check and say provisioned GB was not cross-checked.
- Re-run the existing Recommender sweep (Step 4, [references/recommender-api.md](references/recommender-api.md))
  filtered to that workload's resources. Do not write a new sweep — reuse the same script and
  filter its output.

### Step 2d: Team Attribution (GKE workloads)

`gke/production` is one Q12 line (~$143k/mo, Aug 2026) but holds most product-team compute: 763
Sidekiq worker Deployments plus the Rails web tier in the `leadgenie` namespace on shared spot
pools. The export cannot split it by team until **GKE cost allocation** is enabled (INFRA-2186).
Background, what already exists (queue → team map, `app.kubernetes.io/area` pod label), and the
interim OpenCost method are in
**[references/team-attribution.md](references/team-attribution.md)**.

Each run, read-only:

1. `gcloud container clusters describe <CLUSTER> --region=<REGION> --project=indigo-lotus-415 --format="value(costManagementConfig.enabled)"`
   on the production cluster. Report `True` / not enabled.
1. If enabled, run **[Q14](references/bq-queries.md#q14)** and report the top 10 teams by dollar
   delta with an `(unlabeled)` row. Allocation is by resource *requests*, so over-requesting shows
   up as team cost: a right-sizing finding, not a data error.
1. If not, record a `gap` finding pointing at INFRA-2186. Do not propose per-team node pools to get
   attribution; labels plus cost allocation give the split without fragmenting the spot pools.

### Step 3: Anomaly Detection — Week-over-Week

Query **[Q5](references/bq-queries.md#q5)** (WoW by service) and **[Q6](references/bq-queries.md#q6)**
(WoW by project). Compares the last complete 7 days against the 7 before, excluding the
unfinalized 2-day tail.

Flag as an anomaly when **both**: absolute delta > $500/week **and** relative change > 15%. The dollar
floor keeps small services from dominating; the percent floor keeps steady large services out.

Also run **[Q7](references/bq-queries.md#q7)** — daily net trend for the top 3 movers — to distinguish
a **new plateau** (a shipped change, matters) from a **single spike** (a backfill or batch job, usually
does not). This is the step that would have caught INFRA-2173 in week one rather than at month close.

**If a mover is unexplained**, follow the Notion doc's spike playbook: `git log` over
`terraform/gcp/**` for the ramp window, then `gcloud compute instances list` to confirm live state,
then the audit log for manual changes that bypassed Terraform. Summarize the finding; do not open a
ticket.

### Step 4: GCP's Own Recommendations (Recommender API)

**This is the programmatic equivalent of the Console FinOps Hub.** There is no single
`gcloud finops-hub` command — the Hub is a Console-only aggregation view over the Recommender API.
To pull it headlessly you must sweep `gcloud recommender recommendations list` across the
project × location × recommender matrix yourself.

Run the sweep script in **[references/recommender-api.md](references/recommender-api.md)**. It
iterates the recommenders below and aggregates monthly savings from
`primaryImpact.costProjection.cost` (which is negative for a saving; the script negates it).

| Recommender | Location scope |
| --- | --- |
| `google.compute.disk.IdleResourceRecommender` | **zonal** (`us-central1-a/b/c`, `us-east1-b/c/d`) |
| `google.compute.instance.IdleResourceRecommender` | **zonal** |
| `google.compute.instance.MachineTypeRecommender` (right-sizing) | **zonal** |
| `google.compute.address.IdleResourceRecommender` | **regional** (`us-central1`, `us-east1`) + `global` |
| `google.compute.image.IdleResourceRecommender` | `global` |
| `google.compute.commitment.UsageCommitmentRecommender` | **regional** |
| `google.cloudsql.instance.IdleRecommender` | **regional** |

**Location scope is the #1 cause of false "0 items".** Disks are zonal; addresses are regional. A
sweep that only hits `us-central1` will silently miss every idle disk. Always sweep both.

**Verified behaviour (2026-09):** the API is enabled on `indigo-lotus-415` and returns real results
(e.g. `SNAPSHOT_AND_DELETE_DISK` on `pritunl-0-disk-23-01-2026`, `DELETE_ADDRESS` on
`prod-aplolinks-lb-ip`). `google.cloudbilling.commitment.SpendBasedCommitmentRecommender` returns
`Listed 0 items` at the billing-account/global scope and `INVALID_ARGUMENT` at project scope — see
[references/recommender-api.md](references/recommender-api.md) for the coverage gap this leaves.

Report total addressable monthly savings, then the top 10 by dollar value. Group by
`recommenderSubtype`. **Never act on a recommendation** — including the ones whose recommended action
is literally "Delete".

### Step 5: Right-Sizing — Allocated vs Actual

Two halves, both read-only.

**5a. VM right-sizing** — `MachineTypeRecommender` output from Step 4 is GCP's own verdict, based on
observed utilization. Report each suggested resize with its projected saving.

**5b. GKE headroom** — for each cluster, compare the autoscaler ceiling against nodes actually
running:

```bash
gcloud container clusters list --project=<PROJECT_ID> \
  --format="table(name,location,currentNodeCount,status)"

gcloud container node-pools list --cluster=<CLUSTER> --region=<REGION> --project=<PROJECT_ID> \
  --format="table(name,config.machineType,initialNodeCount,autoscaling.minNodeCount,autoscaling.maxNodeCount)"

# Nodes actually running, by pool:
gcloud compute instances list --project=<PROJECT_ID> --filter="status=RUNNING AND name~^gke-" \
  --format="value(metadata.items.filter(\"key:kube-labels\").extract(\"value\"))" 2>/dev/null \
  || gcloud compute instances list --project=<PROJECT_ID> --filter="status=RUNNING AND name~^gke-" \
       --format="table(name,machineType.basename(),zone)"
```

**Interpret the ceiling correctly.** A raised `maxNodeCount` is **not itself a cost** — you only pay
for nodes that actually run. Report it as *latent risk* ("pool X can scale to 60, currently runs 12 —
a runaway workload has $Nk/mo of headroom"), never as current waste. Getting this wrong produces a
report that cries wolf.

Also note per cluster whether a **backup/failover node pool** exists (see the GKE runbook), and flag
spot-eligible workloads (batch, CI runners, stateless, fault-tolerant, dev/test) not yet on Spot.
Do not recommend Spot for stateful databases.

**Deep dive:** machine-family generation changes → `gcp-vms-migration-advisor`.

### Step 6: Commitment Utilization — Hand Off, Do Not Duplicate

Commitment coverage is owned by `gcp-commitment-review`, full stop. Print one line —
**"Commitment coverage is owned by gcp-commitment-review; run `/gcp-commitment-review` with the same
scope"** — and move on. Do **not** invoke that skill from here: it lives in another repo
(`apolloio/devops/.claude/skills/gcp-commitment-review`), is not installed for marketplace users,
and creates Jira tickets with approval, which would break this skill's read-only guarantee. The user
runs it when they want the deep dive. This is the same one-line pointer the `commitments` argument
prints (see Invocation & Arguments above).
Do not run `gcloud compute commitments list`, query `credit.type` totals, or reproduce any
per-family coverage table, cross-check gate, or per-VM scan here — that is entirely
`gcp-commitment-review`'s job.

### Step 7: Idle & Orphaned Resources

Recommender (Step 4) catches most of this. These fill the gaps it misses.

**Stopped VMs** (still paying for their disks):

```bash
gcloud compute instances list --project=<PROJECT_ID> \
  --filter="status:(TERMINATED OR STOPPED OR SUSPENDED)" \
  --format="table(name,zone,machineType.basename(),status,creationTimestamp,labels.infra_workload)"
```

Age thresholds, matching `gcp-commitment-review` conventions:

- **90+ days stopped** → flag for deletion unless explicitly documented
- **30–90 days** → flag for owner verification
- **7–30 days** → monitor only, do not list individually

**Unattached disks** (`users` empty — the `disk-inventory` convention):

```bash
gcloud compute disks list --project=<PROJECT_ID> --filter="-users:*" \
  --format="table(name,zone,sizeGb,type.basename(),creationTimestamp)"
```

**Snapshots without a lifecycle policy** — snapshot cost compounds silently:

```bash
gcloud compute snapshots list --project=<PROJECT_ID> \
  --format="table(name,diskSizeGb,storageBytes,creationTimestamp,sourceDisk.basename())" \
  --sort-by=creationTimestamp --limit=50
gcloud compute resource-policies list --project=<PROJECT_ID> \
  --format="table(name,region,snapshotSchedulePolicy.retentionPolicy.maxRetentionDays)"
```

Flag any snapshot older than the longest retention policy in the project, plus snapshots whose source
disk no longer exists.

**Reserved IPs** — covered by `google.compute.address.IdleResourceRecommender` in Step 4; cross-check
with `gcloud compute addresses list --filter="status=RESERVED"` since the recommender needs an
observation window a freshly-orphaned IP will not have.

### Step 8: AI / LLM Spend as a Tracked Category

**Track this separately every run.** It is a distinct, fast-growing cost vertical that behaves nothing
like compute or storage, and it caused the INFRA-2173 spike.

Query **[Q9](references/bq-queries.md#q9)**. Match on `service.description`, not project — these
services appear as first-class GCP services in the export.

**Verified service names (2026-09):** `Claude Sonnet 4.6`, `Claude Sonnet 4.5`, `Claude Haiku 4.5`,
`Claude Sonnet 5`, `Claude Sonnet 4`, `Vertex AI`, `Gemini API`. Q9 pattern-matches
`claude|vertex|gemini|anthropic` so new model SKUs are picked up automatically — **re-check the
matched service list each run** and note any newly-appearing model, since a model migration shows up
here first.

Report:

- Total AI spend, MoM change, and **AI as a % of total net spend** — the number that tells leadership
  whether the cost mix is shifting
- Per-model breakdown (a jump can be a model migration, not a volume increase)
- **Token-type split** via **[Q10](references/bq-queries.md#q10)**: input / output / cache-write /
  cache-read. This is the highest-leverage AI cost signal — cache-write growing much faster than
  cache-read means the prompt cache is being written but not hit, which is a fixable application-side
  problem, not a capacity problem. In the verified Aug data, cache-write (TTL 3600s) went
  `$1,169 → $69,217` MoM, the single largest SKU delta in the estate.

### Step 9: Governance Checks

**9a. Label coverage** — the Notion doc flags label-propagation gaps; degrading coverage blinds all
per-team cost attribution. Query **[Q11](references/bq-queries.md#q11)** for the % of gross cost
carrying at least one label, by month.

**Verified trend (2026-09):** 86.6% (May) → 85.0% → 81.8% → 76.8% → 71.2% (Sep). **This is degrading
and should be reported as a finding**, not just a metric. Re-measure each run and report the
direction. Treat any month-over-month drop > 3pp as a finding.

**9b. Native cost anomaly detection — live check, not a citation.** A past attempt to enable this was
blocked on IAM and never resolved. Verify current state each run rather than repeating the claim:

```bash
gcloud services list --enabled --project=indigo-lotus-415 | grep -iE "recommender|billingbudgets"
gcloud billing budgets list --billing-account=0174D0-6590F0-824CC0 --format="table(displayName,amount.specifiedAmount.units)"
gcloud recommender insights list --billing-account=0174D0-6590F0-824CC0 --location=global \
  --insight-type=google.cloudbilling.billingaccount.CostAnomalyInsight --limit=5
```

**Verified results (2026-09) — still blocked:**

- `recommender.googleapis.com` — **enabled** ✅
- `billingbudgets.googleapis.com` — **not enabled** on `indigo-lotus-415`; `budgets list` fails with a
  permission/API-disabled error
- `CostAnomalyInsight` — `INVALID_ARGUMENT`, not reachable at this scope

Report the current state. **Do not enable the API or change IAM** — that is a write action and out of
scope. If still blocked, the report notes it as a standing gap: with no native anomaly detection,
Step 3's WoW query is Apollo's only anomaly signal, and it only fires when someone runs this skill.
That is a legitimate recommendation candidate.

**9d. GKE cost allocation.** Report the `costManagementConfig.enabled` result from Step 2d here
too, as a governance line: until it is on, roughly $215k/mo of GKE spend (`gke/production` plus
`gke/ops`) has no team owner in the billing data. Do not enable it from this skill.

**9c. Fixed-cost levers (light touch).** These never appear in per-resource analysis. Mention once per
run, expand only if the user asks: GCP support plan tier, and SADA reseller terms (SADA is first-line
support; see the Notion contacts doc). No commands — these are contract-level, reviewed at renewal.

### Step 10: Assemble the Report

**Markdown (default):** follow
**[references/output-format-markdown.md](references/output-format-markdown.md)**.

**HTML (`html` argument):** do not hand-write HTML. Write one JSON bundle and render it:

```bash
python scripts/render_html.py --sample-bundle > gcp-cost-review-YYYY-MM-DD.bundle.json   # then edit
python scripts/render_html.py gcp-cost-review-YYYY-MM-DD.bundle.json > gcp-cost-review-YYYY-MM-DD.html
```

Schema and field rules are in **[references/report-bundle.md](references/report-bundle.md)**. The
renderer fixes the page order (summary, KPIs, findings, actions, since-last, detail, method), folds
columns that are zero in every row into a one-line note, draws sparklines for weekly series, and
appends the accuracy disclaimer. If the Artifact tool is available, publish the `.html` as an
artifact and give the user the link; keep the file and bundle on disk regardless.

**Structure — exec first, detail underneath (both formats):**

1. **Summary** (plain language, no jargon, fits on one screen)
   - Net spend last complete month + MoM %
   - One-sentence "what changed and why"
   - Anomalies found this week (or "none above threshold")
   - Total addressable savings identified
1. **Findings** — anything that needs attention *or could not be measured*. A zero that is really a
   labeling gap (disk cost per workload, team cost on GKE) is reported as a gap, never as a zero.
1. **Actions — 3 or 4, no more.** Ranked by dollar impact. Each has: what, estimated monthly $
   (or an honest "not yet priced"), effort (S/M/L), risk, owner, and the owning skill or runbook for
   the deep dive. Fewer, well-evidenced recommendations beat a long list.
1. **Since last run** — status of each prior recommendation: done / open / superseded (Step 0).
1. **Technical detail** — markdown: an `## Technical Detail` section with `###` subsections per step.
   HTML: one collapsible block per step, the scoped workload's tables open by default.
1. **Methodology note** — net-vs-gross, the caveats list, query window, run timestamp, queries run.

**Recommendation quality bar:** every recommendation must name a specific resource, project, or
service and carry a dollar estimate derived from a query you actually ran. "Consider rightsizing VMs"
is not a recommendation. "Resize the 3 `MachineTypeRecommender`-flagged VMs in `apollo-ops` — $340/mo,
S effort, low risk" is.

**Report review before you hand it over.** Read the rendered report once as the reader would and
check:

- Every dollar figure traces to a query ID or gcloud command listed in the report.
- No table has a column that is zero on every row without a note saying why.
- The largest number on the page is explained in the summary (in the 2026-09-14 mongo/main run that
  was a $30.8k/week commitment line, which is a contract, not a usage change).
- At least one action is something the reader can start this week.
- Account-wide context is present even on a scoped run, so a workload is read against the whole bill.

Print the summary + actions to the terminal, and tell the user the report path (and artifact link).

______________________________________________________________________

## Weekly Cadence Notes

Designed to be re-run manually week over week. Dated reports accumulate in the working directory —
that history is the point.

Each run should say:

- What changed since the last report (Step 0)
- Which prior recommendations are now resolved, still open, or superseded
- Whether label coverage and the credit rate moved in the right direction

Monthly (roughly every 4th run), also do the deeper passes this skill defers: `gcp-commitment-review`
for full CUD analysis and `disk-inventory` for storage. Note in the report when one is due.

______________________________________________________________________

## Related skills

Use this table to avoid rebuilding the wrong workflow inside `gcp-cost-optimization-review`.

| Skill | Location | Owns |
| --- | --- | --- |
| `gcp-commitment-review` | `devops/.claude/skills/gcp-commitment-review` | Full CUD/reservation vs actual-usage cross-check, per-family coverage table, the user cross-check gate, and Jira ticket creation with approval. This skill's `commitments` argument and Step 6 are a one-line pointer only — no SQL or `gcloud compute commitments` logic is duplicated here. |
| `disk-inventory` | `devops/.claude/skills/disk-inventory` | Capacity + IOPS/throughput math, boot-vs-data classification, PD→Hyperdisk comparisons. Step 4 and Step 2c here only list Recommender-flagged idle disks and the per-workload provisioned-GB split — the deep dive lives there. |
| `gcp-vms-migration-advisor` | `devops/.claude/skills/gcp-vms-migration-advisor` | N2→C3/C3D/C4/C4D family migration decision matrix and rolling-upgrade mechanics. Step 5 here only counts the on-demand footprint. |

All three live in the `devops` repo (`apolloio/devops/.claude/skills/`), not in this plugin. Name
them in the report and let the user run them; do not invoke them from this skill and do not port
their logic here.
