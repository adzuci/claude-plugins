# Answer Format

Use this in Step 4 when drafting, and for single-question lookups.

## Per-Question Block

```text
Q[N]: [Question text]
A[N] (Proposed): [Your answer — clear, direct, customer-friendly]
Confidence: High / Medium / Low  |  Score: [0–100]
Reasoning: [One sentence explaining the score]
Notes: [Source citation | flag | assumption label if applicable]
```

## Confidence Levels & Scores

Each answer carries both a label and a numeric score (0–100):

| Label | Score range | Meaning |
|-------|-------------|---------|
| High | 90–100 | Directly from approved Apollo docs (Privacy Policy, DPA, SOC 2, Security Whitepaper) |
| High | 70–89 | Consistent with known Apollo practices; minor adaptation needed |
| Medium | 50–69 | Inferred from similar prior answers; SME review recommended |
| Low | 0–49 | Unable to answer confidently; flag for expert and leave as Needs Review |

Always include a one-sentence **reasoning** note explaining the score, e.g.:
`Reasoning: Directly sourced from Apollo DPA Section 4 with no adaptation required.`

## Tone & Style

- Plain language, declarative sentences
- Consistent with Apollo's existing collateral terminology
- No invented certifications, controls, or future-state promises
- If a question requires a legal/binding commitment → answer factually and label: `⚠️ Requires legal/compliance approval`

## Source Citations

Append brief source cues inline, e.g.:
`(Based on: Security Whitepaper 2025, prior ticket DS-1234)`

## Assumptions

Label clearly: `Assumption: [stated assumption]`
