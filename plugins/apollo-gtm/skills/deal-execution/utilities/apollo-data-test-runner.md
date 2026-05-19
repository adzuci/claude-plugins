---
name: apollo-data-test-runner
description: >-
  Prepares and validates client-provided files for Apollo enrichment data tests.
  Separates file assessment from transformation, producing an inspectable intermediate
  state before any data is modified. Outputs a clean, standardized CSV ready for
  manual Apollo enrichment, with structured summaries before and after transformation.
  Designed for handoff to the apollo-fill-rate-report skill after the SC runs enrichment.
  Use when someone says run a data test, prep a data duel, client sent us a file to enrich,
  validate this file for Apollo, prospect wants a POC enrichment, data test file, enrichment test,
  or enrich this list.
metadata:
  version: '2.1'
  author: David Johnson Hall
  scope: org
  library: Apollo GTM Skill Library
---

# Apollo Data Test Runner v2.1

## Overview

### What This Is

A structured pipeline that takes a raw client file, assesses its contents, cleans and standardizes the data, resolves missing company domains, and produces a CSV ready for Apollo enrichment. It separates **assessment** (what the file looks like) from **transformation** (what was done to it), creating an inspectable intermediate state before any data changes occur.

### When To Use It

Any time a prospect or client provides a list of contacts or companies and wants to evaluate Apollo's enrichment capabilities. Common contexts:

- Discovery calls where the prospect challenges Apollo's data quality
- POC setup for a new opportunity
- Competitive data duels (Apollo vs. another provider)
- Onboarding tests during implementation

### What Happens After

1. This skill produces a cleaned CSV file.
2. You (the SC) download that file and run it through Apollo's enrichment flow in your Apollo account.
3. Once Apollo produces its enriched export, feed that export into the `apollo-fill-rate-report` skill to analyze field-level coverage and fill rates.

**Claude prepares the file. You execute the enrichment. `apollo-fill-rate-report` analyzes the results.**

This boundary is intentional. Apollo's live enrichment requires human authentication and account-level access that Claude cannot perform.

---

## Requirements

### Input Contract

| Format | Handling |
|---|---|
| CSV | Read directly from uploaded file |
| XLSX | Convert to CSV via code execution, then process |
| Pasted table | Parse as delimited text |

**Minimum viable input -- Contact Enrichment:** Full name (or first + last) AND company name. Title improves match quality but is not required by Apollo's API. No minimum record count.

**Minimum viable input -- Account Enrichment:** Account/company name. Minimum 4 records (see Phase 1 for rationale and override).

**Hard maximum: 500 records.** Files exceeding 500 records must be split into batches before processing. This limit protects against runaway credit consumption during domain resolution and spot-check validation.

### Output Contract

The downstream `apollo-fill-rate-report` skill expects **exactly** these column names and formats. Do not rename, reorder, or add columns beyond this schema.

**Contact Enrichment -- output schema:**

| Column | Format | Required |
|---|---|---|
| `First Name` | Trimmed, original case preserved | Yes |
| `Last Name` | Trimmed, original case preserved | Yes |
| `Title` | Trimmed, original case preserved | Yes |
| `Company Name` | Trimmed, original case preserved | Yes |
| `Company Domain` | Lowercase, no protocol, no `www.`, no trailing `/` | Yes (blank if unresolved) |
| `LinkedIn URL` | `https://www.linkedin.com/in/<handle>` | Only if present in source |

**Account Enrichment -- output schema:**

| Column | Format | Required |
|---|---|---|
| `Account Name` | Trimmed, original case preserved | Yes |
| `Domain` | Lowercase, no protocol, no `www.`, no trailing `/` | Yes (blank if unresolved) |

**Output filename:** `apollo-data-test-ready.csv`

These column names are a **hard contract**. `apollo-fill-rate-report` depends on them by exact name. Altering them will break the downstream skill.

### Apollo MCP Tool Reference

This skill uses specific Apollo MCP endpoints. The correct parameters for each are documented here to prevent misconfiguration.

| Tool | Purpose | Key Parameters |
|---|---|---|
| `apollo_organizations_enrich` | Enrich one company by domain | `domain` (required) -- accepts domain only, NOT company name |
| `apollo_organizations_bulk_enrich` | Enrich up to 10 companies by domain | `domains` (required) -- array of up to 10 domain strings |
| `apollo_mixed_companies_search` | Search for companies by name, filters | `q_organization_name` -- accepts company name as search query |
| `apollo_people_match` | Enrich one person | `first_name`, `last_name`, `organization_name`, `domain`, `linkedin_url`, `email` -- all optional, more = better match |
| `apollo_people_bulk_match` | Enrich up to 10 people | `details` -- array of person objects with same fields as `people_match` |

**Critical:** `apollo_organizations_enrich` takes `domain`, not `name`. To look up a company by name (e.g., for domain resolution), use `apollo_mixed_companies_search` with `q_organization_name`.

### Tool Dependencies

| Capability | Purpose | Dependency Type | Failure Behavior |
|---|---|---|---|
| Apollo MCP (`apollo_mixed_companies_search`) | Domain resolution for records missing domains | **Conditional** -- required only when domains need resolving | Fall back to web search only; note in summary |
| Apollo MCP (`apollo_organizations_enrich` / `apollo_people_match`) | Spot-check validation | **Soft** -- optional quality gate | Skip validation; note in summary |
| Apollo MCP (`apollo_organizations_bulk_enrich` / `apollo_people_bulk_match`) | Batch spot-check validation | **Soft** -- preferred over single calls | Fall back to single-record calls |
| Code execution | XLSX-to-CSV conversion | **Conditional** -- required only for XLSX | Ask user to re-upload as CSV |
| Web search | Domain resolution (fallback) | **Soft** | Degrade gracefully; flag unresolved domains |
| File save and delivery | Output CSV to user | **Required** | Fall back to in-chat CSV output |

**Apollo MCP dependency logic:** If the uploaded file already has domains for every record, Apollo MCP is not required for the core pipeline. It is only a hard dependency when domain resolution is needed. The spot-check validation step (Phase 2.4) uses Apollo MCP but is optional and offered to the SC rather than required.

---

## Phase 0 -- Pre-Flight Check

Run all checks before reading or processing the file. If any hard dependency fails, do not proceed.

### 0.1 -- Apollo MCP Connection

Probe the Apollo MCP connector with a lightweight call:

```
tool: apollo_organizations_enrich
parameters: { domain: "apollo.io" }
```

**If the call returns a result:** Apollo MCP is active. Log as connected.

**If the call fails or the tool is not found:** Log as disconnected. Do NOT hard stop here. Continue to Phase 1 to assess the file. The MCP connection only becomes a hard dependency if domain resolution is needed (determined in Phase 1). If all records already have domains, the pipeline can complete without MCP.

If MCP is disconnected and domain resolution is later needed, display:

> **Apollo MCP is not connected.** Domain resolution requires the Apollo MCP connector to look up company domains. Without it, only web search fallback is available, which is less reliable.
>
> To connect:
> 1. Open your Claude.works settings and find the Connectors or Integrations section
> 2. Locate Apollo.io and authenticate with your Apollo credentials
> 3. Return to this conversation and re-upload your file
>
> If Apollo MCP was previously connected and you're seeing this, the session may have expired. Try disconnecting and reconnecting.
>
> To proceed with web search only, confirm and I'll continue.

### 0.2 -- Code Execution (XLSX only)

If the uploaded file has an `.xlsx` or `.xls` extension, verify code execution is available by running a trivial operation (e.g., `print("ok")`).

**If available:** Proceed.

**If unavailable:**

> "The uploaded file is Excel format (.xlsx), and I need code execution to convert it. Code execution isn't available in this session. Please re-export the file as CSV from Excel (File > Save As > CSV UTF-8) and re-upload it."

Wait for CSV re-upload. Do not attempt to parse XLSX as raw text.

### 0.3 -- File Presence

Confirm a file has been uploaded or data has been pasted.

**If nothing is present:**

> "I don't see a file attached. Please upload the client's contact or account list -- CSV or Excel both work. You can also paste the data directly into the chat."

**If present but unreadable** (empty, corrupt, binary, wrong format):

> "I wasn't able to read the uploaded file. It may be empty or in an unsupported format. Please re-upload as CSV, or paste the data directly."

---

## Phase 1 -- File Assessment

**Phase 1 is read-only.** No data is modified. The goal is to produce a complete, inspectable picture of the file -- what it contains, what's missing, what's ambiguous -- before any transformation begins. This is the "eliminate before selecting" pass: narrow the space of what's valid, what's blocked, and what needs resolution.

### 1.1 -- XLSX Conversion

If the source file is XLSX, convert to CSV using code execution.

**Multi-sheet handling:** Before reading data, check how many sheets exist:

```python
import pandas as pd

xls = pd.ExcelFile("<uploaded_file_path>")
print(f"Sheets: {xls.sheet_names}")
print(f"Sheet count: {len(xls.sheet_names)}")
```

- If one sheet: read it.
- If multiple sheets: list the sheet names and ask the SC which one contains the data. Do not default to the first sheet without confirmation.

Then read the selected sheet:

```python
df = pd.read_excel("<uploaded_file_path>", sheet_name="<selected_sheet>")
# Strip Excel's leading-apostrophe artifact on text fields
for col in df.columns:
    df[col] = df[col].apply(lambda x: str(x).lstrip("'").strip() if isinstance(x, str) else x)
print(df.columns.tolist())
print(f"Rows: {len(df)}")
```

Use whatever file path the environment provides for the uploaded file. Do not hardcode a filesystem path -- reference the file by its uploaded name and let the runtime resolve the location.

**If conversion fails:** Report the error. Ask the user to re-upload as CSV. Do not continue with the XLSX file.

After conversion, all subsequent steps operate on the resulting data.

### 1.2 -- Record Count Check

**Hard stop at 500 records:**

If the file exceeds 500 rows of data:

> "This file has [N] rows. The maximum for a single data test run is 500 records to control credit consumption during domain resolution and validation. Please split the file into batches of 500 or fewer and run each batch separately."

Do not proceed. Do not silently truncate.

### 1.3 -- Determine Test Type

Inspect column headers to classify the file.

**Contact signals:**
- Columns for first name, last name, full name, title, job function
- LinkedIn URLs present
- Person-level data alongside company identifiers

**Account signals:**
- Company/organization/account name columns only
- No person-name columns
- Website or domain columns without person names

**If clear:** Classify and proceed. If the user already stated the type ("they sent us a contact list"), use their declaration.

**If ambiguous** (both person and company columns present at similar weight, or only company names with no clear person data):

> "This file could be either a contact list or an account list -- I see columns for [list relevant columns]. Which type of enrichment test are you running?"

Wait for user response before proceeding.

### 1.4 -- Column Mapping

Map source column headers to the output schema. Apply flexible matching:

**Contact mapping:**

| Source Variants | Maps To |
|---|---|
| `Name`, `Full Name`, `Contact Name`, `Contact` | Split > `First Name` + `Last Name` |
| `First Name`, `First`, `Given Name`, `FName` | `First Name` |
| `Last Name`, `Last`, `Surname`, `Family Name`, `LName` | `Last Name` |
| `Title`, `Job Title`, `Role`, `Position`, `Function`, `Designation` | `Title` |
| `Company`, `Company Name`, `Employer`, `Organization`, `Account`, `Client`, `Org` | `Company Name` |
| `Domain`, `Website`, `URL`, `Web`, `Homepage`, `Company Domain`, `Company Website`, `Company URL` | `Company Domain` |
| `LinkedIn`, `LI`, `LinkedIn URL`, `Profile URL`, `Profile`, `LinkedIn Profile`, `LI URL` | `LinkedIn URL` |

**Account mapping:**

| Source Variants | Maps To |
|---|---|
| `Company`, `Company Name`, `Organization`, `Client Name`, `Account`, `Account Name`, `Name`, `Org` | `Account Name` |
| `Domain`, `Website`, `URL`, `Web`, `Homepage`, `Company Website` | `Domain` |

**Flag unmapped columns.** Do not silently drop them -- note them in the assessment. They will not appear in the output, but the user should know what was excluded.

**Flag missing expected columns.** If a target column has no source match, note it.

### 1.5 -- Gap and Quality Detection

Scan every record for data issues. Categorize findings:

**Hard gaps -- blocking for that record:**
- Contact: missing Company Name entirely (cannot disambiguate without it)
- Contact: missing both name and title (insufficient signal to match)
- Account: missing Account Name (no enrichment possible)

**Soft gaps -- degraded enrichment quality:**
- Missing Company Domain / Domain (domain resolution will attempt to fill these in Phase 2)
- Contact: missing Title (enrichment still possible but lower match quality)
- Contact: missing LinkedIn URL (enrichment still possible)

**Quality issues -- detect and count:**
- Placeholder values in domain fields: `N/A`, `TBD`, `unknown`, `none`, `-`, `#N/A`, `null`, empty string > treat as missing
- Leading apostrophes on any field (Excel artifact): count affected fields
- Exact duplicate rows: count
- Same-domain duplicates (different name, same normalized domain): count and list pairs
- Fully blank rows: count
- Mixed test-type signals (person + company columns at similar density): flag

**Domain validation:** For records that have a domain value, check for obviously invalid formats:
- No dot in the string (not a valid domain)
- No TLD (e.g., just "acme" with no extension)
- Contains spaces
- Flag these as "invalid domain format" -- they will be routed to domain resolution as if blank

**Name structure assessment (Contact only):**
- Count rows with a combined Full Name field requiring splitting
- Flag names with prefixes (Dr., Mr., Ms., Prof.), suffixes (Jr., Sr., III, Esq.), or hyphenated structures
- Flag single-word names (mononyms)
- Flag names with particles (van, de, von, del, di, la, el, al-)

### 1.6 -- Hard Stops

If any of these conditions are true, stop and do not proceed to Phase 2.

**Contact -- No Company Name column exists:**

> "This file is missing Company Name for all records. Without a company, there's no way to match contacts -- two people can share the same name and title at different companies. Please ask the client to include at least a Company Name column."

**Contact -- Only one column (names only):**

> "This file only contains [column name]. Contact enrichment requires at minimum: name and company. Please ask the client for a more complete file."

**Account -- Fewer than 4 records:**

> "This file has [X] account(s). A data test needs at least 4 accounts to produce an interpretable enrichment sample. With fewer records, the fill-rate results from `apollo-fill-rate-report` won't have enough data points to draw meaningful conclusions about Apollo's coverage for this prospect's segment.
>
> If you have a specific reason to run a smaller test, tell me to proceed and I'll continue."

The 4-account minimum is a practical threshold for downstream fill-rate analysis, not a system-enforced Apollo limit. It exists because fill-rate percentages on 1-3 records are statistically meaningless -- a single miss on 2 records shows 50% coverage, which misrepresents Apollo's actual match rate for that segment. The SC can override this by explicitly requesting to proceed.

**Account -- No identifiable Account Name column:**

> "I can't identify a column that contains company or account names. Account enrichment requires at least one column with company names. The columns I see are: [list]. Which column contains the account names?"

Wait for the user to clarify. If they identify a column, remap and continue.

**Mixed file:**

> "This file has both person-level and company-level columns. Is this meant to be a contact enrichment test, an account enrichment test, or did the client accidentally merge two files?"

Wait for user response.

### 1.7 -- File Assessment Summary

Present this structured summary to the user before proceeding to Phase 2. This is the inspectable intermediate state -- it shows exactly what the file looks like raw, before any cleaning or transformation.

```
----------------------------------------------
FILE ASSESSMENT SUMMARY
----------------------------------------------
Test type:           [Contact Enrichment / Account Enrichment]
Total rows:          [N]
Usable records:      [N]  (excluding blank rows)
Records with hard gaps: [N]  (will be excluded or flagged)

COLUMN MAPPING
  [source column] > [target column]
  [source column] > [target column]
  ...
  Unmapped (will be dropped): [list or "none"]
  Missing expected:           [list or "none"]

DATA GAPS
  Records missing domain:     [N] of [N]  < will attempt resolution in Phase 2
  Records missing title:      [N] of [N]  (contacts only)
  Records missing LinkedIn:   [N] of [N]  (contacts only, not blocking)

QUALITY FLAGS
  Duplicate rows (exact):             [N]
  Duplicate rows (same domain):       [N]  [list pairs]
  Blank rows:                         [N]
  Placeholder domain values:          [N]  (will be treated as missing)
  Invalid domain formats:             [N]  (will be treated as missing)
  Names needing splitting:            [N]
  Names with prefixes/suffixes/particles: [N]
  Single-word names:                  [N]
  Excel apostrophe artifacts:         [N]

APOLLO MCP STATUS
  Connection: [connected / not connected]
  Domain resolution needed: [yes -- N records / no -- all domains present]
  [If MCP disconnected and resolution needed: display reconnection guidance]

ASSESSMENT
  [One or two sentences: file readiness, any concerns, anything unusual.]
----------------------------------------------
```

After presenting the summary, **proceed immediately to Phase 2.** The assessment is informational, not a gate. If hard stops applied, the skill would have already halted in 1.6.

---

## Phase 2 -- Transformation

Phase 2 modifies data. Every change is logged for the Prep Summary. This phase operates only on what survived Phase 1 assessment -- records with hard gaps are excluded, columns are mapped, and the scope of work is known.

### 2.1 -- Data Cleaning

Apply these operations to every record, in order:

**Row-level operations:**
1. Remove fully blank rows
2. Remove exact duplicate rows (match across all mapped columns after trimming and case normalization)
3. Remove same-domain duplicates: after domain normalization, if multiple rows share the same domain, keep the first occurrence (or the row with the most complete/formal name if one is clearly the legal entity name). Log every removal with both the kept and removed row's name.

**Field-level operations:**
4. Trim leading and trailing whitespace from all fields
5. Strip leading apostrophes from any field (`'acme.com` > `acme.com`)

**Name handling:**
6. Do NOT apply title case to company names, account names, or person names. Preserve the original casing from the source file. Only trim whitespace.

**Domain normalization** (apply to any field mapped to Company Domain or Domain):
7. Strip protocol (`https://`, `http://`)
8. Strip `www.` prefix
9. Strip trailing `/`
10. Lowercase the entire value
11. Replace placeholder values (`N/A`, `TBD`, `unknown`, `none`, `-`, `#N/A`, `null`, empty) with blank
12. Replace invalid domain formats (no dot, no TLD, contains spaces) with blank
13. Result format: `acme.com`

**Name splitting** (Contact only, when source has a combined Full Name field):
14. Default: first whitespace-delimited token > `First Name`, remainder > `Last Name`
15. Prefix handling (Dr., Mr., Ms., Mrs., Prof.): strip prefix, then apply default split. Log the stripped prefix.
16. Suffix handling (Jr., Sr., II, III, IV, Esq.): keep suffix attached to `Last Name` (e.g., `Smith Jr.`)
17. Single-word name (no spaces): place in `Last Name`, leave `First Name` blank, flag the record
18. Hyphenated names: preserve hyphens. Do not split on hyphens.
19. Particles (van, de, von, del, di, la, el, al-): preserve in `Last Name`. Split after the first token only. Example: "Maria van der Berg" > First: `Maria`, Last: `van der Berg`

**LinkedIn URL normalization:**
20. Normalize all valid formats to: `https://www.linkedin.com/in/<handle>`
21. Accept: `linkedin.com/in/handle`, `www.linkedin.com/in/handle`, `https://linkedin.com/in/handle`, any combination
22. Strip query parameters and anchors (`?locale=en_US`, `#section`). Keep only `/in/<handle>`.
23. If URL does not contain `/in/`: flag as malformed. Do not normalize. If it contains `/company/`: flag as "LinkedIn company page, not personal profile -- wrong type."

**Preserve original values for:**
- Job titles: no case changes beyond whitespace trimming
- Company names and account names: no case changes beyond whitespace trimming
- Person names: no case changes beyond whitespace trimming

### 2.2 -- Domain Resolution

This sub-phase resolves missing domains. It runs only for records where the domain field is blank after cleaning. Every lookup is logged with its resolution source.

**If no records need domain resolution:** Skip to 2.3.

**Credit consumption warning:** Before starting domain resolution, inform the SC:

> "Domain resolution will make up to [N] Apollo API calls to look up missing domains, which will consume credits. Confirm to proceed, or I can skip resolution and leave those domains blank."

Wait for SC confirmation before proceeding.

**Resolution sequence -- for each record missing a domain:**

**Step 1 -- Apollo MCP (primary):**

Use `apollo_mixed_companies_search` to search by company name:

```
tool: apollo_mixed_companies_search
parameters: { q_organization_name: "<Company Name stripped of legal suffixes>" }
```

If the response includes organizations with a domain/website:
- Check that the top result's name plausibly matches the query company name
- Extract the domain from the result
- Apply domain normalization (lowercase, strip protocol/www/slash)
- Assign to the record
- Log: `source: apollo_mcp`

If Apollo returns no results or no matching organization: proceed to Step 2.

**If Apollo MCP returns a tool-level error** (not just an empty result -- an actual failure): Log the error. Switch all remaining lookups to web search only. Do not retry Apollo MCP for subsequent records. Note in Prep Summary: "Apollo MCP disconnected mid-run."

**Step 2 -- Web search (fallback):**

Search for: `<Company Name> official website`

Extract the primary domain from the most credible top result (official site, LinkedIn company page, Crunchbase).

**Confidence rule:** Only assign a domain if the match is unambiguous.
- Company name is specific and the search returns one clear result > assign. Log: `source: web_search`
- Company name is generic (e.g., "Global Solutions", "Premier Services", "Apex Group") or search returns multiple unrelated companies > do NOT assign. Leave blank. Log: `source: failed -- ambiguous name`

**Domain-to-company plausibility check:** If the domain found does not plausibly correspond to the company name (different industry, different company entirely), do not assign. Log: `source: failed -- confidence check rejected`

**Step 3 -- Neither works:**

Leave domain blank. Log: `source: failed`

**For domain lookups, strip legal suffixes** (Inc., Corp., LLC, Ltd., GmbH, S.A., etc.) from the company name before searching. Use "Acme" not "Acme Inc." for the lookup query. Preserve the full legal name in the Company Name / Account Name output field.

**Domain Resolution Log** (maintained internally, reported in Prep Summary):

| Company Name | Status | Domain | Source |
|---|---|---|---|
| Acme Corp | resolved | acme.com | apollo_mcp |
| Premier Services | failed | -- | ambiguous name |
| Salesforce | resolved | salesforce.com | web_search |
| Unknown Startup | failed | -- | no results |

### 2.3 -- Build Output File

Construct the cleaned CSV with **exactly** the columns defined in the Output Contract. No extra columns. No source column names. No reordering.

- Contact: `First Name`, `Last Name`, `Title`, `Company Name`, `Company Domain`, `LinkedIn URL`
- Account: `Account Name`, `Domain`

Save as `apollo-data-test-ready.csv` using the file save mechanism available in the current environment. Present the file to the user for download.

**If file delivery fails:** Output the full CSV content in a fenced code block and instruct the user:

> "I wasn't able to save the file directly. Copy the CSV content below into a new file named `apollo-data-test-ready.csv`:"
>
> ```csv
> [full CSV content]
> ```

### 2.4 -- Spot-Check Validation (Optional)

After building the output file, offer the SC the option to validate a sample of records through Apollo's API to verify data alignment before running the full enrichment.

> "The cleaned file is ready. Want me to spot-check a sample of records through Apollo to verify the data lines up? This will consume [N] credits (sampling [M] of [total] records). Say yes to validate, or skip to proceed directly."

**If the SC declines or Apollo MCP is not connected:** Skip to Phase 3.

**If the SC confirms:**

**Sampling strategy:**
- For files with 20 or fewer records: sample every 5th record
- For files with 21-100 records: sample every 10th record
- For files with 101-500 records: sample every 25th record
- Minimum sample size: 3 records (if file has fewer than 15 records, sample 3 random)
- Maximum sample size: 20 records

**For Account Enrichment:**

Use `apollo_organizations_bulk_enrich` (up to 10 domains per call) to validate sampled records:

```
tool: apollo_organizations_bulk_enrich
parameters: { domains: ["domain1.com", "domain2.com", ...] }
```

For each result, check:
- Did Apollo return a match for this domain?
- Does the returned organization name plausibly match the Account Name in the file?
- Flag mismatches: "Domain acme.com returned 'Acme Holdings Ltd' but file says 'Acme Corp'" (this may be fine -- legal name vs. common name -- but the SC should know)

**For Contact Enrichment:**

Use `apollo_people_bulk_match` (up to 10 people per call) to validate sampled records:

```
tool: apollo_people_bulk_match
parameters: {
  details: [
    { first_name: "...", last_name: "...", organization_name: "...", domain: "..." },
    ...
  ]
}
```

For each result, check:
- Did Apollo find a match?
- Does the returned person's company match the file's company?
- Flag mismatches or no-matches

**Spot-Check Report:**

```
----------------------------------------------
SPOT-CHECK VALIDATION
----------------------------------------------
Records sampled:    [M] of [total]
Matches:            [N]  (Apollo found and confirmed)
Mismatches:         [N]  [list: row, expected, actual]
No match found:     [N]  [list: row, company/person]
Credits consumed:   [N]

ASSESSMENT
  [One sentence: "Sample looks clean" or "X mismatches found -- review before proceeding"]
----------------------------------------------
```

If mismatches are found, flag them but do not block. The SC decides whether to proceed.

---

## Phase 3 -- Output and Handoff

### 3.1 -- Deliver the File

Present `apollo-data-test-ready.csv` to the user. Confirm delivery with a brief statement:

> "Your cleaned file is ready: `apollo-data-test-ready.csv` -- [N] records, [M] columns."

### 3.2 -- Prep Summary

Present immediately after file delivery:

```
----------------------------------------------
DATA TEST PREP SUMMARY
----------------------------------------------
Test type:                [Contact Enrichment / Account Enrichment]
Records in (original):    [N]
Records out (cleaned):    [N]
  Blank rows removed:     [N]
  Exact duplicates removed: [N]
  Same-domain duplicates removed: [N]  [list: kept name / removed name for each]
  Hard-gap records excluded: [N]

COLUMN CHANGES
  [source] > [target]
  ...
  Dropped columns: [list or "none"]

DOMAIN RESOLUTION
  Needed resolution:             [N]
  Resolved via Apollo MCP:       [N]
  Resolved via web search:       [N]
  Failed -- ambiguous name:       [N]  [list company names]
  Failed -- no results:           [N]  [list company names]
  Failed -- confidence rejected:  [N]  [list company names]
  Apollo MCP status:             [connected / not connected / disconnected mid-run]
  [If no resolution needed: "All records had domains in source file."]

DATA QUALITY FIXES
  Names split (Full > First/Last): [N]
  Prefixes stripped:               [N]  [list if any]
  Names flagged (unusual):         [N]  [list: mononyms, particles, etc.]
  Domain placeholders cleared:     [N]
  Invalid domain formats cleared:  [N]
  Apostrophe artifacts stripped:   [N]
  LinkedIn URLs normalized:        [N]
  LinkedIn URLs flagged:           [N]  [list if any: malformed, company page, etc.]

SPOT-CHECK VALIDATION
  [If run: summary from 2.4]
  [If skipped: "Skipped -- SC declined or Apollo MCP not connected"]

RECORDS TO WATCH
  [List any records with quality concerns -- rejected domain matches,
   unusual name splits, ambiguous company names, mononyms,
   same-domain removals the SC should verify, spot-check mismatches, etc.
   If none, state "None."]

OUTPUT
  apollo-data-test-ready.csv -- [N] records, [M] columns
----------------------------------------------
```

### 3.3 -- Next Steps

After the Prep Summary, state:

> **Next steps:**
>
> 1. Download `apollo-data-test-ready.csv`
> 2. In your Apollo account, go to the enrichment or import flow and upload this file
> 3. Run the enrichment -- Apollo will match and fill each record
> 4. Export the enriched results from Apollo
> 5. Upload that Apollo export here and run it through the `apollo-fill-rate-report` skill to analyze field-level fill rates and coverage
>
> **Important:** Give `apollo-fill-rate-report` the Apollo export file -- not this cleaned file. The export contains Apollo's enrichment data. Running this cleaned file through fill-rate-report will just show your original data, not Apollo's results.

---

## Edge Cases

**Mixed file (contacts + accounts in one sheet):** Ask the user which type this is, or whether they merged two files. Do not guess. If they confirm it's mixed, ask them to split into two files and run each separately.

**Single-column file:** For contacts, hard stop -- not enough data. For accounts, if the column contains company names, proceed (domains will be resolved in Phase 2). If the column contents are ambiguous, ask the user what the column represents.

**Placeholder domain values:** `N/A`, `TBD`, `unknown`, `none`, `-`, `#N/A`, `null`, blank, or any string that is clearly not a domain > treat as missing. Route to domain resolution.

**Invalid domain formats:** Strings with no dot, no TLD, or containing spaces are not valid domains. Treat as missing and route to domain resolution.

**LinkedIn company page URLs** (`linkedin.com/company/...`): Do not treat as a personal LinkedIn URL. Flag: "This is a company LinkedIn page, not a personal profile URL." Leave the `LinkedIn URL` field blank for that record.

**LinkedIn URLs with query parameters or anchors** (`linkedin.com/in/handle?locale=en_US`): Strip query parameters and anchors during normalization. Keep only the `/in/<handle>` portion.

**Excel leading apostrophes:** Strip the `'` prefix. This is an Excel artifact for preserving text formatting on fields that look numeric. The underlying value is correct.

**Names with particles** (van der Berg, de la Cruz, O'Brien, MacDonald): Preserve particles and apostrophes. Apply the default split (first token > First, rest > Last). Flag for SC review in the Prep Summary.

**Company names with legal suffixes** (Acme Corp., Acme Inc., Acme LLC): Strip for domain lookup queries only. Preserve the full name in the output `Company Name` / `Account Name` field.

**Same-domain duplicates:** After domain normalization, if multiple rows resolve to the same domain, they will produce identical enrichment results from Apollo. Auto-remove the duplicate, keeping the row with the more complete or formal name (e.g., keep "Baanx Group Ltd" over "Baanx"). Log both the kept and removed name in the Prep Summary so the SC can verify.

**Duplicates that differ only by case or whitespace:** After trimming and normalizing, if two rows are identical across all mapped columns, remove the later one. Log each removal.

**Domain returned by search that doesn't match the company:** If the domain found via `apollo_mixed_companies_search` or web search does not plausibly correspond to the company name provided (different industry, different company entirely), do not assign. Log as failed with reason.

**Very large files (over 500 records):** Hard stop. Inform the user:

> "This file has [N] rows. The maximum for a single data test run is 500 records. Please split the file into batches of 500 or fewer and run each batch through this skill separately."

Do not silently truncate or drop records.

**File with extra header rows or merged cells** (common in Excel exports): If the first row doesn't look like column headers (e.g., it's a title or date), check the second and third rows. If code execution is available, use it to inspect the raw structure. Ask the user to confirm which row contains the headers if unclear.

**Multi-sheet Excel files:** Check for multiple sheets before reading data. If multiple sheets exist, list them and ask the SC which one contains the data. Do not silently default to the first sheet.

**Records where First Name and Last Name columns both exist but Last Name is entirely blank:** Treat the First Name column as a full name field. Apply name splitting rules to it.

---

## Error Handling

| Failure Point | Response |
|---|---|
| **Apollo MCP not connected, domains need resolving** | Inform SC. Offer to proceed with web search only, or wait for reconnection. |
| **Apollo MCP not connected, all domains present** | Proceed normally. Note MCP status in summary. Spot-check validation unavailable. |
| **Apollo MCP fails mid-run (Phase 2)** | Log error. Fall back to web search for all remaining lookups. Note in Prep Summary: "Apollo MCP disconnected during domain resolution; [N] records fell back to web search only." |
| **Web search unavailable** | Skip web search fallback. All records that Apollo MCP couldn't resolve will have blank domains. Note in Prep Summary. |
| **Code execution unavailable (XLSX upload)** | Ask user to re-upload as CSV. Do not attempt to parse XLSX as text. |
| **Code execution fails during conversion** | Report the specific error. Ask for CSV re-upload. |
| **File exceeds 500 records** | Hard stop. Instruct user to split into batches of 500 or fewer. Do not truncate. |
| **Output file save fails** | Print full CSV in a code block with copy instructions. |
| **Both Apollo MCP and web search fail for a record** | Leave domain blank. Flag the record. Continue with remaining records. |
| **Apollo MCP returns a result but domain is missing from the response** | Treat as no result. Fall back to web search. |
| **Uploaded file is password-protected** | Inform user: "This file appears to be password-protected. Please remove the password and re-upload, or export the data as an unprotected CSV." |
| **All records fail hard-gap checks** | Do not produce an output file. Inform the user that no records passed validation and specify what's missing. |
| **Multi-sheet Excel, SC doesn't specify which sheet** | Wait for response. Do not guess. |
| **Spot-check validation finds mismatches** | Flag in report but do not block. SC decides whether to proceed. |
