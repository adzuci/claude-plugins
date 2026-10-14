---
name: copywriter
description: Draft in-product copy for feature gates, paywalls, and upgrade prompts, with character counts, ranked alternatives, a persuasion score, and a legal risk assessment.
disable-model-invocation: true
requires_config: true
---

# In-Product Copywriter

Draft guidelines-compliant in-product copy for feature gates, paywalls, and upgrade prompts. Every draft includes character counts, alternatives, an adversarial review, and a legal risk assessment.

Usage: `/apollo-growth-product:copywriter [surface-slug] [feature context] [--plainspoken]`

Surface guidelines and references ship with this skill in `surfaces/` and `references/`. They work out of the box. Swap them for your team's equivalents if your surfaces or style rules differ.

## Configuration

Before doing anything else, read `config.md` from this skill's directory. It contains a YAML frontmatter block of variables this skill depends on.

For every `{{placeholder}}` you encounter while running this skill, substitute the matching value from `config.md`'s frontmatter.

`config.md` ships with the skill, so treat it as **defaults and documentation, read-only**. A plugin update replaces it.

Your own answers live in `~/.claude/plugin-config/apollo-growth-product/copywriter.md`. Read that file first when it exists and let it override the shipped values, remembering that a saved empty string is a deliberate answer, not a missing one.

If a value is still `<UNSET>` after that merge, ask the user for it, then write the answer to `~/.claude/plugin-config/apollo-growth-product/copywriter.md` (creating the directory if needed). Never write answers back into the skill's own `config.md`; they'd be wiped on the next plugin update. Do this once per session.

## Workflow

Execute these steps **in order**.

### Step 1: Parse arguments and select the surface

Check the arguments for **"Be plainspoken"** or `--plainspoken` (case-insensitive). If found, set `plainspoken = true` and strip it from the arguments before further parsing. Otherwise `plainspoken = false`.

Check the remaining arguments for a surface slug and optional feature context.

**If a surface slug is provided** and it matches a filename in `surfaces/` without the `.md` extension, load that surface file.

**If no surface slug is provided or it isn't recognized**, glob `surfaces/*.md`, read each file's first line to get the surface name, and present the options:

> "Which surface type is this copy for?"
>
> 1. `modal-standard` — Modal / Standard (limit reached, plan upgrade)
> 1. `modal-content-driven` — Modal / Content-driven (workflow moments, benefit bullets)
> 1. `modal-transactional` — Modal / Transactional (credit purchase, order summary)
> 1. `paywall-standard` — Paywall / Standard (full-page, feature access)
> 1. `drawer-extension` — Drawer [PROVISIONAL]
> 1. `inline-standard` — Inline / Standard [PROVISIONAL]

Wait for the user to pick one.

### Step 2: Load references

Always read these files before drafting:

1. `references/legal-guidelines.md`
1. `references/copy-style.md`
1. The selected surface file from `surfaces/{slug}.md`
1. `references/persuasion-rules.md` — **skip this file if `plainspoken = true`**

### Step 3: Gather context

Ask for anything not already provided. You need:

- **Feature or limit:** what feature is gated, or what limit was hit?
- **Unlock path:** what plan or add-on unlocks this?
- **Audience:** who sees this? (free users, a specific plan tier, all non-enterprise)
- **PII visibility:** is personal identifying information (full name, email, phone) visible on screen when this appears?
- **Differentiator:** what makes this feature or offer different from competitors? (optional, fuels the "nobody else can say this" rule, skip if `plainspoken = true`)
- **Specific numbers:** any metrics, counts, or timeframes that make claims concrete (optional, skip if `plainspoken = true`)
- **Additional context:** links to Figma, Jira, Slack threads, or other background (optional)

If `plainspoken = false`, frame the differentiator and specific-numbers ask as: "These help me write more persuasive copy. If you don't have them, I'll draft without and note the gaps."

Present this as a single grouped ask. Only ask for what's missing.

### Step 4: Draft copy

Using the surface file's **Component Anatomy** table, produce copy for every required component:

1. **Match the component anatomy exactly.** Include every required component.
1. **Respect character limits.** Count characters for each component. Revise anything over the limit before presenting.
1. **Apply style rules** from `references/copy-style.md`.
1. **Apply tone** from the surface file's Tone section.
1. **Follow CTA patterns** from the surface file. Use the exact CTA templates unless legal risk requires informational alternatives.
1. **Provide 2-3 alternatives** for the Header and Primary CTA, each with a character count and brief rationale.
1. **Persuasion pass** (skip if `plainspoken = true`). Run the full persuasion quality score against all 11 rules. Revise any component that scores Fail. Note Partial scores with gaps.

This produces your **candidate set**: a champion plus 2-3 alternatives for Header and Primary CTA, and a single candidate for every other component. Don't finalize champions yet. Step 5 stress-tests them first.

### Step 5: Adversarial validation and refinement

Spawn a **single adversarial subagent** to attack the candidate set, grade every variant, and recommend the champion per component. Its job is to be the harshest reader this copy will ever meet. **Never skip this step**, even in `plainspoken` mode.

**What to pass the subagent** (inline in the prompt, it has no access to this conversation):

- The **full candidate set**: every component, all variants, character counts
- The **context** from Step 3, noting anything that was missing
- The **surface guidelines verbatim**: component anatomy, character limits, tone, CTA patterns
- The **style rules** from `references/copy-style.md` and the **persuasion rules** from `references/persuasion-rules.md` (omit persuasion rules if `plainspoken = true`)
- The **mode**: persuasion-graded, or plainspoken (clarity/style/char-limit only)

**Instruct the subagent** with this brief:

> You are an adversarial copy critic for in-product monetization copy. Assume each variant is weaker than it looks and your job is to prove it. For every component variant:
>
> 1. **Attack it.** Name every concrete weakness: vague or abstract phrasing, weak verbs, generic claims any competitor could make, hedging, fluff, character-limit violations, style-rule violations (sentence case, no period in header, active voice), and tone mismatch with the surface.
> 1. **Grade it** on a 0-100 scale against the rubric for this mode. In persuasion mode, score against the 11 persuasion rules plus style and character-limit compliance. In plainspoken mode, score on clarity, style compliance, and character limits only. A character-limit or hard style violation caps the score at 40.
> 1. **Pick the champion** for each component, the highest-scoring variant. If the strongest variant still scores below 80, **write a refined version yourself** that fixes the weaknesses you named, and explain the fix.
>
> Return structured output: per component, a ranked table of variants with score and one-line critique, the recommended champion (existing or your refinement), and any character counts you changed. Be specific and unsparing, don't rubber-stamp.

**After the subagent returns:**

1. **Finalize the champion** per component using its grading. The highest-scoring variant goes in the Component Copy table, the rest become listed alternatives ordered by score.
1. **Adopt refinements** where the original variants scored below 80, then **re-count characters** on anything changed and confirm every limit still holds. If a refinement now exceeds a limit, trim it and re-verify.
1. **Keep the grading** to surface in the Adversarial Review section.
1. If the subagent flags a hard violation you can't reconcile, fix it directly rather than presenting broken copy.

Don't show the user the raw subagent transcript. Synthesize its findings into the finalized draft.

### Step 6: Legal risk assessment

Score the draft using the 3-factor test from `references/legal-guidelines.md`:

| Factor | Question | Answer |
|--------|----------|--------|
| PII visible | Is PII visible on screen behind or around this component? | Yes / No |
| Transactional language | Does the copy use transactional language (buy, purchase, upgrade, pricing)? | Yes / No |
| Free users | Is this shown to free users? | Yes / No |

**Scoring:** Low risk = 0-1 factors Yes. Medium = 2 factors Yes. High = all 3 Yes.

**If Medium or High risk:**

- Recommend specific mitigations from the legal guidelines (blurred background, step separation, informational CTAs)
- Provide an alternative lower-risk version of the copy with informational language
- If High risk, explicitly recommend legal review via {{legal_review_channels}}

### Step 7: Present the draft for review

Present the complete draft using the **Output Format** below, including the Adversarial Review section. Ask:

> "Here's the draft. The champions below survived an adversarial review pass. Would you like to adjust any copy, swap in an alternative, or change the legal mitigations before I save it?"

Make any requested changes. Re-check character limits after edits.

### Step 8: Save the draft

Write the final draft to `{{copy_output_dir}}/{feature-slug}-{surface-slug}-{YYYY-MM-DD}.md`. Derive the feature slug from the feature name (lowercase, hyphens). Confirm the saved path.

## Output format

Every draft **must** follow this structure:

```markdown
## Copy Draft: [Feature] — [Surface Type]

**Date:** [YYYY-MM-DD]
**Surface:** [surface slug]
**Audience:** [who sees this]
**Unlocked by:** [plan or add-on]

### Component Copy

| Component | Copy | Chars | Limit |
|-----------|------|-------|-------|
| Header | [header text] | [n] | [limit] |
| Description | [description text] | [n] | [limit] |
| Primary CTA | [cta text] | [n] | [limit] |

### Alternatives

**Header options:**
1. [Primary choice, already in table] ([n] chars) — [rationale]
2. [Alternative] ([n] chars) — [rationale]

**Primary CTA options:**
1. [Primary choice, already in table] ([n] chars) — [rationale]
2. [Alternative] ([n] chars) — [rationale]

### Persuasion Check

<!-- If plainspoken = true, replace the table with:
> Persuasion rules skipped (plainspoken mode)
-->

| # | Rule | Header | Description | CTA |
|---|------|--------|-------------|-----|
| 1 | Three-Question Test | ✓/△/✗ | ✓/△/✗ | — |
| 2 | Concrete over Abstract | ✓/△/✗ | ✓/△/✗ | ✓/△/✗ |
| 3 | 1-Mississippi Test | ✓/△/✗ | ✓/△/✗ | ✓/△/✗ |
| 4 | Point, Don't Talk | ✓/△/✗ | ✓/△/✗ | ✓/△/✗ |
| 5 | Falsifiable Claims | ✓/△/✗ | ✓/△/✗ | ✓/△/✗ |
| 6 | Nobody Else Can Say This | ✓/△/✗ | ✓/△/✗ | ✓/△/✗ |
| 7 | Kaplan's Law | ✓/△/✗ | ✓/△/✗ | ✓/△/✗ |
| 8 | Conflict Creates Interest | ✓/△/✗ | ✓/△/✗ | ✓/△/✗ |
| 9 | Reader First | ✓/△/✗ | ✓/△/✗ | ✓/△/✗ |
| 10 | Reassure | ✓/△/✗ | ✓/△/✗ | ✓/△/✗ |
| 11 | Sound Human | ✓/△/✗ | ✓/△/✗ | ✓/△/✗ |

✓ = Pass, △ = Partial (missing context), ✗ = Fail

**Quality Score: X / 11**

**Gaps:** [missing context that would improve partial scores, or "None"]

### Adversarial Review

| Component | Champion (final) | Critic score | Why it won / what changed |
|-----------|------------------|--------------|----------------------------|
| Header | [final champion text] | [n]/100 | [winning variant, or "refined: [what the critic fixed]"] |

**Refinements adopted:** [components where the critic's rewrite replaced the original drafts, with
a one-line reason, or "None — original drafts won on merit."]

### Legal Risk Assessment

| Factor | Value | Risk |
|--------|-------|------|
| PII visible | [Yes/No] | [Low/Medium/High] |
| Transactional language | [Yes/No] | [Low/Medium/High] |
| Free users | [Yes/No] | [Low/Medium/High] |
| **Overall** | **[Low/Medium/High]** | — |

**Recommendation:** [Specific mitigations if needed, or "No additional mitigations required."]

### Guidelines Compliance

- [x/fail] Sentence case
- [x/fail] No period in header
- [x/fail] Active voice
- [x/fail] Character limits met
- [x/fail] Tone matches surface guidelines
- [x/fail] CTA matches approved pattern
- [x/fail] Champions cleared adversarial review (Step 5)
- [x/fail] Legal mitigations applied (if applicable)
```

Each ✗ gets a parenthetical note (e.g. `✗ (header is abstract, no visual object)`). Each △ gets one too (e.g. `△ (no differentiator provided)`).

## Bundled references

- `references/legal-guidelines.md` — the 3-factor risk test, mitigations, and review triggers. Marked attorney-client privileged, treat as internal.
- `references/copy-style.md` — sentence case, voice, punctuation, and formatting rules.
- `references/persuasion-rules.md` — the 11 persuasion rules and how to score against them.
- `surfaces/*.md` — one file per surface type, each with component anatomy, character limits, tone, and approved CTA patterns.

Replace any of these with your team's equivalents. The skill reads whatever is in those paths.

## Safety rules

- **Never fabricate features or plan details.** Only use information the user provides.
- **Always run the adversarial validation pass** (Step 5) before finalizing champions. Never skip it, even in plainspoken mode or for obvious copy. The champion in the final draft must be the one the critic graded highest, or its refinement.
- **Never show the raw subagent transcript.** Synthesize its grading into the Adversarial Review section.
- **Always show the draft** before saving.
- **Always run the legal risk assessment.** Never skip it, even for obvious low-risk cases.
- **Flag provisional surfaces.** If a surface file is marked provisional, note that its guidelines aren't final and recommend confirming with the design team.
- **Re-count characters after every edit.** A single character over is a fail.
- **When in doubt on legal risk, recommend review.** Safer to flag than to miss.
