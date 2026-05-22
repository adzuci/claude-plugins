# Mutual NDA Playbook

Use this playbook when reviewing a Mutual NDA where both parties are disclosing and receiving
confidential information.

**Redline posture: Minimal.** Apollo's goal is to sign NDAs quickly and create as little
friction as possible. Mutual NDAs are largely symmetric agreements — only redline provisions
that are genuinely harmful or where a required protection is completely missing. When in
doubt, do NOT redline.

The two primary concerns in a Mutual NDA are:
1. **Duration** — confidentiality obligations must have a defined end date; perpetual
   obligations are not acceptable.
2. **Data protection** — the NDA must contain language addressing personal data handling.

---

## Auto-RED Triggers — Check These First

Any one of these is an immediate RED. Stop and report without completing the full clause review.

1. **No data protection / personal data clause.** The NDA contains no language addressing
   how personal data about each party's employees, representatives, or contacts will be
   handled. Every Mutual NDA must address this — even a basic acknowledgment that each party
   will handle personal data in accordance with applicable law is sufficient. Absence is a
   hard stop.

2. **Indemnification clause present.** The NDA includes an indemnification obligation
   requiring either party to indemnify the other. NDAs should rely on equitable relief and
   direct damages as remedies — an indemnification clause in an NDA is non-standard and not
   acceptable regardless of how it is scoped or which direction it flows.

---

## Clause Review Matrix

### Confidentiality Period

- **Desired**: 5 years from the effective date. Trade secrets are excluded from the time
  limit and remain confidential for as long as they qualify as trade secrets under applicable
  law.
- **Fallback (acceptable)**: 3 to 5 years with a trade secrets carve-out.
- **Will NOT Accept**: No confidentiality period stated. Perpetual confidentiality obligation.
  Language stating that information "remains confidential until it is no longer confidential"
  or equivalent — this is functionally perpetual and is a hard stop. Any period over 5 years
  should be flagged as YELLOW unless it applies to trade secrets only.

**Redline action if missing or perpetual:** Insert or replace with:
"The obligations of confidentiality under this Agreement will continue for a period of five
(5) years from the Effective Date, except that obligations with respect to Confidential
Information that constitutes a trade secret under applicable law will continue for as long as
such information remains a trade secret."

---

### Definition of Confidential Information

- **Desired**: Broad mutual definition covering information in any form (written, oral,
  electronic) disclosed by either party in connection with the Approved Purpose. Oral
  disclosures confirmed in writing within 14–30 days are acceptable.
- **Fallback (acceptable)**: Definition without a written confirmation requirement for oral
  disclosures is acceptable if the other party's information is otherwise well-protected.
  A definition limited to marked/designated information is YELLOW if it lacks an oral
  confirmation mechanism.
- **Will NOT Accept**: Definition so narrow that obvious categories of confidential
  information are excluded — e.g., covers only written information with no mechanism for
  oral disclosures, or excludes financial information entirely.

---

### Standard of Care

- **Desired**: Each party protects the other's Confidential Information using at least the
  same degree of care it uses for its own confidential information of similar importance,
  but no less than reasonable care.
- **Fallback (acceptable)**: "Reasonable care," "commercially reasonable efforts," "adequate
  security measures," "all security precautions as may be necessary," "same care as own
  confidential information" — all acceptable regardless of exact wording. Do not redline
  for standard of care unless the language is explicitly below reasonable care.
- **Will NOT Accept**: Standard explicitly limited to "any care," or clause that affirmatively
  states no obligation to protect the information.

---

### Exceptions to Confidentiality (Standard Carve-Outs)

- **Desired**: All four standard carve-outs present:
  1. Information that is or becomes publicly known through no fault of the receiving party
  2. Information already known to the receiving party prior to disclosure (without restriction)
  3. Information independently developed by the receiving party without use of the disclosing
     party's Confidential Information
  4. Information rightfully received from a third party without restriction
- **Fallback (acceptable)**: All four carve-outs present, even if worded differently. Minor
  drafting variations are acceptable provided the substance is the same.
- **Will NOT Accept**: One or more of the four standard carve-outs are entirely absent.

---

### Permitted Recipients / Disclosure Restrictions

- **Desired**: Each party may disclose Confidential Information to its employees, contractors,
  agents, and professional advisors who: (a) need to know the information for the Approved
  Purpose, and (b) are bound by confidentiality obligations at least as protective as this
  Agreement (by written agreement or professional obligation).
- **Fallback (acceptable)**: Affiliate sharing for the counterparty only (asymmetric) is
  acceptable if Apollo's core sharing categories (employees, agents, contractors, service
  providers) are present with a binding mechanism. Do not redline asymmetric affiliate rights
  for symmetry.
- **Will NOT Accept**: No binding mechanism for permitted recipients — information can be
  shared with third parties with no confidentiality obligation on those recipients.

---

### Legal Compulsion / Required Disclosure

- **Desired**: A party required by law, regulation, or court order to disclose Confidential
  Information must: (a) provide prompt prior written notice to the disclosing party (to the
  extent permitted by law), (b) cooperate with the disclosing party's efforts to seek
  protective measures, and (c) disclose only the minimum required.
- **Fallback (acceptable)**: Post-disclosure notification rather than advance notice is
  acceptable — the carve-out just needs to exist. Do not redline the timing of notice.
- **Will NOT Accept**: No legal compulsion carve-out at all with no notification obligation
  whatsoever. Or the clause requires the receiving party to resist a court order beyond
  seeking protective measures.

---

### Return or Destruction of Confidential Information

- **Desired**: Upon termination or request by the disclosing party, the receiving party will
  promptly return or destroy all Confidential Information. Written certification of
  destruction upon request is acceptable.
- **Fallback (acceptable)**: Receiving party may elect whether to return or destroy — the
  choice of method is acceptable. Retention exception for "copies required by applicable law
  or for archiving/backup purposes" is acceptable and adequately covers litigation holds.
  Do not redline either of these.
- **Will NOT Accept**: No return or destruction obligation at all. Or all retention exceptions
  are absent.

---

### Data Protection / Personal Data

- **Desired**: Each party acknowledges that personal data of the other party's employees,
  representatives, or contacts may be shared in connection with the Approved Purpose. Each
  party will process such personal data as an independent data controller in accordance with
  applicable data protection law (including GDPR where applicable).
- **Fallback (acceptable)**: Language stating each party will handle personal data "in
  accordance with applicable data protection law" without specifying controller/processor
  status — acceptable provided no language creates a processor relationship.
  For agreements governed by Australian law or other non-GDPR jurisdictions using
  processor-style obligations ("act on instructions from the Owner"): do NOT auto-replace with
  GDPR controller-controller language. Flag as YELLOW for manual review.
- **Will NOT Accept**: No data protection language at all. This is an Auto-RED trigger.

**Privacy Law / Applicable Law definitions**: If the NDA defines "Privacy Law," "Data
Protection Law," or "Applicable Law" and restricts it to a single geographic jurisdiction or
to "legislation" only (excluding regulations), flag as YELLOW and redline:
- Replace geographic restriction with "any jurisdiction"
- Expand "legislation" to "legislation, regulation or other applicable law"

---

### Governing Law and Jurisdiction

- **Desired**: California, Delaware, or New York (courts of the chosen state).
- **Fallback (acceptable)**: Any US state except Louisiana. England and Wales. Switzerland.
- **Will NOT Accept**: Louisiana. Any international jurisdiction other than England and Wales
  or Switzerland — this includes Australian law, German law, Singapore law, French law, and
  all others not listed above. Flag as RED and redline to California.

**Redline action if governing law is unacceptable:** Replace with:
"This Agreement will be governed by and construed in accordance with the laws of the State
of California, without regard to its conflict of law provisions."

---

### Equitable Relief

- **Desired**: Either party may seek equitable relief (injunction, specific performance) in
  any court of competent jurisdiction without posting bond and without such action being
  construed as a waiver of other rights or remedies.
- **Fallback (acceptable)**: Standard equitable relief acknowledgment without the no-bond
  provision is acceptable.
- **Will NOT Accept**: Equitable relief is waived or limited. Or the clause requires the
  aggrieved party to exhaust arbitration before pursuing injunctive relief — this creates
  dangerous delay in the event of a breach.

---

### Residuals Clause

- **Desired**: Absent entirely.
- **Fallback**: None — a residuals clause always undermines confidentiality regardless of
  how it is scoped.
- **Will NOT Accept**: Any residuals clause permitting use of Confidential Information
  retained in unaided memory. Delete entirely if present.

**Redline action if present:** Delete the clause using `<w:del>`.

---

### Non-Solicitation / No-Hire

- **Desired**: Absent from the NDA entirely. Non-solicitation provisions belong in a
  separate commercial agreement, not an NDA.
- **Fallback (acceptable)**: Present if both of the following are true:
  - The restriction period is **under 12 months**, AND
  - Explicit carve-outs exist for general recruitment activities: public job postings,
    general solicitations not targeted at specific individuals, and headhunters not directed
    toward named individuals.
- **Will NOT Accept**: Period of 12 months or longer. Or no carve-outs for general
  recruitment activities.

**Redline action if period is 12+ months:** Redline period to 11 months.
**Redline action if no recruitment carve-outs:** Insert:
"Notwithstanding the foregoing, this Section does not restrict either party from: (i)
conducting generalized searches for employees through public advertisements or job postings
not specifically targeting the other party's personnel; or (ii) hiring any person who
responds to a general solicitation not directed at specific individuals."

---

### Indemnification

- **Desired**: Absent entirely. NDAs rely on equitable relief and direct damages.
- **Will NOT Accept**: Any indemnification clause regardless of scope or direction.
  This is an Auto-RED trigger.

---

### Limitation of Liability / Consequential Damages

- **Desired**: Either absent (standard for NDAs) or mutual exclusion of indirect/
  consequential damages where both parties are equally constrained.
- **Fallback (acceptable)**: Mutual exclusion of consequential damages is acceptable.
  Do not redline.
- **Will NOT Accept**: One-sided exclusion that caps only the counterparty's liability or
  that excludes only Apollo's liability for breach of confidentiality — leaves Apollo
  exposed while protecting the counterparty. Flag as YELLOW.

---

## GREEN / YELLOW / RED Assessment Rules

### 🔴 RED — Any one of these fires:
- No data protection / personal data clause (entirely absent)
- Indemnification clause present (any form, any direction)
- Governing law is Louisiana or any international jurisdiction other than England and Wales
  or Switzerland
- Confidentiality period is perpetual, unstated, or uses "until no longer confidential"
  language
- Non-solicitation period is 12 months or longer
- Non-solicitation present with no carve-outs for general recruitment activities
- Residuals clause present (redline: delete entirely)
- No legal compulsion carve-out and no notification obligation of any kind
- One or more of the four standard carve-outs to confidentiality obligations entirely absent

### 🟡 YELLOW — No RED triggers, but one or more of:
- Confidentiality period over 5 years (other than for trade secrets only — flag the overall
  period)
- Definition of Confidential Information limited to marked/written disclosures only with no
  oral confirmation mechanism
- Data protection clause uses processor-style language in an Australian-law or non-GDPR
  agreement (flag for manual review — do not auto-redline)
- Privacy Law / Applicable Law definition restricted to single jurisdiction or "legislation"
  only (flag and redline per the Privacy Law procedure above)
- One-sided consequential damages exclusion asymmetric against Apollo (flag the specific
  direction)
- Non-solicitation present with period under 12 months and proper carve-outs (flag for
  awareness; acceptable but worth noting)
- Equitable relief clause requires arbitration before injunctive relief

### 🟢 GREEN — All of the following are true:
- Confidentiality period stated and 5 years or under (with trade secrets carve-out acceptable)
- All four standard carve-outs to confidentiality obligations present
- Standard of care at reasonable care level or equivalent
- Permitted recipients restricted with a binding mechanism for third-party recipients
- Legal compulsion carve-out present (timing of notice does not affect this)
- Return or destruction obligation present with acceptable retention exceptions
- Data protection clause present addressing applicable law compliance
- Governing law is acceptable (US except Louisiana; England and Wales; Switzerland)
- No indemnification clause
- No residuals clause
- Non-solicitation absent, OR present with period under 12 months and general recruitment
  carve-outs
