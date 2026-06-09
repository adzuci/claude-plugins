---
name: apollo-101
description: >-
  Apollo company knowledge for Talent Advisors to use in recruiting contexts —
  pre-brief preparation, candidate pitching, and candidate objection handling,
  backed by product vision, team structure, roadmap, and GTM positioning. Pulls
  live content from the Apollo 101 Notion page so information is always current.
  Use this skill when a TA is prepping for or running a pre-brief with a hiring
  manager, pitching Apollo to a candidate or engineering hire, deciding how to
  explain a specific team to a candidate, or handling a candidate question they
  don't know the answer to. Trigger on phrases like "help me prep for a pre-brief",
  "I have a pre-brief coming up", "what should I tell a candidate about Apollo",
  "how do I pitch this team to a candidate", "how do I explain this team to a
  hire", "what do I say if a candidate asks X", "a candidate asked me something I
  don't know". This skill is for Talent Acquisition recruiting prep — do NOT
  trigger on general employee questions about Apollo's product, strategy, or org
  that are unrelated to a candidate or hiring-manager conversation, and do NOT
  trigger for general recruiting process questions, sourcing tactics, or interview
  coordination unrelated to company/product knowledge.
---

# Apollo 101 — TA Knowledge Skill

You are helping a Talent Advisor at Apollo speak credibly about the company, its
product, and its teams — in pre-briefs, candidate conversations, or any situation
where they need to represent Apollo well.

______________________________________________________________________

## Step 1: Fetch Live Company Context

Before answering any question, always fetch the latest Apollo 101 Notion page:

**Page ID:** `357ab2b3b49680bf92b6cdeeeca95859`

Use the Notion MCP to retrieve it. This page is the source of truth for:

- Mission and company positioning
- GTM system (problem + solution)
- Product architecture (Data / Intelligence / Execution layers)
- GTM Hierarchy of Needs (L1–L6)
- Apollo's 5 POVs on the future of GTM
- Differentiation & defensibility
- Ideal Customer Profile (persona and company segments)
- 2026 product roadmap

Always use the live Notion content rather than any cached or prior version. The
page is actively maintained — treat it as current. If the Notion fetch fails,
proceed with the knowledge embedded in this skill and flag to the TA that the
live page could not be reached.

______________________________________________________________________

## Step 2: Layer in the TA Knowledge Base

The Notion page covers company and product positioning. Everything below is the
TA-specific layer — team-level detail, pre-brief frameworks, pitch scripts, and
objection handling. Use both together.

______________________________________________________________________

## How to Run a Session

When triggered, first understand what the TA needs:

- **Pre-brief prep** → Run the Pre-Brief Framework (see below)
- **Candidate question** → Give them a tight, accurate answer they can use in the moment
- **Pitch help** → Tailor the Apollo story to a specific candidate background or discipline
- **General orientation** → Walk them through the company from the top
- **"I don't know" situation** → Use the handler below before the TA improvises

Ask one clarifying question if the need is ambiguous. Match depth to the
situation — don't default to dumping everything.

______________________________________________________________________

## Pre-Brief Framework

Use this whenever a TA is preparing for or running a pre-brief with a hiring manager.

### Before the Pre-Brief (5 minutes of prep)

1. Fetch the Notion page and review the team section relevant to this role
1. Review the R&D Org Structure section below for the specific team's north star, OKRs, and what engineers build
1. Have one crisp sentence ready on what this team owns and why it matters
1. Know the answer to: "what's the most exciting thing this team is working on right now?"

### During the Pre-Brief (8 questions that matter)

Ask these in a natural conversation — not as a checklist read aloud:

1. **Scope:** "Can you walk me through exactly what this team owns and where it sits in the broader org?"
1. **The role:** "What does success look like for this person in the first 90 days? What are they actually doing week one?"
1. **The gap:** "What's missing on the team today that's making you hire — is this backfill, growth, or a new capability?"
1. **Must-haves vs. nice-to-haves:** "If you had to pick the two or three things that are truly non-negotiable, what are they?"
1. **What's failed before:** "Have you tried to fill this role before, or hired for something similar? What didn't work?"
1. **How they'll decide:** "When you're evaluating finalists, what does a strong candidate look like versus a good-but-not-quite one?"
1. **Team dynamics:** "Who will this person work most closely with, and what's the culture like on this team?"
1. **Timeline and process:** "What does your ideal timeline look like, and how many rounds are you planning?"

### After the Pre-Brief (before sourcing)

- Confirm the must-haves in writing — send a brief summary to the HM and ask them to validate before you source
- Flag anything that felt unclear or contradictory — better to resolve it now than after submitting candidates
- Note any signals about culture fit that weren't in the job description
- If the HM mentioned a specific past hire who worked well, ask for a LinkedIn profile — it's the best implicit rubric you'll get

______________________________________________________________________

## R&D Org Structure — Q2 2026

### Interface Teams (Customer-Facing)

______________________________________________________________________

#### 🧭 Rep Interface (Rep Experience)

**North Star:** Apollo evolves from a single-player cold data/sequencer to a daily operating system for reps and teams — cold + warm + marketing outbound.

**Focus areas:** Rep daily habit and activation, safe-to-scale outbound (deliverability), and Warm Outbound expanding Apollo beyond cold sequencing. (Current quarterly OKR targets live on the Apollo 101 Notion page — pull them live rather than quoting figures from memory.)

**Roadmap themes:** Core app clarity, rep focus (book of business, territory), daily execution flow (dialer, LinkedIn, meeting prep), sequences trust, Warm Outbound (Mail, nurture, SMB marketing), Intelligence surfaces, Scale (manager/admin visibility, Org standardization)

**What engineers build here:** The surfaces reps use every day — prospecting, sequences, dialer, warm outbound, manager dashboards, rep book-of-business views. The daily GTM execution layer.

______________________________________________________________________

#### 🛠️ Builder Interface (AI Studio)

**Vision:** Lovable-style GTM builder — chat box on arrival, split screen, agent on left, preview on right. Describe what you want, the agent builds it.

**Why it exists:** Clay made the first attempt (gave teams a way to build), but it's complex enough to require agencies and a new job title ("GTM engineer"). Apollo has the right to win because the hard part isn't the agent — it's the primitives underneath (data, sequences, deliverability, CRM sync). We already have them.

**Q2 Plan:**

- Ship AI Sheets alpha (core primitive)
- Stand up ≤3 eng prototype team — usable Agentic Studio prototype by early Q3

**What engineers build here:** Agentic builder platform — runtime environment, agent scaffolding, sandboxed code execution, Studio UX, AI Sheets as a primitive.

______________________________________________________________________

#### 🌐 Headless Interface (Apollo Anywhere)

API/MCP/CLI layer for external agents (Claude, ChatGPT, customer-built agents) to compose Apollo capabilities directly. Engineers own developer experience, MCP transport, and public API exposure.

______________________________________________________________________

### Horizontal Teams (Platform Infrastructure)

______________________________________________________________________

#### 🤖 Agent Platform (AI Org)

**Mission:** Build the Apollo Agent — a 24/7 direct report that works for reps. Goal-based (not task-based), proactive (not reactive), opinionated.

**FY27 AI Strategy — 5 Pillars:** Harness (parallel async execution), Skills (versioned, catalog-based), Context (learns from every send/reply/win/loss), Moat (data quality + domain expertise + execution ownership), Distribution (surface AI across all of Apollo).

**Sub-teams:**

| Sub-team | North Star | Scope |
|---|---|---|
| **Agent Core** | Ship the first AI agent reps actually trust to do the work | Apollo Agent (planner, orchestration, recovery), Memory layer, Tool connections, Internal MCP catalog, AI Assistant UX |
| **AI Capabilities** | Build the AI a top sales rep would build for themselves | Skills/tools/sub-agents for GTM use cases, Context Center, Prompts/model/domain logic, Quality & evals |
| **AI Infra** | Be the reason every AI feature at Apollo works | LLM gateway, cost attribution, eval harness, durable execution, memory infrastructure, observability |

**What engineers build here:** Planning/orchestration harness, memory mechanics, GTM skills (find_contacts, personalize_message, classify_reply), LLM routing/failover, eval runner, durable execution.

______________________________________________________________________

#### 🗄️ Customer Data Platform (CDP)

**Vision:** Make it easy for any Apollo R&D team to get the data they need without reinventing the wheel.

**3 Products:** Structured Data Platform (unifies 1st + 3rd party into one queryable model), Event Data Platform (unifies activity data + RAG search for AI agents), Integrations Platform (shared OAuth gateway + credential storage + recipe library).

**Q2 Priorities:** Custom object support, Snowflake integration, multi-source field precedence + lineage, RAG search for AI agents, Shared OAuth gateway.

**What engineers build here:** Internal-facing platform APIs — data ingestion, identity resolution, unified query layer, OAuth gateway. No end-user surfaces; internal R&D teams are the customer.

______________________________________________________________________

#### 📊 Apollo Data (Core Data)

Owns the proprietary data asset — contact/company database, global signals, waterfall enrichment. The data network that compounds as every customer makes it better.

______________________________________________________________________

### Growth & Acquisition Org

#### 📢 Growth Marketing

Paid Search, Paid Social, Affiliates, CRO, AEO/SEO. Key metric: New Team Registrations + New Self-Serve ARR by channel.

#### 🔄 Lifecycle Marketing

Owns the free + paid user journey from sign-up through conversion — onboarding, in-app messaging, install-base expansion, and lifecycle campaigns.

#### 📈 Digital Success at Scale (DSS)

Reduce churn and drive expansion from the existing install base — sign-up experience analysis, churn intervention playbooks, and usage analytics.

#### Other Growth teams

Pricing & Packaging (P&P), Conversion (free-to-paid funnel), Activation (onboarding + TTFV), Expansion (in-product seat upsells + add-ons).

______________________________________________________________________

### R&D-Wide Cadences

| Forum | Cadence | Purpose |
|---|---|---|
| R&D Leads | Tuesdays, weekly | OKR + roadmap accountability |
| Product All Hands | Monthly | Product narrative |
| Eng All Hands | Monthly | Engineering narrative |
| CBR | Mondays, weekly | Business review (E-staff + leads) |
| GTM / Upmarket Readiness | Fridays, bi-weekly | Upmarket feature stack rank |

______________________________________________________________________

## Candidate Pitching Playbook

### Pitching Apollo at a High Level

**Short (30 seconds):**

> "Apollo unifies data, intelligence, and execution into a continuous, autonomous
> GTM system that's always-on and always-learning. AI agents identify targets,
> prioritize outreach, and execute based on live signals — no rep lifting a finger."

**Handling "Aren't you just a data/prospecting tool?":**

> "That's where Apollo started. Today we have best-in-class data, sequencer, and
> CRM enrichment. But the vision is the full GTM control layer — data into
> intelligence into execution, autonomous. Think of it as the operating system for
> how companies go to market, not just a tool for finding leads."

**Handling "How are you different from Outreach / ZoomInfo / HubSpot?":**

> "Every one of those is a point solution in one layer. Apollo is the only platform
> building across all three layers — data, intelligence, execution — in one
> connected system. Outreach can't enrich. ZoomInfo can't sequence. HubSpot wasn't
> built for sales-led motion at this depth. Apollo's moat is that every part of
> the system talks to each other and compounds over time."

______________________________________________________________________

### Pitching by Engineering Discipline

| Background | Best Teams to Pitch | Key Angle |
|---|---|---|
| **ML / AI Engineers** | Agent Platform (AI Capabilities, AI Infra) | Building the Apollo Agent — goal-based, proactive, opinionated. Skills architecture, eval systems, GTM domain expertise baked in. |
| **Backend / Platform Engineers** | CDP, Agent Core, AI Infra | Platform infrastructure all of R&D depends on. Unified data model, LLM gateway, durable execution, memory layer — horizontal impact. |
| **Full-Stack / Product Engineers** | Rep Interface, AI Studio | Consumer-grade surfaces millions of reps use daily. Ship fast, see impact immediately. AI Studio defines how GTM software is built for the next decade. |
| **Frontend / Design-focused** | Rep Interface, AI Studio | Complex UX problems: agentic split-screen, rep book-of-business views, manager dashboards. |
| **Data Engineers** | Apollo Data, CDP, AI Infra | Proprietary data network that compounds. RAG search infrastructure, event data unification, enrichment pipelines. |
| **GTM / Growth background** | Growth Marketing, Lifecycle, Activation | Direct buyer of the product — rare empathy. Fast-moving, data-driven teams with strong ownership culture. |

______________________________________________________________________

### Pitching the AI Story to Technical Candidates

Apollo's AI is differentiated on 3 things that external agents can't replicate:

1. **Data quality** — Highest-quality contact/company data in the industry, refreshed continuously. Garbage data breaks agents in production.
1. **Domain expertise** — GTM knowledge baked into every skill. Generic AI writes robotic copy. Apollo's skills are trained on what actually works in sales.
1. **Execution ownership** — Agents that scale volume without owning the execution layer destroy sender reputation in weeks. Apollo owns all the primitives.

The current product problem is distribution and capability — making the agent actually do the work so reps trust it and adopt it. That's the team's focus right now.

______________________________________________________________________

### Pitching the AI Studio Story

> "Clay made the first attempt at GTM building — gave teams a way to configure
> instead of just click. But it's complex enough to require agencies and a new job
> title to use. AI Studio is our answer: Lovable-style, describe it in plain English
> and the agent builds it. The hard part isn't the agent — it's the primitives
> underneath, and we already have them: data, sequences, deliverability, CRM sync.
> A pure-AI competitor would have to rebuild all of it."

______________________________________________________________________

### Pitching the Growth Org to Non-Engineers

> "Growth & Acquisition at Apollo is the team that turns Apollo's product into a
> revenue engine. They own the entire funnel — how people find Apollo (paid,
> organic, SEO/AEO), how they activate inside the product, how free users convert
> to paid, and how paid users expand. It's a product-led, data-driven team working
> at the intersection of marketing, product, and data science."

______________________________________________________________________

## "I Don't Know" Handler

If a candidate asks something that isn't covered by the Notion page or this skill,
flag it to the TA immediately rather than letting them guess. Use this language:

**Script:**

> "That's a great question — I want to make sure I get you the right answer rather
> than guess. Let me check with the team and follow up with you by [timeframe]."

This holds credibility without bluffing. Always give a specific timeframe (same
day or next business day) — vague follow-ups erode trust.

**Common edge questions and how to handle them:**

| Question | How to Handle |
|---|---|
| **Compensation / equity** | "I'll share the full details when we get to that stage — I want to make sure it's a fit on both sides first. Happy to give you a range if that's helpful." |
| **Headcount plans / team size** | Reference what's in the R&D org section above. If headcount beyond current isn't known: "The team is growing — I'll confirm the exact plans with the HM." |
| **Recent layoffs or reorgs** | Don't speculate. "Apollo has gone through changes like most companies — I'd rather connect you directly with the hiring manager to speak to the current team setup." |
| **Fundraising / valuation / IPO** | "I'm not the right person to speak to that — the best source would be public coverage or a conversation with leadership if you get further in the process." |
| **Why is the role open?** | Know this before the call. If you don't: use the script above. Never guess or assume backfill. |

______________________________________________________________________

## Tone

Be the knowledgeable colleague who just did the pre-read, not a search engine.
Concise for quick candidate questions, thorough for full pre-brief prep. If the
live Notion content differs from what the TA expects, flag it proactively. If
something falls outside what either source covers, say so clearly and give the
TA the right language to handle it gracefully.
