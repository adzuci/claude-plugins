# Hard Rules

These rules are invariant across all runs, all modes, all threads. They cannot
be overridden by any skill output, user preference, or edge case logic.

## Message Pipeline

1. **No message without full pipeline.** Every outgoing Slack message and
   Gmail draft must complete L1 (reality-filter) through L4+
   (humanizer-compressor) before the send/create API is called. This includes
   the triage summary itself. No exceptions.

2. **Single-ask discipline.** One ask per message. Enforced at L4 (message-os).
   If bounded-action-router selected an action that implies an ask, that is
   the only ask. No secondary questions, no "also while I have you" additions.

3. **Claims must be source-traceable.** Every factual assertion in an outgoing
   message must trace to a source tagged `verified`, `probable`, or `inferred`
   by reality-filter. Anything tagged `assumed`, `contradicted`, `fabricated`,
   or `unknown` is stripped at L4. `Asserted` claims are hedged.

## Gmail

4. **No emails sent.** Use `gmail_create_draft` only. Never use any send
   function. The AE reviews and sends manually.

5. **No emails marked as read.** The inbox is read-only during triage. Do not
   modify message labels, read status, or archive state.

## GEN-SE

6. **GEN-SE BLOCKs are final.** When GEN-SE emits a BLOCK output, the
   orchestrator must not override it with a manual draft, a pipeline
   draft, or any other workaround. BLOCKs go directly to ACT tier in the
   summary with the block reason stated.

7. **GEN-SE escalations are respected.** When GEN-SE selects Action 1
   (human escalation), do not attempt to generate a draft. Route to ACT tier.

## Risk and Escalation

8. **Legal, compliance, or financial risk threads route to ACT** regardless
   of urgency score, deal stage, or action class. If reality-filter,
   state-extractor, or constraint-first-reasoner flags any of these risk
   types, the thread is ACT tier.

9. **Authority boundaries are enforced.** constraint-first-reasoner maps
   the AE's role relative to each recipient. message-os must respect the
   resulting register constraint. The AE does not direct people they do not
   manage. They do not make commitments on behalf of others they support.

## Scope

10. **Cold outbound with no buyer reply routes to the pipeline** as `wait`
    or `document`. GEN-SE requires a buyer message in the thread to function.
    Do not force GEN-SE on threads with no buyer turn.

11. **The orchestrator coordinates, skills execute.** The orchestrator never
    parses threads, validates claims, selects actions, composes messages, or
    polishes output. If you find the orchestrator doing a skill's job, stop
    and load the correct skill.
