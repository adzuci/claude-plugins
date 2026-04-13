# Source Catalog — Skill Reference

**Owner:** Shyam SK | **Updated:** 2026-03-20

## What it does

A Claude Code skill (`/source-catalog`) that produces a data catalog entry for a source system object. Supports three source systems:

- **Amplitude** — what an event tracks, user action, properties, where it fires, conditionals, squad, last engineer
- **Mongo** — collection schema, fields with types, indexes, relationships, validations, Snowflake mirror, squad, last engineer
- **SFDC** — Salesforce object overview (shape, key fields, validation rules, triggers, flows) or field deep-dive (full metadata, business logic, sync direction)

The skill asks the user which source system to look at, then produces a reference card.

## How to invoke

```
/source-catalog <amplitude|mongo|sfdc> <object-name> [field-name]
```

If you omit the source system, it will ask you.

### Examples

```
# Amplitude events
/source-catalog amplitude User Logged In
/source-catalog amplitude Record Actioned: Copy Email

# Mongo collections
/source-catalog mongo contacts
/source-catalog mongo emailer_messages

# SFDC — object overview
/source-catalog sfdc Account
/source-catalog sfdc Opportunity

# SFDC — field deep-dive
/source-catalog sfdc Account Account_Demographic_Score__c
/source-catalog sfdc Opportunity StageName

# Without source — it will ask
/source-catalog User Logged In
```

## Prerequisites

1. **Claude Code** installed locally
2. **leadgenie repo** cloned locally (or set `LEADGENIE_REPO` env var)
3. **SFDCgearset repo** cloned locally for SFDC lookups (or set `SFDC_REPO` env var)
4. Running from the **analytics-copilot** repo

## SFDC two-mode approach

SFDC objects can have hundreds of fields. Instead of dumping them all:

- **Overview mode** (default): shape of the object — field count, categories, key fields grouped logically, validation rules, triggers, flows, record types. Answers "what is this thing?"
- **Field deep-dive** (pass field name): full metadata for one field — type, label, description, picklist values, formula, validation rules, flows/triggers referencing it, sync direction. Answers "what does this field mean and can I trust it?"

## When to use

- Before writing a query, you want to understand what an event/collection/object actually measures
- You need to know what properties or fields are available
- You want to find the owning squad or the engineer to ask about behavior
- You're onboarding to a new data source and want a quick overview
- You need to check if a specific SFDC field has validation rules or is synced to Apollo
