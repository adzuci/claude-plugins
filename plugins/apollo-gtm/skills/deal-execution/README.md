# Apollo GTM Execution System

A composable AI skill system for solutions consultants and account executives built on a six-layer reasoning architecture. Designed for deal execution where getting it wrong costs something.

**Version:** 3.3.0

## What This Is

A self-contained sales execution system that runs inside Claude. It integrates three frameworks into one unified operating layer:

- **Command of the Message** for how you communicate value and differentiate
- **Apollo Sales Process** (7 stages with SFDC gating) for where you are and what to do next
- **MEDDPICC** for whether the deal is real and where the gaps are

These frameworks are wired together, not stacked. Discovery questions validate MEDDPICC fields. Required Capabilities shape Decision Criteria. Stage progression requires real deal validation, not activity completion.

## Architecture

| Layer | Purpose |
|---|---|
| Pipeline (L1-L3) | Analyze input, assess truth, extract state, map constraints, route actions |
| GEN-SE (L4-sales) | Process sales email threads into safe reply drafts or escalations |
| Orchestrators | End-to-end workflows: inbox triage, post-call follow-up |
| References | Sales methodology, process, qualification, product knowledge |
| Execution | Gmail drafts, Slack posts, Calendar reads, Drive exports via MCP |
| Utilities | Task tracking, data test runner, local config persistence |

## Key Capabilities

- Deal review and stage validation against SFDC exit criteria
- Discovery prep with framework-linked question generation
- Sales email processing with epistemic safety (no hallucinated claims)
- AM/PM inbox triage across Gmail, Calendar, Slack, and Apollo
- Post-call follow-up composition grounded in transcript evidence
- Competitive positioning and objection handling
- MEDDPICC gap analysis and champion validation
- Technical feasibility checks with hard blocker detection

## Getting Started

Load as a Claude skill. Run `PREFLIGHT.md` first for setup and connection verification. Then use `ROUTER.md` for all runtime work. It classifies tasks and tells you which files to load.

## License

