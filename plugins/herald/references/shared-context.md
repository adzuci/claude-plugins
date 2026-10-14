# Herald Shared Context

Every Herald skill reads this file first. Skill-specific references live alongside it in this `references/` folder.

______________________________________________________________________

## Launch Tiers

Every launch is classified into one of four tiers at kickoff. The tier is stored in `brief.md` metadata and determines the scope of every downstream skill.

| Tier | Name | What it is | GTM scope |
|------|------|-----------|-----------|
| **T1** | New Product | New product line, new category, major platform shift | Full loadout — all skills, all artifacts, all channels |
| **T2** | Major | Significant new capability, major feature expansion | Full skills, all artifacts, channel mix may be selective |
| **T3** | Minor | Feature improvement, incremental update, small addition | Focused push — subset of artifacts per skill, no paid |
| **T4** | Internal | Bug fix, backend change, minor UI tweak, internal tooling | Minimal — changelog + in-app notification if UI changed |

### Per-skill scaling

Each skill reads the tier from `brief.md` and adjusts scope:

| Skill | T1 — New Product | T2 — Major | T3 — Minor | T4 — Internal |
|-------|------------------|------------|------------|----------------|
| **foundation** | Strategy + audience | Strategy + audience | Strategy only (inline audience notes) | Skip |
| **paid** | All channels, full variants | Selective channels, full variants | Skip | Skip |
| **content** | Blog + announcement + SEO brief + help center | Blog + announcement + help center (SEO brief optional) | Blog post only | Skip |
| **social** | Full: brand + exec + employee, visual direction, community talking points | Full but fewer platforms | 1 LinkedIn post + 1 tweet (no visual direction) | Skip |
| **email** | Full: architecture + all sequences + in-app + changelog | Full | 1 announcement email + in-app + changelog | Changelog only (+ in-app if UI changed) |

**Rules:**

- T3 and T4 launches skip `herald:paid` entirely — no paid spend for minor/internal launches
- T4 launches skip foundation, paid, content, and social — run only `herald:email` for changelog and optional in-app
- When a skill is skipped, mark its artifacts as `n/a` in the Artifacts table
- Skills should confirm tier-appropriate scope with the user in Phase 1, not silently skip

______________________________________________________________________

## Apollo Brand Voice

Follow these rules when writing any customer-facing GTM artifact: ad copy, emails, blog posts, social media, landing pages, help center articles, in-app copy.

### Core Principles

1. **Write for people who do the work.** Whether that's a founder running their own outbound or a VP overseeing a team, your reader cares about what this does and how it helps them. Avoid jargon and salesy language that sacrifices clarity. They want specifics, not vision statements.

1. **Specific beats clever.** "Find verified emails for 230M+ people" beats "Access the world's largest B2B database." Numbers, features, and concrete outcomes earn trust. Vague superlatives don't.

1. **Confident, not cocky.** State what Apollo does well. Don't trash competitors. Don't use words like "revolutionary" or "game-changing." Let the capability speak.

1. **Short and scannable.** Paragraphs: 1-3 sentences. Bullet points when listing capabilities. Bold key phrases. Readers skim, so frontload the important stuff.

1. **Natural language.** Contractions always (you'll, it's, don't). Active voice. Write how a knowledgeable colleague would explain something in Slack, not how a brochure would describe it.

### Channel-Specific Guidelines

**Email:** Subject lines: specific and curiosity-provoking. One job per email. First sentence hooks — no "We're excited to announce..." openers. One primary CTA. Write preview text intentionally.

**Blog Posts:** Hook openers (moment, frustration, question — not a summary). 800-1200 words for feature launches. Structure: hook, problem, solution, how it works, proof, CTA. End with a clear next step.

**Ad Copy:** Pain-led or benefit-led, not feature-led. Match copy to awareness level. Every ad deploys at least one persuasion principle intentionally. Every ad includes at least one specific concrete claim. Platform-native tone:

- **Google/Bing RSA:** 6-10 headlines that work in any combination. Pin critical headlines.
- **Google PMax:** Short, clear messaging aligned with landing page. Avoid busy screenshots.
- **Demand Gen / YouTube:** Visual-led. Earn attention with the hook.
- **Meta:** Brand-forward video with product overlays + social proof wins. Hook in first 125 chars.
- **Reddit:** Community-native "faux social post" style. Specific, not hype. Always include embedded CTA.
- **Performance TV:** Lead with pain or startling stat. ~35 words/15s, ~70 words/30s.

**Social Media:** LinkedIn: professional storytelling, 150-300 words, hook in first line. X: sharp, specific, 280 chars. Write like a person, not a brand account.

**Landing Pages:** Hero matches ad promise. One conversion action. Social proof early. Feature walkthrough: capability + benefit pairs.

**In-App Copy:** 8-12 word headlines. 1-2 sentence bodies. Action-oriented CTAs. Respect user's context.

**Help Center:** Plain English. Task-oriented ("How to do X"). Step-by-step with screenshots. FAQ + troubleshooting.

### Banned Patterns

- "We're excited to announce..." (just announce it)
- "Best-in-class" / "World-class" / "Industry-leading" (prove it instead)
- "Seamless" / "Seamlessly" (everything claims to be seamless)
- "Solution" as a standalone noun (name what it is)
- Rhetorical questions that don't add value

**Use sparingly:** "Empower" / "Enable" — acceptable in official company language but prefer concrete verbs in customer-facing copy.

### Tone Spectrum

| Context | Tone |
|---------|------|
| Launch announcement email | Confident, direct, a bit of energy |
| Help center article | Clear, patient, task-focused |
| Blog post | Conversational, specific, practitioner-to-practitioner |
| Ad copy | Sharp, benefit-first, action-oriented |
| Social post | Human, authentic, slightly opinionated |
| In-app notification | Brief, helpful, respectful of attention |
| Landing page | Persuasive, proof-heavy, scannable |

______________________________________________________________________

## Apollo Business Context

### What Apollo Is

Apollo.io is a B2B sales intelligence and engagement platform — and the industry's first fully agentic GTM platform. It combines a contact database (230M+ people, 30M+ companies) with outbound engagement tools (sequences, email, dialer, LinkedIn automation), AI agents, and a CRM. The pitch: one platform for prospecting, engaging, and closing.

### Market Category Guidance

Two market category frames — which one to lead with depends on what you're launching:

- **"B2B sales intelligence and engagement platform"** — For data, prospecting, and outbound feature launches. Established category. Competitors: ZoomInfo, Lusha, Outreach, Salesloft, HubSpot.
- **"Fully agentic GTM platform"** — For AI-forward launches and new capability categories. New category Apollo is defining. Fewer direct competitors.

### GTM Motion

| Segment | Motion | How They Buy |
|---------|--------|-------------|
| **VSB** (0-20 emp) | Pure PLG | Fast, alone. Price sensitive. Minutes to days. |
| **SMB** (21-200 emp) | PLG + Velocity Sales | Light validation. Days to weeks. Single buyer. |
| **Mid Market** (201-1K emp) | Sales-led | Evaluates alternatives. Weeks to months. Multiple stakeholders. |
| **Enterprise** (1K+ emp) | Enterprise Sales | Strategic. Months. Heavy procurement. |

Key PLG mechanics: Free plan with real functionality. Usage-based conversion triggers (credit/sequence/export/seat limits). Self-serve upgrade. In-product upgrade prompts.

### Pricing (last verified April 2026)

| | Free | Basic | Professional | Organization |
|---|------|-------|-------------|--------------|
| Annual (per user/mo) | $0 | $49 | $79 | $119 |
| Credits/month | 75 | 2,500 | 4,000 | 6,000 |
| Sequences | 2/team | Unlimited | Unlimited | Unlimited |

Key upgrade triggers:

- **Free → Basic**: Credit ceiling, sequence limit, no dialer, no advanced filters
- **Basic → Pro**: AI lead scoring, unlimited mailboxes/emails, CRM integrations, 10x call recording
- **Pro → Org**: SSO/SCIM, min 3 seats, custom permissions/territories

### Competitive Landscape

| Competitor | Where They Compete | Apollo Advantage |
|------------|-------------------|------------------|
| ZoomInfo | Enterprise data | Free plan + self-serve vs. $15K+ contracts |
| Lusha | VSB prospecting | Broader platform (data + sequences + dialer + CRM) |
| Outreach | Enterprise engagement | Bundles data + engagement, no separate data vendor |
| Salesloft | Engagement/sequences | Built-in data layer eliminates separate subscription |
| HubSpot | CRM + marketing + sales | Data accuracy (97%) and prospecting depth |
| Instantly | Cold email at scale | Verified data + multi-channel + all-in-one |

______________________________________________________________________

## Approved Company Metrics (pre-approved by legal)

These metrics can be used in any artifact without additional legal review:

- **Database:** 230M+ people, 30M+ companies, 97% email accuracy
- **Customers:** 2M+ users, 600K+ companies, nearly 100K paying customers
- **Business:** $1.6B valuation, $250M total raised (Sequoia, BCV, Nexus), grown 5x+ since Series D
- **AI:** 500% YoY AI platform growth, 50K weekly AI users, 46% more meetings booked with AI Research Agent
- **Team:** 800+ people globally, 25 countries. CEO: Matt Curl. Co-founders: Tim Zheng, Ray Li. Founded 2015.
- **Named customers:** Anthropic, Smartling, Redis, Spotdraft, Superside
- **Strategic partners:** Anthropic, Perplexity
- **Accolades:** Deloitte Fast 500 (#119, 2025), Forbes Best Startup Employers (2024, 2025), Double Gold Stevie Awards 2026, MarTech Breakthrough 2025, 624 G2 badges Winter 2026

**Note:** We are no longer proactively disclosing ARR. If asked: "Our most recent publicly cited number was nearly $200M."

### Copy coherence rule

Every claim in a copy artifact must be consistent with the upstream artifacts that informed it. Before finalizing any copy, verify:

- Stats are used in the correct context (don't imply a metric covers a broader population than it does)
- Audience-specific claims match the actual target segment from `audience.md`
- Feature and capability claims match what's described in the brief
- Competitive positioning matches `strategy.md` — don't contradict the framing
- Proof points are attributed to the right source

When combining facts, read the sentence as a skeptical buyer would. If proximity implies a connection that doesn't exist, qualify it or separate them.

______________________________________________________________________

## Notes

- **Fact sheet statistics are pre-approved by legal.** Metrics listed above can be used in any artifact without additional legal review.
- **When voice guidelines and fact sheet language differ:** Voice guidelines govern customer-facing copy. Fact sheet language is appropriate for press, investor, and official company contexts.
