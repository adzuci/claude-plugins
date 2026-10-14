---
name: kickoff
description: |
  Initialize a new GTM launch campaign workspace or check status of an existing one.
  Creates brief.md (the living document), directory structure, and dependency graph.
  Run this first before any other Herald skill. Also works as a status dashboard:
  run it inside an existing launch directory to see what's done and what's next.
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

# herald:kickoff

Initialize a new GTM launch campaign or check status of an existing one.

Before anything else, read `${CLAUDE_PLUGIN_ROOT}/references/shared-context.md` (launch tiers, Apollo voice, PLG context, approved metrics, copy coherence rule). "Shared context" below means that file. If `${CLAUDE_PLUGIN_ROOT}` is not expanded, the plugin's `references/` folder is two levels up from this skill's base directory.

## Detect Mode

1. Check if `campaigns/` exists in the working directory
1. If the user provided a feature slug, check if `campaigns/[slug]/brief.md` exists
1. If brief exists → **Status Mode**
1. If no brief → **Init Mode**

______________________________________________________________________

## Init Mode

### Step 1: Gather basics

Use AskUserQuestion to collect:

1. **Feature name** — what's launching? (e.g., "AI Email Writer")
1. **Feature slug** — URL-safe identifier (suggest one based on the name, let user override)
1. **Launch tier** — T1 (New Product), T2 (Major), T3 (Minor), or T4 (Internal). See shared context for tier definitions. If the user isn't sure, help them pick based on the scope of what's launching.
1. **Ship date** — when does this need to go live?
1. **Target segment** — VSB, SMB, or both?

### Step 2: Create workspace

Create the full directory structure at `campaigns/[feature-slug]/`:

```
campaigns/[feature-slug]/
├── brief.md                        (the living document)
├── foundation/
├── growth/
├── content/
├── social/
└── lifecycle/
    └── emails/
```

### Step 3: Write brief.md

Write `brief.md` with campaign metadata, artifact tracker, and pre-stamped execution plan section.

```markdown
# Launch: [Feature Name]

Slug: [feature-slug]
Tier: [T1/T2/T3/T4] — [New Product/Major/Minor/Internal]
Created: [today's date]
Ship date: [date]
Status: in-progress

## Artifacts

Build this table based on the tier. Use the per-skill scaling matrix in shared context to determine which artifacts apply. Mark artifacts that don't apply for this tier as `n/a` in the Status column.

**T1/T2 — all artifacts:**

| Artifact | Skill | Status | Updated |
|----------|-------|--------|---------|
| Launch Brief | herald:brief | — | — |
| Strategy | herald:foundation | — | — |
| Audience | herald:foundation | — | — |
| Campaign Strategy | herald:paid | — | — |
| Ad Copy | herald:paid | — | — |
| Landing Page Brief | herald:paid | — | — |
| Blog Post | herald:content | — | — |
| Launch Announcement | herald:content | — | — |
| SEO Brief | herald:content | — | — |
| Help Center Article | herald:content | — | — |
| Social Copy | herald:social | — | — |
| Visual Direction | herald:social | — | — |
| Lifecycle Architecture | herald:email | — | — |
| Announcement Emails | herald:email | — | — |
| Nurture Emails | herald:email | — | — |
| Activation Emails | herald:email | — | — |
| In-App Notifications | herald:email | — | — |

For T2, SEO Brief Status may be set to `n/a` if not needed.

**T3 — focused push (no paid, reduced content/social/email):**

| Artifact | Skill | Status | Updated |
|----------|-------|--------|---------|
| Launch Brief | herald:brief | — | — |
| Strategy | herald:foundation | — | — |
| Audience | herald:foundation | n/a | — |
| Campaign Strategy | herald:paid | n/a | — |
| Ad Copy | herald:paid | n/a | — |
| Landing Page Brief | herald:paid | n/a | — |
| Blog Post | herald:content | — | — |
| Launch Announcement | herald:content | n/a | — |
| SEO Brief | herald:content | n/a | — |
| Help Center Article | herald:content | n/a | — |
| Social Copy | herald:social | — | — |
| Visual Direction | herald:social | n/a | — |
| Lifecycle Architecture | herald:email | n/a | — |
| Announcement Emails | herald:email | — | — |
| Nurture Emails | herald:email | n/a | — |
| Activation Emails | herald:email | n/a | — |
| In-App Notifications | herald:email | — | — |

**T4 — minimal (changelog + optional in-app only):**

| Artifact | Skill | Status | Updated |
|----------|-------|--------|---------|
| Launch Brief | herald:brief | — | — |
| In-App Notifications | herald:email | — | — |

All other artifacts are `n/a` for T4. Skip foundation, paid, content, and social entirely.

## Dependency Graph

Stage 1:  herald:kickoff → herald:brief
Stage 2:  herald:foundation (requires: brief) [skip for T4]
Stage 3:  herald:paid        (requires: foundation) [skip for T3, T4]
          herald:content      (requires: foundation) [skip for T4]
          herald:social       (requires: foundation) [skip for T4]
          herald:email        (requires: foundation) [T4: runs after brief, skip foundation]

## Next Steps

Run `/herald:brief` to build the launch brief.

---

<!-- herald:brief fills in everything below -->

## What's Launching?
<!-- Feature name, one-line description, ship date -->

## Target Audience
<!-- VSB, SMB, or both? Job titles, company size, current behavior signals -->

## Key Value Props
<!-- 3-5 bullets. What does this let them do that they couldn't before? -->

## Competitive Context
<!-- Who else does this? Where are we better? Where are we behind? -->

## Success Metrics
<!-- What numbers move if this works? Be specific: "X% increase in Y within Z days" -->

## Timeline
<!-- Launch date, hard deadlines, phased rollout details -->

## Inputs Available
- PRD / Product Spec:
- User research:
- Analytics data:
- Competitive analysis:
- Customer verbatims (Gong, support, G2):
- Pricing/packaging context:
- Historical launch performance:
- Usage data:

## Constraints
<!-- Budget limits, brand guidelines, legal/compliance guardrails, channel restrictions -->

---

<!-- Fill this section when all artifacts are complete -->

## Execution Plan

### Role Assignments
| Deliverable | Owner | Status | Deploy Date |
|------------|-------|--------|-------------|
| Paid campaigns | <!-- Growth Marketing Lead --> | — | <!-- date --> |
| Blog post | <!-- Content Lead --> | — | <!-- date --> |
| Landing page | <!-- Content Lead --> | — | <!-- date --> |
| Social posts | <!-- Brand Lead --> | — | <!-- date --> |
| Email sequences | <!-- Lifecycle Lead --> | — | <!-- date --> |
| In-app notifications | <!-- Lifecycle Lead --> | — | <!-- date --> |
| Help center article | <!-- Content Lead --> | — | <!-- date --> |
| Changelog | <!-- Lifecycle Lead --> | — | <!-- date --> |

### Timing & Sequencing
1. T-7 — Pre-launch: internal enablement, assets staged
2. T-1 — Final review, everything approved
3. T-0 — Changelog, in-app, email blast, social
4. T+1 — Blog post, paid campaigns go live
5. T+3 — Nurture sequences activate
6. T+7 — First performance check

**Intake gates** (add dates when known):
- In-app notifications: Notification Intake Process (Submitted → In Review → Approved)
- Feature gates: feature gate intake + `#growth-feature-gates` Slack
- Lifecycle sequences: Lifecycle team review + holdout coordination

### Success Metrics
| Metric | Target | Measurement Method | Check-in Date |
|--------|--------|--------------------|---------------|
| Feature activation rate | <!-- --> | <!-- --> | <!-- --> |
| Paid CPA | <!-- --> | <!-- --> | <!-- --> |
| Email activation rate | <!-- --> | <!-- --> | <!-- --> |
| Blog traffic | <!-- --> | <!-- --> | <!-- --> |
```

### Step 4: Print summary

Show the user:

- Workspace created at `campaigns/[slug]/`
- The dependency graph
- Remind them to run `/herald:brief` next

______________________________________________________________________

## Status Mode

### Step 1: Read brief

Read `campaigns/[slug]/brief.md` and parse the Artifacts table.

### Step 2: Scan for actual files

Use Glob to check which artifacts actually exist on disk. Cross-reference with the Artifacts table status.

### Step 3: Determine next steps

Based on the dependency graph and current status:

- Which skills have completed all their artifacts?
- Which skills are ready to run (all upstream dependencies met)?
- Which skills are blocked?

### Step 4: Print dashboard

```
Launch: [Feature Name]
Tier: [T1/T2/T3/T4]
Ship date: [date]
Status: [X/Y artifacts complete] (Y = total applicable for this tier)

Done:        [list skills with all artifacts complete]
Ready:       [list skills whose dependencies are met]
Skipped:     [list skills marked n/a for this tier]
Blocked:     [list skills waiting on upstream]

Next: Run /herald:[next-skill]
```
