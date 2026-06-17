# Mutual NDA Clause Playbook

Reference for analyzing Mutual Non-Disclosure Agreements against Apollo's standard template.

______________________________________________________________________

## 1. Purpose / Scope

**Standard**: Purpose is evaluating Apollo's products and services. Each party discloses
Confidential Information to the other. Each party acts as an independent Controller of
any Personal Data received — neither is a processor, joint controller, or service
provider for the other.

**🟡 Flag if**:

- Purpose is defined too broadly (e.g., "any business discussions")
- Controller/processor role language for Personal Data is removed

**🔴 Flag if**:

- NDA is one-sided (only protects counterparty's information)
- Apollo is designated as a processor of counterparty's Personal Data

______________________________________________________________________

## 2. Definition of Confidential Information

**Standard**: Non-public information designated as confidential or that reasonably
should be understood as confidential. Includes business plans, product information,
technical data, pricing, and Personal Data. Standard exclusions: (i) publicly
available, (ii) prior knowledge, (iii) lawful third-party disclosure, (iv) independent
development.

**🟡 Flag if**:

- Definition expanded to include information that is publicly available
- Exclusions narrowed (e.g., independent development excluded from carve-outs)

**🔴 Flag if**:

- All exclusions are removed
- Apollo's pricing or product roadmap is explicitly listed as always-confidential
  without reciprocity

______________________________________________________________________

## 3. Confidentiality Obligations

**Standard**: Receiving Party: (i) uses CI solely for the Purpose; (ii) does not
disclose to third parties except employees/contractors/advisors with need-to-know
under equivalent confidentiality; (iii) protects with at least reasonable care.

**🟡 Flag if**:

- "Reasonable care" standard is lowered
- Third-party disclosure carve-out is removed (no sharing with advisors/legal)

**🔴 Flag if**:

- Obligations are one-sided
- Apollo is prohibited from sharing with its legal counsel or affiliates

______________________________________________________________________

## 4. Compelled Disclosure

**Standard**: If legally required to disclose, Receiving Party: (i) discloses only
to the extent required; (ii) provides prompt written notice where legally permitted
so Disclosing Party may seek protective treatment.

**🟡 Flag if**:

- Notice obligation is removed
- "Prompt" is replaced with a specific short window (e.g., 24 hours)

______________________________________________________________________

## 5. Personal Data Processing

**Standard**: Each party complies with Applicable Data Protection Laws. Personal Data
exchanged is limited to business contact information of individuals in professional
capacity (name, business email, job title, employer, business phone). Each party acts
as an independent Controller.

**🟡 Flag if**:

- Applicable Data Protection Laws are defined too narrowly (e.g., GDPR only, no US laws)
- Personal Data scope is broadened beyond business contact information

**🔴 Flag if**:

- Data protection compliance obligations are removed
- Counterparty attempts to designate Apollo as a data processor

______________________________________________________________________

## 6. Term

**Standard**: NDA is effective from Effective Date. Confidentiality obligations survive
for a stated period after termination (typically 2–3 years in Apollo's standard, or
indefinitely for trade secrets).

**🟡 Flag if**:

- Post-termination confidentiality period is shorter than 2 years
- Trade secret carve-out for indefinite protection is absent

**🔴 Flag if**:

- No survival clause — confidentiality ends on termination of NDA
- Term is excessively long (10+ years) in ways that create ongoing obligations

______________________________________________________________________

## 7. Return or Destruction

**Standard**: Upon request, Receiving Party returns or destroys Confidential Information.
Electronic backup retention is acceptable if subject to continuing confidentiality.

**🟡 Flag if**:

- Destruction certification requirement added (creates compliance burden)

**🔴 Flag if**:

- No return/destroy obligation at all

______________________________________________________________________

## 8. Governing Law

**Standard**: California law; San Francisco County courts.

**🟡 Flag if**:

- Different US state proposed

**🔴 Flag if**:

- Non-US governing law proposed
