# Required sections by artifact kind

Used by Phase 2. A section counts as present if a synonym carrying the same content exists. It counts as missing if it is absent, or present but empty.

Keep this list short on purpose. Every entry is a potential `missing-required-section` finding, and a long list produces noise that trains readers to skim.

## `prd`

| Required | Satisfied by | Notes |
|---|---|---|
| Problem statement | "Why", "Background", "Context" | Must describe a customer or business problem, not a solution |
| Target user / segment | "Audience", "ICP", "Who" | Must name a segment, not "users" |
| Success metrics | "Goals", "KRs", "Measurement" | **Must contain numbers.** A goal without a number does not satisfy this |
| Non-goals | "Out of scope" | One line is enough |
| Acceptance criteria | "Requirements", "Definition of done" | Must be testable. A numbered description of a flow is not acceptance criteria |
| Open questions | "TBD", "FAQ" with unanswered items | A self-answered FAQ does not satisfy this |

## `estimate`

| Required | Satisfied by | Notes |
|---|---|---|
| Work breakdown with effort | "Phases", "Slices", "Milestones" | Needs per-item effort, not just a total |
| Total with assumptions | "Summary", "Program total" | Must state headcount or parallelism assumed |
| External dependencies | "External gates", "Blockers", "Risks" | Anything outside engineering control |
| Out of scope | | |
| Open questions with defaults | "Assumptions" | Best-practice: each with a cost-if-different |

## `constraint-register`

Legal, security, compliance, or platform-policy registers.

| Required | Satisfied by | Notes |
|---|---|---|
| Enumerated items with IDs | | Must be individually referenceable |
| Per-item status | | Pending / resolved / not-applicable |
| Per-item owner | | |
| Per-item gating scope | "Blocks", "Gates" | Which milestone each item gates |
| Verification date | "Last verified", "As of" | Without this, staleness cannot be assessed and every item is suspect |

## `design`

| Required | Satisfied by | Notes |
|---|---|---|
| Enumerated screens or flows | | |
| Scope statement | | Which PRD requirements it covers |
| Option set, if exploratory | "Variants", "Alternatives" | When multiple options exist, each needs a distinguishing rationale |

## `plan`

| Required | Satisfied by | Notes |
|---|---|---|
| Sequenced work items | | |
| Owner per item | | |
| Dependency statement | | |

## `tracker`

Jira epics and issue sets.

| Required | Satisfied by | Notes |
|---|---|---|
| Epic exists for each named workstream | | A workstream in the docs with no epic is a finding |
| Milestone labelling | | If the docs use M1/M2/S3.x, the tracker should be able to express it |
| Assignee on non-backlog items | | |

## No schema defined

If an artifact's `kind` is not listed here, run Phases 1, 3, 4, and 5 on it and **skip Phase 2**. Say so in the Phase 6 coverage note. Do not invent required sections for an unknown kind.
