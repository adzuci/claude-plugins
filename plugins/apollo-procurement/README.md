# apollo-procurement

Procurement & Finance Operations assistant for Apollo employees. Answers questions about spend, travel, cards, vendors, invoices, and contracts — grounding every answer in the live canonical FAQ.

**Owner:** Tyler Davis, Sr. Manager, Procurement & Finance Operations

## Skills

- **`procurement-faq`** — Answers any Procurement & Finance Operations question: travel & expense (Navan), procurement intake (Zip), accounts payable, corporate cards (Ramp/Brex), and contracts (IronClad). Fetches the live canonical FAQ Google Doc on every invocation, answers with exact policy figures and the right routing channel, and falls back to an embedded routing table if the doc can't be reached. Requires the Google Drive connector. Trigger phrases: "how do I book travel", "what's the expense limit", "where do I submit an invoice", "who approves this purchase", "how do I get a corporate card", "what's the contract threshold".

## Source of truth

The **Procurement Systems Integration Map** (owner: Tyler Davis) is the ultimate source of truth. The FAQ doc this plugin fetches summarizes that map — if they ever conflict, the Integration Map wins and the FAQ is corrected.
