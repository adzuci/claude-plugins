# Apollo Sales Process — 7 Stages

7 structured stages (0-6) with clear entry/exit criteria and SFDC gating. Creates a non-negotiable shared language across the sales org.

From the FY27 AOP: "Methodology defines how we sell. Process defines where we are. MEDDPICC defines how de-risked the deal is."

---

## Process Building Blocks

Every stage has three components:

| Component | Definition |
|---|---|
| **Stage** | A specific phase representing where a deal is in its progression. Each has a distinct objective — what must be true for this deal to move forward. |
| **Seller Activities** | Actions, behaviors, and tools sellers use during a stage. Guide execution but do not alone gate advancement. |
| **Exit Criteria** | Required milestones that must be documented in SFDC before advancement. Objective and enforceable. Stage progression = real deal validation, not activity completion. |

---

## Exit Criteria Severity Tiering

| Severity | Rule | Constraint |
|---|---|---|
| **Always Required** | Required on all deals. Gating in SFDC. | Hard blocker |
| **$25K+ Required** | Required on deals >= $25K ARR. | Conditional hard blocker (deal-size-dependent) |
| **Expected** | Expected within ROE standards. Not hard-gated. | Soft limit |

**Critical rule:** $25K+ deals require full MEDDPICC documentation in SFDC. No exceptions.

---

## Stage 0: Lead

**Owner:** BDR
**Objective:** Schedule AE discovery meeting within 48 hours of handoff, with a decision-relevant stakeholder at Director level or above.

**Key Activities:**
- Persona-aligned outreach
- Connect with contact on LinkedIn
- Ensure pre-call email is sent
- Conduct pre-call research
- Schedule AE discovery meeting within 48hrs with Director+ stakeholder

**Exit Criteria (SFDC — BDR inputs):**
- Authority: Initial Meeting Contact (decision-relevant stakeholder)
- Need: BDR → AE Handoff Notes
- Timeline: Initial Meeting Date (within 48 hours) or Email with Intent to Upsell

**SFDC Required Fields:** Handoff Notes, Initial Meeting Contact, Initial Meeting Date

---

## Stage 1: Discovery

**Owner:** AE
**Objective:** Diagnose the customer's current state, uncover pain tied to business impact, validate their capabilities, size the opportunity, and establish the structural foundation for a disciplined deal.

First substantive conversation with the customer. Begin building qualification, establish a Mutual Action Plan, put pieces in place (pricing education, deal room, stakeholder mapping) to run a focused deal from day one.

**MEDDPICC Focus:** M (Metrics), I (Identified Pain)

**Key Activities:**
- Diagnose current state + consequences (CoTM)
- Understand tech stack and technical requirements
- Identify stakeholders
- Educate on pricing and packaging
- Establish MAP
- Launch internal Slack deal room (>$10K SMB / >$20K MM)

**Exit Criteria (SFDC):**
- Identified Pain (tied to business impact)
- Metrics (quantified business impact)
- Submit Capabilities ($10K+ deals)
- Opportunity Size: ARR / Seats / Contract Term
- Next Step, Next Step Date

**SFDC Required Fields:** Identified Pain, Metrics, Capabilities ($10K ARR), ARR, Num Seats, Next Step, Next Step Date, Contract Term

**Key Resources:** Discovery Guide + MEDDPICC Cheat Sheet, MAP template, Apollo Technical Requirements, Persona 1-Pagers, SFDC Capabilities Guide, Apollo Credits Overview

---

## Stage 2: Qualification

**Owner:** AE
**Objective:** Confirm the deal is real — begin testing your champion, identify the Economic Buyer, define decision criteria, understand competitive landscape, and align on a formal evaluation plan.

If Stage 1 is about uncovering pain, Stage 2 is about confirming you have the right people, the right problem, and a real path to a decision. This is where deals that aren't real get disqualified — and real deals get the structure they need to close.

**MEDDPICC Focus:** E (Economic Buyer), D (Decision Criteria), C (Competition)

**Key Activities:**
- Align on evaluation plan + success criteria
- Validate decision criteria + competition
- Confirm budget access
- Identify Champion
- Identify Economic Buyer
- Introduce SC and schedule internal review meeting

**Exit Criteria (SFDC):**
- Economic Buyer (aware of evaluation / agreed with budget commit)
- Decision Criteria (defined for $25K+ deals)
- Competitor Details

**SFDC Required Fields:** Economic Buyer, Decision Criteria ($25K+), Competitor Details

**Key Resources:** Champion Guide, SC Engagement Guidelines, Competitors DB, Compete Takeout Slides

---

## Stage 3: Solution Evaluation

**Owner:** AE + SC
**Objective:** Establish Apollo as the preferred solution through real proof — demo, trial, data duel, or pilot — and secure the technical win.

Goal: leave this stage as Apollo's confirmed Vendor of Choice with a clear path to paper. Technical fit must be confirmed here — not assumed.

**MEDDPICC Focus:** D (Decision Process), C (Champion)

**Key Activities:**
- Determine evaluation process: demo, trial, data duel, pilot
- Validate technical requirements
- Intro Apollo to procurement
- Start legal and security review
- Engage Apollo Exec
- Realign on MAP
- Confirm Apollo as Vendor of Choice

**Exit Criteria (SFDC):**
- Decision Process (mapped for $25K+ deals)
- Champion Y/N (validated + tested)
- Technical Win
- ZP Team ID

**SFDC Required Fields:** Champion Y/N, Champion Name ($25K+), Decision Process ($25K+), Technical Win, ZP Team ID

**Key Resources:** Technical Evaluation Playbook, Trial Playbook, Apollo Exec Engagement Playbook

---

## Stage 4: Pricing and Negotiation

**Owner:** AE
**Objective:** Present and confirm commercial terms, finalize legal and security, and align on rollout strategy and post-sales support.

Translate the value established in Stages 1-3 into a commercial agreement — while making sure the customer feels set up to succeed from day one, not just sold.

**MEDDPICC Focus:** P (Paper Process)

**Key Activities:**
- Present and confirm pricing + packaging
- Finalize legal, security, and commercials
- Align on rollout strategy and resources
- Explain Support Model and GTME (>$15K)
- Maintain MAP

**Exit Criteria (SFDC):**
- Paper Process (documented for $25K+ deals)
- Capabilities (validated for deployment)
- Contract Details (incl. dates, terms, contacts, products sold)

**SFDC Required Fields:** Paper Process ($25K+), Products Sold, Num Seats, Capabilities → Validated, Start Date, End Date, Renewal Date, Payment Method, Payment Terms, Payment Schedule

**Key Resources:** Apollo Contract Process Guidance, Ironclad Guide, Pricing Playbook

---

## Stage 5: Out for Signature

**Owner:** AE
**Objective:** Execute contract and prepare for a seamless transition to onboarding.

Contract is out. Confirm signature timeline, make sure approvers are lined up, get onboarding scheduled before the ink is dry. Deals that go dark at this stage usually signal the paper process wasn't mapped in Stage 3.

**Key Activities:**
- Confirm signature timeline + approvers
- Send contract
- Schedule onboarding meeting with customer
- Process contract + provision licenses

**Exit Criteria (SFDC):**
- AE → Onboarding Prepare Handoff ($10K+ deals)
- Licenses must be provisioned to move to Closed Won (gate to next stage)

**Key Resources:** Provisioning Guide, AE → Onboarding Handoff Process, Closed Won Checklist

---

## Stage 6: Closed

**Owner:** AE → AM/GTME handoff
**Objective:** Execute a structured handoff and ensure all documentation is complete — whether won or lost.

**Key Activities:**
- Onboarding meeting held
- Conduct AE → GTME / AM handoff

**Exit Criteria (Closed Lost only):**
- Loss Detail

**SFDC Required Fields (Closed Lost):** Loss Reason, Loss Reason Detail, Loss Reason Description, Lost to Competitor

---

## Dealroom Specifications

| Parameter | Requirement |
|---|---|
| **Threshold (SMB)** | > $10K ARR |
| **Threshold (MM)** | > $20K ARR |
| **Platform** | Internal Slack channel |
| **Timing** | Launch at Stage 1 |

---

## SC Engagement Model

SC engagement begins at Stage 2 (Qualification) when AE introduces SC and schedules internal review meeting.

| Stage | SC Role |
|---|---|
| Stage 0 (Lead) | Not engaged. BDR-owned. |
| Stage 1 (Discovery) | Not yet engaged unless flagged as complex or strategic. AE owns discovery. |
| Stage 2 (Qualification) | SC introduced. Internal review meeting scheduled. SC begins technical assessment. |
| Stage 3 (Solution Eval) | SC leads evaluation execution: demo, trial, data duel, pilot. Owns technical win. |
| Stage 4 (Pricing/Negotiation) | SC supports objection handling, technical due diligence, security review responses. |
| Stage 5 (Out for Signature) | SC supports as needed for technical questions during contracting. |
| Stage 6 (Closed) | Post-sale handoff responsibilities. |

SC Role Evolution: "Transforming SCs from product experts into strategic deal advisors who can guide sales process decisions, come 'over the top' of reps when needed for deal success."

---

## Mutual Action Plan (MAP)

| Deal Size | MAP Requirement |
|---|---|
| $25K+ | Formal MAP required (Google Sheets template) |
| SMB (all) | Simplified MAP template |
| < $25K | MAP expected but format flexible |

MAP is established at Stage 1 and maintained through close.

---

## Key Resources by Stage

| Stage | Key Resources |
|---|---|
| 0 — Lead | Outbound Hub, BDR → AE Handoff Guide, Pre-Call Checklist |
| 1 — Discovery | Discovery Guide + MEDDPICC Cheat Sheet, MAP template, Apollo Technical Requirements, Persona 1-Pagers, SFDC Capabilities Guide, Apollo Credits Overview |
| 2 — Qualification | Champion Guide, SC Engagement Guidelines, Competitors DB, Compete Takeout Slides |
| 3 — Solution Eval | Technical Evaluation Playbook, Trial Playbook, Apollo Exec Engagement Playbook |
| 4 — Pricing/Negotiation | Apollo Contract Process Guidance, Ironclad Guide, Pricing Playbook |
| 5 — Out for Signature | Provisioning Guide, AE → Onboarding Handoff Process, Closed Won Checklist |
| 6 — Closed | Reference Stage 5 handoff resources |

---

*Source: Apollo Sales Process Hub (Notion, Apr 2026), FY27 AOP.*
