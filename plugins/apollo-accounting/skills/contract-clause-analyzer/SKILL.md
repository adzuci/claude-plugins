---
name: contract-clause-analyzer
description: >-
  Analyzes contracts clause-by-clause against Apollo's standard templates and flags legal,
  financial, and revenue-recognition deviations. Accepts direct file uploads or Ironclad
  scans, and produces a flagged report plus an ASC 606 assessment workbook.
disable-model-invocation: true
---

# Apollo Contract Clause Analyzer

Analyzes incoming contracts clause-by-clause against Apollo's standard templates and
flags deviations — legal, financial, or revenue recognition risk. Accepts a contract
via direct file upload or Ironclad scan.

Work through every phase in order without stopping for input. If a tool fails, handle
it gracefully and continue.

## Usage

This skill does not auto-activate — invoke it explicitly (the
`apollo-accounting:contract-clause-analyzer` skill), then either:

- **Attach a contract file** (PDF or DOCX) for direct review, or
- **Invoke with no file** to scan Ironclad for contracts pending clause review.

______________________________________________________________________

## Error Handling

If any tool fails:

- Log the failure clearly
- Use the fallback described in each phase
- Report the failure in the conversation if no fallback exists
- Continue with the review; do not abort

______________________________________________________________________

## Phase 1 — Accept the Contract

### Path A — Direct File Upload

If the user has attached a file (PDF or DOCX), use it directly. Skip to Phase 2.

### Path B — Ironclad Scan

If no file is attached, scan Ironclad for contracts pending review:

1. Call `ironclad_search_workflows` (for in-flight contracts) with:
   - `query`: search terms "MDSA", "order form", "consulting agreement", "NDA",
     "reseller", "addendum" — run each separately with `pageSize: 50`
   - `status`: "active" for pending review; omit to include all statuses
1. Call `ironclad_search_records` (for completed/imported contracts) with the
   same query terms — covers legacy contracts and PDFs imported from outside Ironclad
1. For each result, call `ironclad_get_contract` with the contract's `id` field
   to retrieve full metadata and document details
1. Skip records already in `<session_mount>/.claude/clause-scan-log.json`
1. Collect: `{ ironclad_id, contract_name, counterparty_name, document_url }`
1. If zero qualifying records found, tell the user and stop
1. **Retrieve the document content for each record** — the Ironclad metadata and
   `document_url` alone are not the contract text. If the Ironclad tools can return the
   document text directly, use that text (and skip the extraction commands in Phase 2).
   Otherwise download the document to `/tmp/contract-analysis/<ironclad_id>.<ext>` and use
   that local path as `<file>` in Phase 2.
1. **Process each qualifying record independently**, running Phases 2–8 once per contract
   and appending each to the scan log (Phase 8) as it completes.

______________________________________________________________________

## Phase 2 — Extract Contract Text

**Path A (direct upload):** extract text from the uploaded file with the commands below.
**Path B (Ironclad):** if the retrieval step already returned the document text, use it and
skip these commands; if it produced a downloaded file, run the commands on that local path.

```bash
# For PDF
pdftotext "<file>" - 2>/dev/null

# For DOCX
pandoc "<file>" -t plain 2>/dev/null
```

Fallback if under 200 characters:

```python
import pdfplumber
with pdfplumber.open("<file>") as pdf:
    text = "\n".join(page.extract_text() or "" for page in pdf.pages)
```

If still under 200 characters, tell the user the file appears to be a scanned image
and request a text-based version. Log `status: "extraction_failed"` and stop.

______________________________________________________________________

## Phase 3 — Classify the Contract Type

Identify the contract type from the extracted text. Match against these types:

| Type | Signals |
|------|---------|
| **MDSA** | "Master Data Services Agreement", Apollo as data provider, DPA attached, Contributor Database, PGI defined |
| **Order Form** | Pricing table, subscription term, payment schedule, credits, "Governing Terms" reference |
| **Mutual NDA** | "Non-Disclosure", "Confidential Information", mutual obligations, no payment terms |
| **Consulting Agreement** | "Statement of Work", independent contractor, IP assignment, services described in Exhibit A |
| **Reseller Addendum** | "End User", "PGI", reseller license, sublicense rights, Apollo branding requirement |
| **Competitor Buyout Addendum** | "Fee Waiver Period", competitor buyout, early termination penalty for waived fees |
| **Upsell Order Form** | "Upsell Order", references a parent Order Form, prorated term, adds products/credits |

If the contract type is ambiguous, note it in the output and apply the closest match.
If it appears to be a counterparty-paper version of one of the above (their template,
not Apollo's), note this prominently — counterparty paper warrants closer scrutiny.

______________________________________________________________________

## Phase 4 — Load the Playbook

Read the appropriate reference file BEFORE analyzing. Do not skip this step.

| Contract Type | Reference File |
|---------------|---------------|
| MDSA | `references/mdsa-playbook.md` |
| Order Form | `references/order-form-playbook.md` |
| Mutual NDA | `references/nda-playbook.md` |
| Consulting Agreement | `references/consulting-playbook.md` |
| Reseller Addendum | `references/reseller-playbook.md` |
| Competitor Buyout Addendum | `references/competitor-buyout-playbook.md` |
| Upsell Order Form | `references/order-form-playbook.md` (same as Order Form) |

Also read `references/revenue-recognition-flags.md` for any contract that involves
subscription fees, payment schedules, variable consideration, or multi-element arrangements.

______________________________________________________________________

## Phase 5 — Analyze Clause by Clause

### Core Philosophy

Apollo's goal is accurate flagging, not noise. Only flag a clause if it genuinely
deviates from the standard language in a way that creates legal, financial, or
revenue recognition risk. Do not flag minor wording differences that are functionally
equivalent to the standard.

> **All flags are recommendations for human review, not autonomous decisions.** RED and
> YELLOW items surface risk for the deal, legal, and finance teams to act on — the skill
> never approves, signs, rejects, or otherwise decides the fate of a contract on its own.

**Flag levels:**

| Level | Meaning |
|-------|---------|
| 🔴 RED | Hard stop — clause materially harms Apollo or is a required clause that's completely absent |
| 🟡 YELLOW | Noteworthy deviation — not fatal but worth reviewing before signing |
| 🟢 GREEN | Matches standard or functionally equivalent — no action needed |

### For each clause in the loaded playbook:

1. Search the full contract text for language addressing that topic
1. Extract the relevant 1–3 sentences
1. Compare against the standard, acceptable variants, and hard stops defined in the playbook
1. Assign a flag level

A clause is **present** when language addressing the topic exists anywhere in the
contract, even under an unexpected heading.

A clause is **absent** when a thorough search finds nothing. Whether absence is a
problem depends on the playbook for that contract type.

### Issue List (internal)

Build this list as you analyze — used to generate the output report:

```json
[
  {
    "clause": "<clause name>",
    "flag": "RED|YELLOW|GREEN",
    "found_language": "<exact quote or 'Not found'>",
    "standard_language": "<what Apollo's template says>",
    "issue": "<why this deviates and what risk it creates>",
    "recommendation": "<suggested action: accept / request change / escalate>"
  }
]
```

Only include RED and YELLOW items in the output report. GREEN items are confirmed as
standard — no need to surface them unless the user asks.

______________________________________________________________________

## Phase 6 — Generate the ASC 606 Assessment Spreadsheet

After completing the clause analysis, generate an Excel workbook that matches Apollo's
internal non-standard contract assessment format. Use openpyxl.

### Workbook Structure

**Sheet 1: "Non-standard contracts assessment"** — Master summary sheet

| Column A | Column B |
|----------|----------|
| Contract | `<counterparty_name>` |
| Ironclad Link | `<document_url if available>` |
| Contract Type | `<classified type>` |
| Overall Flag | 🔴 RED / 🟡 YELLOW / 🟢 GREEN |
| Red Issues | `<count>` |
| Yellow Issues | `<count>` |
| ASC 606 Step 1 — Identify Contract | Assessment text (see below) |
| ASC 606 Step 2 — Performance Obligations | Assessment text |
| ASC 606 Step 3 — Transaction Price | Assessment text |
| ASC 606 Step 4 — Allocate Transaction Price | Assessment text |
| ASC 606 Step 5 — Recognize Revenue | Assessment text |
| Account: Unbilled Receivable | 112000 (if applicable) |
| Account: Revenue | 400006 (if applicable) |

**Sheet 2: `<counterparty_name>`** — Contract-specific detail tab

Rows for each flagged clause:

| Clause | Flag | Found Language | Standard Language | Issue | Recommendation |
|--------|------|---------------|-------------------|-------|----------------|
| ... | 🔴/🟡 | ... | ... | ... | ... |

### ASC 606 Step Assessments to populate

Use the clause analysis findings to fill each step. Use concise, factual language.

**Step 1 — Identify Contract**: Does this contract meet all ASC 606-10-25-1 criteria?
Note: parties approved, rights identified, payment terms identified, commercial
substance, collectability. Flag any net payment terms > 30 days as a collectability
note (reference the spreadsheet's existing note about 6–9 month net terms for buyouts).

**Step 2 — Performance Obligations**: Identify which of Apollo's formally defined POs
are present using the FY24 framework:
(1) Base Platform — subscription access, recognized ratably (~93.6% of TCV norm)
(2) Email Credits — recognized as consumed (~2.7% norm)
(3) Mobile Credits — recognized as consumed (~1.7% norm)
(4) Dialer Credits — recognized as consumed (~1.2% norm)
(5) Export Credits — recognized as consumed (~0.3% norm)
(6) Unified Credits (FY25+) — recognized as consumed
State which POs are present, whether credit POs are bundled or priced separately, and
whether credit volume is disproportionately large vs. the 93.6% base platform norm.
Note any Professional Services as an additional distinct PO (recognized per SOW).
Flag if the contract structure could undermine Apollo's current bundled/ratable approach.

**Step 3 — Transaction Price**: State the total committed consideration across all
tiers and periods. Flag any variable consideration (refund rights, SLA credits, fee
waivers, contingent payments). Note significant financing component if payment terms
exceed 30 days. For tiered/buyout contracts, confirm TCV is calculable from contract terms
alone — not just from billing schedule. Reference revenue-recognition-flags.md findings.
Note: Apollo's current billing-based recognition is flagged as a material weakness by
Deloitte; any gap between billing schedule and contract terms must be surfaced here.

**Step 4 — Allocate Transaction Price**: For single-element contracts (subscription
only), allocation is straightforward. For multi-element, note SSP analysis needed
using Apollo's FY24 % split as a reference benchmark. For Competitor Buyout: total
transaction price spans the full Initial Term including the Fee Waiver Period —
revenue recognized ratably over full term, not just paid periods. Flag if any add-on
is priced at a material discount vs. SSP benchmark (triggers discount allocation rules).

**Step 5 — Recognize Revenue**: State recognition pattern per PO:

- Base Platform: ratably over subscription term (straight-line, not per invoice)
- Credits (POs 2–6): as consumed
- PGI perpetual license: at point in time when delivered
- Professional Services: over time or at completion per SOW
  For fee waiver contracts: revenue starts at contract inception, not when fees begin.
  Record unbilled receivable (112000) during waiver period; revenue to 400006.
  Flag any clause that could accelerate or defer recognition vs. these patterns.
  Flag if billing schedule ≠ contract terms (triggers manual accounting intervention
  given Deloitte's active material weakness on this exact issue).

### Formatting

- Header row: bold, light blue fill (`BDD7EE`)
- RED flag rows: light red fill (`FFD7D7`)
- YELLOW flag rows: light yellow fill (`FFFFD7`)
- GREEN / clean rows: no fill
- Column widths: A=30, B=15, C=50, D=50, E=60, F=40
- Font: Arial 10pt throughout
- Wrap text on all cells with long content

Save to: `/tmp/contract-analysis/<counterparty_name>-asc606-assessment.xlsx`
Copy to outputs folder so the user can download it.

______________________________________________________________________

## Phase 7 — Output the Flagged Report

Output the report directly in the conversation.

```
## 📋 Contract Clause Analysis — <counterparty_name>

**Contract**: <contract_name>
**Type**: <contract type>
**Counterparty Paper**: Yes / No
**Overall**: 🔴 RED — Do Not Sign / 🟡 YELLOW — Review Before Signing / 🟢 GREEN — Standard

---

### 🔴 Hard Stops (<n> issues)
<For each RED item>
**[Clause Name]**
Found: "<exact language or 'Missing'>"
Standard: "<Apollo's standard>"
Issue: <one sentence — what's wrong and the risk>
Action: <escalate to legal / request specific change>

---

### 🟡 Items to Review (<n> items)
<For each YELLOW item>
**[Clause Name]**
Found: "<exact language>"
Standard: "<Apollo's standard>"
Issue: <one sentence — the deviation and why it matters>
Action: <suggested response>

---

### Revenue Recognition Notes
<Only if revenue-recognition-flags.md was consulted — one paragraph summarizing
any financial/accounting flags: variable consideration, non-standard payment terms,
bundled obligations, or revenue timing concerns per ASC 606. Always note if billing
schedule ≠ contract terms, as this is directly relevant to Deloitte's active material
weakness on Apollo's revenue recognition control environment. Include unbilled receivable
and revenue account codes (112000 / 400006) where applicable.>

---

*Analysis based on Apollo's standard templates. RED items require legal review before
execution. YELLOW items require deal team awareness.*
```

**If everything is standard:**

```
## ✅ Contract Looks Standard — <counterparty_name>

**Contract**: <contract_name>
**Type**: <contract type>
**Overall**: 🟢 GREEN

No material deviations from Apollo's standard language were found.
This contract appears ready for execution, subject to standard approvals.
```

Always end the report with:

> 📊 **ASC 606 Assessment Workbook**: [Download](path%20to%20output%20xlsx)

______________________________________________________________________

## Phase 8 — Update State Log (Ironclad Scan Only)

Append to `<session_mount>/.claude/clause-scan-log.json`:

```json
{
  "id": "<ironclad_id>",
  "counterparty": "<counterparty_name>",
  "contract_type": "<type>",
  "processed_at": "<ISO timestamp>",
  "status": "flagged | standard | extraction_failed",
  "red_count": 0,
  "yellow_count": 0
}
```
