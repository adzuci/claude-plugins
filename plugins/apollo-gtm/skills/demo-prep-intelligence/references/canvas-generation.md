# Canvas Generation — Slack Deal Room

> **DELEGATE-ONLY — read this before anything else in this file. Decided 2026-07-28 by David Johnson (skill author); see `GOVERNANCE.md`'s Read-only bullet, which governs on any conflict.**
> This skill **never calls a Slack write tool** — not `slack_create_canvas`, not `slack_update_canvas`, not `slack_send_message`, not `slack_send_message_draft`, not with approval, not ever. It **composes** Canvas-flavored Markdown as copyable output. Creating or posting is the SC's own action in Slack, or a delegation to `deal-execution`, which carries its own approval gate.
> Wherever the text below describes calling one of those tools, gating it behind an approval, or orchestrating a create/update, read it as **describing what the composed content is for**, not as authority for this skill to perform it. Those passages predate this decision; the ones that mattered most have been corrected in place, and any that remain are superseded by this banner.
> **Why:** `GOVERNANCE.md` has always forbidden Slack writes absolutely, so the approval-gated creation path this file documented was canonically unauthorized while reading as a feature (found in a full-file audit, 2026-07-28). David's reframe also conserves tokens on larger deals, since the skill no longer carries write-orchestration it never had authority to use.

This reference defines how the skill compiles and formats a Slack Canvas ("Deal Room") that serves as the single shareable reference artifact for everyone on a deal. The Canvas extends the skill's read-only intelligence into Slack — where the deal team actually operates — without breaking the read-only boundary. Every Slack action with side effects (create, update, send) requires explicit per-action SC approval. The skill itself never writes to Slack autonomously.

Load this reference when the SC selects **Build Slack Canvas deal room** from a Pick Your Path menu, or explicitly asks for a deal room, canvas, shared reference, or Slack canvas.

______________________________________________________________________

## When to Offer Canvas Generation

Canvas generation is offered as a Pick Your Path option after any of these major outputs:

- The seven-section demo prep brief is generated.
- The five-part synthesis package is generated.
- The Apollo AI Context Center payload + demo setup prompts are generated.
- The demo flow / SC walkthrough is generated.
- The SC explicitly asks for a deal room, canvas, shared reference, or Slack canvas for the deal.

Canvas generation is never the first output for assigned-opportunity intent. The Assigned Opportunity Router Default Flow (intake summary → copyable message → AE sync questions → Pick Your Path) still runs first. The canvas option becomes available once the SC has selected a downstream path and at least one major intelligence artifact exists in the session.

______________________________________________________________________

## Data Collection Dependencies

The canvas compiles entirely from the current session's existing outputs and source data. It does not introduce new source queries beyond Slack user / channel resolution. Required inputs (when available in the current session):

| Input | Source in current session |
|---|---|
| Deal snapshot (account, stage, ARR, close date, competitor, lead source, SFDC link) | SFDC via Glean (`references/data-sources.md` §1) — already pulled during brief or synthesis. |
| Team roster (AE, SC, shadow SC) | SFDC opportunity owner + SC assignment + Calendar event attendees (internal only). |
| Prospect contacts | SFDC Contact records on the account (already pulled). |
| Company description (offering, business model, ICP) | Apollo AI Context Center payload Overview block, or web research from the brief. |
| Tech stack | Discovery call / Slack / SFDC evidence captured in the brief. |
| Buyer pains (ranked) | Pain Points (Ranked) section of the brief. |
| Data duel results | Only if the SC ran a data duel and its CSV / analysis exists in the session. |
| Demo flow | Recommended Demo Flow section of the brief, or the synthesis package's demo-flow timeline. |
| Meeting link / Zoom URL | Calendar event captured during Calendar + Gmail alignment. |
| Landmines | Landmines section of the brief. |
| Key questions to ask the buyer | Open Questions section of the brief, reframed as askable questions. |
| Next steps (post-demo) | Deal-lifecycle stage / synthesis package Part 5. |
| Shadow briefing | Generated only if a shadow SC is identified on the deal. |

If a required input is missing, render the section with `Unknown` rather than inventing content. Do not pull new source data solely to fill canvas sections; if the brief is missing data, refresh the brief first.

### Slack user / channel resolution

In addition to compilation, the canvas requires:

- `Slack:slack_search_users` — resolve every internal participant (AE, SC, shadow, any internal stakeholder appearing on the canvas) by name or email to their Slack user ID. Used for Slack Canvas profile cards and for DM distribution. If a user is not found in Slack, fall back to plain name + email text and omit the profile card for that person.
- `Slack:slack_search_channels` — search for an active dealroom channel for the account (e.g. `dealroom-{account-slug}`) before distribution. Also cross-check Glean Slack search results for channel matches.

Search-only Slack actions (`slack_search_users`, `slack_search_channels`, `slack_read_canvas`) may run without explicit SC approval where the connector is available, because they do not produce side effects. Any action with a side effect (create canvas, update canvas, send message) requires explicit per-action SC approval — see "Approval Gates" below.

______________________________________________________________________

## Compilation Sections

The canvas is compiled in this fixed order. Each section maps to a specific need during the live demo. Sections without underlying source data are omitted (not invented).

Each section carries an **audience tier tag** — `team-facing` or `SC-only` — that governs whether it appears in the default shared draft (see "Content Sensitivity Filter and Audience Tiers" below). The tag is fixed per section, not per deal.

1. **Status** `[team-facing]` — single-line indicator (`:large_yellow_circle:` prep / `:large_green_circle:` ready / `:red_circle:` blocked). The SC sets the indicator; the skill suggests one based on data quality and gate status.
1. **Deal Snapshot** `[team-facing]` — table: account, stage, ARR, close date, primary competitor, contract / renewal expiry where known, lead source, SFDC opportunity link.
1. **Team** `[team-facing]` — Slack profile cards for AE, SC, shadow SC, plus a small role table.
1. **Prospect Contact** `[team-facing]` — table: name, title, email, notes.
1. **About [Account]** `[team-facing]` — 3-sentence company description grounded in the prospect's own materials or the Context Center Overview block.
1. **Their Tech Stack** `[team-facing]` — single line listing the prospect's relevant stack with a consolidation / Apollo-fit note.
1. **Buyer Pains (ranked)** `[team-facing]` — numbered list with bold pain name and buyer language in quotes. Ranking matches the brief's Pain Points (Ranked) section.
1. **Data Duel Results** `[team-facing]` — table: metric, current state, comparison. Only if a data duel was run in this session.
1. **Demo Flow ([N] min)** `[SC-only]` — table: time block, what to do. Opening line included verbatim. Contains timing and talk-track hooks intended for the person running the demo.
1. **Zoom link** `[team-facing]` — callout block with the Zoom URL.
1. **Landmines** `[SC-only]` — bulleted list with bold labels. Contains response scripts and things to avoid — SC-facing coaching, not for the shared team surface.
1. **Key Questions** `[team-facing]` — 3–5 askable questions for the primary buyer.
1. **Next Steps** `[team-facing]` — bulleted list of post-demo follow-up actions.
1. **Shadow Briefing** `[SC-only]` — condensed who / what / pains / flow / landmines / role briefing for the shadow SC. Only if a shadow SC is on the deal.

Every claim on the canvas must trace to a source in the current session (brief, synthesis package, Context Center payload, calendar event, transcript, SFDC record). The canvas is a presentation surface, not a new source of truth — it does not introduce claims that are not already in the brief / synthesis.

______________________________________________________________________

## Content Sensitivity Filter and Audience Tiers

The canvas is a shared team artifact. Some content the skill assembles during a session is SC-internal and must not leak onto the shared surface. Two mechanisms enforce this: a content sensitivity filter (always on) and audience tier tags (default omission of SC-only sections).

### Content sensitivity filter (always applied)

Before rendering any canvas draft — shared or full — strip SC-internal content that may have entered the session from source data or SC conversation:

- **Scheduling constraints** — the SC's calendar conflicts, availability windows, PTO, or personal scheduling notes.
- **Coaching notes** — feedback to or about the SC, ramp notes, skill-development commentary.
- **AE performance commentary** — assessments of the AE's performance, deal-handling critique, or internal reliability notes about a teammate.
- **Personal context** — any personal detail about a teammate or prospect not relevant to running the deal.

This content is stripped from the canvas even when it appears in the underlying brief or synthesis. When in doubt whether a line is safe for the shared surface, **flag it for SC review** rather than silently including or dropping it: surface the line and ask the SC whether it belongs on the canvas.

### Audience tiers (default omission of SC-only sections)

Each compilation section is tagged `team-facing` or `SC-only`:

- **team-facing** — Status, Deal Snapshot, Team, Prospect Contact, About [Account], Their Tech Stack, Buyer Pains, Data Duel Results, Zoom link, Key Questions, Next Steps.
- **SC-only** — Demo Flow (timing + talk-track hooks), Landmines (response scripts), Shadow Briefing.

The **default shared draft omits SC-only sections.** The skill compiles the team-facing canvas as the default artifact and tells the SC which sections were held back. The SC can request the full version ("include the full SC canvas" / "add the demo flow and landmines") to get all sections rendered.

This is a single-artifact filter, not a two-canvas system. The skill produces one canvas draft at the SC's chosen tier — team-facing by default, full on request. It does not create, distribute, or maintain two parallel canvas artifacts.

______________________________________________________________________

## Canvas-Flavored Markdown Rules

Slack Canvas uses **Canvas-flavored Markdown**, which differs from standard Slack message formatting. Use these rules; violating them either silently breaks the canvas layout or treats the artifact as a Slack message instead of a Canvas.

| Rule | Canvas behavior | Why |
|---|---|---|
| User profile cards | `![](@SLACK_USER_ID)` on its own line | Renders a large Slack profile card. Standard `<@USER_ID>` mention syntax does **not** render in a canvas. |
| Channel cards | `![](#CHANNEL_ID)` on its own line | Renders a channel card. Standard `<#CHANNEL_ID>` does not render in a canvas. |
| Callout blocks | `::: {.callout}` ... `:::` | Renders a styled callout box. Use for the Zoom link, key reminders, or status highlights. |
| Maximum heading depth | `#`, `##`, `###` only | Anything `####` or deeper is treated as plain text and breaks visual hierarchy. |
| Tables | Pipe syntax with `---` separator row | Standard Markdown tables render. Slack message table fallbacks do not. |
| Code blocks in list items | Forbidden | Code blocks nested inside list items break canvas list rendering. Place code blocks as sibling elements. |
| Mixed nested list types | Forbidden | Do not mix bulleted and numbered lists in the same nesting. Rendering corrupts. |
| Slack emoji codes | Allowed | `:warning:`, `:large_yellow_circle:`, `:page_facing_up:`, etc. render natively. |
| Standard markdown links | `[text](url)` | Use for SFDC opportunity links, Gong links, etc. |

Profile and channel cards must be rendered on their own line (no inline text on the same line). Mixing inline text with `![](@USER_ID)` collapses the card to a small avatar.

The skill must produce the canvas content in Canvas-flavored Markdown — never in Slack message Markdown — even when the connector is unavailable and the output is being delivered as copyable text for manual paste. The SC will be pasting into a canvas, not into a message.

______________________________________________________________________

## Canvas Structure Template

Title format: `[Account Name] — Deal Room` (e.g. `Collage Group — Deal Room`).

```markdown
# Status

:large_yellow_circle: Prep in progress

# Deal Snapshot

| Field | Value |
| --- | --- |
| Account | [Account Name] |
| Stage | [Stage] |
| ARR | [ARR or Unknown] |
| Close date | [Close date or Unknown] |
| Primary competitor | [Competitor or Unknown] |
| Contract / renewal expiry | [Date or Unknown] |
| Lead source | [Source or Unknown] |
| SFDC opportunity | [Link](https://...) |

# Team

![](@AE_SLACK_USER_ID)

![](@SC_SLACK_USER_ID)

![](@SHADOW_SLACK_USER_ID)

| Role | Person | Notes |
| --- | --- | --- |
| AE | [Name] | [Owns commercials, intro] |
| SC | [Name] | [Running demo] |
| Shadow SC | [Name] | [Observing, learning the deal] |

# Prospect Contact

| Name | Title | Email | Notes |
| --- | --- | --- | --- |
| [Name] | [Title] | [email] | [Primary buyer / future stakeholder / etc.] |

# About [Account]

[3-sentence company description grounded in the Context Center Overview block.]

# Their Tech Stack

[Tool 1] → [Tool 2] → [Tool 3] → [Tool 4]

[One-line consolidation / Apollo-fit note.]

# Buyer Pains (ranked)

1. **[Pain name]** — "[buyer language in quotes]"
2. **[Pain name]** — "[buyer language in quotes]"
3. **[Pain name]** — "[buyer language in quotes]"

# Data Duel Results

| Metric | [Current source] | [Comparison source] |
| --- | --- | --- |
| Match rate | [N/N] | [N/N] |
| Email fill | [N/N] | [N/N] |
| Industry fill | [N/N] | [N/N] |

[Note any missing comparison data.]

# Demo Flow ([N] min)

| Time | What to do |
| --- | --- |
| 0–5 | [Opening line verbatim] |
| 5–15 | [Block 2] |
| 15–25 | [Block 3] |
| 25–30 | [Wrap / next steps] |

# Zoom link

::: {.callout}
:movie_camera: [Zoom URL]
:::

# Landmines

- **[Label]** — [what to avoid and why]
- **[Label]** — [what to avoid and why]

# Key Questions

1. [Question 1]
2. [Question 2]
3. [Question 3]

# Next Steps

- [Post-demo follow-up action]
- [Post-demo follow-up action]

# Shadow Briefing

[Condensed who / what / pains / flow / landmines / role for the shadow SC. Omit this section if no shadow SC is on the deal.]
```

Headings stay at depth `#`, `##`, `###`. Profile cards render on their own lines. Tables use pipe syntax. The Zoom link uses a callout block. No code blocks live inside list items.

______________________________________________________________________

## Distribution Logic

After the canvas is created, the skill runs a structured distribution flow. **Distribution is never automatic.** The SC must explicitly approve the full draft messages and recipient list before any post or DM is sent.

### Step 1 — Search for an active dealroom

Run `Slack:slack_search_channels` for `dealroom-{account-slug}` and related patterns (e.g. `deal-{account-slug}`, `{account-slug}-deal-room`). Cross-check Glean Slack search results for channel matches. Record:

- `dealroom_status`: `found | not_found | ambiguous | unavailable`
- candidate channel(s)
- destination reasoning

### Step 2 — Choose distribution path

| dealroom_status | Distribution path |
|---|---|
| `found` | Single post in the dealroom channel — all participants see it at once. |
| `not_found` | Fall back to individual DMs to internal participants. |
| `ambiguous` | Show candidate channels to the SC and ask which is the active dealroom (or none → DMs). |
| `unavailable` | Slack connector unavailable. Output Canvas-flavored Markdown for manual copy and skip distribution. |

### Step 3 — Identify deal participants (internal only)

Union of these sources, then filter:

- Calendar event attendees — internal email domains only. Filter out prospect / external domains.
- SFDC opportunity owner (AE) and SC assignment.
- Slack users mentioned in the dealroom or DM threads about the deal (when available in Slack/Glean search).

Exclude:

- The SC themselves — they already have the canvas in this conversation.
- Prospect / customer attendees — never DM external attendees a Slack canvas link.
- External email addresses that resolve to non-internal Slack users.

### Step 4 — Resolve Slack user IDs

For each identified participant, run `Slack:slack_search_users` by name or email to resolve the Slack user ID. If a participant cannot be resolved (no Slack user found), record them as `unresolved` and surface them in the approval block so the SC can decide whether to add them manually or skip them.

### Step 5 — Compose role-aware distribution messages

Compose every distribution message through the Outbound Messaging Pipeline (state → filter → constraints → route → compose → humanize — see SKILL.md "Outbound Messaging Pipeline"). The SC sees the final composed draft. Never render intermediate drafts.

Default role-aware shapes:

- **AE message** — canvas title, meeting context, canvas link.
- **Shadow / support SC message** — canvas title, shadow role context, canvas link, brief note that they're shadowing.
- **Other internal participants** — canvas title, meeting context, canvas link.
- **Dealroom post** (if dealroom found) — canvas title, single-paragraph context, canvas link.

Each message is short (2–4 lines), Slack-message formatted (not Canvas-flavored), and ends with the canvas URL.

### Step 6 — Approval gate

Show the SC a single approval block that contains:

- Distribution path (`Dealroom #channel` or list of DM recipients).
- For each recipient: Slack handle, role, and the full composed draft message.
- Any `unresolved` participants the SC should review.
- One explicit confirmation: "Approve and send all" / "Revise" / "Cancel".

Do not send anything until the SC explicitly approves. Approval is per-distribution-batch, not standing — every future canvas distribution requires a fresh approval. Re-approve if the SC edits any message.

### Step 7 — Send

Hand the composed messages to the SC, or delegate the post / DMs to `deal-execution`, one message at a time. **This skill does not call `slack_send_message` itself** (delegate-only, see banner). Confirm each send result back to the SC. The skill itself does not autonomously call `slack_send_message` without per-message approval.

______________________________________________________________________

## Approval Gates

Slack actions split into two classes by side-effect risk. The skill applies the corresponding approval rule.

| Slack action | Side effect? | Approval required |
|---|---|---|
| `slack_search_users` | No | No — read-only lookup. |
| `slack_search_channels` | No | No — read-only lookup. |
| `slack_read_canvas` | No | No — read-only fetch. |
| `slack_create_canvas` | Write — **never called by this skill** (delegate-only, see banner) | N/A — compose the Markdown; the SC or `deal-execution` creates it. Formerly: show full Canvas-flavored Markdown draft and destination, ask for explicit approval before creation. |
| `slack_update_canvas` | Write — **never called by this skill** (delegate-only, see banner) | N/A — compose the replacement section; the SC or `deal-execution` applies it. Formerly: show target section, current content, proposed update, ask for explicit approval. Never replace the entire canvas without explicit SC approval. |
| `slack_send_message` | Yes (sends Slack message) | **Yes** — show full composed draft and destination, ask for explicit per-message approval. Auto-sending is forbidden. |
| `slack_send_message_draft` | Yes (creates draft visible to recipient) | **Yes** — same approval rule as `slack_send_message`. |

Connector availability changes the offer, not the approval rule. If the Slack connector is unavailable in the runtime, the skill outputs Canvas-flavored Markdown for manual copy only and does not offer creation or distribution. It does not silently skip the approval gate by attempting an alternate path.

Canvas creation is a write action, which is exactly why **this skill does not perform it** (delegate-only, see banner). What this skill owes the SC is the full Canvas-flavored Markdown draft and the proposed canvas title to the SC before calling `slack_create_canvas`.

______________________________________________________________________

## Canvas Update / Refresh Flow

When the SC returns later in the deal and asks to refresh an existing canvas:

1. **Read the existing canvas** with `Slack:slack_read_canvas` and the `canvas_id`. This is read-only and does not require approval.
1. **Identify sections that need updating** based on new information from the current session (new pains surfaced, new attendees, demo flow changed, landmines added, data duel results new). Compare against the existing canvas contents.
1. **Propose a section-scoped update list** to the SC: which sections will change, what the new content will be, what the diff is.
1. **Update specific sections only** — compose the replacement for individual `section_id`s so the SC (or `deal-execution`) can apply a targeted `slack_update_canvas` replace rather than clobbering the whole canvas. **This skill does not make that call** (delegate-only, see banner). Each section update requires explicit SC approval before the call.
1. **Never replace the entire canvas without explicit SC approval.** Whole-canvas replacement is only allowed when the SC explicitly says "rebuild the canvas from scratch" and the skill re-shows the full new draft and destination before calling `slack_create_canvas` on a new canvas (or `slack_update_canvas` with the entire body replaced — both paths require explicit approval).
1. After updating, ask whether to re-distribute the canvas link via the dealroom channel or DMs. Re-distribution follows the same approval gate as initial distribution.

The canvas is a snapshot at the time of creation. It does not auto-refresh as deal context evolves.

______________________________________________________________________

## Tool Dependency Table

| Tool | Purpose | Side effect | Approval |
|---|---|---|---|
| `Slack:slack_search_users` | Resolve names / emails to Slack user IDs (for profile cards and DM distribution) | No | No |
| `Slack:slack_search_channels` | Find an active dealroom channel | No | No |
| `Slack:slack_read_canvas` | Read existing canvas during refresh | No | No |
| `Slack:slack_create_canvas` | Create the Deal Room canvas | Write | **Not called by this skill** — SC or `deal-execution` |
| `Slack:slack_update_canvas` | Update specific canvas sections | Write | **Not called by this skill** — SC or `deal-execution` |
| `Slack:slack_send_message` | Distribute canvas link via DM or dealroom post | Write | **Not called by this skill** — SC or `deal-execution` |
| `Slack:slack_send_message_draft` | Draft distribution message visible to recipient | Write | **Not called by this skill** — SC or `deal-execution` |

This table documents what the *composed output is ultimately for*, so the content can be shaped correctly. It is not a list of calls this skill makes.

If `/deal-execution` is the integration that exposes Slack execution, the skill delegates the actual call to deal-execution after approval. The skill itself remains read-only — it does not own Slack write authority.

______________________________________________________________________

## Read-Only Boundary

- The canvas does not write to SFDC, Notion, Google Drive, Gmail, Calendar, or any non-Slack system.
- This skill writes nothing, to Slack or anywhere else. The eventual canvas creation is performed by the SC or by `deal-execution` under its own approval gate (delegate-only, see banner).
- The canvas content is a snapshot. It does not auto-update when deal context changes elsewhere. Refreshes are explicitly requested by the SC.
- Distribution is internal-only. The skill never DMs prospect contacts, posts to a customer-facing channel, or shares the canvas link with external email addresses.

______________________________________________________________________

## Anti-Patterns

These behaviors are forbidden and must be treated as failures, not stylistic choices.

- Treating Canvas-flavored Markdown as Slack message Markdown (or vice versa). The two are different formats; mixing them silently breaks rendering.
- Using `<@USER_ID>` mention syntax inside the canvas for team members. Profile cards must be `![](@USER_ID)` on their own line.
- Using `<#CHANNEL_ID>` channel syntax inside the canvas. Channel cards must be `![](#CHANNEL_ID)` on their own line.
- Creating a canvas without showing the full Canvas-flavored Markdown draft and the proposed title to the SC, and getting explicit approval, first.
- Sending any DM or dealroom post without first showing every composed draft and the recipient list, and getting explicit per-batch SC approval.
- Skipping the dealroom search before falling back to DMs. The skill must search Slack/Glean for an active dealroom channel before defaulting to individual DMs.
- Distributing the canvas link to external / prospect attendees. Filter prospect email domains out of the calendar attendee list before resolving Slack user IDs.
- Replacing the entire canvas during a refresh without explicit SC approval. Refreshes update specific sections; whole-canvas replacement requires a fresh, explicit approval.
- Composing distribution messages outside the Outbound Messaging Pipeline (state → filter → constraints → route → compose → humanize). Hand-written or model-direct drafts are not allowed.
- Treating prior approval of one canvas action as a standing pre-authorization for future canvas actions. Every write requires a fresh per-action approval.
- Pulling new source data solely to fill canvas sections. The canvas presents existing brief / synthesis content; if data is missing, refresh the brief or render `Unknown`.
- Inventing canvas content — fictional contacts, fabricated buyer pains, made-up tech stack — to make the canvas look complete. Use `Unknown` or omit the section instead.
- Auto-creating or auto-distributing the canvas on the basis of a prior session's behavior. The connector's availability changes what the skill can offer; it never changes the approval rule.
- Rendering SC-internal content (scheduling constraints, coaching notes, AE performance commentary, personal context) onto the shared canvas, or including SC-only sections (Demo Flow, Landmines, Shadow Briefing) in the default shared draft without the SC explicitly requesting the full version. Apply the content sensitivity filter before every render; flag ambiguous lines for SC review.

______________________________________________________________________

## Interaction Flow (what the SC sees)

```
SC: [completes brief / synthesis / Context Center + Apollo AI prompts / demo flow]

Skill: "[Last output] is ready. Pick your path."
  → Build Slack Canvas deal room (share with the deal team)
  → [next relevant option]
  → [next relevant option]
  → Done for now

SC: [selects Build Slack Canvas deal room]

Skill: [compiles canvas content from session, resolves Slack user IDs, searches for dealroom]
       Shows the full Canvas-flavored Markdown draft, the proposed canvas title, and the
       Slack-action plan (create_canvas + distribution path). Asks for explicit approval.

SC: "Approve canvas creation"

Skill: [returns the composed Canvas-flavored Markdown; SC creates the canvas in Slack, or delegates to deal-execution]
       "Canvas is live: [link].
        I found these deal participants to share it with:
        - Geo Flores (AE) — DM (no dealroom found)
        - Greg Leonardo (shadow) — DM
        Here are the composed messages. Approve all, revise, or cancel?"

SC: "Approve all"

Skill: [returns the composed per-recipient messages; SC posts them, or delegates to deal-execution]
       "Sent to Geo and Greg. Canvas link distributed."
```

If at any point the SC says "cancel" or revises a message, the skill recomposes through the pipeline and re-asks for approval before any side-effect call.
