# Example: Revision — Additional Search Needed

This example shows a revision that requires a targeted internal search before the draft can be updated.

> **Note:** All URLs in this example are illustrative placeholders, not real Apollo internal links.

The conversation already contains `STATE: PRD_REVISION_READY` from the previous revision in `revision_no_search.md`.

______________________________________________________________________

## User message

> The success metrics section feels weak — "adoption" and "reply rates" are fine but generic. Can you find actual baseline data for SDR sequence creation frequency and reply rates in Amplitude or Hex? I want the metrics section to have real numbers so reviewers have context for what we're targeting.

______________________________________________________________________

## Skill classification (internal)

Revision type: **YES — additional search needed.**

The user is explicitly asking to:

- Find baseline data from Amplitude or Hex (named source lookup)
- Add real numbers to the success metrics section (numeric claim, needs source)

→ Run targeted search for SDR sequence creation frequency and reply rate baselines in Amplitude/Hex before revising. Do not re-run full research pass.

______________________________________________________________________

## Skill response — Revised draft

*(Skill searches: Amplitude Sequences Usage Dashboard, Hex sequences adoption report. Scoped to: sequence creation frequency per SDR, reply rates for outbound sequences. Full research pass not re-run.)*

______________________________________________________________________

**Review note:** I've labeled assumptions, inferences, and source-backed claims, but you're responsible for verifying the final PRD, metrics, citations, and strategy before sharing.

# AI Sequence Writer — One-Pager

**Owner:** TBD **Date:** 2026-04-27 **Status:** Draft

## Strategic Alignment

- Sequences is a top-priority surface in the FY26 AOP under the "SDR Productivity" theme. \[Source: [FY26 AOP](https://notion.so/apollo/fy26-aop), Jan 2026\]
- AOP calls out AI-assisted outreach as a key H2 FY26 investment area — this initiative is a direct expression of that bet.
- Uses existing AI credits infrastructure; no new vendor dependency required.

## User Problem + JTBD

- **Who:** SDRs who build sequences from scratch or by modifying templates.
- **Stuck in:** The creation step — they have a target account and persona but face a blank editor.
- **Pain:** 20–30 minutes per sequence customizing templates. ASSUMPTION: PM estimate — not yet validated.
- **Aha moment:** First AI-written sequence good enough to send with minor edits, in under 2 minutes.
- **Behavior change:** AI Write becomes the default sequence creation entry point, not manual writing.
- **If we get it wrong:** SDRs try it once, get generic output, and don't return — deepening distrust of AI on the platform.

## Users + Use Cases

**Primary:** SDRs (inbound + outbound)

1. SDR opens a new sequence for a SaaS AE persona, pastes in company context, gets a ready-to-send 5-step email sequence.
1. SDR edits 1–2 steps to add a personal touch, sends without rewriting from scratch.
1. SDR manager reviews AI-generated sequences before enabling for the team.

## Proposed Solution

Add an **"AI Write"** entry point in the Sequence creation modal. SDR provides: target persona, company type or vertical, optional tone preference. The system uses the existing AI credits infrastructure to generate a 4–6 step sequence. All steps are editable before saving.

**Why this over alternatives:**

| Alternative | Why not |
|---|---|
| Improve template suggestions (existing) | Doesn't solve the blank-editor problem — SDR still writes |
| Standalone writing tool outside Apollo | Breaks the flow; SDR has to re-import |
| Full agentic end-to-end creation | Higher complexity; out of scope for v1 |

[NEEDS INPUT: Does "AI Write" replace "Start blank" or sit alongside it?]

## Requirements

- Integrates with existing AI credits system — no new LLM vendor.
- Supports 4–6 step sequences; step count configurable.
- Input: persona description, company type or vertical, optional tone.
- Output: subject line + body copy per step, editable inline.
- Latency: [NEEDS INPUT: acceptable generation time?]
- Respects existing sequence length limits and compliance guardrails.

## Risks, Tradeoffs, and Decisions Needed

| Decision / risk | Why it matters | Current recommendation | Owner / next action |
|---|---|---|---|
| Generic output kills trust | SDRs who get poor output on first use will not return | Require persona + company type as mandatory inputs; test prompt quality before shipping | PM + AI infra |
| AI credits cost at P90 SDR usage | High-volume SDRs could exhaust credits faster than expected | Model cost at P90 before committing to unlimited credits | PM + Finance |
| Compliance: AI-generated email content | Regulated verticals may have legal constraints | Legal review before GA; opt-out for regulated accounts | PM + Legal |
| Cannibalization of template upsell | AI Write may reduce engagement with paid template packs | [NEEDS INPUT: check with Growth/Monetization] | PM + Growth |

## Success Metrics + Validation

**Baselines** \[Source: [Sequences Usage Dashboard](https://app.amplitude.com/analytics/apollo/dashboard/sequences-usage), Amplitude, accessed Apr 2026\]:

- Median SDR creates 2.1 new sequences/month; P75 creates 4.8/month.
- Median outbound email reply rate across Apollo sequences: 3.2%. Top-quartile sequences: 5.8%.

| Metric | Baseline | Target |
|---|---|---|
| % of new sequences created via "AI Write" | 0% (net-new feature) | ≥25% of new sequences within 60 days |
| Reply rate: AI-written vs. manual | 3.2% median \[Source: [Sequences Usage Dashboard](https://app.amplitude.com/analytics/apollo/dashboard/sequences-usage), Amplitude, Apr 2026\] | Within 0.5pp of manual baseline at 30 days; at or above median by 90 days |
| Sequence creation frequency per SDR | 2.1/month median \[Source: [Sequences Usage Dashboard](https://app.amplitude.com/analytics/apollo/dashboard/sequences-usage), Amplitude, Apr 2026\] | Neutral or higher vs. pre-launch baseline |
| Time to first send | [NEEDS INPUT: session timing data not found in Amplitude] | [NEEDS INPUT] |

INFERENCE: AI Write only needs to match the 3.2% manual median to be a net win on quality, because SDRs save creation time even when reply rate is flat — based on Sequences Usage Dashboard reply-rate distribution; the dashboard does not draw this conclusion directly.

## Next Steps

| Step | Owner | Action |
|---|---|---|
| Validate time estimate | PM | 3–5 SDR interviews or Amplitude session timing data |
| Test prompt quality | PM + AI infra | Run prompt eval on 20+ personas before committing to launch scope |
| Legal review | PM + Legal | Submit AI-generated outbound email use case |
| Credits cost model | PM + Finance | Model credits burn at P50/P90 SDR usage |

______________________________________________________________________

**What changed:**

- Added Amplitude baseline data: sequence creation frequency (2.1/month median, 4.8 P75) and reply rate (3.2% median, 5.8% top-quartile). Source: Sequences Usage Dashboard, Amplitude, Apr 2026.
- Rewrote Success Metrics table with specific numeric targets anchored to baselines.
- Flagged remaining gap: time-to-first-send baseline not found in Amplitude — session timing data or user research needed.

## Key Sources Used

- [FY26 AOP](https://notion.so/apollo/fy26-aop) — strategic planning doc — Jan 2026
- [SDR Productivity Roadmap](https://notion.so/apollo/sdr-productivity-roadmap) — Notion roadmap — Q1 2026
- [Sequences Usage Dashboard](https://app.amplitude.com/analytics/apollo/dashboard/sequences-usage) — Amplitude — accessed Apr 2026

STATE: PRD_REVISION_READY
