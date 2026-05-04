# Vendor JSON Schema Reference

AI Sheets waterfall enrichment returns one JSON blob column per vendor in the exported CSV.
This file documents the schema for each vendor so Claude can extract fields reliably in Phase 6.

---

## How to identify the column names

After a multi-vendor AI Sheets export, vendor columns follow this naming pattern:

| Vendor | Column name in export |
|--------|-----------------------|
| Apollo | `Apollo Enrich Person` |
| Prospeo | `Prospeo Enrich Person` |
| LimaData | `LimaData Enrich Person` |
| LeadMagic | `LeadMagic Enrich Person` |

Column names may vary slightly — scan the header row for substrings `Apollo`, `Prospeo`,
`LimaData`, `LeadMagic` to identify them programmatically.

---

## Parsing rules (apply to all vendors)

Before extracting any field, treat these as "no data":
- Empty string, `{}`, `null`, `NaN`
- A dict with `"error": true` at the top level or inside `vendor_response`
- A Prospeo response with `"error_code": "NO_MATCH"`

```python
def safe_json(val):
    if pd.isna(val) or str(val).strip() in ('', '{}', 'null'): return {}
    try: return json.loads(str(val))
    except: return {}

def is_error(d):
    return not d or d.get('error', False)
```

---

## Apollo — schema

Apollo returns a matched contact when the dict is non-empty and has no `error` key.

**Match detection:** `bool(d) and not d.get('error')`

**Key fields:**

```json
{
  "id": "apollo_uuid",
  "first_name": "Aaron",
  "last_name": "Wysko",
  "name": "Aaron Wysko",
  "title": "Chief Financial Officer",
  "seniority": "c_suite",
  "department": "finance",
  "linkedin_url": "http://www.linkedin.com/in/...",
  "city": "Lawrenceville",
  "state": "Georgia",
  "country": "United States",
  "current_job_start_date": "2024-09-01",
  "duration_at_current_job_months": "19 Months",
  "job_history": ["..."],
  "organization": {
    "name": "Company Name",
    "phone": "+1 770-777-6703"
  }
}
```

**Important:** Apollo does NOT return `email` in this response when the AI Sheets run is
scoped to identity-only enrichment. Email is only returned when **email unlock** is explicitly
enabled in the AI Sheets enrichment configuration. Always check for this before Phase 5 —
see the pre-flight checklist in phases.md.

**Extraction:**
```python
email           = d.get('email')                      # None if email unlock not enabled
phone           = d.get('organization', {}).get('phone')  # HQ/org phone, not direct dial
linkedin_url    = d.get('linkedin_url')
seniority       = d.get('seniority')
department      = d.get('department')
title           = d.get('title')
current_employer= d.get('organization', {}).get('name')
job_start_date  = d.get('current_job_start_date')
tenure_months   = d.get('duration_at_current_job_months')
```

---

## Prospeo — schema

Prospeo returns a matched contact when the dict has no `error: true` and has a `person` key.

**Match detection:** `bool(d) and not d.get('error')`

**Key fields:**

```json
{
  "person": {
    "person_id": "...",
    "first_name": "Aaron",
    "last_name": "Murphy",
    "full_name": "Aaron Murphy",
    "linkedin_url": "https://www.linkedin.com/in/...",
    "current_job_title": "Vice President & Director of Survey",
    "job_history": [...],
    "email": {
      "status": "VERIFIED",
      "revealed": true,
      "email": "aaron@company.com",
      "verification_method": "BOUNCEBAN",
      "email_mx_provider": "Barracuda"
    },
    "mobile": {
      "number": "+1...",
      "country": "US"
    }
  }
}
```

**Email status values:** `VERIFIED` | `UNAVAILABLE`
Only treat `VERIFIED` emails as usable for enrichment output.

**Extraction:**
```python
p = d.get('person', d)
e = p.get('email', {})
email        = e.get('email') if isinstance(e, dict) and e.get('status') == 'VERIFIED' else None
email_status = e.get('status') if isinstance(e, dict) else None
linkedin_url = p.get('linkedin_url')
mob          = p.get('mobile', {})
mobile       = mob.get('number') if isinstance(mob, dict) else mob
```

---

## LimaData — schema

LimaData returns identity and LinkedIn data only — no email, no phone in current integration.

**Match detection:** `bool(d) and not d.get('error')`

**Key fields:**

```json
{
  "person": {
    "name": "Faia Anthony Tappe",
    "first_name": "Faia",
    "last_name": "Anthony Tappe",
    "headline": "Principal at Tappe Associates",
    "gender": "male",
    "location": { "city": "...", "state": "...", "country": "..." },
    "linkedin": {
      "handle": "faia-anthony-tappe-38ab578",
      "url": "https://linkedin.com/in/..."
    },
    "employment": {
      "title": "Principal",
      "company_name": "Tappe Associates",
      "seniority": "Strategic"
    }
  }
}
```

**Extraction:**
```python
p           = d.get('person', d)
li          = p.get('linkedin', {})
emp         = p.get('employment', {})
linkedin_url= li.get('url') if isinstance(li, dict) else None
headline    = p.get('headline')
title       = emp.get('title') if isinstance(emp, dict) else None
seniority   = emp.get('seniority') if isinstance(emp, dict) else None
```

---

## Multi-vendor match + coalesce pattern

When all three vendors are present, always compute:

1. **Per-vendor match rate** — how many rows each vendor matched independently
2. **Combined match rate** — rows matched by ANY vendor (`apollo | prospeo | limadata`)
3. **Waterfall uplift** — incremental contacts each vendor adds beyond Apollo

```python
apollo_match   = apollo_parsed.apply(lambda d: bool(d) and not d.get('error'))
prospeo_match  = prospeo_parsed.apply(lambda d: bool(d) and not d.get('error'))
limadata_match = limadata_parsed.apply(lambda d: bool(d) and not d.get('error'))
any_match      = apollo_match | prospeo_match | limadata_match

# match_source column (single column, human-readable)
def match_source(ap, pr, li):
    sources = []
    if ap: sources.append('Apollo')
    if pr: sources.append('Prospeo')
    if li: sources.append('LimaData')
    return ', '.join(sources) if sources else 'No Match'
```

**Coalesce priority for enriched_ fields:**
Apollo first → Prospeo second → LimaData third (for fields where multiple vendors return data).

---

## Output CSV schema (multi-vendor enrichment)

After parsing, the customer-ready output CSV should follow this column order:

**Block 1 — Input (as-is, original column names):**
All original columns from the customer's file, untouched.

**Block 2 — Match source (1 col):**
`match_source` — comma-separated list of vendors that matched the row, or `No Match`.

**Block 3 — Apollo enriched (prefix: `apollo_`):**
`apollo_linkedin_url`, `apollo_title`, `apollo_seniority`, `apollo_department`,
`apollo_city`, `apollo_state`, `apollo_org_phone`, `apollo_current_employer`,
`apollo_job_start_date`, `apollo_tenure_months`

**Block 4 — 3P enriched (prefix: `3p_`):**
`3p_email`, `3p_mobile`, `3p_linkedin_url`, `3p_headline`, `3p_seniority`, `3p_title`

**Block 5 — Consolidated enriched (prefix: `enriched_`):**
Best value coalesced from Apollo + 3P. These are the columns the customer should use.
`enriched_email`, `enriched_phone`, `enriched_mobile`, `enriched_linkedin_url`,
`enriched_title`, `enriched_seniority`, `enriched_department`, `enriched_headline`,
`enriched_current_employer`, `enriched_job_start_date`, `enriched_tenure_months`

Use `scripts/generate_output.py` to produce this file automatically.
