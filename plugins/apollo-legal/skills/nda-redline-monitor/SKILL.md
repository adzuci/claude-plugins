---
name: nda-redline-monitor
description: >
  Scans Ironclad for new Mutual NDA counterparty paper, applies Apollo's NDA playbook,
  generates a redlined Word document with tracked changes, and reports back in the
  conversation. Also handles direct file uploads — detects whether the file is counterparty
  paper or counterparty redlines to Apollo's template and routes accordingly.
  Triggers: "run the NDA monitor", "check Ironclad for new NDAs", "redline any new NDAs",
  "scan for counterparty paper", "process NDAs from Ironclad", "review this NDA",
  "redline this NDA", or any NDA / confidentiality agreement upload.
---

# NDA Redline Monitor

Work through every phase in order without stopping to ask for input. If a tool fails, handle
it gracefully per Error Handling below and continue.

---

## Working Paths

- **Scan log**: `~/.claude/legal-plugin/nda-scan-log.json`
  Tracks processed Ironclad records between sessions. Run `mkdir -p ~/.claude/legal-plugin/` before writing if the directory does not exist.
- **Output folder**: `~/Downloads/`
  Where completed redlined documents are saved for the reviewer to access.
- **NDA template reference**: `assets/apollo-nda-template.docx` (relative to this SKILL.md)
  Apollo's current Mutual NDA template. Used in Phase 0 to identify Apollo template structure when classification is unclear.

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

If any tool or MCP call fails:
- Log the failure clearly in the conversation
- Use the fallback described in each phase if one exists
- If no fallback is available, report the failure in the conversation describing what failed and why
- Continue with any remaining NDAs; do not abort the full run

---

## Phase 0 — Document Type Classification (direct uploads only)

**Only execute this phase when a document has been uploaded directly by the user.** If the
skill was triggered without an uploaded file (e.g., "run the NDA monitor"), skip to Phase 1.

When a document is uploaded, classify it before doing anything else:

### How to Classify

Extract the document text:

```bash
# For PDF
pdftotext "<uploaded_file_path>" - 2>/dev/null

# For DOCX
pandoc "<uploaded_file_path>" -t plain 2>/dev/null
```

> **Apollo's NDA Template Reference:** A copy of Apollo's current Mutual NDA template is
> stored at `assets/apollo-nda-template.docx` (relative to this SKILL.md). Use it as the
> ground-truth reference for identifying Apollo template structure when classification is unclear.

Then determine which type it is by looking for these signals:

**Apollo Template with Counterparty Redlines** — The document is based on Apollo's Mutual NDA
template if it contains all of the following hallmarks:
- Opening recital names "Zenleads Inc. d/b/a Apollo.io" (or a placeholder like `[•]` /
  `[Company]` in the Apollo party slot) as one of the two parties
- The defined structure matches Apollo's template: sections on Confidential Information,
  Use of Confidential Information, Ownership/No License, Disclosure of Third-Party
  Information, No Obligation, Term/Return or Destruction, Governing Law, Equitable Relief,
  Miscellaneous — in roughly that order
- Contains Ironclad merge-field placeholders (e.g., `[counterpartyName_...]`,
  `[effectiveDate_...]`, `[governingLaw_...]`) OR has those fields already filled in
- Has tracked changes (insertions/deletions) by a counterparty author, OR has clean text
  that deviates from Apollo's standard language

**Counterparty Paper** — The document is the counterparty's own template if it:
- Does not open with Apollo/ZenLeads as a named party
- Uses a structure, defined terms, or section order that does not match Apollo's template
- Bears the counterparty's company name, logo, or footer branding
- Lacks Apollo's Ironclad merge-field patterns entirely

If classification is ambiguous, default to **Counterparty Paper** and proceed as normal.

### Routing Based on Classification

**If Counterparty Paper:**
- Skip Phases 1–3 (Ironclad scan/download) and go directly to Phase 4, using the uploaded
  file as input. The existing playbook analysis and redlining logic applies without change.

**If Apollo Template with Counterparty Redlines:**
- Skip Phases 1–4 entirely and follow the sub-workflow in
  [`references/template-redlines-workflow.md`](references/template-redlines-workflow.md) —
  it covers reading the tracked changes, classifying each one (ACCEPT/REJECT/MODIFY) per the
  Apollo NDA Playbook, and generating the reviewed DOCX. Then return to Phase 6 (Save and
  Report) and Phase 7 (Update State) as normal.

---

## Phase 1 — Load State

Read the processed-record log from `~/.claude/legal-plugin/nda-scan-log.json`.

If the file does not exist, treat it as an empty log: `[]`.

Extract the list of already-processed Ironclad record IDs by reading the `id` field from
each record in the array. These must be skipped entirely.

> Note: This skill has **no time-based lookback window** — it processes all unprocessed Mutual
> NDA records at version 2 or higher, regardless of when they were last updated. This makes it
> suitable for catch-up runs after a gap in the schedule.

---

## Phase 2 — Scan Ironclad for Mutual NDAs

Call `ironclad_search_workflows` with query "Mutual NDA" and limit 100.
If `ironclad_search_workflows` returns no results or errors, retry with `ironclad_search_records`.

For every result returned, call `ironclad_get_contract` with the record ID to retrieve full
metadata including document version history and uploader information.

**Skip without processing or logging:**
- Records whose Ironclad ID is already in the processed_ids list from Phase 1
- Records at **version 1 only** (v1 = Apollo's own template; skip silently)

**Proceed with:**
- Records at **version 2 or higher** that are NOT already in the processed log

Collect for each qualifying record:
```
{ ironclad_id, contract_name, counterparty_name, document_version, document_url, uploader_name, uploader_email }
```

If zero qualifying records are found, report that there are no new NDAs to process and stop.
Do not send a Slack notification.

---

## Phase 3 — Download the NDA Document

For each qualifying record:

### Attempt 1 — web_fetch on document_url
The `ironclad_get_contract` result includes a `document_url`. Call `web_fetch` on that URL.
If it returns a PDF or DOCX file, save to `/tmp/nda-downloads/<ironclad_id>.<ext>` and
proceed. If the response is HTML or contains login/auth indicators (`<html>`, `Sign In`,
`log in`, `401`, `403`, redirect to `/login`), mark this record as `auth_required` and
move on to the next record without logging a failure yet.

### Attempt 2 — Batch Manual Handoff
After attempting all records, if any are marked `auth_required`:

1. Do NOT log them as `download_failed` — they haven't been processed yet.
2. Present the user with a single grouped message:

```
📎 Manual download needed for <n> NDA(s)

The following NDAs require an active Ironclad session to download automatically.
Please download each file from Ironclad and upload them all here — I'll review each
one as you drop it in.

<For each auth_required record:>
• <contract_name> — <counterparty_name> (v<document_version>)
  🔗 https://app.ironcladapp.com/records/<ironclad_id>
```

3. Wait for the user to upload each file. As each file arrives, run it through the full
   review pipeline (Phase 4 onward) using the uploaded file as input — exactly as the
   direct upload path works.
4. After reviewing each uploaded file, log it normally in Phase 7.

### Attempt 3 — True Failure Fallback
If web_fetch fails for a reason other than auth (network error, malformed URL, no
`document_url` in the contract metadata), log with `status: "download_failed"` and
continue to the next record.

---

## Phase 4 — Convert to Word (PDF only)

> **Path note:** For Ironclad downloads, use `<ironclad_id>` as the base filename throughout
> this phase and Phase 5. For direct uploads (no ironclad_id), use a sanitized version of
> the uploaded filename as the base name (e.g., `counterparty-nda`).

If the file is a PDF, convert to DOCX using LibreOffice:

```bash
soffice --headless --infilter="writer_pdf_import" --convert-to docx \
  --outdir /tmp/nda-working/ \
  "<source_file_path>"
```

If LibreOffice fails, extract text with pdfplumber and build the redlined DOCX from scratch
using OOXML (same approach as Phase 5e).

If the file is already a DOCX, copy it to `/tmp/nda-working/<base_name>.docx` and skip
this phase.

---

## Phase 5 — Analyze and Redline

### 5a — Read the NDA Text

```bash
pandoc --track-changes=all '/tmp/nda-working/<ironclad_id>.docx' \
  -o /tmp/nda-working/<ironclad_id>.md
```

Read the markdown output for full clause-by-clause analysis.

### 5b — Determine Document Type

Classify as:
- **Counterparty Paper** — the counterparty's own template
- **Redlines to Apollo Template** — Apollo's template with counterparty modifications

### 5c — CORE PHILOSOPHY — READ BEFORE APPLYING THE PLAYBOOK

**Apollo's goal is to sign NDAs with as few redlines as possible.** A redline creates friction
and slows deals. Only redline if a provision is genuinely harmful or a required provision is
completely missing. When in doubt, do NOT redline.

Functionally acceptable language — even if non-standard or differently worded — must be left alone.

**Do NOT add comments, annotations, or explanatory text anywhere in the Word document.**
The conversation summary is where issues are explained; the document contains only tracked changes.

**Explicit do-not-redline list (GREEN regardless of wording):**
- Standard of care that is ambiguous but not clearly below "reasonable care" (e.g., "all
  security precautions as may be necessary," "adequate security measures," "same care as
  own CI") — do not redline
- Legal compulsion carve-outs with post-disclosure notification rather than advance notice —
  the carve-out just needs to exist; do not redline
- Permitted recipient restrictions that include a signing/binding mechanism for third parties
  (e.g., "unless such party has signed on to this Agreement") — functionally equivalent; do
  not redline
- Asymmetric "Related Bodies Corporate" or affiliate sharing rights in counterparty paper —
  if the counterparty extends group-company rights only to itself but Apollo's core sharing
  categories (employees, agents, service providers, contractors) are present with a binding
  mechanism, the one-sided affiliate benefit is acceptable; do not redline for symmetry
- Mutual consequential/indirect damages exclusions where both parties are equally constrained —
  do not redline; only flag if the limitation is one-sided or includes an aggregate cap
- Return/destroy where the receiving party elects the method — acceptable; do not redline
- Return/destroy with "required by law or for archiving purposes" as the retention exception —
  adequately covers litigation holds and backup retention; do not redline
- Only flag return/destroy if the obligation is entirely absent or all retention exceptions
  are entirely absent
- Data protection clauses in Australian-law (or other non-GDPR jurisdiction) agreements that
  use processor-style obligations ("act on instructions from the Owner") — do not auto-replace
  with GDPR controller-controller language; flag YELLOW for manual review instead

### 5d — Load and Apply the Apollo NDA Playbook

Read `references/nda-mutual.md` (relative to this SKILL.md) before analyzing the contract.

Apply every criterion systematically, keeping the Core Philosophy in mind throughout.

Produce a structured issue list:
```json
[
  {
    "clause": "<clause name>",
    "classification": "RED|YELLOW|GREEN",
    "original_language": "<exact quote from NDA>",
    "issue": "<description of the problem>",
    "redline_language": "<Apollo's preferred replacement language, if applicable>"
  }
]
```

Only include items that genuinely require a redline per the playbook. Do not create YELLOW
items for provisions the playbook or do-not-redline list marks as acceptable.

**Additional scan — Privacy Law / Applicable Law definitions**: After running the full playbook
check, also scan for any defined term covering "Privacy Law," "Data Protection Law,"
"Applicable Law," or similar. If the definition is geographically restricted to a single
jurisdiction (e.g., "Australian jurisdiction," "laws of England and Wales") or covers only
"legislation" but not regulations, flag as YELLOW and redline:
- Replace geographic restriction with "any jurisdiction"
- Expand "legislation" to "legislation, regulation or other applicable law"
This applies regardless of the agreement's governing law.

### 5e — Generate the Redlined Word Document

Output: `/tmp/nda-redlines/<ironclad_id>-redlined.docx`

Unpack the DOCX (ZIP archive), edit `word/document.xml`:
- Deletions: `<w:del w:id='N' w:author='Apollo Legal' w:date='<ISO8601>'><w:r><w:delText>...</w:delText></w:r></w:del>`
- Insertions: `<w:ins w:id='N' w:author='Apollo Legal' w:date='<ISO8601>'><w:r><w:t>...</w:t></w:r></w:ins>`
- Revision IDs must be unique and incrementing
- Repack into a valid DOCX ZIP
- **Do NOT add any `<w:comment>` elements anywhere in the document**

If the NDA is entirely acceptable under the minimal-redlines philosophy, produce a clean copy
with no tracked changes.

For PDF-sourced documents where LibreOffice conversion produced poor XML, build the redlined
DOCX from scratch using Python rather than patching the converted XML. Use pdfplumber to
extract text, reproduce the agreement content faithfully, and apply the tracked changes inline.

---

### Apollo Entity Information — Fill Blank Placeholders

**Before** applying playbook redlines, scan the document for any unfilled placeholders
representing Apollo. Common patterns: `[•]`, `[__]`, `[Company]`, blank underlined fields in
the preamble, empty name/address/title fields in signature blocks, and "Contract Details" or
equivalent tables with blank Apollo party rows.

**Apollo's signing entity and address:**
- **Legal name:** ZenLeads Inc. d/b/a Apollo.io
- **Address:** 440 N Barranca Ave #4750, Covina, CA 91723-1722, United States

For each blank or placeholder found:
- Delete the placeholder text (e.g., `[•]`, `[Company]`, `[insert]`) using `<w:del>`
- Insert the correct Apollo information using `<w:ins>`
- If the placeholder is empty (blank run or underline space with no text), insert Apollo's
  information as `<w:ins>` at the correct position

Apply to **all occurrences**: preamble recitals, Contract Details tables, signature block
name/address fields, and any other location where company name or address is blank.

**Approved Purpose field**: If the document has an "Approved Purpose" definition field or
equivalent that is blank or contains only a placeholder, insert using `<w:ins>`:
> "evaluating and discussing a potential commercial relationship between the parties"
This gives the reviewer a usable starting point. The deal team may refine the scope before signing.

**Do NOT auto-fill**: Deal-specific contact details (AE name, email, phone) — these require
input from the sales rep handling the deal and must be left blank for them to complete.

---

### Defined Term Capitalization — Match the Document's Convention

Before writing any inserted clause language, scan the document to determine how "party"/
"parties" is treated:

1. Search for phrases like `each party`, `either party`, `the parties`, `each Party`,
   `the Parties` in the body paragraphs.
2. Determine the dominant capitalization:
   - Lowercase `party`/`parties` consistently → use lowercase in all inserted text
   - Capitalized `Party`/`Parties` as a defined term → use capitalized form
   - Mixed → default to lowercase

Apply the detected convention to **every occurrence** in every `<w:ins>` block. Do not copy
capitalization from the playbook template if it conflicts with the document's own convention.

---

### Section Cross-References — Update When Section Numbers Shift

When inserting a new numbered section that causes subsequent sections to renumber, scan the
full document for inline cross-references to the shifted sections and update them with tracked
changes.

**Procedure:**
1. Build a map of every numbered section in the document body before writing any XML.
2. Determine the new section number. **Preferred**: append after all numbered sections and
   before signature blocks — this avoids renumbering entirely.
3. If inserting between two existing sections: apply tracked changes to renumber the displaced
   section first, then insert the new section at the correct body index.
4. Verify before writing: the paragraph immediately before the new section must belong to a
   lower-numbered section; the paragraph immediately after must belong to a higher-numbered
   section or be a signature block. If the assertion fails, adjust before proceeding.

---

## Phase 6 — Save and Report

Copy the redlined DOCX to `~/Downloads/`.

Report back in the conversation with a summary including:
- Number of redlines made
- One sentence per redline describing what was changed and why
- Any YELLOW items flagged for awareness but not redlined
- The output file as both a clickable link and a plain path:
  `📄 **Redlined document**: [<filename>](computer://<absolute_path_to_output_file>) \`~/Downloads/<filename>\``

Always include the plain path — this ensures the reviewer can find the file even if the
clickable link does not render correctly.

---

## Phase 7 — Update State File

Append each processed record to `~/.claude/legal-plugin/nda-scan-log.json` (the file is a
JSON array of records — read it, append, and write the full array back):

```json
{
  "id": "<ironclad_id>",
  "counterparty": "<counterparty_name>",
  "processed_at": "<current ISO timestamp>",
  "status": "redlined | clean | download_failed | skipped_v1 | redlines-reviewed",
  "document_version": "<version_number>",
  "red_count": 0,
  "yellow_count": 0
}
```

---

## Cleanup

Remove temporary files from `/tmp/nda-downloads/` and `/tmp/nda-working/` after the run.
Keep files in `/tmp/nda-redlines/` only if not successfully copied to `~/Downloads/`.
