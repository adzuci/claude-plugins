---
name: paid
description: |
  Paid campaign strategy, ad copy, and landing page brief. Produces campaign
  strategy (channels, budget, targeting), platform-specific ad copy with A/B
  variants grounded in copywriting frameworks, and a landing page brief.
  Requires foundation artifacts from /herald:foundation.
disable-model-invocation: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - WebFetch
  - AskUserQuestion
---

# herald:paid

Paid campaign strategy + ad copy + landing page brief in one pass.

Before anything else, read `${CLAUDE_PLUGIN_ROOT}/references/shared-context.md` (launch tiers, Apollo voice, PLG context, approved metrics, copy coherence rule). "Shared context" below means that file. If `${CLAUDE_PLUGIN_ROOT}` is not expanded, the plugin's `references/` folder is two levels up from this skill's base directory.

## Tier Scoping

Read the `Tier` field from `campaigns/[slug]/brief.md` metadata.

- **T1/T2:** Run this skill. Full channel mix for T1, selective channels for T2.
- **T3/T4:** Skip this skill entirely. Tell the user paid isn't needed for T3/T4 launches and stop.

Read `${CLAUDE_PLUGIN_ROOT}/references/paid-acquisition-playbook.md` for Apollo's actual channel mix, attribution insights, operating rules, and channel-specific learnings. **Source of truth for paid acquisition context.**
Read `${CLAUDE_PLUGIN_ROOT}/references/ad-copy-guide.md` for copywriting frameworks: Schwartz awareness levels, Cialdini persuasion principles, direct response checklist.

## Apollo's Active Paid Channels

Select from these channels based on the launch context. Not every launch uses every channel. See `${CLAUDE_PLUGIN_ROOT}/references/paid-acquisition-playbook.md` for the full channel registry.

| Channel | Best for | Typical awareness level |
|---------|---------|----------------------|
| **Google Search** | High-intent capture. Highest pipeline attribution. | Solution → Most Aware |
| **Google Demand Gen** | Visual discovery across YouTube, Discover, Gmail | Problem → Solution Aware |
| **Google Performance Max** | Cross-surface reach with audience signals | Mixed |
| **YouTube** | Video reach, brand and consideration | Unaware → Problem Aware |
| **Bing Search** | Incremental high-intent; mirrors Google Search | Solution → Most Aware |
| **Meta** | Registrations objective, broad/lookalike/retargeting. All traffic to landing pages — no lead gen forms. | Problem Aware → Unaware |
| **Reddit** | Community-native B2B. "Faux social post" is the standout creative. | Problem → Solution Aware |
| **Performance TV — MNTN** | CTV brand awareness | Unaware → Problem Aware |
| **Performance TV — TV Scientific** | Display and CTV programmatic | Unaware → Problem Aware |
| **Affiliate (Partnerstack)** | Lowest overall CAC | Mixed |
| **G2** | _Coming next_ — planned addition | Solution Aware |
| **LinkedIn** | B2B targeting by job title, company, industry. Thought leadership + sponsored content. | Solution → Product Aware |

## Phase 1: Load and Orient

Read `campaigns/[slug]/brief.md` and the Artifacts table — verify foundation is done. Read `foundation/strategy.md` and `foundation/audience.md`. If foundation artifacts don't exist, tell the user to run `/herald:foundation` first and stop.

Fetch Apollo's sitemap to find existing pages for this campaign:

```
WebFetch https://www.apollo.io/sitemap.xml
```

Search for URLs related to the feature, product area, or use case. Note relevant existing pages (SEO equity, backlinks, traffic).

If WebFetch is unavailable or the fetch fails, skip it: ask the user whether existing pages cover this feature, and note in the landing page brief that the sitemap wasn't checked.

From the brief and foundation, assess:

- Budget constraints, timeline, channel restrictions
- Whether this is awareness, activation, or retargeting focused
- Which audience segments are primary vs. secondary
- Awareness levels by audience-channel combination (map using the Schwartz framework from `ad-copy-guide.md`)

Outline your approach:

- Which channels and why (tied to audience + awareness level)
- How many ad groups / asset groups per channel
- Whether retargeting copy is needed (separate from prospecting)
- Landing page: update existing page vs. create new

**STOP.** Wait for go-ahead.

## Phase 2: Campaign Strategy

### Step 1: Campaign architecture

Present:

- Recommended channels and why (match channel to audience awareness level)
- Campaign structure: how many campaigns, what objective each serves
- Budget allocation rationale (Google Search typically largest allocation — highest pipeline attribution. Affiliates/Partnerstack typically lowest CAC). Note playbook benchmarks are dated Feb–Mar 2026 and should be confirmed with Growth Marketing.

### Step 2: Targeting parameters by channel

**Audience layering (default for all channels):** Platform-native targeting layered with first-party data (customer match, site visitors, product events) and third-party signals (G2 intent).

**Google Search:**

- Keywords by match type: exact (highest intent, branded), phrase (category/feature), broad (wider discovery, smart bidding only)
- Negative keywords: competitor brands (unless competitive campaigns), irrelevant verticals, job-seeker terms
- Search intent mapping

**Bing Search:** Mirror Google structure. Reuse keyword list as starting point.

**Google PMax:** Audience signals (custom segments, customer match, in-market). Asset group themes. Brand/placement exclusions. Per playbook: spend heavily weighted toward text ads and sitelinks.

**Google Demand Gen / YouTube:** Custom segments, lookalikes, in-market. Run alongside Performance TV for video reach.

**Meta:** Registrations objective. Broad + lookalike + retargeting + keyword-based audiences with exclusion lists. 4–7 ads per ad set. ~50/50 image/video split. All traffic to landing pages — no lead gen forms.

**Reddit:** Target communities (r/sales, r/startups, r/SaaS, etc.). Interest-based + broad + lookalike + retargeting + keyword. Ad-skeptical audience — needs community-native creative.

**Performance TV (MNTN, TV Scientific):** Behavioral/demographic targeting. Spot length (15s vs. 30s). Frequency cap. TV Scientific can run display alongside CTV.

**Affiliate (Partnerstack):** Lowest overall CAC. Placement notes per active offer.

**Retargeting (if applicable):** Source audiences (site visitors, page URLs, product events). 30-day lookback (per policy). Frequency cap always on. No sequential creative today — rotate angles instead. Exclude converted users, pipeline accounts, internal employees.

**Exclusion lists (all channels):** Current customers, existing pipeline, internal employees, recently converted (cooling period).

### Step 3: Campaign decisions

Use AskUserQuestion for:

1. **Channel mix:** "I'm recommending [channels] because [reasoning]. Any to include or exclude?"
1. **Campaign objective:** "Should the primary objective be signups, feature activation, or pipeline?"
1. **Budget range:** (if not in brief) "Ballpark budget? This affects channel count and allocation."
1. **Landing page strategy:** "Should all channels drive to the same page, or separate experiences for high-intent (Google Search) vs. awareness (MNTN/Reddit)?"

**STOP.** Wait for approval.

## Phase 3: Ad Copy

### Step 1: Copy angle matrix

For each channel, present:

- Awareness level and copy approach
- Variant angles being tested (pain vs. benefit, social proof vs. reciprocity, question vs. statement, audience-specific messaging, CTA variation)
- Test hypothesis for each variant
- Persuasion lever (Cialdini: Social Proof, Authority, Reciprocity, Scarcity, Commitment, Unity)
- Character limits and format constraints

### Step 2: Landing page strategy

Start from sitemap findings. If existing pages found: recommend which to update and what changes are needed (headline, CTA, proof, SEO metadata). Explain why reusing beats creating new. If no pages found: propose a new page.

Present: recommended destination, hero headline direction, key sections, primary + secondary CTA, social proof approach, visual direction, whether channels need different variants.

### Step 3: Copy decisions

Use AskUserQuestion for:

1. **Copy approach:** "Based on awareness mapping: [summary]. Does this match your read?"
1. **Landing page:** "Found [URLs] / No existing pages. [Recommendation]. Agree?"
1. **Proof points:** "Which specific metrics or claims? (230M+ people, 97% email accuracy, 2M+ users, G2 badges — use the approved metrics in shared context)"
1. **Creative direction:** "For MNTN video and Reddit visuals — any existing creative assets or screenshots?"

**STOP.** Wait for approval.

## Phase 4: Draft

### Step 1: Write campaign strategy

Write to `campaigns/[slug]/growth/campaign-strategy.md`:

- Campaign objective and channel strategy
- Budget and timeline with allocation table
- Campaign architecture per channel (objective, targeting, format, landing page, bid strategy)
- Audience targeting with specific parameters and exclusions
- Keyword strategy (Google), community targeting (Reddit), audience signals (PMax)
- Retargeting strategy (if applicable)
- Success metrics and targets
- Test plan

### Step 2: Write ad copy

Write to `campaigns/[slug]/growth/ad-copy.md` — all variants by channel:

> **Cross-channel rule (per playbook):** Top/bottom performers do NOT transfer across channels. Treat ported angles as fresh tests.

**Google Search (RSA):** 6-10 headlines (30 char) + 3-4 descriptions (90 char) per ad group. Pin guidance. Headlines work in any combination. Mix: pain, benefit, proof, CTA. At least 1 headline with a specific number.

**Bing Search:** Mirror Google RSA structure. Flag platform-specific variants.

**Google PMax:** Short headlines (30 char, up to 5), long headlines (90 char, up to 5), descriptions (90 char, up to 5). Audience signals. Visual direction. Per playbook: short, clear messaging wins.

**Google Demand Gen / YouTube:** Visual-led. Headline + description pairs. Audience signals.

**Ad Extensions:** 4-6 sitelinks (25-char headline + 35-char desc), 4-6 callouts (25 char), structured snippets.

**Meta:** Registrations objective. Single image + carousel + video (~50/50 split). 4-7 ads per ad set. Landing pages only — no lead gen forms. Primary text (hook in first 125 char, full up to 400). Headline (40 char hard limit). Per playbook: brand-forward video with product overlays + social proof wins consistently. Typography videos with music drive outsized CTR.

**Reddit:** Headline (aim 100-150 of 300 char max) — write like a Reddit post. Optional body (1-3 sentences, specific claim). Community-native. Per playbook: "faux social post" style is the standout. Always include embedded CTA (~20% higher CVR, ~25% lower CAC).

**Performance TV — MNTN:** Video script brief (15s/30s). [VISUAL] / [VO] pairs with timestamps. CTA overlay (10 words max).

**Performance TV — TV Scientific:** Display or CTV format. Headline, body, CTA, visual direction (display) or video script (CTV).

**Affiliate (Partnerstack):** Copy variants per active offer. CTA aligned to motion.

**Retargeting:** Separate copy for retargeting (Most Aware / Product Aware). Objection handling, social proof, urgency. Don't reuse prospecting copy. Rotate angles. 30-day lookback, frequency cap always on.

Every variant includes: test hypothesis, persuasion lever (Cialdini), awareness level (Schwartz), CTA motion (SLG: Talk to Sales / Request a Demo. PLG: Get Started / Sign Up Free / Sign Up Now).

**Character limits are hard constraints.** Count characters for every headline and description.

### Step 3: Write landing page brief

Write to `campaigns/[slug]/growth/landing-page-brief.md`:

If updating existing page: URL, what to keep, what to update, rationale. If new page: proposed URL slug, rationale.

Then: hero section (headline matching ad promise, subheadline, CTA, visual), social proof block (early — trust before ask), feature walkthrough (capability + benefit pairs), bottom CTA, SEO metadata (target keyword, 60-char title, 155-char meta description), channel-specific variant notes.

### Step 4: Coherence review

Re-read the foundation artifacts (`strategy.md`, `audience.md`, and the brief). Scan every claim, stat, and audience reference in the draft against what the foundation actually says. Fix anything that contradicts, overstates, or misattributes.

### Step 5: Self-review

Check every ad against the direct response checklist:

- [ ] Every headline leads with pain, benefit, or proof — not a feature name?
- [ ] Every ad includes at least one specific concrete claim?
- [ ] Exactly one CTA per ad? Previews what happens next?
- [ ] CTA matches SLG vs. PLG standard?
- [ ] Can you name the persuasion principle each variant deploys?
- [ ] Copy matches awareness level of target audience on this channel?
- [ ] Strongest line in the headline, not buried in description?
- [ ] Read aloud: sounds like a person, not a brochure?

Fix violations before presenting.

### Step 6: Update artifact status

Update the Artifacts table in `campaigns/[slug]/brief.md`:

- Set "Campaign Strategy", "Ad Copy", and "Landing Page Brief" to `done` with today's date

### Step 7: Summary

Tell the user: artifacts written with file paths, total ad variants by channel, awareness levels and persuasion levers used, what's being A/B tested, character limit issues, creative assets needed.
