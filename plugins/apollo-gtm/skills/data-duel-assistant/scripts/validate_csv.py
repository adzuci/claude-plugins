"""
CSV Validation — Data Duel Assistant
Phase 2: Record count, column audit, and model schema comparison.

Usage:
  python validate_csv.py <path_to_csv>

Output:
  - Record count (data rows, excluding header)
  - Column inventory against the 34-column model schema
  - Mapping suggestions for unknown columns
  - Hard stop if record count exceeds 1,500
"""

from __future__ import annotations

import pandas as pd
import sys
from pathlib import Path

# ── Model schema ────────────────────────────────────────────────────────────────

MODEL_COLUMNS = [
    "row_id",
    "first_name",
    "last_name",
    "title",
    "email",
    "phone",
    "mobile_phone",
    "person_linkedin_url",
    "organization_name",
    "organization_website",
    "organization_linkedin_url",
    "city",
    "state",
    "country",
    "industry",
    "employees",
    "seniority",
    "department",
    # Apollo enrichment outputs
    "apollo_match_status",
    "apollo_person_id",
    "apollo_email",
    "apollo_email_status",
    "apollo_phone",
    "apollo_mobile_phone",
    "apollo_title",
    "apollo_seniority",
    # Apollo account-level firmographic outputs
    "apollo_revenue",
    "apollo_employee_count",
    "apollo_industry",
    "apollo_funding",
    "apollo_hq_location",
    # Waterfall outputs
    "waterfall_email",
    "waterfall_phone",
    "waterfall_source",
]

HARD_LIMIT = 1500

# ── Common non-standard column aliases (supplement column_mappings.json) ────────

QUICK_ALIASES = {
    "company": "organization_name",
    "account name": "organization_name",
    "account_name": "organization_name",
    "corp website": "organization_website",
    "company url": "organization_website",
    "company domain": "organization_website",
    "domain": "organization_website",
    "web": "organization_website",
    "website": "organization_website",
    "job title": "title",
    "position": "title",
    "linkedin": "person_linkedin_url",
    "li url": "person_linkedin_url",
    "contact linkedin": "person_linkedin_url",
    "company linkedin": "organization_linkedin_url",
    "email address": "email",
    "work email": "email",
    "phone number": "phone",
    "mobile": "mobile_phone",
    "employee count": "employees",
    "headcount": "employees",
    "firstname": "first_name",
    "lastname": "last_name",
    "full name": "SPLIT:first_name,last_name",
    "name": "SPLIT:first_name,last_name",
    "contact name": "SPLIT:first_name,last_name",
}

ENRICHMENT_BLOCK_COLS = {
    "apollo_match_status", "apollo_person_id", "apollo_email",
    "apollo_email_status", "apollo_phone", "apollo_mobile_phone",
    "apollo_title", "apollo_seniority",
    "waterfall_email", "waterfall_phone", "waterfall_source",
}

INPUT_REQUIRED = ["organization_name"]  # minimum bar for any duel type


# ── Helpers ──────────────────────────────────────────────────────────────────────

def normalize_col(name: str) -> str:
    return name.strip().lower().replace("-", "_").replace(" ", "_")


def match_column(col: str) -> tuple[str | None, str | None]:
    """
    Returns (model_col, note).
    model_col: the canonical model column name, or None if unknown.
    note: a human-readable explanation of the mapping.
    """
    col_lower = col.strip().lower()
    col_normalized = normalize_col(col_lower)

    # Direct model match
    if col_normalized in MODEL_COLUMNS:
        return col_normalized, None

    # Quick alias lookup
    if col_lower in QUICK_ALIASES:
        target = QUICK_ALIASES[col_lower]
        return target, f"Alias → {target}"

    # Partial match (substring)
    for model_col in MODEL_COLUMNS:
        if model_col in col_normalized or col_normalized in model_col:
            return model_col, f"Partial match → {model_col} (confirm with rep)"

    return None, None


# ── Main ─────────────────────────────────────────────────────────────────────────

def validate_file(filepath: str) -> None:
    path = Path(filepath)
    if not path.exists():
        print(f"ERROR: File not found: {filepath}")
        sys.exit(1)

    df = None
    for enc in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
        try:
            df = pd.read_csv(filepath, encoding=enc)
            if enc != 'utf-8':
                print(f"  ⚠  Encoding: file read as {enc} (not UTF-8). Safe to proceed.")
            break
        except Exception:
            continue
    if df is None:
        print(f"ERROR: Could not parse CSV with any common encoding.")
        sys.exit(1)

    # Strip completely empty rows (common in Salesforce exports)
    raw_rows = len(df)
    df = df[~df.isnull().all(axis=1)].copy()
    empty_dropped = raw_rows - len(df)
    if empty_dropped > 0:
        print(f"  ⚠  Stripped {empty_dropped:,} completely empty rows (Salesforce export artifact).")
        print(f"     Raw rows: {raw_rows:,} → Usable rows: {len(df):,}")

    total_rows = len(df)
    columns = list(df.columns)

    print("\n" + "=" * 60)
    print("  CSV VALIDATION REPORT")
    print("=" * 60)
    print(f"  File:        {path.name}")
    print(f"  Total rows:  {total_rows} (data rows, header excluded)")
    print(f"  Columns:     {len(columns)}")

    # ── Record count gate ────────────────────────────────────────────────────────
    print()
    if total_rows > HARD_LIMIT:
        print(f"  🔴 HARD STOP — {total_rows} rows exceeds the {HARD_LIMIT}-row limit.")
        print(f"  Tell the rep: \"This file has {total_rows} rows. Our standard duel limit is {HARD_LIMIT}.")
        print(f"  A well-designed {min(total_rows, 1000)}-row sample gives 95% of the insight.")
        print(f"  Please re-upload a trimmed file.\"")
        print("=" * 60 + "\n")
        sys.exit(2)
    elif total_rows > 1000:
        print(f"  🟡 LARGE FILE — {total_rows} rows is within limit but consider discussing")
        print(f"     credit budget with the SC lead before proceeding.")
    else:
        print(f"  🟢 Record count OK — within the {HARD_LIMIT}-row limit.")

    # ── Column audit ─────────────────────────────────────────────────────────────
    print()
    print("  COLUMN AUDIT")
    print(f"  {'-'*56}")

    matched_cols = {}       # file_col → model_col
    split_cols = {}         # file_col → SPLIT instruction
    unknown_cols = []       # need rep input
    raw_cols = []           # clearly non-model (IDs, custom fields)
    enrichment_cols = []    # already enriched — note this

    for col in columns:
        model_col, note = match_column(col)

        if model_col is None:
            # Check if it looks like a CRM/internal field
            col_l = col.lower()
            if any(x in col_l for x in ["id", "sfdc", "crm", "record", "score", "tier", "segment", "custom"]):
                raw_cols.append(col)
            else:
                unknown_cols.append(col)
        elif model_col.startswith("SPLIT:"):
            split_cols[col] = model_col
            print(f"  ↔  {col:<35} → {model_col} (split required)")
        elif model_col in ENRICHMENT_BLOCK_COLS:
            enrichment_cols.append((col, model_col, note))
        else:
            matched_cols[col] = (model_col, note)
            tag = f"= {model_col}" if normalize_col(col) != model_col else "(exact match)"
            label = f" [{note}]" if note else ""
            print(f"  ✓  {col:<35} {tag}{label}")

    if enrichment_cols:
        print()
        print("  ℹ  ENRICHMENT COLUMNS PRESENT (already processed?):")
        for col, model_col, note in enrichment_cols:
            print(f"     {col:<35} → {model_col}")

    if raw_cols:
        print()
        print("  📎 NON-MODEL COLUMNS (will be kept as _raw_):")
        for col in raw_cols:
            print(f"     {col}")

    if unknown_cols:
        print()
        print("  ❓ UNKNOWN COLUMNS — need rep input:")
        for col in unknown_cols:
            # Sample 3 non-null values
            sample_vals = df[col].dropna().astype(str).head(3).tolist()
            sample_str = " | ".join(sample_vals) if sample_vals else "(all empty)"
            print(f"     {col}")
            print(f"       Sample values: {sample_str}")
            print(f"       → Ask rep: \"What does '{col}' represent? Does it map to a model field?\"")

    # ── Missing input columns check ───────────────────────────────────────────────
    model_cols_present = set()
    for col, (model_col, _) in matched_cols.items():
        model_cols_present.add(model_col)

    missing_critical = [c for c in INPUT_REQUIRED if c not in model_cols_present]
    if missing_critical:
        print()
        print(f"  ⚠  MISSING CRITICAL COLUMNS: {', '.join(missing_critical)}")
        print(f"     File may not be ready for enrichment. Check with rep.")

    # ── Spot-checks on key columns ────────────────────────────────────────────────
    print()
    print("  SPOT-CHECKS")
    print(f"  {'-'*56}")

    website_col = None
    for orig_col, (model_col, _) in matched_cols.items():
        if model_col == "organization_website":
            website_col = orig_col
            break

    email_col = None
    for orig_col, (model_col, _) in matched_cols.items():
        if model_col == "email":
            email_col = orig_col
            break

    if website_col:
        website_vals = df[website_col].dropna().astype(str)
        # LinkedIn URLs in website field
        li_as_website = website_vals[website_vals.str.contains('linkedin.com', case=False)]
        if len(li_as_website) > 0:
            print(f"  ⚠  {len(li_as_website)} row(s) have a LinkedIn URL in organization_website.")
            print(f"     These must be moved to person_linkedin_url or organization_linkedin_url.")
            print(f"     Rows: {list(li_as_website.index[:5])}")
        else:
            print(f"  ✓  No LinkedIn URLs found in organization_website.")

        # Email domain vs website domain mismatch
        if email_col:
            def get_domain(url):
                if pd.isna(url): return None
                s = str(url).strip().lower()
                s = s.replace('https://','').replace('http://','').replace('www.','')
                return s.split('/')[0].strip()
            def get_email_domain(email):
                if pd.isna(email): return None
                parts = str(email).split('@')
                return parts[-1].lower().strip() if len(parts) == 2 else None

            web_domains   = df[website_col].apply(get_domain)
            email_domains = df[email_col].apply(get_email_domain)
            mismatch = (web_domains.notna() & email_domains.notna() & (web_domains != email_domains))
            n_mismatch = mismatch.sum()
            if n_mismatch > 0:
                print(f"  ℹ  {n_mismatch} row(s) have email domain ≠ org website domain.")
                print(f"     This may indicate job-changers or personal emails. Spot-check before enrichment.")
            else:
                print(f"  ✓  Email domains align with org website domains.")


    print()
    print("  SUMMARY")
    print(f"  ├─ Matched to model:   {len(matched_cols) + len(split_cols)} columns")
    print(f"  ├─ Non-model (raw):    {len(raw_cols)} columns → will be kept as _raw_")
    print(f"  ├─ Need rep input:     {len(unknown_cols)} columns")
    print(f"  └─ Enrichment cols:    {len(enrichment_cols)} columns")

    next_steps = []
    if split_cols:
        next_steps.append(f"Split {len(split_cols)} full-name column(s) into first_name / last_name")
    if unknown_cols:
        next_steps.append(f"Resolve {len(unknown_cols)} unknown column(s) with rep before proceeding to Phase 3")
    if not next_steps:
        next_steps.append("Column audit clean — proceed to Phase 3 (ID Health)")

    print()
    print("  NEXT STEPS:")
    for step in next_steps:
        print(f"  → {step}")

    print("=" * 60 + "\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_csv.py <path_to_csv>")
        sys.exit(1)
    validate_file(sys.argv[1])
