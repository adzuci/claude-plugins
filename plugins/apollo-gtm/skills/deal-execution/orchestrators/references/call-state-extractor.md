# Apollo Call State Extractor

Parses raw sales call transcripts into structured deal state for downstream use by the follow-up email engine. This is a parsing tool — it describes what is, not what to do about it.

> **Note:** The Command of the Message concepts referenced throughout this document — Before Scenario, Negative Consequences, After Scenario, Positive Business Outcomes (PBOs), and Required Capabilities — are defined in full in `references/methodology.md`. Refer there for framework definitions and usage guidance.

---

## When to Use

Run this extractor when the user provides:
- A full call transcript (from Gong, Chorus, Fireflies, Otter, etc.)
- A partial transcript or recording summary
- Raw call notes (unstructured)
- Any combination of the above

The extractor produces a structured state object that the follow-up email engine consumes. The user should verify the extraction before the engine composes.

---

## How to Run

Read the full input. Execute the following steps in order.

### Step 1: Classify the Input

Determine:
- **Input type:** full_transcript / partial_transcript / recording_summary / raw_notes / mixed
- **Input quality:** rich (lots of detail, clear speakers) / adequate (enough to extract from) / thin (missing significant context)
- **Speaker identification:** Can you distinguish the Apollo rep from the prospect(s)? If not, flag it.

If input quality is **thin**, stop after Step 1. Tell the user what's missing and what additional context would produce a useful extraction. Don't extract from insufficient data.

### Step 2: Identify Actors

Extract every identifiable person from the input.

| Field | Description |
|---|---|
| name | As stated or identifiable |
| role | Apollo rep / prospect (primary) / prospect (additional stakeholder) / unknown |
| title | Job title if stated |
| company | Company if stated |
| signals | What they seem to care about, based on what they said — not what you infer about their personality |

**Rules:**
- Only assign roles you can support from the text
- If you can't tell who's the rep and who's the prospect, flag it in parser notes
- Preserve the distinction between "they said their title is VP Sales" (stated) and "they seem senior based on their questions" (inferred)

### Step 3: Extract Deal State

For every field below, mark the epistemic status:
- **stated** — someone said it directly on the call
- **inferred** — reasonable conclusion from context, not directly said
- **missing** — not in the input

```yaml
deal_state:
  company:
    name: string | missing
    status: stated | inferred | missing
    headcount: string | missing
    headcount_status: stated | inferred | missing
    industry: string | missing
    industry_status: stated | inferred | missing

  segment: small_smb | mid_smb | large_smb | unknown
  segment_basis: string  # what signals led to this classification

  current_state:  # Command of the Message: Before Scenario
    prospecting_motion:
      value: string | missing  # inbound / outbound / mix / unclear
      status: stated | inferred | missing
    current_tools:
      items:
        - tool: string
          status: stated | inferred
      # list every tool, CRM, provider, or platform mentioned
    team_structure:
      value: string | missing  # who does prospecting — SDRs, AEs, founder, etc.
      status: stated | inferred | missing
    team_size:
      value: string | missing
      status: stated | inferred | missing
    process_description:
      value: string | missing  # how they actually work day-to-day
      status: stated | inferred | missing

  pain_points:  # Command of the Message: Before Scenario + Negative Consequences
    items:
      - pain: string  # in their exact words when possible
        status: stated | inferred
        speaker: string  # who said it
        negative_consequence: string | null  # what happens if this doesn't change
        consequence_status: stated | inferred | null
        severity: high | medium | low | unknown  # based on emphasis, repetition, emotion
    # ONLY include pain points grounded in the input.
    # If nobody expressed frustration, this section can be empty.

  desired_outcomes:  # Command of the Message: After Scenario
    items:
      - outcome: string
        status: stated | inferred
        speaker: string

  apollo_fit:
    capabilities_discussed:
      items:
        - capability: string  # data, sequences, workflows, dialer, inbox, AI, enrichment, etc.
          status: stated | inferred
          interest_level: high | medium | low | neutral
          # high = asked follow-up questions, said "that's what we need," visible excitement
          # medium = engaged, asked clarifying questions
          # low = acknowledged but moved on
          # neutral = mentioned by rep, no visible reaction from prospect
    value_driver_category: revenue_growth | cost_efficiency | productivity_execution | risk_compliance | strategic_advantage | multiple | unclear
    value_driver_basis: string  # what in the call tells you this

    hooks_landed:  # moments of genuine interest
      items:
        - moment: string  # describe what happened
          status: stated | inferred
          prospect_words: string | null  # exact quote if available

    champion_signals:
      quote: string | null  # exact words if available
      quote_type: verbatim | paraphrased | null
      champion_potential: high | medium | low | none_identified
      basis: string  # what makes you think they could be a champion

  deal_mechanics:
    pricing:
      discussed: boolean
      details: string | null  # plan, seats, term, amount — whatever was said
      status: stated | inferred | missing
    objections:
      items:
        - objection: string
          status: stated | inferred
          category: price | data_quality | adoption | switching_cost | security | integration | timeline | authority | other
          addressed_on_call: yes | partially | no
          resolution: string | null  # how it was addressed, if at all
    stakeholders:
      items:
        - name: string | null
          role: string | null
          status: stated | inferred
          involvement: decision_maker | influencer | evaluator | blocker | unknown
    decision_timeline:
      value: string | missing
      status: stated | inferred | missing
    competitors:
      items:
        - name: string
          status: stated | inferred
          context: string  # what was said about them
      competition_status: active_evaluation | apollo_only | unclear | not_discussed

  meddpicc:
    metrics:
      value: string | missing
      status: stated | inferred | missing
    economic_buyer:
      identified: boolean
      name: string | null
      role: string | null
      status: stated | inferred | missing
    decision_criteria:
      value: string | missing
      status: stated | inferred | missing
    decision_process:
      value: string | missing
      status: stated | inferred | missing
    paper_process:
      value: string | missing
      status: stated | inferred | missing
    identify_pain:
      value: string | missing  # core business pain in their words
      status: stated | inferred | missing
    champion:
      value: string | missing
      validation_level: validated | potential | none
      status: stated | inferred | missing
    competition:
      value: string | missing
      status: stated | inferred | missing

  next_steps:
    agreed:
      items:
        - step: string
          owner: string | null  # who's doing it
          deadline: string | null
          status: stated  # agreed steps must be stated, not inferred
    implied:
      items:
        - step: string
          basis: string  # why you think this is a logical next step
          status: inferred
    follow_up_deadline: string | missing

  ps_material:  # personal, non-deal moments worth referencing
    items:
      - moment: string
        context: string  # why it's usable for a PS note
```

### Step 4: Extract Verbatim Quotes

Scan the transcript for exact prospect quotes worth preserving. These are high-value for email personalization.

**What to capture:**
- Pain statements in their own words ("we're drowning in..." / "our reps waste half their day...")
- Excitement moments ("that's exactly what we need" / "if it could do that, we'd be interested")
- Objection language ("my concern is..." / "the problem with tools like this is...")
- Decision context ("my boss would need to see..." / "we'd want to pilot first")

```yaml
verbatim_quotes:
  items:
    - quote: string  # exact words
      speaker: string
      context: string  # what prompted this
      category: pain | excitement | objection | decision | other
      usable_in_email: boolean  # is this appropriate to echo back?
```

**Rules:**
- Only capture actual quotes, not paraphrases. If you're not confident in the exact wording, don't include it.
- For recording summaries where exact words aren't available, skip this section and note it in parser notes.

### Step 5: Assess Extraction Quality

Rate the overall extraction:

```yaml
extraction_quality:
  overall: high | medium | low
  confidence_notes:
    - string  # what you're most/least confident about
  thin_areas:
    - string  # fields where you had to infer heavily or leave missing
  enrichment_suggestions:
    - string  # what additional context would improve the extraction
  parser_notes:
    assumptions:
      - string  # structural assumptions you made
    ambiguities:
      - string  # things that could be read multiple ways
    dropped_noise:
      - string  # content you intentionally excluded and why
```

---

## Extraction Rules

These are non-negotiable:

1. **Never invent pain.** If nobody expressed frustration, the pain_points section can be empty. An empty field is better than a fabricated one.

2. **Never inflate interest.** Polite acknowledgment is not excitement. "That's interesting" at neutral energy is `low` interest, not `high`.

3. **Preserve exact language.** When the prospect uses a specific phrase, capture it verbatim in the quotes section. These drive email personalization.

4. **Stated vs. inferred is the most important distinction.** This determines what the email engine can assert as fact vs. what needs hedging language. Get this right.

5. **Objections are signal, not noise.** Capture every one. The email engine decides which to address.

6. **Don't over-extract from thin input.** A 5-minute recording summary should not produce the same field density as a 45-minute full transcript. Mark fields missing rather than forcing inferences.

7. **Speaker attribution matters.** "The prospect said data quality is important" is very different from "the Apollo rep said data quality is important." Track who said what.

8. **Map to Command of the Message naturally.** The extraction schema maps to CoTM concepts (Before Scenario, Negative Consequences, After Scenario, PBOs, Required Capabilities — see `references/methodology.md` for full definitions). Don't force the mapping — if something doesn't fit cleanly, capture it in the closest field and note the ambiguity.

9. **MEDDPICC fields will often be partially empty for first calls.** That's expected. A Stage 1 discovery call typically surfaces Pain (I), initial Metrics (M), and maybe Economic Buyer (E). Don't fabricate the rest.

10. **The prospect's energy and emphasis are data.** When someone repeats a concern three times, or audibly gets excited about a feature, or goes quiet after pricing — those are signals. Capture them in severity ratings and interest levels.

---

## Output Format

Present the extraction in readable form (not raw YAML — translate it into a scannable structure the user can quickly verify). Group by section. Flag anything marked as inferred with a note.

```
## Call State Extraction

### Input Assessment
- Type: [full_transcript / partial / summary / notes / mixed]
- Quality: [rich / adequate / thin]
- Speaker ID: [clear / partial / unclear]

### Actors
[list of people identified, with roles and titles]

### Company & Segment
[company name, headcount, segment classification with basis]

### Current State (Before Scenario)
[how they prospect today, tools, team, process]
[mark stated vs. inferred for each item]

### Pain Points
[each pain point with speaker attribution, exact words when available]
[negative consequences if stated]
[mark stated vs. inferred]

### Desired Outcomes (After Scenario)
[what they want their world to look like]

### Apollo Fit
[capabilities discussed, interest levels, value driver category]
[hooks that landed — what moments showed real interest]
[champion signals]

### Deal Mechanics
[pricing, objections, stakeholders, timeline, competitors]

### MEDDPICC Snapshot
[field-by-field status — populated or missing]

### Next Steps
[agreed steps with owners and deadlines]
[implied steps with basis]

### Verbatim Quotes Worth Using
[exact quotes with speaker and context]

### Extraction Quality
[overall confidence, thin areas, enrichment suggestions]

### Parser Notes
[assumptions, ambiguities, dropped content]
```

After presenting the extraction, ask: **"Does this look right? Anything to correct or add before I draft the email?"**

Then hand off to the follow-up email engine (Step 2: Compose).
