# Data Duel Phases — Full Playbook

---

## Phase 0: Qualify — Is This Duel Worth Running?

Before investing any effort, run this checklist with the rep.

**Proceed if most of these are true:**
- Deal ARR is **≥ $15K** (SMB threshold) or is a strategic logo regardless of ARR
- Customer's decision **will hinge** on data quality or coverage
- There is a willing champion who will **co-design** the test
- Customer will accept guardrails (sample size, identifier requirements, time)
- Customer can articulate the decision this test will unlock (e.g., "We'll switch from ZoomInfo"
  or "We'll approve a 30-seat contract")
- Deal is in **Stage 3 or later** in SFDC (active evaluation, not just discovery)

**Redirect or delay if:**
- Customer insists on name-only lists with no identifiers AND won't accept caveats
- They want 5,000+ records with no clear buying intent (fishing for free enrichment)
- There is no champion willing to help co-design the test
- They cannot state what decision the test will inform
- Deal is Stage 1–2 (too early — a data duel at this stage rarely closes)

**If redirecting:** Offer a lighter alternative — a live Apollo demo on their ICP segment, a
sample export, or a free enrichment of 50–100 rows to establish credibility. Push the formal
duel to when buying intent is confirmed.

---

## Phase 1: Scope — Lock Down the Test Design

### 1A. Confirm the decision question
Ask the rep (or customer via the rep):
- "What decision will this test help you make?"
- "If Apollo wins on this sample, what happens next in the process?"

Do not proceed to Phase 2 until there is a clear answer.

### 1B. Choose the duel type

| Type | Goal | Primary Input | Jump to |
|------|------|---------------|---------|
| **Contact Enrichment** | Enrich missing person-level data | CSV with names + company info | Phase 2 |
| **Account Enrichment** | Enrich missing firmographic data | CSV of company records | Phase 2 |
| **TAM + Contact Discovery** | Find new contacts in a target market | ICP criteria (filters) | TAM Workflow below |
| **TAM + Account Discovery** | Find new accounts in a target market | ICP criteria (filters) | TAM Workflow below |
| **Data Accuracy Check** | Verify existing records against Apollo | CSV with existing email/phone | Phase 2 |

### 1C. Agree on sample size and ICP
- Target: **500–1,000 rows**. Acceptable up to 1,500 for large deals.
- Anything larger: push to a representative sample.
- Confirm the sample reflects **real ICP** — not random noise, not cherry-picked easy records.
- If the customer can't produce a representative file: offer to build a sample via Apollo's TAM
  filters and run a coverage comparison (treat as TAM duel instead).

### 1D. Align on success criteria
Define upfront what "winning" looks like:
- X% more verified emails than incumbent?
- Y% more direct dials?
- Z total contacts in their TAM?

Write this down. Misaligned criteria after the fact is how deals are lost even when Apollo
performs well.

### 1E. Confirm identifiers
For enrichment tests:
- **Must-have**: Company domain OR LinkedIn URL (person or company)
- **Strongly recommended**: Existing emails, LinkedIn profile URLs, clean titles

If they have only names: flag this before proceeding. Use the scripted response in
`references/objections.md` ("We only have name + company").

### 1F. Set timing expectations
Share these timelines with the rep at the end of Phase 1:

| Phase | Target Duration |
|-------|----------------|
| File intake + ID health | Same day (15–30 min) |
| Domain resolution | 30 min – 2 hrs |
| Enrichment | 1–4 hrs (queue-dependent) |
| Analysis + scorecard | 30–60 min |
| **Total** | **1–2 business days** (standard); up to 5 for complex |

---

## TAM DUEL WORKFLOW (Contact Discovery / Account Discovery)

> Use this workflow instead of Phases 2–6 for TAM duel types. Rejoin at Phase 7 for the scorecard.

TAM duels are fundamentally different: there is no customer CSV to enrich. Instead, you are
building a target market from scratch inside Apollo and comparing the result to the customer's
incumbent.

### TAM-1: Define the ICP Filters

Work with the rep to translate the customer's ICP into Apollo filter criteria:

| ICP Dimension | Apollo Filter | Notes |
|---------------|--------------|-------|
| Industry | Industry → select from list | Match customer's exact terminology where possible |
| Company size | Employee count range | Clarify: total employees or revenue-based? |
| Geography | Country / State / Region | Be precise — "US enterprise" ≠ "North America" |
| Seniority | Seniority level | Director+, VP+, C-Suite — confirm exact scope |
| Department/Function | Department | Engineering, Sales, Finance — confirm |
| Technology stack | Technology used | If relevant; note Apollo vs. ZoomInfo tech data freshness |
| Company type | Public/Private | If relevant to the deal |

Document the exact filter set. Share it with the rep before running — this is the test design
and both sides need to agree on it.

### TAM-2: Get the Incumbent's Baseline Count

Before running Apollo, establish the comparison number:

1. Ask the rep: "Can the customer share their current ZoomInfo/Lusha TAM count for this filter
   set? We want to compare apples to apples."
2. If the customer can share: get the exact count and, if possible, the filter criteria they used
   (so you can match them in Apollo).
3. If the customer cannot or won't share: run Apollo first, then frame the scorecard around
   Apollo's absolute coverage rather than a comparative metric.

**Never invent or estimate the competitor's number.** If you can't get it, say so in the scorecard.

### TAM-3: Run Apollo TAM Pull

1. Navigate to Apollo's People or Companies filter view.
2. Apply all ICP filters from TAM-1 exactly.
3. Note the total count before selecting/exporting.
4. Take a screenshot of the filter set and the result count — this is your audit trail.
5. If exporting for deeper analysis: export a representative sample (up to 1,500 contacts) for
   data quality spot-checks.

### TAM-4: Spot-Check Data Quality (if sample exported)

Run `scripts/id_health.py` on the exported sample to assess the quality of Apollo's results:
- What % have verified emails?
- What % have direct dials?
- Any obvious data quality issues in titles or organization names?

Surface these findings in the scorecard — they demonstrate Apollo's data depth, not just breadth.

### TAM-5: Analyze and Frame Results

| Scenario | Framing |
|----------|---------|
| Apollo TAM > Incumbent | "Apollo found [X] contacts vs. your current [Y] — [Z]% more coverage in your target market." |
| Apollo TAM ≈ Incumbent | "Coverage is comparable. Apollo's advantage is data freshness and the unified workflow — same TAM, more actionable data." |
| Apollo TAM < Incumbent | Be honest about where the gap is. Isolate the segment/region driving the shortfall. Offer to run a quality check: are the competitor's extra records actually reachable? |

**Data quality angle:** If you have the sample, show email verification rates. A competitor
claiming 50K contacts is less impressive if 40% are unverifiable emails. Frame it as:
"Coverage without quality is noise."

Rejoin the main workflow at **Phase 7** to package the scorecard.

---

## Phase 2: File Intake

### 2A. Rename the file
```
{duel_type}_{YYYY-MM-DD}_{company_name}.csv
```

### 2B. Record count validation
Run `scripts/validate_csv.py` to count data rows (excluding header). The script will:
- Hard-stop at 1,500 rows and tell you exactly what to say to the rep
- Flag large files (>1,000) for credit review
- Confirm counts for normal-sized files

> **Do not manually count rows** — use the script. It also does the column audit (step 2C).

### 2C. Column normalization
`scripts/validate_csv.py` produces a full column audit. Based on its output:

1. Apply auto-mappings from `references/column_mappings.json` for known non-standard headers.
2. For unknown columns: the script shows sample values — ask the rep what they represent.
3. Add missing model columns as empty columns in correct position.
4. Keep non-model columns at the end as `_raw_` prefixed columns.

Load `references/model_columns.md` if you need to understand any column's purpose or position.

**Spot check before moving on:** Scan 5–10 rows manually:
- Are company names real and plausible?
- Are domain fields actually domains (not email addresses, not LinkedIn URLs)?
- Are LinkedIn URLs actually LinkedIn profile URLs?

Flag anything suspicious to the rep before proceeding.

**Save the normalized file as:** `{base_name}_normalized.csv`

---

## Phase 3: Identifier Health Assessment — THE Critical Step

This is the most important phase. Never skip it.

Run `scripts/id_health.py` on the normalized file. It produces an **Identifier Health Report**
with percentage breakdowns for domain, LinkedIn URL, and work email coverage.

### What to assess

| Identifier | Weight | Notes |
|------------|--------|-------|
| `organization_website` (domain) | **Primary** | Strongest account matching signal |
| `person_linkedin_url` | **Primary** | Strongest contact secondary identifier |
| `email` | **Primary** | Strongest contact identifier; flag generic domains |
| `organization_linkedin_url` | Secondary | Good account fallback |
| `first_name` + `last_name` | Tertiary | Alone insufficient; needs a primary signal |
| `organization_name` | Tertiary | Alone ambiguous; needs domain or LinkedIn |

### Gate: Set expectations before proceeding

Four-band decision framework — take the action listed, do not skip ahead.

| % rows with ≥1 strong ID | Band | Action |
|--------------------------|------|--------|
| ≥ 70% | **Green** | Proceed normally. No caveat needed. |
| 40–69% | **Yellow** | Proceed with explicit caveat to rep and customer. State upfront: "Match rate will be moderate due to identifier gaps — this is not a coverage gap." Document the caveat in your Phase 8 SFDC notes. |
| 20–39% | **Amber** | Stop before enrichment. Present the rep with two options: (A) augment the file with domains/LinkedIn before running — preferred, or (B) run with explicit "best effort on sparse identifiers" framing AND get written rep sign-off in Slack first. Do not proceed silently. |
| < 20% | **Red** | Do not run enrichment. The test will produce misleading numbers that will hurt Apollo more than help. Escalate to SC lead. Propose re-scoping to a TAM duel (Apollo builds the list from ICP filters) instead of an enrichment duel on their file. |

Each band requires a different conversation — 38% and 25% both fall below 40% but have materially different implications. Use the exact band, not just the threshold.

**Never show the customer raw match rate numbers without first establishing identifier health
context.** If 60% of rows have no domain and no LinkedIn, a 30% match rate is expected — it is
not Apollo failing.

---

## Phase 4: Domain Discovery & LLM-Assisted Identifier Enhancement

This phase is the highest-leverage step for improving match rate before enrichment runs. In
documented duel cases (FIS Global EMEA: 591/622 records with #N/A domains), LLM-based domain
resolution has moved match rate from near-zero to 87%. Treat this as an active enrichment step,
not a passive cleanup.

### Step 4A: Validate existing domains

Scan the `organization_website` column. A valid domain:
- Has a recognizable TLD (`.com`, `.io`, `.co.uk`, etc.)
- Is **not** a generic email provider (gmail, yahoo, outlook, hotmail, icloud)
- Does not contain spaces, `#N/A`, `#VALUE!`, or clearly random characters
- Is **not** `linkedin.com` or another platform URL (those go in `organization_linkedin_url`)
- Does not include protocol prefix (`http://` or `https://`) — strip these on intake

Flag all invalid values as absent before scoring identifier health.

### Step 4B: LLM batch name-to-domain lookup

When 15+ rows are missing domains and `organization_name` values look specific (not generic),
run a batch LLM lookup before falling back to row-by-row manual search.

**How to run the batch:**

1. Extract a deduplicated list of company names with missing/invalid domains.
2. For each company, use the following prompt pattern:

   > "I have a list of B2B companies from a sales CSV. For each company, find the official
   > business website domain (e.g., acme.com — no protocol, no www, just the root domain).
   > If you cannot find a confident match, return UNKNOWN. Do not guess.
   > Companies: [list]"

3. Parse the response. Accept a proposed domain only if:
   - The company name is specific and unambiguous (see rules below)
   - The proposed domain passes the validation rules in Step 4A
   - You can verify the match with a quick web search or the domain resolves to the expected company

4. Present the batch to the rep before writing: show a table of `company_name → proposed_domain`
   with a "Confirm all? Or flag specific rows?" prompt.

5. Write accepted domains to `organization_website`. Flag rejected rows as `_domain_unknown`.

**Specificity rules — only attempt LLM lookup for:**
- ✅ Named companies: "Workday", "Brex", "Genpact", "Quantcast", "South Pole Group"
- ✅ Companies with location context: "Metro Bank UK", "Softbank Japan"
- ❌ Generic names: "Apex Solutions", "Global Tech", "TechCorp", "Consulting Group"
- ❌ Roles/contacts without a company: "John Smith at a retail firm"
- ❌ Any name where two or more companies could match

When in doubt: leave it UNKNOWN. A wrong domain is actively worse than a blank.

### Step 4C: Row-by-row resolution for remaining gaps

For rows the LLM batch left as UNKNOWN or that look ambiguous:

1. Web search: `"{company_name}" official website`
2. Confirm the result matches the company in context (industry, location, size)
3. Present individually: `"Found [company_name] → [domain]. Evidence: [brief]. Confirm?"`
4. Write only after rep confirms.

### Step 4D: Subsidiary and parent domain flags

Flag any company that is a known subsidiary of a larger parent — even if a domain was found.
Note explicitly in the Phase 4 summary. These are likely to match the parent entity in Apollo
rather than the subsidiary, which can cause apparent match failures even with a valid domain.
Examples: "LinkedIn" (microsoft.com), regional offices sharing a parent domain.

### Domain resolution summary (required before Phase 5)

```
DOMAIN RESOLUTION SUMMARY
==========================
Already valid:          [X] rows
LLM batch resolved:     [X] rows (confirmed by rep)
Manual lookup resolved: [X] rows (confirmed by rep)
Remain unfilled:        [X] rows → identifier-gap rows (see Phase 3 band)
Subsidiary flags:       [X] rows → noted in scorecard
```

Re-run `scripts/id_health.py` after domain resolution to get the updated identifier health score.
This score (post-resolution) is what goes into the Phase 8 SFDC log and the Phase 7 scorecard.

**Save the domain-fixed file as:** `{base_name}_id_fixed.csv`

---

## Phase 5: Enrichment Execution

### 5A. Estimate credits before running
Use the table from SKILL.md to estimate credit consumption. Confirm with rep/SC lead if estimate
exceeds 5,000 credits. Do not start enrichment without credit approval for large files.

### 5A-PRE. Email unlock pre-flight check ⚠️

**Always confirm this before starting the AI Sheets run.** Apollo enrichment in AI Sheets can be
scoped in two modes:

| Mode | What Apollo returns | Credits |
|------|--------------------| --------|
| Identity match only | Name, title, LinkedIn, seniority, org data — **NO email** | Lower |
| Email unlock enabled | All identity fields + work email | Higher |

**If email unlock is not enabled, Apollo will return 0 emails even on fully matched rows.**
This is the single most common post-enrichment surprise in duels. It looks like a data gap but
is a run configuration issue.

Before Phase 5B, confirm with the rep:
> "For this duel, do we need Apollo to return email addresses? If yes, we need to enable email
> unlock in the AI Sheets enrichment settings before running. This will consume additional credits."

Document the answer. If email unlock was NOT enabled, flag this explicitly in the Phase 6 analysis
and the Phase 7 scorecard — never let the customer interpret 0% Apollo email fill as a coverage gap.

### 5B. Choose enrichment path
Ask the rep:
1. **AI Sheets** — `https://app.apollo.io/#/projects?status[]=active&page=1`
2. **Salesforce (SFDC)** — `https://apolloio.lightning.force.com/lightning/o/Opportunity/list`

#### Using AI Sheets (recommended for most duels)
1. Create a new project for this duel with the naming convention:
   `Data Duel — [Company] — [Date]`
2. Import the normalized/id-fixed CSV.
3. Map fields carefully — check every field before confirming:
   - First Name, Last Name → `first_name`, `last_name`
   - Organization Website → `organization_website` (most important)
   - Person LinkedIn URL → `person_linkedin_url`
   - Email → `email` (existing email, used as secondary identifier)
4. **Watch for duplicate column headers and mis-mapped fields.** These have caused match failures
   in past deals. Double-check the mapping screen before confirming import.
5. Run Apollo-only enrichment.
6. Export results when complete.
7. Note: rows processed, credits consumed (check project credit log).

#### Using SFDC path
If rep prefers SFDC-based enrichment (common for enterprise deals with existing Opportunity records):
1. Navigate to the Opportunity record.
2. Use the Data Enrichment action within the SFDC Opportunity workflow.
3. Follow the same field mapping logic as AI Sheets.
4. Export results from the SFDC Data Enrichment report.

### 5C. Save Version A
Rename the export: `{base_name}_apollo_only.csv`
Record: rows processed, match count (preliminary), credits consumed.

### 5D. Run waterfall enrichment (Version B, if in-scope)
Before running, confirm with rep:
> "Waterfall improves fill rate on matched records — it does not change which rows we can
> identify. Match rate will be identical in Version A and Version B. Waterfall will consume
> additional credits. Shall I proceed?"

If approved:
1. Trigger waterfall on the Version A results.
2. Waterfall priority: Apollo native → Apollo third-party → LeadMagic → Prospeo → Limadata.
3. Export results.
4. Rename: `{base_name}_with_waterfall.csv`
5. Record: additional credits consumed.

---

## Phase 6: Results Analysis

**Two paths depending on the enrichment export format:**

### Path A — Flat column export (standard Apollo-only)
Run `scripts/analyze_results.py` as described below. This works when the export has flat columns
like `apollo_match_status`, `apollo_email`, `waterfall_email`, etc.

### Path B — Multi-vendor JSON blob export (AI Sheets waterfall)
When the export contains raw JSON blob columns (e.g., `Apollo Enrich Person`,
`Prospeo Enrich Person`, `LimaData Enrich Person`), use `scripts/generate_output.py` instead:

```bash
python generate_output.py "Data Duel - Acme - Contacts - Enrichment - 2026-04-08_with_waterfall.csv" \
                          "Data Duel - Acme - Contacts - Enrichment - 2026-04-08_enriched_output.csv"
```

This script:
- Detects vendor columns by name substring (`Apollo`, `Prospeo`, `LimaData`, `LeadMagic`)
- Parses each vendor's JSON schema (see `references/vendor_schemas.md` for field maps)
- Produces the 5-block customer-ready CSV (input as-is → match_source → apollo_ → 3p_ → enriched_)
- Prints match rate, waterfall uplift, and enriched field fill rates to console

After running `generate_output.py`, manually extract the console metrics for the scorecard.
Do not run `analyze_results.py` on a JSON blob export — it will not find the expected columns.

**Read `references/vendor_schemas.md` before parsing any vendor JSON blob manually.**

---

**Run `scripts/analyze_results.py` first (Path A only).** The script computes all core metrics and categorizes
match failures automatically.

```bash
# Apollo-only analysis
python analyze_results.py contact_enrichment_2026-04-08_Acme_apollo_only.csv

# Apollo-only + waterfall comparison
python analyze_results.py contact_enrichment_2026-04-08_Acme_apollo_only.csv \
                          contact_enrichment_2026-04-08_Acme_with_waterfall.csv
```

The script outputs:
- Full metrics table (match rate, email fill, phone fill, waterfall uplift)
- Match failure breakdown (Identifier Gap / True Coverage Gap / Input Noise)
- Narrative framing guidance

### Review and validate script output
After running, do a manual sanity check:
- Do the percentages pass the smell test given what you saw in Phase 3?
- Are there any rows the script may have miscategorized? (e.g., rows with a domain that looked
  valid but didn't match — check a few manually)
- Is the match rate roughly consistent with the identifier health ceiling from Phase 3?

### Draft internal summary (before talking to customer)
Write 3–5 bullets:
- 1–2: Where Apollo clearly performed well
- 1–2: Where there are constraints and the honest reason why
- 1: Recommended narrative framing

Share this with the rep before the customer call. No surprises.

### Product signal capture
If analysis reveals a **true coverage gap** in the customer's core ICP, this is a product signal.
Before moving to Phase 7, capture it:

1. Note the specific segment/region/seniority where Apollo has confirmed coverage gaps.
2. Share with your SC lead or PM contact with context: deal size, ICP, gap description.
3. If this is the second time you've seen this gap in a duel, escalate to PM — recurring coverage
   gaps across accounts are prioritization signals for the data team.

> Coverage gaps captured from duels feed directly into Apollo's data roadmap. Don't let this
> signal die in the SFDC log.

---

## Phase 7: Scorecard — Package Results for the Customer

Use `references/scorecard_template.md` as the structure. Produce a clean written summary.

### Structure

**1. Objective Recap**
"You asked us to compare Apollo vs [incumbent] on coverage and enrichment for [ICP/segment]."

**2. Identifier Health Context** *(always lead with this)*
"Before showing the numbers: [X]% of your rows had strong identifiers (domain or LinkedIn URL).
[Y]% had no strong identifiers. This is important context — rows without identifiers cannot be
reliably matched by any vendor."

**3. High-Level Metrics** (use script output from Phase 6)
| Metric | Apollo Only | Apollo + Waterfall |
|--------|------------|-------------------|
| Match rate | X% | X% (same — waterfall doesn't change match) |
| Email coverage | Y% | Z% |
| Phone/mobile coverage | A% | B% |

**4. Key Insights**
- Where Apollo is stronger (be specific: "More verified direct dials in your US SaaS segment")
- Where there are honest constraints (be specific: "Lower coverage for LATAM SMBs; this is a
  known gap in our data")
- Match failure breakdown from Phase 6: identifier gaps vs. true coverage gaps

**5. What It Means for Your GTM**
Translate into business outcomes:
- "With [X]% more valid emails, your SDRs can work [Y]% more records per sequence run."
- "With [Z] more direct dials, connect rate improvement of roughly [estimate] is plausible."

**6. Next Steps**
- If results are strong: "We're ready to move to commercial discussion."
- If mixed: "We'd recommend a follow-up cut focused on [high-confidence segment] where Apollo
  performs strongest for your ICP."
- If a re-run is warranted: define exactly what changes (more domains added, different segment)
  and set a specific turnaround date. Do not leave it open-ended.

### Delivery format
Adapt to the rep's relationship with the customer:
- **Slack/email**: Use the scorecard template as written — clean, structured, no jargon.
- **Live call**: Pre-brief the rep privately; walk through the identifier health context *first*
  before showing numbers.
- **Slide**: If the customer wants a deck, use the same structure; the metrics table becomes
  a simple slide and the narrative bullets become speaker notes.

> **Rule**: Never share the raw CSV with the customer. Share only the scorecard narrative.

---

## Phase 8: SFDC Logging + Product Signal Capture

Navigate to Salesforce and log on the Opportunity record. Use `references/sfdc_fields.md` for
field names and valid values.

Required fields: Data Test Conducted, Test Type, Test Date, Sample Size, Main Competitor(s),
Match Rate Apollo, Email Fill Rate, Phone Fill Rate, Waterfall Run, Identifier Health Score,
Primary Failure Reason, Test Outcome, Notes.

Confirm to the rep that logging is complete and show them what was recorded.

### Notes field best practices
The free-text Notes field should capture what the structured fields cannot:
- ICP segment performance breakdown ("US SaaS: 84% match; LATAM: 31% match")
- Customer-specific context ("Champion is replacing a ZoomInfo contract expiring June")
- Follow-up commitments ("Rep promised to re-run with domain-enriched file by Apr 15")
- Any objections raised and how they were handled
- Whether a product signal was escalated to the PM team

### Closing the loop
After logging:
1. Confirm the outcome field is correct (Won / Lost / Ongoing / No Decision).
2. If Won: ask the rep to note what specifically convinced the customer (match rate? phone
   coverage? ease of use?). This is institutional learning.
3. If Lost: record why. Was it a genuine data gap? Pricing? Competitor relationship?
   This improves future duel strategy.
4. If coverage gaps were escalated in Phase 6: confirm the PM team received the signal.
