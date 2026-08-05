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
- **Write the rendered brief to the session scratchpad — mandatory, added 2026-07-28.** Rendering this brief triggers `SKILL.md`'s Terminal Output Assertion condition (c): its exact content, with every `[verified]`/`[inferred]`/`[assumed]` tag intact, must be written to `demo-prep-scratchpad.md` per `GOVERNANCE.md`'s session-scratchpad exception. This is not conditional on the SC asking and is not skippable — it is the only channel `demo-instance-configuration` has for picking this brief up, and skipping it silently breaks the Layer 1 → Layer 2 handoff. It is also the *sole* exception to this skill's read-only boundary; nothing else here writes anywhere.
