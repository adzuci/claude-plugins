# Markdown Output Format

Skeleton for the default (non-HTML) output mode. Write to `./gcp-cost-review-YYYY-MM-DD.md`.

Markdown has no native collapse, so structure carries the hierarchy: exec content first, a single
`## Technical Detail` heading, then `###` subsections per step. Anyone reading only down to the
horizontal rule should have everything they need.

Replace every `{{...}}` placeholder. **Delete sections that produced no findings** rather than
printing "N/A" — a skeleton padded with empty sections trains the reader to skim past the full ones.

______________________________________________________________________

```markdown
# GCP Cost Optimization Review — {{YYYY-MM-DD}}

**Period:** {{last complete month}} · **Prior report:** {{date or "first run"}} · **Run by:** {{user}}
**Scope:** all Apollo GCP projects, billing account `0174D0-6590F0-824CC0`
**All dollar figures are NET** (after credits) unless explicitly labelled gross.

---

## Summary

{{Two or three plain-language sentences. What the bill did, what drove it, whether anything needs
attention this week. No jargon, no SKU names, no acronyms — this paragraph is for someone who does
not work in the console.}}

| | |
| --- | --- |
| Net spend, {{month}} | **${{net}}** |
| Change vs {{prior month}} | {{+/-$X}} ({{+/-Y%}}) |
| Largest increase | {{service/project}} {{+$X}} |
| Anomalies this week | {{N above threshold, or "none"}} |
| Addressable savings identified | **${{X}}/mo** |
| Label coverage | {{X}}% ({{direction vs last month}}) |

### Since the last report

{{What moved since {{prior date}}. Status of each prior recommendation: done / open / superseded.
Omit this section entirely on a first run.}}

---

## Recommendations

Three or four, ranked by dollar impact. Each names a specific resource, project, or service and
carries an estimate derived from a query actually run this session.

### 1. {{Action}} — ~${{X}}/mo · {{S|M|L}} effort · {{low|med|high}} risk

**What:** {{specific, named resources or services}}
**Why:** {{evidence — the query or recommender output that produced this}}
**Next step:** {{the deep-dive skill, runbook, or investigation — not an action taken}}

### 2. …

### 3. …

<!-- Stop at 4. If a fifth candidate is compelling, it belongs in Technical Detail. -->

---

## Technical Detail

Raw results per check. Skip to the section you care about.

### 1. Spend Summary (Q1)

{{Q1 table: month, gross, credits, net, credit rate}}

Credit rate {{trend}}. {{Note if the rate is drifting relative to gross.}}

### 2. Month-over-Month Movers

**By service (Q2)** — {{table}}
**By project (Q3)** — {{table}}
**By SKU (Q4)** — {{table, ranked by absolute dollar delta}}

{{Which projects are increasing, and what inside them.}}

### 2b. Workload Attribution (Q12, Q13)

| infra_workload | infra_cluster | project | last_mo | prior_mo | delta |
| --- | --- | --- | --- | --- | --- |
| {{...}} | | | | | |

{{Keep the `(unlabeled)` row — a large or growing one is itself the finding, cross-referenced with
Step 9a label coverage.}}

**WoW flags (Q13):** {{rows where relative change > 20% **and** absolute delta > $2,000/wk — both,
per `scripts/workload_report.py` `flag_wow()`; or "no workload cleared both thresholds".}}

### 2c. Workload Decomposition — `workload=` runs only

{{Omit this section entirely when `workload=` was not given.}}

| Week | commitments | cores | ram | pd-ssd | pd-balanced | snapshots | nat | egress | other |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| {{...}} | | | | | | | | | |

{{Drop any column that is zero for every week and say so in one line: a zero category is a labeling
gap (disks carry no infra labels today) or a pattern miss, never a saving. Provisioned-GB cross-check
from `gcloud compute disks list --filter="name~<cluster>"`, and the Recommender sweep filtered to this
workload. A growing `other` bucket means a SKU pattern needs updating, not a vanished cost.}}

### 3. Week-over-Week Anomalies (Q5, Q6)

Threshold: absolute delta > $500/wk **and** > 15% relative change.

{{Table, or "No services or projects cleared both thresholds this week."}}

**Daily trend for top movers (Q7):** {{plateau vs spike per mover — this determines whether the
finding is structural or transient}}

### 4. GCP Recommender Findings

Swept {{N}} project × location × recommender combinations. Total addressable:
**${{X}}/mo** across {{N}} active recommendations.

| Subtype | Count | $/mo |
| --- | --- | --- |
| {{...}} | | |

Top 10 by value: {{table}}

{{Any project that could not be read, and why — a permissions gap must not read as a clean result.}}
{{CUD recommender coverage gap, if still present — see references/recommender-api.md}}

### 5. Right-Sizing

**VM (MachineTypeRecommender):** {{resize suggestions with projected savings, or "none flagged"}}

**GKE headroom:**

| Cluster | Pool | Machine type | Running | Max | Headroom |
| --- | --- | --- | --- | --- | --- |

{{A raised ceiling is latent risk, NOT current cost — phrase it that way.}}
{{Clusters lacking a backup/failover node pool.}}
{{Spot-eligible workloads not on Spot. Never suggest Spot for stateful databases.}}

→ Machine-family generation changes: run `gcp-vms-migration-advisor`.

### 6. Commitment Utilization

Commitment coverage is owned by `gcp-commitment-review`.

→ Run `gcp-commitment-review` for CUD coverage, expiries, and the full commitment-vs-usage
analysis. Do not reproduce credit-rate or expiry tables here.

### 7. Idle & Orphaned Resources

**Stopped VMs:** {{90+ days → flag for deletion; 30–90 → verify with owner; 7–30 → count only}}
**Unattached disks:** {{table: name, project, zone, size, type, age}}
**Snapshots beyond retention / orphaned:** {{table}}
**Reserved-but-unused IPs:** {{table}}

→ Full storage capacity and IOPS analysis: run `disk-inventory`.

### 8. AI / LLM Spend

| Month | AI net | % of total net | MoM |
| --- | --- | --- | --- |

**By model (Q9):** {{table}}
{{Flag any newly-appearing model — that is a migration or a new adopter.}}

**By token type (Q10):** {{input / output / cache-write / cache-read}}

{{Cache-write vs cache-read ratio. Cache-write outgrowing cache-read = paying to populate a cache
that is not being hit — an application-side fix, not a capacity problem.}}

### 9. Governance

**Label coverage (Q11):** {{X}}% of gross cost carries at least one label ({{trend}}).
{{Flag any MoM drop > 3pp. Note the propagation caveat before attributing it to a team.}}

**Native anomaly detection:** {{live check result — recommender API, billingbudgets API,
CostAnomalyInsight}}. {{If still blocked, say so plainly: without it, the Q5/Q6 WoW check is the only
anomaly signal, and it only runs when someone runs this skill.}}

**Fixed-cost levers:** support plan tier and SADA reseller terms reviewed at renewal — no change
recommended this cycle {{unless there is one}}.

---

## Methodology

- **Source:** `databricks-apolloio.billing_export.gcp_billing_export_v1_0174D0_6590F0_824CC0`, queried
  from `indigo-lotus-415`. Queries in `references/bq-queries.md`.
- **Net vs gross:** all headline figures are net of credits. Credits run ~35–40% of gross at Apollo;
  gross would overstate the bill by roughly a third and match nothing leadership has seen.
- **Finalization lag:** the most recent 2 days are excluded from all trend queries; billing data
  finalizes 24–48h after usage.
- **Billing period ≠ calendar month:** the Console reports by billing period (28–32 days observed);
  this report uses calendar months. Small gaps are expected.
- **Console reconciliation gap:** an unexplained variance beyond lag and period misalignment is known
  and uncharacterized. Spot-check against the Console before quoting externally.
- **Approximate splits:** no `sku.category` field exists; resource-type splits are pattern-matched on
  `sku.description`.
- **Label undercount:** label-propagation gaps mean label-based breakdowns undercount — see §9.
- **Read-only:** no infrastructure, ticket, or configuration was changed to produce this report.

*Generated by `.claude/skills/gcp-cost-optimization-review` on {{timestamp}}.*
```
