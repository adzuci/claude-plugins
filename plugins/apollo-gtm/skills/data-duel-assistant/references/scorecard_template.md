# Data Duel Scorecard Templates

Two templates in this file:

1. **Contact / Account Enrichment Scorecard** — use for enrichment duels (Phases 2–6 path)
2. **TAM Discovery Scorecard** — use for TAM Contact Discovery and TAM Account Discovery duels

---

---

# TEMPLATE 1: Contact / Account Enrichment Scorecard

Use this structure when packaging enrichment results for the customer (Phase 7). Adapt tone to the
rep's relationship — Slack message, email, or slide. Fill from `analyze_results.py` output.

---

## APOLLO DATA DUEL RESULTS
### [Customer Name] · [Date] · [Contact Enrichment | Account Enrichment]

---

### Test Overview
**What we tested:** [Brief description — e.g., "Contact enrichment on your EMEA SaaS AE list
against your current ZoomInfo subscription"]
**Sample:** [N] records · [ICP description]
**Compared against:** [Incumbent vendor(s) — or "internal CRM baseline"]

---

### Identifier Health (Pre-Test)
> This context matters for interpreting all results below. Rows without identifiers cannot be
> reliably matched by any vendor — including the incumbent.

| Identifier | Coverage in Your File |
|-----------|----------------------|
| Company domain | [X]% of rows |
| Person LinkedIn URL | [X]% of rows |
| Work email | [X]% of rows |
| **Rows with ≥1 strong identifier** | **[X]%** |
| Rows with no strong identifiers | [X]% ← these rows face match constraints for all vendors |

*Identifier health band: [Green / Yellow / Amber / Red] — see Phase 3 gate for interpretation.*

---

### Results Summary — Contact Enrichment

> Use this table for contact enrichment duels. Delete and replace with Account Enrichment table below
> if this is an account duel.

| Metric | Apollo Only | Apollo + Waterfall | [Incumbent] |
|--------|------------|-------------------|-------------|
| Match rate | [X]% | [X]% | [X]% |
| Email coverage (overall) | [X]% | [X]% | [X]% |
| Email coverage (matched rows) | [X]% | [X]% | [X]% |
| Phone / mobile coverage | [X]% | [X]% | [X]% |
| 'Verified' email status | [X]% | — | — |

**Contact depth (on matched rows):**

| Field | Apollo Fill Rate | [Incumbent] |
|-------|-----------------|-------------|
| Job title | [X]% | [X]% |
| Seniority | [X]% | [X]% |
| Department | [X]% | [X]% |

> If department or seniority fill rate is below 80%: frame proactively — "Department classification
> requires inference from job title; we're improving this continuously. For your ICP, we'd recommend
> validating department routing with a 50-row spot check against your CRM records."

*Note: Match rate is identical between Apollo-only and Apollo + waterfall — waterfall improves
fill rate on records already matched, not the number of records we can identify.*

---

### Results Summary — Account Enrichment

> Use this table instead of the Contact Enrichment table above for account enrichment duels.

| Metric | Apollo Only | [Incumbent] |
|--------|------------|-------------|
| Match rate | [X]% | [X]% |

**Firmographic fill rates (on matched rows):**

| Field | Fill Rate | vs. Target (80%) | [Incumbent] |
|-------|-----------|-----------------|-------------|
| Employee count | [X]% | [status] | [X]% |
| Industry | [X]% | [status] | [X]% |
| HQ location | [X]% | [status] | [X]% |
| Revenue | [X]% | ⚠ structurally low | [X]% |
| Funding | [X]% | ⚠ structurally low | [X]% |

> Revenue and Funding fill rates are consistently below 80% across all B2B data vendors for private
> companies. This is an industry-wide gap. If the incumbent claims >80% on these fields, ask for
> their methodology — it likely includes inferred/estimated ranges, not verified figures.

---

### Segment-Level Performance

> Complete this section from the segment breakdown in `analyze_results.py` output.
> Only include segments where you have ≥10 rows for statistical meaning.

| Segment | Apollo Match Rate | [Incumbent] |
|---------|-----------------|-------------|
| [Country/region A] | [X]% | [X]% |
| [Country/region B] | [X]% | [X]% |
| [Industry A] | [X]% | [X]% |
| [Seniority level] | [X]% | [X]% |

*Highlight your strongest segment first. If a segment is weak, name it and explain the reason
(identifier gaps, regional coverage, or true gap) — don't let the customer discover it unannounced.*

---

### What's Driving the Numbers

**Where Apollo is strong:**
- [Specific finding — e.g., "On your US enterprise SaaS segment (340 rows with domains),
  match rate was 84% and email fill rate was 71%."]
- [Second finding if applicable]

**Where there are constraints:**
- [Honest gap with reason — e.g., "For the 80 rows with only company name and no domain,
  match rate was 18%. This is an identifier limitation, not a coverage gap — adding domains
  for these accounts would significantly improve results."]
- [Second constraint if applicable — e.g., "Funding fill rate is 24%. This is consistent with
  what ZoomInfo and other vendors report for private company funding — not an Apollo-specific gap."]

**Match failure breakdown:**
- [X] rows: Identifier gap (no domain, no LinkedIn — user-fixable)
- [X] rows: True coverage gap (strong identifiers, no Apollo record)
- [X] rows: Input noise / junk data

---

### What This Means for Your Team

[Translate into business language — pick the relevant framing]

**For contact enrichment:**
- "With [X]% email coverage on your priority accounts, your SDRs have actionable data on [Y]
  more contacts per sequence run than your current setup."
- "The [Z] additional direct dials from waterfall represent approximately [estimate] more connect
  opportunities per month."

**For account enrichment:**
- "With [X]% of accounts matched and employee count at 100% fill, your RevOps team can apply
  territory rules and routing logic immediately — no manual research needed."
- "Revenue fill at [X]% means [Y] of your [N] target accounts have revenue data for scoring."

---

### Recommended Next Steps

**Option A — Results are strong:** Move to commercial discussion; propose full deployment scope.

**Option B — Mixed results:** Run a focused follow-up cut on [highest-performing segment] to
demonstrate Apollo's strength where it matters most for your ICP.

**Option C — Identifier gaps are limiting:** Share domain enrichment approach; offer to re-run
once [X]% of rows have domains added. Set a specific date — do not leave open-ended.

---
*Apollo · Data Duel · [Rep name] · [Date]*

---

---

# TEMPLATE 2: TAM Discovery Scorecard

Use this for TAM Contact Discovery and TAM Account Discovery duels (TAM Workflow path).
There is no customer CSV in TAM duels — Apollo builds the list from ICP filters.

---

## APOLLO TAM DISCOVERY RESULTS
### [Customer Name] · [Date] · [TAM Contact Discovery | TAM Account Discovery]

---

### What We Set Out to Measure

**Your ICP definition:** [Paste the filter set agreed in TAM-1]

| Filter Dimension | Apollo Filter Applied | Value |
|------------------|-----------------------|-------|
| Industry | [value] | |
| Company size (employees) | [range] | |
| Geography | [countries / regions] | |
| Seniority | [level(s)] | |
| Department / Function | [value] | |
| Technology (if applicable) | [value] | |

**Baseline from incumbent:** [X total contacts / accounts in [Incumbent]'s TAM for this filter set]
*If incumbent baseline was not available:* "We were not provided a comparable count from [Incumbent];
Apollo's absolute coverage is reported below."

---

### Coverage Results

| Metric | Apollo | [Incumbent] | Delta |
|--------|--------|-------------|-------|
| Total [contacts / accounts] in ICP | [X] | [Y] | [+/- Z] |
| % of target companies with ≥1 contact | [X]% | [Y]% | [+/- Z pp] |
| % of target companies with ≥3 contacts | [X]% | — | — |
| Avg contacts per matched account | [X] | — | — |

> The "≥3 contacts per account" metric matters because reaching one person rarely closes a deal.
> Apollo's TAM advantage is depth per account, not just breadth.

---

### Data Quality Spot-Check

> Complete from TAM-4 (id_health.py on exported sample). Only include if sample was exported.

| Quality Metric | Apollo Result |
|----------------|--------------|
| % with verified email | [X]% |
| % with direct dial / mobile | [X]% |
| % with job title populated | [X]% |
| % with seniority populated | [X]% |
| % with department populated | [X]% |

> If incumbent TAM count is higher but their data quality is weaker, frame: "Coverage without
> quality is noise — [X]% of our contacts have verified emails vs. [Y]% for [Incumbent]."

---

### Segment Breakdown

> Show TAM counts by the dimensions that matter most for this customer's GTM motion.

**By region:**

| Region | Apollo Contacts | [Incumbent] |
|--------|----------------|-------------|
| [NORAM] | [X] | [Y] |
| [EMEA] | [X] | [Y] |
| [APAC] | [X] | [Y] |

**By seniority:**

| Seniority | Apollo Contacts | % of total |
|-----------|----------------|------------|
| C-Suite | [X] | [X]% |
| VP | [X] | [X]% |
| Director | [X] | [X]% |
| Manager | [X] | [X]% |

**By department (if relevant):**

| Department | Apollo Contacts | % of total |
|------------|----------------|------------|
| [Department A] | [X] | [X]% |
| [Department B] | [X] | [X]% |

---

### What This Means for Your GTM

[Pick the framing that matches the result]

**If Apollo TAM > Incumbent:**
"Apollo surfaced [X] contacts in your ICP vs. [Y] in [Incumbent] — [Z]% more addressable market.
That's [estimate] more accounts your SDRs can work with verified contact data from day one."

**If Apollo TAM ≈ Incumbent:**
"Coverage is comparable in total size. Apollo's advantage is the unified workflow — same TAM,
but data + sequences + intent signals all in one platform, eliminating tool-switching overhead."

**If Apollo TAM < Incumbent in specific segment:**
"[Incumbent] shows more coverage in [specific region/segment]. We want to be straight about that.
Where Apollo is particularly strong is [counter-segment]. For your core motion in [primary segment],
our TAM is [X] — [describe relative to their workflow needs]."

---

### Recommended Next Steps

**Option A — Coverage is clearly better:** Move to commercial discussion.

**Option B — Coverage is comparable, quality advantage exists:** Propose a pilot sequence run
on Apollo-sourced contacts vs. their existing data — bounce rate and reply rate will validate
quality in a way counts alone can't.

**Option C — Gap in a specific region:** Narrow the evaluation to the region where Apollo is
strongest. If the customer's primary motion is in a region Apollo wins, close on that.

**Option D — Reframe to enrichment duel:** If TAM count is lower but the customer has an existing
list, pivot to "let's see how Apollo enriches your current list" — turns a coverage question into
a fill rate story where Apollo can show direct uplift on their data.

---
*Apollo · TAM Discovery · [Rep name] · [Date]*
