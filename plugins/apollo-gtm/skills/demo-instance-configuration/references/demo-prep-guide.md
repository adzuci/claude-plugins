# Demo Prep Guide — generation reference (added 2026-08-19)

Loaded by Workflow Step 10. Governs the single self-contained HTML file this skill writes at the end of a run: a read-only receipt of what was prepped and what was built, for the SC to keep open next to the Claude session during the call.

`references/demo-prep-guide-template.html` is the file that gets written. This document says what fills its slots.

## The three rules that govern every slot

**1. Nothing appears on the page that `demo-prep-intelligence` or this skill did not generate or gather.** "Gathered" includes Salesforce record data the skills ingest. There is no fourth source — not this skill's own judgment, not plausible-sounding filler, not a rephrasing that adds a claim the source did not make.

**2. Cite the Salesforce field label, never the API name — and take the label from `demo-prep-intelligence`'s SFDC Field Dictionary rather than reading it off the API name.** Two labels in the qualification set do not match their API names at all: `Negative_Consequences__c` is labelled **Business Impact** and `Before_Scenario__c` is labelled **🔴 Identified Pain**. The hand-built prototype this design comes from shipped "Negative Consequences" as a label — a field this org does not have. If a label is not in the Field Dictionary, cite nothing rather than guessing one.

**3. When a source is empty, show it empty and say which source was empty.** Do not fill the gap, and do not silently drop the row — a dropped row is indistinguishable from a field that does not exist, and the empty one is usually the actionable fact. This is `references/canvas-generation.md`'s omit-never-invent rule with one deliberate difference: that file omits an unsourced section, this one **renders it as visibly empty** where the emptiness is itself information the SC should act on. Per-block behaviour is in the mapping table; where the table says omit, omit.

**A note for whoever adds the next block to this artifact.** Rules 1-3 work — dry runs confirm a generator will refuse to invent. The consequence is that **under-specification in this file shows up as a silently empty block, not as an error.** Four separate blocks have rendered empty or thin because this file named a source it never supplied: an inventory it did not enumerate, a group whose scope was written too narrowly, a link whose host was unstated, and a crumb with no URL scheme in existence. So when adding a block, check the inventory behind it, not just the rule governing it — and if a source cannot be supplied, say so here rather than leaving a slot that will quietly come out blank.

**Why these are stated this bluntly.** Five talk-track quotes were fabricated while mocking this artifact up, then pasted into a downstream prompt whose own instructions said "use exactly this, invent nothing" — so they were reproduced faithfully and arrived looking sourced after passing through three hands. Nothing in any run or record contained them. A generated artifact removes the hand-population step where that happened; it does not remove the temptation.

**This skill still does not investigate.** Everything below reads from the Layer 1 handoff, the approved plan, and this run's own results. Generating this guide never authorizes a new query, a Salesforce read, or any research call — a slot with no source is an empty slot, not a research task.

## Section-to-source mapping

| Block | Source | When the source is empty |
|---|---|---|
| `{{ACCOUNT_NAME}}` | The account name resolved by Layer 1 | Cannot be empty — if there is no resolved account, do not generate a guide |
| `{{GENERATED_AT}}` | Today's date, `YYYY-MM-DD` | n/a — always stamped, see "Why the stamp matters" |
| `{{META_FACTS}}` | Brief §1 Account Snapshot plus the deal metadata Layer 1 extracts: domain, employee count, segment, tier, region | Omit that one fact from the line. Never write `Unknown` into the header — an absent fact reads better than a header full of unknowns |
| `{{STAGE}}` | Opportunity Stage from the deal metadata | Omit the stage span entirely |
| `{{CRUMBS}}` | The Salesforce Opportunity and Account records only. **A bare record ID is not a link** — see below. **No Apollo crumb**: there is no documented per-team URL scheme, so the Team ID goes in the Environment card instead, which is its designated place | Omit the individual link. If neither resolves, emit nothing — the container collapses |
| *(no token)* — the CTA | Constant in the template: `Log into Test Box Environment` → `https://app.testbox.com/deals`. See "The environment CTA" below | n/a — never substituted, never derived |
| `{{HEADLINE_RISK}}` | The single most decision-critical item among **🔴 Next Step**, **Close Date**, and **Solution Engineer Notes** | Render the lead as `No headline risk on record.` with a `cf-n` chip naming the fields checked. Do not promote a lesser item to fill the slot |
| `{{OPEN_WITH}}` | Brief §7 Open Questions, the "Ask these in the first 5 minutes" list. Not the internal AE/SC sync questions — those are internal | One `<li>` reading `The brief produced no opening questions for this deal.` |
| `{{DEMO_PATH}}` | `what` ← Brief §5 Recommended Demo Flow, one step per item, in the brief's order. `why` ← the pain point or decision criterion that item cites. `say` ← the `Demo talk-track hook` from the Apollo AI demo setup prompt covering that step | No flow at all: omit the whole section. Flow present but a step has no hook: emit the no-hook line (below) — **never compose a hook** |
| `{{ENVIRONMENT}}` | The approved plan's action list, Step 6's provisioning result, and Step 7's batch result | See "The Environment block" below — a failed run is reported as failed, not as staged |
| `{{QUALIFICATION}}` | The handoff's Qualification Record Block, pillars in its order: Metrics, Economic Buyer, Decision Criteria, Decision Process, Paper Process, Identified Pain, Champion, Competition | No block in the handoff: omit the section and the divider above it, and say so in the Step 10 completion note. Block present with `EMPTY` pillars: render those rows empty per the pill rules |
| `{{VALUE_CASE}}` | The same block's Force Management trio: Before state, Business Impact, After scenario | Same as above |
| `{{WATCHOUTS}}` | Brief §6 Landmines, plus §4 Competitive Landscape positioning notes and gaps | Omit the section if both are empty. Do not carry a `Unknown` landmine through as a watch-out — an unknown blocker is not a warning |
| `{{PEOPLE}}` | Brief §2 Stakeholder Map, including its risk flags. A stakeholder with no engagement evidence gets the `<em>Not yet engaged.</em>` treatment | Omit the section if the map has no stakeholders |
| `{{ALSO_AVAILABLE}}` | The fixed inventory under "The Also available inventory" below, each item sorted into `GENERATED` or `NOT GENERATED` by whether the handoff shows this run produced it | Never drop the section. An inventory item with no evidence in the handoff belongs under `NOT GENERATED` — that is the whole point of the block. Drop a *group* only if it would be empty |
| `{{SOURCES}}` | The sources the brief cited inline — records, calls, dealroom, web | Say plainly what was unavailable, e.g. `No Slack deal room exists for this deal.` Sparse sources are a fact the SC needs |

**A bare Salesforce record ID is not a link, and turning one into a link requires inventing the org's domain.** `006UM00000TzvVMYAZ` names a record; it does not say which Lightning host serves it. Constructing `https://<something>.lightning.force.com/lightning/r/Opportunity/<id>/view` means guessing `<something>`, and a guessed host produces a button that goes nowhere — the same failure as `href="#"`, just harder to spot. **The org's Lightning host is `apolloio.lightning.force.com`** — stated here as a constant so a record ID *can* become a link, rather than left to be guessed per run. **This is an org-specific value with no single source of truth in this repo** (it also appears in `demo-prep-intelligence/SKILL.md`'s usage example and two `data-duel-assistant` references): if Apollo's My Domain ever changes, every one of those places needs updating and every guide generated before the change carries dead links. Raised in review on [PR #238](https://github.com/apolloio/claude-plugins/pull/238); accepted as-is because the alternative — omitting the crumb entirely — costs the SC a working link on every run to guard against a rename that has not happened. Build Opportunity and Account crumbs as `https://apolloio.lightning.force.com/lightning/r/<SObject>/<id>/view`. Use no other host. **Every crumb anchor must carry `target="_blank" rel="noopener noreferrer"`.** The guide is meant to stay open beside the Claude session for the whole call. A crumb that navigates in place costs the SC the artifact they are running the call from, and unlike a wrong host that failure is invisible until someone clicks it mid-demo. The `rel` is not decoration: `target="_blank"` alone hands the opened Salesforce tab a live `window.opener` handle back to the guide. The template's own Testbox CTA already carries both. **These crumbs are generated here rather than in the template**, so the template cannot enforce it, and a template-only fix would silently miss them. **Note the exact spelling: `apolloio`, not `apollo`** — that one missing character is a link that 404s, and it is the mistake that produced this rule.

If the handoff carries neither a URL nor a record ID for a given object, omit that crumb. An ID-only handoff is now enough for a working link; nothing else is.

**Why the stamp matters.** The prototype's most prominent claim — a headline risk built on a close date — went stale in eight days because the date moved after the run. The stamp is what tells an SC whether they are reading a receipt of today's run or last month's. It is also the reason this artifact is generated per run and never hand-maintained.

## Pill and chip vocabulary

**Status pills.** Solid fill means the information exists; a dashed outline means there is a hole. Nothing shouts unless it is actionable, and absence looks like absence rather than an alarm.

**The pill is a direct read of the handoff's `state` field — never re-derived here.** Layer 1 already resolved it against an ordered, exclusive four-test rule; re-deriving it from the values on this page would produce a second answer that can disagree with the first, which is the same two-conflicting-specs problem the prompt-precedence rule exists to stop. Map it one-to-one:

| `state` | Markup | Reads as |
|---|---|---|
| `VERIFIED` | `<span class="pill solid">VERIFIED</span>` | On record and confirmed |
| `PARTIAL` | `<span class="pill flag">PARTIAL</span>` | Some of it is there; needs attention |
| `UNCONFIRMED` | `<span class="pill hole">UNCONFIRMED</span>` | Populated but not confirmed |
| `EMPTY` | `<span class="pill hole">EMPTY</span>` | Nothing captured |

**Do not emit any other pill text on a qualification or value-case row.** In particular `THIN`, `WEAK` and `UNKNOWN` are forbidden: they are judgments about how good the content is, nothing in the handoff grounds them, and a generator producing them is inventing. The prototype carried all three because a person wrote them.

**Confidence chips** trail the claim they qualify:

| Handoff confidence | Chip |
|---|---|
| `verified` | `<span class="cf cf-v">verified &middot; [label]</span>` |
| `inferred` | `<span class="cf cf-i">inferred &middot; [label]</span>` |
| `assumed` | `<span class="cf cf-i">assumed &middot; [label]</span>` |
| field is null | `<span class="cf cf-n">empty &middot; [label]</span>` |

`assumed` shares `cf-i`'s amber styling because both mean "not confirmed," but **the chip text still reads `assumed`** — the distinction stays visible in words even though there are only three chip colours. Never relabel an `assumed` claim as `inferred`.

`[label]` is the verified Salesforce field label, or the named non-Salesforce source (`Gong`, `Apollo AI prompt 4`, the prospect's site).

## Row markup

Copy these shapes. The template's `<style>` block is data — **reproduce it byte-for-byte and never edit, reformat, minify or "improve" it.** The design is settled; a run that restyles it produces an artifact that no longer matches every other one.

Demo path step, with and without a hook:

```html
<div class="step"><div class="n">1</div><div>
  <div class="what">[flow item]</div>
  <div class="why" data-lvl="2"><b>Why:</b> [the pain or criterion it cites].</div>
  <div class="say" data-lvl="3">“[verbatim hook]”<span class="cf cf-v">verified &middot; Apollo AI prompt 1</span></div>
</div></div>

<div class="step"><div class="n">4</div><div>
  <div class="what">[flow item]</div>
  <div class="why" data-lvl="2"><b>Why:</b> [the pain or criterion it cites].</div>
  <div class="say nohook" data-lvl="3">No talk-track hook generated for this step.</div>
</div></div>
```

Qualification / value-case row, populated and empty:

```html
<div class="row"><div class="pil">Metrics</div><div><span class="pill solid">VERIFIED</span></div>
  <div class="cell">
    <div class="know" data-lvl="2">[value]<span class="cf cf-v">verified &middot; 🔴 Metrics</span></div>
    <div class="gap"><b>Gap:</b> [only from an Open Question that maps to this pillar].</div>
  </div></div>

<div class="row"><div class="pil">Business Impact</div><div><span class="pill hole">EMPTY</span></div>
  <div class="cell">
    <div class="gap"><b>Gap:</b> Business Impact is empty on the opportunity.<span class="cf cf-n">empty &middot; Business Impact</span></div>
  </div></div>
```

**The `Gap:` line is the single most likely place invention enters, so it is constrained.** Only three forms are allowed:

- `state: EMPTY` → `[Label] is empty on the opportunity.` Nothing more. Do not add advice about what to ask; that advice was not generated by anything.
- `state: UNCONFIRMED` → `Populated but not confirmed — validate before relying on it.`
- `state: VERIFIED` or `PARTIAL` → emit a gap line **only** when Brief §7 Open Questions contains a question that maps to this pillar, and then use that question's own wording. Otherwise omit the line.

Person row, engaged and not:

```html
<div class="person"><div class="nm">[Name]</div><div class="rl">[Title]</div>
  <div class="ds">[role in deal].<span class="cf cf-v">verified</span>
    <div data-lvl="3">Cares about: [from the brief's Cares about line].</div></div></div>

<div class="person"><div class="nm">[Name]</div><div class="rl">[Title]</div>
  <div class="ds"><em>Not yet engaged.</em> [what the record does say].<span class="cf cf-n">no data</span></div></div>
```

## Level assignment

The three views are **strict subsets, not three documents**: AE ⊂ Hybrid ⊂ SC. Every gated node carries the lowest level at which it appears, and AE view is the default — set on the `<body>` tag, so with JavaScript disabled the page renders AE view rather than blank.

Assign by role, not by length:

- **No `data-lvl` (AE view, always visible)** — the headline risk lead, the first two Open with questions, every Demo path `what`, the Environment lead and its failure note, every Qualification and Value case pill and `Gap:` line, the first two Watch-outs.
- **`data-lvl="2"` (Hybrid adds)** — Demo path `why` lines, the object list in the Environment card, the `know` value lines on qualification rows, remaining Open with questions and Watch-outs, the whole People section.
- **`data-lvl="3"` (SC view adds)** — Demo path `say` lines, second and later `know` lines on a pillar, per-person "Cares about" detail, the Also available and Sources sections.

**The gap and the CTA appear on every view.** A missing economic buyer or thin metrics is exactly what an AE needs, so it is never gated behind Hybrid — only the supporting detail is.

**Never gate a `Gap:` line or a pill.** If a row's only content is a gap, that row is fully visible at AE view. This is the rule most likely to be broken by treating `data-lvl` as a length control.

## The Environment block

Report **only what this run actually did**. The prototype originally read "Staged…" for a run whose provisioning had died on a seat limit and which created nothing — the single worst kind of error this artifact can make, because the SC would walk into a call trusting an instance that does not exist.

- **Provisioned and configured** — lead states what exists; the `.objs` grid lists the objects Step 7 reported created, each with its state (`draft`, `inactive`, `shared`).
- **Approved but not provisioned** — lead reads `Approved configuration` and a `.note` states plainly that provisioning did not complete, why, and that **nothing was created**.
- **Partially executed** — list what was created and state which actions failed. If Step 7 surfaced `attempts > 1`, say a duplicate may exist and name the record IDs, exactly as Step 7 reported them.
- Keep the `data-lvl="3"` note about inert defaults (sequence is a draft, workflow inactive, so nothing sends) whenever those defaults applied.
- **Always carry the two access-path notes** from "The environment CTA" below. The CTA alone is one step of four, and the remaining three are tribal knowledge an SC should not have to already have.

**Never write the `api_key` or the `login_url` into this file.** Both are governed by `Provisioning the Demo Sub-Account`; a file the SC may share is the last place either belongs. The Team ID is fine.

## The environment CTA

**Both the label and the target are constants, baked into the template — there is no token to fill and nothing to derive per run.** The button reads `Log into Test Box Environment` and points at **`https://app.testbox.com/deals`**. Leave the element exactly as the template has it.

**Two different things are both called "Testbox," and confusing them is how this button ends up pointing at the wrong place:**

- **Testbox the tool**, at `app.testbox.com` — the product SCs log into to reach demo environments. **This is what the CTA targets**, and its `/deals` page is the SC's entry point.
- **"Testbox Development 1"** — the Apollo *parent team* every demo sub-account is provisioned under, Team ID `67572bf036b5c001b03be634`. This is an Apollo team, not a URL, and it is never a link target.

**The CTA is step 1 of a four-step path, not the whole journey.** Reaching a tailored demo instance goes:

1. Log into **Testbox the tool** — `https://app.testbox.com/deals`. **This is what the CTA targets.**
1. Click **Start Demo** in the Testbox portal. That triggers a script in the SC's browser which logs them into the **Testbox Development 1** Apollo instance.
1. Inside that instance, open **Sub-accounts** — `https://app.apollo.io/#/sub-accounts`.
1. Next to the target sub-account, click its **Log In As …** link to God-mode into the tailored instance.

**Why the CTA points at step 1 and not step 3, even though step 3 has a stable URL.** `app.apollo.io/#/sub-accounts` resolves against whatever Apollo org the browser session is already in. Without step 2 having run, an SC signed into the RevOps org lands on the wrong sub-account list — which is exactly what the "logged into Testbox rather than RevOps" caveat from the 13:00 sync is warning about. Step 1 is the only entry point that reaches the right place from a cold browser.

**Carry the path in the Environment card as two `.note` lines, using this wording** (the second names this run's sub-account, so the SC knows which row to click rather than scanning a list of prospect names):

```html
<div class="note">Access path: log into Testbox, click Start Demo, then open Sub-accounts in the Testbox Development 1 instance.</div>
<div class="note">Then click <b>Log In As</b> next to <b>[sub-account name]</b>. You must be in the Testbox Development 1 instance rather than RevOps for that list to be the right one.</div>
```

When no sub-account was created (provisioning failed, or the plan was approved but not run), keep the first note and replace the second with one line saying there is no sub-account to log into yet. **Do not name a row that does not exist.**

**Not a per-sub-account deep link, either.** The provisioning response's `login_url` is a live account-creation token that completes onboarding *as the prospect* rather than opening the instance for a demo, and step 4's God mode is what keeps manual changes attributed to the real person who made them. Pointing this button at `login_url` would break both. See `Provisioning the Demo Sub-Account`.

**Never emit a dead target** — no `href="#"`, no empty `href`, no placeholder string. A button that silently does nothing is worse than no button. If the constant above is ever removed from the template rather than replaced, drop the whole `<a class="cta">` element and keep the access-path notes.

## The Also available inventory

**This list is fixed, and it is a property of `demo-prep-intelligence`'s design rather than of any deal — so it does not come out of the handoff and must not be derived from it.** Nothing deal-specific is invented either way: the item names are generic, and only the sorting depends on the run.

**Sort from the handoff's `Produced this session:` line (its Block 3), matching its names against the table below.** The names in this table are the same fixed vocabulary Block 3 writes, so they match literally — **if one ever does not, treat it as a spec bug to fix rather than something to resolve by guessing at intent.** A mismatch was found in review on [PR #238](https://github.com/apolloio/claude-plugins/pull/238), where this table read "Deal-specific Context Center calibration notes" against Block 3's "Context Center calibration notes," which would have told an SC to re-run for work they already had. An item on that line goes under `GENERATED`; every item not on it goes under `NOT GENERATED`. **Do not infer production from anything else** — not from the presence of a prompt set, not from the brief's contents, not from what a run of this shape usually produces. Block 3 is written on every Layer 1 run, so its absence means an old or incomplete handoff, not a run that produced nothing: in that case put the whole inventory under `NOT GENERATED` except items the handoff itself visibly contains, and say in the Step 10 completion note that the handoff carried no Block 3.

| Inventory item | What it is |
|---|---|
| Apollo AI demo setup prompts | The paste-ready prompt set for the in-app AI Assistant. `GENERATED` whenever the handoff carries them — say how many, and name each prompt's subject in one clause |
| Context Center calibration notes | The deal-specific calibration block, held separate from the global company profile. **Counts as produced whenever the handoff's Context Center payload carries a deal-specific calibration section**, whether or not Block 3 names it separately — a live run treated the two as one artifact and listed only the payload |
| Strategic angle | Why Buy Anything, Why Now, Why Apollo, and value-driver mapping. Synthesis Part 1 |
| Fuller talk track | Phrases to Use and Phrases to Avoid, plus the demo-day execution order. Synthesis Part 4 |
| Pre-demo checklist and post-demo actions | Synthesis Parts 4 and 5 |
| Run Sheet | A time-blocked cue card to keep open during the call, compiled from the demo flow and talk track. Never a new source, just a compilation |
| Slack deal room Canvas | The deal's shared reference surface, compiled from the session and posted to the dealroom |
| AE sync questions | With a copyable coordination message ready to send to the AE |
| Calendar and Gmail alignment check | Reconciles attendees, timing and recent threads against the deal before the call |
| SC walkthrough | The implementation walkthrough for the SC. Synthesis Part 4 |
| Post-demo debrief prep | The follow-up pass after the call |

**Group headings and their calls to action:**

- **`GENERATED`** — `<span class="pill solid">GENERATED</span> Produced on this run and saved to the session handoff file — <b>ask Claude to show any of these.</b>`
- **`NOT GENERATED`** — `<span class="pill hole">NOT GENERATED</span> Skipped by the configuration fast path — <b>re-run <code>/apollo-gtm:demo-prep-intelligence</code> on this opportunity to produce them.</b>`

**Why this block is load-bearing rather than decorative.** The configuration fast path deliberately deletes the menu where an SC would otherwise learn these artifacts exist, so on the fast path they are unreachable in the exact flow SCs are told to use. This block is the only place they get advertised. **A run that renders it with one item, or drops it because the handoff did not enumerate the inventory, silently reintroduces that gap** — which is why the inventory is written out here instead of being left to derivation.

Where an item's status is genuinely ambiguous from the handoff, put it under `NOT GENERATED`. Under-claiming costs an SC one re-run; over-claiming sends them looking for something that was never produced.

## Apollo AI setup prompts as specification

Where a prompt from the Layer 1 handoff and this skill's own derivation describe the same object, **the prompt governs** — see the Input Contract. That has two consequences here:

- The Environment block describes the object as the prompt specified it, because that is what was built.
- A prompt with **no** Layer 2 counterpart stays uncounterparted. Prompt sets routinely include items that are live walkthroughs or pre-demo readiness checks rather than stageable objects; those never appear in the Environment block as though something was created. Prompts governing does not mean prompts must all become staged objects.

**One clarification, because a dry run read it the narrow way — added 2026-08-20.** The point above is about the *Environment* block. It does **not** mean the Also available section's `GENERATED` group is only for prompts that lack a counterpart. That group covers **every** inventory item the handoff shows this run produced, the full prompt set included — a prompt that did get built as an object is still a prompt the SC can ask to see. Reading it narrowly rendered a one-item callout on a run that had produced the whole prompt set plus calibration notes.
