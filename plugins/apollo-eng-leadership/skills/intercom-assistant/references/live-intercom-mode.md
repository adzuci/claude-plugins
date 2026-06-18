# Live Intercom Mode

Use this reference when the user asks about a real support question or provides an Intercom conversation, customer, company, email, or vague live-support ask without `sim`.

## Investigation Workflow

1. Identify the lookup key:
   - conversation ID or Intercom URL
   - customer email or contact ID
   - company name, domain, or company ID
1. Use Intercom tools before drafting conclusions:
   - `mcp__intercom.fetch` for prefixed IDs or Intercom URLs
   - `mcp__intercom.get_conversation` for raw conversation IDs
   - `mcp__intercom.search` with `object_type:contacts email:<email>` or `object_type:conversations ...`
   - `mcp__intercom.search_conversations` for structured conversation filters
   - `mcp__intercom.get_contact` / `get_company` for full profiles when needed
1. Read the full thread before drafting a reply if a conversation is provided.
1. Build a short private diagnosis:
   - customer goal
   - observed symptom
   - account or permission facts found
   - what is unverified
   - likely next best action
1. If the route is clear, use `routing-and-macros.md` to propose the appropriate Intercom macro/workflow. Do not apply it.
1. If the customer asks a product/process/how-to/troubleshooting question, use `glean-support-rep-assistant.md` before drafting factual guidance.
1. Draft a customer-facing response that acknowledges the concrete situation, verifies the goal, guides, and sets expectations.

## Customer-Facing Style

- Do not apologize for Apollo, the product, or product behavior unless Apollo has clearly made an error and that tone is appropriate.
- Do not infer feelings the customer did not state. Avoid "I can see how frustrating..." and similar phrases.
- Acknowledge facts instead: deadline, blocked workflow, missing button, account change, failed step, or stated concern.
- Use calm ownership language: "I can help narrow this down", "Let's check the exact screen", "The fastest path is a quick screen share."

## Search Starters

```text
object_type:contacts email:"customer@example.com"
object_type:contacts email_domain:"example.com"
object_type:conversations source_author_email:"customer@example.com"
object_type:conversations state:open source_body:contains:"export"
```

## Evidence Rules

- Cite Intercom conversation IDs or URLs in private notes.
- Do not expose internal-only facts in customer-facing copy unless they are appropriate to share.
- If search results are incomplete, say exactly what was searched and what remains unverified.
- If Intercom tools are unavailable or auth fails, ask for pasted context or a screenshot and label the answer as not live-verified.
- Do not propose a macro or workflow unless the route is clear from source-backed context.

## Escalation Ask Template

```text
Customer/account:
Issue:
Customer goal:
What I checked:
Evidence:
Need help with:
Urgency:
```
