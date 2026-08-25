# Demo Prep Brief Output Template

Use this exact structure for every brief. Preserve all seven numbered sections.

```markdown
# Demo Prep Brief: [Account Name]

Generated: [date] | Stage: [current stage or Unknown] | ARR: [value or Unknown] | Close Date: [date or Unknown]

---

## 1. Account Snapshot

[3-5 sentences explaining who they are, what they do, size, industry, current tools, and why they are evaluating Apollo. Every factual claim includes a confidence tag and source.]

[If relevant: No dealroom or call history found — brief based on SFDC data only.]
[If relevant: Sparse data — recommend AE sync before demo.]

## 2. Stakeholder Map

- **[Name or Unknown]** — [Title or Unknown] — [Role in deal] — [email, when the SFDC contact record has one; omit the field entirely if not — never guess or construct one from a domain]
  - Cares about: [specific priority, pain, metric, or Unknown]. [confidence] Source: [source]
  - Notes: [deal-relevant context]. [confidence] Source: [source]

**Include each stakeholder's email when SFDC has it — added 2026-07-30.** Whichever contact records get resolved for this map, carry their email address through. `demo-instance-configuration` needs one (the prospect-side Apollo Admin's) to provision the demo sub-account, and it has no research capability of its own — so an email missing here becomes a cold prompt to the SC for something the deal record already contained. A live run (2026-07-30) hit exactly that: the skill resolved contact records for this map, then Layer 2 had to ask for a named stakeholder's email even though she was quoted by name elsewhere in the same brief. **Never fabricate one** — no guessing `first.last@domain`, no constructing from the company domain. Omit the field and let Layer 2 ask; a wrong email would provision a real account to the wrong person.

Risk flags:

- [Single-thread risk / No Economic Buyer identified / Champion not validated / None identified]

## 3. Pain Points (Ranked)

1. **[Pain point]** — maps to [Apollo capability].
   - Confidence: [verified | inferred | assumed]
   - Source: [exact source]
   - Demo implication: [what this means for the show plan]

2. **[Pain point]** — maps to [Apollo capability].
   - Confidence: [verified | inferred | assumed]
   - Source: [exact source]
   - Demo implication: [what this means for the show plan]

[If fewer than 3 pain points are verified: Thin pain documentation. Recommend confirming pain points in first 5 minutes of demo.]

## 4. Competitive Landscape

- **Known competitors**: [competitor names or Unknown]. [confidence] Source: [source]
- **Deal-specific readout**:
  - **[Competitor]** — Strength for this deal: [specific strength or Unknown]. Weakness for this deal: [specific weakness or Unknown]. [confidence] Source: [source]
- **Positioning notes**:
  - [Use the competitive-positioning reference only for competitors present in this deal.]
- **Gaps**:
  - [Competitive intel gaps or None identified]

[If section is only inferred or assumed: Low confidence section — verify with AE before demo.]

## 5. Recommended Demo Flow

1. **[Apollo Capability]** — Show this because [specific pain point, decision criterion, or stated need]. [confidence] Source: [source]
2. **[Apollo Capability]** — Show this because [specific pain point, decision criterion, or stated need]. [confidence] Source: [source]
3. **[Apollo Capability]** — Show this because [specific pain point, decision criterion, or stated need]. [confidence] Source: [source]

### Standard flow additions

- **[Capability]** — Worth showing because [standard reason tied to use case]. [assumed] Source: Standard Apollo demo practice from capabilities map

## 6. Landmines

- **Technical blockers**: [blockers or Unknown]. [confidence] Source: [source]
- **Integration risks**: [risks or Unknown]. [confidence] Source: [source]
- **Product gaps for this use case**: [gaps or Unknown]. [confidence] Source: [source]
- **Sensitive topics**: [pricing promises, AE commitments, security/compliance issues, competitive claims to handle carefully, or Unknown]. [confidence] Source: [source]

Hard blocker scan:

- Salesforce Essentials plan: [Detected / Not detected / Unknown]
- Microsoft GCC High or government tenant: [Detected / Not detected / Unknown]
- On-premise Exchange: [Detected / Not detected / Unknown]

[Include the hard blocker scan only when a source mentions CRM plan tier, government/GCC, Exchange, mailbox, email infrastructure, or related technical feasibility. Otherwise omit the scan and write: No hard blocker signals detected in available data.]

## 7. Open Questions

Ask these in the first 5 minutes:

- [Actual question the SC can ask]
- [Actual question the SC can ask]
- [Actual question the SC can ask]

Internal AE/SC sync questions, if needed:

- [Actual question for the AE or SC]
```

## Formatting Requirements

- Every factual claim needs a confidence tag and source.
- Use `Unknown` when data is unavailable.
- Keep Account Snapshot concise.
- Make Open Questions longer when source data is sparse.
- Include the hard blocker scan only when relevant signals appear; otherwise use the single no-signal line.
- Do not include a separate source appendix; cite sources inline.
- Do not add sections beyond the seven-section contract.
- **Write the handoff appendix to the scratchpad alongside the brief — mandatory, added 2026-08-19.** See "Handoff Appendix" below. It is scratchpad-only and never rendered to the SC, so it does not add an eighth section to the contract above.
- **Write the rendered brief to the session scratchpad — mandatory, added 2026-07-28.** Rendering this brief triggers `SKILL.md`'s Terminal Output Assertion condition (c): its exact content, with every `[verified]`/`[inferred]`/`[assumed]` tag intact, must be written to `demo-prep-scratchpad.md` per `GOVERNANCE.md`'s session-scratchpad exception. This is not conditional on the SC asking and is not skippable — it is the only channel `demo-instance-configuration` has for picking this brief up, and skipping it silently breaks the Layer 1 → Layer 2 handoff. It is also the *sole* exception to this skill's read-only boundary; nothing else here writes anywhere.

---

## Handoff Appendix (scratchpad only — added 2026-08-19)

Two blocks that go into `demo-prep-scratchpad.md` and **never into the rendered brief**. They exist because `demo-instance-configuration` ends its run by generating an SC-facing Demo Prep Guide, and that guide is bound by a hard rule: nothing appears on it that this skill or `demo-instance-configuration` did not generate or gather. Anything Layer 2 needs and does not receive is a section the guide has to leave empty.

All three blocks are **major artifacts** for the purposes of the Terminal Output Assertion's condition (c) — write them whenever the data behind them exists, and accumulate them into the same per-deal file rather than overwriting a sibling block. **Block 3 is written on every run without exception**, since "what did this session produce" always has an answer.

Do not render these blocks to the SC, do not summarize them in the closing note, and do not treat their presence as a reason to expand the brief. They are a machine handoff.

### Block 1 — Qualification Record Block

The seven-section brief folds qualification data into Stakeholder Map risk flags, Pain Points, and Competitive Landscape. That is right for the brief and insufficient for the handoff: Layer 2 needs the per-pillar state, which the folded prose does not carry. This block carries it.

**Populate it from the fields already ingested per `references/data-sources.md`'s SFDC Field Dictionary. Never query anything new to fill it, and never carry a pillar this deal's record has no field for.**

One line per pillar, then the value:

```
- **[Pillar]** | label: [verified field label(s) from the Field Dictionary] | state: [VERIFIED | PARTIAL | UNCONFIRMED | EMPTY] | confidence: [verified | inferred | assumed | none]
  - [The value, in the same normalized form the brief would use. Omit this line entirely when state is EMPTY.]
```

Pillars, in this order, with the **exact source fields** that determine each one's `state`. A pillar's fields are every Field Dictionary row for that concept, `- CI` variants and detail fields included — this is spelled out because `state` turns on how many of a pillar's fields are populated, so leaving the grouping implicit makes `PARTIAL` versus `VERIFIED` undecidable:

| Pillar | Source fields |
|---|---|
| Metrics | `Metrics__c`, `Metrics_CI__c` |
| Economic Buyer | `Economic_Buyer__c`, `Economic_Buyer_Details__c`, `Economic_Buyer_CI__c` |
| Decision Criteria | `Decision_Criteria__c`, `Decision_Criteria_CI__c` |
| Decision Process | `Decision_Process_del__c`, `Decision_Process_CI__c` |
| Paper Process | `Paper_Process__c`, `Paper_Process_CI__c` |
| Identified Pain | `Before_Scenario__c`, `Pain_Points_CI__c` |
| Champion | `Champion__c`, `Champion_CI__c`, `Champion_Details__c`, `Champion_Identified__c` |
| Competition | `Competition__c`, `Competition_CI__c`, `Competitor_Details__c` |
| Before state | `Before_Scenario__c` |
| Business Impact | `Negative_Consequences__c` |
| After scenario | `After_Scenario__c` |

**The Force Management trio are single-field pillars, so they can only ever be `EMPTY`, `VERIFIED` or `UNCONFIRMED` — never `PARTIAL`.** `Before_Scenario__c` appears twice on purpose, once as the Identified Pain pillar's field and once as the before state, because in this org it is one field serving both.

**A populated `Economic_Buyer__c` is a record ID, not a name** — resolve it per the Field Dictionary's lookup note before writing the value line, and never put the raw ID in the block.

**Where a pillar's fields disagree, that is a real conflict, not a `state` question.** `Competition__c` reading `Other;` while `Competition_CI__c` names actual competitors is the documented case. Both fields being populated still makes the pillar `VERIFIED`; the disagreement itself goes to Open Questions per the existing conflict rule, and the value line here carries both readings rather than silently picking one.

**`state` is mechanical, not a quality judgment. The four tests are ordered and exclusive — take the first that matches and stop:**

| # | Test | `state` |
|---|---|---|
| 1 | Every source field for the pillar is null | `EMPTY` |
| 2 | The pillar has more than one source field and some, but not all, are populated | `PARTIAL` |
| 3 | All source fields populated, and the claim carries `[verified]` | `VERIFIED` |
| 4 | All source fields populated, and the claim carries `[inferred]` or `[assumed]` | `UNCONFIRMED` |

**The ordering is what makes this deterministic, so do not reorder it.** A two-field pillar with one field populated and a `[verified]` claim matches both test 2 and test 3 on their wording alone; taking the first match resolves it to `PARTIAL`, every time, for every deal. **A single-field pillar can never be `PARTIAL`** — with one field there is no "some but not all," so it falls to test 1, 3 or 4.

**Do not emit any other state value.** In particular, do not emit `THIN`, `WEAK`, or `UNKNOWN`: those describe how good the content is, which nothing in this handoff grounds, and inventing them is exactly the failure this block exists to prevent. Four states, derived from field population and the confidence tag the brief already assigned — nothing else.

**Always name the verified label, never the API name**, and take the label from the Field Dictionary rather than reading it off the API name. Two in this set do not match their API names: `Negative_Consequences__c` is labelled **Business Impact**, and `Before_Scenario__c` is labelled **🔴 Identified Pain** and serves as both the MEDDPICC Identified Pain pillar and Force Management's before state. A guide citing "Negative Consequences" is citing a field this org does not have.

**When `state` is `EMPTY`, still emit the pillar line.** A missing pillar and an empty pillar are different facts, and the empty one is the actionable one — it is what tells the SC what to probe. Dropping the line makes an unfilled field indistinguishable from a field that does not exist.

### Block 2 — Apollo AI Demo Setup Prompts

When this run generated Apollo AI demo setup prompts, write **all of them, verbatim**, to the scratchpad — full prompt text, their numbering, and every `Demo talk-track hook` line intact.

**Why verbatim matters.** The hooks are the only sourced, verbatim SC phrasing the configuration fast path produces, and they are the only legitimate talk track the Demo Prep Guide can carry. Paraphrasing them makes them unciteable — a hook that has been reworded is no longer something the run generated, so the guide has to drop it. A prompt that produced no hook should say so; do not compose one to fill the slot.

Layer 2 also consumes these prompts as a **specification**, not only as talk track — see below, then — see `demo-instance-configuration`'s Input Contract, where a prompt's spec for a given object governs over Layer 2's own derivation of that same object. Truncating or summarizing a prompt therefore degrades what gets built, not just what gets written on the guide.

### Block 3 — Artifacts produced this session

One line naming which of this skill's artifacts the session actually produced. Write it on every run, even when the answer is short.

```
Produced this session: [comma-separated artifact names]
```

Use exactly these names, and only these:

`demo prep brief`, `Apollo AI Context Center payload`, `Apollo AI demo setup prompts`, `Context Center calibration notes`, `strategic angle`, `fuller talk track`, `pre-demo checklist and post-demo actions`, `SC walkthrough`, `Run Sheet`, `Slack deal room Canvas`, `AE sync questions`, `calendar and Gmail alignment check`, `post-demo debrief prep`

**Why this block exists, and why the names are fixed.** `demo-instance-configuration`'s Demo Prep Guide ends with an "Also available" section that tells the SC which of these artifacts exist and which need a re-run to produce. That section is the **only** place the configuration fast path advertises them — the fast path deletes the menu where an SC would otherwise discover them. Layer 2 sorts that section from this line, matching these names against its own inventory, so a name that does not match is an artifact the SC is told to re-run when they already have it.

**Two of the thirteen names deliberately have no row in Layer 2's inventory: `demo prep brief` and `Apollo AI Context Center payload`.** They are the run's primary outputs, not things an SC would be told to re-run for, so they are listed here for completeness and simply do not render in the guide's "Also available" section. That asymmetry is intentional — do not "fix" it by adding inventory rows for them, and do not drop them from this vocabulary. Every other name must match its inventory row literally.

**Anything absent from this line is reported to the SC as not generated.** That is the safe direction — under-claiming costs one re-run, over-claiming sends someone looking for something that was never produced — but it means an artifact you genuinely produced and forgot to list gets hidden from the SC. List what exists.
