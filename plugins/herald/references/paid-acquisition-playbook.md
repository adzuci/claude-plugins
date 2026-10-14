# Apollo Paid Acquisition Playbook

Source of truth for Apollo's paid acquisition channel mix, performance learnings, and operating rules. Captures team-sourced context that the `herald:paid` skill should reflect.

> **As of:** February–March 2026. Specific numbers and named creatives are dated anchors, not live targets. Patterns and operating rules are durable until updated. Verify dated specifics with the Growth Marketing team before using as targets.

______________________________________________________________________

## Active channels

| Channel | Status | Notes |
|---------|--------|-------|
| Google Search | Active | Highest pipeline attribution. Largest area of paid spend. |
| Google Demand Gen | Active | |
| Google Performance Max | Active | RSAs and PMax both active. |
| YouTube | Active | Runs alongside Performance TV for video reach. |
| Bing Search | Active | Mirrors Google Search structure (RSAs). |
| Meta | Active | Registrations objective. All traffic to landing pages — no lead gen forms. |
| Reddit | Active | Standout format: "faux social post" with snarky/self-aware tone. |
| Performance TV — MNTN | Active | CTV / video. |
| Performance TV — TV Scientific | Active | Display and CTV programmatic. |
| Affiliates (via Partnerstack) | Active | Lowest overall CAC across channels. |
| G2 | Coming next | Planned addition to active mix. |
| LinkedIn | Active | B2B targeting by job title, company size, industry, seniority. Sponsored content + thought leadership ads. Brand page reinstated April 2026. |

**Removed from prior skill versions:** Audiohook (no longer in active mix).

______________________________________________________________________

## Channel attribution insights

- **Paid Search** has the greatest pipeline attribution of any paid channel.
- **Affiliates** have the lowest overall CAC.
- Specific keyword segments and themes within Paid Search can outperform Affiliates on CAC.
- Use these insights when allocating budget and setting per-channel targets in `herald:paid`.

______________________________________________________________________

## Channel-specific winning formulas

Concrete patterns observed in February–March 2026. Use as anchors when drafting copy and creative direction; verify currency before treating numbers as live targets.

### Reddit

- **Format:** Platform-native "faux social post" style with snarky, self-aware copy is the standout format multi-month running.
- **Themes tested on AI Assistant messaging:**
  - **Strongest:** "AI Executes" — drove the strongest overall performance across engagement and conversion.
  - **Underperformed:** "Less Busywork", "Modern Outbound" — underperformed on spend share.
- **CTA finding:** Ads with an embedded CTA drove 20% higher CVR and 25% lower CAC vs. ads without a CTA.
- **Top creative anchor:** February — top-performing faux-social-post drove a CAC of $190 (43% below channel average) and accounted for 45% of registrations that month.
- **Audience layer:** Broad, lookalike, retargeting, subreddit, and keyword-based, with exclusion lists.

### Meta

- **Format:** Brand-forward videos with product overlays and social proof are the consistent top performers.
- **Top creative anchors (February):**
  - "Cut Your Stack" typography video with music — 14% of February registrations, CTR 150% above average.
  - "Every Sales Tool" video — CTR 144% above average.
  - "Be Everywhere" — CAC 15% below average.
  - Top videos overall: CACs 6–15% below average, CTRs 84–144% above average.
- **Image/video split:** ~50/50 in February.
- **Audience layer:** Broad, lookalike, retargeting, keyword-based, with exclusion lists.

### Google Performance Max

- **Pattern:** Short, clear, easy-to-understand messaging that aligns with landing page expectations.
- **Top creative anchors (March):**
  - Top images — CTR 13–14% (vs. 11.56% benchmark), ROAS 8–9x (vs. 3.48 benchmark).
  - "Close Faster" and "Total Pipeline Visibility" both significantly outperformed benchmarks on CTR and ROAS.
  - "Find Leads and Close" video — 18.1x ROAS (vs. 4.63 video benchmark), strongest ROAS performer in the channel.
- **What's underperforming:** Too much on screen. AI Assistant product UI images significantly underperformed on ROAS.
- **Spend distribution:** Heavily weighted toward text ads and sitelinks. Majority of visual spend consolidated to one image and one video.

### YouTube / MNTN (Performance TV)

- **Baseline benchmarks:** ~8.5% conversion rate, ~0.39% visit rate (using "Pool" video as comparator).
- **Underperformance signal:** "Future of GTM" was paused in March after a 0.06 ROAS vs. Pool's 1.2 — useful anchor for what underperformance looks like on this channel.

### Cross-channel transferability rule

**Top and bottom performers do NOT reliably transfer across channels.** A creative that wins on Reddit may flop on Meta or PMax. When porting a winning creative or angle from one channel to another, treat it as a fresh test — do not assume the learning carries over.

______________________________________________________________________

## Audience targeting strategy

- **Primary:** Platform-native targeting (interest, keyword, behavioral, demographic per platform).
- **Layered with first-party data:** Customer match lists, site visitors, product event audiences.
- **Layered with third-party signals:** G2 intent.
- **Reddit and Meta specifically:** Combine broad, lookalike, retargeting, subreddit/keyword-based targeting, with exclusion lists applied (current customers, existing pipeline, internal employees, recently converted users).

______________________________________________________________________

## CTA standards

CTAs are standardized by go-to-market motion, not by segment.

| Motion | Standard CTAs |
|--------|---------------|
| **SLG (sales-led)** | "Talk to Sales", "Request a Demo" |
| **PLG / self-serve** | "Get Started", "Sign Up Free", "Sign Up Now" |

CTAs are not currently broken down further by segment beyond the SLG/PLG split. When in doubt, ask the user which motion the campaign serves.

______________________________________________________________________

## Retargeting policy

- **Frequency caps:** Always implemented across retargeting campaigns.
- **Lookback window:** Typically capped at 30 days.
- **Sequential creative:** Not running today. On the longer-term roadmap. When writing retargeting variants, rotate angles (objection handling, social proof, urgency) instead of building a sequenced narrative.

______________________________________________________________________

## Meta operating rules

- **Objective:** Registrations.
- **Audiences:** Broad, lookalike, retargeting, keyword-based.
- **Recommended ad density:** 4–7 ads per ad set.
- **Primary format:** Single image, with carousel and video also in rotation.
- **Image/video split:** ~50/50 in February.
- **Destinations:** All traffic drives to landing pages. **No lead gen forms in use.**

______________________________________________________________________

## Google Ads operating rules

- **Active formats:** RSAs and PMax both active. Apollo runs all available Google Ads creative types **except Shopping Ads**.
- **PMax spend distribution:** Heavily weighted toward text ads and sitelinks. Majority of visual spend consolidated to one image and one video.
- **Extensions:** Sitelinks, callouts, and structured snippets are all in use.
- **Demand Gen and YouTube:** Active, run alongside Performance TV for video reach.
- **Bing Search:** Mirrors Google Search structure (RSAs).

______________________________________________________________________

## Creative production process

- **All paid creative is produced in-house** by the design team.
- **Static and carousel:** Growth Marketing initiates a brief in Notion → adds to Asana for design execution.
- **Video:** Production runs separately through Chad's team without a formal briefing process.
- **Copy:** Requests handled separately through Michelle.
- **Implication for Herald skills:** Ad copy artifacts feed Michelle's intake. Visual direction notes feed the Notion → Asana brief flow for static/carousel and the informal video flow for video.

______________________________________________________________________

## Known gaps (unanswered as of 2026-04-08)

These questions exist in the Herald XFN Questions DB but don't yet have answers from the team. Surface them to users when relevant; do not speculate:

- Testing cadence — how long variants run before picking winners
- Attribution model in use (first touch / last touch / multi-touch / self-reported)
- Standard UTM parameter conventions
- Audience overlap deduplication strategy across campaigns
- Channels deliberately tested and stopped, and why
- Words/claims/angles that have bombed or caused compliance issues
- Number of ad variants per ad group (2 vs. 3-4+)
- Single landing page per campaign vs. channel-specific / audience-specific variants
- Meta as prospecting vs. retargeting vs. both — experience to date
