---
name: quarterly-experiment-summary
description: Bring the cross-team quarterly experiment learnings doc current with newly concluded experiments, refreshed TL;DR patterns, and a follow-up list.
disable-model-invocation: true
requires_config: true
---

# Quarterly Experiment Summary

Bring the canonical experiment learnings doc current. This doc is the org's memory of what has and hasn't worked on a team's surfaces. Other teams read it to borrow patterns and avoid dead ends, and execs read it to see whether the team is learning or just shipping.

Usage: `/apollo-growth-product:quarterly-experiment-summary [team code]`

**Who reads this:** executives and product team leads. They're scanning, not studying. Most read the TL;DR and one or two quarter sections. Nobody reads all 60 entries in one sitting.

**What that means for the writing:** every entry has to survive a 10-second read. One sentence on what changed, the two or three numbers that matter, and a learning another team could act on. Anything that doesn't clear that bar is noise in a reference doc, and noise is what makes people stop opening it.

## Configuration

Before doing anything else, read `config.md` from this skill's directory. It contains a YAML frontmatter block of variables this skill depends on.

For every `{{placeholder}}` you encounter while running this skill, substitute the matching value from `config.md`'s frontmatter.

`config.md` ships with the skill, so treat it as **defaults and documentation, read-only**. A plugin update replaces it.

Your own answers live in `~/.claude/plugin-config/apollo-growth-product/quarterly-experiment-summary.md`. Read that file first when it exists and let it override the shipped values, remembering that a saved empty string is a deliberate answer, not a missing one.

If a value is still `<UNSET>` after that merge, ask the user for it, then write the answer to `~/.claude/plugin-config/apollo-growth-product/quarterly-experiment-summary.md` (creating the directory if needed). Never write answers back into the skill's own `config.md`; they'd be wiped on the next plugin update. Do this once per session.

**Output directory:** `{{summary_output_dir}}`

## Team to doc registry

The Team column on each experiment decides which doc it belongs in. One doc per team. The registry lives in `{{team_doc_registry}}`.

Source DB: data source `{{notion_experiments_data_source}}`.

Experiment IDs in the doc are written `{{experiment_id_prefix}}-<ExpID>` from the DB's `ExpID` column.

## Workflow

### Step 1: Confirm the team

Check the arguments for a team code or team name. If absent, ask which team's learnings doc, listing the codes from the registry.

Don't guess from context. The Team column is the filter for the whole run, and getting it wrong means writing another team's experiments into the wrong doc.

If the team has no doc yet, say so and offer to create one at the same structure in `{{notion_docs_data_source}}`. Get an explicit yes before creating a page.

### Step 2: Read the existing doc

Fetch the doc. Pull out and hold onto:

- **Every `{{experiment_id_prefix}}-<n>` already covered.** This is your dedupe key. Grep the fetched text for the ID pattern.
- **Quarter headings present**, and their exact date ranges.
- **The TL;DR list**: how many entries, what each claims, what evidence each cites.
- **Current title, `Description` property, and the Scope line** in the header block.
- **The cross-cutting themes section** and which experiment IDs each bullet cites.

### Step 3: Query the DB for what's missing

```sql
SELECT "ExpID", "Short Name", "Status", "[Post] Confidence / StatSig" AS conf,
       "[Post] Est. Annual Impact -- Rollout Only" AS impact, "Metric",
       "date:Experiment Run Dates:start" AS run_start,
       "date:Experiment Run Dates:end" AS run_end,
       "date:Shipped Date:start" AS shipped,
       "Summary: Results + Key Learnings" AS results_summary, url
FROM "{{notion_experiments_data_source}}"
WHERE "Team" = '<TEAM>' AND "ExpID" > <highest ExpID already in the doc - 60>
ORDER BY "ExpID" DESC
```

**Do not filter on dates in SQL.** `Experiment Run Dates` and `Shipped Date` are null on a large share of rows, so any date predicate silently drops real experiments, and any `IS NULL` escape hatch drags in years of ancient ones. `ExpID` is auto-increment, so it's the only reliable recency proxy. The "past ~90 days" framing is a sanity check on the result set, not a query filter. What decides inclusion is whether the ID is already in the doc.

Then partition the results three ways:

**Write up** — `Done : 🚢` or `Done : Rollback`, and the ID is not already in the doc.

**Flag for follow-up** — don't write entries, but name them so they can be chased:

- `In Post-Mortem` → the writeup isn't finished. These need someone to close them out.
- `Live` → still running. Come back after it concludes.

**Drop silently** — `Idea`, `Backlog`, `Backlog : Next`, `In Design`, `Ready for Dev`, `In Development`, `Ready to Test`, `Cancelled`.

If nothing lands in the write-up bucket, say so plainly and stop. Report the follow-up list, because that's the actionable finding: the doc is current and N experiments are waiting on post-mortems.

### Step 4: Read each new experiment's page

Fetch each one. The `Summary: Results + Key Learnings` property is a starting point, but the real material is in the **Analysis and Results** and **Post-Mortem Summary** sections. That's where the mechanism lives, and the mechanism is the only part another team can use.

For experiments whose page has an empty or stub results section, don't invent a finding. Use the thin-evidence entry format (see `references/entry-format.md`) and let the gap show.

Run these fetches in parallel when there are more than three.

### Step 5: Assign each experiment to a quarter

Quarter boundaries come from `{{fiscal_quarter_definition}}`.

Assign on **`Experiment Run Dates` start**, not end. A test that ran 4/15 → 5/13 belongs to the quarter containing 4/15. A test belongs to the quarter it was a bet in.

Fallback chain when run start is null: `Shipped Date` → run end → ask the user. Never guess a quarter from the ExpID.

If a quarter heading doesn't exist yet, create it in the doc's format, newest quarter first, directly under the TL;DR:

```text
## FY27Q2 (May 1 – Jul 31, 2026) {toggle="true"}
```

### Step 6: Draft the entries

Read `references/entry-format.md` and follow it exactly. It has the heading convention, the three-bullet body, the confidence label definitions, and four worked examples covering a shipped win, a clean null, thin evidence, and an invalidated result.

The bar for the **Learning** bullet is the whole point of the doc, so hold it: name the *mechanism*, not the outcome. "Treatment didn't win" tells another team nothing. "Behavioral triggers only work when there's real friction" tells them when to reuse the pattern and when not to. Where a result contrasts with a sibling test, point at it by ID. The pairs are what make this doc more useful than reading the tracker.

### Step 7: Re-evaluate the TL;DR learnings

Read `references/tldr-curation.md`. In short:

- A new experiment does **not** earn a TL;DR slot on its own. Slots go to patterns that held across two or more independent tests, or to a single high-impact, high-confidence result that changes how the team operates.
- Prefer **strengthening an existing entry** with new evidence over adding a near-duplicate. Most new results are the fourth data point on a pattern already listed.
- If a new result **contradicts** an existing learning, say so out loud in the review. Split it, narrow its scope, or downgrade its confidence. Quietly leaving both is how a reference doc goes stale without anyone noticing.
- Over 20 entries, stop and present pruning options rather than trimming on your own judgment.

### Step 8: Update the doc's framing

Four things go stale every time a quarter is added:

1. **Title** — "(Through Q1 FY27)" → "(Through Q2 FY27)".
1. **`Description` property** — the experiment count and quarter range.
1. **Scope line** in the header block — count and range. Check whether it still describes what's actually included.
1. **Cross-cutting themes** — add new experiment IDs to the bullets they support. If a new result undercuts a theme bullet, revise the bullet.

### Step 9: Write the local draft and review

Write to `{{summary_output_dir}}/<team>-<quarter>-summary-draft.md`, containing only what's changing:

- the new (or amended) quarter section, full entries
- the revised TL;DR list, marking each entry `[new]`, `[updated]`, `[unchanged]`
- the revised Scope line, title, and Description
- amended cross-cutting theme bullets
- the follow-up list

Then present in chat: a one-line count of what's being added, the full new quarter section, the TL;DR diff, and the follow-up list. Ask:

> "Here's the draft. Check the learnings and confidence labels before I push to Notion. Those are the parts other teams will act on."

Make requested changes in the local file first, then push.

### Step 10: Push to Notion

After explicit approval:

1. **Insert the new quarter section as one whole block.** Don't patch line by line. Notion content edits apply partially and silently on long pages, so a single insert is far safer than a sequence of small edits.
1. **Rewrite the TL;DR list as a whole block** rather than editing individual numbered items. Renumbering across a partial apply is how you end up with two item 4s.
1. Update the title and `Description` property.
1. Update the Scope line and any amended theme bullets.
1. **Re-fetch the page and verify** the new quarter, the TL;DR count, and the title all landed. Report what you confirmed. If anything is missing, fix it and re-verify rather than reporting success.
1. Append the follow-up list to the chat response, not the doc, unless the user asked for it in the doc.

## Style rules

The audience is other product teams, so shared acronyms are fine. Platform-specific metric names, flag names, cohort definitions, and experiment-config detail are not. They mean nothing outside the team that ran the test.

**Metrics, sparingly.** Two or three numbers per entry, max. Every percentage needs its p-value or significance level attached, otherwise a reader can't tell a real result from noise, and this doc's whole job is helping them tell the difference. When you cite a change between two absolute numbers, give the relative change too (`5.08% vs 5.19% control, -2.1% relative`).

**Follow `references/voice-style-guide.md`** in all prose: contractions, short sentences, no em dashes, no banned phrases. The one exception is structural: the `—` separator in `### [Name (ID)](url) — SHIPPED` headings stays, because the existing entries use it and consistency in a scannable reference beats the rule here.

**Be honest about weak evidence.** A large share of entries in a doc like this are underpowered or undocumented, and the doc is trustworthy precisely because it says so. "Shipped on leading indicators" and "Results section incomplete in tracker" are good sentences. Never dress up a null as directional, and never let a shipped status imply the revenue read was real when it wasn't.

## Bundled references

- `references/entry-format.md` — exact entry format, heading conventions, confidence label definitions, four worked examples. Read before drafting entries.
- `references/tldr-curation.md` — how TL;DR slots are earned, merged, and pruned, contradiction handling, cross-cutting themes maintenance. Read before Step 7.
- `references/voice-style-guide.md` — the voice rules. Swap in your team's guide if you have one.

## Related skills

1. `/apollo-growth-product:experiment-results` — close out a single experiment page
1. `/apollo-growth-product:quarterly-experiment-summary` (this skill) — roll concluded experiments into the multi-quarter learnings doc
