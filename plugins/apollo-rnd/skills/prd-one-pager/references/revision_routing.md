# Revision Routing

How the PRD One-Pager Skill detects drafts, classifies revision requests, and routes to the correct behavior.

______________________________________________________________________

## Detecting that a draft exists

Check conversation history for either of these strings:

- `STATE: PRD_DRAFT_READY`
- `STATE: PRD_REVISION_READY`

If either is present → skip intake entirely, enter revision mode.

If neither is present → run intake (Step 2 of SKILL.md).

Edge case: if the user pastes a PRD draft directly without a STATE tag, treat the pasted content as the current draft and enter revision mode. Do not run intake.

______________________________________________________________________

## Classifying a revision: YES (search needed) vs NO

After detecting that a draft exists, classify the user's message before responding.

### YES — run targeted search

Trigger YES when the user:

| Signal | Example |
|--------|---------|
| Asks to find or locate something | "find the adoption data for sequences" |
| Asks to verify or confirm a claim | "is it true that X% of AEs use sequences daily?" |
| Asks to cite or add a source | "can you add a citation for that" |
| Asks for proof points or evidence | "what evidence do we have for the JTBD?" |
| Asks for metrics, data, or numbers | "add reply rate data" / "what does Amplitude show?" |
| Asks for Amplitude / Hex analysis | "pull the Hex dashboard for sequences" |
| Asks for Enterpret themes or VoC | "what are the top Enterpret themes for this area?" |
| Introduces a new unverified factual claim | "I heard that 60% of enterprise deals close faster with sequences — can you add that?" |

### NO — revise from existing content

Trigger NO when the user:

| Signal | Example |
|--------|---------|
| Asks for structural changes | "move requirements before the solution section" |
| Asks for shortening or tightening | "this is too long, cut it by a third" |
| Asks for tone changes | "make it more executive-friendly" |
| Asks for renaming or relabeling | "rename 'Proposed Solution' to 'What We're Building'" |
| Asks for reframing | "reframe the problem around the AE persona instead of SDRs" |
| Asks for prioritization changes | "deprioritize requirement #3 and promote #5" |
| Asks for a variant of existing content | "write me a version of this for a leadership review" |

### Bias rule

If the classification is ambiguous, treat it as **YES** and run a targeted search. The cost of a targeted search is low. The cost of adding an unverified numeric or customer claim to the PRD is high.

______________________________________________________________________

## Behavior on YES

1. Identify exactly what evidence or source is needed — be specific, not broad.
1. Run a targeted search for only that evidence. Do not restart the full research pass.
1. Revise the relevant sections of the draft using new findings.
1. Leave unchanged sections unchanged — do not rewrite the whole document unless asked.
1. Include a "What changed" section:
   - What sections were updated
   - What was found (source name and what it showed)
   - What was not found (and how it was handled: ASSUMPTION label or omitted)
1. Include the **Review note** verification reminder at the top of the revised draft (new evidence was added).
1. End with `STATE: PRD_REVISION_READY`.

______________________________________________________________________

## Behavior on NO

1. Apply the requested edits directly using the existing draft content.
1. Do not search for new evidence unless it becomes necessary mid-edit.
1. Include a "What changed" section listing the edits made.
1. Skip the **Review note** unless new factual claims, metrics, or citations were introduced during the edit.
1. End with `STATE: PRD_REVISION_READY`.

______________________________________________________________________

## Fallback behavior

| Situation | Action |
|-----------|--------|
| User says "new initiative" or "start over" | Reset. Run intake from the beginning. |
| User pastes a new PRD topic mid-conversation | Ask one clarifying question: "Is this a new initiative or a follow-up to the current draft?" |
| User provides conflicting feedback | Implement the most recent instruction. Note the conflict in "What changed." |
| Search returns nothing useful | Proceed without the evidence. Label claims ASSUMPTION or [NEEDS INPUT:]. Note what wasn't found in "What changed." |
| User asks 2+ distinct revisions at once | Apply all in one pass. List each in "What changed." |
| Connector (Amplitude, Hex, Enterpret, Notion, Drive, Slack) appears unavailable | Do **not** default immediately to manual paste. Tell the user which connector failed, instruct them to check Settings → Connections, and if the connector is not visible tell them to contact the Apollo Claude admin. Ask the user to rerun after enabling. Only offer manual fallback if the connector cannot be enabled. |

______________________________________________________________________

## Question discipline in revision mode

- Default: 0 questions.
- If blocked (cannot complete the revision without clarification): ask at most 2 targeted questions.
- Never ask the full intake questions again.
- Never ask questions just to appear thorough — if you can make a reasonable call, make it and note it in "What changed."
