---
name: accountplan
disable-model-invocation: true
description: >-
  Builds a comprehensive account strategy plan for a named customer account
  (or Salesforce ID) from Salesforce, Snowflake, Apollo MCP, Slack, and web
  research, delivered as a page in the MM AM Account Plans Notion database
  (Google Doc fallback if Notion isn't connected). Invoke explicitly via
  /apollo-gtm:accountplan.
---

# Account Plan Builder

## What this does

Given one named customer account, this skill produces an account strategy plan
that helps an account manager penetrate whitespace and drive retention and
expansion. It gathers evidence from several systems, researches the customer's
business, and assembles everything into the standard six-question account plan
template as a page in the MM AM Account Plans Notion database (or a Google Doc
if Notion isn't connected).

The value is consistency and grounding: every plan follows the same structure,
every claim is backed by a cited source with a date where available, and gaps
are marked honestly rather than filled with guesses.

## Step 1 — Identify the account and run autonomously

The user will ask to "build an account plan" and give either an account name or
a Salesforce account ID. **Run the whole skill end-to-end without asking the
user any clarifying questions.** Resolve ambiguity yourself and state your
resolution in the output rather than pausing to ask — the person invoking this
skill wants a finished plan back, not a dialogue.

1. Find the account in Salesforce (see `references/data-sources.md` for the
   query). Resolve to a single account and its Salesforce account ID.
2. **If the name is unambiguous (one match, or a Salesforce ID was given
   directly), just proceed.** Do not ask the user to confirm it — echoing back
   the name and ID inside the finished plan's header is sufficient
   confirmation.
3. **If the name is genuinely ambiguous (multiple distinct accounts share the
   name)**, don't ask which one — pick the best match yourself (highest ARR,
   or the one with an open renewal/opportunity, in that order) and state the
   assumption plainly in the plan's snapshot header (e.g. "Multiple Salesforce
   accounts matched 'Acme' — used the highest-ARR match, Acme Corp
   (0015a...), per Salesforce"). This mirrors how `account-detail` handles the
   same situation.

## Step 1a — Check for an existing plan before building

Before doing any research, check whether this account already has a page in
the MM AM Account Plans Notion database (see `references/notion-output.md`
for how to query it, by Salesforce ID first, account name second). This
determines the output mode automatically — **don't ask the user whether to
create a new page, update the existing one, or make a duplicate:**

- **Existing page found** → regenerate the plan and **update that page in
  place** (`notion-update-page`, `replace_content` for the body, plus
  `update_properties`), so there is always exactly one live plan per account.
  Keep the same page URL/ID; don't create a second page.
- **No existing page** → create a new one as normal.

The only exception is if the user's own request explicitly asks for a second/
duplicate/test copy (e.g. "make another one to test" or "don't touch the real
page") — in that case, honor that instruction literally and create a new page
without touching the existing one.

## Step 2 — Source responsibilities

Pull each type of evidence from its owning source. Read
`references/data-sources.md` for concrete query patterns and tool names before
running queries.

- **Salesforce** — account record, ARR, renewal date, open and closed pipeline,
  contacts, and the **GTME owner** (see GTME rule below).
- **Snowflake** — product usage, consumption, and health: the "are they actually
  using it" signal, including direction of travel over recent periods.
- **Apollo MCP** — firmographic enrichment, hiring / job-posting signals, and the
  stakeholder map (see stakeholder spec below).
- **Web research** — business signals: the customer's website, recent news,
  LinkedIn, product launches, earnings, blog posts, hiring, and case studies
  from their own site.
- **Transcripts (Granola / Gong / Fireflies) + Slack + Glean** — sentiment, exec
  alignment, and internal context that won't appear in any system of record.
- **One-sheets** — Apollo value props and proof stats, distilled in
  `references/apollo-value-props.md`. Use these to answer "where can we create
  value" and to build the value hypothesis.

## Step 3 — Research scope and stopping rule

"Deep research" can run forever, so bound it. For the customer's business,
check these source types, then stop and synthesize:

1. Their website (positioning, products, customers/case studies, **and who they
   sell to** — see the ICP analysis below)
2. Recent news / press
3. LinkedIn (company page, leadership posts, headcount trend)
4. Product launches / release notes / blog
5. Earnings or funding, if public/available

Capture the 6–12 month change story: what has shifted in their business, and
what priorities or initiatives that implies. **Put a date on every research
finding where one is available** so the reader knows how recent it is. Then move
on — don't keep digging for marginal signal.

### Who does this account sell to? (ICP → Apollo prospecting play)

When reviewing the account's website (homepage, product/solutions pages,
customer/case-study pages, and any "industries we serve"), explicitly work out
**who the customer sells to**, because that is the raw material for how Apollo
helps them find and win more of their own market:

- **Audience & segments:** what customer types, company sizes, industries/
  verticals, and regions do they target? Which buyer personas and titles do they
  sell to (e.g. CISO, VP Security, IT Director)?
- **Their ICP in Apollo terms:** translate that audience into the firmographic +
  persona filters Apollo would use to build lookalike target lists (industry/
  NAICS, headcount, geography, technologies used, titles/seniority).
- **Relevant buying-intent signals:** propose the specific prospect behaviors
  Apollo can monitor to alert *their* reps at the right moment. Apollo can
  research a wide variety of signals — pick the ones that map to this account's
  buyers. Examples to choose from: hiring for relevant roles, recent funding,
  leadership/exec changes, new tech adoption or a competitor/rip-and-replace
  technology footprint, headcount growth in a target department, website-visitor
  intent, news/press triggers, and keyword/topic intent. Name the handful that
  fit *this* customer's ICP, not a generic list.
- **Target-list & personalization play:** describe how Apollo would build the
  target lists (saved searches on the ICP above) and use AI research + the
  Context Center to tailor personalized outbound around each segment's pains.

Turn these findings into **concrete, usable output** (not theory): put the
ICP/signal/target-list play into the "Where can we create value" section.
Then use it directly inside the **AM → customer** sample outbound messages
in the "Sample Outbound Messages" section, below the Stakeholder Map (see
Step 4, item 6) — those messages should give concrete examples of how Apollo
would help the customer prospect *their own* market (e.g. "surface [their
ICP persona] at [their target segment] the moment [signal] fires"), not
literal snippets the
customer's own reps would send to their own prospects. The message direction
is always the Apollo AM writing to the customer; showing the customer Apollo
working on *their* go-to-market (as an illustration inside an AM message) is
the persuasive expansion argument — the ICP play should never be delivered as
ready-to-send customer→prospect copy.

## Step 4 — Output document structure

The canonical structure to produce is the Notion page format in
`references/notion-output.md` ("Content template") — use that when delivering
to the MM AM Account Plans database, which is the default output. The six
questions below describe the underlying content model (what each section must
establish); `references/notion-output.md` shows how those map onto the actual
page sections, in this order: Account Goal & Strategy, Executive Summary,
Action Plan, Current State, What's Happening in Their Business, Value
Hypothesis, Stakeholder Map, Sample Outbound Messages.

### Account Goal & Strategy (opens the page)

The very first thing on the page, before the Executive Summary, is a small
two-row table:

| | |
|---|---|
| **Account Goal** | *(one or two sentences: the top-line commercial goal for this account — e.g. retain and expand past the Jan 2027 renewal, or land a specific expansion product)* |
| **Our Strategy** | *(one or two sentences: the AM/GTME's high-level approach to get there — e.g. "fix adoption first to de-risk the renewal, then open the Inbound expansion conversation with marketing")* |

Derive both rows from the plan's own findings (renewal risk, adoption state,
biggest opportunity) rather than inventing generic language — this is the
one-line frame the reader should carry into everything below it. If a
confident goal or strategy can't be derived from the evidence gathered, say so
plainly in the cell rather than filling it with boilerplate.

### Executive Summary (opens the body, above Current State)

Right after Account Goal & Strategy, give a busy reader the state of the
account at a glance in **3–5 bullet points**. Cover, in whatever order makes
sense for the account:

- **Current adoption** — the headline usage/health read (growing / flat /
  declining, and the standout feature(s)).
- **Known risks or opportunities** — the single biggest risk and/or the
  single biggest whitespace/expansion opportunity, named plainly.
- **Recent engagements** — the most relevant recent call/meeting/touchpoint
  (transcripts, Salesforce activity), dated.
- **Recent Slack context** — the most relevant recent update from the
  account's internal Slack channel (see `references/data-sources.md` §5 for
  how to find it), dated.

Each bullet should be groundable to a source named elsewhere in the plan —
this section is a summary of what follows, not new analysis. If a category
above has no confident signal, say so briefly rather than omitting the bullet
silently (e.g. "No recent Slack activity found in the account channel").

### Action Plan (comes right after the Executive Summary)

See "'Action Plan' is always blank" below for the spec — it sits third on the
page, before Current State, not inside it.

If you're instead producing a Google Doc (Notion unavailable, or the user asked
for both), use `assets/account-plan-template.md`, which follows the
six-question structure directly. Above the questions, include a short snapshot
header (account name, Salesforce ID, ARR, renewal date, GTME owner). Every
section must be backed by cited evidence with dates where available.

1. **What do we believe is happening in their business?** — business signals from
   web research and usage. Why did they buy Apollo? What changed in 6–12 months?
   What priorities/initiatives/challenges look most important, and what evidence
   supports that (earnings, hiring, leadership posts, launches, news, usage)?
2. **Where can we create value?** — connect those priorities to Apollo using
   `references/apollo-value-props.md`. Which outcomes matter most to them, and
   what proof/customer examples support that Apollo has solved it before?
   **Include the ICP → Apollo prospecting play** from the website analysis: how
   Apollo's AI signals and research can help this customer find more of their own
   ICP, surface the buying-intent signals relevant to their buyers, build target
   lists, and personalize outbound to their market.
3. **Who cares most?** — the stakeholder map (see spec below).
4. **Why now?** — the trigger or event that makes this timely rather than in six
   months.
5. **What is our value hypothesis?** — This section's job is to focus
   entirely on **the business impact Apollo can make for the customer's own
   business** — not on Apollo's renewal or expansion motives. For Notion
   output (the default), deliver the 2–3 pillar table described in
   `references/notion-output.md` ("Value Hypothesis"), built on the **Force
   Management "Command of the Message"** framework: one row per pillar, with
   columns for **Current State**, **Negative Consequences**, **Future
   State**, and **Positive Business Outcomes**. Populate every row using only
   what the plan has already established in the **Current State** and
   **What's Happening in Their Business** sections above — don't introduce
   new claims here. Specifically draw on:
   - **Key Apollo capabilities they're not using** — pull straight from the
     Feature Usage table's 🟡/🔴 rows; each underused capability is raw
     material for a "Current State" cell (what's not happening today) and a
     "Future State" cell (what using it well would look like).
   - **Whitespace opportunities for teams not yet using Apollo** — pull from
     Seat Whitespace and the Stakeholder Map's coverage gaps (e.g. a function
     or team with no Apollo footprint yet); frame as a pillar in its own
     right when a specific team/whitespace opportunity is concrete enough.
   - **Ways Apollo can help drive more pipeline, meetings, and revenue for
     the customer's own business** — pull from the ICP/prospecting play and
     the dated business developments in "What's Happening in Their
     Business"; the Future State and Positive Business Outcomes cells should
     name a concrete customer-facing impact (more pipeline in a named
     market/segment, faster time-to-meeting, etc.), not an Apollo-internal
     outcome like renewal or seat expansion.
   Within each pillar's write-up, you may still use the classic
   single-sentence framing as a useful internal check —
   > We believe that because [business priority/event], your team is likely
   > trying to [desired outcome]. We think we can help by [Apollo solution] so
   > you can [business impact].
   — but the delivered artifact is always the Current State/Negative
   Consequences/Future State/Positive Business Outcomes table, never a single
   quoted sentence. This applies equally to the Google Doc fallback
   (`assets/account-plan-template.md`), which uses the same table.
6. **How will we start the conversation?** — the outreach: an insight or question
   an exec would respond to, the most relevant proof point/story, and a single
   clear call to action. **Include 1–2 sample outbound messages that the Apollo
   account manager can send to the account** — to a power user, champion, or
   exec — to inspire action and give them a reason to engage with Apollo. These
   are the AM's messages TO the customer, not the customer's messages to their
   own prospects. **Draw directly on the "who they sell to → Apollo prospecting
   play"** from the "Where can we create value" question above: give concrete
   examples of how Apollo would help this customer sell into *their own* core
   customer segments — name a real segment/persona they target and a relevant
   intent signal, and show the resulting play (e.g. "surface [their ICP
   persona] at [their target segment] the moment [relevant signal] fires, then
   auto-build a personalized sequence"). Anchor it with their own usage wins
   and renewal timing so the message is both credible and timely. **Mark the
   specific segment/signal plays as illustrative** — the ICP is grounded in the
   account's public positioning, but the exact signals (e.g. a compliance
   deadline or cloud-migration trigger) are hypotheses. Note that the rep
   should validate them against what the customer's team actually prioritizes
   (e.g. with a power user or at the onsite) before treating them as the
   committed plan. **This content is delivered in the "Sample Outbound
   Messages" section, placed directly below the Stakeholder Map** (see
   `references/notion-output.md`), since it's naturally paired with knowing
   who to reach out to.

**If you cannot find anything you're confident in for a question, say so
explicitly** in that section (e.g. "No confident signal found for X") rather
than inventing an answer.

## "Action Plan" is always blank

The **Action Plan** section (renamed from "Key Actions We Want To Take"; see
`references/notion-output.md` for its exact placement — third on the page,
right after Account Goal & Strategy and the Executive Summary, before
Current State) is **always delivered as an empty table** — headers only
(Workstream / Action / Owner / Deliver by / Status / Notes), no rows filled
in. This is deliberate: it's the account manager's own space to commit to
next steps in their own words, not a place for the skill to inject its own
recommendations. **Never pre-fill this section**, even with reasonable-
looking suggestions and even though it now sits near the top of the plan —
its position changed, but its purpose (and its emptiness) didn't. There is no
separate "Next Immediate Actions" or milestone-plan table elsewhere in the
skill's output; the Action Plan table is the only forward-looking-actions
table, and the skill never populates it.

## Stakeholder map spec (question 3)

Use Apollo MCP to map the relevant people to engage for expansion and renewal,
covering at least: **sales leadership, revenue operations, marketing leadership,
and sales enablement**. For each stakeholder, provide:

| Field | How to determine it |
|---|---|
| Name & LinkedIn | **Mandatory.** Every stakeholder's name must be hyperlinked to their LinkedIn profile. See "LinkedIn links" below. |
| Title | Apollo people search; cross-check Salesforce contacts |
| Function | Which of the target functions above they cover |
| Engaged? | Yes/No — are we already in contact (Salesforce contacts/activity, transcripts, Slack)? |
| Exec alignment | Are they aligned with an Apollo exec? Infer from SFDC contact roles, exec presence in transcripts, or Slack — and **mark a confidence level (high/med/low)**. |
| Sentiment | Champion / Influencer / Economic buyer / Detractor — based on evidence (transcript tone, meeting cadence, who advocates). **Flag when it's an inference, not established.** |

Exec alignment and sentiment are the hardest signals — there is no clean field
for them. Base them on evidence and hedge honestly. A confident-but-wrong
stakeholder read is worse than a clearly-hedged one.

### LinkedIn links (mandatory, every stakeholder)

Every row in the stakeholder table must render the person's name as a
hyperlink to their LinkedIn profile: `[Name](linkedin-url)`. Source the URL in
this order and take the first hit:

1. Apollo MCP people search / org enrichment (`linkedin_url` on the person or
   org record).
2. Salesforce Contact record, if it carries a LinkedIn URL field.
3. Web search for `"<name>" <company> linkedin` as a last resort.

**Never fabricate or guess a LinkedIn URL** (e.g. never construct
`linkedin.com/in/firstname-lastname` from a name pattern). If no URL is found
through any of the above, render the name as plain text with an explicit
`*(LinkedIn not found)*` note next to it — this is expected for some contacts
and is preferable to an invented or unverified link.

### Power users (bottoms-up motion)

Beyond leaders, identify the account's **power users — the people using Apollo
most frequently** — and include them in the stakeholder map (tag their row
"Power user"). Source them from Apollo usage data: per-user activity from
Snowflake / Apollo A360 (logins, sequences built, emails sent, meetings booked),
the Apollo team view, or the most Apollo-active contacts in Salesforce/Slack. If
per-user usage isn't available, infer likely power users from the most active
engaged cohort and mark it as inferred.

Power users are the entry point for a **bottoms-up strategy**: engage them first
to learn what's working, what's clunky, and what they'd want more of, then carry
those team-level insights up to the relevant leader as concrete, credible
evidence. The action plan must reflect this sequence: which power users to engage,
what to learn, and which leader to bring those insights to.

### Formatting the stakeholder table (make it easy to scan)

Render the stakeholder map as a visually clear table, not plain text:

- **Bold the column headers** and give the header row a shaded background
  (e.g. a dark fill with light text, or a light-gray fill).
- **Color-code each row by sentiment** using cell background colors so the reader
  can scan status at a glance. Use a consistent legend:
  - Champion → green
  - Influencer → blue
  - Economic buyer → purple
  - Detractor → red
  - Unknown / unconfirmed → gray
- Optionally shade the "Engaged?" cell (green = yes, gray = no) and show the
  confidence level as a short tag (High / Med / Low).
- **Include a one-line legend** above or below the table explaining the colors.

**For Notion output** (the default): use Notion-flavored Markdown tables per
`references/notion-output.md` — set `header-row="true"` on the `<table>`, and
apply cell background colors with a `color="..._bg"` attribute on each `<td>`
(e.g. `color="green_bg"`), per the Notion markdown spec. Do not use raw HTML
tags for this.

**For Google Doc output** (fallback only): the doc is created from HTML, so
apply these with inline HTML on the table instead: bold headers via `<th>` (or
`<strong>`), and cell background colors via a `style="background-color:#RRGGBB"`
(or `bgcolor`) attribute on the `<td>`/`<tr>` — Google Docs preserves table
cell shading and bold on import. Keep text readable (dark text on light fills,
light text on dark fills).

## GTME rule

Use the **GTME owner** (GTM Engineer / GTME owner field) for account ownership.
**Do not use any CSM or CS-ownership fields.** Field names are custom — use
`salesforce_describe_object` on `Account` to find the GTME/GTM-owner field, and
explicitly ignore CSM/CS-owner fields even if they're populated.

## Output format

Primary output: a page in the **"MM AM Account Plans"** Notion database. Read
`references/notion-output.md` before writing anything — it has the exact
database/data-source IDs, the property schema (including the fixed select
options), and the content template to follow. Use the Notion connector's
`notion-create-pages` tool with the data source as parent, and populate both
the database properties and the page content as described there.

If the Notion connector is **not** available in this session, don't silently
fall back — tell the user: "To deliver this into the MM AM Account Plans
Notion database, please connect Notion to Claude (Settings → Connectors), then
re-run." Offer a Google Doc as an alternative in the meantime:

- If Google Drive is connected, you may produce a Google Doc version too (name
  it `Account Plan — <Account Name> — <YYYY-MM-DD>`) — either as the immediate
  fallback when Notion isn't available, or in addition to the Notion page if
  the user explicitly asks for both.
- If neither connector is available, offer Word or Markdown instead, and
  proceed only in whichever format the user chooses.

## Guardrails

- **Never fabricate** numbers, contacts, quotes, or activity. Empty source →
  say so in that section.
- **Attribute every figure to its source** (e.g. "ARR per Salesforce",
  "consumption per Snowflake", "75% more meetings per Apollo") so a reviewer can
  separate grounded data from inference.
- **Degrade gracefully.** Not every account has Slack chatter, transcripts, or
  Snowflake usage. Build from what's available and mark missing sections
  explicitly.
- **Date your evidence** wherever a date exists, especially research findings.
- Financial and commercial figures are inputs for the account manager's
  judgment, not recommendations — present them plainly.
- If a connector returns an auth error, note it and continue with other sources.

## Reference files

- `references/data-sources.md` — query patterns and tool names per system.
- `references/apollo-value-props.md` — Apollo value props + proof stats for
  questions 2 and 5.
- `references/notion-output.md` — database/data-source IDs, property schema,
  and page content template for delivering into the MM AM Account Plans
  Notion database (the default output).
- `assets/account-plan-template.md` — six-question template to use when
  delivering as a Google Doc instead of (or alongside) the Notion page.
