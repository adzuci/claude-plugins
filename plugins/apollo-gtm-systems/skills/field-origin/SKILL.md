---
name: field-origin
description: Traces a Salesforce field (Object.FieldApiName__c) back to its origin — integration source, automation chain, ticket reference, and dependent objects — using field descriptions, automation docs, and the Salesforce MCP.
---

# Field origin

Triggered when the user names a specific Salesforce field and asks where it comes from, what populates it, who owns it, or why it has a specific value.

Input: `Object.FieldApiName__c` (e.g., `Opportunity.Position__c`, `Lead.Enrichment_Source__c`).

If the user gives a label instead of an API name, ask for the API name or look it up via SF MCP before proceeding.

## Step 1 — Check the SFDCgearset repo

Use the GitHub MCP to search `apolloio/SFDCgearset` for the field API name. The repo contains the full metadata-as-code representation of Apollo's Salesforce org, including field descriptions, dependencies, automation references, and ticket traceability. This is usually faster and more complete than querying the Salesforce MCP directly.

Search for the field API name in:
- `force-app/main/default/objects/<ObjectName>/fields/<FieldApiName__c>.field-meta.xml` — field definition with description
- `force-app/main/default/flows/` — flows that reference the field
- `force-app/main/default/classes/` — Apex classes that touch the field

If the repo yields a field description or automation reference, note it and cite: `[source: apolloio/SFDCgearset, field-meta.xml, queried <date>]`

If GitHub MCP is unavailable, skip directly to Step 2.

If the field is not in the repo, proceed to Step 2.

## Step 2 — Read the field description from SF MCP

Query the Salesforce MCP for the field metadata on the named object. Pull:
- `Label`
- `Description`
- `Type`
- `Length` or `Precision` (if applicable)
- `CreatedDate`, `LastModifiedDate`

Check the `Description` field for an RVOSYS ticket reference. Apollo convention: field descriptions follow the format `RVOSYS-XXXX | <human description>`. If a ticket reference is present, pull the JIRA ticket via JIRA MCP for additional context (owner, request details, implementation notes).

Cite as: `[source: SF field metadata (<Object>.<FieldApiName>), queried <date>]`

## Step 3 — Check automation docs

Load `knowledge/salesforce/automation.md`. Search for the field API name. This file documents:
- Flows that read or write the field
- Apex classes or triggers that touch it
- Scheduled jobs that use it as input

If the field appears in automation docs, note which automation writes it, the trigger condition, and any dependent fields.

Cite as: `[source: knowledge/salesforce/automation.md]`

## Step 4 — Check integration sources

Load `knowledge/salesforce/integrations.md`. Search for the field API name. This file documents which external systems write to Salesforce fields and via which connector (Workato, native connector, Apex callout).

Common sources at Apollo: Apollo product (sequence enrollment and contact activity fields), Gong (call and engagement fields), Chili Piper (routing and scheduling fields), Ironclad (contract status fields). If a field has a package namespace prefix in its API name, it was installed by a managed package; check the Setup Audit Trail for the install date and package name.

If the field is owned by an integration, note the source system, connector type, and sync direction.

Cite as: `[source: knowledge/salesforce/integrations.md]`

## Step 5 — Live SF MCP query (if steps 1-4 are inconclusive)

If the field description, automation docs, and integration docs don't explain origin, query Salesforce MCP directly:

- Check if any active Flow references the field as a target (write) variable
- Check if any installed package declares ownership of the field (package namespace prefix on the API name is a strong signal)
- Check `SetupAuditTrail` for who created the field and when

Only use this step when knowledge files don't resolve the question. Live queries are slower; knowledge files are faster.

## Step 6 — Synthesize and respond

Combine what you found across steps. A complete field origin answer includes:

1. What the field stores (from description or label)
2. What writes to it (automation, integration, or manual)
3. The originating ticket, if found (RVOSYS-XXXX)
4. Any downstream dependencies (other fields, objects, or processes that read it)

If origin is still unclear after all steps, log a gap entry per the gap-flagging procedure in `agents/athena.md` with topic: `field origin unknown: <Object>.<FieldApiName>`.

## Special case — traceability fields

Fields named `Position__c`, `Source_Position__c`, or any field with "position", "origin", or "trace" in the label often exist to track where a record came from in a pipeline or routing flow. Treat these as high-value — their description and automation chain are usually more important than the field value itself.
