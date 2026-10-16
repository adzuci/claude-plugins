# Finding classes

Closed taxonomy. If a finding does not fit one of these, do not invent a class — either it belongs in an existing one or it is not a finding for this skill.

Each class lists what evidence is required. Findings that cannot meet the evidence bar are dropped.

## `missing-required-section`

A required section for the artifact's `kind` is absent, or present but empty.

**Evidence:** the artifact's actual heading list, quoted, plus the required-section name from `artifact-schemas.md`.

**Check synonyms first.** "Goals" containing numeric targets can satisfy "success metrics". "FAQ" containing unanswered items can satisfy "open questions". A rename is not a gap. An empty section is.

**Consequence tier:** low on its own. It matters when combined with another class (a PRD with no acceptance criteria *and* an unestimated requirement is a real problem; either alone is housekeeping).

## `lapsed-date`

A date field is in the past while the artifact's status indicates the work is not done.

**Evidence:** the date, the status, and today's date, quoted together.

**Consequence tier:** medium. Usually reporting drift rather than product risk, but it is the cheapest possible signal that a document has stopped being maintained, which makes every other claim in it suspect.

## `stale-relative-to-sibling`

Two artifacts cover the same fact and the older one has not absorbed something the newer one records.

**Evidence:** both quotes, both `last_edited` timestamps, and a statement of which fact the older one is missing.

**Do not conflate with `mutually-exclusive-claim`.** Staleness means one side simply has not caught up. Mutual exclusivity means both are current and they cannot both hold.

**Authority does not settle this.** A higher-authority artifact can be the stale one. Report both the authority ranking and the recency and let the human decide.

**Consequence tier:** high when the stale side is the one people are working from.

## `mutually-exclusive-claim`

Two artifacts make claims that cannot both be true, and neither is obviously stale.

**Evidence:** both quotes, plus an explicit statement of why they are incompatible. "These seem to differ in emphasis" is not a contradiction. If a reasonable reader could hold both, it is not this class.

**Consequence tier:** highest. This is what the skill exists for.

Sub-patterns worth naming, because they recur:

- **Scope asymmetry** — a capability appears in one artifact's scope and another's out-of-scope.
- **Semantics inversion** — the same operation is described with opposite behaviour (a pause that stops all activity versus a pause that continues removals).
- **Segment/constraint mismatch** — a target segment cannot satisfy a documented eligibility threshold.
- **Value-prop/constraint collision** — the stated differentiator is the thing a constraint register prohibits.

## `unestimated-requirement`

A requirement is asserted in a PRD or constraint register but appears in no plan or estimate artifact.

**Evidence:** the requirement quoted from its source, plus a statement of which estimate artifact was searched and what was found in the nearest matching line.

Be precise about partial coverage: an estimate line covering three of five sub-requirements is still a finding, and the finding should say which two are uncovered. Partial coverage reported as full coverage is how schedule risk hides.

**Consequence tier:** high. This class most directly predicts schedule slip.

## `unowned-decision`

An open question, decision, or blocker has no named owner.

**Evidence:** the item quoted, plus confirmation that no owner field or assignee exists anywhere in the artifact set for it.

**Consequence tier:** medium alone, high in aggregate. One unowned question is normal; thirty is a process failure and should be reported as a count with examples, not thirty separate rows.

## `unreachable-artifact`

An artifact in the config could not be fetched.

**Evidence:** the reference, the failure mode (auth, 404, size, permission), and what was attempted.

Always report. An artifact nobody can read has never been checked against anything, and its absence from the audit is a coverage gap the reader must know about.

**Consequence tier:** medium, escalating to high if the unreachable artifact is the only source for a whole category (for example, the only design artifact).

## Explicitly not findings

- Style, tone, formatting, or length
- Absence of something no schema requires
- Disagreement between an artifact and your own product judgment
- Anything a reasonable reader could hold both sides of
- Anything you cannot quote from two sides
