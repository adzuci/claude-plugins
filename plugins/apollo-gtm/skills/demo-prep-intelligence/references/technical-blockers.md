# Technical Blockers and Integration Risks

Use this reference when source data mentions CRM, mailbox provider, security, compliance, migration, data flow, enrichment, integrations, or technical feasibility.

## Hard Blockers

These conditions make Apollo technically infeasible unless the customer changes environment or plan.

| Blocker | Impact | Required handling |
|---|---|---|
| Salesforce Essentials plan | No API access; CRM integration impossible. | Flag as hard blocker. Confirm plan tier. Do not imply Apollo can integrate without a Salesforce plan upgrade. |
| Microsoft GCC High or government tenant | Mailbox linking is not supported; core email functionality is blocked. | Flag as hard blocker. Escalate to SC and validate tenant type. |
| On-premise Exchange | Not supported because Apollo requires cloud-based email access. | Flag as hard blocker or severe limitation depending on use case. Validate whether cloud migration exists. |

## Integration Risk Signals

These do not automatically block the deal, but they require careful handling.

| Signal | Risk | Recommended handling |
|---|---|---|
| Replacing Outreach or Salesloft | Manual sequence migration; no native migration path. | Set realistic expectations and do not promise painless migration. |
| Complex Salesforce customization | Custom objects, validation rules, automations, or triggers may conflict with sync. | Ask for CRM admin involvement and map critical fields before demo/trial. |
| Multiple CRM instances | Sync conflicts and dedupe complexity. | Clarify source of truth and data architecture. |
| HubSpot Free or Starter | Reduced API limits and functionality. | Confirm use case feasibility with SC. |
| Non-native CRM | API, Zapier, Make, or CSV process may be needed. | Validate prospect has technical resources. |
| Strict data residency requirements | Apollo data processing may need legal/security validation. | Avoid compliance claims until Security/Legal confirms. |
| SSO/SAML requirements | May require specific plan or configuration. | Confirm packaging and identity provider requirements. |
| No CRM and no technical team | Apollo data may have nowhere to sync or operationalize. | Clarify whether Apollo will be system of action only or if CRM adoption is planned. |

## Migration Risk Signals

Replacement deals almost always carry migration risk. Surface migration topics in Landmines and Open Questions even when they are not hard blockers.

| Migration area | Risk | Recommended handling |
|---|---|---|
| Sequence or cadence migration | Existing templates, steps, rules, and reporting may need manual rebuild. | Ask which sequences must migrate before launch and which can be retired. Do not promise one-click migration unless verified. |
| Workflow or automation migration | Trigger logic, suppression rules, branching, and ownership rules may not map 1:1. | Demo the target-state workflow and identify what needs UI setup, CRM config, or workaround. |
| Data migration | Lists, saved searches, enriched fields, custom fields, and exclusions may be incomplete. | Clarify source of truth, required fields, and migration owner. |
| CRM integration migration | Field mappings, validation rules, custom objects, and ownership logic may change behavior. | Require RevOps/admin validation before POC or rollout. |
| Reporting migration | Incumbent reports may not map directly to Apollo analytics. | Identify must-have reports and show the closest Apollo view or gap. |
| User adoption migration | Reps may resist tool changes or lose familiar workflows. | Include enablement plan, phased rollout, and manager visibility in next steps. |

For any replacement deal, add at least one Open Question about migration scope unless the source data already documents it.

## Sensitive Topics

Watch for these in SFDC, Slack, or Gong and include them in Landmines:

- Pricing already discussed or quoted.
- AE promises about functionality, implementation, migration, security, or legal terms.
- Competitive claims that require PMM-approved proof.
- Security/compliance requirements such as SOC 2, GDPR, data residency, DPA, SSO, or vendor review.
- Data Duel or enrichment test results that are weak, incomplete, or still in progress.
- Prospect asks for product features Apollo does not support or supports differently.

## Demo Handling Guidance

- If a hard blocker is detected, do not recommend a normal product demo without surfacing the blocker first.
- If risk is unvalidated, turn it into an Open Question.
- If the blocker is only inferred, tag it `[inferred]` and ask the SC to confirm before raising it forcefully.
- Do not contradict pricing, packaging, security, or roadmap commitments already made by the AE; flag them as sensitive topics.
