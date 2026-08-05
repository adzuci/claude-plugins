# Apollo AI Prompt Patterns

Use this reference when generating Part 3 of the Demo Synthesis Package or standalone Apollo AI prompts. The target user is an Apollo SC pasting prompts into Apollo's in-app AI Assistant, not a developer calling MCP tools.

> Internal terminology: "brief mode" and "synthesis mode" are architectural labels for the agent. Never surface these labels to the SC. Translate to plain language ("the brief", "the full synthesis package") in any user-visible output.

## Design Center

Default output is natural-language, paste-ready prompts for the Apollo AI Assistant panel in the Apollo app.

There are two prompt families:

| Prompt family | Purpose | Risk posture |
|---|---|---|
| Demo setup prompts | Configure a controlled demo experience using sample or demo-safe objects. | Moderate. Must review before confirming, but should generally avoid real buyer data. |
| Trial planning prompts | Help define trial scope, success criteria, dependencies, and risks before configuring anything. | Low-to-moderate. Planning only; no writes, enrichment, activation, enrollment, sending, or credit consumption. |
| Trial setup prompts | Help configure or guide the prospect's real evaluation environment using their ICP, target accounts, and success criteria. | Higher. Must default to preview/draft/disabled states and warn about data mutation, enrichment, activation, enrollment, sending, and credit consumption. |

Observed / expected Apollo AI surface as of May 2026 includes:

- Build your target audience
- Create signal-based sequence
- Analyze sequence performance
- Score accounts for fit
- People and company search
- Sequences, emails, calls, tasks
- Workflows
- Analytics
- Website visitors and forms
- Deals, meetings, and conversations

The prompt set should configure the demo experience around the best sales angle from the synthesis, not merely retrieve data.

Maintenance note: this surface inventory is based on direct observation and may change as Apollo AI ships new capabilities. Before generating prompts for a new deal or team rollout, verify the current Apollo AI Assistant capabilities in the live app. If Apollo AI cannot execute a requested action, move that setup step to Part 4 of the synthesis package as a manual UI instruction.

## Step 0: Apollo AI Context Center Payload (mandatory upstream of every prompt set)

**Hard precondition — Visible Gate Block first.** Before ANY field below is composed, the skill MUST have emitted the **Visible Gate Block** for the Company + Business Understanding Gate (defined in SKILL.md) and every criterion must pass. This is not an internal-only check — the SC must see the pass/fail block *before* the payload. If the gate blocks (any criterion fails or rests on `[assumed]` company facts), emit the Missing Business Context checklist instead and STOP; do not compose the payload. Criteria 1–7 and CTA-8a must be grounded in prospect / public / company sources; deal evidence calibrates only the demo objective (8b), never the company profile. The visible gate is mandatory upstream of the field-mapped payload, not merely a silent prerequisite.

Apollo AI's in-app Assistant interprets every prompt through the Apollo AI Context Center configured in **Apollo Settings → AI Context Center**. The Context Center is calibration, not deal context — it tells Apollo AI **who the prospect company is and how their business works**, so Apollo AI's interpretations are grounded in the prospect's offering, ICP, pains, value prop, and competitors rather than generic SaaS framing.

The observed Apollo AI Context Center UI groups editable fields under non-editable section headers (Overview, Key benefits & outcomes, Unique characteristics, Other details, Additional information). The Step 0 payload is a **field-mapped Apollo AI calibration payload** that maps directly onto the editable child fields under each section header, in this exact hierarchy:

- **Overview** *(section header — UI element only, not a paste target)*
  - Company domain *(editable)*
  - Company name *(editable)*
  - Offering *(editable)*
  - Customer profile *(editable)*
- **Key benefits & outcomes** *(section header — UI element only, not a paste target)*
  - Pain points *(editable)*
  - Value proposition *(editable)*
- **Unique characteristics** *(section header — UI element only, not a paste target)*
  - Advantage over competitors *(editable)*
  - Primary competitors *(editable)*
  - Social proof *(editable)*
- **Other details** *(section header — UI element only, not a paste target)*
  - CTA *(editable child field under Other details — not a top-level field, not a section header)*
- **Additional information** *(section — paste target only if the UI exposes a visible editable body field under it; otherwise treat as a section header only)*

Plus a clearly separated, smaller **Deal-specific calibration notes** section appended at the end (this meeting's strategic angle, AE commitments, do-not-say constraints, prompt interpretation instructions). The deal-specific block must never be the body of the payload; it is a calibration tail. It is **not** pasted into any global Context Center field, and is not forced into a UI field unless the SC confirms the UI exposes an editable Additional information / account-specific / demo-context field that can scope it. Otherwise it is provided to the SC as a separate note for them to keep outside the global Context Center.

Cancel and Save are page controls, not fields, and must never appear as field blocks in the payload.

**UI hierarchy note**: Do not paste body text into any non-editable section header (Overview, Key benefits & outcomes, Unique characteristics, Other details, Additional information). Paste only into the editable child fields under each header. Text dropped into a section header has no effect and corrupts the layout. CTA is the editable child field under Other details — render it there, never as a top-level field.

If the Context Center is configured from deal mechanics alone (deal pains, AE notes, Apollo's competitors), Apollo AI ends up calibrated against either an invented company profile or a generic SaaS template. Step 0 fixes this by grounding Apollo AI on the **actual prospect** before any prompt is interpreted.

### Mandatory upstream gate

Before producing any Step 0 payload, the skill must pass the **Company + Business Understanding Gate** (defined in `SKILL.md`). The gate requires source-grounded answers for: what the prospect company does, who they sell to, how they go to market, what pains *their* buyers have, their value prop and positioning, their competitors in their market, and their proof. If the gate fails, emit the Missing Business Context checklist instead of a payload. Never invent or backfill company facts.

### When to generate the Context Center payload

Always generate the Context Center payload first whenever this skill produces Apollo AI demo or trial setup prompts:

- Standalone Apollo AI prompts after a brief.
- Inside the synthesis package (Part 3 starts with the Context Center payload, then the prompts).
- After the Pick Your Path "Context Center payload + Apollo AI prompts" option is selected.
- Before any trial setup prompt set (see Trial section below for trial-specific framing).

The Context Center payload precedes Prompt 1 as **Step 0**. Never produce demo setup prompts without it.

### Read-only boundary for the Context Center

This skill **drafts** the Context Center payload as a copy-paste artifact for the SC. It does **not** update Apollo, the Context Center, or any Apollo object. The SC manually pastes the payload into Apollo Settings → AI Context Center.

### Placement-and-safety warning (must accompany every payload)

The Context Center may apply broadly to Apollo AI interactions across the SC's workspace. Mass-pasting account-specific confidential claims into the global Company information or Products & services profile risks contaminating the global company truth and leaking deal-specific framing into other AI sessions.

Surface this warning explicitly with each payload:

```text
Placement-and-safety warning:
- Apollo's AI Context Center may apply broadly to AI interactions in this workspace.
- Do NOT paste account-specific or confidential deal claims into the global Company information or global Products & services profile unless you also have an account-specific or session-level context area.
- **There is no per-account or per-session scoping inside an Apollo instance — corrected 2026-07-28.** Earlier versions of this warning ranked an "account-specific / session-level Demo context block" and a "deal-scoped Products & services card" as the preferred placements. Neither exists: every Context Center operation resolves to that team's single Global Context Center (one profile per team), and a product card is one of the prospect's own product/service lines, not a deal-scoped notes container. Recommending them pushed the SC toward options that aren't real.
- **Isolation comes from which instance you're in, not from a scoped block within one.** Two cases:
  1. **A per-prospect demo sub-account** (what `demo-instance-configuration` now provisions for each deal — one fresh sub-account per prospect). The instance itself *is* the isolation boundary, so the company-profile payload can be pasted into its Global Context Center directly. This is the normal case going forward.
  2. **A shared or multi-purpose instance.** The company-profile fields are still fine — they describe the prospect's public business. The risk is the **deal-specific calibration block** (buyer pains from a call, AE commitments, do-not-say constraints), which must stay out of global fields regardless. Keep it as a separate note for the SC, exactly as the Deal-specific calibration section already specifies — that is the real answer, not a scoped field to hunt for.
- If the SC is unsure which case they're in, ask before pasting.
- This skill does not write to the Context Center. You paste it manually after review.
- Confirm placement with the SC before any account-specific section is pasted into a global profile.
```

If Apollo's UI or workspace configuration is unknown for this deal, ask the SC to verify which Context Center surfaces are available before pasting account-specific content.

### Required Context Center payload fields (field-mapped to the Apollo UI)

The payload must be concise, source-grounded, and **primarily about the prospect company's business**. Use the Company + Business Understanding object built by the upstream gate, plus the brief's confidence tags and source labels — `[verified]`, `[inferred]`. `[assumed]` is not allowed in the company-profile fields; if that is all you have, omit the field and surface it in Missing Business Context.

Company-profile fields (paste-ready into the Apollo Context Center UI, organized under their observed section headers):

- **Overview** *(section header — UI element only, not a paste target)*
  - `domain` *(editable; UI label "Company domain")* — the prospect's primary domain (e.g. `acme.com`). Source: prospect website / SFDC.
  - `company_or_product_name` *(editable; UI label "Company name")* — legal/marketing name as the prospect uses it.
  - `company_overview` *(editable; UI label "Offering")* — what the company sells, in their own language. 1–3 sentences.
  - `customer_profile` *(editable; UI label "Customer profile")* — who the company sells to: ICP, industries, segments, geographies, buyer personas. 1–3 sentences or a short bullet list.
- **Key benefits & outcomes** *(section header — UI element only, not a paste target)*
  - `customer_pain_points` *(editable; UI label "Pain points")* — pains *the prospect's buyers* have, in the prospect's framing. 2–4 bullets.
  - `value_proposition` *(editable; UI label "Value proposition")* — the prospect's positioning / why customers buy from them. 1–3 sentences.
- **Unique characteristics** *(section header — UI element only, not a paste target)*
  - `product_differentiators` *(editable; UI label "Advantage over competitors")* — how the prospect frames their advantage in *their* market. 2–4 bullets. Not Apollo's advantage over Apollo competitors.
  - `primary_competitors` *(editable; UI label "Primary competitors")* — competitors in the prospect's market (alternatives their buyers consider). 2–6 bullets, only when source-backed. Omit if unknown.
  - `social_proof` *(editable; UI label "Social proof")* — verifiable named customers, case studies, metrics, awards. Only if directly attested by the company or a credible public source. Omit if unverifiable.
- **Other details** *(section header — UI element only, not a paste target)*
  - `call_to_action` *(editable child field under Other details; UI label "CTA")* — the prospect company's call-to-action to their own buyers: what the prospect asks their customers, leads, or prospects to do next in the prospect's own sales cycle. 1–2 sentences. This is a company-profile fact, NOT the Apollo demo objective — if it mentions Apollo, the demo, or the trial, move it to Deal-specific calibration notes. Render this under the Other details header — never as a top-level field and never as a section header.
- **Additional information** *(section — paste target only if the UI exposes a visible editable body field under it. If no such editable field is visible, treat it as a section header only and provide the deal-specific calibration as a separate note kept outside the global Context Center.)*

Each editable field carries a one-line annotation underneath the paste-ready text: `Source: [...] | Confidence: [verified|inferred]`. Section headers carry no annotation because they have no body. The Unique characteristics section is required as a section *with at least one source-backed editable child field* where grounding exists; section headers themselves are never paste targets.

Cancel / Save are page controls, never fields. Do not include them in the payload.

Deal-specific calibration (separate, smaller appended section — not the body):

- `deal_specific_calibration` — bundles:
  - `strategic_angle` — the highest-leverage Why Apollo for *this* deal, drawn from Part 1 of the synthesis or inferred from the brief.
  - `deal_buyer_pains` — top 2–3 deal-specific buyer pains from the brief, each tagged and sourced.
  - `prospect_product_card` — one specific product/service line from **the prospect's own business** (e.g., one item from their actual offering list), to represent as an Apollo Context Center product card. This is never an Apollo product, capability, or generic notes field — a real live dry run once produced a payload describing Apollo's own product instead of the prospect's, traced back to this field's old `apollo_`-prefixed name reading as "Apollo's card" rather than the prospect's. Include placement guidance (existing card to select vs. new card to propose creating vs. session-level note).
  - `hard_blockers_and_landmines` — CRM/email/security/migration blockers and AE commitments to preserve.
  - `buyer_language` — direct quotes from transcripts/notes when available, with source labels.
  - `do_not_say` — pricing/security/roadmap/compliance/performance/integration claims to avoid.
  - `prompt_interpretation_instructions` — explicit guidance for Apollo AI on interpreting subsequent prompts (optimize for the strategic angle, ground in the company profile above, avoid generic feature tour).

### Output template (field-mapped)

Render the payload as a Markdown block. Each field is its own paste-ready fenced block so the SC can copy field-by-field into the corresponding Apollo Context Center UI input. The Deal-specific calibration block is rendered last and labeled clearly.

````markdown
## Step 0: Update Apollo AI Context Center

**Where to paste**: Apollo Settings → AI Context Center → [Company information card or account-scoped Products & services card]. Paste each field below into the matching UI input.

**What this payload is**: an Apollo AI calibration payload about [Account Name]'s business (offering, customers, pains, value prop, competitors, proof, CTA), plus a separate deal-specific calibration block for *this* meeting. The company-profile fields condition Apollo AI's interpretation of every subsequent prompt; the deal-specific block tunes it for this demo.

**Source-grounding rule**: Every company-profile field below is sourced and confidence-tagged. No invented or `[assumed]` content has been added. If you see a field omitted, the underlying source was missing — see Missing Business Context.

**Placement guidance**: [this prospect's own demo sub-account, pasted into its Global Context Center | a shared instance, deal-specific block kept as a separate note]. See the placement-and-safety warning below — there is no account-scoped or session-level block inside an instance.

### Overview *(section header in the Apollo UI — do not paste body text into this header. Paste into the editable child fields below.)*

**Company domain** *(editable)*
```text
[domain]
```
Source: [...] | Confidence: [verified|inferred]

**Company name** *(editable)*
```text
[Company Name]
```
Source: [...] | Confidence: [verified|inferred]

**Offering** *(editable)*
```text
[1–3 sentence description of what the company sells, in the prospect's own language]
```
Source: [...] | Confidence: [verified|inferred]

**Customer profile** *(editable)*
```text
[Who they sell to: ICP, industries, segments, geographies, buyer personas. 1–3 sentences or a short bullet list, in the prospect's framing.]
```
Source: [...] | Confidence: [verified|inferred]

### Key benefits & outcomes *(section header in the Apollo UI — do not paste body text into this header. Paste into the editable child fields below.)*

**Pain points** *(editable)*
```text
- [Pain their buyers have, in the prospect's framing]
- [Pain their buyers have, in the prospect's framing]
- [Pain their buyers have, in the prospect's framing]
```
Source: [...] | Confidence: [verified|inferred]

**Value proposition** *(editable)*
```text
[1–3 sentence positioning statement in the prospect's words]
```
Source: [...] | Confidence: [verified|inferred]

### Unique characteristics *(section header in the Apollo UI — do not paste body text into this header. Paste into the editable child fields below.)*

**Advantage over competitors** *(editable)*
```text
- [How the prospect frames their advantage in their market]
- [How the prospect frames their advantage in their market]
```
Source: [...] | Confidence: [verified|inferred]

**Primary competitors** *(editable — omit if unknown, do not invent)*
```text
- [Named competitor in the prospect's market]
- [Named competitor in the prospect's market]
```
Source: [...] | Confidence: [verified|inferred]

**Social proof** *(editable — omit if unverifiable, do not invent)*
```text
- [Named customer, case study, or metric attested by the company or a credible public source]
```
Source: [...] | Confidence: [verified]

### Other details *(section header in the Apollo UI — do not paste body text into this header. Paste into the editable child field below.)*

**CTA** *(editable child field under Other details)*
```text
[1–2 sentences: the prospect company's call-to-action to their own buyers — what the prospect asks their customers, leads, or prospects to do next in the prospect's own sales cycle. NOT the Apollo demo objective; if it mentions Apollo/the demo/the trial, move it to Deal-specific calibration notes.]
```
Source: [...] | Confidence: [verified|inferred]

### Additional information *(section in the Apollo UI — paste here only if the UI exposes a visible editable body field under it. If no such editable field is visible, treat this as a section header only and place the Deal-specific calibration block below outside the global Context Center.)*

[If the UI exposes a visible editable Additional information body field, render the deal-specific calibration block here, scoped to this account/session. Otherwise leave this section header empty and keep the deal-specific block as a separate note for the SC to retain outside the global Context Center.]

### Deal-specific calibration notes (separate section — keep outside the global Context Center unless a visible editable Additional information / account-specific / demo-context field exists. Paste into an account-scoped card, session-level context, or a clearly labeled "Demo context" note kept separate from the global Context Center.)

```text
Deal-specific calibration for [Account Name] — [meeting type, e.g. demo / technical evaluation / trial setup]

Strategic angle (Why Apollo for this deal): [primary differentiator tied to verified pain]

Top deal-specific buyer pains (from the brief, not generic):
1. [pain] — Confidence: [verified|inferred]. Source: [source].
2. [pain] — Confidence: [...]. Source: [...].
3. [pain] — Confidence: [...]. Source: [...].

Prospect product/service line to represent as a Context Center product card: [one specific product or service from the prospect's own offering — never an Apollo product]. Placement: [existing card to select | new card to propose creating | session-level note].

Hard blockers / landmines:
- [blocker]: [why this constrains the demo].
- AE commitments to preserve: [pricing | security posture | roadmap | timeline | functionality].

Buyer language (use these phrases, do not paraphrase away):
- "[direct quote]" — Source: [transcript / notes].
- "[direct quote]" — Source: [...].

Do not say / do not promise:
- [claim or promise to avoid].
- [claim or promise to avoid].

Prompt interpretation instructions for Apollo AI:
- Treat the company-profile fields above as the canonical truth about [Account Name].
- Optimize every output for the strategic angle above.
- Ground all examples in [Account]'s actual buyer pains, not generic SaaS framing.
- Avoid feature-tour outputs. Prefer narrow, deal-specific configurations.
- Treat the buyer language above as the canonical phrasing.
- Treat the do-not-say list as hard constraints.
```

### Placement-and-safety warning

[Insert the placement-and-safety warning block from this reference. Confirm with the SC before pasting any account-specific or deal-specific section into a global Company information or Products & services profile.]
````

### Validation checklist (run before emitting any prompt)

Before producing Prompt 1, verify the just-rendered payload satisfies all of:

- [ ] The **Visible Gate Block** for the Company + Business Understanding Gate was emitted to the SC *before* this payload, and every gate criterion passed. If the gate blocked, no payload should exist — the Missing Business Context checklist should have been shown instead.
- [ ] Payload renders the observed UI hierarchy: Overview → Key benefits & outcomes → Unique characteristics → Other details, with Additional information used as a paste target only if the UI exposes a visible editable body field under it.
- [ ] No section header (Overview, Key benefits & outcomes, Unique characteristics, Other details, Additional information) contains body text — they are headers only.
- [ ] Cancel and Save are not present as fields.
- [ ] Company domain and Company name (under Overview) are present and verified.
- [ ] Offering (under Overview) is in the prospect's own language and source-backed.
- [ ] Customer profile (under Overview) describes the prospect's customers, not Apollo's.
- [ ] Pain points (under Key benefits & outcomes) describe pains the prospect's buyers have, not Apollo's pitch.
- [ ] Value proposition (under Key benefits & outcomes) is the prospect's positioning, not generic SaaS language.
- [ ] Advantage over competitors (under Unique characteristics) reflects the prospect's framing in their market.
- [ ] Primary competitors (under Unique characteristics) are competitors in the prospect's market, not Apollo battlecard competitors.
- [ ] Social proof (under Unique characteristics) is omitted unless verifiable.
- [ ] CTA describes the prospect's call-to-action to their own buyers, not the Apollo SC's demo objective. If the CTA mentions Apollo, the demo, or the trial, move that content to Deal-specific calibration notes. CTA is rendered as the editable child field under Other details (not as a top-level field).
- [ ] Every company-profile field has a source and confidence tag, with no `[assumed]` content.
- [ ] Deal-specific calibration is in its own clearly labeled block kept outside the global Context Center, unless a visible editable Additional information / account-specific / demo-context field exists and the SC has confirmed scoping.

If any item fails, do not emit prompts. Either revise the payload, run more research, or fall back to the Missing Business Context checklist.

### Trial-specific Context Center payload variant

When generating trial setup prompts, the company-profile fields above are unchanged — Apollo AI still needs to be calibrated on the prospect's actual business. In the Deal-specific calibration block, swap `strategic_angle` framing for `evaluation_goal` and add `success_criteria`, `evaluation_owner`, `target_users`, and `do_not_activate` (workflows, sequences, enrichment, enrollment, sending, credit-consuming actions). The CTA field becomes the trial CTA (what the prospect should validate or decide by end of trial). The placement-and-safety warning still applies and is more important for trial scope, since trial calibration often includes confidential evaluator names, internal goals, and procurement language.

### Hard rules for the Context Center payload

1. The Company + Business Understanding Gate must pass before any payload is rendered. If it fails, emit the Missing Business Context checklist instead.
1. The payload precedes Prompt 1 as Step 0. Never generate prompts without it.
1. The payload is **primarily about the prospect company's business**, mapped to the observed Apollo Context Center UI hierarchy: **Overview** (Company domain, Company name, Offering, Customer profile), **Key benefits & outcomes** (Pain points, Value proposition), **Unique characteristics** (Advantage over competitors, Primary competitors, Social proof), **Other details** (CTA), and **Additional information** (paste target only when the UI exposes a visible editable body field under it). Section headers are UI elements only — never paste targets. CTA is the editable child field under Other details, not a top-level field. Cancel / Save are page controls, never fields. Deal-specific calibration is a separate, smaller appended section that is **not** forced into any global UI field; it is kept outside the global Context Center unless a visible editable Additional information / account-specific / demo-context field exists.
1. Never invent or backfill company facts. No fictional offering, ICP, persona, competitor, customer, metric, case study, or proof point. No unrelated example company. No Apollo battlecard competitors masquerading as the prospect's market competitors. No generic SaaS pain language standing in for the prospect's real buyer pains.
1. Every company-profile field carries a source label and confidence tag (`[verified]` or `[inferred]`). `[assumed]` content is not allowed in the company-profile fields; omit the field and surface the gap in Missing Business Context instead.
1. Run the Validation Checklist before emitting any prompt. If any item fails, do not emit prompts.
1. Surface the placement-and-safety warning with every payload; do not omit it for brevity.
1. Do not present this skill as updating Apollo AI or the Context Center. The SC pastes it manually.
1. If only the global Apollo company/product profile is available and no account-scoped or session-level surface exists, ask the SC where to place the payload before generating it; if pressed for output, generate a minimal, generic version and flag in the warning that the deal-specific block has been withheld pending placement confirmation.
1. The prompts that follow must explicitly reference the Context Center: each prompt's "Why this works" should note that Apollo AI is now anchored to the Step 0 company-and-deal calibration, and the "How to use" section must instruct the SC to update the Context Center before pasting Prompt 1.

## Read-Only Boundary

This skill may generate prompts that the SC can paste into Apollo AI. It must not execute those prompts. Prompts that may create or modify records, sequences, workflows, lists, scoring, enrichment, or enrollments must include a review/confirmation note.

Use this pattern:

`Review Apollo AI's proposed changes before confirming. Do not activate, enroll, or send anything until the SC has reviewed the setup.`

For trial prompts, use the stronger pattern:

`Review Apollo AI's proposed changes before confirming. Keep everything in preview, draft, sample, or disabled mode unless the SC explicitly decides to activate it. Do not enroll real contacts, send emails, enrich records, trigger workflows, or consume credits without confirming scope and success criteria.`

## MCP and Programmatic Schema Rule

Do not make MCP JSON/tool schemas the primary output for SCs. Only include programmatic schemas when the user explicitly asks for MCP or API execution.

If MCP details are requested:

1. Inspect the live Apollo connector or MCP tool schema in the execution environment.
1. Use exact tool names and parameter names returned by that schema.
1. If the schema cannot be inspected, label examples as `schema pattern — verify live connector before execution`.
1. Warn before credit-consuming or data-mutating actions.

## Prompt Set Structure

Generate only prompts relevant to the deal. Scale prompt count to evidence quality; do not pad with assumed-confidence setup prompts to reach a target count.

- Deals with 1-2 verified pains: generate 3-4 prompts plus the dry-run/readiness prompt.
- Deals with 3+ verified pains and a clear strategic angle: generate 5-8 prompts plus the dry-run/readiness prompt when setup creates multiple objects.
- Sparse deals: prioritize one setup prompt for the highest-confidence demo flow item, one validation/setup prompt, and the dry-run prompt.

A rich synthesis package usually draws from these prompt categories:

1. Target audience / ICP list setup.
1. Sequence setup aligned to the primary pain.
1. Workflow setup aligned to the primary automation use case.
1. Account scoring or fit analysis.
1. Stakeholder / multithreading search.
1. Analytics or reporting view.
1. Dry-run / readiness check.

If the deal's primary use case is not prospecting, put audience/data prompts after the core workflow or sequence prompts and label them as secondary.

If Apollo AI prompts are requested without a full synthesis package, first attempt to infer a lightweight strategic angle from the brief (top-ranked verified pain → Apollo capability → "why Apollo here"). If a coherent angle emerges, order prompts from that angle. If not, fall back to the Recommended Demo Flow evidence ranking: highest-ranked verified item first, then inferred needs, then standard additions.

Trial prompt sets should be shorter than demo prompt sets unless the trial scope is fully defined. If trial success criteria are unknown, generate trial planning prompts first and defer the full setup prompt set.

## Prompt Template

For each prompt, use this structure:

````markdown
### Prompt [N]: [Outcome-oriented title]

**Purpose**: [what this prepares and why it matters for this deal]

**Paste into Apollo AI**:
```text
[natural-language prompt]
````

**Why this works**: [tie to a verified pain, stakeholder priority, or strategic angle]

**Demo talk-track hook**: "[one sentence the SC can say while showing it]"

**Review before confirming**: [what the SC should inspect before accepting Apollo AI's proposed action]

````

## Prompt Categories

### Build Target Audience

Use when the demo should show Apollo finding the buyer's ICP or replacing a data provider.

```text
Build me a list of people at [target company type] in [region] with [employee range] employees. I want titles like [titles]. Only show people with verified emails. Save this as a list called "[Account] Demo - [ICP Name]".
````

Review before confirming:

- Geography and employee filters.
- Titles and seniority.
- Verified email requirement.
- Whether the list should be saved or only previewed.

### Create Signal-Based Sequence

Use when the demo includes automated messaging, stage-based follow-up, signal-triggered outreach, or sequence consolidation.

```text
Create a signal-based sequence called "[Account] Demo - [Sequence Name]" with [number] steps:

Step 1: [trigger/context and message goal]. Subject: "[subject]". Keep it under [word count] words.

Step 2: Wait [time period]. If [condition], send [message goal]. Subject: "[subject]".

Step 3: Wait [time period]. If [condition], send [message goal]. Subject: "[subject]".

Use a [tone] tone. Do not activate or enroll anyone until I review it.
```

Review before confirming:

- Sequence name.
- Step timing.
- Tone and content.
- Activation/enrollment status.
- Sender identity.

### Build Workflow

Use when the primary demo angle is automation, routing, stage triggers, activity suppression, branching, enrichment, or operational scale.

```text
Create a workflow called "[Account] Demo - [Workflow Name]" that triggers when [trigger event].

The workflow should:
1. Check whether [condition].
2. If [condition true], [action].
3. If [condition false], [action].
4. Add a branch for [segment/persona/status] where [branch behavior].

Do not turn the workflow on until I review the logic.
```

Review before confirming:

- Trigger source and trigger event.
- Branching logic.
- Suppression or exclusion rules.
- Whether the workflow is active or draft.
- Any unsupported capability that Apollo AI cannot configure.

### Score Account for Fit

Use when the demo should show account intelligence, fit scoring, intent, or AI insight.

```text
Score [Account Name] ([domain]) for fit with [our/my] ideal customer profile. Show company details, employee count, industry, technologies, buying signals, and reasons this account is or is not a strong fit.
```

Review before confirming:

- Whether the score is based on actual data or inferred signals.
- Any missing data fields.
- Whether enrichment or credits are required.

### Find Additional Stakeholders

Use when the buyer cares about multithreading, contact discovery, ZoomInfo replacement, or stakeholder coverage.

```text
Find people at [Account Name] with titles related to [functions/titles]. Show their titles, seniority, location, and email status. Prioritize people who would influence [use case or buying committee].
```

Review before confirming:

- Whether results are the prospect's own employees or target-market prospects.
- Email verification status.
- Whether to save, add, enrich, or simply preview.

### Analyze Sequence Performance

Use when reporting, rep productivity, engagement visibility, or manager inspection matters.

```text
Analyze the performance of my active sequences. Show metrics by sequence: emails sent, delivered, opened, replied, meetings booked, and bounce rate. Also show rep-level engagement if available.
```

Review before confirming:

- Date range.
- Whether demo data is representative.
- Whether real customer or internal performance data should be hidden during customer-facing demos.

### Dry Run / Readiness Check

Always include this in the full synthesis package when prompts create or configure multiple demo objects.

```text
Show me a readiness summary for this demo:
1. [List name] — does it exist and how many people are in it?
2. [Sequence name] — does it exist, how many steps, and is it active or draft?
3. [Workflow name] — does it exist, what is the trigger, and is it enabled or draft?
4. Linked email accounts — which mailbox would send demo emails?
5. Anything missing or risky before I show this to a customer?
```

Review before confirming:

- Nothing is active unless intended.
- No real customer/prospect is enrolled.
- Email sender is safe.
- Workflow does not trigger unintentionally.

## Trial Planning and Setup Prompt Patterns

Use this section when the SC asks to set up a trial, POC, pilot, evaluation environment, live validation, or buyer-facing proof motion.

Trial prompts are not just demo prompts with the word "trial" substituted. They must reflect the prospect's real evaluation goal and include stronger safety boundaries.

Trial planning prompts are safe first-step prompts for unclear evaluations. Trial setup prompts are higher-stakes prompts for configuring or proposing Apollo objects after scope is clear.

### Trial Preconditions

Before generating a full trial prompt set, check whether the brief contains:

- Verified or strongly inferred pain points.
- Decision criteria or success criteria.
- Primary use case.
- Known trial owner or evaluator.
- Data sources, target accounts, or ICP definition.
- Technical landmines that could break the evaluation.

If success criteria are missing, start with this trial planning prompt instead of generating setup prompts:

```text
Help me define trial success criteria for [Account Name] based on this evaluation goal: [known goal or pain].

Return:
1. The 3-5 outcomes the prospect should validate during the trial
2. The Apollo objects or workflows needed to test each outcome
3. The data, integrations, or permissions required
4. Risks or unknowns we should resolve before configuring anything

Do not create, enrich, enroll, activate, or send anything. This is planning only.
```

Review before confirming:

- Whether the output defines measurable success criteria.
- Whether the evaluation owner and target users are known.
- Whether setup dependencies are missing.
- Whether the trial is ready for configuration or still needs AE/SC alignment.

### Import or Build Trial ICP

Use when the trial needs a target audience, ICP list, or sample account/contact universe.

```text
Create a trial audience plan for [Account Name] based on their ICP:
- Target company type: [company type]
- Region: [region]
- Employee range: [range]
- Target personas/titles: [titles]
- Exclusions: [competitors, customers, current open opportunities, suppressed domains]

First show me the proposed filters and estimated audience size. Do not save the list, enrich records, or add contacts until I review the filters.
```

Review before confirming:

- Whether the audience represents the prospect's real ICP.
- Exclusion rules and suppression lists.
- Whether Apollo AI is previewing only or saving a list.
- Whether any enrichment or credits are required.

### Enrich a Trial Sample

Use when enrichment quality, data coverage, waterfall enrichment, or data replacement is a decision criterion.

```text
Prepare a trial enrichment plan for [Account Name].

Using up to [sample size] records from [source/list name], show me a preview only:
1. Current fields available
2. Fields Apollo can enrich
3. Expected match/coverage rate without actually enriching
4. Records that should be excluded from testing
5. Estimated credit cost if I were to run enrichment

Do not enrich any records, do not consume credits, and do not save changes until I explicitly confirm. This is a planning preview, not an enrichment run.
```

Review before confirming:

- Sample size.
- Fields to enrich.
- Whether this uses real prospect/customer data.
- Credit consumption.
- Export or data-sharing expectations.

### Build Trial Sequence Draft

Use when the buyer wants to validate outbound messaging, sequencing, rep productivity, or stage-based follow-up.

```text
Draft a trial sequence for [Account Name]'s [use case] motion.

Goal: [trial success criterion]
Audience: [persona or list]
Steps: [number of steps]
Tone: [tone]
Constraints: [compliance, brand, timing, opt-out, region]

Create the sequence in draft mode only. Do not activate it and do not enroll any contacts. Show me the draft copy, timing, sender settings, and any risks before I confirm.
```

Review before confirming:

- Copy and tone.
- Sender identity.
- Regional/compliance constraints.
- Whether the sequence is draft only.
- Enrollment status.

### Configure Trial Workflow Draft

Use when the buyer needs to validate workflow automation, stage-triggered actions, routing, enrichment, suppression, or handoff logic.

```text
Draft a trial workflow for [Account Name] that validates this use case: [use case].

Trigger: [trigger]
Conditions: [conditions]
Branches: [branches]
Suppression rules: [suppression rules]
Output/action: [action]

Keep the workflow disabled. Show me the full trigger logic, branch logic, affected records, and activation risks before anything is turned on.
```

Review before confirming:

- Trigger source.
- Affected records.
- Branch and suppression logic.
- Whether workflow is disabled.
- Risk of accidental enrollment, enrichment, notifications, or CRM sync.

### Configure Scoring or Signals for Trial

Use when the evaluation depends on account prioritization, intent, fit scoring, buying signals, or territory focus.

```text
Create a trial scoring plan for [Account Name].

Score accounts based on:
- Fit criteria: [criteria]
- Intent or signal criteria: [signals]
- Exclusions: [exclusions]
- Priority segments: [segments]

Show me the scoring model and example scored accounts before saving or applying it broadly.
```

Review before confirming:

- Criteria match the buyer's stated decision criteria.
- Scores are explainable.
- No broad data mutation occurs without confirmation.
- Any signal sources are understood and not overclaimed.

### Trial Readiness Check

Always include this when trial prompts configure multiple objects or touch real data.

```text
Run a trial readiness check for [Account Name].

Show:
1. Trial success criteria and whether each is testable
2. Lists/audiences created or proposed
3. Sequences created and whether they are draft or active
4. Workflows created and whether they are disabled or enabled
5. Enrichment actions proposed or completed, including credit impact
6. Email accounts, sender settings, suppression rules, and enrollment status
7. Any risks before the prospect uses the trial environment

Do not activate, enroll, send, enrich, or sync anything as part of this check.
```

Review before confirming:

- Everything remains draft, disabled, preview, or sample-only unless intentionally activated.
- Real contacts are not enrolled unintentionally.
- Credits are not consumed unexpectedly.
- Trial success criteria are clear enough to judge the evaluation.

## Prompt Generation Rules

- Always pass the Company + Business Understanding Gate, then produce the Step 0 Apollo AI Context Center calibration payload first. Prompts are downstream of the Context Center and are never emitted without it. If the gate or the validation checklist fails, emit the Missing Business Context checklist and stop.
- Each prompt's "Why this works" should note that Apollo AI is anchored to the Step 0 company-and-deal calibration (the prospect's offering, customer profile, pains, value prop, competitors, plus the deal-specific strategic angle and do-not-say constraints).
- Lead with the highest-leverage sales angle. If the deal is about workflow automation, prompt order starts with workflow/sequence setup, not data search.
- If the full synthesis package is active, take the highest-leverage sales angle from Part 1. If only the seven-section brief exists, first infer a lightweight strategic angle when possible; otherwise use the Recommended Demo Flow evidence ranking.
- Tie every prompt to a verified pain point, decision criterion, stakeholder priority, or recommended demo flow item.
- Include "Why this works" so the SC understands why the prompt exists.
- Include a talk-track hook for customer-facing demo moments.
- Keep prompts concrete enough that Apollo AI can produce usable artifacts.
- Add safety language to prompts that could activate workflows, enroll contacts, send emails, enrich data, or consume credits.
- If Apollo AI may not support a requested setup, say so and provide a manual UI walkthrough in Part 4 rather than pretending the prompt can do it.
- Scale prompt count to evidence quality; fewer grounded prompts are better than a complete-looking but assumption-heavy setup plan.
- For trial prompts, lead with success criteria and safety. When evaluation scope is unknown, generate trial planning prompts rather than broad setup prompts.
- Trial prompts must default to preview, draft, sample, or disabled states.
- The "How to use these prompts" walkthrough must instruct the SC to update the Apollo AI Context Center (Step 0) before pasting Prompt 1, and to confirm placement (account-specific/session-level vs. global) before pasting any account-specific block.
