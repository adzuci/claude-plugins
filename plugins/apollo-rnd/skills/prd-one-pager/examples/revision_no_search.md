# Example: Revision — No Additional Search Needed

This example shows a revision that only requires editing existing content. No new search is triggered.

> **Note:** This is the negative case for the **Review note** — because no new evidence, metrics, or factual claims were added, the verification reminder is intentionally omitted from the revised draft.

The conversation already contains `STATE: PRD_DRAFT_READY` from the AI Sequence Writer draft in `new_initiative.md`.

______________________________________________________________________

## User message

> The problem statement is too long and a bit rambling. Tighten it up. Also, move "Risks" before "Success Metrics" — I want reviewers to see the risks early.

______________________________________________________________________

## Skill classification (internal)

Revision type: **NO — no additional search needed.**

The user is asking for:

- Shortening and editing the problem statement (structural/tone change on existing content)
- Reordering sections (structural change)

No new evidence, metrics, or sources are requested. No new factual claims introduced.

→ Revise from existing content.

______________________________________________________________________

## Skill response — Revised draft

# AI Sequence Writer — One-Pager

**Owner:** TBD **Date:** 2026-04-27 **Status:** Draft

## Strategic Alignment

- Sequences is a top-priority surface in the FY26 AOP under the "SDR Productivity" theme. *(Source: FY26 AOP — Jan 2026)*
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

| Metric | Type | Target |
|---|---|---|
| % of new sequences created via "AI Write" | Leading — adoption | ≥25% within 60 days of launch |
| Reply rate: AI-written vs. manually written | Lagging — quality | Within 0.5pp of manual baseline at 30 days |
| SDR sequence creation frequency, 30/60/90 days | Lagging — habit | Neutral or higher vs. pre-launch baseline |

ASSUMPTION: neutral-or-better reply rate is the v1 quality bar.

## Next Steps

| Step | Owner | Action |
|---|---|---|
| Validate time estimate | PM | 3–5 SDR interviews or Amplitude session timing data |
| Test prompt quality | PM + AI infra | Run prompt eval on 20+ personas before committing to launch scope |
| Legal review | PM + Legal | Submit AI-generated outbound email use case |
| Credits cost model | PM + Finance | Model credits burn at P50/P90 SDR usage |

______________________________________________________________________

**What changed:**

- User Problem section: condensed each bullet to one sentence; removed "staring at a blank editor" phrasing.
- Risks section moved above Success Metrics.

## Key Sources Used

- FY26 AOP — strategic planning doc — Jan 2026
- SDR Productivity Roadmap — Notion roadmap — Q1 2026

STATE: PRD_REVISION_READY
