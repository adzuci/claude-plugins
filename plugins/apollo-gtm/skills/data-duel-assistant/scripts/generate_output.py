"""
Output CSV Generator — Data Duel Assistant
Phase 6 post-analysis: Build the customer-ready enriched output CSV from a multi-vendor
AI Sheets export.

Usage:
  python generate_output.py <enriched_csv> <output_path>

Input:  Multi-vendor AI Sheets export (with Apollo/Prospeo/LimaData JSON blob columns)
Output: Clean 5-block CSV ready to share with customer (input as-is + match_source +
        apollo_ + 3p_ + enriched_ consolidated columns)

See references/vendor_schemas.md for field extraction logic per vendor.
"""

import pandas as pd
import json
import sys
from pathlib import Path

JUNK = {'#n/a', 'null', 'unknown', '-', 'n/a', 'none', '', '#ref!', 'nan', 'na', '#value!'}

def safe_json(val):
    if pd.isna(val) or str(val).strip() in ('', '{}', 'null'): return {}
    try: return json.loads(str(val))
    except: return {}

def nv(val):
    if val is None or (isinstance(val, float) and pd.isna(val)): return None
    s = str(val).strip()
    return None if s.lower() in JUNK else s

def coalesce(*vals):
    for v in vals:
        if v is not None and str(v).strip().lower() not in JUNK | {'none'}: return v
    return None

def find_vendor_col(columns, vendor_substring):
    """Find a column name containing the vendor substring (case-insensitive)."""
    for col in columns:
        if vendor_substring.lower() in col.lower():
            return col
    return None

# ── Vendor extractors ─────────────────────────────────────────────────────────

def from_apollo(d):
    if not d or d.get('error'): return {}
    return {
        'matched':          True,
        'linkedin_url':     nv(d.get('linkedin_url')),
        'title':            nv(d.get('title')),
        'seniority':        nv(d.get('seniority')),
        'department':       nv(d.get('department')),
        'city':             nv(d.get('city')),
        'state':            nv(d.get('state')),
        'email':            nv(d.get('email')),
        'phone':            nv((d.get('organization') or {}).get('phone')),
        'current_employer': nv((d.get('organization') or {}).get('name')),
        'job_start_date':   nv(d.get('current_job_start_date')),
        'tenure_months':    nv(d.get('duration_at_current_job_months')),
    }

def from_prospeo(d):
    if not d or d.get('error'): return {}
    p = d.get('person', d)
    e = p.get('email', {})
    email_val    = e.get('email')  if isinstance(e, dict) else e
    email_status = e.get('status') if isinstance(e, dict) else None
    mob = p.get('mobile', {})
    mobile_val = mob.get('number') if isinstance(mob, dict) else mob
    return {
        'matched':      True,
        'email':        nv(email_val) if email_status == 'VERIFIED' else None,
        'email_status': email_status,
        'linkedin_url': nv(p.get('linkedin_url')),
        'mobile':       nv(mobile_val),
    }

def from_limadata(d):
    if not d or d.get('error'): return {}
    p   = d.get('person', d)
    li  = p.get('linkedin', {})
    emp = p.get('employment', {})
    return {
        'matched':      True,
        'linkedin_url': nv(li.get('url') if isinstance(li, dict) else None),
        'headline':     nv(p.get('headline')),
        'title':        nv(emp.get('title') if isinstance(emp, dict) else None),
        'seniority':    nv(emp.get('seniority') if isinstance(emp, dict) else None),
    }

# ── Main ──────────────────────────────────────────────────────────────────────

def generate_output(input_path: str, output_path: str) -> None:
    # Load with encoding fallback
    df = None
    for enc in ['utf-8', 'latin-1', 'cp1252']:
        try:
            df = pd.read_csv(input_path, encoding=enc)
            break
        except Exception:
            continue
    if df is None:
        print(f"ERROR: Could not read {input_path}")
        sys.exit(1)

    # Strip completely empty rows
    df = df[~df.isnull().all(axis=1)].copy().reset_index(drop=True)
    n = len(df)
    print(f"Loaded {n} rows from {Path(input_path).name}")

    # Find vendor columns
    apollo_col   = find_vendor_col(df.columns, 'apollo')
    prospeo_col  = find_vendor_col(df.columns, 'prospeo')
    limadata_col = find_vendor_col(df.columns, 'limadata') or find_vendor_col(df.columns, 'lima')

    vendor_cols = [c for c in [apollo_col, prospeo_col, limadata_col] if c]
    print(f"Vendor columns found: {vendor_cols}")

    # Parse JSON blobs
    apollo_parsed   = df[apollo_col].apply(safe_json)   if apollo_col   else [{}] * n
    prospeo_parsed  = df[prospeo_col].apply(safe_json)  if prospeo_col  else [{}] * n
    limadata_parsed = df[limadata_col].apply(safe_json) if limadata_col else [{}] * n

    # Extract per vendor
    ap_rows = [from_apollo(d)   for d in apollo_parsed]
    pr_rows = [from_prospeo(d)  for d in prospeo_parsed]
    li_rows = [from_limadata(d) for d in limadata_parsed]

    # ── Build output ──────────────────────────────────────────────────────────
    # Block 1: original input columns (drop vendor blob columns)
    input_cols = [c for c in df.columns if c not in vendor_cols]
    out = df[input_cols].copy()

    # Block 2: match_source
    def match_source(i):
        sources = []
        if ap_rows[i].get('matched'): sources.append('Apollo')
        if pr_rows[i].get('matched'): sources.append('Prospeo')
        if li_rows[i].get('matched'): sources.append('LimaData')
        return ', '.join(sources) if sources else 'No Match'

    out['match_source'] = [match_source(i) for i in range(n)]

    # Block 3: Apollo enriched
    out['apollo_linkedin_url']     = [ap.get('linkedin_url')     for ap in ap_rows]
    out['apollo_title']            = [ap.get('title')            for ap in ap_rows]
    out['apollo_seniority']        = [ap.get('seniority')        for ap in ap_rows]
    out['apollo_department']       = [ap.get('department')       for ap in ap_rows]
    out['apollo_city']             = [ap.get('city')             for ap in ap_rows]
    out['apollo_state']            = [ap.get('state')            for ap in ap_rows]
    out['apollo_org_phone']        = [ap.get('phone')            for ap in ap_rows]
    out['apollo_current_employer'] = [ap.get('current_employer') for ap in ap_rows]
    out['apollo_job_start_date']   = [ap.get('job_start_date')   for ap in ap_rows]
    out['apollo_tenure_months']    = [ap.get('tenure_months')    for ap in ap_rows]

    # Block 4: 3P enriched
    out['3p_email']        = [pr.get('email')        for pr in pr_rows]
    out['3p_email_status'] = [pr.get('email_status') for pr in pr_rows]
    out['3p_mobile']       = [pr.get('mobile')       for pr in pr_rows]
    out['3p_linkedin_url'] = [
        coalesce(pr.get('linkedin_url'), li.get('linkedin_url'))
        for pr, li in zip(pr_rows, li_rows)
    ]
    out['3p_headline']     = [li.get('headline')  for li in li_rows]
    out['3p_seniority']    = [li.get('seniority') for li in li_rows]
    out['3p_title']        = [li.get('title')     for li in li_rows]

    # Block 5: Consolidated enriched (Apollo first, 3P fills gaps)
    out['enriched_email']        = [coalesce(ap.get('email'), pr.get('email'))                                   for ap, pr     in zip(ap_rows, pr_rows)]
    out['enriched_phone']        = [coalesce(ap.get('phone'), pr.get('mobile'))                                  for ap, pr     in zip(ap_rows, pr_rows)]
    out['enriched_mobile']       = [pr.get('mobile')                                                             for pr         in pr_rows]
    out['enriched_linkedin_url'] = [coalesce(ap.get('linkedin_url'), pr.get('linkedin_url'), li.get('linkedin_url')) for ap, pr, li in zip(ap_rows, pr_rows, li_rows)]
    out['enriched_title']        = [coalesce(ap.get('title'),     li.get('title'))                               for ap, li     in zip(ap_rows, li_rows)]
    out['enriched_seniority']    = [coalesce(ap.get('seniority'), li.get('seniority'))                           for ap, li     in zip(ap_rows, li_rows)]
    out['enriched_department']   = [ap.get('department')                                                         for ap         in ap_rows]
    out['enriched_headline']     = [li.get('headline')                                                           for li         in li_rows]
    out['enriched_current_employer'] = [ap.get('current_employer')                                               for ap         in ap_rows]
    out['enriched_job_start_date']   = [ap.get('job_start_date')                                                 for ap         in ap_rows]
    out['enriched_tenure_months']    = [ap.get('tenure_months')                                                  for ap         in ap_rows]

    out.to_csv(output_path, index=False)

    # ── Print summary ─────────────────────────────────────────────────────────
    def fill(col):
        return out[col].notna() & out[col].apply(lambda x: str(x).strip().lower() not in JUNK | {'none', 'nan'})

    print(f"\nSaved: {len(out)} rows × {len(out.columns)} cols → {Path(output_path).name}")
    print()
    print("=== MATCH SOURCE BREAKDOWN ===")
    print(out['match_source'].value_counts().to_string())
    print()
    print("=== ENRICHED FIELD FILL RATES ===")
    for col in [c for c in out.columns if c.startswith('enriched_')]:
        n_fill = fill(col).sum()
        print(f"  {col:<30} {n_fill:>4} / {n}  ({n_fill/n*100:.1f}%)")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python generate_output.py <enriched_csv> <output_csv>")
        sys.exit(1)
    generate_output(sys.argv[1], sys.argv[2])
