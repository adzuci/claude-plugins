# Output Contract

Exact format rules for the PRD One-Pager Skill. These are enforced throughout drafting and revision.

______________________________________________________________________

## First draft format

The first draft response has six parts, in this order:

### A. Framing note

One or two sentences. Personable, direct. Acknowledges this is a fuller first pass and explains what to do with it.

Style guide:

- Useful, not apologetic.
- Do not say "I am bad at page count."
- Adapt the wording each time — do not copy a template verbatim.
- Example: "I know this is more than a one-pager. I'm giving you a fuller first pass so you can see the strategic shape, evidence, risks, and possible paths forward. From here, we can tighten it into something you're excited to share."

**Verification reminder** (immediately after the framing note, before the PRD body):

```markdown
**Review note:** I've labeled assumptions, inferences, and source-backed claims, but you're responsible for verifying the final PRD, metrics, citations, and strategy before sharing.
```

### B. PRD one-pager

```markdown
# [Initiative Name] — One-Pager
**Owner:** [name or TBD]  **Date:** [YYYY-MM-DD]  **Status:** Draft

## Strategic Alignment
...

## User Problem + JTBD
...

## Users + Use Cases
...

## Proposed Solution
...

## Requirements
...

## Success Metrics + Validation
...

## Risks, Tradeoffs, and Decisions Needed
...

## Next Steps
...
```

Rules:

- Target one page, tolerate two. If the draft exceeds two pages, cut.
- No section should contain long quoted summaries of source documents.
- All sections are required, even if brief. Use a single sentence rather than omitting.
- Short bullets and 1–3 sentence paragraphs preferred over dense prose.

### C. How to work with this from here

A short practical guide that appears after the draft and before the feedback questions.

```markdown
**How to work with this from here:**
- Tell me what's directionally right or wrong — rough notes are fine.
- Say "revise without search" for wording, structure, scope, or tone edits.
- Say "find evidence" when you want me to search Notion, Amplitude, Hex, Drive, Enterpret, or Slack.
- Paste links, screenshots, docs, metrics, or messy notes if you already have them.
- Most useful inputs: target user, v1 surface, desired outcome, out-of-scope items, known constraints, decision-makers.
- I can keep this broad for strategy alignment or tighten it into a one-page exec-ready PRD.
```

Keep it concise — a practical guide, not a manual.

### D. Feedback questions

```markdown
**Feedback questions:**
1. What did I get directionally right?
2. What did I get wrong, overstate, or miss?
3. What should we optimize for next: sharper strategy, tighter scope, stronger evidence, or a cleaner exec-ready one-pager?
```

Exactly 3 questions. Default set above. Adapt if a more targeted question is clearly better.

### E. Key sources used

```markdown
## Key Sources Used
- FY26 AOP — strategic planning doc — Jan 2026
- Sequences Surface Roadmap — Notion roadmap — Q1 2026
- VoC: Enterprise AE Interviews — Notion research doc — Feb 2026
- Sequences Adoption Dashboard — Amplitude — accessed Apr 2026
```

Rules:

- Only list sources that were actually retrieved and used.
- Do not list sources that were unavailable or not found.
- If no sources were found: `No internal sources found. Claims labeled ASSUMPTION where applicable.`
- Do not fabricate document titles, URLs, owners, or dates.

### F. STATE tag

```
STATE: PRD_DRAFT_READY
```

On its own line. At the very end. After Key Sources Used.

______________________________________________________________________

## Revision format

```markdown
[Full revised draft in the same section structure as the PRD body]

---
**What changed:**
- [Bullet: what section changed and what was updated]
- [Bullet: what new evidence was added and from where, if search was run]

## Key Sources Used
- [updated list if sources changed]

STATE: PRD_REVISION_READY
```

Rules:

- Revisions include the full PRD body only — no framing note, no "How to work with this" section.
- Always include "What changed" — do not skip it even for small edits.
- `STATE: PRD_REVISION_READY` replaces `STATE: PRD_DRAFT_READY` in revisions.
- Do not include the 3 feedback questions in revisions unless the user requests them.
- Key Sources Used appears after "What changed" in revisions.
- Include the **Review note** verification reminder at the top of the revised draft **only when** new evidence, metrics, citations, or factual claims were added or changed. Pure wording / structural / tone revisions skip it.

______________________________________________________________________

## User Problem + JTBD section

Every first draft must answer these questions (or flag with `[NEEDS INPUT:]` if unanswerable):

- **Who:** Who is the user? Specific persona, tier, and moment in their journey.
- **Stuck in:** What moment are they failing to reach, or getting stuck before?
- **Pain:** What pain, confusion, or friction are they experiencing today?
- **Aha moment:** What value moment are we trying to get them to?
- **Behavior change:** What should change about how they use the product if this works?
- **If we get it wrong:** What user-facing risk exists if we build this incorrectly?

If the draft feels too internally focused (too much overlap/dependency discussion, not enough user pain), rebalance toward user journey and value.

______________________________________________________________________

## Risks, Tradeoffs, and Decisions Needed format

Prefer a table when there are 4+ items:

```markdown
| Decision / risk | Why it matters | Current recommendation | Owner / next action |
|---|---|---|---|
| [risk or decision] | [why it matters] | [recommendation or TBD] | [who, what, when] |
```

Use bullets for 3 or fewer items. Never use a long numbered list.

______________________________________________________________________

## Next Steps format

```markdown
| Step | Owner | Action |
|---|---|---|
| What you should do next | [person or role] | [specific action] |
| What team should align on | [person or role] | [specific action] |
| What data to pull | [person or role] | [specific action] |
```

3–5 rows. Action-oriented. Separate: (1) what the user should do, (2) what the team should align on, (3) what data/evidence to pull. Omit a category if it's not applicable.

______________________________________________________________________

## `[NEEDS INPUT: ...]` usage

Use when information is missing and only the user or further clarification can resolve it.

Format: `[NEEDS INPUT: what is needed and why]`

Examples:

- `[NEEDS INPUT: primary user segment — is this targeting AEs, SDRs, or both?]`
- `[NEEDS INPUT: launch timeline — needed to scope requirements]`
- `[NEEDS INPUT: confirm whether this replaces legacy sequence templates or runs alongside them]`

Rules:

- Use inline in the relevant section, not in a separate list.
- Remove `[NEEDS INPUT:]` labels once the user has provided the information.
- Do not use for information that can be reasonably inferred — use `ASSUMPTION:` instead.

______________________________________________________________________

## What counts as a hard statistic

Any precise numeric claim: percentages, counts, dollar amounts, rates, frequencies, percentiles, time durations, dated events, adoption/retention/funnel figures, named survey or interview counts. Hard statistics **must** be cited or, if no source exists, dropped — never published without attribution. Soft estimates ("roughly half", "most users") are not hard statistics but must carry `ASSUMPTION:` if not source-backed.

## What counts as a source-backed claim

A claim — quantitative or qualitative — derived from a retrieved internal artifact you actually opened: Notion doc, Drive file, Slack thread, Hex notebook, Amplitude chart, Enterpret report, exported CSV, call transcript, or named research artifact.

## Source citation format

Preferred (link available):

```
Metric or claim. [Source: [<linked source title>](<url>), <date if available>]
```

Fallback (no link available):

```
Metric or claim. [Source: <source title>, <date if available>; NEEDS SOURCE LINK]
```

Rules:

- Prefer clickable Markdown links whenever a URL is available.
- Cite Notion, Drive, Slack, Hex, Amplitude, Enterpret, dashboards, docs, notebooks, and exported files by their actual title.
- Never fabricate URLs, titles, dates, owners, dashboards, metrics, or quotes.
- Do not output a precise number without a source. If the source can't be located, use `[NEEDS SOURCE LINK: ...]` or drop the number.

______________________________________________________________________

## `INFERENCE:` usage

Use when you draw a conclusion from a retrieved source that the source does not explicitly state.

Format: `INFERENCE: [the conclusion] — based on [source].`

Examples:

- `INFERENCE: enterprise AEs are the highest-value segment for this initiative — based on FY26 AOP focus areas, though AOP does not explicitly link this surface to enterprise AEs.`
- `INFERENCE: reply rate decline correlates with template overuse — based on Sequences Usage Dashboard, which shows both trends but does not assert causation.`

Rules:

- Always cite the underlying source the inference is based on.
- Do not present inferences as facts.
- Replace with a direct source-backed claim if/when one is found.

______________________________________________________________________

## `[NEEDS SOURCE LINK: ...]` usage

Use when a statistic or claim references a known source, but the URL or artifact location is missing.

Format: `[NEEDS SOURCE LINK: what to find]`

Examples:

- `25% of enterprise accounts churned within 90 days. [Source: Q1 churn review; NEEDS SOURCE LINK: Drive doc title or URL]`
- `[NEEDS SOURCE LINK: Amplitude chart for SDR session timing]`

Rules:

- Use whenever a precise number lacks a verifiable link.
- Pair with the cited source name when one is known.
- Do not let a `[NEEDS SOURCE LINK: ...]` flag silently disappear in revisions — either resolve it or keep it.

______________________________________________________________________

## `ASSUMPTION:` usage

Use when a claim is useful to include but is not directly supported by a retrieved source.

Format: `ASSUMPTION: [the claim]`

Examples:

- `ASSUMPTION: most AEs currently copy-paste sequences manually — no Amplitude data found to confirm.`
- `ASSUMPTION: enterprise accounts are the primary segment based on AOP focus areas, but no explicit user research found.`

Rules:

- Appears inline in the section where the claim is made.
- Never remove an `ASSUMPTION:` label without replacing it with an actual source.
- Do not use `ASSUMPTION:` for claims that are clearly wrong or speculative to the point of misleading — omit those entirely.

______________________________________________________________________

## `STATE:` tag usage

| Tag | When to emit |
|-----|-------------|
| `STATE: PRD_DRAFT_READY` | End of every first draft |
| `STATE: PRD_REVISION_READY` | End of every revision |

Rules:

- The tag appears on its own line, at the very end of the response, after all content.
- Only one `STATE:` tag per response.
- The skill uses the presence of either tag in conversation history to detect that a draft exists (skip intake, enter revision mode).
- Do not emit a `STATE:` tag in intake responses or mid-research updates.
