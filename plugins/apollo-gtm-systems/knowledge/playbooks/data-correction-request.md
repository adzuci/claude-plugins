---
last_reviewed: 2026-05-20
---

# Playbook: requesting a data correction

Use this playbook to correct inaccurate records in Salesforce or other GTM tools.

## For one or two records

Post in `#sales-ops` with:

- System (e.g., Salesforce)
- Object and record ID (or record name and link)
- Current incorrect value
- Correct value
- Why the correction is needed

GTM Systems or the relevant system admin will action the correction.

## For bulk corrections (10 or more records)

File an RS JIRA ticket with the same information above, plus:
- A CSV or a Salesforce report link showing all affected records
- The field API name (e.g., `Segment__c`, not just "Segment") to avoid ambiguity

GTM Systems will confirm the field and scope before making changes.

## For integration sync issues

If the problem is that one system shows the correct value but another does not (e.g., a contact is correct in Apollo but wrong in Salesforce), include:

- The last date you saw the correct value in each system
- The integration involved (e.g., Apollo-to-Salesforce contact sync, Gong-to-Salesforce activity writeback)
- Example record IDs in both systems

File as an RS JIRA ticket. Integration fixes require GTM Systems to investigate the sync job and may take longer than single-record corrections.

## What not to change directly

Do not attempt to correct system-managed fields (formula fields, rollup summaries, fields owned by an automation) by editing the record manually. If the field is read-only or keeps reverting after you save a change, the value is being set by an automation. File an RS JIRA ticket instead.
