# Category 3 — SaaS Vendor Integrating with Apollo's Product

Use this playbook when the contract is for a vendor whose software integrates with Apollo's
customer-facing product, APIs, or customer data infrastructure.

**Redline posture: Full scrutiny.** This is Apollo's highest-risk vendor category. These
vendors touch Apollo's product and Apollo's customers. If something goes wrong — a breach, a
compliance failure, a system outage — it lands on Apollo's customers and on Apollo's
reputation. Redline missing provisions actively. The three concerns driving this scrutiny are:

1. **Security** — The vendor must maintain rigorous security standards and Apollo must have
   contractual rights to verify them and to respond quickly if something goes wrong.
2. **Compliance** — The vendor will be a subprocessor handling Apollo customer data. Data
   protection compliance is not optional.
3. **Ability to collect** — If the vendor causes harm to Apollo or Apollo's customers, Apollo
   must be positioned to collect. Uncapped or low-capped liability for data breach and
   security incidents is non-negotiable.

---

## Auto-RED Triggers — Check These First

Any one of these is an immediate RED. Stop and report without completing the full clause review.

1. **No DPA for customer data processing.** The vendor will access Apollo customer data and
   there is no DPA executed or attached. There is no acceptable fallback for Cat 3 — the DPA
   must exist before any integration goes live.

2. **No security incident notification obligation.** The contract contains no requirement for
   the vendor to notify Apollo of security incidents or data breaches affecting Apollo's data.
   Apollo cannot manage customer impact or regulatory obligations without timely notice.

3. **Vendor can use Apollo customer data for its own purposes.** Any language permitting the
   vendor to use data flowing through the integration for model training, product improvement,
   benchmarking, analytics, or any purpose other than providing the contracted service to
   Apollo. This is a fundamental conflict of interest and a potential customer trust issue.

---

## Clause Review Matrix

### Data Processing Agreement (DPA)
- **Desired**: DPA executed and attached. Vendor identified as Apollo's subprocessor. Vendor
  processes Apollo customer data only as instructed by Apollo, only to provide the contracted
  service, and for no other purpose. Apollo customer data may not be used for vendor's own
  benefit. Deletion/return within 30 days of termination.
- **Fallback**: None for Cat 3. DPA must exist before the integration goes live. This is an
  Auto-RED trigger.
- **Will NOT Accept**: No DPA. Or DPA that permits vendor to use Apollo customer data for
  vendor's own purposes (training, analytics, benchmarking, product improvement).

### Security Standards
- **Desired**: Vendor must maintain SOC 2 Type II certification and provide a current SOC 2
  Type II report to Apollo upon request (at minimum annually). Vendor must maintain
  industry-standard security practices (encryption in transit and at rest, access controls,
  vulnerability management) throughout the full term of the agreement — not just at signing.
- **Fallback (acceptable)**: Vendor certifies to SOC 2 Type II equivalent or commits to
  achieving it within a defined timeframe (not more than 6 months). "Industry-standard
  security practices" language without specific certification is YELLOW, not RED, if the
  vendor is a known/reputable provider.
- **Will NOT Accept**: No security representations at all. Vendor expressly disclaims any
  security obligations. Or vendor explicitly refuses to provide a SOC 2 report on request.

**Redline action if missing:** Insert:
"Vendor will maintain SOC 2 Type II certification throughout the Term and will provide Apollo
with a copy of its then-current SOC 2 Type II report upon Apollo's written request, no more
than once per calendar year."

### Security Incident Notification
- **Desired**: Vendor must notify Apollo of any actual or suspected security incident, breach,
  or unauthorized access affecting Apollo's data within 24 hours of discovery. Notification
  must include: nature of the incident, data affected, steps being taken.
- **Fallback (acceptable)**: Notification window between 24 and 72 hours is acceptable.
  Apollo will accept anything in that range. Notice must include reasonable detail about the
  nature and scope of the incident.
- **Will NOT Accept**: No notification obligation at all (Auto-RED trigger). Notification
  window longer than 72 hours. Notification requirement triggered only by "confirmed" breaches
  (as opposed to suspected or potential ones).

**Redline action if missing or over 72 hours:** Insert or replace:
"Vendor will notify Apollo within 48 hours of discovering any actual or suspected unauthorized
access to, or use, disclosure, modification, or destruction of, Apollo's Confidential
Information or Customer Data."

### Data Processing Restrictions
- **Desired**: Explicit restriction limiting vendor's use of Apollo's data (including all
  customer data flowing through the integration) exclusively to providing the contracted
  service. Vendor may not: train machine learning or AI models on Apollo data, use Apollo data
  for vendor's own product development, sell or license Apollo data, or use Apollo data for
  benchmarking or competitive intelligence.
- **Fallback (acceptable)**: "Purpose limitation" language that restricts vendor to processing
  only as necessary to provide the service, even if it doesn't enumerate prohibited uses,
  provided there is no language affirmatively permitting secondary use.
- **Will NOT Accept**: Any language affirmatively permitting vendor to use Apollo data for its
  own purposes. This is an Auto-RED trigger.

**Redline action if missing:** Insert:
"Vendor will process Apollo's Confidential Information and Customer Data solely to perform its
obligations under this Agreement and for no other purpose. Vendor will not use Apollo's data
to train or improve any machine learning or AI model, develop Vendor's own products or
services, or share or sell such data to any third party."

### SOC 2 Report on Request
- **Desired**: Explicit right for Apollo to request and receive Vendor's current SOC 2 Type II
  report at any time, at least once per calendar year, at no additional charge.
- **Fallback (acceptable)**: Right to request security attestation documentation (may include
  SOC 2 or equivalent). Even a commitment to "reasonably cooperate with Apollo's security
  diligence requests" is acceptable if paired with a certification provision.
- **Will NOT Accept**: No right whatsoever to review or request security documentation.

**Redline action if missing:** Insert:
"Upon Apollo's written request, Vendor will provide Apollo with a copy of Vendor's then-current
SOC 2 Type II report, or equivalent third-party security attestation, no more than once per
calendar year."

### Security Standards Maintenance (Ongoing)
- **Desired**: Vendor must maintain its stated security standards throughout the full term of
  the agreement — not just at execution. If vendor loses certification or has a material
  downgrade in its security posture, vendor must notify Apollo promptly.
- **Fallback (acceptable)**: General obligation to maintain industry-standard security
  practices throughout the term.
- **Will NOT Accept**: Security representations are limited to the date of signing only.

### Indemnification
- **Desired**: Mutual indemnification. Vendor specifically indemnifies Apollo for: (a) security
  incidents caused by vendor's failure to maintain its security obligations; (b) data breaches
  affecting Apollo customer data caused by vendor; (c) vendor's violation of the DPA or
  applicable data protection law; (d) third-party IP infringement by vendor's software.
  Apollo indemnifies vendor for Apollo's misuse of the platform.
- **Fallback (acceptable)**: Vendor indemnification for (a)–(d) above; Apollo's
  indemnification limited to Apollo's own acts. Vendor's indemnification does not need to be
  broader than these four categories.
- **Will NOT Accept**: Vendor provides zero indemnification to Apollo. Or vendor indemnification
  is limited to IP claims only (excluding security incidents and data breach). Or vendor
  indemnifies Apollo for security incidents only up to the liability cap (see Liability section
  — carveout is required).

### Liability Cap
- **Desired**: Mutual cap at 12 months of fees paid. The following are UNCAPPED:
  - Violations of the DPA or data protection law
  - Confidentiality breaches
  - Vendor's indemnification obligations
  The cap structure reflects that these are the scenarios where Apollo's actual damage — and
  its customers' damage — can far exceed fees paid.
- **Fallback (acceptable)**: 12-month cap standard. Uncapped carveouts for DPA violations and
  confidentiality breaches are required. Indemnification carveout can be at a higher cap
  (e.g., 2–3x fees) rather than fully uncapped, but a full uncapped carveout is preferred.
- **Will NOT Accept**: Apollo's liability is uncapped. Or cap is below 12 months on any
  material contract. Or DPA violations and confidentiality breaches are subject to the
  standard cap with no carveout. Or vendor's liability for security incidents or data breaches
  is capped at a nominal amount.

**Redline action:** If DPA/confidentiality carveouts are absent, insert:
"Notwithstanding the foregoing, the liability cap set forth in this Section will not apply to:
(i) either party's breach of its confidentiality obligations; (ii) Vendor's violation of its
data protection or DPA obligations; or (iii) Vendor's indemnification obligations."

### Termination for Security / Compliance Cause
- **Desired**: Apollo may terminate immediately (or on 15-day notice) if vendor: (a) suffers a
  material security incident affecting Apollo data; (b) materially violates the DPA; (c) loses
  its SOC 2 certification without a replacement. Standard termination for convenience on 30
  days notice also required.
- **Fallback (acceptable)**: Standard termination for cause with a 30-day cure period for
  material breach. Termination for convenience on 30–60 days notice.
- **Will NOT Accept**: No termination right for Apollo at all. Or cure period over 60 days for
  material breach. Or no termination for convenience right.

### Data Return on Termination
- **Desired**: Vendor returns or destroys all Apollo data (including customer data) within 30
  days of termination. Vendor provides written confirmation of deletion upon request.
- **Fallback (acceptable)**: Return/deletion window up to 60 days. Written certification of
  deletion is acceptable (does not have to be proactive — can be upon request).
- **Will NOT Accept**: No return/deletion obligation. Vendor retains Apollo customer data
  beyond 60 days post-termination without a legitimate legal basis.

---

## GREEN / YELLOW / RED Assessment Rules

### 🔴 RED — Any one of these fires:
- No DPA for customer data processing (hard stop — must exist)
- No security incident notification obligation in the contract
- Vendor can use Apollo customer data for its own purposes (training, analytics, etc.)
- Vendor provides zero indemnification to Apollo
- Liability cap has no carveout for DPA violations or confidentiality breaches
- Apollo's liability is uncapped

### 🟡 YELLOW — No RED, but one or more of:
- Security incident notification window over 48 hours but under 72 (flag the window)
- SOC 2 report access not explicitly addressed (flag for insertion)
- Security standards limited to signing date only, with no ongoing obligation (flag)
- Data deletion window over 60 days post-termination
- Termination for cause cure period over 30 days
- No termination for convenience right
- Indemnification carveout for security incidents is capped rather than fully uncapped

### 🟢 GREEN — All of the following are true:
- DPA executed/attached; customer data restricted to service delivery only
- Security incident notification within 24–72 hours
- Vendor maintains SOC 2 or equivalent; Apollo has right to request report annually
- Data processing restrictions: no secondary use of Apollo customer data
- Mutual indemnification covering data breach, DPA violation, and IP infringement
- Liability cap at 12 months with carveouts for DPA violations and confidentiality breaches
- Termination for convenience right exists
- Data return/deletion within 60 days of termination