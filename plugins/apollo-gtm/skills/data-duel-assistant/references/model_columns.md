# Canonical 34-Column Data Duel Schema

This is the authoritative column schema for all duel CSVs. Every file is normalized to this
structure on intake (Phase 2). Columns are grouped into three blocks.

---

## Block 1 — Input Identifiers (Columns 1–18)

Customer-provided data. These are the columns Claude normalizes, validates, and uses for matching.

| # | Column Name | Type | Description | Required for Enrichment |
|---|-------------|------|-------------|-------------------------|
| 1 | `row_id` | Integer | Sequential row number added by Claude on intake. Enables row-level tracking across versions. | Always |
| 2 | `first_name` | String | Contact first name | Contact duels |
| 3 | `last_name` | String | Contact last name | Contact duels |
| 4 | `title` | String | Job title at time of export | Optional |
| 5 | `email` | String | Existing email address (work or personal) | Optional |
| 6 | `phone` | String | Existing phone (office/main) | Optional |
| 7 | `mobile_phone` | String | Existing mobile number | Optional |
| 8 | `person_linkedin_url` | URL | Full LinkedIn profile URL (linkedin.com/in/...) | Strong ID |
| 9 | `organization_name` | String | Company name as written in the customer's system | Always |
| 10 | `organization_website` | String | Company domain (e.g., `acme.com`). Strip protocols on intake. | **Primary matching ID** |
| 11 | `organization_linkedin_url` | URL | Company LinkedIn page (linkedin.com/company/...) | Secondary ID |
| 12 | `city` | String | Contact or HQ city | Optional |
| 13 | `state` | String | Contact or HQ state/province | Optional |
| 14 | `country` | String | Contact or HQ country | Optional |
| 15 | `industry` | String | Industry vertical | Optional |
| 16 | `employees` | Integer | Company employee count (as of customer export) | Optional |
| 17 | `seniority` | String | Seniority level (Director, VP, C-Suite, etc.) if provided | Optional |
| 18 | `department` | String | Functional department (Sales, Engineering, etc.) if provided | Optional |

---

## Block 2 — Apollo Enrichment Output (Columns 19–31)

Populated after Apollo enrichment runs. These columns are empty on intake and filled by Apollo.

**Contact-level output (columns 19–26) — present in contact enrichment duels:**

| # | Column Name | Type | Description | Valid Values |
|---|-------------|------|-------------|--------------|
| 19 | `apollo_match_status` | String | Did Apollo identify this contact/account? | `Matched`, `Not Matched` |
| 20 | `apollo_person_id` | String | Apollo's internal contact ID (for debugging match issues) | Apollo UUID or blank |
| 21 | `apollo_email` | String | Email returned by Apollo (Apollo-native, Version A) | Email address or blank |
| 22 | `apollo_email_status` | String | Apollo's email verification verdict | `verified`, `likely to engage`, `risky`, `do not email`, blank |
| 23 | `apollo_phone` | String | Office/direct phone returned by Apollo | Phone number or blank |
| 24 | `apollo_mobile_phone` | String | Mobile returned by Apollo | Phone number or blank |
| 25 | `apollo_title` | String | Title on Apollo's record (may differ from customer's title) | String or blank |
| 26 | `apollo_seniority` | String | Seniority classification from Apollo | String or blank |

**Account-level firmographic output (columns 27–31) — present in account enrichment duels:**

These columns are populated when running account enrichment. They are the primary fill-rate
metrics customers test in account duels. The 80% fill-rate threshold applies to each field.

| # | Column Name | Type | Description | Typical Duel Threshold |
|---|-------------|------|-------------|------------------------|
| 27 | `apollo_revenue` | String | Annual revenue band or exact figure | ≥80% fill on matched rows |
| 28 | `apollo_employee_count` | Integer | Employee headcount from Apollo | ≥80% fill on matched rows |
| 29 | `apollo_industry` | String | Industry classification from Apollo | ≥80% fill on matched rows |
| 30 | `apollo_funding` | String | Latest funding round / total raised | ≥80% fill — structurally low; flag proactively |
| 31 | `apollo_hq_location` | String | HQ city, state, country | ≥80% fill on matched rows |

> **Note on Revenue and Funding:** These fields consistently underperform the 80% threshold
> across all B2B data vendors, including ZoomInfo. When these come up in a duel, frame proactively:
> "Revenue and funding are hard to verify at scale for private companies — this is an industry-wide
> limitation, not specific to Apollo." Do not let the customer treat these as Apollo-unique gaps.

---

## Block 3 — Waterfall Output (Columns 32–34)

Populated only when waterfall is run (Version B). Empty in Version A files.

| # | Column Name | Type | Description | Notes |
|---|-------------|------|-------------|-------|
| 32 | `waterfall_email` | String | Best email found across waterfall providers | Blank if no uplift vs. apollo_email |
| 33 | `waterfall_phone` | String | Best phone found across waterfall providers | Blank if no uplift |
| 34 | `waterfall_source` | String | Which provider supplied the waterfall result | `LeadMagic`, `Prospeo`, `Limadata`, `Apollo 3P`, blank |

---

## Notes on Non-Model Columns

If the customer's file contains columns that don't map to any of the 34 above (e.g., CRM IDs,
internal account codes, custom scores), keep them at the end of the file in their original
column order. Do not discard customer columns — they may be needed for the customer to reconcile
results back to their CRM.

Label any retained non-model columns by prepending `_raw_` (e.g., `_raw_sfdc_account_id`).

---

## Column Order Enforcement

When normalizing a file in Phase 2, reorder columns strictly to match this table (1–34), then
append any `_raw_` non-model columns at the end. Consistent column ordering is critical because:
- The `id_health.py` and `analyze_results.py` scripts look for columns by name, not position
- Humans reviewing the file can find columns predictably
- AI Sheets and SFDC imports benefit from consistent schemas

---

## Version Suffixes for Multi-Run Duels

Files with the same base name but different processing states use these suffixes:

| Suffix | Meaning |
|--------|---------|
| `_normalized` | After Phase 2 (columns normalized, row_id added) |
| `_id_fixed` | After Phase 4 (domains resolved) |
| `_apollo_only` | After Phase 5A enrichment (Version A) |
| `_with_waterfall` | After Phase 5C enrichment (Version B) |
| `_v2`, `_v3` | Second/third full iteration (full re-run with new input file) |

Example sequence:
```
contact_enrichment_2026-04-08_Acme_normalized.csv
contact_enrichment_2026-04-08_Acme_id_fixed.csv
contact_enrichment_2026-04-08_Acme_apollo_only.csv
contact_enrichment_2026-04-08_Acme_with_waterfall.csv
```
