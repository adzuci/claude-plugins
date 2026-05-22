---
name: vendor-contract-review
description: >
  Reviews incoming vendor contracts, classifies into one of six categories, generates a
  redlined Word doc with tracked changes, and outputs a summary report. Categories: (1) SaaS
  with personal data, (2) SaaS without personal data, (3) SaaS integrating with Apollo
  product, (4) Data Providers, (5) Event Contracts, (6) Other. Accepts direct file uploads
  or Ironclad scans. Use when a vendor contract needs review or redlines before signing.
  Triggers: "review this contract", "redline this vendor contract", "new vendor contract",
  "check this before I sign", "scan Ironclad for vendor contracts", "does this need changes",
  "can you redline this", "is this okay to sign", or any vendor agreement upload.
---

# Vendor Contract Review

Work through every phase in order without stopping for input. If a tool fails, handle it
gracefully per Error Handling below and continue.

---

## Pre-flight Check

Before starting, verify required system tools are available:

```bash
which pdftotext pandoc soffice 2>/dev/null && python3 -c "import pdfplumber" 2>/dev/null
```

If any are missing, stop and tell the user exactly what is missing and how to install it:

| Tool | Install |
|------|---------|
| `pdftotext` | `brew install poppler` |
| `pandoc` | `brew install pandoc` |
| `soffice` (LibreOffice) | `brew install --cask libreoffice` |
| `pdfplumber` (Python) | `pip3 install pdfplumber` |

---

## Error Handling

If any MCP tool fails:
- Log the failure clearly
- Use the fallback described in each phase
- Report the failure in the conversation if no fallback is available
- Continue with remaining contracts; do not abort the full run

---

## Working Paths

- **Scan log**: `~/.claude/legal-plugin/vendor-scan-log.json`
  Tracks processed Ironclad records between sessions. Run `mkdir -p ~/.claude/legal-plugin/` before writing if the directory does not exist.
- **Output folder**: `~/Downloads/`
  Where completed redlined documents are saved for the reviewer to access.

---

## Phase 1 — Accept the Contract

### Path A — Direct File Upload
If the user has attached a file (PDF or DOCX), use it directly. Skip the Ironclad scan and
proceed to Phase 3.

### Path B — Ironclad Scan
If no file is attached, scan Ironclad for unprocessed vendor contracts:

1. Read the processed-record log at `~/.claude/legal-plugin/vendor-scan-log.json` (treat a
   missing file as `[]`). Extract the list of already-processed IDs from the `id` field of
   each record.

2. Call `ironclad_search_workflows` with multiple queries to catch different contract types:
   "vendor agreement", "MSA", "master services agreement", "subscription agreement",
   "order form", "data agreement", "data license". Run each with limit 50.
   If `ironclad_search_workflows` returns no results or errors, retry with `ironclad_search_records`.

3. For each result, call `ironclad_get_contract` to retrieve full metadata.

4. **Skip without logging:**
   - Records already in `processed_ids`
   - Internal Apollo documents where Apollo is the service provider, not the customer
   - NDAs (those belong to the nda-redline-monitor skill)

5. Collect for each qualifying record:
   `{ ironclad_id, contract_name, counterparty_name, document_version, document_url }`

6. If zero qualifying records found, report that no qualifying records were found and stop.

---

## Phase 2 — Download the Contract (Ironclad Path Only)

For each qualifying record:

### Attempt 1 — web_fetch on document_url
The `ironclad_get_contract` result includes a `document_url`. Call `web_fetch` on that URL.
If it returns a PDF or DOCX file, save to `/tmp/vendor-downloads/<ironclad_id>.<ext>` and
proceed. If the response is HTML or contains login/auth indicators (`<html>`, `Sign In`,
`log in`, `401`, `403`, redirect to `/login`), mark this record as `auth_required` and
move on to the next record without logging a failure yet.

### Attempt 2 — Batch Manual Handoff
After attempting all records, if any are marked `auth_required`:

1. Do NOT log them as `download_failed` — they haven't been processed yet.
2. Present the user with a single grouped message:

```
📎 Manual download needed for <n> contract(s)

The following contracts require an active Ironclad session to download automatically.
Please download each file from Ironclad and upload them all here — I'll review each
one as you drop it in.

<For each auth_required record:>
• <contract_name> — <counterparty_name>
  🔗 https://app.ironcladapp.com/records/<ironclad_id>
```

3. Wait for the user to upload each file. As each file arrives, run it through the full
   review pipeline (Phase 3 onward) using the uploaded file as input — exactly as the
   direct upload path works.
4. After reviewing each uploaded file, log it normally in Phase 9.

This ensures the Ironclad scan path degrades gracefully into the direct upload path
rather than silently skipping contracts.

---

## Phase 3 — Extract Contract Text

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

If still under 200 characters, the file is likely a scanned image. Report in the
conversation and request a text-based version. Log `status: "extraction_failed"` and move on.

---

## Phase 3b — Detect and Fetch Linked Terms

Many vendor order forms incorporate their full governing terms by reference to a URL rather
than attaching them. Without fetching those terms, the review is incomplete.

Scan the extracted text for linked-terms patterns (`available at <URL>`, `incorporated by
reference`, URLs containing `/legal`, `/msa`, `/dpa`, `/terms`). If any are found, follow the
full fetch workflow in [`references/linked-terms-fetch.md`](references/linked-terms-fetch.md)
— it covers detection of previously executed agreements, fetch attempts via `web_fetch` and
`WebSearch` fallback, DPA retrieval (always required for Cat 1 and Cat 3), and graceful
handling of fetch failures.

If no linked terms are found, skip to Phase 4.

---

## Phase 4 — Classify the Vendor Contract

Classify the contract into exactly one of six categories. Read the full text carefully —
classification signals are often in scope-of-service, data provisions, and integration
sections rather than the contract title.

---

### Category 1 — SaaS with Personal Data (Not Product-Related)
A software subscription or platform that will access, process, or store personal data (employee
PII, prospect/lead data, customer billing/support/account data) but does NOT integrate with
Apollo's customer-facing product or APIs.

**Signals (2+ = match):**
- Software subscription, SaaS, cloud-hosted service, or API access
- Vendor will access employee, HR, payroll, or benefits data
- Vendor will access marketing, prospect, or lead contact data
- Vendor handles billing, support, or account management data for Apollo customers
- DPA or data processing terms are referenced
- No language about integrating with Apollo's product, customer systems, or APIs

---

### Category 2 — SaaS without Personal Data (Not Product-Related)
A software subscription used internally at Apollo that does NOT access personal data and does
NOT integrate with Apollo's product.

**Signals (2+ = match):**
- Software subscription, SaaS, or cloud tool
- No personal data, DPA, data processing, or privacy obligations referenced
- No product integration, customer data access, or API connection
- Internal productivity, project management, design, analytics, or operational tooling

---

### Category 3 — SaaS Vendor Integrating with Apollo's Product
Software whose service integrates with Apollo's customer-facing product, APIs, or customer
data infrastructure. THIS IS THE HIGHEST-SCRUTINY CATEGORY.

**Signals (2+ = match):**
- API keys issued to vendor to access Apollo's systems
- Webhook, bi-directional data sync, or SDK embedded in Apollo's product
- Vendor will process or access Apollo's customer data (contact records, usage data, end-user
  account data originating from Apollo's platform)
- Integration, data pipeline, or platform connectivity language
- Subprocessor obligations or customer-data DPA terms

---

### Category 4 — Data Providers
A vendor whose primary service is providing data (contacts, companies, intent, enrichment, or
similar datasets) to Apollo.

**Signals (2+ = match):**
- Data license, data supply, data feed, or enrichment service
- Vendor provides records, contacts, firmographic, or intent data to Apollo
- License to use data for Apollo's business purposes
- References to data accuracy, sourcing, or data compliance obligations

---

### Category 5 — Event Contracts
Contracts for physical events: venues, hotels, catering, AV, team dinners, offsites,
conferences, or sponsorships.

**Signals (2+ = match):**
- Venue, hotel, room block, catering, AV, F&B minimum, event space
- Specific event date or period; attendee count; per-person charge
- Sponsorship, exhibit space, or conference participation
- Team outing, offsite, dinner reservation, or activity booking

---

### Category 6 — Other
Does not clearly fit any of the five categories above. Apply the closest-matching playbook and
note it is an approximate match in the output summary.

**Closest-match logic:**
- Software/platform elements → use Category 1 or 2 (Category 1 if any data handling exists)
- Data supply elements → use Category 4
- Physical space or events → use Category 5
- Co-working space, hot desk, dedicated desk, shared workspace, or facility access → use Co-working playbook (`references/coworking.md`)
- Marketing, co-marketing, case study, community partner, participant agreement, or participant release → use Marketing playbook (`references/marketing.md`)
- Pure services (consulting, staffing) → use Category 2 as a floor; flag for legal review

---

### Classification Conflicts
- Category 3 signals present → classify as Category 3 regardless (product integration governs)
- Category 4 signals alongside Category 1 or 2 → classify as Category 4
- Otherwise → use the category with more signals; note the ambiguity in your output

---

## Phase 5 — Load the Playbook

Read the appropriate reference file BEFORE analyzing the contract. Do not skip this step.

| Category | Reference File |
|----------|---------------|
| 1 — SaaS with personal data | `references/cat1-saas-personal-data.md` |
| 2 — SaaS without personal data | `references/cat2-saas-no-personal-data.md` |
| 3 — SaaS product integration | `references/cat3-saas-product-integration.md` |
| 4 — Data Providers | `references/cat4-data-providers.md` |
| 5 — Events | `references/cat5-events.md` |
| 6 — Other → Co-working | `references/coworking.md` |
| 6 — Other → Marketing | `references/marketing.md` |
| 6 — Other (general) | Closest match from above |

---

## Phase 6 — Analyze the Contract

### Core Philosophy

Apollo's goal is minimal redlines. Redlines create friction and slow procurement. Only redline
a provision if it is genuinely harmful or a required provision is completely missing. When in
doubt, do NOT redline.

Do NOT add comments, annotations, or explanatory text inside the Word document. The summary
report is where issues are explained. The document contains only tracked changes.

Functionally acceptable language — even if worded differently — must be left alone.

**Redline posture by category:**

| Category | Posture |
|----------|---------|
| 1 — SaaS with personal data | Minimal — DPA absence and data ownership are the primary concerns |
| 2 — SaaS without personal data | Near-zero — only two hard stops exist; accept almost everything else |
| 3 — SaaS product integration | Full scrutiny — actively redline missing security, compliance, and liability provisions |
| 4 — Data Providers | Targeted — redline missing warranties and indemnification; accept other terms |
| 5 — Events | Minimal — standard venue/event terms are acceptable |
| 6 — Other | Follow the closest-match category's posture |

### Clause-by-Clause Analysis

For each clause in the loaded reference file:
1. Search the full contract text for language addressing that topic
2. Extract the relevant 1–3 sentences
3. Compare against desired / fallback / won't-accept criteria

A clause is **present** when language addressing the topic exists anywhere in the contract,
even under an unexpected heading.

A clause is **absent** when a thorough search finds nothing. Whether absence matters depends
on the category's playbook — do not assume absence is always a problem.

### Issue List

```json
[
  {
    "clause": "<clause name>",
    "classification": "RED|YELLOW|GREEN",
    "original_language": "<exact quote, or 'Not found'>",
    "issue": "<why this is a problem>",
    "redline_action": "insert|delete|replace|none",
    "redline_language": "<Apollo's preferred replacement or insertion>"
  }
]
```

Only include items that genuinely require action per the playbook. Do not create YELLOW items
for provisions the playbook marks as acceptable.

---

## Phase 7 — Generate the Redlined Word Document

### 7a — Convert PDF to DOCX if needed

```bash
soffice --headless --infilter="writer_pdf_import" --convert-to docx \
  --outdir /tmp/vendor-working/ \
  /tmp/vendor-working/<filename>.pdf
```

If LibreOffice fails, extract text with pdfplumber and build the DOCX from scratch (see 7b).
If the source is already DOCX, copy to `/tmp/vendor-working/` and proceed.

### 7b — Apply Tracked Changes via OOXML

Output: `/tmp/vendor-redlines/<counterparty>-cat<N>-redlined.docx`

Unpack the DOCX (ZIP archive), edit `word/document.xml`:
- Deletions: `<w:del w:id='N' w:author='Apollo Legal' w:date='<ISO8601>'><w:r><w:delText>...</w:delText></w:r></w:del>`
- Insertions: `<w:ins w:id='N' w:author='Apollo Legal' w:date='<ISO8601>'><w:r><w:t>...</w:t></w:r></w:ins>`
- Revision IDs must be unique and incrementing
- Repack into a valid DOCX ZIP
- Do NOT add any `<w:comment>` elements

If the contract needs no redlines, produce a clean copy and note this in the summary.

For PDF-sourced documents with poor LibreOffice XML output, build the DOCX from scratch using
Python: extract text with pdfplumber, reproduce the contract content faithfully, apply tracked
changes inline.

Copy the final DOCX to `~/Downloads/`.

---

## Phase 8 — Output Summary Report

After generating the redlined document, output a summary report in the conversation.

**If redlines were made:**
```
## 📋 Vendor Contract Review — <counterparty_name>

**Contract**: <contract_name>
**Counterparty**: <counterparty_name>
**Category**: <#> — <category name>
**Overall**: 🟢 GREEN / 🟡 YELLOW / 🔴 RED

---

### Changes Made (<n> redlines)
<For each redline: one sentence — what was changed and why>

### Items to Review (no redline applied)
<For each YELLOW without a redline: one sentence — what to look at and why>

---

📄 **Redlined document**: [<filename>](computer://<absolute_path_to_output_file>) `~/Downloads/<filename>`
```

**If no redlines needed:**
```
## ✅ Vendor Contract Clear — <counterparty_name>

**Contract**: <contract_name>
**Counterparty**: <counterparty_name>
**Category**: <#> — <category name>
**Overall**: 🟢 GREEN

No redlines required. This contract is acceptable as-is under Apollo's playbook.

📄 **Clean copy**: [<filename>](computer://<absolute_path_to_output_file>) `~/Downloads/<filename>`
```

**If overall rating is RED:**
```
## 🔴 STOP — Full Review Required — <counterparty_name>

**Contract**: <contract_name>
**Counterparty**: <counterparty_name>
**Category**: <#> — <category name>

DO NOT SIGN. Full legal review required before execution.

### Hard Stops (<n> issues)
<For each RED item: one sentence — the problem and why it's a hard stop>

📄 **Redlined document**: [<filename>](computer://<absolute_path_to_output_file>) `~/Downloads/<filename>`
```

For event contracts, append the Operator Comment (if applicable) after the summary.

---

## Phase 9 — Update State Log (Ironclad Scan Only)

Append each processed record to `~/.claude/legal-plugin/vendor-scan-log.json` (the file is a
JSON array of records — read it, append, and write the full array back):

```json
{
  "id": "<ironclad_id>",
  "counterparty": "<counterparty_name>",
  "category": "<category number and name>",
  "processed_at": "<ISO timestamp>",
  "status": "redlined | clean | download_failed",
  "red_count": 0,
  "yellow_count": 0
}
```

---

## Cleanup

Remove temporary files from `/tmp/vendor-working/` and `/tmp/vendor-downloads/` after the
run. Keep files in `/tmp/vendor-redlines/` only if not successfully copied to the output
folder.
