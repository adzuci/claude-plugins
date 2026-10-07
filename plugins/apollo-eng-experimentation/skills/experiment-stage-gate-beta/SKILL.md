---
name: experiment-stage-gate-beta
description: >-
  BETA. Walks the experiment DRI through a lifecycle stage gate, one checklist
  item at a time. Gathers the stage's artifacts for context, explains each item
  in plain terms, lets the DRI say whether it is done, digs into the artifacts
  only when they say no or unsure, and offers next steps for anything not
  there yet. Chat only; writes nothing. Not for producing the artifacts it
  checks.
disable-model-invocation: true
metadata:
  lifecycle-stage: Discovery, Execution, Impact
---

# Experiment Stage Gate

Lifecycle stages: **Discovery, Execution, Impact**, one gate at the end of
each. This file is the same for every gate; each gate's items live in
`references/<gate>-gate.md`. Follow
`${CLAUDE_PLUGIN_ROOT}/references/experiment-lifecycle-conventions.md` for how
to check tools, teach, review, and close; the opening message is this skill's
own, below.

A gate is a checklist the DRI and the skill review together, one item at a
time. The skill reads the stage's artifacts first; for each item it says what
the item means and where the experiment stands, and the DRI confirms, corrects,
or asks to dig in. Their answer is the status. It ends with a summary the DRI
can share and the recommended next steps. The skill never judges the business
merit of the experiment and adds no items of its own.

## Invocation

```text
/apollo-eng-experimentation:experiment-stage-gate-beta <gate> <Experiments DB entry URL> [artifact links]
```

`<gate>` is `discovery`, `execution`, or `impact`. Arguments are optional;
intake asks for anything not passed.

## Open

This skill replaces the conventions' opening message with its own. No beta
preamble. If the gate was not given, ask for it and the DB entry link in one
message. Otherwise open with the purpose line and go straight to item 1:

```text
**<Gate> gate: <experiment>**
This checks whether the experiment is ready to move from <stage> into <next stage>.
We will go through the <N> things an experiment should have in place by the end
of <stage>, one at a time.
```

- **Produces:** a walk through the gate's items with the DRI, then a shareable
  summary (verdict, one line per item) and recommended next steps.
- **Does not:** size or power the experiment (`experiment-pre-analysis-beta`);
  inventory its events (`experiment-analytics-audit-beta`); decide where
  exposure fires (`experiment-exposure-design-beta`); write to Notion, the
  team's tracker, or code.

## Preflight

- **Notion MCP** is required: the Experiments DB entry is the one artifact every
  gate reads.
- **A way to read artifacts outside Notion**, when the DB entry links to one: a
  Jira or Atlassian MCP, `acli`, or Glean's `read_document` on the URL. Without
  one, those artifacts are the DRI's word.

## Inputs

1. **The gate** (`discovery`, `execution`, or `impact`). It selects
   `references/<gate>-gate.md`.
1. **The Experiments DB entry** (URL, in the Growth & Acquisition Experiments
   DB; the DB entry from here on). Required at every gate: if none exists, say
   so, point at the DB's "New" button and its default template, and stop. An
   entry in the older Product Experiment DB is not this DB.
1. **Links to the stage's other artifacts**, if the DB entry does not already
   carry them. Ask once, in one message, for what the gate's reference lists
   and you could not find. Missing ones are fine; they become "unsure" answers
   later, not blockers now.

## Flow

1. **Gather context, quietly.** Read the DB entry and the artifacts the gate's
   reference lists. Do not report what you found yet.

1. **Check the DB entry is filled for this stage.** The gate's reference says
   which parts of the DB entry this stage depends on. If any are empty or still
   template text, say so in one short message and ask the DRI to fill them
   before continuing.

1. **Open**, then walk the items **one per message**, in order. Each message:

   ```text
   **<n> of <N>: <Item title>**
   **What this means:** <the reference's "What this means" text, verbatim.>
   **Complete when:** <the reference's "Complete when" text, verbatim.>
   **Status: <completed / partial / missing / couldn't verify>.** <One or two
   lines on what you found and where.>

   Do you agree with this status? Anything here you want to dig into?
   ```

   - **Confirmed:** that is the status. Next item.
   - **Corrected:** take their status. If they say completed, it is completed;
     if they say it is not, treat it as a dig-in.
   - **Dig in:** ask one or two of the reference's clarifying questions, share
     more of what you found as it helps, and settle the status together. If it
     is not completed, give the reference's "What can help" as a short list.
     Then the next item.

1. **Hand over** the summary and next steps.

## How to work

- **The DRI's answer is the status.** You propose from the documents; they
  decide. If their correction plainly contradicts what you read, ask one
  question; their answer stands.
- **One item per message.** Never present the whole checklist at once, and
  never ask about two items in one message.
- **Keep each item short.** Three labeled lines: what it means, when it is
  complete, status. A completed status gets one sentence of evidence ("no
  open tickets, bug bash done, sign-offs in"), not an inventory. Detail waits
  until the DRI asks to dig in.
- **Teach lightly.** "What this means" is the teaching. Read it from the
  reference as written so every DRI hears the same thing. The reference's
  "More, if asked" paragraph, where one exists, comes out only during a
  dig-in or when the DRI asks why an item matters.
- **Do not assign owners.** "What can help" says who usually helps; offer it as
  a suggestion, do not ask the DRI to name people.
- **Speak the DRI's language.** Assume no shared vocabulary. Name a skill by
  its full slash command, never "the audit skill". Call things from their
  documents exactly what the documents call them, never a shortened form you
  made up. Keep the reference's working terms (decision, learning, and
  treatment events; symmetry risk) out of chat; say what they mean instead,
  such as "the events behind your primary, secondary, and guardrail metrics".
  When a term of art is unavoidable, say what it means in the same sentence.
  "Tracker" is one of these internal words: in chat, name the tool the team
  actually uses when a document names it ("your Jira epic ACT-1234"), and
  otherwise say "wherever you track the work".
- **Substance, not structure.** Items are about what the team knows, not which
  heading it sits under. Templates and processes differ by team.
- **Say what you did not check, and how it can be closed.** When a status
  rests on something you could have verified but did not, say so plainly
  ("the A/A flag exists in code, so it likely ran, but I have not looked for
  its results"), then offer the ways that apply: you can go look, if a tool
  can reach it; the DRI can point you at it, if it exists somewhere; and the
  DRI's explicit yes always closes it. Never leave "I have not seen it"
  hanging without a way forward.
- **Never invent** a number, event, or finding. Pull it or say you could not.
  A search hit is not a finding: do not mention a ticket, incident, or
  document as related to the experiment unless you opened it and it says so.

## Hand over

Two parts, in one message. The first is written to be pasted into Slack or the
DB entry as is, so it carries no questions, no mechanics, and no "I".

```text
**<Gate> gate: <experiment>** (<date>)
Ready for <next stage>: <yes / not yet>. <One line on why.>

1. <Item title>: <status>. <One line.>
2. ...

**Recommended next steps**
- <For each item not completed: the step, and the skill, guide, or role that helps.>
```

Statuses: **completed**, **partial**, **missing**, **couldn't verify**. The
verdict is **yes** only when every item is completed. When the gate's
reference carries a verdict note and its condition holds, it goes in the "why"
line. Next steps come from the reference's "What can help" for the items that
are not completed, in the order the DRI should take them; none if everything is
completed.

Nothing is written anywhere. If the DRI wants the summary on the DB entry or in
Slack, they paste it.

## Review

The conventions' silent review, plus:

- Every status came from the DRI's answer or from a document you opened in
  this run.
- No item was marked from a document you did not open.
- Every recommended next step is something the DRI can act on now.
- The summary reads cleanly on its own when pasted elsewhere.

## Never

- Write to the Experiments DB entry, the team's tracker, Notion, or code.
- Present the whole checklist at once, or ask about more than one item per
  message.
- Overrule the DRI's "done".
- Judge the hypothesis, the metric choice, or the ROI; raise a concern as a
  teaching note and leave the call with the PM.
- Produce a plan, audit, or ERD yourself.
- Use shorthand for a skill, a document, a metric, or an event; use the full
  name as the DRI's documents or the skill's invocation give it.
- Add an item the gate's reference does not list.
- Run a gate without its reference file.

## Reference files

Paths relative to this skill's folder. One file per gate,
`references/<gate>-gate.md`, each with: the artifacts the gate reads, which
parts of the DB entry this stage depends on, and per item: what it means in
"What this means" and "Complete when" text read to the DRI verbatim, the
clarifying questions for a dig-in, and what can help.

### Discovery

- `references/discovery-gate.md`: the Discovery to Execution gate (five items).

### Execution

- `references/execution-gate.md`: the Execution to Impact gate (six items).

### Impact

- TODO
