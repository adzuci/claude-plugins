"""
Results Analysis — Data Duel Assistant
Phase 6: Compute all enrichment metrics and diagnose match failure categories.

Requires Python 3.9+ (uses list[dict] type hints and pandas ≥1.3).

Usage:
  python analyze_results.py <apollo_only_csv> [waterfall_csv]

  If only one file is provided: reports Apollo-only metrics.
  If both files are provided: reports Apollo-only + waterfall comparison.

Output:
  Full Phase 6 metrics table + match failure breakdown.
  Paste directly into the Phase 7 scorecard.
"""

import pandas as pd
import sys
from pathlib import Path

# ── Constants ─────────────────────────────────────────────────────────────────

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

# Identifier columns for failure diagnosis
DOMAIN_COL = "organization_website"
PERSON_LI_COL = "person_linkedin_url"
EMAIL_COL = "email"
MATCH_COL = "apollo_match_status"
APOLLO_EMAIL_COL = "apollo_email"
APOLLO_EMAIL_STATUS_COL = "apollo_email_status"
APOLLO_PHONE_COL = "apollo_phone"
APOLLO_MOBILE_COL = "apollo_mobile_phone"
WATERFALL_EMAIL_COL = "waterfall_email"
WATERFALL_PHONE_COL = "waterfall_phone"
WATERFALL_SOURCE_COL = "waterfall_source"

# Contact-level enrichment depth columns
APOLLO_TITLE_COL = "apollo_title"
APOLLO_SENIORITY_COL = "apollo_seniority"
DEPT_COL = "department"          # input department (customer-provided)
SENIORITY_INPUT_COL = "seniority"  # input seniority

# Account-level firmographic output columns (present in account enrichment duels)
ACCOUNT_REVENUE_COL = "apollo_revenue"
ACCOUNT_EMPLOYEES_COL = "apollo_employee_count"
ACCOUNT_INDUSTRY_COL = "apollo_industry"
ACCOUNT_FUNDING_COL = "apollo_funding"
ACCOUNT_HQ_COL = "apollo_hq_location"

# Segment breakdown columns — script will auto-detect which are present
SEGMENT_COLS = ["country", "industry", "seniority", "department"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def is_junk(value) -> bool:
    if pd.isna(value):
        return True
    s = str(value).strip().lower()
    return s in JUNK_VALUES or len(s) == 0


def has_col(df: pd.DataFrame, col: str) -> bool:
    return col in df.columns


def pct(n: int, total: int) -> str:
    if total == 0:
        return "N/A"
    return f"{n/total*100:.1f}%"


def count_valid(series: pd.Series) -> int:
    return series.apply(lambda v: not is_junk(v)).sum()


def is_generic_email(email: str) -> bool:
    if is_junk(email):
        return False
    domain = str(email).strip().lower().split("@")[-1]
    return domain in GENERIC_EMAIL_DOMAINS


def detect_duel_type(df: pd.DataFrame) -> str:
    """Infer whether this is a contact or account enrichment duel from column presence."""
    contact_signals = [APOLLO_EMAIL_COL, APOLLO_PHONE_COL, APOLLO_MOBILE_COL, PERSON_LI_COL]
    account_signals = [ACCOUNT_REVENUE_COL, ACCOUNT_EMPLOYEES_COL, ACCOUNT_FUNDING_COL]
    contact_hits = sum(1 for c in contact_signals if has_col(df, c))
    account_hits = sum(1 for c in account_signals if has_col(df, c))
    if account_hits > 0 and contact_hits == 0:
        return "account"
    return "contact"  # default; contact enrichment is the common case


def account_firmographic_metrics(df: pd.DataFrame, matched_mask: pd.Series) -> dict:
    """
    Compute fill rates for account-level firmographic fields on matched rows.
    Returns dict of {field_label: (n_filled, n_matched)}.
    Only includes fields actually present in the file.
    """
    field_map = {
        "Revenue": ACCOUNT_REVENUE_COL,
        "Employee count": ACCOUNT_EMPLOYEES_COL,
        "Industry": ACCOUNT_INDUSTRY_COL,
        "Funding": ACCOUNT_FUNDING_COL,
        "HQ location": ACCOUNT_HQ_COL,
    }
    results = {}
    n_matched = matched_mask.sum()
    matched_df = df[matched_mask]
    for label, col in field_map.items():
        if has_col(df, col):
            n_filled = matched_df[col].apply(lambda v: not is_junk(v)).sum()
            results[label] = (n_filled, n_matched)
    return results


def contact_depth_metrics(df: pd.DataFrame, matched_mask: pd.Series) -> dict:
    """
    Compute fill rates for contact-level enrichment depth fields (title, seniority, department)
    on matched rows.
    Returns dict of {field_label: (n_filled, n_matched)}.
    """
    n_matched = matched_mask.sum()
    matched_df = df[matched_mask]
    results = {}
    for label, col in [("Job title (Apollo)", APOLLO_TITLE_COL),
                        ("Seniority (Apollo)", APOLLO_SENIORITY_COL)]:
        if has_col(df, col):
            n_filled = matched_df[col].apply(lambda v: not is_junk(v)).sum()
            results[label] = (n_filled, n_matched)
    # Department: use input column if present (Apollo doesn't always return dept separately)
    if has_col(df, DEPT_COL):
        # Fill rate = rows where input dept exists AND row was matched (Apollo confirmed the contact)
        dept_filled = matched_df[DEPT_COL].apply(lambda v: not is_junk(v)).sum()
        results["Department (input coverage)"] = (dept_filled, n_matched)
    return results


def segment_breakdown(df: pd.DataFrame, matched_mask: pd.Series, top_n: int = 6) -> list[dict]:
    """
    For each auto-detected segment column, compute match rate per segment value.
    Returns a list of dicts: [{col, value, n_total, n_matched, match_pct}, ...]
    Only runs for segment columns that are present and have ≥2 distinct non-junk values.
    Sorted by total rows desc within each column.
    """
    rows = []
    for col in SEGMENT_COLS:
        if not has_col(df, col):
            continue
        clean = df[col].apply(lambda v: None if is_junk(v) else str(v).strip())
        unique_vals = clean.dropna().unique()
        if len(unique_vals) < 2:
            continue  # skip single-value or all-null columns
        for val in unique_vals:
            mask_val = clean == val
            n_total = mask_val.sum()
            n_matched = (mask_val & matched_mask).sum()
            rows.append({
                "col": col,
                "value": val,
                "n_total": int(n_total),
                "n_matched": int(n_matched),
                "match_pct": n_matched / n_total * 100 if n_total > 0 else 0,
            })
    return rows


def has_strong_id(row: pd.Series) -> bool:
    """Row has at least one strong Apollo matching identifier."""
    domain_ok = not is_junk(row.get(DOMAIN_COL, None))
    li_ok = not is_junk(row.get(PERSON_LI_COL, None))
    email_val = row.get(EMAIL_COL, None)
    email_ok = (not is_junk(email_val)) and (not is_generic_email(str(email_val)))
    return domain_ok or li_ok or email_ok


def classify_failure(row: pd.Series) -> str:
    """Categorize why an unmatched row failed to match."""
    if has_strong_id(row):
        # Has identifiers but still didn't match → true coverage gap
        org_name = str(row.get("organization_name", "")).strip()
        # Heuristic: check if org_name looks like junk/very generic
        if is_junk(org_name) or len(org_name) < 3:
            return "Input Noise"
        return "True Coverage Gap"
    else:
        # No strong identifiers → identifier gap
        return "Identifier Gap"


def is_matched(row: pd.Series) -> bool:
    match_val = row.get(MATCH_COL, None)
    if is_junk(match_val):
        return False
    return str(match_val).strip().lower() in {"matched", "yes", "true", "1"}


# ── Analysis ──────────────────────────────────────────────────────────────────

def analyze(df_apollo: pd.DataFrame, df_waterfall: pd.DataFrame | None) -> None:
    total = len(df_apollo)
    has_waterfall = df_waterfall is not None and len(df_waterfall) > 0
    duel_type = detect_duel_type(df_apollo)

    # ── Match rate ────────────────────────────────────────────────────────────
    matched_mask = df_apollo.apply(is_matched, axis=1)
    n_matched = matched_mask.sum()
    n_unmatched = total - n_matched

    # ── Apollo email metrics ───────────────────────────────────────────────────
    if has_col(df_apollo, APOLLO_EMAIL_COL):
        apollo_email_mask = df_apollo[APOLLO_EMAIL_COL].apply(lambda v: not is_junk(v))
        n_apollo_email = apollo_email_mask.sum()
        n_apollo_email_on_matched = (apollo_email_mask & matched_mask).sum()
    else:
        n_apollo_email = 0
        n_apollo_email_on_matched = 0

    if has_col(df_apollo, APOLLO_EMAIL_STATUS_COL):
        verified_mask = df_apollo[APOLLO_EMAIL_STATUS_COL].apply(
            lambda v: str(v).strip().lower() == "verified"
        )
        n_verified = verified_mask.sum()
    else:
        n_verified = None

    # ── Apollo phone metrics ───────────────────────────────────────────────────
    apollo_has_phone = pd.Series([False] * total)
    if has_col(df_apollo, APOLLO_PHONE_COL):
        apollo_has_phone |= df_apollo[APOLLO_PHONE_COL].apply(lambda v: not is_junk(v))
    if has_col(df_apollo, APOLLO_MOBILE_COL):
        apollo_has_phone |= df_apollo[APOLLO_MOBILE_COL].apply(lambda v: not is_junk(v))
    n_apollo_phone = apollo_has_phone.sum()
    n_apollo_phone_on_matched = (apollo_has_phone & matched_mask).sum()

    # ── Account firmographic fill rates (account duels only) ──────────────────
    acct_metrics = account_firmographic_metrics(df_apollo, matched_mask)

    # ── Contact depth fill rates (dept, seniority, title) ────────────────────
    contact_depth = contact_depth_metrics(df_apollo, matched_mask)

    # ── Waterfall metrics (if Version B provided) ──────────────────────────────
    n_wf_email = 0
    n_wf_phone = 0
    wf_email_uplift = 0.0
    wf_phone_uplift = 0.0

    if has_waterfall:
        if has_col(df_waterfall, WATERFALL_EMAIL_COL):
            wf_email_mask = df_waterfall[WATERFALL_EMAIL_COL].apply(lambda v: not is_junk(v))
            n_wf_email = wf_email_mask.sum()
        if has_col(df_waterfall, WATERFALL_PHONE_COL):
            wf_phone_mask = df_waterfall[WATERFALL_PHONE_COL].apply(lambda v: not is_junk(v))
            n_wf_phone = wf_phone_mask.sum()

        wf_source_breakdown = {}
        if has_col(df_waterfall, WATERFALL_SOURCE_COL):
            sources = df_waterfall[WATERFALL_SOURCE_COL].dropna().astype(str)
            sources = sources[sources.str.strip().str.len() > 0]
            wf_source_breakdown = sources.value_counts().to_dict()

        total_email_wf = max(n_apollo_email, n_wf_email)
        total_phone_wf = max(n_apollo_phone, n_wf_phone)
        wf_email_uplift = (total_email_wf - n_apollo_email) / total * 100 if total else 0
        wf_phone_uplift = (total_phone_wf - n_apollo_phone) / total * 100 if total else 0
    else:
        wf_source_breakdown = {}

    # ── Match failure diagnosis ────────────────────────────────────────────────
    unmatched_df = df_apollo[~matched_mask]
    failure_categories = {"Identifier Gap": 0, "True Coverage Gap": 0, "Input Noise": 0}
    for _, row in unmatched_df.iterrows():
        cat = classify_failure(row)
        failure_categories[cat] = failure_categories.get(cat, 0) + 1

    # ── Segment breakdown ─────────────────────────────────────────────────────
    seg_rows = segment_breakdown(df_apollo, matched_mask)

    # ── Print report ──────────────────────────────────────────────────────────
    print("\n" + "=" * 62)
    print("  PHASE 6 — RESULTS ANALYSIS")
    print(f"  Duel type detected: {'Account enrichment' if duel_type == 'account' else 'Contact enrichment'}")
    print("=" * 62)
    print(f"  File:        {Path(sys.argv[1]).name}")
    print(f"  Total rows:  {total}")
    print()

    col_w = has_waterfall

    header = f"  {'Metric':<42} {'Apollo Only':>12}"
    if col_w:
        header += f"  {'+ Waterfall':>12}"
    print(header)
    print(f"  {'-'*42} {'-'*12}" + (f"  {'-'*12}" if col_w else ""))

    def row_line(label, apollo_n, apollo_total, wf_n=None, wf_total=None):
        apollo_val = f"{pct(apollo_n, apollo_total)} ({apollo_n})"
        line = f"  {label:<42} {apollo_val:>12}"
        if col_w and wf_n is not None:
            wf_val = f"{pct(wf_n, wf_total)} ({wf_n})"
            line += f"  {wf_val:>12}"
        print(line)

    row_line("Match rate", n_matched, total,
             n_matched, total)

    if duel_type == "contact":
        row_line("Email coverage (overall)", n_apollo_email, total,
                 n_apollo_email + (n_wf_email if col_w else 0), total)
        if n_matched > 0:
            row_line("Email coverage (matched rows only)", n_apollo_email_on_matched, n_matched)
        row_line("Phone/mobile coverage (overall)", n_apollo_phone, total,
                 n_apollo_phone + (n_wf_phone if col_w else 0), total)
        if n_matched > 0:
            row_line("Phone/mobile (matched rows only)", n_apollo_phone_on_matched, n_matched)
        if n_verified is not None:
            row_line("'Verified' email status", n_verified, total)

    if col_w:
        print()
        print(f"  Waterfall email uplift:  +{wf_email_uplift:.1f}% additional coverage")
        print(f"  Waterfall phone uplift:  +{wf_phone_uplift:.1f}% additional coverage")
        print()
        print("  Note: Match rate is IDENTICAL in Apollo-only and waterfall runs.")
        print("  Waterfall fills data on records already matched — it does not identify new ones.")

        if wf_source_breakdown:
            print()
            print("  Waterfall source breakdown:")
            for source, count in sorted(wf_source_breakdown.items(), key=lambda x: -x[1]):
                print(f"    {source:<20} {count} rows")

    # ── Account firmographic fill rates ───────────────────────────────────────
    if acct_metrics:
        print()
        print(f"  {'─'*58}")
        print(f"  ACCOUNT FIELD FILL RATES  (on {n_matched} matched rows)")
        print(f"  {'─'*58}")
        print(f"  {'Field':<30} {'Fill rate':>12}  {'Count':>8}")
        print(f"  {'-'*30} {'-'*12}  {'-'*8}")
        FILL_THRESHOLD = 80
        for label, (n_filled, n_total) in acct_metrics.items():
            fill_pct_str = pct(n_filled, n_total)
            flag = ""
            if n_total > 0 and (n_filled / n_total * 100) < FILL_THRESHOLD:
                flag = " ⚠ below 80%"
            print(f"  {label:<30} {fill_pct_str:>12}  {n_filled:>5}/{n_total:<5}{flag}")
        print()
        print("  ⚠ fields below 80% fill rate are typical duel objection points.")
        print("  Revenue and Funding are structurally low across all vendors — flag proactively.")

    # ── Contact depth fill rates ───────────────────────────────────────────────
    if contact_depth and duel_type == "contact":
        print()
        print(f"  {'─'*58}")
        print(f"  CONTACT DEPTH FILL RATES  (on {n_matched} matched rows)")
        print(f"  {'─'*58}")
        print(f"  {'Field':<35} {'Fill rate':>12}  {'Count':>8}")
        print(f"  {'-'*35} {'-'*12}  {'-'*8}")
        for label, (n_filled, n_total) in contact_depth.items():
            fill_pct_str = pct(n_filled, n_total)
            flag = " ⚠ below 80%" if n_total > 0 and (n_filled / n_total * 100) < 80 else ""
            print(f"  {label:<35} {fill_pct_str:>12}  {n_filled:>5}/{n_total:<5}{flag}")
        print()
        print("  Department fill rate is a common duel objection — see objections.md.")

    # ── Segment breakdown ──────────────────────────────────────────────────────
    if seg_rows:
        print()
        print(f"  {'─'*58}")
        print("  SEGMENT-LEVEL MATCH RATE BREAKDOWN")
        print(f"  {'─'*58}")
        current_col = None
        for r in sorted(seg_rows, key=lambda x: (x["col"], -x["n_total"])):
            if r["col"] != current_col:
                current_col = r["col"]
                print()
                print(f"  By {current_col.upper()}:")
                print(f"  {'Segment':<28} {'Matched':>8} {'Total':>8} {'Rate':>8}")
                print(f"  {'-'*28} {'-'*8} {'-'*8} {'-'*8}")
            flag = " ⚠" if r["n_total"] > 0 and r["match_pct"] < 60 else ""
            print(f"  {r['value']:<28} {r['n_matched']:>8} {r['n_total']:>8} {r['match_pct']:>7.1f}%{flag}")
        print()
        print("  ⚠ segments below 60% match rate are worth calling out in the scorecard narrative.")
        print("  Isolate strong segments to frame against overall results.")

    # ── Failure diagnosis ──────────────────────────────────────────────────────
    print()
    print(f"  {'─'*58}")
    print(f"  MATCH FAILURE BREAKDOWN  ({n_unmatched} unmatched rows)")
    print(f"  {'─'*58}")

    categories = [
        ("Identifier Gap", "No domain/LinkedIn/work email — not an Apollo coverage issue. User-fixable."),
        ("True Coverage Gap", "Strong identifiers present but no Apollo record found."),
        ("Input Noise", "Malformed names, invalid data, or empty organization fields."),
    ]
    for cat, explanation in categories:
        n_cat = failure_categories.get(cat, 0)
        print(f"  {cat:<22} {n_cat:>4} rows  ({pct(n_cat, n_unmatched)} of unmatched)")
        print(f"    → {explanation}")
        print()

    # ── Narrative guidance ─────────────────────────────────────────────────────
    print(f"  {'─'*58}")
    print("  RECOMMENDED NARRATIVE FRAMING")
    print(f"  {'─'*58}")

    id_gap_pct = failure_categories["Identifier Gap"] / n_unmatched * 100 if n_unmatched > 0 else 0
    coverage_gap_pct = failure_categories["True Coverage Gap"] / n_unmatched * 100 if n_unmatched > 0 else 0

    if id_gap_pct >= 60:
        print("  🟢 Strong framing position:")
        print(f"     {id_gap_pct:.0f}% of match failures are identifier gaps, not Apollo gaps.")
        print("     Lead with identifier health context before showing the match rate.")
    elif coverage_gap_pct >= 60:
        print("  🟡 Honest gap framing required:")
        print("     True coverage gaps dominate. Be specific about which segment/region is weak.")
        print("     Counter with Apollo's strengths in adjacent segments.")
    else:
        print("  🟡 Mixed picture — use segment-specific framing:")
        print("     Isolate the sub-segment where Apollo performs strongest and lead with that.")
        print("     Acknowledge identifier gaps clearly for the weaker portion.")

    if acct_metrics:
        low_fill = [(label, n_f, n_t) for label, (n_f, n_t) in acct_metrics.items()
                    if n_t > 0 and n_f / n_t * 100 < 80]
        if low_fill:
            print()
            print("  🟡 Account fill rate flags to address proactively:")
            for label, n_f, n_t in low_fill:
                print(f"     {label}: {pct(n_f, n_t)} — frame as a known data industry gap,")
                print(f"     not Apollo-specific. Revenue and Funding are low across all vendors.")

    print()
    print("  Proceed to Phase 7 (Scorecard) using these numbers.")
    print("=" * 62 + "\n")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_results.py <apollo_only_csv> [waterfall_csv]")
        sys.exit(1)

    apollo_path = sys.argv[1]
    wf_path = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        df_apollo = pd.read_csv(apollo_path)
    except Exception as e:
        print(f"ERROR: Cannot read Apollo file: {e}")
        sys.exit(1)

    df_wf = None
    if wf_path:
        try:
            df_wf = pd.read_csv(wf_path)
        except Exception as e:
            print(f"WARNING: Cannot read waterfall file: {e}")
            print("Proceeding with Apollo-only analysis.")

    analyze(df_apollo, df_wf)


if __name__ == "__main__":
    main()
