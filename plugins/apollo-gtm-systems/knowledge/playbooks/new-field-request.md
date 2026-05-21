---
last_reviewed: 2026-05-20
---

# Playbook: requesting a new Salesforce field or field modification

## Simple requests

Scope: adding a text, picklist, checkbox, or number field; adding or modifying picklist values on an existing field.

File an RS JIRA ticket at https://apollopde.atlassian.net/servicedesk/customer/portal/8 with:
- Object name (e.g., Account, Opportunity, Lead)
- Desired field label and API name (if you have a preference)
- Field type and, for picklists, the allowed values
- How the field will be populated: manual entry, integration, automation, or formula
- What decision or process it supports
- Who uses it and how often

Typical turnaround: 1 sprint (2 weeks), depending on the queue.

## Complex requests

Scope: custom objects, formula fields, rollup summaries, fields that will trigger automations, or fields with reporting dependencies.

Use the Notion RevOps intake form. Include a mini-spec covering:
- Purpose: what decision or process this enables
- Logic: if it is a formula or rollup, write out the logic in plain language
- Dependencies: objects, fields, or automations this will interact with
- Reporting needs: will this field appear in dashboards or reports? Which ones?
- Downstream effects: does anything break if the field is missing or null?

Turnaround is scoped per ticket after intake review.

## Naming convention

All new fields must include the RVOSYS ticket reference in the field description field (not the label). Format: `RVOSYS-XXXX | Brief description of purpose`. This is required for traceability and is enforced during GTM Systems review.

## Modifying an existing field

For picklist value changes, type changes, or label updates, file an RS JIRA ticket. Include the current field API name, what you want changed, and whether any existing records hold values that will be affected.

Type changes (e.g., text to picklist) on fields that already hold data require a migration plan. Flag this in the ticket.
