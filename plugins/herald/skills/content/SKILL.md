---
name: content
description: |
  Blog post, launch announcement, SEO brief, and help center article. Produces
  all written content artifacts for the launch. Requires foundation artifacts
  from /herald:foundation.
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

# herald:content

Blog post, launch announcement, SEO brief, and help center article.

Before anything else, read `${CLAUDE_PLUGIN_ROOT}/references/shared-context.md` (launch tiers, Apollo voice, PLG context, approved metrics, copy coherence rule). "Shared context" below means that file. If `${CLAUDE_PLUGIN_ROOT}` is not expanded, the plugin's `references/` folder is two levels up from this skill's base directory.

## Tier Scoping

Read the `Tier` field from `campaigns/[slug]/brief.md` metadata.

- **T1:** All 4 artifacts — blog post, launch announcement, SEO brief, help center article
- **T2:** Blog post + launch announcement + help center article (SEO brief optional — ask user)
- **T3:** Blog post only
- **T4:** Skip this skill entirely. Tell the user content isn't needed for T4 launches and stop.

Read `${CLAUDE_PLUGIN_ROOT}/references/content-platform.md` for Apollo's actual content publishing operations: the `/magazine` vs `/insights` distinction, ButterCMS and Zendesk format requirements, the curated SEO keyword strategy, and gold-standard examples. **Source of truth for which surface to publish to and what format the deliverable needs.**

## Phase 1: Load and Orient

Read `campaigns/[slug]/brief.md`, `foundation/strategy.md`, and `foundation/audience.md`. Verify foundation is done. If not, tell the user to run `/herald:foundation` first and stop.

Assess: blog post angle (feature story, problem/solution, data-led), announcement tone (GA vs. beta vs. limited release), SEO keyword from the **curated AI-agent keyword set** in `content-platform.md` (never invent fresh keywords), help center scope (simple vs. comprehensive). This skill produces a `/magazine` launch post (ButterCMS-ready). `/insights` content is out of scope (handled by Apollo's AI content agent).

Tell the user: "I'll produce 4 artifacts: blog post (`/magazine`, ButterCMS-ready), launch announcement, SEO brief, and help center article (Zendesk HTML)." Include proposed blog angle, SEO keyword (or flag gap), and help center scope.

**STOP.** Wait for go-ahead.

## Phase 2: Outline

### Step 1: Blog post outline

Calibrate against the gold-standard `/insights` examples in `content-platform.md` — the same practitioner-to-practitioner voice and structure apply to `/magazine` launch posts.

Present:

- Proposed title (specific and curiosity-provoking, not generic)
- Hook opener concept (the moment, frustration, or question to start with)
- Section-by-section skeleton:
  - Opening hook (what moment/pain)
  - The problem (what's broken, with specifics)
  - What we built (plain language intro)
  - How it works (which examples/screenshots to feature)
  - Early results (what proof points to include)
  - Get started (CTA)
- Estimated word count
- Target surface: `/magazine` (ButterCMS-ready rich text)

### Step 2: Announcement outline

Present:

- What's new (2-3 sentence draft)
- Key changes list (3-5 items)
- Known limitations to acknowledge

### Step 3: SEO brief outline

Present:

- **Target keyword from Apollo's curated AI-agent keyword set** (see `content-platform.md`). Do not invent fresh keywords. If the launch concept doesn't map to an existing curated keyword, propose the closest fit and **flag the gap** for the Content team to either add the keyword to the curated set or steer the launch toward an existing one.
- Search intent classification
- Proposed page structure

### Step 4: Help center outline

Present:

- Scope: getting started vs. comprehensive guide
- Number of use cases to cover
- FAQ candidates

### Step 5: Key decisions

Use AskUserQuestion for:

1. **Blog angle:** "I'm proposing [angle/title]. Does this feel right, or do you want a different angle?"
1. **Proof points:** "What early results or metrics can I include? Beta numbers, customer quotes, internal benchmarks?"
1. **Known limitations:** "What limitations should we be upfront about in the announcement?"
1. **SEO keyword fit:** "I'm proposing [keyword] from Apollo's curated AI-agent keyword set. Does this map cleanly to the launch, or should the SEO brief flag a gap to Content?"

**STOP.** Wait for approval.

## Phase 3: Draft

### Step 1: Write artifacts

Write to `campaigns/[slug]/content/`:

1. `blog-post.md` — full 800–1200 word blog post following the approved outline. Write it like a real blog post, not a template with blanks. **Format: ButterCMS-ready rich text** — use paragraphs, headings, bullets, blockquotes, and inline links. Avoid Markdown-only constructs (reference-style links, fenced code blocks, footnotes) — the Content team will paste this into ButterCMS and rich-text constructs translate cleanly. Target surface: `/magazine`.

1. `launch-announcement.md` — concise announcement with what's new, key changes, getting started steps, known limitations, and feedback channel. (Internal working doc — Markdown is fine.)

1. `seo-brief.md` — target keyword pulled from Apollo's curated AI-agent keyword set (see `content-platform.md`), search intent, SERP analysis notes, recommended structure, internal linking strategy. **If no curated keyword fits, document the gap** in the brief: which closest curated keyword you're using as a placeholder, and what new keyword the launch would ideally target — flag for Content team review. (Internal working doc — Markdown is fine.)

1. `help-center.md` — plain English getting started guide with setup steps, common use cases, FAQ, and troubleshooting. **Format: HTML** (Zendesk requires HTML — do not write Markdown and assume conversion). Use `<h2>`, `<p>`, `<ul>`, `<ol>`, `<a href>`, `<strong>`, `<em>`, etc.

### Step 2: Coherence review

Re-read the foundation artifacts (`strategy.md`, `audience.md`, and the brief). Scan every claim, stat, and audience reference in the draft against what the foundation actually says. Fix anything that contradicts, overstates, or misattributes.

### Step 3: Update artifact status

Update the Artifacts table in `campaigns/[slug]/brief.md`:

- Set "Blog Post", "Launch Announcement", "SEO Brief", and "Help Center Article" to `done` with today's date

### Step 4: Summary

Tell the user:

- Artifacts written with file paths
- Blog post headline and word count, plus a reminder that it's `/magazine`-bound and ButterCMS-ready
- Help center article note: HTML-formatted for Zendesk
- SEO brief: which curated keyword was used (or which gap was flagged for Content)
- Any sections that need real screenshots, metrics, or customer quotes before publishing
- Remind them that content is independent of other Stage 3 skills
