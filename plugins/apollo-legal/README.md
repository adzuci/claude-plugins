# apollo-legal

End-to-end contract review for Apollo's Commercial Legal team.

## Skills

- **`vendor-negotiation-support`** — Helps managers evaluate vendor renewals, pricing proposals, renewal dates, negotiation options, and vendor email responses, then coordinate next steps with Procurement and Legal. Finds existing vendor relationships from Slack channels and CRM, unblocks stalled deals (leadership warm intros, legal-to-legal calls), and handles 360 / two-way deals where the vendor is also an Apollo customer. Builds the deal's who's-who and verifies vendor-side contacts with Apollo data (`enrich` mode). Calls out to `vendor-contract-review` for legal review, redlines, or signability.
- **`vendor-contract-review`** — Reviews vendor contracts. Classifies into one of six categories, applies the Apollo playbook, generates a redlined Word document, and outputs a summary. Trigger phrases include "review this contract", "redline this vendor contract", "is this okay to sign". Excludes NDAs.
- **`nda-redline-monitor`** — Reviews Mutual NDAs. Detects counterparty paper vs. counterparty redlines to Apollo's template and routes accordingly. Trigger phrases include "review this NDA", "run the NDA monitor". One-way NDAs are not yet supported.
- **`privacy-questionnaire-bot`** — Drafts answers for Trust & Compliance Deal Support security and privacy questionnaires (vendor assessments, RFP security sections, DPA reviews) from a Jira ticket or a pasted/uploaded file. Reuses prior completed questionnaires, scores each answer 0–100 for confidence, lists open questions, and exports CSV or HTML. Invoke with `/apollo-legal:privacy-questionnaire-bot [JIRA-KEY]`. Needs Atlassian, Glean, and Google Drive connectors.

Each skill's full scope, prerequisites, and workflow live in its own `SKILL.md`. The playbooks live in each skill's `references/` folder.

## MCP

`Ironclad MCP - Corp Eng [Dev]` — used by legal review skills to scan and download contracts. Direct file upload works without it.
