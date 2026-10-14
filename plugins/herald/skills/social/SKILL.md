---
name: social
description: |
  Social media copy, visual direction brief, and community talking points. Produces
  platform-specific social content for LinkedIn, X/Twitter, plus visual asset specs
  and community engagement guidance. Requires foundation artifacts.
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

# herald:social

Social copy (with community talking points) and visual direction.

Before anything else, read `${CLAUDE_PLUGIN_ROOT}/references/shared-context.md` (launch tiers, Apollo voice, PLG context, approved metrics, copy coherence rule). "Shared context" below means that file. If `${CLAUDE_PLUGIN_ROOT}` is not expanded, the plugin's `references/` folder is two levels up from this skill's base directory.

## Tier Scoping

Read the `Tier` field from `campaigns/[slug]/brief.md` metadata.

- **T1/T2:** Full — social copy (brand + exec + employee, community talking points) + visual direction brief. T2 may use fewer platforms.
- **T3:** 1 LinkedIn brand post + 1 tweet only. No visual direction doc, no community talking points.
- **T4:** Skip this skill entirely. Tell the user social isn't needed for T4 launches and stop.

Read `${CLAUDE_PLUGIN_ROOT}/references/social-platform.md` for Apollo's brand & social operations: channel mix, monitored communities, and the employee advocacy program. **Source of truth for which platforms to use, who posts where, and how amplification works.**

## Phase 1: Load and Orient

Read `campaigns/[slug]/brief.md`, `foundation/strategy.md`, and `foundation/audience.md`. Verify foundation is done. If not, tell the user to run `/herald:foundation` first and stop.

Assess social needs (anchored on `social-platform.md` channel mix — don't propose channels not on that list): LinkedIn (brand page + personal/exec), X (brand account), Reddit/Instagram/YouTube (brand, if relevant). No TikTok (deprioritized). No Apollo Slack Community (removed from mix).

Tell the user: "I'll produce 2 artifacts: social copy and visual direction brief." Proposed channel mix, which exec voice for LinkedIn, which monitored communities for talking points.

**STOP.** Wait for go-ahead.

## Phase 2: Outline

### Step 1: Social copy angles

Present for each active platform (per `social-platform.md`):

**LinkedIn (brand page + personal/exec):**

- 1 brand page post concept (official announcement, links to blog/landing page)
- 1 exec/founder post concept (which exec voice + angle: announcement, behind-the-build, data proof)
- 2 employee template concepts (different angles, both adaptable, both carrying the launch's specifics)
- The hook line for each (the "see more" line)

**X (brand account):**

- 3 tweet concepts + optional thread
- Opening line for each

**Reddit / Instagram / YouTube (brand accounts):** Only include if relevant to this launch. For each included platform, propose 1–2 post concepts in the platform-native tone (see `social-platform.md`).

### Step 2: Visual direction

Present:

- Key visual concept (1-2 sentences)
- Required asset list with dimensions
- General direction: screenshot-heavy, illustration, data visualization?

### Step 3: Community strategy

Present (anchored on the monitored channels in `social-platform.md` — do not invent community surfaces nobody is watching):

- Which monitored channels (Reddit, X, LinkedIn comments, YouTube comments, Instagram) the launch should engage on
- Timing: proactive posts vs. reactive (responding to conversations)
- **Do not propose Apollo Slack Community** — it's currently removed from the channel mix

### Step 4: Key decisions

Use AskUserQuestion for:

1. **Channel mix:** "LinkedIn (personal/exec) and X are defaults. Should this launch also activate Reddit, Instagram, and/or YouTube?" (Do not offer TikTok or Apollo Slack Community.)
1. **Exec voice for LinkedIn:** "Which Apollo exec should the founder/exec LinkedIn post be drafted for? (CEO, CPO, PM lead, etc.)"
1. **Visual approach:** "Should visuals feature product screenshots, abstract graphics, or data visualizations?"

**STOP.** Wait for approval.

## Phase 3: Draft

### Step 1: Write artifacts

Write to `campaigns/[slug]/social/`:

1. `social-copy.md` — all social copy organized by platform, plus community talking points:

   - **LinkedIn (brand page + personal/exec):**
     - 1 brand page post (official announcement, concise, links to blog/landing page)
     - 1 exec/founder post (150–300 words), labeled with the exec voice it's drafted for
     - 2 employee templates (100–200 words each), each with a "feel free to remix" framing and obvious personalization placeholders
   - **X (brand account):** 3 tweet variants (280 char max each, with character counts), optional thread (3–5 tweets)
   - **Reddit / Instagram / YouTube** (only platforms confirmed in Phase 2): platform-native copy with hashtags/mentions where relevant
   - **Hashtags and mentions** appropriate per platform
   - **Community talking points:** "What is this?", "Why should I care?", "How does this compare to [competitor]?", bug/limitation response, proactive engagement targets — anchored on the monitored channels in `social-platform.md` (no Apollo Slack Community)

1. `visual-direction.md` — complete brief for design team:

   - Key visual concept
   - Required assets with exact dimensions
   - Visual references
   - Brand constraints
   - Copy for each asset

### Step 2: Coherence review

Re-read the foundation artifacts (`strategy.md`, `audience.md`, and the brief). Scan every claim, stat, and audience reference in the draft against what the foundation actually says. Fix anything that contradicts, overstates, or misattributes.

### Step 3: Update artifact status

Update the Artifacts table in `campaigns/[slug]/brief.md`:

- Set "Social Copy" and "Visual Direction" to `done` with today's date

### Step 4: Summary

Tell the user:

- Artifacts written with file paths
- Total posts produced per platform (note the LinkedIn shape: 1 brand + 1 exec + 2 employee templates)
- Visual assets the design team needs to create
- Monitored channels to target for community engagement
