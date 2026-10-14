---
name: brief
description: |
  Draft-first launch brief builder. Gathers all available context (kickoff metadata,
  qmd brain repo, local docs, reference files), drafts the full brief automatically,
  then presents a readiness review with downstream impact warnings and legal flags.
  Run after /herald:kickoff.
disable-model-invocation: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - AskUserQuestion
  - mcp__qmd__query
  - mcp__qmd__get
  - mcp__plugin_qmd_qmd__query
  - mcp__plugin_qmd_qmd__get
---

# herald:brief

Draft-first launch brief builder. Two modes: gather context and draft automatically, then review with the user.

Before anything else, read `${CLAUDE_PLUGIN_ROOT}/references/shared-context.md` (launch tiers, Apollo voice, PLG context, approved metrics, copy coherence rule). "Shared context" below means that file. If `${CLAUDE_PLUGIN_ROOT}` is not expanded, the plugin's `references/` folder is two levels up from this skill's base directory.

## Tier Scoping

Read the `Tier` field from `campaigns/[slug]/brief.md` metadata. The tier determines brief depth:

- **T1/T2:** Full brief — all 8 sections with maximum depth. Readiness review in Phase 4.
- **T3:** Lighter brief — What's Launching, Target Audience, Key Value Props, Timeline, and Constraints. Skip Competitive Context, detailed Success Metrics, and Inputs Available.
- **T4:** Minimal brief — What's Launching and Timeline only. Skip the readiness review (Phase 4) and go straight to finalize.

## Phase 1: Load Context (automated — no questions)

### Step 1: Read kickoff metadata

Read `campaigns/[slug]/brief.md` to get the feature name, slug, tier, ship date, and target segment from the campaign metadata (written by kickoff).

If no brief exists, tell the user to run `/herald:kickoff` first and stop.

### Step 2: Read reference docs

Read `${CLAUDE_PLUGIN_ROOT}/references/legal-marketing-playbook.md` — high-risk topics that need legal review, approved metrics policy, do's and don'ts.

### Step 3: Search for existing context

If a qmd search tool is available (`mcp__qmd__query`, or `mcp__plugin_qmd_qmd__query` when qmd is installed as a plugin), use it to search the brain repo for existing documents about this feature. Try multiple searches:

1. Search for the feature name (lexical)
1. Search for related concepts (semantic/vector)
1. Search for PRDs, pitches, or planning docs mentioning it

If qmd is unavailable (team members without it installed), skip gracefully.

For each relevant document found, read it with the matching qmd `get` tool and extract structured notes covering:

- Feature description and scope
- Target audience details
- Value propositions mentioned
- Competitive context
- Success metrics mentioned
- Constraints or timeline info

### Step 4: Scan for local context files

Use Glob to check `test/fixtures/` and `campaigns/[slug]/` for any docs (.md, .txt) that might contain context about this feature. Read any that look relevant.

### Step 5: Assess coverage

Count how many of the 8 brief sections have substantive content from the sources gathered. A section counts as "covered" if you have enough to write 2+ sentences of real content (not just a label or placeholder).

- **Rich context** = 5+ sections covered → skip Phase 2, go straight to Phase 3
- **Thin context** = fewer than 5 sections covered → proceed to Phase 2

## Phase 2: Ask for Context Doc (0 or 1 question)

Skip this phase entirely if Phase 1 found rich context.

Otherwise, use `AskUserQuestion` to ask ONE question:

"I found [brief summary of what context was gathered and from where]. The brief will be strongest if I have a PRD, context doc, or planning doc to work from. Do you have one?"

Options:

- "No — proceed with what you have"

The user can also paste a file path or additional context in the free-form response.

If the user provides a file path or pastes context → read it, extract structured notes, and proceed to Phase 3.
If the user says no → proceed to Phase 3 with available context.

## Phase 3: Draft Brief (automated — no questions)

### Step 1: Classify launch type

Determine from context which type of launch this is:

| Type | Signal |
|------|--------|
| **New feature launch** | Feature has not shipped yet, or ships on/after the campaign date |
| **Awareness push** | Feature already shipped; campaign goal is adoption/activation |
| **Packaging/pricing change** | Changes to plans, tiers, credits, or pricing |
| **Integration launch** | New integration or partnership |
| **Market expansion** | Existing feature, new segment or geo |

Write this classification into the "What's Launching?" section explicitly. This affects framing for every downstream skill.

### Step 2: Fill all 8 sections

Use this priority stack for each section — use the highest-signal source available:

1. User-provided context doc (if given in Phase 2)
1. qmd results from brain repo
1. Local context files found in Step 4
1. Kickoff metadata (feature name → What's Launching, ship date → Timeline, target segment → Target Audience)
1. Shared context inferences (segment definitions for Target Audience, competitive landscape for Competitive Context)
1. Best-effort inference with `<!-- TODO: [specific thing needed] -->` markers for genuine gaps

**Section-specific guidance:**

- **What's Launching?** — Include the launch type classification. If this is an awareness push, say so explicitly: "This feature already shipped on [date]. The campaign is an awareness push to drive adoption."
- **Target Audience** — Use Apollo's segment model (VSB/SMB/Mid Market/Enterprise) from shared context. Include job titles, company size, and behavior signals where known. If kickoff only said "SMB," expand with shared context details but flag that behavior signals are assumed.
- **Key Value Props** — Frame as outcomes, not features. "What can they do now that they couldn't before?" Aim for 3-5 specific props.
- **Competitive Context** — Check shared context for relevant competitors. Note whether the framing should name competitors or use "category norm" positioning. If unsure, default to category norm and flag it.
- **Success Metrics** — Be specific: "X% increase in Y within Z days." If no baseline data exists, state assumed targets and mark with TODO.
- **Timeline** — Pull ship date from kickoff metadata. Note whether this is a firm date or aspirational.
- **Inputs Available** — Fill the checklist honestly. Mark what exists (with file paths) and what doesn't.
- **Constraints** — Include any legal/compliance items discovered in Step 3.

### Step 3: Legal scan

Scan the drafted content against the high-risk topics from `${CLAUDE_PLUGIN_ROOT}/references/legal-marketing-playbook.md`:

- **AI** — claims about models learning, training, fine-tuning
- **Dialer / cold calling** — claims about automated calling, private numbers
- **ZoomInfo** — active litigation; ALL mentions need legal review
- **LinkedIn** — litigation-related; all public-facing statements need review
- **Data accuracy** — cannot claim "most accurate"; use "validated and multi-sourced"
- **Competitor comparisons** — must be factual, based on public data only
- **Pricing/packaging** — plan changes, discounts, trials, credit claims need review
- **Metrics** — any metric NOT in the Apollo Company Fact Sheet needs legal validation
- **Product screenshots** — no real PII; must use fake data
- **Mobile/email data** — cannot suggest access to "private" or "personal" info

For each match, add an inline comment: `<!-- LEGAL REVIEW: [topic] — [specific reason from playbook] -->`

### Step 4: Write the brief

Edit `campaigns/[slug]/brief.md` to fill in all strategic content sections below the `---` separator. Keep the campaign metadata and artifact tracker at the top unchanged.

## Phase 4: Readiness Review (1 interaction)

Present a single consolidated review to the user with three parts.

### Part 1: Section Readiness

Show a table with the status of each section:

| Section | Status | Notes |
|---------|--------|-------|
| What's Launching | READY / THIN / EMPTY | [one-line explanation] |
| Target Audience | ... | ... |
| Key Value Props | ... | ... |
| Competitive Context | ... | ... |
| Success Metrics | ... | ... |
| Timeline | ... | ... |
| Inputs Available | — | Checklist filled |
| Constraints | ... | ... |

Definitions:

- **READY** — substantive content from a real source; foundation can work with this
- **THIN** — has content but lacks specificity; downstream artifacts will be weaker in this area
- **EMPTY** — couldn't fill this section; marked with TODOs

### Part 2: Downstream Impact Warnings

Only show warnings for sections that are THIN or EMPTY. Map each gap to its specific downstream impact:

- EMPTY or THIN **Value Props** → "Foundation will produce weak positioning. Ad copy will lack differentiation."
- EMPTY **Competitive Context** → "Foundation can't produce battle cards. Differentiators will be generic. Ad copy will lack competitive angles."
- THIN **Target Audience** → "Audience segmentation will rely on assumptions, not behavior signals. Lifecycle triggers may not match real user behavior."
- THIN or EMPTY **Success Metrics** → "Campaign won't have clear optimization targets. Converge execution plan will have placeholder KPIs."
- EMPTY **Constraints** → "Legal and compliance issues may surface late in downstream artifacts."

### Part 3: Gotcha Flags

Surface only the flags relevant to this specific launch. Do not show all of these every time — only include ones that apply:

- **Launch type confirmation:** "I classified this as [type]. Correct?"
- **Legal flags:** "This content mentions [topic] which requires legal review per the marketing playbook." (List each flagged topic.)
- **Competitive framing:** "Should we name specific competitors, or frame against the category norm?"
- **Missing baseline data:** "No usage data provided — metric targets are estimates."
- **Timing risk:** "Ship date is [X days away / already passed]. Is this correct?"
- **Missing assets:** "No [PRD / user research / customer verbatims / analytics data] available — brief relies entirely on [source]."

### Ask for confirmation

Use `AskUserQuestion` with ONE question:

"The brief is drafted at `campaigns/[slug]/brief.md`. Review the readiness assessment above."

Options:

- "Looks good — proceed to /herald:foundation"
- "I have more context to add"

The user can also provide specific edits or adjustments in the free-form response.

**If confirmed** → proceed to Phase 5.
**If user provides edits or more context** → update brief.md accordingly, then re-present the readiness review (loop back to the start of Phase 4). Each iteration updates the actual file, so the user can stop at any point.

## Phase 5: Finalize (automated)

### Step 1: Update artifact status

Update the Artifacts table in `campaigns/[slug]/brief.md`:

- Set "Launch Brief" status to `done`
- Set the Updated date to today
- Update Next Steps to indicate `/herald:foundation` is ready to run

### Step 2: Summary

Tell the user:

- Brief filled in at `campaigns/[slug]/brief.md`
- What sections are READY vs. have TODOs
- Any legal review flags that were marked inline
- Next step: run `/herald:foundation`
