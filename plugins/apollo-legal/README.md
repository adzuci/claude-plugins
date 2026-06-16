# apollo-legal

End-to-end contract review for Apollo's Commercial Legal team.

## Skills

- **`vendor-negotiation-support`** — Helps managers evaluate vendor renewals, pricing proposals, renewal dates, negotiation options, and vendor email responses before involving Procurement or Legal. Calls out to `vendor-contract-review` for legal review, redlines, or signability.
- **`vendor-contract-review`** — Reviews vendor contracts. Classifies into one of six categories, applies the Apollo playbook, generates a redlined Word document, and outputs a summary. Trigger phrases include "review this contract", "redline this vendor contract", "is this okay to sign". Excludes NDAs.
- **`nda-redline-monitor`** — Reviews Mutual NDAs. Detects counterparty paper vs. counterparty redlines to Apollo's template and routes accordingly. Trigger phrases include "review this NDA", "run the NDA monitor". One-way NDAs are not yet supported.

Each skill's full scope, prerequisites, and workflow live in its own `SKILL.md`. The playbooks live in each skill's `references/` folder.

## MCP

`Ironclad MCP - Corp Eng [Dev]` — used by legal review skills to scan and download contracts. Direct file upload works without it.
