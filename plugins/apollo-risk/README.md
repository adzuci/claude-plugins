# apollo-risk

Privacy and compliance skills for Apollo's Legal Risk team — DSR response drafting, privacy queue triage, and regulatory compliance workflows.

## Skills

- **`dsar-response-drafter`** — Handles data subject requests (DSRs) under GDPR, CCPA/CPRA, and other privacy frameworks. Operates in two modes: **Queue Scan** (surfaces open, unassigned access requests from Apollo's Privacy inbox in Intercom, sorted by urgency) and **Draft Response** (produces a legally grounded, ready-to-review response email for a specific request). Classifies request types, checks escalation triggers, calculates response deadlines, and applies Apollo-specific context (legal basis, data sources, recipient disclosure rules). Requires the Intercom connector. Trigger phrases: "draft a DSR response", "data subject request", "DSAR", "check the Privacy queue", "GDPR request", "CCPA request", "right to erasure", "privacy deletion request", "what's open in the Privacy queue". Does not trigger on generic "access request" / "deletion request" phrasing (tool access, file deletion) — only data-subject privacy requests.

Each skill's full trigger phrases, scope, and workflow live in its own `SKILL.md`.
