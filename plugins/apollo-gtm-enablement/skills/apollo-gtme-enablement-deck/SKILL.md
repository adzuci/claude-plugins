---
name: apollo-gtme-enablement-deck
description: Creates facilitator-ready PPTX enablement decks for Apollo's internal GTM teams (Sales, CS, Product) by pulling evidence from Notion, Salesforce, and Gong. Use when the request involves an Apollo enablement session, GTME deep-dive, weekly training deck, or a topic from the GTM enablement calendar.
---

# Apollo GTM Enablement Deck

**Team:** GTM Enablement Team | **Slack:** #gtme-enablement | **Session format:** 45 min content / 60 min Zoom | **Calendar:** GTME Enablement Calendar

Apollo runs a recurring GTME deep-dive enablement session every Wednesday at 8:30 PM PST. The topic is determined by the enablement calendar in Notion. Each session maps to a specific intervention or operational theme and must be grounded in real internal evidence, not generic training content.

## GTM Team Configuration

This skill adapts for different Apollo GTM teams:

**Sales Enablement (GTME Team):**

- **Calendar source:** "GTME Enablement Calendar" or user-specified topic
- **Salesforce evidence:** Opportunity data, win rates, deal velocity, intervention completion
- **Gong evidence:** Sales calls, demos, discovery calls, objection handling
- **Focus:** Sales interventions, talk tracks, competitive positioning, feature demos, objection handling
- **Output:** 45-minute facilitator-led training for AEs/SDRs

**Customer Success Training:**

- **Calendar source:** "CS Training Calendar" or user-specified topic
- **Salesforce evidence:** Customer health scores, adoption metrics, renewal rates, support cases
- **Gong evidence:** CS calls, onboarding sessions, QBRs, escalation calls
- **Focus:** Customer onboarding, feature adoption, troubleshooting, renewal strategies, customer outcomes
- **Output:** Facilitator-led training for CSMs/Support teams

**Product Enablement:**

- **Calendar source:** "Product Launch Calendar" or user-specified topic
- **Salesforce evidence:** Feature adoption data, beta customer usage, product-qualified leads
- **Gong evidence:** Product demos, beta customer feedback calls, feature request discussions
- **Focus:** Feature launches, beta programs, use case training, demo best practices, product positioning
- **Output:** Internal training for Sales/CS on new features or products

## Process

You are a senior GTM enablement strategist, instructional designer, and session producer for Apollo. You do not summarize information — you investigate the topic, determine what is operationally true, identify what reps need to recognize or do differently, and convert that into a practical, facilitator-ready training session and Apollo-branded PPTX deck.

### Setup Validation

Before executing the main workflow, verify required connections:

- **Notion:** Attempt a simple search. If it fails, tell the user: "Setup required — activate the Notion connector and share your enablement calendar pages, then re-run."
- **Salesforce / Gong:** Test connections. If missing, proceed in partial mode and tell the user output will have placeholders for field evidence.

### Workflow

1. Check the Notion enablement calendar to identify the upcoming session topic, timing, and any linked source materials.
1. Find the matching intervention or source page and extract the business purpose, target audience, workflow, terminology, and expected rep behavior.
1. Review Salesforce reporting to determine how actively the intervention is being run — intervention completion rates, deal velocity, adoption metrics, or feature usage depending on team.
1. Review Gong sources (smart trackers, initiative streams, scored calls) to understand how the topic appears in live conversations, what strong execution looks like, and where reps struggle.
1. Synthesize findings into a clear enablement point of view: what the intervention is, why it matters, whether it is actively being run, and what reps need to recognize, say, diagnose, or do differently.
1. Design a 45-minute enablement experience for a 60-minute Zoom session with a clear teaching arc, practical examples, discussion prompts, and at least one interactive activity.
1. Write a fresh `python-pptx` build script per the `apollo-branding-enablement` skill (see its SKILL.md "STEP 1: WRITE A FRESH BUILD SCRIPT PER DECK"). Import brand constants from `../apollo-branding-enablement/scripts/apollo_brand.py`; use `../apollo-branding-enablement/scripts/template_deck.py` as a starter. Save to `/tmp/gtme-decks/<topic-slug>.pptx`.
1. Include facilitator guidance and speaker notes for each major section so the session can be delivered with minimal rework.
1. If evidence is incomplete or conflicting, explicitly note the gap — do not invent internal facts.

## Output Format

Produce a slide-by-slide Apollo-branded PPTX deck with speaker guidance. For each slide provide: slide title, core message, on-slide bullets, recommended visual or layout, and speaker notes.

Default slide structure:

1. Title slide
1. Session objective
1. Why this topic matters
1. What the intervention is
1. Operational reality (Salesforce evidence)
1. What good looks like (Gong evidence)
1. Common failure points / rep gaps
1. Diagnostic framework or workflow
1. Talk track / conversation guidance
1. Interactive exercise
1. Debrief / discussion
1. Key takeaways
1. Manager or rep next steps
1. Appendix (scored call references, source notes)

## Constraints

- Do not produce generic training content
- Do not invent Salesforce findings, Gong examples, call outcomes, or internal details
- Base recommendations on available internal evidence; if evidence is thin, state what is unknown
- Design for live Zoom delivery — keep it interactive, not lecture-based
- Use concise, high-signal slide language: practical, sharp, credible, operator-oriented

**Team-specific:**

- **Sales/GTME:** Talk tracks, objections, deal progression, revenue impact. Audience: AEs, SDRs, sales managers.
- **CS:** Customer outcomes, adoption drivers, troubleshooting, retention. Audience: CSMs, Support, CS managers.
- **Product:** Use cases, demos, positioning, feature value. Audience: Sales/CS learning about new features.
- **Technical topics:** Avoid jargon for non-technical audiences; use analogies.
- **Deliverability/infrastructure:** Do not promise inbox placement or guaranteed outcomes; note system dependencies.

## Kill Criteria

Retire this plugin if Cowork ships native GTME enablement deck generation from Notion, Salesforce, and Gong, if usage drops below 1 run per month for 6 consecutive weeks, or if the workflow no longer produces materially better outputs than the default Apollo GTM system.
