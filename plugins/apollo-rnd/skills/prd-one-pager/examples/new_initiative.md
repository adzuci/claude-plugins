# Example: New Initiative — AI Sequence Writer

This example shows the full flow for a new PRD: orientation pass, hypothesis-first intake, research, and first draft.

> **Note:** All URLs in this example are illustrative placeholders, not real Apollo internal links.

______________________________________________________________________

## User invocation

```
/prd-one-pager AI-powered sequence writer for SDRs
```

______________________________________________________________________

## Skill response — Orientation + Intake

*(Skill runs a lightweight Notion search for "sequence writer AI SDR" and "AI sequences roadmap" before asking questions. Finds: FY26 AOP mentions "AI-assisted outreach" as an H2 investment area; SDR Productivity Roadmap references template suggestions but no full sequence generation. Existing AI infrastructure: AI credits system is already live.)*

> **My hypothesis:** This is a net-new capability in the Sequences surface — Apollo has template suggestions today but no full AI-generated sequences. Primary users are probably SDRs. This likely touches the AI credits system and the existing Sequence creation flow. Correct me where I'm wrong.
>
> Before I research, a few quick questions:
>
> 1. **Net-new vs. rework** — Sounds net-new, but is there a specific existing feature (e.g., template suggestions) this would replace or supersede?
> 1. **Initiative + desired outcome** — What should the AI do exactly, and what does success look like at 60 days? (e.g., "SDRs adopt it over manual copy-paste" vs. "measurable reply rate lift")
> 1. **Users, pain, and scope** — Primary user SDRs — confirmed? What's the core pain? Any constraints (latency, model cost, must use existing AI infrastructure)?
> 1. **Links** — Any Notion specs, Slack threads, or prior PRDs I should pull before drafting?

______________________________________________________________________

## User response

> 1. Net-new. Template suggestions stay; this is additive.
> 1. SDR pastes in a prospect's company + persona, AI writes a 4–6 step outbound sequence. Success = SDRs adopt it over manual copy-paste and reply rates are neutral or better.
> 1. Yes, SDRs. Pain: they spend 20–30 min per sequence customizing templates. Constraint: must use existing AI credits system, can't add new LLM vendor. No prior PRDs — greenfield.
> 1. No links. Keywords: sequence writer, AI outbound, SDR productivity.

______________________________________________________________________

## Skill response — Draft

*(Skill searches: FY26 AOP, SDR/Sequences roadmap, Sequences VoC Notion docs, prior AI feature PRDs. Amplitude/Hex not searched — user did not ask for metrics or usage data.)*

______________________________________________________________________

I know this is more than a one-pager. I'm giving you a fuller first pass so you can see the strategic shape, evidence, risks, and possible paths forward — then we can tighten it into something you're excited to share with the team.

**Review note:** I've labeled assumptions, inferences, and source-backed claims, but you're responsible for verifying the final PRD, metrics, citations, and strategy before sharing.

______________________________________________________________________

# AI Sequence Writer — One-Pager

**Owner:** TBD **Date:** 2026-04-27 **Status:** Draft

## Strategic Alignment

- Sequences is a top-priority surface in the FY26 AOP under the "SDR Productivity" theme. \[Source: [FY26 AOP](https://notion.so/apollo/fy26-aop), Jan 2026\]
- AOP calls out AI-assisted outreach as a key H2 FY26 investment area. \[Source: [FY26 AOP — H2 Investment Areas](https://notion.so/apollo/fy26-aop#h2-investments), Jan 2026\]
- INFERENCE: this initiative is the most direct expression of the AOP's AI-assisted outreach bet for SDRs — based on FY26 AOP focus areas, though the AOP does not name the AI Sequence Writer specifically.
- Uses existing AI credits infrastructure; no new vendor dependency required.

## User Problem + JTBD

- **Who:** SDRs, primarily outbound, who build sequences from scratch or by modifying templates.
- **Stuck in:** The sequence creation step — they have a target account and persona but face a blank or partially-filled editor.
- **Pain:** 20–30 minutes per sequence spent manually customizing templates for each prospect vertical and persona. ASSUMPTION: estimate provided by PM — not yet validated against usage data or session timing.
- **Aha moment:** First fully AI-written sequence that's good enough to send with minor edits — under 2 minutes.
- **Behavior change:** SDRs stop treating sequences as a manual writing task and start using AI Write as the default entry point.
- **If we get it wrong:** SDRs try it once, get a generic output that doesn't match their ICP, and never return — deepening distrust of AI features on the platform.

## Users + Use Cases

**Primary:** SDRs (inbound + outbound)

1. SDR opens a new sequence for a SaaS AE persona, pastes in company context, gets a ready-to-send 5-step email sequence with subject lines.
1. SDR edits 1–2 generated steps to add a personal touch, sends without rewriting from scratch.
1. SDR manager reviews AI-generated sequences for quality before enabling for the team.

## Proposed Solution

Add an **"AI Write"** entry point in the Sequence creation modal. SDR provides: target persona, company type or vertical, optional tone preference. The system uses the existing AI credits infrastructure to generate a 4–6 step sequence with subject lines and body copy. All steps are editable before saving.

**Why this over alternatives:**

| Alternative | Why not |
|---|---|
| Improve template suggestions (existing) | Doesn't solve the blank-editor problem — still requires SDR to write |
| Standalone AI writing tool outside Apollo | Breaks the flow; SDR still has to import back into sequences |
| Full agentic sequence creation (end-to-end) | Higher complexity, higher latency, out of scope for v1 |

[NEEDS INPUT: Does "AI Write" replace the "Start blank" option or sit alongside it in the creation modal?]

## Requirements

- Integrates with existing AI credits system — no new LLM vendor.
- Supports 4–6 step sequences; step count configurable.
- Input: persona description, company type or vertical, optional tone.
- Output: subject line + body copy per step, editable inline.
- Latency: [NEEDS INPUT: acceptable generation time? Under 5 seconds? Under 10?]
- Respects existing sequence length limits and compliance guardrails.

## Success Metrics + Validation

| Metric | Type | Target |
|---|---|---|
| % of new sequences created via "AI Write" | Leading — adoption | ≥25% within 60 days of launch |
| Reply rate: AI-written vs. manually written | Lagging — quality | Within 0.5pp of manual baseline at 30 days |
| Time to first send | Leading — efficiency | [NEEDS INPUT: baseline not yet established] |
| SDR sequence creation frequency, 30/60/90 days | Lagging — habit | Neutral or higher vs. pre-launch baseline |

ASSUMPTION: neutral-or-better reply rate is the v1 quality bar — AI sequences do not need to outperform manual ones at launch.

## Risks, Tradeoffs, and Decisions Needed

| Decision / risk | Why it matters | Current recommendation | Owner / next action |
|---|---|---|---|
| Generic output kills trust | SDRs who get low-quality output on first use will not return | Require persona + company type as mandatory inputs; test prompt quality before shipping | PM + AI infra |
| AI credits cost at P90 SDR usage | High-volume SDRs could exhaust credits faster than expected | Model cost at P90 before committing to unlimited credits per sequence | PM + Finance |
| Compliance: AI-generated email content | Regulated verticals may have legal constraints on AI-authored outbound | Legal review before GA; add opt-out for regulated accounts | PM + Legal |
| Cannibalization of template upsell | AI Write may reduce engagement with paid template packs | [NEEDS INPUT: check with Growth/Monetization] | PM + Growth |

## Next Steps

| Step | Owner | Action |
|---|---|---|
| Validate time estimate | PM | 3–5 SDR interviews or Amplitude session timing data to confirm 20–30 min/sequence claim |
| Test prompt quality | PM + AI infra | Define persona/vertical input contract; run prompt eval on 20+ SDR personas before committing to launch scope |
| Legal review | PM + Legal | Submit AI-generated outbound email use case for review |
| Credits cost model | PM + Finance | Model credits burn at P50/P90 SDR usage before finalizing free-tier vs. metered approach |

______________________________________________________________________

**How to work with this from here:**

- Tell me what's directionally right or wrong — rough notes are fine.
- Say "revise without search" for wording, structure, scope, or tone edits.
- Say "find evidence" when you want me to search Notion, Amplitude, Hex, Drive, Enterpret, or Slack.
- Paste links, screenshots, docs, metrics, or messy notes if you already have them.
- Most useful inputs: target user, v1 surface, desired outcome, out-of-scope items, known constraints, decision-makers.
- I can keep this broad for strategy alignment or tighten it into a one-page exec-ready PRD.

______________________________________________________________________

**Feedback questions:**

1. What did I get directionally right?
1. What did I get wrong, overstate, or miss?
1. What should we optimize for next: sharper strategy, tighter scope, stronger evidence, or a cleaner exec-ready one-pager?

## Key Sources Used

- [FY26 AOP](https://notion.so/apollo/fy26-aop) — strategic planning doc — Jan 2026
- [SDR Productivity Roadmap](https://notion.so/apollo/sdr-productivity-roadmap) — Notion roadmap — Q1 2026
- Sequences VoC Interviews — Notion research doc — Feb 2026 [NEEDS SOURCE LINK: confirm Notion URL with research team]

STATE: PRD_DRAFT_READY
