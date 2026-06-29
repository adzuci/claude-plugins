---
name: add-support-rotation-idea
description: Capture support-rotation observations as Ideation Log entries in Notion, or generate HTML reports of existing ideas.
disable-model-invocation: true
---

# Add Support Rotation Idea

Capture actionable product insight during an EM support rotation. The Ideation Log is for meaningful observations that someone in Support Leadership, Product, or Engineering can act on without a follow-up interrogation.

Ideation Log database target: read `references/notion-connector.md`.

Before any workflow that uses external context or writes/fetches Notion data, read `references/connectivity-test.md` and run the smallest connector check needed for the mode. If setup help is needed, lazily read and share `references/connector-setup.md`; do not load or paste setup instructions when the connectors already work.

Before creating an entry, run `scripts/check_idea_entry.py` against the drafted fields. When the product area, ownership, existing context, impact, duplicate status, or related PRD/ERD status is uncertain, read `references/research-and-erd.md`. Use the local PRD cache there before live Glean PRD searches, and call out to the Glean CLI before asking the user to fill gaps.

## Golden Rule

If someone reading the entry can take action without asking a follow-up question, it is a good entry. Good entries are specific, under 800 words, and backed by clear data.

## Purpose

Use this skill to convert EM support rotation observations into structured, triageable product signals, or to report on existing Ideation Log entries. The goal is to make support experience visible to Product and Engineering in a way that can be reviewed, prioritized, and followed up.

This is not a general notes log. Do not capture routine support handling, duplicate known issues without new signal, vague complaints, or ideas that cannot be acted on without more discovery.

## Route KB Gap Work Elsewhere

If the user is asking to detect, audit, maintain, or update Support KB gaps, do not run this leadership ideation workflow. Redirect them to the moved Support-owned skill:

```text
/apollo-support:support-kb-gap-agent
```

Use this skill only when the work is support rotation idea capture, ideation, or Ideation Log reporting.

## Choose a Mode

- Add idea mode: default when the caller gives a support-rotation observation or asks to create an Ideation Log entry.
- Report mode: use when the caller asks for an idea report, summary, dashboard, HTML report, all ideas, recent ideas, or a timeframe such as `2d`, `1w`, `30d`, or `2026-06-01`.

For add idea mode, check the Notion connector before creating the entry. If classification or related-context research is needed, also check Glean before searching; if the user mentions meeting notes, support rotation debriefs, Granola notes, or recorded discussions, check Granola before relying on it.

For report mode, check the Notion connector, then read `references/report-mode.md` and use `scripts/render_ideas_report.py` after fetching or receiving Ideation Log entries.

## Decide Whether to Log

Log 2-5 meaningful entries per support shift. Err on logging when there is a clear signal and enough context.

### Do Log

- Target 2-5 meaningful entries per shift.
- Entries captured in real time or during end-of-shift wrap-up.
- Observations that create new product, process, or customer-experience signal.
- Entries that include likely root cause, engineering effort to fix, or which squad/team would likely own the fix.
- Friction where a similar Jira issue exists only when the rotation surfaced new signal, new affected users, new impact, or a sharper fix hypothesis.

### Do Not Log

- Routine support handling with no new learning.
- Known Jira issues just because they appeared again.
- Vague complaints without context or specifics.
- Ideas someone could not act on without multiple follow-up questions.

## What Belongs in an Entry

Every strong entry should include enough structured detail that a reviewer can understand the problem and take action.

| Field | Guidance |
| --- | --- |
| Idea Name | `Ideation Log (Your Name) - <3-8 word observation>` — always use this prefix |
| Entry Type | Pick the primary action type, or multiple types only when the database schema confirms multi-select |
| Category Tags | Pick tags such as product friction, customer pain, UX issue, onboarding, or process gap |
| Product Area | Which part of Apollo is affected |
| Impact Level | High, Medium, or Low |
| Effort to Fix | Your engineering estimate |
| Who Is Affected | Plan type, seat count, role, segment, or internal team |
| Shift / Wave Context | When the observation happened |
| Description | Observed friction, gap, or idea with enough detail to act without follow-up |
| Related ERD | Link only after asking the caller when a definitely related ERD exists |

## Entry Type Options

Use one or more when the database allows multi-select:

| Entry Type |
| --- |
| Product Fix |
| Product Enhancement |
| Support Process Feedback |
| Idea to Share with Peer |
| Automation Idea |
| Poor Customer Experience |

## Quality Examples

| Quality | Example |
| --- | --- |
| Bad | "Customer had trouble with sequences." No title, no product area, no friction detail, no impact level. A reviewer cannot act on this. |
| Good | "Manual email step hidden in sequence builder. Type: Product Fix. Area: Sequences. Impact: High. Effort: Low. Who: Professional, 5 seats, first-time user. Description: Customer could not find how to add a manual email step. The button is hidden under a dropdown with no visual affordance. Hypothesis: a UI label or tooltip would resolve this for most first-time users." |

## Write the Entry

If the observation lacks enough detail to classify, route, or make actionable, ask a focused clarification question before drafting or creating the entry. Prefer one question that unlocks the missing field, such as "Which product area was affected?" or "What customer/support behavior did you observe?"

**Impact Level** is the user's gut feel — do not be prescriptive. Present your read lightly ("feels Medium to me") rather than asserting it. If the signal could reasonably be Medium or High, ask before assigning: "This feels like it could be Medium or High impact — what's your gut?" Do not ask if the level is clearly Low or clearly High.

Run `scripts/check_idea_entry.py` before creating the final entry:

```bash
python3 scripts/check_idea_entry.py \
  --title "Ideation Log (Your Name) - <3-8 word idea name>" \
  --description "<entry description>" \
  --product-area "<product area>" \
  --entry-type "<entry type>" \
  --impact "<High|Medium|Low>" \
  --effort "<effort estimate>" \
  --who "<affected users>" \
  --next-step "<owner/team/action>"
```

Fix any script errors before creating the Notion page. Treat warnings as prompts to research with Glean or ask the caller.

Produce a compact Notion-ready body:

```markdown
## Observation
<what happened, with the specific customer/support evidence>

## Why it matters
<customer, support, product, or engineering impact>

## Suggested next step
<owner/team/action>

## Related context
<optional ERD or source links approved by the caller>
```

Keep it specific and rooted in observed behavior. If the evidence is thin, say what is unknown.

## Triage and Lifecycle

Entries are reviewed after each wave by Support Leadership and Product. High-impact, low-effort ideas may be fast-tracked. Items escalated to Product may be forwarded into Productboard.

Lifecycle:

- `New` - just logged, not yet reviewed.
- `Under Review` - being assessed by Leadership or Product.
- `Prioritized` - accepted for action.
- `Backlogged` - valid but not immediately actionable.
- `Will Not Fix` - reviewed and closed.

Fast-track criteria:

- High impact and low effort.
- Item escalated to Product may go into Productboard.
- Goal is entries that can be triaged, not just noted.

## Create in Notion

Read `references/notion-connector.md` for the database target, creation defaults, clarification rule, and optional Granola MCP guidance. Read `references/research-and-erd.md` when any classification is uncertain or when you need to check for an existing related ERD.

If Notion tools are available, create the entry after classification using the Ideation Log target in `references/notion-connector.md`. Do not require the user to provide the database again.

If Notion is unavailable, do not dead-end the user. Draft the Notion-ready entry, include the Ideation Log database link, and say that you can create it after the connector is enabled or the user can paste it manually. Read `references/connector-setup.md` only when the user wants setup help or the connector failure blocks their requested mode.

Use these defaults unless the user says otherwise:

- `Status`: `New`
- `Linked KR`: `KR 1.4 — Ideation Capture`
- `Escalated to Product?`: unchecked
- `Date`: today's date

## Recap

After drafting or creating the entry, return a short recap with:

- The 3-8 word idea name.
- The Ideation Log database target from `references/notion-connector.md`.
- The created entry URL, if created in Notion.
- Key classification fields: entry type, category, product area, impact, effort, status.
- Any related ERD offered to or approved by the caller.
- Any related PRD offered to or approved by the caller.
- Any clarification still needed before the entry can be acted on.

## Roadmap

Pause on implementing Notion API uploads for now. If IT approves Notion personal access tokens for this workflow, image support can be added later with a small helper that uses the Notion file upload API to upload local screenshots, then appends them to the Ideation Log page as image blocks or files properties. Track the approval/context thread here: <https://apolloio.slack.com/archives/C03RULANP33/p1782493670266309>.

Until then, support only URL-based images through Notion MCP. For pasted or local screenshots, create the idea with a `Screenshot pending` note and tell the user to paste the screenshot into the Notion UI manually.
