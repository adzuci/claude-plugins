---
name: foundation
description: |
  Generate the 2 foundational artifacts that every downstream skill builds on:
  strategy (positioning + messaging + value props) and audience segmentation.
  Run after /herald:brief.
disable-model-invocation: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - AskUserQuestion
---

# herald:foundation

Produce the foundational artifacts. Every downstream skill reads these, so getting them right matters most.

Before anything else, read `${CLAUDE_PLUGIN_ROOT}/references/shared-context.md` (launch tiers, Apollo voice, PLG context, approved metrics, copy coherence rule). "Shared context" below means that file. If `${CLAUDE_PLUGIN_ROOT}` is not expanded, the plugin's `references/` folder is two levels up from this skill's base directory.

## Tier Scoping

Read the `Tier` field from `campaigns/[slug]/brief.md` metadata.

- **T1/T2:** Produce both artifacts — `strategy.md` and `audience.md`
- **T3:** Produce `strategy.md` only — include audience notes inline (skip separate `audience.md`)
- **T4:** Skip this skill entirely. Tell the user foundation isn't needed for T4 and stop.

## Phase 1: Load and Orient

Read `campaigns/[slug]/brief.md` — verify the brief is done (sections filled, not placeholders). If not, tell the user to run `/herald:brief` first and stop.

Assess which brief sections are complete vs. have TODOs. Flag critical gaps: missing value props → weak positioning, missing competitive context → generic differentiators, missing audience details → vague segmentation, missing metrics → no success criteria.

For T1/T2: "I'll produce 2 artifacts: strategy doc (positioning + messaging + value props) and audience segmentation."
For T3: "This is a T3 (Minor) launch, so I'll produce 1 artifact: a strategy doc with audience notes inline."

Call out gaps and their downstream impact.

**STOP.** Wait for go-ahead.

## Phase 2: Outline

### Step 1: Strategy outline

Present the skeleton for the strategy document:

**Positioning:**

- Proposed market category frame (see "Market Category Guidance" in shared context)
- Target buyer profile per relevant segment
- Problem statement (2-3 sentence draft)
- Unique value proposition (one sentence draft)
- Key differentiators (table headers + proposed rows)

**Messaging:**

- Core narrative arc (problem → insight → solution → result)
- Primary message (one sentence)
- 3 supporting message themes
- Segment-specific angle differences

**Value Props:**

- Proposed segment dimensions (from Apollo's 4-segment model + plan-based targeting)
- Proposed persona columns

### Step 2: Audience outline

Use Apollo's company segmentation (VSB / SMB / Mid Market / Enterprise) as the default menu. Select the 2-4 segments most relevant to this launch. Also consider plan-based targeting (Free / Basic / Professional / Organization) as a cross-cutting dimension.

Present:

- Selected segments with one-line descriptions and why they fit this launch
- Plan-tier targeting if relevant (e.g., "Free users who've hit credit limits")
- Key behavior signals for each
- Estimated reach (if data available)

### Step 3: Key decisions

Use AskUserQuestion to work through the positioning sequence. These questions build on each other — ask them one at a time, waiting for each answer before the next.

1. **Best customers:** "Which segment and buyer profile would be *raving fans* for this feature? What behavioral signals indicate they'd get value fastest?" (Identify the beachhead, not the broadest audience.)
1. **Competitive alternatives:** "What would these buyers actually do without this feature? Consider manual processes (spreadsheets, LinkedIn, hiring), status quo tools, and named competitors."
1. **Unique capabilities:** "What specific capabilities does this feature have that no alternative — software or manual — can match? Map each to a concrete outcome."
1. **Market category frame:** "Should we position this as part of Apollo's sales intelligence/engagement platform, or as part of the agentic GTM platform? Are we competing head-to-head in an existing category, dominating a niche, or creating something new?"
1. **Positioning angle + segment weighting:** "Given the above: which positioning angle leads? Which segments get primary vs. secondary emphasis?"

**STOP.** Wait for approval of the shape before writing prose.

## Phase 3: Draft

### Step 1: Write artifacts

Write each artifact to its file path (relative to `campaigns/[slug]/`):

1. `foundation/strategy.md` — the combined strategy document with three major sections:

   - **Positioning:** category, target buyer, problem statement, UVP, differentiators, proof points, positioning statement
   - **Messaging:** core narrative, message hierarchy, audience-specific angles, objection handling, word choice
   - **Value Propositions:** by-segment matrix and by-persona matrix

1. `foundation/audience.md` — 2-4 segments with profiles, behavior signals, current pain, activation path, estimated reach, and exclusion criteria

Adapt structure where the specific launch calls for it.

### Step 2: Update artifact status

Update the Artifacts table in `campaigns/[slug]/brief.md`:

- Set "Strategy" and "Audience" to `done` with today's date
- Update Next Steps:
  ```
  Stage 3 skills are now ready (run in any order):
  - /herald:paid (campaign strategy + ad copy + landing page brief)
  - /herald:content (blog, announcement, SEO, help center)
  - /herald:social (social copy, visual direction)
  - /herald:email (lifecycle architecture + email copy + in-app)
  ```

### Step 3: Summary

Tell the user:

- List all artifacts written with file paths
- Call out the strongest pieces and any areas where more input would improve quality
- Remind them of the 4 Stage 3 skills now available
