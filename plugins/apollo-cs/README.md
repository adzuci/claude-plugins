# apollo-cs

Customer support skills for Apollo's Product Advocates and Tech Support reps — real-time peer assist for billing decisions, refund eligibility, escalation routing, and product issue guidance.

## Skills

- **`apollo-cx-peer-assist`** — Real-time peer assist for Apollo PAs and Tech Support reps handling live tickets. Answers billing and refund eligibility questions, routes escalations (Billing, Legal, Tech, Security), and covers common product/tech issues (AI credits, sequences, API, warmup). Reads from reference playbooks first, falls back to Notion MCP, then directs reps to `#ama-support-peer-assist` if neither source covers the scenario. Requires the Notion and Slack connectors. Trigger phrases: "can I process this refund", "do I need to escalate this", "how do I handle this ticket", "what is the policy on", "should I escalate", "customer is asking for a refund".

Each skill's full trigger phrases, scope, and workflow live in its own `SKILL.md`.
