---
initiative: {{INITIATIVE}}
run_id: {{RUN_ID}}
stage: {{STAGE}}            # A.audit | B.research | C.specify | D.design | E.review | F.<slice>.build | G.verify | council.<slug>
persona: {{PERSONA}}         # persona that produced this snapshot; A.context grill validation uses this value
as_of: {{ISO_TIMESTAMP}}
produced_by: {{AGENT_NAME}} on {{FAMILY}}/{{MODEL}}
supersedes: {{PATH_OF_PREVIOUS_SNAPSHOT_OR_none}}
inputs:
  - path: {{PATH}}
    sha256: {{HASH}}
  - url: {{URL}}
    retrieved: {{DATE}}
    tier: P | S | U
notion: {{NOTION_PAGE_URL}}       # required: the human-readable page (templates/notion-page.md) under the initiative's notion_parent; a snapshot without it is not done. `blocked: <reason>` only when the Notion connector is unavailable, and then the next session publishes it first
jira: {{KEY-123 | blocked: reason | omit for notion-only profiles}}   # required when updates.tracker is jira or both
human_gate: {{GATE_ID_OR_none}}   # e.g. G2b; status below
gate_status: open | passed | rejected | n/a
---

## Facts established

| Fact | Source |
|---|---|
| | path:line / URL+date+tier / "asserted by <who>, <date>" |

## Decisions

| Decision (imperative) | Why | Alternatives rejected (and why) | Consequences |
|---|---|---|---|

## Options handed to the human (if any)

| Option | Trade-offs | Evidence | Recommendation |
|---|---|---|---|

## Checks

| Check | Pass/Fail | Evidence |
|---|---|---|

## Open questions

| Question | Owner (or `unowned`) | Blocked on |
|---|---|---|

## Artifacts written

- path — one line on what changed

## Loop report

Build, fix and council stages only (doc 46 §6); wall-clock minutes from tool timestamps. Name any breach of doc 46 on the next line.

Loop report: build {{M}} min · tests {{M}} min ({{N}} runs, {{K}} full) · mutation {{M}} min ({{N}} mutants) · review {{M}} min ({{N}} passes, {{TOKENS}} tokens, {{CHARS}} prompt chars) · fix-loop {{M}} min ({{N}} loops) · total {{M}} min, {{TOKENS}} tokens

## Mirrors

| Mirror (Notion page, PR body, Slack) | Updated | Read back |
|---|---|---|

## Reconciliation

Conflicts between the conversation, agent reports, and disk, and how they were resolved.

## Next stage needs

What the next stage must read from here, in one list.
