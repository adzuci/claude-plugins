# Account Plan — {{Account Name}}
_Prepared {{YYYY-MM-DD}} · Salesforce ID: {{account_id}}_

## Snapshot
| Field | Value | Source |
|---|---|---|
| Industry | {{industry}} | Salesforce |
| Current ARR | {{ARR}} | Salesforce |
| Renewal date | {{renewal_date}} | Salesforce |
| GTME owner | {{gtme_owner}} | Salesforce |
| Usage / health | {{trend}} | Snowflake / Apollo |

## Account Goal & Strategy
_A small two-row table, before anything else below the Snapshot:_
| | |
|---|---|
| **Account Goal** | _one-two sentence top-line commercial goal for this account (e.g. retain/expand past the renewal, land a specific expansion product)._ |
| **Our Strategy** | _one-two sentence high-level approach to get there._ |
_Derive both rows from the plan's own findings; say so plainly if a confident
goal/strategy can't be derived rather than filling with boilerplate._

## Executive Summary
_3–5 bullets: current adoption headline, biggest known risk or opportunity,
most relevant recent engagement (dated), most relevant recent update from the
account's internal Slack channel (dated). Say so briefly if a category has no
confident signal rather than dropping the bullet silently._
-
-
-

## Action Plan
_Always leave this table empty — see SKILL.md "'Action Plan' is always
blank." Do not fill it in, even with reasonable-looking suggestions._
| Workstream | Action | Owner | Deliver by | Status | Notes |
|---|---|---|---|---|---|
| | | | | | |
| | | | | | |
| | | | | | |

---

## 1. What do we believe is happening in their business?
_Business signals with dates. Why did they buy Apollo? What changed in the last
6–12 months? Which priorities/initiatives/challenges matter most, with evidence._

## 2. Where can we create value?
_Connect priorities to Apollo (see apollo-value-props.md); proof points "per Apollo"._

**Who they sell to → Apollo prospecting play** (from website analysis):
- **Their audience / ICP:** segments, verticals, sizes, regions, buyer personas.
- **Find more ICP:** Apollo firmographic + persona filters for lookalike lists.
- **Intent signals to monitor for their reps:** the specific prospect behaviors
  Apollo can alert on, chosen to fit their buyers.
- **Target lists & personalization:** how Apollo builds lists and tailors outbound.

## 3. Who cares most? — stakeholder map
_Render as a color-coded HTML table (see SKILL.md "Formatting the stakeholder
table"): bold, shaded header row; each row background colored by sentiment
(Champion=green, Influencer=blue, Economic buyer=purple, Detractor=red,
Unknown=gray); one-line color legend. Columns:_
Name (linked to LinkedIn — mandatory, see SKILL.md "LinkedIn links"; if none
found, plain text + "(LinkedIn not found)") | Title | Function | Engaged? |
Exec alignment (confidence) | Sentiment

_**Power users:** include the most frequent Apollo users (tag "Power user"),
sourced from Apollo usage data (per-user activity) or inferred from the active
cohort. These anchor the bottoms-up motion._

_Coverage gaps: functions/personas with no relationship yet._

## Sample Outbound Messages
_Placed here, directly below the stakeholder map, since it's naturally paired
with who to reach out to:_
- **Insight/question an exec would respond to:**
- **Most relevant proof point / customer story:**
- **Single call to action:**
- **Sample outbound from the Apollo AM (1–2):** _messages the account manager can
  send to a power user, champion, or exec at the account to inspire action and a
  reason to engage with Apollo. Draw on the section-2 prospecting play: include
  concrete examples of how Apollo helps them sell into their own core customer
  segments (name a target segment/persona + a relevant intent signal + the play).
  (AM → customer, not customer → their prospects.)_

## 4. Why now?
_The trigger/event making this timely rather than in six months. Date it._

## 5. Value hypothesis
_Focus entirely on the business impact Apollo can make for the customer's own
business — never frame a row around Apollo's renewal/expansion motives.
Populate using only what's already established in the Current State (Snapshot/
adoption above) and section 1/2 (business signals, ICP play) — no new claims
here. Prioritize: key Apollo capabilities the account isn't using, whitespace
opportunities for teams/functions not yet on Apollo, and ways Apollo can help
the customer drive more of their own pipeline, meetings, and revenue. Built on
the Force Management "Command of the Message" framework:_

| Pillar | Current State | Negative Consequences | Future State | Positive Business Outcomes |
|---|---|---|---|---|
| | | | | |
| | | | | |

_Internal single-sentence check, useful while drafting each row but not the
delivered artifact — the table above is the delivered artifact here too:_
> We believe that because {{business priority/event}}, your team is likely trying
> to {{desired outcome}}. We think we can help by {{Apollo solution}} so you can
> {{business impact}}.

---

## Appendix — sources
_Which of Salesforce / Snowflake / Apollo / web / transcripts / Slack / Glean
returned data, and any empty/unreachable. Note anything marked "no confident
signal found"._
