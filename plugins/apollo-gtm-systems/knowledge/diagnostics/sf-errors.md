---
last_reviewed: 2026-05-20
---

# Diagnostic: Salesforce errors and save failures

When a user reports an error, ask them to share:
- A screenshot or the full error text (copy-paste is fine)
- The record link or record ID where the error occurred
- What they were trying to do when the error appeared

This lets Athena cross-reference the error text against knowledge files and the SFDCgearset codebase for more context.

Common error patterns, what they mean, and how to resolve them.

## Validation rule errors

**Message format:** `[Rule name]: [error message]`

These are intentional. A validation rule is blocking the save because a required condition is not met. Read the error message carefully; it usually names the field to fill in or the condition that must be true before saving.

Resolution: satisfy the condition described in the message. If the rule appears incorrect for your use case or is blocking a legitimate action, open an RS JIRA ticket so GTM Systems can review the rule.

## Required field errors

**Message format:** `[Field name] is required`

The field named in the error must be populated before saving.

Resolution: fill in the field. If the field is not visible on your page layout, file an RS JIRA ticket asking GTM Systems to check your profile and layout configuration.

## Duplicate record errors

**Message format:** `A duplicate record was found`

Salesforce identified an existing record that matches the one you are creating or editing.

Resolution: review the suggested duplicate. If they are genuinely the same record, merge or update the existing one. If they are distinct records that Salesforce is incorrectly flagging, escalate to GTM Systems via `#sales-ops` with both record IDs.

## Insufficient permissions

**Message format:** `You don't have access to [object or field]` or `Insufficient privileges`

Your profile or permission set does not include the access level needed for that action.

Resolution: file an RS JIRA access request specifying the object or field name, what you need to do (read, edit, create, or delete), and why.

## Apex errors (DML exceptions and system errors)

**Message format:** `System.DmlException`, `System.LimitException`, or other Apex class names

These are developer-level errors caused by a failing automation or trigger. They are not user-fixable directly.

Resolution: screenshot the full error message including the Apex class name if visible, then open an RS JIRA ticket with the screenshot and the exact steps you took before the error appeared.

## Record locked by another user

**Message format:** `Record was modified by another user`

Salesforce detected an optimistic lock conflict — the record was updated by someone else (or by an automation) between when you opened it and when you tried to save.

Resolution: reload the record and try your edit again on the fresh version. If this conflict occurs repeatedly on the same record, the record may be targeted by a high-frequency automation. Escalate to GTM Systems so they can review the automation firing pattern.

## Escalation

For any Salesforce error not covered here, post in `#sales-ops` or file an RS JIRA ticket with:
- The full error text (screenshot preferred)
- The object and record ID (or record name)
- The action you were attempting
- The steps to reproduce
