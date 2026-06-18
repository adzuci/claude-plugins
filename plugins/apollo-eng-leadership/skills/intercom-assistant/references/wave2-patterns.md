# Wave 2 Patterns

Use this reference when the user invokes `intro`, `deescalate`, or `macro-suggest`. Use `recap-recipe.md` for `recap`.

Source: Customer Care Rotation Wave 2 Notes, fetched June 17, 2026. Re-verify current Support process details before acting.

## Shared Rules

- Keep output concise, paste-ready, and operational.
- If the input includes an Intercom URL, conversation ID, customer email, customer name, company name, or company domain, use Intercom tools before making factual claims.
- If Intercom tools are unavailable, say the answer is not live-verified and ask for pasted context.
- Separate customer-facing copy from private notes.
- Do not invent account state, plan limits, permissions, outages, billing authority, product behavior, root cause, timelines, refunds, credits, or ownership.
- Do not auto-send, tag, close, snooze, route, or mutate Intercom.
- Offer a call when the customer seems stuck, confused, blocked, or screen sharing would resolve ambiguity faster.
- Prefer fact-based empathy. Do not infer emotions the customer did not state.

## Toolkit Order

When recommending the next check, use this order unless the user has already checked a source or the issue clearly requires a specific tool:

1. GodMode: account plan, flags, usage, permissions, and activity.
1. Glean/IKB: support process, known issues, standard procedures, and internal docs.
1. Apollo Agent: feature behavior and product Q&A.
1. Slack search: prior support threads or team-specific context.
1. `#ama-support-peer-assist`: only after the useful checks above are exhausted or blocked.

## `intro`

Use for first Intercom replies and first call openers.

Follow the opening flow:

1. Welcome: greet and set a helpful tone.
1. Verify: restate the concrete issue or what the customer appears to need.
1. Set expectations: say what you will check or how you will proceed.
1. Clarify and align: ask one concrete question to confirm the goal before troubleshooting.

Required fields: `Opening reply`, `Private check`, `Recommended first reply`, and `Next question`. Include the remaining diagnostic fields only when useful or available.

Output shape:

```text
Opening reply:
<paste-ready message>

Private check:
<what is known, what is assumed, and what still needs verification>

Customer / company:
<name, company, or not provided>

Plan tier / seats / ARR if available:
<source-backed account context or needs GodMode verification>

What is the customer asking for?
<one sentence>

What outcome are they trying to get?
<one sentence>

What have they already tried or been told?
<known attempts or not provided>

Is this a how-to, bug, billing, access, deliverability, or account setup issue?
<classification and confidence>

What account context matters from Intercom/GodMode?
<facts and missing checks>

Any recent related tickets or repeated friction?
<source-backed recent history or not checked>

Recommended first reply:
<paste-ready message>

Should I offer a call in the first response?
<yes/no and why>

If I get stuck, where should I escalate?
<tool, macro/workflow, or support channel>

Next question:
<one concrete clarifying question>
```

Keep the first message short enough for live chat. Include at most two questions. Do not offer a call by default; include it when a live walkthrough would materially help. After the first answer, use `call-nudges.md` when the customer is stuck, the UI state is unclear, or a screen share would be faster. If the customer asks a product/process/how-to/troubleshooting question, call the Glean Support Rep Assistant before writing factual guidance.

## `deescalate`

Use when the customer is upset, blocked, impatient, or has spent time troubleshooting.

Follow the de-escalation loop:

1. Align: acknowledge the concrete situation, time spent, urgency, or workflow impact.
1. Acknowledge: take calm ownership of the next step without assigning blame.
1. Act: move to one specific next check, reply, call, escalation, or follow-up.

Output shape:

```text
Customer reply:
<specific situation + ownership of next step + one check/action + call offer if useful + one clear next step>

What not to say:
<wording to avoid: blame, overpromises, projected emotions, or unsupported claims>

If they push back:
<one short follow-up that keeps the conversation moving>

Internal note:
<customer concern, what was acknowledged, and next step>
```

Avoid promises like "fully resolved today" unless that is verified and appropriate. Do not apologize for Apollo or product behavior unless Apollo has clearly made an error and the user asks for that stance.

## `macro-suggest`

Use when the user wants help selecting an Intercom macro/workflow or drafting a reusable macro body. Read `routing-and-macros.md` before proposing a macro or workflow.

Output shape:

```text
Best macro/workflow:
<known macro/workflow, closest category, or "confirm exact name in IKB">

Why:
<short rationale>

Required fields/context:
<fields to fill before applying, or context still needed>

Customer reply:
<paste-ready reply or "not needed">

Internal note:
<paste-ready internal note or "not needed">

Verification needed:
<IKB/source/tool check, or "none">
```

Macro/workflow guardrails:

- Apply the correct macro or internal note first for context, then run the workflow to route the conversation.
- If exact names are source-backed, use them. If names are image-only, uncertain, or missing, say to confirm the exact macro/workflow name in IKB.
- For Tech Support, confirm the product is behaving unexpectedly and the issue is not a billing/invoice problem before suggesting a Tech route.
- For Customer Advocate transfers, confirm no technical help is needed before suggesting CA transfer.
- For Billing or Billing Renewals, do not decide refunds, credits, downgrades, or account authority without verified policy/context.
- For External Fraud, preserve the two-step pattern when relevant: customer-facing macro first, then workflow after the customer responds.
- For `#ama-support-peer-assist`, include customer/account, issue, customer goal, what was checked, evidence, need help with, and urgency.

## Out Of Scope

Keep these out of Wave 2 v1 unless the user explicitly asks:

- `feedback`: polished training feedback from rough rotation notes.
- Full `escalate` decision engine beyond `macro-suggest` guidance.
- Intercom macro rotation, automatic routing, tagging, closing, snoozing, or mutation.
