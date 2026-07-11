# Glean Support Rep Assistant

Use this reference in `intro` and `live` when the customer asks a product, process, how-to, troubleshooting, or internal Support policy question.

## Source

Apollo Glean Support Rep Assistant:
`https://app.glean.com/chat/agents/90b93c53b44840d5b25a7836d4042304`

## Runtime

Prefer the local Glean CLI:

```bash
python3 scripts/ask_glean_support_rep_assistant.py --mode intro --question "<customer question>"
```

For questions that should be wrapped around Zendesk KB/IKB pages, pass:

```bash
python3 scripts/ask_glean_support_rep_assistant.py --mode intro --glean-assistant zendesk-kb --question "<customer question>"
```

The script calls:

```bash
glean agents run --json '{"agent_id":"90b93c53b44840d5b25a7836d4042304","input":{"query":"<question and context>"}}'
```

`--glean-assistant zendesk-kb` keeps the same Support Rep Assistant agent but asks it to ground the answer in Apollo Zendesk KB/IKB pages, include page titles or URLs when available, and say plainly when no matching KB page is found.

If `glean` is missing or unauthenticated, tell the user:

```text
Glean CLI is needed for exact Support Rep Assistant output. Install/authenticate it, then run `glean auth login` or set `GLEAN_API_TOKEN`.
```

You may use Glean MCP/search as a clearly labeled degraded fallback for general research, but do not call that output the Support Rep Assistant's answer.

## When To Call It

- Customer asks how a feature works.
- Customer asks why Apollo behaved a certain way.
- Customer needs troubleshooting steps or internal process guidance.
- You need source-backed product or Support process language before drafting a reply.

## When Not To Call It

- Customer-specific facts: use Intercom and GodMode/account tools.
- Billing authority, refunds, credits, exceptions, or legal/compliance decisions: route through Support escalation.
- Cases where the user only needs a recap of already-provided notes.

## Output Integration

Separate the Glean answer from customer-specific context:

```text
Support Rep Assistant finding:
<brief source-backed product/process answer>

Customer-specific verification still needed:
<Intercom/GodMode/account facts that are not proven by Glean>

Recommended customer language:
<paste-ready reply that combines verified context with the Glean-backed guidance>
```
