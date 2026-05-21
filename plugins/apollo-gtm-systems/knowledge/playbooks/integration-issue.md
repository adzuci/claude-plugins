---
last_reviewed: 2026-05-20
---

# Playbook: reporting an integration issue

## Symptoms that suggest an integration problem

- Data present in one system is absent or stale in another (e.g., a new Salesforce Contact not appearing in Apollo)
- A field value in one system does not match the same field in a connected system (e.g., Opportunity Stage in Gong differs from Salesforce)
- Duplicate records appearing after a sync
- Error messages in a system log referencing an integration or middleware name (Workato, Tray.io)

## Before filing

1. Check the sync delay. Most GTM stack integrations run on a 15-60 minute cycle. If the discrepancy is less than one hour old, wait one full cycle before assuming a bug.
2. Verify the record exists in both systems and that the matching key is consistent. For most integrations, the matching key is email address or an external ID field. A mismatch on the key means the sync cannot link the records.
3. Note the specific field or object affected, the expected value, the actual value, and when you first noticed the discrepancy.

## Filing the report

**Active pipeline impact (deal at risk, incorrect data going to a customer-facing system):**
Post immediately in `#sales-ops` with the details below.

**All other integration issues:**
File an RS JIRA ticket.

Include in either case:
- System A and System B (which two systems are out of sync)
- Object or field affected
- Example record IDs or links in both systems
- Expected value and actual value
- When you first noticed the issue

## Common integration pairs at Apollo

| Integration | Managed by | Typical sync lag |
|---|---|---|
| Apollo product to Salesforce (contacts, accounts) | GTM Systems | Near real-time to 30 min |
| Gong to Salesforce (call activities) | GTM Systems | ~15 min (SLA: <1 hour) |
| Gong to Apollo product (recordings) | GTM Systems | ~15 min (SLA: <1 hour) |
| Chili Piper to Salesforce (meetings booked, routing events) | GTM Systems | Near real-time |
| Ironclad to Salesforce (contract status, opportunity linkage) | GTM Systems | Near real-time |

For integrations not listed here, GTM Systems can identify the middleware and owner.

## Monitoring dashboards

Use these when investigating whether an issue is systemic vs. isolated:

- **Apollo to Salesforce integration:** Grafana dashboard — https://apolloio.grafana.net/goto/sp4psl?orgId=stacks-928328
- **SFDC/Mongo data mismatches:** Metaplane dashboard — https://app.metaplane.dev/dashboard/1451?range=%7B%22duration%22%3A%7B%22unit%22%3A%22days%22%2C%22value%22%3A7%7D%7D
