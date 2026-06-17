# Revenue Recognition Flags (ASC 606 / Topic 606)

Reference for identifying contract clauses that create non-standard revenue recognition
treatment under US GAAP. Consult this file for any contract involving subscription fees,
payment schedules, variable consideration, or multi-element arrangements.

Based on:

- KPMG Revenue for Software and SaaS Handbook (Dec 2025)
- Deloitte Revenue Recognition Roadmap (Nov 2025)
- Apollo Accounting Team SKU Memo (Feb 2025)
- Apollo ASC 606 Revenue Recognition Memo (FY24)

______________________________________________________________________

## Apollo's Defined Performance Obligations (FY24 — Internal)

The Apollo Accounting Team has formally identified the following performance obligations:

| # | Performance Obligation | FY24 % of TCV | Recognition Pattern |
|---|------------------------|---------------|---------------------|
| 1 | Base Platform (subscription access) | 93.6% | Ratably over contract term |
| 2 | Email Credits | 2.7% | As consumed |
| 3 | Mobile Credits | 1.7% | As consumed |
| 4 | Dialer Credits | 1.2% | As consumed |
| 5 | Export Credits | 0.3% | As consumed |
| 6 | Unified Credits (FY25+) | TBD | As consumed |

**Current accounting treatment**: Revenue recognized on total billed amount (bundled
price), ratably over contract term. POs 2–5 are not tracked separately because their
combined share (~6.4%) was deemed immaterial relative to the effort of tracking.

**Critical context**: Deloitte has issued a **material weakness** on Apollo's revenue
recognition control environment. Any contract with unusual structure, non-standard
payment terms, or complex bundling is directly relevant to remediating this weakness
and must be flagged carefully.

______________________________________________________________________

## Step 2 Analysis — How to Assess Performance Obligations

For every contract, identify which of Apollo's defined POs are present and how they
are structured. Use this logic:

### Single-element contracts (Base Platform only)

- Org Plan or similar subscription with credits included per user
- Recognition: ratable over term
- Flag: none unless credits are unusually large relative to subscription

### Multi-element contracts (Base Platform + Add-Ons)

- Any contract adding Inbound, Dialer, Advanced Dialer, or other add-ons
- Each add-on may represent a separate PO (check if distinct)
- Recognition: allocate based on relative SSP; each component recognized per its pattern
- Flag if: add-ons are bundled at a blended price without separate line-item pricing

### Credit-heavy contracts

- Flag if credits represent an unusually large share of TCV vs. the 93.6/6.4% norm
- Large credit allocations may require separate tracking and consumption-based recognition
- This could undermine Apollo's current bundled/ratable approach

### Contracts with Professional Services

- Professional Services = separate PO, recognized over time or at point in time per SOW
- Flag if: PS is bundled into subscription price without separate line item
- Discount allocation may be required if PS appears "free"

______________________________________________________________________

## 1. Variable Consideration

**What to look for**: Clauses making fees contingent on performance, usage, outcomes,
or Customer satisfaction. Common forms: refund rights, credits for service failures,
performance bonuses, tiered pricing, SLA penalties.

**ASC 606 issue**: Variable consideration must be estimated and constrained. Broad
refund or credit rights require recognition deferral until uncertainty resolves.

**🔴 Flag if**:

- Fees subject to Customer's unilateral satisfaction (unconstrained variable
  consideration — revenue deferral likely required)
- Refund rights beyond standard termination-for-breach
- Credits applicable to future periods without expiry

**🟡 Flag if**:

- SLA credits are large relative to TCV (variable consideration constraint analysis needed)
- Pricing tiers based on usage that could result in downward price adjustments

______________________________________________________________________

## 2. Contract Modifications

**What to look for**: Upsells, expansions, renegotiations, or mid-term Order Form changes.

**ASC 606 issue**: Modifications treated as (a) new contract, (b) termination and
replacement, or (c) continuation — depending on whether distinct goods/services are
added at SSP. Incorrect treatment affects revenue timing.

**Apollo context**: Current billing-based recognition increases the risk that
modifications are not properly identified and accounted for under contract terms.

**🔴 Flag if**:

- Upsell reprices existing services at a discount inconsistent with SSP
- Modification retroactively changes fees already invoiced without a credit mechanism

**🟡 Flag if**:

- Upsell bundles new + existing services at a blended rate (SSP analysis needed)
- Term extended without adjusting total consideration pro-rata

______________________________________________________________________

## 3. Multi-Element / Bundled Arrangements

**What to look for**: Order Forms including multiple products (subscription + add-ons + credits + Dialer). Each distinct PO requires separate revenue allocation.

**ASC 606 issue**: Transaction price must be allocated based on relative SSP. Discounts
must be allocated proportionately unless SSP evidence supports concentration.

**Apollo context**: Current approach bundles all POs and recognizes ratably. This works
only while credit POs (2–5) remain immaterial (~6.4% of TCV). Contracts that shift
this balance require closer scrutiny.

**🟡 Flag if**:

- Order Form bundles subscription + add-ons with a single blended price and no
  line-item breakdown (allocation analysis needed)
- Credit volume is disproportionately large vs. the 93.6% base platform norm
- Professional Services included at no extra charge alongside a large subscription

**🔴 Flag if**:

- Contract explicitly prices POs 2–5 separately at amounts materially different
  from Apollo's internal SSP percentages (breaks the bundled recognition argument)

______________________________________________________________________

## 4. Non-Standard Payment Terms

**What to look for**: Deviations from Apollo's standard (Net 30, paid in advance,
annual schedule).

**ASC 606 issue**: Extended terms (Net 60+) can create a significant financing
component requiring transaction price adjustment. Payment contingencies create
variable consideration.

**Apollo context**: The accounting team has flagged that current revenue is recognized
on billing data, not contract terms — creating discrepancies when payment terms deviate.
Non-standard payment terms amplify this existing control weakness.

**🟡 Flag if**:

- Net 60 or Net 90 payment terms (significant financing component analysis if
  contract term > 12 months)
- Payment due only upon Customer acceptance or milestone completion

**🔴 Flag if**:

- Payment contingent on Customer satisfaction with no objective criteria
- Payment schedule extends beyond service period without recognizable progress

______________________________________________________________________

## 5. Right of Return / Refund Rights

**What to look for**: Any clause giving Customer refund, credit, or price reduction
rights beyond Apollo's standard termination-for-cause scenario.

**ASC 606 issue**: Rights of return require deferral until return is improbable.

**🔴 Flag if**:

- Unconditional refund right within any period
- Refund tied to subjective satisfaction criteria
- Credits applicable to future invoices without expiry

______________________________________________________________________

## 6. License vs. Service Classification

**What to look for**: Ambiguity between right to access (service — over time) vs.
right to use (license — point in time).

**ASC 606 issue**: SaaS/platform access recognized over time. If recharacterized as
perpetual license grant at inception, point-in-time recognition is triggered.

**🟡 Flag if**:

- Contract describes Apollo's obligation as delivering a perpetual license at signing
- PGI perpetual license is priced separately and is the primary value driver

______________________________________________________________________

## 7. Fee Waiver / Competitor Buyout Arrangements

**What to look for**: Competitor Buyout Addenda with a Fee Waiver Period.

**ASC 606 issue**: Fee waivers are a form of variable/deferred consideration. Total
transaction price spans the full Initial Term including post-waiver periods. Revenue
recognized over the full term — not just paid periods. An unbilled receivable (112000)
must be recorded during the waiver period; revenue booked to 400006.

**Apollo context**: These contracts are explicitly tracked in the Non-Standard Contracts
Assessment spreadsheet. The accounting team has flagged that current billing-based
recognition does NOT handle fee waiver periods correctly — revenue must be based on
contract terms, not invoices.

**🟡 Flag if**:

- Fee waiver period is > 30% of contract term (assess whether waiver is a material right)
- Contract does not clearly state total committed fees across all tiers
- Waiver period is additive to contract term (inflates total commitment — RED if so)

**🔴 Flag if**:

- Revenue is being recognized only on invoiced amounts during fee waiver period
  (i.e., $0 recognized during waiver) — this is incorrect under ASC 606
- Total TCV is not clearly calculable from the contract (complicates transaction price)

______________________________________________________________________

## 8. Billing vs. Contract Terms Discrepancy (Apollo-Specific)

**What to look for**: Any contract where the billing schedule does not directly mirror
the contractual fee structure — tiered pricing, fee waivers, prorated upsells,
mid-term modifications.

**ASC 606 issue**: Apollo's current revenue recognition is based on billed amounts,
not contract terms. Deloitte has flagged this as a material weakness. Any contract
where billing ≠ contract terms requires manual accounting intervention to ensure
correct recognition.

**🔴 Flag if**:

- Tiered pricing (Year 1 fee ≠ Year 2 fee) — revenue must be straight-lined over
  full term, not recognized at each tier's invoiced amount
- Fee waiver period creates $0 invoice while revenue obligation has already begun
- Mid-term modification changes fees without a corresponding billing adjustment

**🟡 Flag if**:

- Annual payment schedule with multi-year tiered pricing (common in buyout deals)
  — confirm finance team is straight-lining, not recognizing per invoice

______________________________________________________________________

## 9. Audit and Control Flags (Material Weakness Context)

Given Deloitte's active material weakness on Apollo's revenue recognition environment,
the following contract characteristics should always be surfaced in the report even
if they don't meet a RED/YELLOW threshold on their own:

- Any contract where provisioning scope could differ from contracted scope
- Any contract where the deal paper, billing invoice, and system configuration
  may not align (e.g., add-ons purchased in-app not reflected in Order Form)
- Any contract with unusual credit structures that would require consumption-based
  tracking if Apollo's bundled recognition approach is ever challenged
- Any contract where the counterparty has negotiated restrictions on Apollo's
  data use (relevant to Contributor Database growth — a core business asset)
