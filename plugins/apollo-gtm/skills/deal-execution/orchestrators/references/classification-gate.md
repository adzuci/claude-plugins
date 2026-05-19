# Classification Gate Reference

## Decision Tree

```
For each email thread:

  1. Is the sender domain in seller_domains or internal_domains?
     YES → Pipeline (internal thread)
     NO  → continue to step 2

  2. Does the thread contain at least one message from someone
     outside seller_domains / internal_domains?
     NO  → Pipeline (outbound only, no buyer turn)
     YES → continue to step 3

  3. Are B2B sales signals present?
     NO  → Pipeline (external but non-sales)
     YES → GEN-SE Pipeline
```

## B2B Sales Signals (step 3)

Any ONE of these qualifies a thread as B2B:

**Content signals (subject or body):**
- demo, trial, pricing, proposal, contract, evaluation
- POC, proof of concept, pilot
- ROI, business case, decision
- renewal, expansion, upsell
- onboarding, implementation, go-live
- champion, executive sponsor, stakeholder

**Context signals (from Phase 1 data):**
- Sender appears in Apollo as a prospect, customer, or deal contact
- Sender's company has a Slack deal channel
- Thread originated from an Apollo sequence or outbound campaign
- Calendar shows a demo or deal meeting with the sender's company
- Gong notification references a call with the sender

## Edge Cases

| Scenario | Classification | Rationale |
|----------|---------------|-----------|
| Calendar invite with external attendees | Pipeline | Not an email thread with replies |
| Gong call recording notification | Pipeline/document | Deal intel, not a reply-able thread |
| Auto-forward from personal email | Pipeline/document | Self-sent, no reply needed |
| Zoom/Miro/tool notification | Pipeline | Automated, check if action implied |
| Newsletter from internal team | Pipeline/document | Informational broadcast |
| Vendor email (not a customer) | Pipeline | External but not a sales thread |
| Recruiter outreach to AE | Pipeline | External but personal, not B2B sales |
| Customer support thread | Pipeline | B2B but not sales — message-os handles |
| Buyer replies to a sequence email | GEN-SE | B2B sales, buyer turn exists |
| Champion forwards thread to VP | GEN-SE | Multi-stakeholder, buyer turns exist |
| Procurement asks for security docs | GEN-SE | B2B sales, procurement stage |

## GEN-SE Configuration

When routing to GEN-SE, pass this configuration:

```yaml
# Required — replace placeholders with values from the orchestrator config block
seller_emails: ["{{YOUR_EMAIL}}"]
seller_domains: ["{{YOUR_SELLER_DOMAINS}}"]
internal_domains: ["{{YOUR_INTERNAL_DOMAINS}}"]
product_context: >
  Apollo.io — B2B sales intelligence and engagement platform.
  See references/ for full product context.

# Optional (pass when available from Phase 1)
account_context:
  related_threads: []     # from Slack deal channel + Apollo (if connected)
vertical: ""              # from Apollo enrichment (if connected)
account_tier: ""          # from CRM/Apollo (if connected)
sending_identity: "{{YOUR_EMAIL}}"
```
