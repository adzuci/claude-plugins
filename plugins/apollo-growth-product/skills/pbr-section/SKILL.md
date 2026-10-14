---
name: pbr-section
description: Draft a section for the weekly Growth Product Business Review from raw metrics, KR status, and experiment updates.
disable-model-invocation: true
requires_config: true
---

# GPBR Section Writer

Draft a section for the weekly Growth Product Business Review. Takes raw context (dictated notes, metric updates, experiment results) and produces a polished narrative section that matches the GPBR formatting standard.

Usage: `/apollo-growth-product:pbr-section [section name] [metrics, KR status, experiment updates]`

**Who reads this:** growth leadership and cross-functional stakeholders. They're scanning for exceptions (what's off track and why), status changes (what moved this week), and forward momentum (what's shipping next). They won't read every word. Front-load the signal, bury nothing, and keep the whole section readable in under two minutes.

## Configuration

Before doing anything else, read `config.md` from this skill's directory. It contains a YAML frontmatter block of variables this skill depends on.

For every `{{placeholder}}` you encounter while running this skill, substitute the matching value from `config.md`'s frontmatter.

`config.md` ships with the skill, so treat it as **defaults and documentation, read-only**. A plugin update replaces it.

Your own answers live in `~/.claude/plugin-config/apollo-growth-product/pbr-section.md`. Read that file first when it exists and let it override the shipped values, remembering that a saved empty string is a deliberate answer, not a missing one.

If a value is still `<UNSET>` after that merge, ask the user for it, then write the answer to `~/.claude/plugin-config/apollo-growth-product/pbr-section.md` (creating the directory if needed). Never write answers back into the skill's own `config.md`; they'd be wiped on the next plugin update. Do this once per session.

**Output directory:** `{{pbr_output_dir}}`

## Workflow

### Step 1: Parse arguments

Check the arguments for the section name, the DRI, KR names and targets and status, metric updates, experiment updates, and what's next. If anything critical is missing, go to Step 2.

### Step 2: Gather missing context

> "I'll draft your GPBR section. Give me:
>
> - **Section name**: which section? (e.g. Growth Expansion, Onboarding & Activation)
> - **DRI**: your name
> - **Guiding question**: the one-line question under your section header
> - **Headline metric**: what's the primary metric? Current value, target, trend direction. Describe the chart you'll paste in.
> - **What changed**: experiments that launched, concluded, or moved metrics. Include links where possible.
> - **KRs**: for each, the name and target, the status (On Track / At Risk / Off Track), and if At Risk or Off Track, what's wrong, why, and what you're doing about it
> - **What's next**: upcoming experiments or launches grouped by theme, with target dates
> - **Strategy**: only if it changed since last week. Otherwise I'll carry it forward.
>
> You can dictate stream-of-consciousness. I'll structure it into the narrative."

**Auto-check for prior context.** Glob and read:

- `{{pbr_output_dir}}` — previous updates matching this section's slug, for tone and continuity
- `{{debrief_dirs}}` — team debrief reports. When a debrief is saved as both `.html` and `.md`, read the `.md`. These are a primary input for the current week's numbers, KR status, and "why it moved" explanations. Pick the debrief whose date is closest to, and not after, the PBR date.

Report relevant prior updates and debriefs so the narrative maintains continuity. When a debrief is available, prefer its numbers over recollection, but confirm with the user if there's a conflict. Treat debriefs flagged provisional with appropriate hedging. They're directional signal, not certified fact.

### Step 3: Draft the section

Produce the update following the **Formatting Standard** and **Template** below. On your first draft for a section, read `references/worked-example.md` too: it shows the structure applied end to end. Then run Step 4 before showing the draft to anyone.

### Step 4: Adversarial validation pass (required)

Before you present the draft, attack it with fresh, skeptical eyes against the checklist in `references/adversarial-review.md`. Prefer to spawn a separate subagent so the critique is genuinely independent, and pass it the checklist plus the full draft. It returns a pass/fail per criterion plus specific, surgical fixes. Apply the fixes, then re-run only if it flagged something structural.

If no subagent tool is available, don't skip this step. Run the checklist yourself as a deliberate, separate pass: read the draft cold against each criterion, write the verdict in the checklist's output format, then fix.

The reviewer enforces what this section can't afford to get wrong: tight and concise copy, consistency across blocks (names, numbers, KR status all agree), no missing links or broken formatting, and no outdated or irrelevant information slipping through. This second set of eyes exists because the author always reads past their own fog. The reader won't.

### Step 5: Review the draft

> "Here's the draft GPBR section for {Section Name}. Review the narrative before I save it. Let me know if anything needs adjusting: tone, emphasis, missing context."

Make any requested changes.

### Step 6: Save

After approval, save to `{{pbr_output_dir}}/pbr-{section-slug}-{YYYY-MM-DD}.md` using lowercase hyphenated slugs (`onboarding-activation`, `growth-conversion`, `pricing-packaging`, `growth-expansion`). Confirm the path.

## Formatting standard

These rules enforce consistency across all GPBR sections. They're distilled from the strongest sections and correct the drift patterns that creep in over time.

### Voice (read this first)

Every GPBR section follows `references/voice-style-guide.md`. Read it before drafting. The rules below are the ones this skill gets wrong most often, so treat them as the pre-flight check.

- **No corrective negation. This is the single most common failure.** Any sentence that negates one framing and then asserts the corrected one gets rewritten as the positive claim alone. Kill "the loss comes from qualification rate, not deal size," "a propensity decline, not a cohort-size artifact," "broad rather than specific to one surface." Say what's true and stop: "Qualification rate is doing all the damage." The same ban covers contrasting pairs, antithesis, and every variant of "This isn't X. This is Y."
- **Answer up front.** Conclusion at the front of the sentence, evidence behind it. "Teams that sign up are buying less often. Conversions fell 14.1% while the cohort only shrank 8.2%" beats burying the finding in a trailing "which suggests..." clause.
- **No jargon. Say it simply.** "Cohort-size artifact," "propensity," "composition effect," and "within-segment dynamics" all have plain-English versions. Use them: "the buying rate itself dropped," "the funnel is handing us smaller teams."
- **Contractions always.** Don't, can't, won't, it's, we're.
- **Max 3 sentences per paragraph.** Hard cap, and it applies to the paragraph under a bolded lead too. Vary sentence length inside the cap.
- **No em dashes, ever.**
- Also banned and worth watching here: rule of three, parallel sentence structures inside one paragraph, stacked noun phrases, nominalization, hedging qualifiers, filler intensifiers, corporate-register verbs, throat-clearing openers, landing sentences, summary beats.

### General principles

- **Narrative, not mechanical.** Tell a story, don't recite a dashboard. The reader should understand what happened and why without cross-referencing a spreadsheet.
- **Specifics for facts, hedges for causes.** Use specifics for measured outcomes (numbers, p-values, deltas, dates): "FTP rate dropped 0.3pp to 4.2%" not "conversion dipped slightly." Hedge causal claims with "likely," "possibly," "aligns with." When root cause isn't known, say so plainly ("we haven't nailed down a root cause yet") rather than passive "investigating."
- **Direction in the verb.** Lead with the movement, not the static value. Use directional verbs that carry trend: hit, slipped, popped, compressed, fell, climbed, held, rebounded, settled. "W2 FTP hit 1.56% but slipped the following week" beats "W2 FTP at 1.56%, then 1.43% the following week."
- **One editorial reaction per section, max.** When the data warrants it, a brief reaction is welcome ("Seriously strong!", "A clean miss"). Once per section signals confidence. More than once feels like cheerleading.
- **Honest.** If something is off track, say so directly with Problem/Diagnosis/Plan. Burying bad news wastes the meeting on discovery instead of decisions.
- **Scannable.** Executives skim. Front-load the key message. One paragraph per idea.
- **No fabrication.** Only use numbers the user provides. If data is missing, say so.
- **Cohort phrasing.** Use "for the {date} cohort" (e.g. "for the 4/06 cohort") as the canonical framing for cohort-week metrics.
- **Label the population when sources disagree.** The same gate or segment can carry different numbers in the KR dashboard and a weekly report (different denominators, different filters). When you cite both in one section, name the source inline so nobody cross-references and finds a contradiction.
- **Link everything, then check the links.** Every Notion item, experiment, and roadmap row you name gets an inline link. Before saving, verify each URL resolves (`curl -s -o /dev/null -w "%{http_code}" -L <url>`, or fetch the page). A dead link in a leadership doc is worse than no link.
- Always show the draft before saving.

### Strategy

- 1-2 sentence narrative opener that frames the quarter's focus.
- Numbered strategic pillars: `**1. Verb Phrase.** Explanation sentence.`
- Each pillar is self-contained in 1-2 sentences. Don't nest sub-bullets under pillars, fold the detail into the sentence. Sub-bullets break the scannable rhythm and make the strategy feel like a task list.
- Optional: one quantified impact line (e.g. "Each +1pp in Habit RA = $305K incremental ARR").
- This section rarely changes week to week. Carry it forward unless the user signals a change.

### The Story

- **One paragraph, or two when there's a watch item.** First paragraph is the macro frame (2-3 sentences). If there's a clear watch item or risk, promote it to its own short second paragraph (1-2 sentences). Length caps are per paragraph.
- **Lead with the dominant pattern, not a KR roll-call.** What's the through-line across KRs this week? ("All three KRs reading below target on the latest cohort, dominated by mix-shift" or "Q1 closed above target on 2/3 KRs"). Don't recite KR-by-KR status, that's what Supporting KRs at a Glance is for.
- **Counterbalance with one underlying signal.** When the blended numbers look bad, name the underlying truth that complicates the picture: "Non-freemail FTP is essentially flat at 5.74%." One short clause is enough. This is what makes the Story honest instead of doom-y.
- **Be precise about hit counts.** "Closed above target on 2/3 KRs" not "closed on track across all three KRs" if all three didn't actually clear.
- **Use specific status language.** "Closed above target," "rebounded into Q2," "held above target through March." Avoid generic "on track" framing when you can name the movement.
- **No experiment-level details.** Don't name shipped experiments, dates, or numeric results here. The Story is for KR-level framing and cross-cutting watch items only.
- **Stay high-level. Defer the specific metrics.** A single framing figure is fine when it *is* the story. A stack of cohort reads, segment rates, and deltas means you're writing What Changed twice.
- **Watch-item lead pattern.** Use a clean setup like "One watch item heading into Q\[X\]:" then state what's slipping and what you're doing about it in one sentence. Don't bury it inside the status paragraph.
- **No sub-headings, H4s, or bullets.** Narrative form only.
- **Optional context bridge.** First clause can bridge from an adjacent area ("With activation still recovering..."). One clause, not a paragraph.

### Headline Metric

- Chart placeholder: `[Chart: {chart description}]`
- **One chart is usually enough.** Default to a single chart for the primary KR. Add a second only when it shows a non-obvious driver the narrative leans on. Three or more chart placeholders signal a dashboard, not a story.
- No commentary here. Commentary belongs in What Changed and Why.
- If there's a supporting data table, put it here under the chart reference. This keeps the quantitative snapshot in one place.

### What Changed and Why

Organize either by **KR** (each KR gets its own paragraph, the default) or by **driver/theme** (a few cross-cutting drivers explain the metric movement). KR-organized works when each KR has a distinct story. Driver-organized works when one or two themes cut across the metric.

**One paragraph per KR (or driver), not two.** Be ruthless about cutting. The lead sentence does most of the work. The supporting paragraph adds 2-4 sentences of input, cause, and hedged interpretation. If you're writing a second paragraph, you're padding.

**Bold the entire lead sentence.** Open each paragraph with a bolded lead that embeds the metric, the movement, the cohort, and the cause in one go:

> **{Metric} {directional verb} {value} for the {cohort/week}, {but/and} {what happened next} {due to/driven by} {cause}.**

Examples:

- **"W2 FTP hit 1.56% for the 4/06 cohort, but slipped the following week due to freemail growth + softening SMB conversion."**
- **"Trial W2 CVR fell slightly to 4.04% for the 4/13 cohort."**
- **"W2 FTP slipped to 1.22% for the 4/27 cohort, the third consecutive read below target, driven by VSB-Freemail dilution."**

The bolded lead is the scaffold the reader scans. The unbolded supporting paragraph is the prose for anyone going deeper.

**Name the metric, never the KR number.** Open each block with the metric's real name: "Non-freemail W2 free-to-paid fell to 4.64% for the July 19 cohort." Never "KR1 fell to 4.64%." Inside the supporting paragraph, say "the metric" instead of "this KR." KR numbers belong in Supporting KRs at a Glance, where readers cross-reference them against the OKR tracker.

**Don't repeat target language per KR.** State the target once in Supporting KRs at a Glance. In What Changed, "above target" or "second above-target read" is enough context.

**Don't restate plans here.** What Changed is backward-looking: what moved, why. Forward-looking plans belong in Supporting KRs (Plan) or What's Next. Mentioning a live experiment by name is fine when it directly explains the current read. Listing what's next for it is not.

**Recent ships and rollbacks.** Only include them here if they materially moved the metric in the current read. Cross-KR ships that haven't shown up in the numbers yet belong in What's Next.

Other rules:

- Narrative paragraphs, not bullet lists. Bullets are OK only for 3+ data points under a single driver.
- Only include experiments that meaningfully moved a metric. Drop inconclusive results.
- Don't use H6 or other sub-headers for grouping experiment details. Bold lead sentences do the same job without fragmenting the narrative into a changelog.
- When citing statistical results, fold them into the narrative paragraph rather than scattering them as bullet items. A stat without its story is noise.

### Supporting KRs at a Glance

- Format: `**KR{n}: {KR Name} (target {target})** – **{Status}** – {One sentence}`
- **Use `KR{n}:` prefixes** when the section owns numbered KRs. Readers cross-reference KR numbers across PBR sections, planning docs, and OKR trackers.
- For KR names, include the verb framing when it matches how the KR is tracked (e.g. "Maintain >= 3.5% W2 trial conversion rate"). Match the language the org uses, don't paraphrase.
- Status values: **On Track** / **At Risk** / **Off Track** (always bold the status).
- **On Track**: one sentence. Lead with the latest read plus a directional cue.
- **At Risk or Off Track**: use the **Problem / Diagnosis / Plan** mini-arc. This is the standard structure across all sections. Don't substitute "Mitigation" or other labels. The consistency lets readers pattern-match across sections instantly.
  - `* **Problem:** {what's wrong, stated plainly with specific numbers}`
  - `* **Diagnosis:** {why it's happening}`
  - `* **Plan:** {concrete next actions with links and dates}`
- Keep each line to 1-2 sentences. The Plan is where forward-looking experiment plans live, not What Changed.
- No embedded charts or images inside KR entries. Inline images break the scannable KR list.

### What's Next

- Group by theme with a bold header: `**{Theme}:** description`
- Themes are roadmap-tied buckets (Trial experience, Feature gates, Monthly-to-annual, Add-ons, Dead-end moments). Match how the team's actual workstreams are grouped, not generic categories.
- Use natural prose with linked experiment names and target dates woven in. Readability matters more than consistency of punctuation.
- Only mention items actually upcoming (this week or next 1-2 weeks).
- Don't repeat experiment details already covered in What Changed and Why. Name the experiment and state what's next for it.
- **Skip generic "investigation" buckets** unless the next step is concrete and actionable. "We're looking into X" without a date or owner is filler. Fold it into the relevant KR's Plan line instead.

## Template

```markdown
# **{Section Name}**

## *{Guiding question}*

**DRI:** {Name}

### {Quarter} Strategy

{1-2 sentence narrative opener framing the quarter's focus.}

**1. {Verb Phrase}.** {Explanation in 1-2 sentences.}

**2. {Verb Phrase}.** {Explanation in 1-2 sentences.}

{Optional: one quantified impact line.}

### The Story

{2-3 sentences naming the dominant macro pattern across KRs (not KR-by-KR). Counterbalance with one
short clause on the underlying signal. Use specific directional language. No experiment-level
details.}

{Optional second paragraph for a watch item.}

### Headline Metric

[Chart: {chart description}]

### What Changed and Why

**Pattern A — KR-organized (default).** Bold the entire lead sentence per KR, one supporting
paragraph (2-4 sentences) follows.

> **{Metric name} {directional verb} {value} for the {cohort/week}, {but/and} {what happened next}
> {due to/driven by} {cause}.** {Supporting paragraph with the inputs that moved the number. Hedged
> causal explanation. No forward-looking experiment plans.}

**Pattern B — Driver-organized.** Use when one or two themes cut across the metric. Open with the
headline metric commentary, then bolded driver lead sentences.

> {Headline metric commentary: current value, trend direction, supporting funnel signals.}
>
> **{Driver 1 name}.** {Narrative explanation of what happened and why.}

### Supporting KRs at a Glance

**KR1: {KR Name} (target {target})** – **{On Track}** – {One sentence on status and trend.}

**KR2: {KR Name} (target {target})** – **{At Risk}** – {One sentence framing the slip.}

* **Problem:** {What's wrong, stated plainly with specific numbers.}
* **Diagnosis:** {Why it's happening.}
* **Plan:** {What you're doing about it, concrete next actions with links and dates.}

### What's Next

**{Theme 1}:** {Upcoming experiments and launches with linked names and target dates.}

**{Theme 2}:** {Same pattern.}
```

## Bundled references

- `references/adversarial-review.md` — the checklist for the Step 4 validation subagent.
- `references/expansion-example.md`, `references/onboarding-example.md`, `references/pricing-example.md` — worked sections for other GPBR areas, for cross-section tone calibration.
- `references/voice-style-guide.md` — the voice rules. Swap in your team's guide if you have one.
- `references/worked-example.md` — a full approved section showing the all-At-Risk pattern with Problem/Diagnosis/Plan arcs on every KR. Read it before your first draft.
