# Category 1 — SaaS with Personal Data (Not Product-Related)

Use this playbook when the contract is a software subscription or platform that will access,
process, or store personal data (employee PII, prospect/lead data, customer billing/support/
account data) but does NOT integrate with Apollo's customer-facing product.

**Redline posture: Minimal.** The DPA is the primary battlefield. Beyond that, redline only
genuinely harmful provisions — data ownership grabs and clearly unacceptable liability
structures. Do not redline standard SaaS terms just because they're vendor-friendly.

---

## Auto-RED Triggers — Check These First

Before scanning any other clauses, check for both of the following. Either one is an
immediate RED — stop and report without completing the full clause review.

1. **No DPA and personal data will be processed.** The vendor will access, process, or store
   personal data and there is no DPA executed, attached, or a firm written commitment to
   execute one before go-live. Look for: data processing terms, privacy addendum, GDPR/CCPA
   provisions, DPA reference. Absence of any of these = RED.

2. **Vendor claims ownership of Apollo's data.** Any clause that gives the vendor ownership
   of, or a broad license to, data Apollo inputs, uploads, or generates through the platform.
   A license to use aggregated/anonymized data for product improvement is acceptable; a claim
   of ownership or broad license over identifiable Apollo data is not.

---

## Clause Review Matrix

### Data Processing Agreement (DPA)
- **Desired**: DPA executed and attached, incorporated by reference (including via a URL to
  vendor's trust/compliance page), or a written commitment to execute one before go-live.
  Vendor processes only the personal data necessary to provide the contracted service. Data
  used solely for service delivery; no secondary use. Deletion/return of personal data within
  30 days of termination.
- **Fallback (acceptable)**: DPA not yet attached but vendor has signed a written commitment
  (in the contract or order form) to execute Apollo's standard DPA or a mutually agreed DPA
  before any personal data is shared. Do not flag as YELLOW — do not rate RED if the
  commitment is in writing.
- **URL-incorporated DPA**: A DPA incorporated by reference at a vendor URL (e.g., "the DPA
  at vendor.com/legal/dpa") is **acceptable and GREEN**. This is standard practice for major
  SaaS vendors. Do not flag.
- **Will NOT Accept**: Vendor will process personal data with no DPA in place and no written
  commitment to execute one. This is the Auto-RED trigger.

### Data Ownership
- **Desired**: Apollo explicitly retains ownership of all personal data it inputs, uploads,
  or that is generated through Apollo's use of the platform. Vendor has no rights to the data
  beyond performing the contracted service.
- **Fallback (acceptable)**: Vendor may use aggregated, anonymized usage data for product
  improvement, benchmarking, or internal analytics, provided Apollo's data is not identifiable
  and no ownership claim is made.
- **Will NOT Accept**: Vendor claims ownership of, or a broad license to, Apollo's data,
  configurations, inputs, or outputs. This is the Auto-RED trigger.

### Indemnification
- **Desired**: Mutual indemnification. Vendor indemnifies Apollo for claims arising from
  vendor's data breach, security failure, or violation of the DPA. Apollo indemnifies vendor
  for Apollo's misuse of the platform.
- **Fallback (acceptable)**: Vendor provides indemnification for its own security failures
  and DPA violations. Apollo's indemnification obligation is limited to Apollo's own acts.
- **Will NOT Accept**: Vendor provides zero indemnification to Apollo — contract is entirely
  silent on vendor's obligations to Apollo, or vendor expressly disclaims all liability to
  Apollo entirely. Flag as RED.

### Liability Cap
- **Desired**: Mutual cap at 12 months of fees paid. Carveouts for: data breach / DPA
  violation, confidentiality breach, and gross negligence — these are uncapped.
- **Fallback (acceptable)**: Cap between 6–12 months of fees. Carveouts for data breach and
  confidentiality breach are the minimum acceptable — other carveouts can be absent.
- **Will NOT Accept**: Apollo's liability is uncapped. Or the cap is materially asymmetric
  (vendor's liability capped significantly lower than Apollo's). Or the cap is below 3 months
  of fees on a contract over $50k. Flag as RED.

### Term, Auto-Renewal, and Termination
- **Desired**: Annual term. Auto-renewal with at least 60-day cancellation notice. Apollo can
  terminate for convenience on 30-day notice. Data deleted/returned within 30 days of
  termination.
- **Fallback (acceptable)**: Auto-renewal with 30-day notice window. Termination for
  convenience right exists even if notice period is up to 60 days. Data return/deletion up
  to 60 days post-termination.
- **Will NOT Accept**: No termination for convenience right. Auto-renewal with under 30-day
  notice window. Vendor retains Apollo data indefinitely after termination.

### Price Increases
- **Desired**: Pricing locked for the initial term. Renewal increases capped at CPI or ≤5%.
- **Fallback (acceptable)**: Renewal increase cap up to 10%, or at least 60 days advance
  notice before renewal pricing takes effect.
- **Will NOT Accept**: Vendor can increase pricing at will with no cap and no advance notice.
  Flag as YELLOW (not RED) unless the contract value is material.

---

## GREEN / YELLOW / RED Assessment Rules

### 🔴 RED — Any one of these fires:
- Vendor will process personal data and no DPA exists and no written commitment to execute
  one before go-live
- Vendor claims ownership of or a broad license over Apollo's data
- Vendor provides zero indemnification to Apollo (completely absent or expressly disclaimed)
- Apollo's liability is uncapped, or cap is materially asymmetric

### 🟡 YELLOW — No RED triggers, but one or more of:
- DPA is absent but vendor has given a written commitment to execute one (flag the commitment
  and remind that DPA must be executed before data is shared)
- Data deletion window after termination exceeds 60 days
- Auto-renewal notice window under 30 days (flag the specific window)
- No termination for convenience right
- Liability cap below 6 months of fees
- Price increase provision with no cap and no advance notice (for material contracts)
- Vendor's data use rights go beyond service delivery in an ambiguous way (flag exact language)

### 🟢 GREEN — All of the following are true:
- DPA executed/attached or a written commitment to execute before go-live exists
- Apollo retains ownership of its data; vendor's rights limited to service delivery or
  clearly scoped aggregated/anonymized use
- Mutual or balanced indemnification; vendor indemnifies for data breach and DPA violation
- Liability cap at 6+ months with carveouts for data breach and confidentiality
- Termination for convenience right exists
- Auto-renewal with at least 30-day cancellation notice