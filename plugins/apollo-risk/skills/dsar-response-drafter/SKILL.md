---
name: dsar-response-drafter
description: >-
  Draft legally sound responses to data subject requests (DSRs) and scan Apollo's Privacy queue
  in Intercom for open access requests, legal basis inquiries, and combined requests. Handles
  GDPR, CCPA/CPRA, and other privacy frameworks. Classifies requests, checks escalation triggers,
  and produces ready-to-review drafts grounded in Apollo's DSR Playbook.

  Trigger on: "draft a DSR response", "data subject request", "data subject access request",
  "DSAR", "privacy deletion request", "right to erasure", "GDPR request", "CCPA request",
  "someone's asking for their data under GDPR/CCPA", "check the Privacy queue", "scan the
  Privacy inbox", "what DSRs are open", "what's open in the Privacy queue", or a similar
  privacy-rights request or Privacy-queue review. Do NOT trigger on generic, non-privacy
  phrasing such as a plain "access request" (tool/system access) or "deletion request"
  (deleting a record/file) — those are not data-subject requests.
---

# /dsar-response-drafter

This skill has two modes. Read the user's message and choose the right one:

- **Queue Scan** — the user wants to check what's open in the Privacy inbox (e.g. "check the queue", "any access requests?", "what's open?"). Follow the Queue Scan section below.
- **Draft Response** — the user wants to respond to a specific DSR conversation (e.g. gives an ID, URL, or description of a ticket). Skip to Step 1.

______________________________________________________________________

## Queue Scan Mode

Use this mode when someone on the Legal Risk team asks what's currently open in the Privacy queue, wants to see pending access requests, or hasn't specified a particular conversation to act on.

### How to scan the queue

Use `search_conversations` with:

- **team_assignee_id: 6717368** (Apollo's Privacy inbox)
- **state: "open"** and **open: true** (both filters together to ensure only truly open conversations are returned — this excludes resolved tickets that may still show as open at the conversation level)
- **admin_assignee_id** — do not set this parameter, so that only unassigned conversations are returned. If the connector returns assigned conversations anyway, filter them out post-fetch by discarding any where `admin_assignee_id` is set to a non-zero/non-null value.
- **per_page: 50**

Only surface tickets where `ticket_state` is `"submitted"` or `"in_progress"` (not `"resolved"`). Discard any conversation where a ticket object exists with `ticket_state: "resolved"`.

For each conversation returned:

1. **Read the first customer message** (or most recent if it's a follow-up thread). You don't need to read every message — just enough to classify the request type.
1. **Classify it** using the categories below.
1. **Skip pure deletion-only requests** — don't include these in the output. They're handled separately and don't need surfacing here.
1. **Note the conversation timestamp** — calculate how many days have passed since the request arrived using today's date (which you already know from context). This drives the urgency flag.

**Classification categories to include:**

| Type | What it looks like |
|---|---|
| **Access / Right to Know** | "Send me my data", "What do you have on me?", "Can I see my information?", "I want a copy of my data" |
| **Legal Basis Inquiry** | "Why do you have my data?", "Where did you get this?", "What's your legal basis?", "I didn't give you permission" |
| **Combined (Access + Legal Basis)** | Message invokes both: wants their data AND questions the legal basis |
| **Combined (Access + Deletion)** | Primarily wants access, but also mentions deletion |
| **Unclear / Needs Review** | Can't classify confidently from the message alone — flag for manual review |

Deletion-only requests → **skip** (don't include in queue summary).

### Queue summary output format

Present results as a numbered table, sorted by urgency (most urgent first). After the table, offer to draft a response for any item.

```
## Privacy Queue — Unassigned Open Requests (excluding deletion-only)
Scanned [N] open unassigned conversations · [DATE] · Showing [M] non-deletion requests

| # | Requester | Type | Days open | Regulation | ⚠️ Urgency | Conversation ID |
|---|---|---|---|---|---|---|
| 1 | Jane Smith (jane@example.com) | Access | 27 days | GDPR | 🔴 URGENT — 3 days to deadline | 123456 |
| 2 | Carlos Ruiz (c.ruiz@corp.com) | Legal Basis Inquiry | 14 days | GDPR | 🟡 Monitor | 789012 |
| 3 | [Unknown] | Combined (Access + Legal Basis) | 5 days | Unknown (defaulting to GDPR) | 🟢 OK | 345678 |
```

**Urgency flags:**

- 🔴 **URGENT** — deadline within 5 days (GDPR: 30-day clock; CCPA: 45-day clock)
- 🟡 **Monitor** — more than 5 days remain but past the halfway point of the deadline window
- 🟢 **OK** — comfortably within deadline
- ⚪ **Unknown** — can't determine date from conversation; flag for manual review

After the table, add a short **Escalation Flags** section for any ticket that shows an obvious escalation trigger (e.g., mentions litigation, is from a law firm, references a minor). Just flag them — don't draft a full escalation note.

Then ask: **"Would you like me to draft a response for any of these? Just say the number."**

When a ticket is selected, use its conversation ID and proceed to Step 1 below with that conversation.

______________________________________________________________________

## Draft Response Mode

Draft a legally compliant, Apollo-playbook-grounded response to a data subject request (DSR) received via Intercom.

**Supported request types:**

- **Access / Right to Know** — "Send me my data" (GDPR Article 15; CCPA Right to Know)
- **Deletion / Right to Erasure / Opt-Out** — "Delete my data" (GDPR Article 17; CCPA Right to Delete)
- **Legal Basis Inquiry** — "Why do you have my data?" / "What's your legal basis?" / "Where did you get this?"
- **Combined** — requests that invoke multiple rights in a single message

**Supported regulations:** GDPR (EU/EEA/UK and aligned jurisdictions), CCPA/CPRA (California + other US states), and best-practice responses for other jurisdictions.

______________________________________________________________________

## Step 1: Identify the Conversation

If the user provides a conversation ID or URL, use `get_conversation` to retrieve it directly.

If they describe a request without a specific ID (e.g., "I just got a deletion request from someone named Maria"), use `search_conversations` or `search` (DSL query by contact email or name) to find the right thread.

Pull the full conversation to capture:

- The requester's message(s) in their own words
- Any prior back-and-forth (especially any prior opt-out or deletion confirmation — this changes the tone significantly)
- Timestamps — needed for calculating hard response deadlines

Use `fetch` to retrieve contact details by ID or URL, particularly:

- **Location/country** — determines the applicable regulation
- **Email address** — for identity matching
- Any company/account information

**Check the automation note:** Intercom's automation should have added an internal note with a copy of the requester's data from the GDPR Claim Management Tool. Review this note for:

- What data Apollo holds about the individual
- Whether data is linked via email, LinkedIn URL, phone number, or alternate email
- If the automation note is missing (can happen when the ticket was redirected from Gmail and shows as "Individual's name via Privacy"), note this for follow-up

If Intercom is unavailable or the conversation can't be found, ask the user to paste the request text and share the requester's email address so you can still draft a response.

______________________________________________________________________

## Step 2: Classify the Request

Read the requester's message and determine the request type. People rarely use legal terminology — look for the underlying intent:

| What they say | Request type |
|---|---|
| "Send me everything you have on me", "I want a copy of my data", "What data do you hold about me?", "Can I see my information?" | **Access / Right to Know** |
| "Delete my data", "Remove me from your database", "I want to be forgotten", "Opt me out", "Please remove my profile" | **Deletion / Right to Erasure** |
| "Why do you have my data?", "Where did you get this?", "What's your legal basis?", "I didn't give you permission", "Who gave you my information?" | **Legal Basis Inquiry** |
| Any message combining the above | **Combined** — note each component |

**Detect authorized agents:** If the requester appears to be acting on someone else's behalf, or if the domain/sender suggests a privacy service, flag it. Known authorized agents include: **Optery, GoInvisible.io, PrivacyBee, Incogni, Deleteme, Freeze, GoHush**. Authorized agent requests should be acknowledged as such and handled using the appropriate "Authorized Agent" macro language.

**Post-deletion follow-ups:** If a prior deletion confirmation exists but the individual is following up with access questions (e.g., "How did you obtain my data?", "Who did you share my data with?", "What data did you have about me?"), classify as **Access questions after opt-out**. This is handled differently — use the "Individual // Data source after deletion" or "Individual // Specific questions after deletion" macro approach.

**Company / business profile requests:** If the request is for deletion of a *company* profile (not an individual's personal data), note this — Apollo is not required to honor deletion of company/business data. The obligation applies only to personal data of natural persons.

______________________________________________________________________

## Step 3: Determine the Applicable Regulation

Use the requester's **location** (from contact record or their message) to determine the correct framework. Only two deadlines below are stated as authoritative — GDPR and CCPA. For every other jurisdiction, the deadline must be confirmed against local law; do not assert a specific number you haven't verified.

**GDPR — EU/EEA, UK, and EEA-adjacent (authoritative: 1 month / ~30-day response deadline):**

- EU/EEA member states
- United Kingdom
- Switzerland, Norway, Liechtenstein

**CCPA/CPRA — California (authoritative: 45-day response deadline):**

- California, USA

**Other US state laws (apply best practice, CCPA-aligned):**

- Maryland, Oregon, Virginia, Colorado, Connecticut, and other US states with comprehensive privacy laws
- Respond as if CCPA, noting the applicable state law if known

**Other jurisdictions with their own privacy law (Australia, Argentina, Brazil, Canada, India, Mexico, Singapore, Philippines, South Africa, and others):**

- These are **not** GDPR. Each has its own statute, legal bases, and response deadline — and several are **shorter** than GDPR's (e.g. Brazil's LGPD expects a complete access response in ~15 days; Mexico's ARCO rights run on business days). Do **not** assume "GDPR, 30 days."
- **Confirm the local statutory deadline with counsel.** Until confirmed, default to the **stricter** of (a) the local requirement, if known, or (b) 30 days — and **flag the jurisdiction in the draft header as "deadline to verify."**
- Frame the legal basis and citations generically (Apollo's lawful basis for processing publicly-sourced B2B professional data) rather than citing GDPR article numbers to a non-GDPR subject.

**Location unknown:** Default to GDPR-level response (highest standard of protection, ~30 days) and note the assumption in the draft header.

______________________________________________________________________

## Step 4: Check Escalation Triggers

Before drafting, run through this checklist. If **any trigger applies, stop and alert the user** — do not draft a final send-ready response. Mark it "DRAFT — FOR COUNSEL REVIEW ONLY" if a draft would be helpful, and clearly indicate why escalation is needed.

**Escalate to Legal (legal@apollo.io) if:**

- The requester is a **current or former Apollo employee** (HR/employment law implications)
- The request **mentions litigation, a lawsuit, or a regulatory investigation** against Apollo
- The message is from a **government agency, data protection authority (DPA), or regulator** — not an individual consumer
- The requester involves a **minor** (anyone under 18)
- The request seeks **financial compensation** for alleged privacy violations
- The request is from a **law firm** acting on behalf of a client, especially if it appears to be a mass campaign
- **Special category data** is referenced (health/medical, biometric, political/religious views, sexual orientation, etc.)
- The request involves a **litigation hold** that may apply to the data in question

**Escalate to Privacy Counsel queue (#privacy-gdpr) if:**

- The individual explicitly **threatens to file a regulator complaint** against Apollo
- The individual is **pushing back aggressively** on a prior deletion confirmation (data still visible, re-ingestion concerns)

**Escalate to #acp-dc-legal-wg if:**

- **50+ emails from the same company domain** are sending similar requests in a coordinated fashion

**Legal escalation procedure:**
When escalating to Legal, note the following for the user to action (do not auto-send):

- In Intercom: switch the response box to **Note**, apply the "Email to Legal" macro
- Fill in: Individual's request/inquiry, Steps taken so far, Existing customer (Y/N), ARR + Tier if yes, Reason for Transfer, Lead approval (link to conversation)
- Send email to **legal@apollo.io** with subject: `REQUEST || PRIVACY TEAM TO LEGAL_{General_Context}`
- Apply the **Legal Escalations** tag in Intercom
- If the ticket is resolved and no response received within **48 hours**, re-open the ticket and reach out to @Briana Jimenez

**When escalation is NOT triggered:**
Include a clear "Escalation check: Clear — no triggers detected" line in the output header.

______________________________________________________________________

## Step 5: Draft the Response Email

Produce a complete, ready-to-review email draft. Tailor the language to the regulation, request type, and tone (a frustrated individual warrants more empathy than a routine B2B inquiry). Use plain English — the requester should not need a law degree to understand the response.

### Apollo-specific context

Apollo is a **B2B sales intelligence platform**. Its primary legal basis for processing contact data under GDPR is **legitimate interests** (Article 6(1)(f)) — Apollo collects and surfaces professionally relevant contact information (name, job title, employer, business email, phone number) to help B2B sales teams identify and reach relevant contacts. Under CCPA/CPRA, Apollo operates as a **data broker** and must honor deletion and opt-out requests.

**Where Apollo's data comes from:**

- **Name, job title, employer, location:** Gathered from publicly available sources such as Google Search, company websites, professional networks, and public business records
- **Business email address and phone number:** Sourced from Apollo's **Customer Contributory Network** — data contributed by users of the Apollo platform who have connected their email/calendar accounts — as well as licensed data providers
- Apollo does **not** collect or process sensitive personal data (health, financial, biometric, etc.)

**Do NOT** redirect the requester to Apollo's Privacy Center (privacy@apollo.io / apollo.io/privacy-center) — the auto-responder has already done this. The response should be substantive, not another redirect.

**Recipient disclosure — GDPR vs. CCPA (this distinction matters legally):**

- **GDPR subjects (EU/EEA/UK and aligned jurisdictions):** Under GDPR Article 15(1)(c), data subjects have the right to know the recipients or categories of recipients to whom their personal data has been disclosed. For GDPR requests, **include the customer recipient list from the Access Analysis** — list the customer names and/or domains that accessed the individual's profile. This is a legal obligation, not optional.
- **CCPA/non-GDPR subjects:** Do **not** share the Access Analysis customer list. CCPA does not carry the same recipient disclosure obligation. For these requests, describe only the categories of third parties (e.g., "B2B sales teams using the Apollo platform") without naming specific customers.

______________________________________________________________________

### By request type:

**Access / Right to Know (GDPR Article 15 / CCPA Right to Know):**

- Acknowledge the request and cite the applicable regulation
- Confirm Apollo will respond with the data by the regulatory deadline (give the calculated date)
- Describe the **categories of data** Apollo may hold: professional identifiers (name, title, employer), contact information (business email, phone), usage/interaction data if applicable
- Explain **data sources** using Apollo-specific language above
- **GDPR only — include the recipient list:** List the customer names and/or domains from the Access Analysis that have accessed the individual's profile. This satisfies GDPR Article 15(1)(c). Format it clearly (e.g., a list of company names/domains). Do not include internal Apollo team IDs or ARR data — share only the customer name and domain.
- **CCPA/non-GDPR — omit the recipient list:** Describe only the category of recipients (e.g., "B2B sales and marketing teams") without naming specific customers.
- State the **format** for delivery (structured, portable format via secure download link or email attachment)
- Include the right to lodge a complaint with a supervisory authority (GDPR) or the AG/CPPA (CCPA)

**Deletion / Right to Erasure / Opt-Out (GDPR Article 17 / CCPA Right to Delete):**

- Acknowledge the request
- Confirm Apollo will process the deletion within the regulatory deadline (give the calculated date)
- **Explicitly explain the suppression mechanism:** deletion means removal from Apollo's active database AND placement on a suppression list to prevent re-ingestion from third-party data providers. This is critical — make it clear so the requester understands their data won't reappear
- If there is a **prior opt-out on record** (visible in the conversation history or automation note), acknowledge it proactively: apologize that the data reappeared, explain that re-ingestion can occur when data providers push updates, and emphasize that the suppression flag is being reapplied
- Confirm Apollo will notify downstream processors/partners where feasible (GDPR)
- Include the right to lodge a complaint with the relevant supervisory authority

**Legal Basis Inquiry (GDPR Article 13/14 / CCPA):**

- Explain that Apollo is a B2B data intelligence platform
- State the legal basis clearly: **legitimate interests under GDPR Article 6(1)(f)** — Apollo's interest is facilitating effective B2B business outreach by maintaining an accurate directory of business professionals, balanced against the individual's privacy interests
- Under CCPA: Apollo collects publicly available professional information for commercial purposes as a data broker
- Explain where the data came from using Apollo-specific source language above
- Describe the **right to object** (GDPR Article 21) and how to exercise it (reply to this email or submit via Privacy Center)
- Describe the **right to opt out** (CCPA) and how to exercise it
- Do not use dense legal language — explain it in plain terms

**Combined requests:** Address each component explicitly and separately. Don't merge them into one vague paragraph.

______________________________________________________________________

### Response deadlines

| Regulation | Standard | With extension |
|---|---|---|
| GDPR | 30 days from receipt | Up to 3 months total (must notify requester of extension within the first 30 days) |
| CCPA/CPRA | 45 days from receipt | Up to 90 days total (must notify requester of extension within the first 45 days) |

Always **calculate the specific date** from the conversation timestamp and include it in the draft (e.g., "We will respond by May 2, 2026").

______________________________________________________________________

### Tone guidelines

- **Professional and empathetic** — the requester may be concerned or frustrated; meet them with warmth
- **Plain English** — avoid dense legal language in the body; use parenthetical citations or a closing note for regulatory references
- **Confident, not defensive** — Apollo takes privacy seriously; the response should reflect competence and care, not anxiety
- **Clear on next steps** — the requester should leave knowing exactly what happens and when
- Avoid **"Please visit our Privacy Center"** as the primary response — this is unhelpful and the requester already received that from the auto-responder

______________________________________________________________________

______________________________________________________________________

## Step 6: Manual Actions & Ticket Hygiene ⚠️ These steps must be completed in Intercom — Claude cannot perform them

After presenting the draft, pause and present the user with the following checklist of manual steps that need to be completed before the ticket can be closed. Ask them to confirm when done before proceeding.

______________________________________________________________________

**Please complete the following steps manually in Intercom:**

> Before we close this out, here are the manual steps you'll need to complete in Intercom:
>
> **Sending the response:**
>
> - [ ] Review and copy the draft above into Intercom's reply box
> - [ ] Select the appropriate macro (listed below for reference) — Claude cannot apply macros
> - [ ] Send the reply to the requester
>
> **For deletion requests — internal documentation required:**
>
> - [ ] Go to the GDPR Claim Management Tool (app.apollo.io/#/admin/gdpr-claim-management) and process the deletion
> - [ ] Add an internal note in Intercom with a **screenshot of the GDPR Claim Management Tool** confirming deletion
>   - Exception: if data is linked via LinkedIn URL, phone number, or alternate email — paste the *text* output only; no screenshot required
> - [ ] Message **#lifecycle-marketing** in Slack to request the Customer.io unsubscribe
> - [ ] Add an internal note in Intercom with the **Customer.io screenshot** confirming unsubscribe (or confirming no data exists)
>
> **Tagging & escalation (if applicable):**
>
> - [ ] If this was escalated to Legal: apply the **Legal Escalations** tag in Intercom manually
>
> **Closing the ticket:**
>
> - [ ] Close the ticket once all of the requester's questions have been addressed — including access responses, deletion confirmations, data source explanations, legal basis questions, recipient disclosures, and customer deletion notifications
> - [ ] If the individual can't be located and you need more info: close the ticket rather than leaving it snoozed indefinitely (snooze is only appropriate when waiting on lead assistance)
>
> **Macro reference** (apply manually in Intercom — Claude cannot trigger these):
>
> - Deletion confirmations → **"Individual // Confirm Deletion"**
> - GDPR access responses → **"Individual // GDPR access requests"**
> - CCPA access responses → **"Individual // CCPA access request"**
> - Authorized agent deletions → **"Authorized Agent // Confirming Deletion"**
> - Post-deletion data source questions → **"Individual // Data source after deletion"**
> - Post-deletion specific questions → **"Individual // Specific questions after deletion"**
>
> **LinkedIn URL vs. Apollo URL data mismatch:**
> If the requester provided both an Apollo profile URL and a LinkedIn URL but the GDPR Admin Console shows different data for each: use any additional details they provided (company, location, job title) to confirm the correct identity before proceeding with deletion.

______________________________________________________________________

After presenting the checklist, ask: **"Have you completed the steps above and are ready to close this out, or is there anything else you need help with on this ticket?"**

______________________________________________________________________

## Output Format

Present the draft in this exact structure:

```
## DSR Response Draft

**Request type:** [Access / Deletion / Legal Basis / Combined — list all components]
**Regulation:** [GDPR / CCPA/CPRA / Best Practice — with jurisdiction note]
**Response deadline:** [Calculated date — e.g., "May 2, 2026 (30 days from April 2, 2026)"]
**Authorized agent:** [Yes — [service name] / No]
**Prior opt-out on record:** [Yes / No / Unknown]
**Escalation check:** [Clear — no triggers detected / ⚠️ ESCALATION REQUIRED — [reason and recommended path]]

---

**To:** [Requester name and email]
**Subject:** Re: Your Privacy Request — Apollo.io

---

Hello [First name],

Thank you for reaching out to us. I'm happy to assist you with your [data access / source / deletion] request under the [GDPR / CCPA].

**1. Deletion and suppression confirmation** *(include for deletion requests)*

We have processed your deletion request. Your personal data has been removed from Apollo's active database and your profile has been added to our suppression list. The suppression list is a critical part of this process — it prevents your information from being re-ingested if a third-party data provider pushes an update in the future. In other words, this isn't just a deletion; it's a permanent opt-out that blocks your data from reappearing in our system.

**2. Data Apollo held about you** *(include for access requests — GDPR Article 15 / CCPA Right to Know)*

In response to your access request, below is the personal data Apollo had on file for you at the time of this request:

- **Name:** [Name]
- **Job title:** [Title]
- **Employer:** [Company]
- **Location:** [Location]
- **LinkedIn profile:** [URL if available]
- **Business email:** [Email]
- **Phone number:** [Phone if available]

Apollo does not process sensitive personal data (health, financial, biometric, or similar categories) as part of its platform.

**3. Sources of your data** *(include for source/legal basis inquiries — GDPR Article 15(1)(g))*

Here is where each category of information came from:

- **Name, job title, employer, and location:** Gathered from publicly available online sources, including publicly accessible professional profiles and company websites indexed via web search.
- **Business email address:** Sourced from Apollo's **Customer Contributory Network** — a network of Apollo platform users who have connected their professional email accounts and, in doing so, contribute business contact information encountered in their professional communications.
- **Phone number:** [Also sourced from Apollo's Customer Contributory Network / Gathered from publicly available online sources — use whichever matches the GDPR Claim Management Tool. Do NOT name specific contributing customers.]

Apollo is a B2B sales intelligence platform. Our legal basis for processing your professional contact information under GDPR is **legitimate interests** (Article 6(1)(f)) — specifically, facilitating effective business-to-business outreach by maintaining an accurate, publicly-sourced directory of business professionals. Under CCPA, Apollo operates as a data broker and collects publicly available professional information for commercial purposes.

**4. Recipients of your data** *(GDPR access requests only — required under Article 15(1)(c). Omit for CCPA/non-GDPR.)*

The following companies have accessed your profile in Apollo's platform:

- [Company Name — domain.com]
- [Company Name — domain.com]
- [... list from the Access Analysis: customer name + domain only. Omit internal IDs, ARR, team creation dates.]

*(For CCPA/non-GDPR requests, replace this section with: "Your professional contact information may be accessed by B2B sales and marketing teams who use the Apollo platform to identify and reach relevant business contacts.")*

**5. Third-party notification** *(include for deletion requests or when requester asks about third parties)*

When Apollo processes a deletion request, we notify our customers (the businesses using the Apollo platform) that you have opted out and that they should remove your contact from their records unless they have an independent legal basis to retain it — such as a pre-existing business relationship with you. We cannot compel customers to delete data they hold independently, as they are the controllers of their own account data. However, they are contractually required under our Terms of Service to comply with all applicable privacy laws.

If you believe a specific company is processing your data unlawfully, you have the right to contact that company directly to exercise your rights, or to lodge a complaint with the competent data protection authority (see below).

**6. Your rights going forward**

Now that your data has been deleted and suppressed, Apollo will not process your personal information. If you have any further questions or concerns, please don't hesitate to reply to this email.

You also have the right to lodge a complaint with the **[relevant DPA — e.g., Spanish Data Protection Authority (AEPD) at aepd.es / California Privacy Protection Agency (CPPA) at cppa.ca.gov / ICO at ico.org.uk]**.

Kind regards,
Apollo Privacy Team
privacy@apollo.io

---

### Review checklist
- [ ] Requester name and details are correct
- [ ] Regulation and deadline are accurate for their jurisdiction
- [ ] All request components in their message have been addressed
- [ ] Suppression language is included (if deletion) — explains both removal AND re-ingestion prevention via suppression list
- [ ] Prior opt-out acknowledged if relevant
- [ ] **GDPR access requests:** Customer recipient list from the Access Analysis IS included (Art. 15(1)(c) — legal obligation)
- [ ] **CCPA/non-GDPR access requests:** Customer recipient list is NOT included — only category language used
- [ ] Data source attribution matches GDPR Claim Management Tool — do not substitute "proprietary algorithm" if source shown is Customer Contributory Network
- [ ] No specific contributing customer names used in source attribution — attribute to CCN generally
- [ ] Signature block uses privacy@apollo.io
- [ ] If authorized agent: agent language is used, not first-person to the individual
- [ ] If deletion: confirm GDPR Claim Management deletion and Customer.io unsubscribe before sending
- [ ] If data linked via LinkedIn URL or alternate email: text output only from GDPR tool (no screenshot required)
```

Always present the draft for review. Never send automatically.

______________________________________________________________________

## Notes

- If location is ambiguous, apply GDPR standards (more protective) and note the assumption.
- If the deadline is within 5 days of today, flag it prominently at the top of the draft.
- When a request combines multiple rights, address each one explicitly — don't merge them.
- Company/business profile deletion requests: note that Apollo is not obligated to honor deletion of company records (only individual personal data).
- The closing email signature should use **privacy@apollo.io** as the contact address.
- Compensation demands always escalate to Legal — never acknowledge liability or offer compensation in a draft.
