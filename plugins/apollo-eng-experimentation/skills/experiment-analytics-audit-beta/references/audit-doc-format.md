# Analytics Audit output format

**The output is team-agnostic.** The audit is delivered as chat findings plus a
standalone markdown doc built from `assets/analytics-audit-template.md`. Notion
is an *offered* export, never an assumption: teams using the Experiment ERD
template have a pre-created **Analytics Audit** page (a one-line pointer to this
skill plus an inline **Experiment Events** database — the template page:
[Analytics Audit](https://app.notion.com/p/apolloio/Analytics-Audit-752883bcb695462e818b2d808d89181f),
in `Experiment ERD (Template)`, schema verified 2026-10-05). After showing the
content, ask: fill their ERD's page (when it exists), create one from the
template (if they want it), or leave the output as chat + file. Never edit the
template page itself — only the experiment's own copy.

**Humans are the audience.** No YAML, no internal jargon, no certainty grades on
the page. Confident findings read as statements; shaky ones read as questions
("needs a check: …") with how to resolve them. The skill's working vocabulary
maps onto the page per the table below and otherwise stays in chat.

## What the audit covers (and what it doesn't own)

The **metric split** (primary / secondary / guardrail) lives on the Experiments
DB entry and is usually reused team-standard metrics; the audit *sanity-checks*
that it is logical and maps to the experiment design, and flags mismatches — it
never redesigns it. The audit's own substance is the **event inventory**: every
interaction on the surfaces the experiment touches (clicks, form submissions,
dialog opens/closes, redirects, …) that the team wants for learnings, plus the
events behind the reused metrics — which is where symmetry risk usually hides.

## Doc layout (top to bottom)

1. **Header:** the title, nothing else; what the audit was built on and what
   it replaces go in the toggle at the end.
1. **Verdict callout:** "**Can we measure this experiment yet?** Yes / Not yet —
   {N} things to fix first", each blocker as one plain sentence. The rule:
   **yes** only when every event behind a primary or guardrail metric is
   `Preexisting` with the properties its metric and segment cuts need, and
   nothing is skew-flagged. Anything else — including "couldn't verify" — is
   **not yet**. A net-new primary event (learning experiments) keeps the verdict
   at "not yet" until it exists and fires in both arms.
1. **TL;DR callout:** 3–4 lines on how to read this experiment's analytics —
   which events carry it, the properties that answer what/where/which-arm, the
   intent-vs-success rule of thumb. Written for whoever queries Amplitude next
   month. Model: the SSO audit's TL;DR.
1. The **event inventory** — the Experiment Events table (next section).
1. **Open questions:** owner-tagged bullets (engineer / DS / PM). Include the
   standing variant-stamping question from `experiment-taxonomy.md` until DS
   answers it for the team.
1. **"How this was checked" toggle** (collapsed): branch/commit inventoried,
   code searches run, Amplitude lookups and volume pulls with project + dates,
   Snowflake queries or "not needed", metric-split source, the pre-analysis
   plan and exposure-design hand-over it was built on, and what it replaces.

## The event inventory (Experiment Events columns)

One row per event-and-action. Stage B of this skill reads
these rows, so fill every column and keep their meanings stable:

- **Action** (title) — the user or system moment, in plain words ("renames a
  search from the … menu").
- **Event Name** — the exact name code sends (not the Amplitude display name;
  note a differing display name in Description).
- **Trigger** — when it fires (page mount, user action, API response, backend
  job), the condition it's gated on, and the code path in parentheses. For
  `New` events this is the build spec: where it *should* fire.
- **Properties** — the properties the metrics, segment cuts, and learnings
  need; anything required but not arriving is written as `missing: <property>`.
- **Description** — what the reader needs: which metric or learning the row
  serves, a volume with pull date when it matters, and any skew warning as one
  🚨-prefixed sentence (what the treatment changes about its gating, what the
  readout would wrongly say, and the fix).
- **Status** (select):
  - `Preexisting` — fires today, confirmed in **code and Amplitude** (never a
    doc).
  - `New` — comes with the treatment; the row itself is the spec to build from.
- **Amplitude Link** (url) — the event's page in the Amplitude data catalog,
  e.g.
  `https://app.amplitude.com/data/apollo-io/Marketing%20%2B%20App%20V2%20(PROD)/events/main/latest/<URL-encoded event name>` (format verified against
  the SSO audit's links, 2026-10-05). Blank for `New` events — Stage B
  fills it once the event lands.

## Working vocabulary → the inventory

| Internal status | On the doc |
|---|---|
| `exists` | Status `Preexisting` + Amplitude Link |
| `missing-property` | `Preexisting` + `missing: X` in Properties; a verdict blocker when a primary/guardrail metric needs it |
| `new-for-treatment` | Status `New`; Trigger carries the build spec |
| `unknown-until-built` | Status `New`, plus the question under Open questions |
| `symmetry-risk` | 🚨 sentence in that row's Description, plus a verdict blocker |

## Other writes (all offered, never assumed)

- The experiment's **Experiments DB entry**, when the team keeps its metric
  split there: resolved event names and baselines into its Metrics tables, and
  a link line to wherever the audit landed, carrying the verdict (e.g.
  `Analytics Audit (Discovery): 🔴 not yet — <link>`). The Growth & Acquisition
  Experiments DB has **no dedicated status property** for this (verified
  2026-10-05); if one is added later, set it too.
- Every write is shown verbatim and approved before anything is sent.

## Verification contract

Stage B of this skill later verifies the built code
against this inventory, reading the rows (a database query or the markdown
table — never a string diff) and re-auditing semantically. Keep the column set
and the two statuses as defined here; per-experiment variation belongs in row
content, never in renamed columns or new statuses.
