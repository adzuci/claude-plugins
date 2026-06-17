# MDSA Clause Playbook

Reference for analyzing Master Data Services Agreements against Apollo's standard template.

______________________________________________________________________

## 1. License Grant to Customer

**Standard**: Non-exclusive, non-transferable, non-sublicensable license to access and
use Services for internal business purposes only. Covers: viewing Contributor Database,
B2B communications, sales/marketing/recruiting activities.

**Acceptable variants**: Broader use language is acceptable if still limited to B2B
internal purposes. Minor rewording is fine.

**🔴 Flag if**:

- Customer receives transferable or sublicensable rights (without a Reseller Addendum)
- License extends to Customer's customers or third parties
- No limitation to internal business purposes

______________________________________________________________________

## 2. Perpetual License to PGI

**Standard**: Customer gets a perpetual, worldwide, transferable, royalty-free license
to use PGI for internal business purposes. PGI may be combined with Customer Data.
Customer has no rights to underlying data sources, methodologies, or Apollo IP.

**🔴 Flag if**:

- Customer claims ownership of PGI
- Customer gets rights to Apollo's underlying database or IP
- No acknowledgment that PGI rights don't include source data

______________________________________________________________________

## 3. Apollo's License to Customer Data

**Standard**: Apollo gets a term license to host/process Customer Data to provide
Services and grow/enrich/verify the Contributor Database. Apollo also gets an
irrevocable perpetual license to use Customer Data with AI to improve the Platform
(without identifying Customer).

**🟡 Flag if**:

- The perpetual/irrevocable AI training license is removed or limited
- Apollo is prohibited from using Customer Data to improve the Contributor Database

**🔴 Flag if**:

- Apollo is prohibited from all use of Customer Data beyond narrow service delivery

______________________________________________________________________

## 4. IP Ownership

**Standard**: Apollo owns all rights to the Platform and PGI. Customer owns Customer Data.
Customer's feedback incorporated into the Platform is assigned to Apollo.

**🔴 Flag if**:

- Customer claims joint ownership of the Platform or PGI
- Feedback/suggestions assignment to Apollo is removed
- Apollo's ownership of the Contributor Database is contested

______________________________________________________________________

## 5. Usage Restrictions

**Standard**: Customer may not: use Services/data to build a competing product, resell/
sublicense data, access the Platform on behalf of third parties, incorporate Platform
into Customer's own products, use for FCRA purposes, use for illegal purposes.

**🔴 Flag if**:

- Any of the above restrictions are removed
- Competitive use restriction is limited to only a subset of Apollo's offerings
- Third-party access carve-outs are inserted without Apollo approval

______________________________________________________________________

## 6. Fees and Payment Terms

**Standard**:

- Fees stated in Order Form; non-cancelable and non-refundable during Term
- Paid in advance; auto-renews unless 30-day written notice
- Payment due within 30 days of invoice in USD
- Late payments: 1.5%/month interest
- Taxes: Customer's responsibility (except taxes on Apollo's net income)
- Credits/seats do not roll over; no decreases during Term

**🟡 Flag if**:

- Payment terms extended beyond 30 days (e.g., Net 60, Net 90)
- Refund rights added beyond the standard termination-for-cause scenario
- Auto-renewal notice period shortened below 30 days

**🔴 Flag if**:

- Fees made cancelable during the Term
- Credits made rollable or refundable
- Annual price increase cap added (limits Apollo's renewal pricing rights)

______________________________________________________________________

## 7. Term and Termination

**Standard**:

- Agreement is non-cancelable; remains in effect until expiration or cause-termination
- 30-day cure period for material breach
- Termination by Apollo for uncured breach: remaining fees immediately due
- Termination by Customer for Apollo's uncured breach: pro-rata refund of prepaid fees
- Insolvency/bankruptcy triggers immediate termination right

**🟡 Flag if**:

- Cure period extended beyond 30 days
- Termination for convenience added

**🔴 Flag if**:

- Apollo's right to collect remaining fees upon Customer-caused termination is removed
- Customer gets unilateral termination right without cause

______________________________________________________________________

## 8. Indemnification

**Standard**: Mutual indemnification for: gross negligence/willful misconduct, law
violations, confidentiality breaches (non-data breach), IP infringement. Apollo's
indemnification excludes: modifications by non-Apollo parties, non-current versions,
combinations with non-Apollo programs.

**🟡 Flag if**:

- Indemnification scope is broadened to include ordinary negligence
- Exclusions from Apollo's IP indemnity are removed

**🔴 Flag if**:

- Indemnification is one-sided (Customer only, or Apollo only without reciprocity)
- Apollo's IP infringement indemnity is expanded to cover Customer's modifications

______________________________________________________________________

## 9. Limitation of Liability

**Standard**:

- No indirect/consequential damages for either party
- Direct damages cap: 12 months of fees paid
- Data breach/Security Incident cap: greater of $100,000 or 5x total fees paid
- Exceptions to caps: indemnification obligations, gross negligence/willful misconduct/
  fraud, confidentiality breaches (non-data breach), law violations

**🟡 Flag if**:

- Data breach cap is reduced below $100,000 or 5x fees
- Additional exceptions to the cap are added

**🔴 Flag if**:

- Direct damages cap is removed entirely
- Apollo's liability for data breaches is uncapped
- Consequential damages exclusion is removed

______________________________________________________________________

## 10. Confidentiality

**Standard**: Mutual; protect with at least commercial reasonableness; use only for
Agreement purposes; standard carve-outs (public domain, prior knowledge, independent
development, third-party disclosure). Return or destroy on request. Prior NDAs superseded.

**🟡 Flag if**:

- Standard exclusions (prior knowledge, independent development) are removed
- Confidentiality term is limited (standard is coterminous with Agreement + survival)

**🔴 Flag if**:

- Confidentiality is one-sided
- Apollo's Confidential Information protections are materially weakened

______________________________________________________________________

## 11. Data Processing Addendum (DPA)

**Standard**: Apollo DPA attached as Appendix A. DPA governs data protection obligations.
DPA takes precedence over Agreement in case of conflict. Covers: processor/controller
roles, subprocessor notification (30 days), security incident notification (72 hours),
data deletion within 90 days of termination, audit rights (once/year), SCCs for EU/UK/Swiss
data transfers.

**🔴 Flag if**:

- DPA is absent entirely
- Security incident notification window is extended beyond 72 hours
- Data deletion period is extended beyond 90 days
- Customer's right to object to new subprocessors is removed
- SCCs for international transfers are removed for EU/UK customers

______________________________________________________________________

## 12. Governing Law and Dispute Resolution

**Standard**: California law; courts in San Francisco County, California.

**🟡 Flag if**:

- Different US state law is proposed
- Arbitration clause is added

**🔴 Flag if**:

- Non-US governing law proposed (e.g., UK, EU, specific foreign jurisdiction)
- Mandatory arbitration with unfavorable terms (class action waiver, etc.)

______________________________________________________________________

## 13. Assignment

**Standard**: Either party may assign to an acquirer of substantially all stock/assets.
All other assignments prohibited. Competitor-acquisition triggers 30-day termination right.

**🟡 Flag if**:

- Assignment to affiliates is added without restriction

**🔴 Flag if**:

- Competitor-acquisition termination right is removed
- Assignment rights are broadened without Apollo consent requirement

______________________________________________________________________

## 14. Order of Precedence

**Standard**: (1) DPA, (2) Order Form, (3) Other Addenda, (4) Agreement, (5) Linked policies.

**🟡 Flag if**:

- Order Form is elevated above the DPA
- Customer's own terms are inserted into precedence hierarchy
