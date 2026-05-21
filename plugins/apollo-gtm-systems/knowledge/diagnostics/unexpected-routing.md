---
last_reviewed: 2026-05-20
---

# Diagnostic: lead or meeting routed to the wrong rep or queue

Work through these root causes in order.

## 1. Account ownership in Salesforce

Chili Piper reads the Account Owner field on the matching Salesforce Account record when routing for named accounts. If the account is unowned (blank Account Owner) or owned by the wrong rep, routing follows that state.

Check: open the Account in Salesforce and confirm the Account Owner field is correct. If it is wrong, file a data correction request in `#sales-ops`.

## 2. Territory or segment assignment

Territory and segment fields on the Lead or Contact record drive which Chili Piper routing rule applies. If the record's segment or territory value is incorrect, routing will fire against the wrong rule.

Check: on the Lead or Contact in Salesforce, verify the Segment and Territory fields match the rep's book. If they are wrong, request a data correction via `#sales-ops`.

## 3. Rep availability

If the assigned rep is marked OOO or is at capacity in Chili Piper, the system will round-robin or escalate to the next available rep. This is expected behavior.

Check: ask the rep to verify their availability settings in Chili Piper. If they were available but still didn't receive the meeting, escalate to GTM Systems.

## 4. Round-robin configuration

For unowned accounts, Chili Piper uses a round-robin rule to assign meetings across eligible reps. If the round-robin sent the meeting to the wrong team, the routing rule assignment for that segment may be misconfigured.

Resolution: file an RS JIRA ticket describing the expected routing team and what was received. Include the booking link used, the rep it was sent to, and the account name.

## 5. Duplicate records with conflicting ownership

If a Contact or Lead record is duplicated and the two records have different owners, Chili Piper may match against the wrong duplicate and route accordingly.

Check: search Salesforce for the contact by email and confirm there is only one active record. If duplicates exist, report via `#sales-ops` with both record IDs.

## Escalation

For a live misroute where a deal is at risk, post immediately in `#sales-ops` with the account name, rep it was routed to, rep it should have gone to, and the meeting date and time.

For retroactive or process questions, open an RS JIRA ticket with the same information.

## Chili Piper edge API routing context

Once the Chili Piper MCP proxy is live, Athena can query the CP edge API routing logs to pull context based on form field values and matching router rules. This will allow more precise root-cause identification without requiring the user to manually describe the booking flow. Until then, work through the root causes above using Salesforce MCP for record state and ask the user to describe the booking path used.
