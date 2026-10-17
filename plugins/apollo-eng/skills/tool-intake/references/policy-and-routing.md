# Apollo Intake Routing

Process details change. Verify current steps from the linked source before stating them as policy.

## Sources

- Zip Guide in Notion: https://www.notion.so/2feab2b3b49680ee9309d07a5fc58111
- Procurement FAQ in Notion: https://www.notion.so/176ab2b3b49680f991e4f051934f41e6
- AI Cybersecurity Training in Notion: https://www.notion.so/2bcab2b3b4968094808feb3b156b7665
- Security's interim isolation guidance: https://apolloio.slack.com/archives/C050992HHFE/p1784570260259349?thread_ts=1784208961.859939&cid=C050992HHFE
- Legal's data-use and vendor-training follow-up: https://apolloio.slack.com/archives/C08KG1BFW/p1784157755671229?thread_ts=1784123855.491269&cid=C08KG1BFW
- Start a Zip request: https://apollo.zip.com/create-workflow-request
- Zip help desk: https://apolloio.slack.com/archives/C078HCHU1SL
- Procurement & Finance Operations FAQ skill: `/apollo-procurement:procurement-faq`

Credit Apollo Legal's Engineering training on data use and vendor contracting as source material when it informs an answer.

## Routing Rules

- Use the current Zip or Procurement source before describing required steps or thresholds.
- Route process uncertainty to `#zip-help-desk`; do not invent intake steps.
- Route contract, DPA, click-through, training-use, or legal-language questions to the appropriate Legal and Procurement workflow.
- Route security/privacy questions involving production data, customer data, credentials, subprocessors, or AI training to Security/Privacy review.
- Draft handoffs only. Do not submit Zip records or send Slack messages unless the user separately asks and authorizes the write.
- Route every vendor, including POCs, online terms, free tools, and $0 vendors, through Zip. Involve Legal early for cross-customer data uses, new uses of existing data, email or recording data, native data outside core-product uses, and third-party vendor restrictions.
- For AI tools, point to the AI Cybersecurity Training and data-use/vendor-training sources. Surface model training, cross-customer use, provider jurisdiction, data residency, and customer-trust concerns when relevant.

## Lightweight Exploration

Security's interim guidance allows lightweight exploration in a clean environment and blank folder with no Apollo confidential data, customer data, PII, credentials, or corporate integrations. Do not connect unvetted extensions or plugins. Route a new AI vendor or a materially new use case for an existing vendor through Legal and Security review.

## Zip MCP

Apollo's Zip MCP is live and read-only.

- Endpoint: HTTP `https://mcp.zip.com/mcp`.
- Auth: OAuth with DCR and PKCE; metadata at `https://app.ziphq.com/.well-known/oauth-authorization-server`.
- Setup: `claude mcp add --transport http zip https://mcp.zip.com/mcp`, then `claude mcp login zip` (or `/mcp`).
- Tools read vendors, requests, purchase orders, invoices, agreements, workflows, departments, users, and similar records. There are no write or submit tools, so requests are still created in Zip by a human.
- Token visibility may be scoped to agreements the user created, so an empty result is not proof that no record exists.
- Owner: Procurement (Tyler Davis); help in `#zip-help-desk`.
- Do not substitute a similarly named public package.

## Intake Packet

```text
Tool and vendor:
Delivery model and version:
Canonical repository or product URL:
Business problem and intended use:
Business owner:
Users and expected scale:
Data involved and classification:
Requested permissions and integrations:
Network destinations and subprocessors:
AI training, retention, and deletion controls:
Apollo alternatives considered:
Proposed synthetic-data test:
Contract, DPA, or click-through terms:
Pricing page and expected cost:
Unknowns requiring review:
Sources:
```
