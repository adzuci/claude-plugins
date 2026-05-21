"""
Identifier Health Assessment — Data Duel Assistant
Scores a normalized CSV for Apollo matching readiness.
"""

from __future__ import annotations

import pandas as pd
import sys
import re
from pathlib import Path

# Values treated as absent regardless of column presence
JUNK_VALUES = {
    "#n/a", "n/a", "na", "null", "none", "unknown", "-", "—",
    "#na", "nan", "#value!", "#ref!", "#error!", "nil", "undefined",
    "not available", "not provided", "n.a.", "n.a", "tbd", "tbc", ""
}

GENERIC_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com",
    "aol.com", "protonmail.com", "mail.com", "ymail.com", "live.com",
    "me.com", "msn.com", "googlemail.com"
}

COLUMN_MAP = {
    "domain": ["organization_website", "domain", "website", "company_domain", "web"],
    "person_li": ["person_linkedin_url", "linkedin_url", "linkedin", "li_url", "contact_linkedin"],
    "email": ["email", "work_email", "email_address", "contact_email"],
    "org_li": ["organization_linkedin_url", "company_linkedin", "company_linkedin_url"],
    "first_name": ["first_name", "firstname", "first"],
    "last_name": ["last_name", "lastname", "last"],
    "org_name": ["organization_name", "company", "company_name", "account_name"],
}


def is_junk(value) -> bool:
    if pd.isna(value):
        return True
    s = str(value).strip().lower()
    return s in JUNK_VALUES or len(s) == 0 or re.match(r'^[\s\-_\.]+$', s) is not None


def find_col(df: pd.DataFrame, aliases: list[str]) -> str | None:
    cols_lower = {c.lower(): c for c in df.columns}
    for alias in aliases:
        if alias.lower() in cols_lower:
            return cols_lower[alias.lower()]
    return None


def has_valid_domain(value) -> bool:
    if is_junk(value):
        return False
    s = str(value).strip().lower()
    # Remove protocol prefixes
    s = re.sub(r'^https?://', '', s)
    s = s.rstrip('/')
    # Must have a dot and a TLD of at least 2 chars
    if '.' not in s:
        return False
    parts = s.split('.')
    if len(parts[-1]) < 2:
        return False
    if s in GENERIC_EMAIL_DOMAINS:
        return False
    return True


def has_valid_li_url(value) -> bool:
    if is_junk(value):
        return False
    s = str(value).strip().lower()
    return 'linkedin.com' in s


def has_valid_email(value) -> tuple[bool, bool]:
    """Returns (has_email, is_generic)"""
    if is_junk(value):
        return False, False
    s = str(value).strip().lower()
    if '@' not in s:
        return False, False
    domain = s.split('@')[-1]
    return True, domain in GENERIC_EMAIL_DOMAINS


def score_file(filepath: str) -> None:
    df = pd.read_csv(filepath)
    total = len(df)

    if total == 0:
        print("ERROR: File is empty.")
        sys.exit(1)

    # Find columns
    domain_col   = find_col(df, COLUMN_MAP["domain"])
    person_li_col = find_col(df, COLUMN_MAP["person_li"])
    email_col    = find_col(df, COLUMN_MAP["email"])
    org_li_col   = find_col(df, COLUMN_MAP["org_li"])
    org_name_col = find_col(df, COLUMN_MAP["org_name"])

    # Score each signal
    has_domain    = df[domain_col].apply(has_valid_domain)    if domain_col    else pd.Series([False]*total)
    has_person_li = df[person_li_col].apply(has_valid_li_url) if person_li_col else pd.Series([False]*total)
    has_org_li    = df[org_li_col].apply(has_valid_li_url)    if org_li_col    else pd.Series([False]*total)

    email_results     = df[email_col].apply(has_valid_email)  if email_col     else pd.Series([(False, False)]*total)
    has_email         = email_results.apply(lambda x: x[0])
    has_generic_email = email_results.apply(lambda x: x[1])
    has_work_email    = has_email & ~has_generic_email

    # Strong identifier: domain OR person LinkedIn OR work email
    has_strong_id = has_domain | has_person_li | has_work_email

    # Rows that are truly identifier-poor
    has_any_id = has_strong_id | has_org_li
    identifier_poor = ~has_any_id

    pct = lambda n: f"{n/total*100:.1f}%  ({n} rows)"

    print("\n" + "=" * 50)
    print("  IDENTIFIER HEALTH REPORT")
    print("=" * 50)
    print(f"  File:        {Path(filepath).name}")
    print(f"  Total rows:  {total}")
    print()
    print("  PRIMARY IDENTIFIERS (Apollo matching signals)")
    print(f"  ├─ Company Domain           {pct(has_domain.sum())}")
    if not domain_col:
        print("     ⚠  Column not found in file")
    print(f"  ├─ Person LinkedIn URL      {pct(has_person_li.sum())}")
    if not person_li_col:
        print("     ⚠  Column not found in file")
    print(f"  └─ Work Email (non-generic) {pct(has_work_email.sum())}")
    if has_generic_email.sum() > 0:
        print(f"     ↳ Generic emails (gmail/outlook/etc): {has_generic_email.sum()} rows — treated as weak signal")
    print()
    print("  SECONDARY IDENTIFIERS")
    print(f"  └─ Company LinkedIn URL     {pct(has_org_li.sum())}")
    print()
    print("  SUMMARY")
    strong_n = has_strong_id.sum()
    print(f"  ├─ Rows with ≥1 strong identifier:  {pct(strong_n)}")
    print(f"  └─ Rows with NO strong identifier:  {pct(identifier_poor.sum())}  ← MATCH RATE CONSTRAINED")
    print()

    pct_strong = strong_n / total * 100
    if pct_strong >= 70:
        tier = "🟢 GREEN — proceed normally"
        ceiling = f"{int(pct_strong * 0.85)}–{int(pct_strong * 0.95)}%"
    elif pct_strong >= 40:
        tier = "🟡 YELLOW — proceed with explicit caveat to rep and customer"
        ceiling = f"{int(pct_strong * 0.70)}–{int(pct_strong * 0.85)}%"
    elif pct_strong >= 20:
        tier = "🟠 AMBER — stop; offer rep: augment file or get written sign-off before proceeding"
        ceiling = f"{int(pct_strong * 0.50)}–{int(pct_strong * 0.70)}% (sparse)"
    else:
        tier = "🔴 RED — do not run enrichment; escalate to SC lead"
        ceiling = f"<{int(pct_strong * 0.50)}% (highly variable; results will mislead)"

    print(f"  Identifier health tier:  {tier}")
    print(f"  Estimated match ceiling: {ceiling}")
    print("=" * 50 + "\n")

    # Flag top junk issues
    junk_issues = []
    if domain_col:
        junk_domain = df[domain_col].apply(lambda v: not is_junk(v) and not has_valid_domain(v))
        if junk_domain.sum() > 0:
            junk_issues.append(f"  ⚠  {junk_domain.sum()} rows have a domain value that looks invalid or junk")
    if junk_issues:
        print("  DATA QUALITY FLAGS")
        for issue in junk_issues:
            print(issue)
        print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python id_health.py <path_to_csv>")
        sys.exit(1)
    score_file(sys.argv[1])
