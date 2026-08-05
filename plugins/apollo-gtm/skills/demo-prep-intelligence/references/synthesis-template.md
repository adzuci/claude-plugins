# Demo Synthesis Package Template

Use this template when the user asks for full synthesis, Apollo AI prompts, demo automation, setup walkthrough, talk track, or "how should the SC implement this demo?"

The seven-section Demo Prep Brief remains the Layer 1 intelligence contract. In this expanded mode, embed the full brief as Part 2. Do not remove confidence tags or sources.

````markdown
# Demo Synthesis Package: [Account Name]

Generated: [date] | Stage: [stage or Unknown] | ARR: [value or Unknown] | Close Date: [date or Unknown]
AE: [name or Unknown] | SC: [name or Unknown] | Segment: [segment or Unknown]

---

## Part 1: Strategic Angle

### Why Buy Anything?

[Describe the real business problem in customer language. Tie it to verified pains, consequences, and metrics. Use `[verified] Source:` labels for factual claims.]

### Before Scenario

[Describe their current-state workflow and why it is painful. Ground in the brief.]

### Negative Consequences

[List business consequences, operational drag, cost, risk, or missed revenue. Use verified metrics where available.]

### After Scenario

[Describe the desired future-state workflow once Apollo is in place. Tie each element to a verified or strongly inferred pain from the brief. This is analysis, not new evidence.]

### Why Buy Now?

- [Urgency driver tied to source]
- [Timing/event/contract/process driver tied to source]
- [Executive pressure or business initiative tied to source]

### Why Apollo?

[Name the highest-leverage Apollo differentiator for this deal. Make it deal-specific. If using deal-execution logic, preserve only claims supported by the brief.]

### Value Driver Mapping

| Customer pain | Value driver | Apollo capability | Demo moment |
|---|---|---|---|
| [pain] | [increase quality pipeline / reduce cost and complexity / improve productivity / reduce risk / other buyer-relevant driver] | [capability] | [specific show moment] |

### MEDDPICC Health Check

| Element | Status | Gap |
|---|---|---|
| Metrics | [Strong / Partial / Missing] | [gap or None] |
| Economic Buyer | [Identified / Inferred / Unknown] | [gap or None] |
| Decision Criteria | [Clear / Partial / Unknown] | [gap or None] |
| Decision Process | [Mapped / Partial / Unknown] | [gap or None] |
| Paper Process | [Documented / Partial / Unknown] | [gap or None] |
| Identified Pain | [Deep / Partial / Thin] | [gap or None] |
| Champion | [Validated / Possible / Unknown] | [gap or None] |
| Competition | [Known / Partial / Unknown] | [gap or None] |

This health check is a lightweight demo-prep assessment from available deal data. If deal-execution produces a MEDDPICC assessment for the same deal, defer to deal-execution as the authoritative qualification analysis. This skill's MEDDPICC check exists to shape demo prep, not to replace formal deal review.

---

## Part 2: Demo Prep Brief

[Insert the complete seven-section Demo Prep Brief here. Preserve the exact section order and all confidence/source labels.]

---

## Part 3: Apollo AI Context Center Calibration Payload + Demo Instance Setup Prompts

Part 3 has two ordered sections: **Step 0 — Apollo AI Context Center calibration payload** (mandatory, upstream) and **Steps 1..N — paste-ready Apollo AI prompts**. Render Step 0 first; never emit prompts without it.

Step 0 is an **Apollo AI calibration payload**, not a deal-prompt context blob. It is primarily about the prospect company's business — what they sell, who they sell to, their buyers' pains, their value prop, their competitors in their market, their proof, and the demo's CTA. Deal-specific calibration is a separate appended section. Step 0 must depend on the **Company + Business Understanding Gate** (defined in `SKILL.md`); if the gate fails, emit the Missing Business Context checklist instead of a payload, and do not generate prompts.

Use `references/apollo-ai-prompt-patterns.md` "Step 0: Apollo AI Context Center Payload" for the field-mapped payload contract, the validation checklist, and the placement-and-safety warning. Use the same reference for prompt patterns. Include:

- The Step 0 calibration payload — paste-ready, field-mapped to the observed Apollo Context Center UI hierarchy. The UI groups editable fields under non-editable section headers in this exact order: **Overview** (Company domain, Company name, Offering, Customer profile), **Key benefits & outcomes** (Pain points, Value proposition), **Unique characteristics** (Advantage over competitors, Primary competitors, Social proof), **Other details** (CTA), and **Additional information** (paste target only if the UI exposes a visible editable body field under it). Section headers are UI elements only — not paste targets. CTA is the editable child field under Other details, not a top-level field. Cancel / Save are page controls, never fields. Paste only into the editable child fields under each header. Then a separate Deal-specific calibration block (strategic angle, deal-specific buyer pains, the **prospect's own** product/service line to represent as a product card — never an Apollo product, see `prospect_product_card` in `references/apollo-ai-prompt-patterns.md`, hard blockers/landmines, buyer language, do-not-say, prompt interpretation instructions) is delivered outside the global Context Center — provided as a separate note for the SC to keep outside global fields, unless a visible editable Additional information / account-specific / demo-context field exists and the SC confirms scoping. Every editable company-profile field carries a source label and confidence tag; no `[assumed]` content in the editable company-profile fields.
- Paste-ready natural-language prompts for Apollo's in-app AI Assistant, generated **only after** the Context Center calibration payload has been rendered and the validation checklist has passed.
- A short "How to use" walkthrough: update the AI Context Center first (Step 0), then open Apollo, click AI Assistant, paste prompts one at a time, review before confirming actions.
- Prompts ordered by strategic priority, not by source system. Prompt ordering and emphasis must derive from the strategic angle identified in Part 1, reinforced by the Step 0 company-profile + deal-calibration payload.
- The first prompt should configure the demo element that maps to the primary "Why Apollo?" differentiator.
- Subsequent prompts should follow the Value Driver Mapping table priority.
- "Why this works" and "Demo talk-track hook" for each prompt. "Why this works" must note that Apollo AI is anchored to the Step 0 company-and-deal calibration — the prospect's offering, customer profile, and pains, plus the deal-specific strategic angle.
- Credit, side-effect, or confirmation warnings for prompts that may mutate data, create assets, enroll contacts, enrich data, or consume credits.
- MCP/tool-call examples only if the user explicitly asks for programmatic execution and the live connector schema has been verified.

### Step 0: Update Apollo AI Context Center

Render the Apollo AI Context Center calibration payload here using the field-mapped template in `references/apollo-ai-prompt-patterns.md` "Step 0: Apollo AI Context Center Payload". Render the company-profile fields under their observed section headers in this exact order — Overview (Company domain, Company name, Offering, Customer profile), Key benefits & outcomes (Pain points, Value proposition), Unique characteristics (Advantage over competitors, Primary competitors, Social proof), Other details (CTA), and Additional information (only as a paste target if the UI exposes a visible editable body field under it). Section headers are not paste targets. Then the Deal-specific calibration block (kept outside the global Context Center unless a visible editable Additional information / account-specific / demo-context field exists), then the placement-and-safety warning. Run the validation checklist. Do not skip this step. Do not introduce unverified or invented company facts. The skill drafts the payload; the SC pastes it into Apollo Settings → AI Context Center.

### How to Use These Prompts

1. **Update the Apollo AI Context Center first** (Step 0 above) in Apollo Settings → AI Context Center. Confirm placement (account-specific/session-level vs. global) before pasting any account-specific block.
2. Open Apollo.
3. Click **AI Assistant** in the top-right panel.
4. Paste each prompt into the chat box one at a time.
5. Review Apollo AI's proposed changes before confirming any action.
6. Run the dry-run prompt before the customer demo.

### Prompt 1: [Setup step name]

**Goal**: [what this prepares for the demo]

**Paste into Apollo AI**:
```text
[prompt]
````

**Why this works**: [why this setup maps to the strategic angle or a pain point]

**Demo talk-track hook**: "[what the SC can say when showing this element]"

**Confirmation note**: [if this may create, modify, enrich, enroll, or consume credits, say what to review before confirming]

______________________________________________________________________

## Part 4: SC Implementation Walkthrough

### Cue-card density rules (mandatory)

Part 4 is a live-execution aid, not a reading document. A wall of dense prose is unusable mid-demo, and an over-sparse outline gives the SC nothing to lean on. Encode these density rules so the walkthrough stays glanceable in front of a customer. These same rules govern the Run Sheet (Part 4's compiled sibling), so keep them consistent.

- **One screen per block.** Each demo moment / segment is a self-contained block the SC can absorb in a single glance — no scrolling within a moment. If a block does not fit one screen, split it.
- **Time markers on every block.** Prefix each block with a wall-clock or elapsed marker (e.g. `[0:00–0:05]`, `[open]`, `[~15 min in]`) so the SC always knows where they are in the call.
- **Short cue lines, not paragraphs.** Cue lines are terse imperatives or one-line hooks (≤ ~15 words). Move any supporting rationale to a collapsed "why" note; it must never crowd the cue line the SC reads live.
- **Inline landmine responses.** Put the response to a known landmine directly beside the moment where it is likely to surface — not in a separate section the SC has to hunt for mid-call.
- **PASTE blocks are clearly delimited and copy-ready.** Anything the SC pastes live (an Apollo AI prompt, a phrase, a link) is in a fenced, labeled `PASTE:` block, self-contained, with no surrounding prose to accidentally copy. A `PASTE` block must never contain an `[assumed]` company fact.
- **Confidence stays out of the cue line.** Do not tag every line inline (that recreates the density problem). Verified content flows clean; only cue lines resting on `[assumed]` or `[inferred]` premises carry a short inline flag.

### Pre-Demo Checklist

- [Concrete prep step]
- [Concrete prep step]
- [Concrete prep step]

### Demo Day Execution Order

| Order | What to show | Why from brief | Talk-track hook |
|---|---|---|---|
| 1 | [capability / screen / workflow] | [pain or decision criterion] | "[phrase the SC can use]" |

### Handling Known Landmines

- **[Landmine]** — [how to handle it, what to say, and what not to promise]

### Phrases to Use

- "[phrase]"
- "[phrase]"

### Phrases to Avoid

- "[phrase or claim to avoid]"
- "[phrase or claim to avoid]"

______________________________________________________________________

## Part 5: Post-Demo Recommended Actions

These are recommendations only. Do not write to SFDC, Slack, email, or Apollo from this skill. **One exception, and it is mandatory:** rendering this synthesis package triggers `SKILL.md`'s Terminal Output Assertion condition (c) — its exact content must be written to the session scratchpad `demo-prep-scratchpad.md` (see `GOVERNANCE.md`), which is how `demo-instance-configuration` picks it up. That write is not optional and not a real-system write.

1. **[Action]** — [why it matters]
1. **[Action]** — [why it matters]
1. **[Action]** — [why it matters]

If the user wants drafts, SFDC updates, Slack recaps, or execution, hand off to deal-execution.

```

## Synthesis Rules

- Part 1 is analysis, not new evidence. It must not introduce unsupported factual claims.
- Part 1 uses Command of the Message-style constructs natively inside this template. It does not require loading deal-execution unless the user explicitly asks for the GTM router or full pipeline.
- Part 2 is the source-of-truth brief. Preserve sources and confidence tags.
- Part 3 begins with Step 0 — the Apollo AI Context Center **calibration payload** — and then renders paste-ready natural-language Apollo AI prompts. Step 0 calibrates Apollo AI on the prospect company's business using the field-mapped Apollo UI template under its observed section headers: Overview (Company domain, Company name, Offering, Customer profile), Key benefits & outcomes (Pain points, Value proposition), Unique characteristics (Advantage over competitors, Primary competitors, Social proof), Other details (CTA), and Additional information (paste target only if the UI exposes a visible editable body field under it). Section headers are not paste targets. The Deal-specific calibration block is delivered outside the global Context Center unless the UI exposes a visible editable Additional information / account-specific / demo-context field and the SC confirms scoping. The Company + Business Understanding Gate must pass first; if it fails, render the Missing Business Context checklist instead and do not emit prompts. Prompt order must inherit from Part 1's strategic angle and value driver priority. The Context Center payload is the upstream context that conditions Apollo AI's interpretation of every prompt; never emit prompts without it, and never emit prompts against an ungrounded or invented Context Center. The skill itself remains read-only and does not execute the prompts or update the Context Center.
- Part 4 should be practical enough for an SC to run the demo, but it is not a verbatim script.
- Part 5 may recommend updates or recaps, but must not draft or execute them unless another skill is explicitly invoked.

## Run Sheet (optional 5th artifact)

The **Run Sheet** is an OPTIONAL fifth output mode, offered after a synthesis package exists (see `SC-GUIDE.md` for the trigger and menu entry). It is a **compilation, never a new source**: it merges Part 3 (Apollo AI prompts / setup) and Part 4 (implementation walkthrough) into a single time-blocked, in-call sheet the SC keeps open during the live demo. Adding the Run Sheet does NOT change the seven-section brief or the five-part synthesis package — both remain byte-stable; the Run Sheet is generated alongside, not by rewriting them.

### Format

The Run Sheet obeys the **cue-card density rules** in Part 4 above (one screen per block, time markers on every block, short cue lines, inline landmine responses, delimited PASTE blocks). Structure it as an ordered sequence of time-blocked moments; each moment carries its cue line, any inline landmine response, and any PASTE block (Apollo AI prompt or phrase) needed at that moment.

### Epistemic rule (governs the Run Sheet — supersedes tag-every-line)

Tagging every cue line inline makes the sheet too dense to use live. Instead:

- **Header declaration (once, at the top):** *"All claims below derive from the Demo Prep Brief generated [date]. Review the brief for full source and confidence annotations."*
- **Tag ONLY the exceptions inline:** a cue line resting on an `[assumed]` or `[inferred]` premise carries a short inline flag; an `[assumed]` premise must state the assumption. Verified claims flow clean (no inline tag).
- **`[assumed]` company facts are barred from PASTE blocks** (extends the SKILL.md rules against `[assumed]` content in pasteable payloads). A prompt the SC pastes into Apollo AI in front of the buyer is the highest-damage place for an unverified claim.
- **No new claims.** No claim may appear in the Run Sheet that is not already present in Part 2 (the brief) or Part 4 (the walkthrough). The Run Sheet compiles; it never introduces evidence.

### Scope boundary (state explicitly)

The Run Sheet is a **pre-call artifact**, frozen at generation time. Mid-call guidance from live transcript drops (e.g. a Granola/live-transcript feed during the meeting) is a **separate interaction mode handled by the skill's conversational layer — NOT by regenerating the Run Sheet.** The "no new claims" rule is correct precisely because the Run Sheet is frozen pre-call; live evidence flows through the conversational layer instead. Do not attempt to hot-patch the Run Sheet from a live transcript.

### Preconditions

- Requires an existing synthesis package (specifically Parts 3 + 4) to compile from.
- Inherits a **gate-passed** Context Center payload: any PASTE block containing an Apollo AI prompt must come from a payload that already passed the Visible Gate Block for the Company + Business Understanding Gate. A Run Sheet must never carry a prompt built on an ungrounded or failed-gate Context Center.
- Read-only: the Run Sheet is a copy-target for the SC; it sends and posts nothing. (The mandatory `demo-prep-scratchpad.md` write is triggered by the underlying brief/synthesis/Context Center render, not by compiling the Run Sheet — see the note above.)
```
