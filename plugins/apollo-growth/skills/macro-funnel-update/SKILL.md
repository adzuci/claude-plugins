---
name: macro-funnel-update
description: Draft a team's weekly Macro Funnel section from the Notion roadmap, capped at 3 hits and 5 notable mentions, with an adversarial selection review.
disable-model-invocation: true
requires_config: true
---

# Macro Funnel Weekly Update

Drafts a team's section of the weekly **Macro Funnel** doc: a fast, cross-team check-in that runs live in a meeting where each team gets three minutes. Three blocks per team:

1. **Top 3 Hits** (max 3, often fewer)
1. **Notable Mentions** (max 5)
1. **💡Top Takeaway** (exactly one sentence)

Source of truth is the Notion roadmap database. Takes one or more teams as input, plus optional must-include items.

Usage: `/apollo-growth:macro-funnel-update [team names] [--include "Roadmap item name"]`

## Configuration

Before doing anything else, read `config.md` from this skill's directory. It contains a YAML frontmatter block of variables this skill depends on.

For every `{{placeholder}}` you encounter while running this skill, substitute the matching value from `config.md`'s frontmatter.

`config.md` ships with the skill, so treat it as **defaults and documentation, read-only**. A plugin update replaces it.

Your own answers live in `~/.claude/plugin-config/apollo-growth/macro-funnel-update.md`. Read that file first when it exists and let it override the shipped values, remembering that a saved empty string is a deliberate answer, not a missing one.

If a value is still `<UNSET>` after that merge, ask the user for it, then write the answer to `~/.claude/plugin-config/apollo-growth/macro-funnel-update.md` (creating the directory if needed). Never write answers back into the skill's own `config.md`; they'd be wiped on the next plugin update. Do this once per session.

**Roadmap data source:** `{{notion_roadmap_data_source}}`
**Local drafts:** `{{macro_funnel_output_dir}}/{YYYY-MM-DD}-macro-funnel.md`

## What the room actually wants

The meeting's own framing shapes everything below, so read it before selecting anything:

> Quick, high-signal check-in on only experiments driving our key metrics. What's live, what shipped, what concluded, what's next, and any blockers. **What isn't a hit?** It's not a project, or BAU, or homework, or something you'd skip over. It's okay to not have any hits this week.

Two consequences.

**Only the Top 3 get discussed out loud.** Notable Mentions exist so the room can see the rest without spending time on it. So the Top 3 should be the three things the author would actually want to talk about with eight other teams listening.

**Padding costs more than a short section.** Three minutes across eight teams means a weak third hit crowds out a strong one somewhere else. One genuinely good hit beats three mediocre ones, and an empty week is an allowed answer. Resist the pull of the number 3.

## Inputs

**Teams (required).** One or more. If none are named, default to `{{default_teams}}` and ask whether the user wants others. Map each team name to roadmap filters:

| Team said as | `Area` contains | `Delivery team` = |
|---|---|---|
| Growth Conversion, Conversion | `Product - Conversion` | `Conversion` |
| Expansion | `Product - Expansion` | `Expansion` |
| Activation | `Product - Activation` | `Activation` |
| Lifecycle | `Lifecycle` | `Lifecycle` |
| Pricing & Packaging, P&P | `Pricing & Packaging` | `Pricing & Packaging` |
| Digital Success, DSS | `DSS` | (none) |
| Growth Marketing, GM | `Growth Marketing` | (none) |
| CRO | `CRO` | (none) |
| Extension | `Product - Extension` | `Extension Team` |

Match on either field with `OR`. Items are tagged inconsistently, and a missing `Area` tag shouldn't hide a real launch. `Area` is a multi-select stored as a JSON array, so use `LIKE '%...%'`. `Delivery team` is a single select, so use `=`.

If your roadmap uses different team names or properties, edit this table. It's reference data, not config.

**Must-include items (optional).** The user may name specific roadmap items. Those are guaranteed placement, and they land in Top 3 unless the user says otherwise or including them would push out something clearly bigger, in which case put them in Notable Mentions and say why in the review message. They were asked for a reason, usually visibility with another team, so never silently drop one.

## Workflow

### Step 1: Set the week and load last week's draft

The Macro Funnel is dated by the Monday it covers. Work that date out (today if it's Monday, otherwise the most recent Monday unless told otherwise).

Glob `{{macro_funnel_output_dir}}/*.md` and read the most recent file. You need it for one reason: **anything that was "Coming Up" last week has to resolve this week.** It either launched (a hit), or it slipped (an honest one-liner), or it's genuinely unchanged, in which case it isn't news and shouldn't reappear. Repeating last week's "Coming Up" verbatim is the most common way this section goes stale, and the room notices.

If no prior file exists, this is the first one. Carry on.

### Step 2: Query the roadmap, once per team

Pull every candidate in a single query per team. Run teams in parallel.

```sql
SELECT "Name", url, "Stage", "Status", "Update", "Goal", "Track", "KR",
       "Reporting link", "Amplitude link", "Description",
       "date:Shipped date:start",
       "date:Target Launch Date:start",
       "date:Last status update:start",
       "date:Last Updated:start"
FROM "{{notion_roadmap_data_source}}"
WHERE (Area LIKE '%Product - Conversion%' OR "Delivery team" = 'Conversion')
  AND (
        "date:Shipped date:start" >= date('now', '-14 days')
     OR "Stage" IN ('Test running', 'Blocked', 'QA', 'Building', 'Complete: Rollback')
     OR ("date:Target Launch Date:start" >= date('now')
         AND "date:Target Launch Date:start" <= date('now', '+21 days'))
     OR "date:Last status update:start" >= date('now', '-10 days')
  )
```

Swap the first `WHERE` clause per the mapping table. The window is deliberately wider than the week so you can see what's genuinely fresh versus what's been sitting. Narrow it during selection, not in SQL.

Field notes that are easy to get wrong:

- **`Stage`** is workflow position: `Needs review / Not started / Deprioritized / Up next / Planning` (to-do), `Designing / Ready to build / Building / QA / Blocked` (in progress), `Test running / Complete: Rollback / Launched` (done).
- **`Status`** is health (`On track / At risk / Off track`) and is independent of Stage. Don't conflate them. An item can be `Building` and `Off track` at once.
- Date properties expand as `date:<Property Name>:start`, not the bare name.
- `Goal`, `Track`, `Area`, `Quarter` come back as JSON arrays. Render as plain comma-separated text if you use them at all.
- `Update` is the PM's own latest note and is your best raw material. `Description` is the standing one-liner and is a fallback, not a substitute.
- **`url` comes back broken for pasting.** See the URL rule in Step 7.

If a must-include item doesn't show up in the query results, fetch it directly by name or URL rather than dropping it.

### Step 3: Classify each candidate

Every bullet carries one of these labels, with the emoji, exactly as the doc uses them:

| Label | Use when |
|---|---|
| 🏁 **Concluded:** | Test finished and there's a verdict: win, loss, or flat. `Complete: Rollback`, or `Launched`/`Test running` with a readout in `Update`. |
| 🚀 **Launched/Kicked:** | Went live in the last 7-10 days. `Shipped date` inside the window, or `Launched` with a recent update. |
| 🔬 **Live:** | Running right now with an early read or a mechanic worth watching. Usually `Test running`. |
| 🔁 **Coming Up:** | Not live yet, launching soon. `Target Launch Date` ahead, Stage in `Designing / Ready to build / Building / QA`. |
| 🚩 **Blockers / Flags:** | Stuck or slipping in a way another team can unblock. `Stage = Blocked`, or `Status = Off track`, or a slip against last week's draft. |

Pick the label that describes the newest thing that happened. A test that launched three weeks ago and just read out is **Concluded**, not Launched. Use `Launched/Kicked` when the news is that it's live and there's no result yet.

### Step 4: Select the Top 3 (this is the whole job)

Rank candidates against four questions, in this order:

1. **Is it novel?** Did something change since last week that the room hasn't heard? A conclusion, a first read, a rollback, a surprise. Status that hasn't moved is not news.
1. **Is it high impact?** Does it move a headline metric at a size worth saying out loud?
1. **Will it teach the team something?** A clean read that changes what the group believes earns a slot even when the result is flat or negative. Flat results with a real learning are frequently the best hits in the doc, because they stop other teams from re-running the same idea.
1. **Does it need to be visible?** Cross-team dependency, a surface another team also touches, a decision the author needs in the room, something a must-include implies.

Then apply the cuts:

- Must-includes take their slots first.
- **Max 3. Fewer is correct when only one or two clear the bar.** Two strong hits and no filler beats three where one is padding. If you're reaching for a third, don't.
- No BAU, no project status, no homework. If a bullet reads "still building, on track," it's a Notable Mention at most.
- One bullet per initiative. Don't split a single item into two hits.
- Rank the strongest hit first. The room's attention drops with each bullet.

### Step 5: Notable Mentions (max 5)

Everything else worth showing but not discussing. Mix across upcoming, completed, and newly launched so the block reads as a real picture of the team's week. Blockers belong here too if they didn't earn a Top 3 slot.

Order them so the reader scanning for five seconds gets the most useful ones first: fresh launches and conclusions, then blockers or slips, then upcoming. Five is a ceiling, not a target.

### Step 6: The Top Takeaway (one sentence)

One sentence naming the biggest learning or the biggest win from **the items you just highlighted**. It has to follow from a bullet above it. A takeaway about something not in the section reads as a non-sequitur.

Prefer the learning over the win when both exist, because the learning is what other teams can use. "Non-admin request flow is ripe for follow-up iteration: pitch us your best ideas" works because it hands the room something to do. "We had a strong week" says nothing.

### Step 7: Format the draft

Multiple teams get their own `##` heading, each with the full three-block set, in the order the user named them.

```markdown
## {Team Name}

**Top 3 Hits**

1. {emoji} **{Label}:** [{Item name}]({url}) — {one sentence: what it does or tests, plus the
   freshest result or the reason it matters}. {Date or day count if it sharpens the point.}

**Notable Mentions**

- {emoji} **{Label}:** [{Item name}]({url}) — {one short sentence}.

**💡Top Takeaway**

- {One sentence.}
```

Formatting rules:

- **The item name is the link.** Prefer the Notion page URL, then `Reporting link`, then `Amplitude link`. If there's nothing at all, flag it rather than shipping a bare name. A named initiative with no link reads to the room as work nobody can check.

- **Rebuild every Notion URL. Never paste the raw `url` value.** The query returns `{{notion_app_base_url}}/<32-hex-id>` with no `/p/` segment, and that form 404s in a browser. The working form is:

  ```text
  {{notion_app_base_url}}/p/{Title-In-Kebab-Case}-{32-hex-id}
  ```

  Take the id off the end of the raw `url`, kebab-case the item's `Name` (drop emoji, slashes, parentheses, quotes, and the `%` and `+` signs, collapse whitespace and other punctuation to single hyphens), and join them with a hyphen. So `Streamline End of Trial Modal` at id `32fab2b3b49681f588eccbf5855d5baf` becomes `{{notion_app_base_url}}/p/Streamline-End-of-Trial-Modal-32fab2b3b49681f588eccbf5855d5baf`. Notion resolves on the trailing id, so an imperfect slug still lands on the right page, but a missing `/p/` does not. If an item has no `Name`, use `{{notion_app_base_url}}/p/{id}`.

  This has burned a real run before: every Notion link in the delivered section was dead. Check it before handing the draft over.

- At most one sub-bullet per item, and only when the "why" genuinely doesn't fit in the line. The doc's best sections are one line per item.

- One or two numbers per bullet. Include the significance figure when you cite a lift, since the room asks for it every time.

- Dates as `Jul 29` or `Aug 12`. Day counts (`21 days in`) when runtime is the point.

- Never invent a number, a date, or a result. If `Update` doesn't have it, the bullet says what's known and stops.

### Step 8: Adversarial review (required, before anyone sees the draft)

Attack the draft against `references/adversarial-review.md` with fresh eyes. Spawn a subagent so the critique is actually independent, and pass it the checklist, the full draft, and the candidate list you selected from. It returns a pass/fail per criterion plus surgical fixes. Apply them.

The reviewer's most valuable job is the selection check: it sees the candidates you rejected, so it can tell you when the third hit is padding or when something in Notable Mentions is plainly bigger than something in the Top 3. That judgment is very hard to make on your own draft, and it's the difference between a section that earns its three minutes and one that burns them.

If no subagent tool exists in your environment, run the checklist yourself as a separate, deliberate pass. Don't skip it.

### Step 9: Present and save

Show the full draft in chat along with:

- Any item you had to leave unlinked.
- Any must-include you placed in Notable Mentions instead of Top 3, with the reason.
- Items whose `Last status update` is NULL or older than 7 days, as a short list. Stale roadmap updates are the reason good work goes unreported, and they're fixable in a minute.
- What resolved from last week's Coming Up, and anything that silently slipped.

After approval, save to `{{macro_funnel_output_dir}}/{YYYY-MM-DD}-macro-funnel.md` with frontmatter:

```yaml
---
date: {Monday the update covers}
type: macro-funnel-update
teams: [{teams}]
quarter: {e.g. FY27Q3}
---
```

Report the path. The deliverable gets pasted into a Google Doc, so keep it to plain markdown headings, bold, bullets, and links.

## Voice rules

Follow `references/voice-style-guide.md`. The rules that bite hardest in a section this compressed:

- **No em dashes.** Commas, periods, colons, or parentheses.
- Contractions always. Short sentences. One idea per bullet.
- Lead with the verdict, then the number. "Concluded as a win after 21 days: +18.4% new customers" beats "After running for three weeks, the experiment showed positive results."
- Never the "This isn't X, it's Y" construction, in any variant.
- Cut banned phrases (leverage, robust, in order to, it's worth noting, straightforward).
- No hedging stacks ("early signals suggest we may be seeing"). Say what you know, then say what's uncertain, plainly.

## Bundled references

- `references/adversarial-review.md` — the Step 8 checklist.
- `references/format-example.md` — the doc's own template instructions plus a worked section. Read it before your first draft.
- `references/voice-style-guide.md` — the voice rules. Swap in your team's guide if you have one.

## Your task

Run the workflow. Resolve the teams, load last week's draft, query the roadmap, classify and rank the candidates, then draft at most 3 hits, at most 5 notable mentions, and one takeaway per team. Run the adversarial pass before showing the draft. The section's value is the selection, not the coverage.
