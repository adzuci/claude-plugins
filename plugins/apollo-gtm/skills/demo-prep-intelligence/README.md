# demo-prep-intelligence

A Claude Skill that turns scattered pre-demo intel — discovery notes, CRM data, public signals, prospect website material — into a structured, SC-ready demo brief.

## What it does

- Synthesizes raw deal context into a tight, demo-day-usable brief
- Maps prospect needs to Apollo capabilities using a defined capabilities map
- Surfaces likely technical blockers and competitive positioning before they bite
- Can compile an internal Slack Canvas deal room for the AE/SC team when appropriate — an internal-team artifact, never prospect-facing (see `references/canvas-generation.md`)
- Aligns to the deal lifecycle so the output is staged correctly (discovery vs. technical validation vs. business case)

## When to use

Load this skill when an SC needs to:

- Prep for a discovery or technical demo
- Synthesize call notes + research into a single working brief
- Anticipate objections, blockers, and competitive landmines
- Compile an internal Slack Canvas deal room for the AE/SC team (internal only — not a prospect-facing demo artifact)

## Repo contents

- `SKILL.md` — the skill definition (frontmatter + orchestration logic)
- `SC-GUIDE.md` — the human-readable SC operator guide
- `GOVERNANCE.md` — non-negotiable output, messaging, and read-only rules; canonical source for the SC-Facing Output Rules, Outbound Messaging Pipeline, and Operating Boundaries. Load unconditionally, every session.
- `references/` — modular reference files the skill loads on demand:
  - `apollo-ai-prompt-patterns.md`
  - `canvas-generation.md`
  - `capabilities-map.md`
  - `competitive-positioning.md`
  - `data-sources.md`
  - `deal-lifecycle-support.md`
  - `output-template.md`
  - `synthesis-template.md`
  - `technical-blockers.md`

## Installation

Drop this folder into your Claude Skills directory. Reference files are loaded by `SKILL.md` on demand — no manual wiring required.

## Pipeline position

```
deal context (discovery notes, CRM, public signals)
    │
    ▼
demo-prep-intelligence ──▶ structured demo brief + Apollo AI Context Center payload
    │                          (both also written to demo-prep-scratchpad.md — the Layer 2 handoff)
    │
    ├──▶ SC walks into the demo with the right story, the right blockers flagged,
    │    and the right capability mapping
    │
    ▼
demo-instance-configuration (Layer 2) ──▶ proposes a config plan, gets SC approval,
    │                                      provisions a fresh demo sub-account
    ▼
Democles (Layer 2 execute) ──▶ writes the approved config into that sub-account
```

The Layer 2 handoff is not optional: rendering a brief, synthesis package, or Context Center payload writes it to `demo-prep-scratchpad.md`, which is the only channel `demo-instance-configuration` has for picking it up.

## Maintainer

David Johnson — Senior Solutions Consultant, Apollo.io

This skill and its underlying consulting frameworks are authored by David Johnson. For feedback, questions, or bug reports, DM @David on Slack.

## Changelog

### v1.4.0

Aligned to the `apollo-gtm` repo's conventions ahead of the merge. Behavior inside a run is unchanged; how the skill is *entered* is not.

**1. `disable-model-invocation: true` added — the skill is now direct-invocation only.** The repo's `AGENTS.md` sets this as the default (*"Default new skills to `disable-model-invocation: true` so they do not add routing context unless the user calls them"*), reviewers are instructed to flag skills that omit it, and **all five existing `apollo-gtm` skills carry it.** The `v1.3.8` decision to stay auto-invocable was made before any of that was known. Per Claude Code's docs the flag means *"Only you can invoke the skill"* — so an SC now types `/apollo-gtm:demo-prep-intelligence` rather than describing the task in prose.

**2. Description cut from 1,354 characters to one concise line.** `AGENTS.md`: *"Set `description` to one concise line describing what the skill does. Avoid long trigger lists unless natural-language activation is intentional."* With item 1 in place, natural-language activation is not intentional, so the trigger list had no remaining job.

**This resolves the `deal-execution` overlap outright.** `v1.3.8` addressed it by adding an explicit boundary clause to the description; with neither skill model-invocable, there is no automatic selection between them to get wrong, and the clause was dropped along with the rest of the trigger text. The open question of whether this skill should match `deal-execution`'s slash-only pattern is now answered — it does.

**3. Usage examples added to the body.** `AGENTS.md` requires direct-invoked skills to document their inputs as usage examples rather than declaring `arguments` frontmatter. Everything after the command is still read as the SC's message, so Step Zero's intent detection and `SC-GUIDE.md`'s routing table are unaffected.

**Deliberately not applied to `demo-instance-configuration`.** Layer 2 must stay model-invocable or the Layer 1 → Layer 2 handoff breaks: `v1.3.7` made Layer 1 call the `Skill` tool on an explicit go-ahead, and the flag would block exactly that. There is no setting for "invocable by a sibling skill but not autonomously," so Layer 2 remains auto-loadable on its own; its approval gate is the control.

**Untested in this form** — invocation changes only take effect on install.

### v1.3.9

Closes a first-run friction defect that had been misdiagnosed as an environment problem since 2026-07-09.

**1. `allowed-tools` now declares `Read` and `Write`.** It previously declared only `AskUserQuestion`. Per Claude Code's frontmatter reference, `allowed-tools` grants tools "Claude can use without asking permission during the turn that invokes this skill," and "your permission settings still govern tools that are not listed." So every file this skill loads after `SKILL.md` - `GOVERNANCE.md`, `SC-GUIDE.md`, and each `references/*.md` - was a `Read` call subject to whatever the individual user's permission settings happened to allow. On a machine with no persisted `Read` allow-rule, that is a run of consecutive approval prompts at the top of the very first run, which presents as the skill struggling rather than as a missing grant. `Write` had the same gap on the mandatory scratchpad handoff - the one write `GOVERNANCE.md` calls "a mandatory step, not a discretionary permission."

**Why it took eleven versions to surface:** it was originally investigated on 2026-07-09 and pinned on the *user's* settings not carrying a persisted `Read` rule. That was true but was the symptom. The cause is that the skill never granted itself one, so every user starts from the same empty slate; one-off "Yes" clicks papered over it and don't persist. Checked against `GOVERNANCE.md` before adding `Write`: it already names the scratchpad file as "the single, narrow exception" and specifies the convention, so this pre-approves what that file authorizes rather than widening it.

**2. The scratchpad write is now specified as a direct `Write`, with shelling out explicitly forbidden.** A live run was observed calling `mkdir -p` on the scratchpad directory before writing. Nothing in any instruction file asks for that - it was improvised, the host already provides the directory, and the call returned empty. Reaching for `Bash` is out of character for a skill whose stated boundary is read-only plus one file, so the rule now says to use `Write` on the target path and nothing else, and to report a genuine failure plainly rather than shelling out to fix it. **Deliberately not addressed by adding `Bash(mkdir *)` to `allowed-tools`** - that would have pre-approved behavior the skill never specified.

**Known limitation:** the grant covers the turn that invokes the skill and clears on the SC's next message, so reference files loaded in later turns can still prompt. Smaller than the opening wall, not zero.

**Untested in this form** - `allowed-tools` changes only take effect on install, so this is verified against the documentation rather than against a run.

### v1.3.8

Pre-merge pass for absorption into the `apollo-gtm` plugin. No behavior change inside a run; both items only matter once this skill ships as a sibling of `deal-execution`.

**1. Plugin prefix corrected on all three functional references.** `/apollo-gtm-solutions:demo-instance-configuration` became `/apollo-gtm:demo-instance-configuration` in the prescribed handoff line and the `Skill`-tool invocation instruction (`SKILL.md`), and in the "selecting Configure the demo instance is an explicit go-ahead" rule (`SC-GUIDE.md`). Shipped unchanged, these would have handed the SC a slash command that doesn't resolve and attempted a `Skill` call that can't - presenting as the sibling skill being missing rather than as a naming error, i.e. a worse form of the exact bug v1.3.6 and v1.3.7 were spent fixing.

**2. Description tightened against `deal-execution`'s.** The old text closed on "or guided deal support," nearly as unbounded as `deal-execution`'s "Load when working on any Apollo sales activity." Rewritten to lead with the demo-prep use case, state the Layer 1 role explicitly, scope the trigger to "when a demo is the object of the request," and name the boundary directly: deal review, stage/MEDDPICC validation, email composition, objection handling, competitive positioning, pipeline inspection, inbox triage, and deal channel management belong to `deal-execution`. 1,354 characters, inside the 1,536-character skill-listing cap, so nothing truncates.

**Finding that reframed this item, worth keeping.** `deal-execution` carries `disable-model-invocation: true`, so Claude cannot auto-load it - it is reachable only by slash command. The risk previously assumed (the model choosing `deal-execution` over this skill) therefore cannot occur. The live risk runs the other way: this skill has no such flag, so post-merge it is the auto-invocable one and would catch vague deal requests David intended for his slash command. That is what the description change addresses. Whether this skill should instead match `deal-execution`'s slash-only pattern is a question for David as author of both; keeping it auto-invocable was the deliberate call here, on discoverability grounds.

### v1.3.7

Handoff invocation fix, from the first live run of the v1.3.6 build. Two related corrections, both traced to a single wrong factual claim this file's own v1.3.6 pass introduced.

**1. The skill now invokes `demo-instance-configuration` on an explicit go-ahead.** A live run ended with the SC saying "go ahead" and the skill replying that it *"can't chain directly … skills don't invoke each other as function calls"* — then asking the SC to run the slash command themselves. That claim is false. Claude Code's skills documentation states *"By default, both you and Claude can invoke any skill,"* a `Skill` tool exists for exactly this, and `demo-instance-configuration` sets no `disable-model-invocation` flag. On an explicit go-ahead — including selecting "Configure the demo instance" from any Deal Action Menu — the skill now calls the `Skill` tool directly, with the slash command kept only as a stated fallback for when that tool is genuinely denied or errors. **Chaining is still never automatic:** Layer 1 deciding to start Layer 2 is the SC's call, not the skill's.

**2. Root cause was a sentence added in v1.3.6.** The v1.3.6 fix for the "isn't available as an invokable skill" bug also asserted that *"this skill has no mechanism to invoke it directly (skills don't call other skills as functions) and was never meant to try."* That was wrong, and the live run echoed it back almost verbatim — the instruction planted the belief rather than the model inventing it. Corrected in place. The valid half of that rule is unchanged and still governs: never describe the sibling skill's *presence* as conditional or unverified. Also reworded the handoff line itself, which said "just say the word" — a false affordance that invited exactly the bare affirmative the skill then couldn't act on.

**3. `allowed-tools` semantics corrected against the docs.** v1.3.6 recorded an empirical guess that `allowed-tools` "is not exhaustive for MCP connector tools," implying it might restrict built-ins. It restricts nothing: the docs define it as *"Tools Claude can use without asking permission during the turn that invokes this skill,"* clearing on the next message — a permission pre-grant, not an allowlist. Removing tools is a separate field, `disallowed-tools`. So the sibling skill adding `Bash` made shell access *unprompted*, not newly possible, and there is no built-in-vs-MCP distinction here.

**4. Calendar + Gmail alignment can no longer grant itself a caveat.** A live run rendered *"Calendar + Gmail alignment: not run — proceeding with caveat (no calendar/email search performed this session)"* and then produced a full Context Center payload plus four Apollo AI prompts. Three problems at once: `not run` isn't one of the gate's four defined statuses (`found | partial | not_found | unavailable`, all of which presuppose an attempt), the caveat was self-granted without asking the SC, and doing so tripped an existing anti-pattern. Now explicit: the four statuses are exhaustive, `unavailable` requires a real failed attempt rather than an un-attempted check, the gate fires whenever the meeting exists regardless of who mentioned it, and **only the SC may grant a caveat** — via `AskUserQuestion`, offering "supply the details" or "proceed with caveat." The v1.3.6 pass had tightened *which* gates may be caveated without ever addressing *who may grant one*.

**5. Stakeholder Map now carries contact emails.** Layer 2 needs the prospect-side Apollo Admin's email to provision a demo sub-account and has no research capability of its own, so an email absent from the handoff becomes a cold prompt to the SC for something the deal record already held — which is what happened live. Emails are now included when the SFDC contact record has one, with an explicit prohibition on fabricating one (no `first.last@domain` guessing, no constructing from the company domain). Omitting remains correct when SFDC has none: a prompt is a fine outcome, a wrong email would provision a real account to the wrong person.

No change to the read-only invariant, the confidence model, or the seven-section brief contract. Item 4 changes gate *procedure* (who may waive a check) without changing which gates exist or what they require.

### v1.3.6

Cross-file alignment pass. A full audit of all four instruction files found that **every drift ran the same direction: the file that wins on conflict was more restrictive than the file specifying the feature.** That is the same mechanism as the v1.3.4 Step Zero bug, found in four more places. All fixes below are reconciliations, not new capability — no change to the read-only invariant (beyond naming its one existing exception explicitly), the 3-value confidence model, the attribution block, or the seven-section brief contract.

**1. `SC-GUIDE.md` no longer contradicts the mandatory scratchpad write.** Design Principle 5 said the skill "never … writes to any system" and the Deal Continuity Model said it "does not persist private deal state," while `GOVERNANCE.md` requires exactly one handoff file per run and `SKILL.md` calls that write unskippable. An agent obeying `SC-GUIDE.md` would skip it, and `demo-instance-configuration` — which checks for that file first on every run — would silently fall through to its paste fallback. Both statements now name the exception explicitly. Related: `SKILL.md`'s Terminal Output Assertion said "It has two conditions" while listing three; the uncounted one was the scratchpad write.

**2. The Company + Business Understanding Gate is no longer bypassable via `SC-GUIDE.md`.** Its Visible Gate Block Presentation section listed all three preconditions as caveat-eligible (`passed | not met | proceeding with caveat`). `SKILL.md` is absolute that this gate blocks — it names a miscalibrated Context Center the highest-severity live-demo trap, since it produces wrong Apollo AI output in front of the buyer. `SC-GUIDE.md` also contradicted itself here: its own Step 1 intent table already scoped the caveat correctly to meeting-evidence and Calendar/Gmail only. Now scoped to those two everywhere, with the gate's non-bypassability stated where the block is described.

**3. The v1.3.3 hard-STOP menu fix, which had been silently reverted, is restored.** `SC-GUIDE.md`'s Interactive Prompt Rules said the menu is "persistent but **not blocking**" — the literal opposite of `SKILL.md`'s Menu Presentation Contract — and offered a plain-text menu "when no interactive prompt UI is available," reopening exactly the escape hatch v1.3.3 closed. Rewritten: always call `AskUserQuestion` (hosts degrade it themselves), end the turn on the call, and re-offer only after a genuine SC detour. Also dropped the nonexistent `ask_user_question` alternative.

**4. Step Zero's fast path closed in four more places.** The v1.3.4 fix added routing but left `SC-GUIDE.md`'s own absolutes intact: its Active interaction model paragraph still stated the intake-summary-first ordering unconditionally; Deal Entry step 5 never said what happens on "Skip to demo configuration"; two intent-table rows routed straight to that ordering without asking Step Zero's bounded question; and — most consequentially — the generic "configure my demo" row sits *above* the explicit demo-instance row with no reciprocal precedence guard, which is the precise failure mode of Step Zero's first live test. All four now carry carve-outs or guards.

**5. Two reference-file corrections.** `apollo-ai-prompt-patterns.md`'s rendered calibration template still emitted "Apollo product/service card to select or create" — the half of the v1.3.4-era `apollo_product_service_card` → `prospect_product_card` rename that was never applied to the template the model actually renders from, leaving the original bug live (a real dry run once produced a payload describing Apollo's own product instead of the prospect's). Fixed here and in `synthesis-template.md`, which repeated it. Separately, `deal-lifecycle-support.md` instructed "use the YAML payload above instead" as the first artifact for assigned-opportunity intent — contradicting SC-Facing Output Rule 1, the output-leak strip, and two statements in its own file. Reworded to point at the visible copyable-message-first flow.

**6. Target-environment wording.** Three places described the handoff as staging in "the live Tailored Demo environment." Since 2026-07-27 the sibling skill provisions a fresh sub-account per prospect.

**7. Slack Canvas and dealroom posting are now delegate-only (David Johnson's decision, as skill author).** `GOVERNANCE.md` has always forbidden Slack writes absolutely, while this file and `references/canvas-generation.md` documented an approval-gated `slack_create_canvas` path — so that whole path was canonically unauthorized while reading as a feature. David's call: reframe as delegate-only, which he noted also "help[s] to conserve tokens for the larger deals." This skill now **never** calls `slack_create_canvas`, `slack_update_canvas`, `slack_send_message`, or `slack_send_message_draft` under any circumstance. It composes Canvas-flavored Markdown and message drafts as copyable output; creating or posting is the SC's own action or a delegation to `deal-execution` under its own approval gate. `GOVERNANCE.md` now states that boundary explicitly rather than leaving it to inference — recording *where the line sits* is the actual fix, since otherwise the next reader re-derives the same contradiction. Also relaxed: the "must offer Build Slack Canvas after any major output" rule became "may offer," because `SC-GUIDE.md`'s bounded 2-4 option menus made an unconditional must-offer unsatisfiable by construction.

**8. "Standalone by Design" reworded to name `deal-execution` as a sibling dependency.** The prior claim ("requires nothing outside this plugin — everything it needs ships with it") was contradicted by the dealroom-send and canvas-delivery options, which cannot complete without `deal-execution`. Every *generation* path remains fully self-contained; only delivery delegates. This resolves at the merge into `apollo-gtm`, where `deal-execution` already lives; until then those options degrade to copyable text.

**9. `allowed-tools` semantics documented.** The frontmatter lists `AskUserQuestion` only while the instructions require several MCP connector reads. Clarified that it is not an exhaustive allowlist for connector tools — established empirically by many successful live runs — so nobody "fixes" it by enumerating every connector, or concludes a connector is unavailable because it isn't listed.

Two known items remain from that audit: a build-history de-narration pass, and one real action with a date — `references/capabilities-map.md`'s Apollo AI surface inventory needs human re-verification against the live app by **2026-08-02**, when its own 90-day staleness caution starts firing. That date was deliberately *not* reset during this pass, since bumping it without an actual review would falsify one.

### v1.3.5

Sibling-skill handoff fix. After a run completed, the skill told the SC that `demo-instance-configuration` "isn't available as an invokable skill in this session" — false; it was installed and slash-invokable the whole time, confirmed by the SC's own autocomplete. Root cause: the "Same-session continuation" handoff step said only "no extra step is needed" and never specified what to actually say, so the model improvised — apparently borrowing this file's genuinely-conditional Slack/dealroom-connector availability pattern for a situation where it doesn't apply. A sibling skill in the same installed plugin is always present. Fixed with a prescribed one-line hand-off and an explicit rule against ever framing a sibling skill's presence as an availability check.

### v1.3.4

Step Zero routing fix. The Configuration Fast Path added in the prior build was reachable only through `SKILL.md`'s own logic, but `SC-GUIDE.md` — the file that actually decides which flow runs — never routed to it, so genuinely qualified phrasing ("create a tailored demo instance for this opportunity: [SFDC URL]") fell through to the generic brief-producing row instead. Its first live test failed for exactly that reason. Fixed with a new Step 1 Detect-Intent row and a Deal Entry step checked *before* the assigned-opportunity check. A review of the same fix caught a second, higher-priority instance: `GOVERNANCE.md` — which governs on conflict and loads unconditionally every session — still asserted intake-summary-first in its own SC-Facing Output Rule 2, the same assertion already carved out four times in `SKILL.md` but never checked in the governing file. Given a matching carve-out.

### v1.3.3

Interactive-menu enforcement + tight default output. Runtime confirmed at the time: the **Claude.ai app (Opus)**, which renders Claude's `AskUserQuestion` tool as clickable option buttons. *(Current runtime, as of v1.3.6: Claude / Claude Code, per `SKILL.md`. `AskUserQuestion` renders as buttons there too, and hosts that can't draw them degrade the call to a text prompt on their own.)*

**1. Menus now fire `AskUserQuestion` (clickable buttons).** Root cause of the "no buttons / it just printed A-B-C-D" behavior: the agent never *called* the button tool — it emitted a Markdown list and stopped. A skill can only instruct the agent to call a runtime tool; it cannot draw a widget itself. Fixes: (a) added `allowed-tools: AskUserQuestion` to the SKILL.md frontmatter so the tool is available at every gate; (b) rewrote the **Menu Presentation Contract** to Claude's actual mechanism — a hard **STOP + call `AskUserQuestion` + do NOT proceed until the SC selects** pattern, with the concrete `question` / `header` / `options` shape; (c) forbade emitting a Markdown menu (`A./B./C.` or `1./2./3.`) without an `AskUserQuestion` call as an anti-pattern; (d) kept a numbered-menu fallback only for surfaces that don't render the tool. Verified in-app that `AskUserQuestion` renders as buttons.

**2. Tight default output (no more wall of text).** The router default flow already specified intake summary + copyable AE message + AE sync questions + menu as the default, with the seven-section brief downstream — but a live run dumped the full brief on intake anyway. Hardened Step 4 as the **terminal step of the default response** and added an explicit rule: producing the seven-section brief (or any Step 5+ action) in the same response as the intake, before the SC selects "Build brief", is a violation of both the router default flow and the menu STOP rule. The default response now ends at the Pick Your Path `AskUserQuestion` call.

No change to the read-only invariant, the 3-value confidence model, the attribution block, or the v1.3.2 Glean degraded-mode / Provenance Guard.

### v1.3.2

Resilience + presentation pass. Two fixes, no change to the read-only invariant or the 3-value confidence model.

**1. Interactive Pick Your Path menus.** Added a **Menu Presentation Contract** to `SKILL.md` and a matching header rule to the SC-GUIDE Deal Action Menus. Every action menu (Pick Your Path and all post-output menus) is now an instruction to surface options through the host's interactive question / choice mechanism so each option renders as a **clickable button**, not a numbered/bulleted Markdown list. A bounded plain-text list is now an explicit fallback only when the interactive mechanism is genuinely unavailable in the runtime. Closes the observed defect where the final menu rendered as a text list the SC had to type back.

**2. Glean transport degraded mode + Provenance Guard.** `references/data-sources.md` §1 previously defined a fallback only for *thin* Glean data (the `data[0]['text']` envelope → snippet path), but had **no defined behavior when the Glean search tool cannot be invoked at all** — so the skill failed *open*, improvising across Notion/Slack/Drive and presenting dealroom-inferred stage/ARR/MEDDPICC as canonical SFDC fact while reasoning past the router gate. Added: (a) a **Resolving and invoking the Glean tool** block (locate by capability, invoke with the SFDC app filter, retry once on empty discovery, don't drift); (b) a **Glean transport unavailable (degraded mode)** block — declare `SFDC record NOT resolved`, allow *tagged fallback* to other sources where every SFDC-origin field is tagged `[inferred – dealroom/Notion]` / `[assumed]` and never laundered into an SFDC label, offer the SC a paste-fields / retry recovery path, and keep running the router default flow; (c) a **Provenance Guard** forbidding bare canonical claims and gate-skipping on dealroom-inferred context; (d) a new Graceful-Degradation row for the unresolved-SFDC state. Glean-first for Salesforce remains intentional — no flaky Salesforce connector was added as a fallback.

**Router gate:** left as a soft guard (the Provenance Guard note + degraded-mode item 5) rather than a hard structural block, pending a future decision on making the gate fully structural.

**Anti-pattern count:** one bullet was folded into the existing "burying/omitting the Pick Your Path menu" anti-pattern (Markdown-list rendering named as the same defect) rather than adding a new standalone rule, keeping the net rule count flat.

### v1.3.1

Attribution & support pass. Adds first-class author metadata (author, title, handle, Slack contact, framework provenance) to the SKILL.md frontmatter; a one-line author credit in the SC-GUIDE Welcome; and a pull-based **Author & Support** route (triggered only when a user asks who built the skill or how to contact/give feedback). Consistent with the read-only, no-surprise invariant — contact info is never injected into normal deal output, and the skill never messages the author on the user's behalf.

### v1.3.0

Architecture patch addressing the error catalog and model-council synthesis. Fixes were sequenced as a build order (Waves 0–3) with critical-path dependencies preserved.

**Governing principles carried through the build**

- Gates were *specified but not enforced/surfaced* — fixed with two composable primitives (Visible Gate Block + Terminal Output Assertion), not a monolith.
- Read-only invariant is inviolate; confidence stays a 3-value model (verified | inferred | assumed).
- **Net rule count must go DOWN.** The two SKILL.md anti-pattern lists went from **68 → 66** (main 56 → 55, assigned-opp 12 → 11): rules that merely restated primitive-enforced checks were removed and replaced with single references to the primitives, with no loss of enforcement.

**Wave 0 — governance + defect fixes**

- Extracted `GOVERNANCE.md` (SC-Facing Output Rules, Outbound Messaging Pipeline, read-only Operating Boundaries) as the canonical, load-unconditionally source; added it to the Required References table.
- Fixed the CTA spec defect (P0): rewrote 6 CTA locations to be prospect-centric and split the Company + Business Understanding gate item 8 into 8a/8b.
- Data-source doc fixes: Glean `data[0]['text']` envelope as primary transport with snippet fallback; Gong indexing-degradation note; ordered Slack channel-search fallback chain.
- Added SFDC account cross-validation (email domain + Gong + notes identity check).

**Wave 1 — gate enforcement primitives**

- Added the **Visible Gate Block** primitive and the **Terminal Output Assertion** primitive.
- Wired the Visible Gate Block as a hard precondition for the Apollo AI Context Center payload and demo setup prompts (Feature C / Error 2.1, P0).
- Consolidation sweep: removed anti-pattern bullets now enforced by the primitives (net count 68 → 66).

**Wave 2 — output modes**

- Added cue-card density rules to the synthesis template (Error 3.1).
- Added the **Run Sheet** as a 5th output mode — a compressed, single-screen live-demo cue card derived from existing gate-passed content (Feature A / Error 3.2, P0).
- Added a **Canvas Content Sensitivity Filter** and minimal audience-tier tagging to canvas generation: each of the 14 canvas sections is tagged `team-facing` or `SC-only`; the default shared draft omits SC-only sections (Demo Flow, Landmines, Shadow Briefing); the SC can request the full version (Feature B / Error 5.2). Single-artifact filter — not a two-canvas system.

**Wave 3 — SC-GUIDE interaction layer**

- Visible Gate Block presentation before the Context Center payload on Apollo-AI / synthesis paths (pairs with Wave 1.2).
- Run Sheet trigger in the intent tree + Pick Your Path entry after a synthesis package exists (pairs with Wave 2.2).
- Canvas audience-tier choice (team-facing canvas default vs. full SC canvas) across the canvas menus (pairs with Wave 2.3).

**Deferred to v1.3.1 (not in this build):** `ROUTER.md` extraction, full Feature E, and errors 3.3 / 3.4 / 5.4.
