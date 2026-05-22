# Category 4 — Data Providers

Use this playbook when the contract is with a vendor whose primary service is providing data
to Apollo (contact records, company data, intent data, enrichment data, or similar datasets).

**Redline posture: Targeted.** The concern is not the standard SaaS structure of the contract
— it's the data itself. Apollo's two core risks with data providers are:

1. **Legal compliance** — The vendor collected the data in violation of GDPR, CCPA, or other
   applicable data protection laws. If Apollo uses that data, Apollo shares in the liability.

2. **Platform ToS violations** — The vendor collected data by scraping platforms (LinkedIn,
   websites, social networks) in violation of those platforms' terms of service. Apollo could
   face downstream legal exposure, injunctions, or loss of access to its own accounts.

Redline hard on warranties and indemnification. Accept standard SaaS structure otherwise.

---

## Auto-RED Triggers — Check These First

Any one of these is an immediate RED. Stop and report.

1. **No warranty that data was lawfully collected.** The vendor makes no representation
   that its data was collected with proper legal basis (consent, legitimate interest, or
   similar) under applicable law. A vendor that won't warrant the lawfulness of its own data
   collection is a serious red flag.

2. **No indemnification for data compliance failures.** The vendor provides no indemnification
   to Apollo for third-party claims, regulatory actions, or enforcement arising from the
   vendor's own data collection or compliance failures. This indemnification is non-negotiable
   for data providers — Apollo is taking on downstream risk from the vendor's practices, and
   must have contractual recourse if that risk materializes.

3. **No warranty that data was not collected in violation of third-party platform ToS.** The
   vendor makes no representation that its data was collected without violating platform terms
   of service (LinkedIn, websites, social networks). This carries the same weight as the
   lawful-collection warranty — stop and report without completing the full clause review.

---

## Clause Review Matrix

### Lawful Collection Warranty
- **Desired**: Vendor explicitly warrants that all data provided to Apollo was collected with
  proper legal basis under applicable data protection laws, including GDPR (consent, legitimate
  interest, or other valid basis), CCPA/CPRA (compliant with opt-out and disclosure
  requirements), and any other applicable jurisdiction's requirements. Vendor maintains records
  demonstrating compliance with applicable legal bases.
- **Fallback (acceptable)**: Vendor warrants compliance with "applicable data protection laws"
  without enumerating specific jurisdictions, provided the language is affirmative (not just
  a disclaimer). A warranty that vendor will "maintain compliance" throughout the term is also
  acceptable.
- **Will NOT Accept**: No warranty about the lawfulness of data collection. Or a warranty so
  heavily qualified that it is functionally meaningless (e.g., "to vendor's knowledge, as of
  the date of this agreement..."). This is an Auto-RED trigger.

**Redline action if missing:** Insert:
"Vendor represents and warrants that all data provided to Apollo under this Agreement has been
collected with appropriate legal basis under applicable data protection laws, including the
General Data Protection Regulation and the California Consumer Privacy Act, as amended."

### No ToS-Violating Collection Warranty
- **Desired**: Vendor explicitly warrants that none of the data provided was collected through
  means that violate any third-party platform's terms of service, including but not limited to
  automated scraping, account credential abuse, or any other method prohibited by platform
  terms. Vendor will promptly notify Apollo if it becomes aware of any claim that its data
  collection violates any platform ToS.
- **Fallback (acceptable)**: Vendor warrants compliance with "applicable third-party terms" or
  that its data collection "does not violate any applicable platform restrictions." Specific
  enumeration of platforms (LinkedIn, etc.) is preferred but not required.
- **Will NOT Accept**: No warranty about ToS compliance. Or vendor affirmatively states that
  some portion of its data is collected through means a third-party platform disputes. Flag
  immediately — this is a hard stop.

**Redline action if missing:** Insert:
"Vendor represents and warrants that no data provided to Apollo has been collected in violation
of any third party's terms of service, including any restriction on automated data collection,
scraping, or harvesting."

### Right to Provide Warranty
- **Desired**: Vendor explicitly warrants that it has the legal right to provide the data to
  Apollo and that doing so does not violate any third-party rights, license, or obligation.
  This covers situations where vendor may have acquired data from a third party under
  restrictions that prevent resale or sublicensing.
- **Fallback (acceptable)**: General representation that vendor has "all necessary rights and
  licenses" to provide the data to Apollo for Apollo's stated purpose.
- **Will NOT Accept**: No representation about vendor's right to provide the data. Or contract
  language suggesting vendor is re-licensing data it obtained under restrictions that may not
  permit the arrangement. Flag for legal review.

**Redline action if missing:** Insert:
"Vendor represents and warrants that it has the full right, power, and authority to provide
the data to Apollo and that Apollo's use of the data in the manner contemplated by this
Agreement does not and will not infringe any third-party rights."

### Indemnification for Data Compliance Failures
- **Desired**: Vendor indemnifies, defends, and holds harmless Apollo against any and all
  third-party claims, regulatory actions, enforcement proceedings, fines, penalties, and
  related costs arising from: (a) vendor's violation of applicable data protection laws in
  collecting the data; (b) vendor's violation of any third-party platform's terms of service
  in collecting the data; (c) vendor's breach of any warranty in this Agreement. This
  indemnification should be uncapped or at a high cap.
- **Fallback (acceptable)**: Vendor indemnification covering (a)–(c) above, even if subject
  to a reasonable cap (e.g., 2x or 3x annual fees). Flag if indemnification is capped at a
  low amount that would be inadequate to cover a regulatory fine.
- **Will NOT Accept**: No indemnification for data compliance failures whatsoever. Or an
  indemnification provision that expressly excludes regulatory proceedings, fines, or
  governmental actions. This is an Auto-RED trigger.

**Redline action if missing:** Insert:
"Vendor will defend, indemnify, and hold harmless Apollo and its affiliates, officers, and
employees from and against any claims, losses, damages, fines, penalties, and expenses
(including reasonable attorneys' fees) arising out of or related to: (i) Vendor's breach of
any representation, warranty, or obligation in this Agreement; (ii) Vendor's violation of
any applicable data protection law in connection with the collection of data provided to
Apollo; or (iii) any claim that the data provided to Apollo was collected in violation of any
third party's terms of service or other rights."

### Ongoing Compliance Obligation
- **Desired**: Vendor must maintain its data compliance practices throughout the full term of
  the agreement — not just at the time of signing. If vendor's data collection practices
  change materially, or if vendor receives a regulatory inquiry or enforcement action related
  to its data collection, vendor must notify Apollo promptly.
- **Fallback (acceptable)**: General obligation to "maintain compliance with applicable laws"
  throughout the term. Notification on regulatory inquiry is preferred but absence is YELLOW,
  not RED.
- **Will NOT Accept**: Warranties limited to the date of signing only, with no ongoing
  obligation. This creates a loophole where vendor's practices could change after signing.

### Liability Cap
- **Desired**: Mutual cap at 12 months of fees paid. Vendor's indemnification obligations for
  data compliance failures are uncapped or subject to a significantly higher cap.
- **Fallback (acceptable)**: 12-month standard cap. Indemnification carveout that is at least
  2–3x annual fees (even if not fully uncapped).
- **Will NOT Accept**: Vendor's liability for indemnification is subject to the same low
  standard cap (e.g., 1 month of fees) as everything else. The whole point of the
  indemnification is that regulatory fines and third-party litigation can vastly exceed fees
  paid.

### Data Accuracy (Not a Hard Requirement)
- **Note**: Data accuracy warranties are useful but not required. Do not redline their absence.
  If a data accuracy warranty is present but so heavily qualified as to be meaningless, flag
  as YELLOW. If absent entirely, note in the Slack summary but do not treat as a finding.

---

## GREEN / YELLOW / RED Assessment Rules

### 🔴 RED — Any one of these fires:
- No warranty that data was lawfully collected under applicable data protection law
- No warranty that data was not collected in violation of third-party platform ToS
- No indemnification for vendor's data compliance failures (absent or expressly excluded)
- Vendor's indemnification for regulatory proceedings/fines is expressly excluded

### 🟡 YELLOW — No RED, but one or more of:
- Right-to-provide warranty is absent or weakly stated (flag for insertion)
- Indemnification is present but capped at a very low amount (flag the cap amount)
- Vendor warrants compliance only as of signing date with no ongoing obligation (flag)
- No notification obligation if vendor receives regulatory inquiry about its data practices
- Vendor's data collection practices rely on a legal basis Apollo is not comfortable with
  (e.g., "legitimate interest" with no further explanation — flag for legal review)

### 🟢 GREEN — All of the following are true:
- Lawful collection warranty present and substantive
- No ToS-violating collection warranty present and substantive
- Right-to-provide warranty present
- Vendor indemnifies Apollo for data compliance failures, including regulatory actions
- Ongoing compliance obligation exists (or warranties are not limited to signing date)