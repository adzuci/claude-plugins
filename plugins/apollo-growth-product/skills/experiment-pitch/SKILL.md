---
name: experiment-pitch
description: Pressure-test a rough experiment idea through divergence, an adversarial reframe, and a 7-mistake gauntlet, then push a sharpened pitch to the Notion roadmap.
disable-model-invocation: true
requires_config: true
---

# Experiment Pitch: Shape It Before You Build It

Take a rough experiment idea and make it the sharpest, most effective version of itself, then ship a simple pitch to the roadmap. The rigor happens in the *process* (divergence, an adversarial reframe, a 7-mistake gauntlet, and a forced choice between sharpened options). The *output* stays scannable. Everything considered but cut lives in an appendix, so the road-not-taken and the durable learning are captured without cluttering the headline.

This is the missing step between capturing an idea and designing the experiment. Capture is loose, design never challenges. This skill challenges.

Usage: `/apollo-growth-product:experiment-pitch <rough idea> [notion/analytics links] [--goal KR]`

**The belief underneath everything here:** a good experiment refines your intuition with customer data AND leaves the whole team smarter. Experimentation isn't free. Every test costs eng time, user exposure, and a roadmap slot, so the job is the *right* test, sharply framed, not another 1% tweak.

## Configuration

Before doing anything else, read `config.md` from this skill's directory. It contains a YAML frontmatter block of variables this skill depends on.

For every `{{placeholder}}` you encounter while running this skill, substitute the matching value from `config.md`'s frontmatter.

`config.md` ships with the skill, so treat it as **defaults and documentation, read-only**. A plugin update replaces it.

Your own answers live in `~/.claude/plugin-config/apollo-growth-product/experiment-pitch.md`. Read that file first when it exists and let it override the shipped values, remembering that a saved empty string is a deliberate answer, not a missing one.

If a value is still `<UNSET>` after that merge, ask the user for it, then write the answer to `~/.claude/plugin-config/apollo-growth-product/experiment-pitch.md` (creating the directory if needed). Never write answers back into the skill's own `config.md`; they'd be wiped on the next plugin update. Do this once per session.

**Notion destination:** `{{roadmap_database_name}}`, data source `{{notion_roadmap_data_source}}`

**Default properties:** `Name` (title), `Area`, `Delivery team`, `Quarter` (parse from args, quarter boundaries per `{{fiscal_quarter_definition}}`), `Goal` (pick best fit from {{roadmap_goal_options}}), `Track`, `KR`, `Type` = `Pitch`, `Stage` = `{{roadmap_new_pitch_stage}}`, `Description` (1-2 sentence summary). Leave `Effort`, `Eng effort (days)`, `Priority`, `DRI`, and `Product manager` blank for partner review.

**Route the team fields off the audience, not off a default.** When you own more than one team, the team is a decision, not a constant. Pick it from who the experiment is aimed at using `{{team_routing_rules}}`. When the audience straddles both, ask rather than defaulting.

The pitch body goes in page `content`, never in `Description`.

## Workflow

Run these steps in order. Steps 3 and 4 are the part nothing else does. Don't skip them to save time. They're the cheapest leverage in the whole process: 20 minutes of thinking here beats three weeks building the wrong test.

### Step 1: Parse arguments

Check the arguments for:

- **The rough idea** (e.g. "show a high-contrast upgrade CTA on the bulk-select gate")
- **Notion URLs** (existing idea, roadmap item, prior experiment to learn from)
- **Analytics links** (for the current baseline of the metric you want to move)
- **Local file paths** or references ("idea #5 from the brainstorm doc")
- **The goal / KR this ladders to**

If nothing was given, go to Step 2.

### Step 2: Gather context (and find the baseline)

Ask for whatever's missing, but keep it light:

> "What experiment do you want to shape? Give me:
>
> - **The rough idea** (however half-formed)
> - **The metric you're trying to move** and roughly where it sits today (analytics link if you have one)
> - **The bigger goal / KR** this ladders to
> - **Any links**: prior experiments, an existing idea, research, Slack threads"

Then auto-scan for context so you come in informed:

- Search your knowledge repo for prior experiments, pitches, and learnings in this area. Past results are the best input to a sharper hypothesis.
- Glob and read `{{team_context_dirs}}` for planning docs and prior roadmap exports. Skip when empty.
- Fetch any Notion URLs. Pull metric baselines from any analytics links.

Summarize what you found in 3-4 lines so a misread gets corrected before you spend effort on it. **If a prior experiment already answered this question, say so now.** The best outcome of this step is sometimes "you don't need to run this."

### Step 3: Diverge before you commit

The first idea that sounds good is almost never the sharpest version. Before you evaluate anything, shake loose 2-3 genuinely different creative variants of the *solution*.

Work through `references/divergence-toolkit.md`: it has the evaluate-mode flips that stop you killing ideas too early, and the SCAMPER prompts that generate the variants.

Keep the 2-3 strongest variants. Each should be a real alternative, not a reword. You'll offer these as the "creative approach" choice in Step 6.

### Step 4: Adversarial pressure-test (spawn a sub-agent)

This is the step that finds the 10x version and kills weak hypotheses. Spawn an **independent adversarial reviewer** as a general-purpose sub-agent. Independence matters: it has no attachment to the original idea, so it'll challenge what you've already half-committed to.

Pass it the brief in `references/adversarial-brief.md` verbatim, along with the idea, the gathered context, the baseline, and the candidate variants from Step 3.

When it returns, read it critically. It can be wrong or over-reach. Then synthesize: fold its strongest alternate hypotheses and its 10x reframe into the option sets you'll present in Step 6. Don't silently discard a strong reframe because it's more work. Surface it as a real choice.

### Step 5: Run the 7-mistake gauntlet

Work through these checks. Resolve most yourself and surface only the ones with a genuine decision or a real gap. This is the quality bar.

1. **Local maximum.** Walk the metric tree: where does this change sit, and what parent metric does it roll into? If you can't name the company-level metric it ladders to, stop and zoom out. Trace the event sequence and the user's feeling at each step (Emotion, Logic, Motivation, Reward), treating motivation as a finite tank that friction drains. The downstream drain often shows up a step *after* the one you touched. **Name the trade-off / guardrail metric now.** A test with no named downside hasn't been thought through.
1. **Volume vs. the right test.** Name the desired future state this test steps toward, even if not fully validated. Map the follow-up sequence: if it wins the next test is X, if it loses you learn Y and try Z. A single test inside a planned sequence beats ten orphans. Gut-check return on time invested: rough dollar impact ÷ (prep + launch + analyze time).
1. **One question.** Can you say in one sentence what this test will teach you? If not, it's two tests. Scope to the single highest-signal change and push the rest into the follow-up sequence.
1. **Validatable result.** What would void this test? Flag sample-ratio-mismatch risk, the specific instrumentation it depends on, and whether you can detect the effect in a reasonable window (rough power check). A green metric on broken plumbing is the most expensive thing you can ship.
1. **Pre-committed finish line.** One primary metric, the secondaries, the guardrails, and the leading indicators, decided before launch. Plus the decision rule: ship if X, roll back if Y, iterate if Z. No moving goalposts after the numbers land.
1. **Durable, shareable learning.** Will the insight outlive this one test? Frame the hypothesis so the *learning* is reusable by another team. If the only takeaway would be "this specific button moved 0.3%", reframe toward the underlying principle.
1. **Sharp hypothesis, in plain words.** Pull it together into **one short sentence a new hire could read once and understand**: *If we [change], then [metric] will [direction], because [reason].* Hard rules:
   - **One sentence. No semicolons, no nested clauses.** If you need a second sentence, the hypothesis is doing too much work. Move the detail into Current vs. Proposed.
   - **No jargon.** Strip mechanism-speak, behavioral-science vocabulary, and internal shorthand. "Choosing takes fewer clicks and less thought" beats "the option set is hidden behind a discovery step that suppresses consideration."
   - **No hedging and no stacked qualifiers.** Say the bet.
   - **Audience only if it narrows the test.** If it's everyone on the surface, the surface line already says so.
   - The mechanism detail, the named prior experiments, and the design intent belong in section 3 and the appendix. The hypothesis is the one line someone repeats back to you in a meeting.

### Step 6: Force the decision

Present the sharpened options and make the user pick. Use a **single question call with up to 4 questions**, one per axis. For each axis, lead with your recommendation and one sentence of *why*. Be opinionated. You're being paid for judgment, not a menu. Include the adversarial sub-agent's sharper alternatives as real options.

The four axes:

1. **Audience** — which segment? (e.g. all free users vs. high-intent vs. dormant-but-reactivatable). The audience often *is* the experiment.
1. **Hypothesis** — which framing? Offer the original, the sharpened version, and the strongest adversarial alternate. This is where durable-learning framing wins or loses.
1. **Metrics** — which primary metric, and which guardrail must not degrade?
1. **Creative approach** — which of the SCAMPER variants (or the 10x reframe) do we actually build?

Escape hatch: if an axis has one obvious answer with no real tradeoff, don't waste a question. State what you're going with and why, and drop it from the call. Only ask about genuine decisions. If the 10x reframe is compelling, make "reframe vs. hold the original scope" its own explicit choice rather than burying it.

### Step 7: Assemble the pitch

Fill the **Template** below. The main body (sections 1-5) stays tight and scannable, so someone gets 80% in 45 seconds. Everything considered-but-cut goes in the appendix. Don't let the appendix bleed into the headline.

**Specific in intention, flexible in implementation.** Describe the proposed experience at the level of mechanism and design intent, not literal execution. State the principle the change is betting on ("give the upgrade action clear primary-action prominence at the decision moment") rather than the pixel ("orange #FF6B00"). Over-specifying implementation makes the pitch overreach into decisions a designer or engineer should own, and it narrows the test before they've weighed in. If the user came in with a specific implementation instinct, carry it as *one candidate execution* in the appendix, not as the pitch's hypothesis. The hypothesis rests on the mechanism, so the learning survives even if the execution changes.

### Step 8: Review

Show the full draft. Ask:

> "Here's the shaped pitch. Want to adjust the hypothesis, the chosen approach, the metrics, or the finish line before I push to the roadmap?"

Make changes. If the user swaps the chosen option, update the appendix so the rejected one moves into "considered" and the reasoning stays honest.

### Step 9: Push to roadmap and save a local copy

After approval:

1. Push to the roadmap DB with `notion-create-pages` (data source `{{notion_roadmap_data_source}}`), setting the properties above with `Stage` = `{{roadmap_new_pitch_stage}}`. **Before you write, state the team routing back in one line** ("paid-team audience, so Expansion team / Expansion KR3") so a wrong read gets caught before the page exists.
1. **Write the body in a second call, not the first.** `notion-create-pages` silently strips a leading H1 from `content`, treating it as the page title, which kills the `# Pitch` toggle and orphans everything nested under it. Verified recipe: create the page with properties and the body, then immediately call `notion-update-page` with `command: "replace_content"` and `new_str` set to the full nested body (starting at `# Pitch {toggle="true"}`). `replace_content` preserves the leading H1 and the tab nesting. `insert_content` does not solve this, because prepending a heading won't adopt existing sibling blocks as children.
1. **Verify with `notion-fetch` before you report done.** Check four things: `# Pitch` is present, both top-level headings carry `{toggle="true"}`, sections 1-5 are tab-indented under Pitch (not siblings of it), and no `---` divider survived. Notion drops and escapes things quietly, so never claim the formatting landed without re-fetching.
1. Save a local copy to `{{pitch_output_dir}}/experiment-{slug}-{YYYY-MM-DD}.md`.
1. Confirm both: paste the Notion URL and the local path.
1. Suggest the next step: "Run `/apollo-growth-product:experiment-writeup` on this page to append the detailed design (user journey, sample size, metric tables) when you're ready to build."

**Notion-flavored markdown gotchas that bite this skill:**

- Escape `~` as `\~`. A bare `~` can start a strikethrough, so approximations like `\~1,829` need it.
- Tab-indent every child of a toggle heading. Space indentation won't nest.
- `$` and `<` get auto-escaped in output. That's cosmetic and fine, don't chase it.
- Read `notion://docs/enhanced-markdown-spec` via `notion-fetch` if you're unsure of syntax rather than guessing.

## Template

Both top-level headings are **toggle headings**, so the page opens as two collapsed sections. In Notion-flavored markdown that's `{toggle="true"}` on the heading, and **every child block must be indented one level with a tab** or it won't sit inside the toggle. No `---` dividers anywhere.

<!-- markdownlint-disable MD010 -->

```markdown
# Pitch {toggle="true"}
	## 1. Goal
	[1-2 sentences: the measurable outcome, and the KR / future state it ladders to.]

	## 2. Hypothesis
	[One short plain-language sentence: If we [change], then [metric] will [direction], because
	[reason]. No jargon, no second sentence.]
	**Durable learning:** [what the team banks either way, the reusable insight, not the local result.]

	## 3. Current vs. Proposed
	**Current:** [1-2 sentences on today's experience.]
	**Proposed:** [2-3 sentences. Specific about who / what / where and the *design intent*, flexible
	about exact execution. Name the principle, not the pixel. Leave room for design and eng to pick
	the implementation.]
	Surfaces: [affected surfaces, e.g. "bulk-select feature gate (modal, web app, free users only)"]

	## 4. Metrics & finish line
	- **Primary:** [metric + current baseline]
	- **Guardrail(s):** [the trade-off metric(s) that must not degrade]
	- **Decision rule:** Ship if [X]. Roll back if [Y]. Iterate if [Z].

	## 5. Timing
	[Target window, t-shirt effort estimate (Small/Medium/Large, never sprint counts), key
	dependencies.]

## Appendix: what we considered {toggle="true"}
	**Sharper question / 10x reframe:** [the bigger version the adversarial pass surfaced. If we held
	the original scope, one line on why.]
	**Alternate hypotheses considered:** [the framings not chosen + why each lost.]
	**Audiences considered:** [segments weighed + why this one.]
	**Creative variants (SCAMPER):** [the other approaches generated + why the chosen one wins.]
	**Follow-up sequence:** If it wins → [next test]. If it loses → [what we learn] → [what we try].
	**Validity pre-checks:** [SRM watch, instrumentation it depends on, rough power/runtime read.]
	**Open questions:** [blockers or decisions still needed before build.]
```

<!-- markdownlint-enable MD010 -->

Keep the main body to roughly 25-40 lines. The appendix can run longer. It's the holding pen for rigor, not the headline.

For the **local markdown copy**, drop the `{toggle="true"}` attributes (Notion-only) and lead with `# Experiment Pitch: [Name]` instead of `# Pitch`, since a local file has no title property to carry the name. Everything else matches.

## Writing style

Follow `references/voice-style-guide.md`: contractions always, short sentences, no em dashes, no banned phrases, never the "this isn't X, it's Y" pattern. Carry forward specific numbers (baselines, prior-experiment lifts, p-values). They anchor the reader. Name mechanisms, not outcomes ("the gate pulled users out of the job they came for", not "users didn't convert").

## Safety rules

- **Never fabricate metrics or baselines.** Use only analytics data, prior experiments, or what the user provides. If you don't have a baseline, say "baseline TBD, pull from analytics" rather than inventing one.
- **Always run the adversarial sub-agent** (Step 4). It's the point of the skill. Don't replace it with the main agent putting on a hat. Independence is the value.
- **Always diverge before you converge** (Step 3). Bringing one idea straight to the decision step defeats the purpose.
- **Always show the draft** before pushing to Notion or saving.
- **One-sentence, jargon-free hypothesis.** If it needs two sentences, a semicolon, or a term you'd have to explain, it isn't done. Rewrite it before showing the draft.
- **Always apply the Notion formatting rules** and re-fetch to verify. Don't report the push as done without checking.
- **Keep the main pitch scannable.** Push rigor and rejected options into the appendix.
- **Pitch intent, not pixels.** Specific in intention, flexible in implementation.
- **Name a guardrail / trade-off metric.** A pitch with no named downside fails the gauntlet.
- **Pre-commit the finish line.** Every pitch needs ship/rollback/iterate criteria before launch.
- **Don't prescribe sprint counts.** T-shirt sizes only.
- **Don't overwrite existing Notion content.** Create a new roadmap item, or update only the page body if given a specific URL.

## Bundled references

- `references/divergence-toolkit.md` — the evaluate-mode flips and SCAMPER prompts for Step 3.
- `references/adversarial-brief.md` — the verbatim brief for the Step 4 sub-agent.
- `references/voice-style-guide.md` — the voice rules. Swap in your team's guide if you have one.
