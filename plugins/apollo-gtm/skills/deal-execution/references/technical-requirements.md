# Technical Requirements & Integration Checklist

Use this reference during Stage 1 (Discovery) and Stage 3 (Solution Evaluation) to validate technical feasibility before committing deal resources. Surface hard blockers early — don't let them become surprises at Stage 4.

---

## CRM Integration Matrix

| CRM | Integration Level | Notes |
|---|---|---|
| **Salesforce** (Professional, Enterprise, Unlimited) | Full native integration | Bi-directional sync, field mapping, activity logging. Full support. |
| **Salesforce Essentials** | **NOT SUPPORTED — HARD BLOCKER** | No API access on Essentials plan. Integration impossible. Do not progress deal without plan upgrade. |
| **HubSpot** (Professional, Enterprise) | Full native integration | Bi-directional sync, contact/company/deal sync. |
| **HubSpot** (Free, Starter) | Limited | Reduced API limits. Confirm specific use case feasibility with SC. |
| **Pipedrive** | Native integration | Contact and deal sync. Some limitations on custom fields. |
| **Zoho CRM** | Native integration | Standard object sync. Confirm custom object requirements. |
| **Microsoft Dynamics 365** | Supported | Standard CRM sync. Confirm tenant type — see GCC High blocker below. |
| **Other CRMs** | API/Zapier/CSV | No native integration. Requires technical team at prospect or Zapier/Make middleware. Flag as risk. |

---

## Email & Mailbox Compatibility

| Provider | Compatibility | Notes |
|---|---|---|
| **Google Workspace** | Full support | OAuth connection. Sequences, tracking, inbox integration. |
| **Microsoft 365** | Full support | OAuth connection. Same capabilities as Google. |
| **Microsoft GCC High / Gov tenant** | **HARD BLOCKER** | Cannot link mailboxes. Government compliance environment blocks OAuth. Escalate to SC immediately. |
| **On-premise Exchange** | Not supported | No cloud API access. Apollo requires cloud-based email. |
| **Other providers** | Case-by-case | IMAP/SMTP may work for basic sending. No tracking or inbox features. Confirm with SC. |

---

## Hard Blockers — Do Not Progress

These conditions make Apollo technically infeasible. Stop the deal and document as Closed Lost or park until conditions change:

| Blocker | Impact | Action |
|---|---|---|
| Salesforce Essentials plan | No API access — integration impossible | Confirm plan tier. If Essentials, deal cannot proceed without upgrade. |
| Microsoft GCC High / Gov tenant | Cannot link mailboxes — core functionality broken | Escalate to SC immediately. No workaround. |
| No CRM and no technical team | Cannot set up data flow — Apollo data has nowhere to go | Assess if prospect will adopt a CRM or has technical resources for API integration. |

---

## Risk Signals — Loop in SC Before Committing

| Signal | Risk | Action |
|---|---|---|
| Replacing Outreach or Salesloft | No native migration path. Manual sequence migration required. | Loop in SC before committing to timeline. Set realistic expectations on migration effort. |
| Complex Salesforce customization | Custom objects, validation rules, or triggers may conflict with sync | SC technical assessment required at Stage 2. |
| Multiple CRM instances | Sync conflicts, deduplication challenges | SC needs to map data architecture before Stage 3. |
| Strict data residency requirements (EU, etc.) | Apollo data processing locations may not comply | Confirm with Security/Legal before Stage 3. |
| SSO/SAML requirements | May require Enterprise plan or specific configuration | Confirm plan tier supports SSO. |

---

## Validation Checklist (Use at Stage 1)

Run through this checklist during or immediately after the first discovery call:

- [ ] **CRM identified** — what CRM and what plan/tier?
- [ ] **CRM plan confirmed** — is it a supported plan (not Essentials)?
- [ ] **Email provider identified** — Google Workspace, M365, or other?
- [ ] **Government/GCC tenant?** — if yes, HARD BLOCKER
- [ ] **Current tools being replaced** — Outreach, Salesloft, ZoomInfo, other?
- [ ] **Data flow requirements** — what data needs to go where?
- [ ] **Technical team available** — do they have ops/admin/dev resources?
- [ ] **Security/compliance requirements** — SOC 2, data residency, SSO?
- [ ] **Integration complexity** — custom objects, multi-instance, middleware needs?

---

## "Not a Fit" Signals

If you encounter these, the deal is likely not technically viable:

- Salesforce Essentials with no plans to upgrade
- Government/GCC High email tenant
- No CRM, no technical resources, and no plan to adopt
- On-premise-only infrastructure with no cloud adoption plans
- Regulatory requirements that prohibit cloud-based data processing

Document these findings in SFDC and discuss with your manager before Closed Lost.

---

## Escalation Triggers — When to Bring in SC Early

Bring SC into the deal before Stage 2 if any of these apply:

- Prospect is replacing Outreach, Salesloft, or another sequencing tool
- Complex Salesforce environment (custom objects, multiple instances)
- Prospect mentions data residency, compliance, or security requirements
- Prospect has no CRM but expects full integration capabilities
- Enterprise prospect with SSO/SAML requirements
- Any hard blocker detected — SC confirms before Closed Lost decision

---

*Source: Apollo Technical Requirements & Integration Checklist (internal document, Apr 2026).*
