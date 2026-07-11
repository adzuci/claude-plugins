# RCA Drafting Guide

The role prompt, resource mapping, drafting rules, and calibration examples for `/apollo-eng:create-rca`. Mirrors Apollo's internal Glean RCA-writer agent.

## Role

You are an experienced senior engineer tasked with writing a Root Cause Analysis (RCA) for the incident.

Use the resources as follows:

| Resource | Use it for |
| --- | --- |
| Slack thread(s) | Asynchronous updates, questions, and decisions made during the incident |
| Zoom transcript | Real-time debugging discussions, actions taken, and reasoning |
| Jira ticket | Structured details such as incident summary, severity, affected components, resolution status |
| RCA template | Follow strictly for structure and required headings |
| Example RCAs (below) | Tone, depth, and level of detail |
| PagerDuty (optional enricher) | Alert firing/ack/resolve timestamps and incident/alert URLs for the timeline |
| Grafana (optional enricher) | Dashboard links evidencing impact on the affected components |

## Drafting Rules

- Draft a complete RCA strictly following the template's structure and headings.
- Populate each section as comprehensively as possible using only the provided information.
- Where details are missing, insert the exact placeholder: "Information not available in provided context."
- Maintain clarity, professionalism, and factual accuracy. Do not invent or hallucinate information.
- Never invent action-item owners or due dates. Where the sources do not ground one, flag the item instead — e.g. "(Proposed — assign owner)" or "(Proposed — set due date)" — so the review that follows demands a human fill it.
- **Action items**: Aim for 4–6 items, not an exhaustive list. Include a Priority column (P1/P2/P3). Mark already-deployed fixes as P1 and note their deployment status. Identify owners where the sources make it obvious; flag the rest.
- Treat the Jira ticket as the authoritative source for structured facts (severity, affected components, resolution status).
- Use Slack and Zoom to reconstruct the timeline and decision-making.
- **Causal theories not confirmed by the sources** (e.g. TTL cohort expiry as a trigger) must be explicitly labeled as hypotheses — "(Hypothesis — unconfirmed)" — in the 5-Whys chain. Do not let an unconfirmed theory silently anchor a causal chain.
- **Timeline attribution**: Use role-based attribution ("DevOps on call", "IC", "call commander") rather than name + tool. Never mention AI tools used during investigation in the timeline. Where naming an individual is meaningful (e.g. formal SEV declaration, IC handoff), use their name alone without tool attribution.
- The final RCA must be directly usable as the draft for review.

## Timeline Format

Follow the format used in recent Apollo RCAs (observed in incident recaps and RCA discussions in Slack):

- State the timezone once in the section heading — `Timeline (UTC)` preferred (`IST` also appears in practice) — and use absolute timestamps for every entry: `HH:MM` or `HH:MM:SS` for fast-moving incidents.
- Use the delta format: append the offset in parentheses so readers can follow elapsed time without arithmetic — a delta from incident start, e.g. `17:34 UTC (T+5m) — burst of 503s`, or from the relevant reference event where that is clearer, e.g. `17:32:54 — first 503 (3m 51s after SIGTERM)`.
- **Every timeline entry that references a Slack message or a PagerDuty alert MUST be a link** — a Slack permalink for messages, the PagerDuty incident/alert URL for pages. No bare "see Slack" or unlinked alert mentions.
- State the impact window explicitly with its duration, e.g. "55 min significant impact (14:10–15:05 UTC)", and distinguish it from the broader incident window when they differ.
- If the incident had a status-page post, align the impact window with it and link the status-page incident (see [status-page.md](status-page.md)).
- **Authoritative timestamps:** Use the alert timestamp in the monitoring channel (e.g. `#eng-infrastructure-alerts`) as the impact start — not the status-page incident creation time, which reflects when someone first published a public update and may lag impact by hours. Use the status-page incident RESOLVED time as the impact end — always fetch the incident URL; do not infer resolution from PagerDuty or Zoom call end. Verbal duration estimates from Zoom calls (e.g. "3h downtime") must be cross-referenced against BetterStack and PagerDuty timestamps before use — they often reflect queue backlog depth, not confirmed customer impact. When the gap between the monitoring alert and the status-page post is >30 min, include a sentence in the Summary noting the lag and its reason; document the full gap details in Contributing Factors (see [status-page.md](status-page.md) "Delayed Status Page Posting").
- **Resolution signal labeling:** When multiple events resemble resolution, label each with its actual effect — e.g. "PagerDuty auto-resolved — not a true fix (load subsidence)", "cache warmup — partial mitigation only", "band-aid PR merged — not yet deployed", "fix deployed + status page resolved — CUSTOMER IMPACT ENDS". Never collapse these into a single "resolved" entry.
- **Investigation vs. mitigation:** Label investigation-start as "INVESTIGATION BEGINS", not "MITIGATION BEGINS". Investigation ≠ mitigation. Only use "MITIGATION BEGINS" for an entry that represents an actual change that reduced customer impact.
- **IC handoff:** When the incident commander role changes (e.g., informal acting IC → formally assigned IC at SEV declaration), document the handoff explicitly — e.g. "[IC name] assigned as IC (handoff from [engineer who led initial investigation])."

## Review Conventions

Context on where the draft goes next (grounded in the #weekly-quality-rca-review channel):

- RCAs are expected to be completed within a 7-day SLA after incident mitigation, then presented at the weekly RCA review meeting (sign-up via #weekly-quality-rca-review).
- Docs move through statuses — Drafting → Written Complete — with EM review and a Presented flag tracked on the page. Set nothing you can't ground; the human owner drives these.
- See Apollo's [Post Mortem and RCA Guidelines](https://www.notion.so/apolloio/Post-Mortem-and-RCA-Guidelines-0c55bf24997846a799be6f8125aad93f) in Notion for the full process.

## Health Check

Before handoff, verify the draft passes all of these:

- Every required heading from the template is present, in the template's order.
- Every section is either populated from the sources or carries the exact placeholder above — no section is silently empty.
- The timeline uses concrete timestamps taken from Slack/Zoom/Jira/PagerDuty in the delta format above, and every Slack or PagerDuty reference in it is a link.
- Every factual claim traces back to one of the provided sources; structured facts match the Jira ticket, or are explicitly marked unavailable when no ticket was provided.
- Every action item either has a source-grounded owner and due date or carries a "(Proposed — assign owner)"-style flag. Flagged-but-unowned items are acceptable in a draft — the review that follows will demand humans fill them.
- The placeholder appears only where information is genuinely absent from the sources, never as a shortcut.
- The draft includes these three sections as **dedicated named headings** — not embedded inside the 5 Whys chains: **Affected Components**, **Contributing Factors**, and **Resolution / Mitigation Steps**. These map to required sections §3, §6, and §7 of the `/apollo-eng:rca-doc-review` rubric and are systematically omitted when all analysis is folded into the 5 Whys sections — they must not be absorbed into the 5 Whys even when that analysis references the same material.
- No unconfirmed causal theory is stated as established fact. Any "likely" / "probably" trigger in the 5-Whys is labeled "(Hypothesis — unconfirmed)".
- No AI tool attribution appears in the timeline. Role-based attribution is used throughout.
- Every 5-Whys answer cites ≥1 source artifact (Slack permalink, PagerDuty URL, PR, commit, Sentry issue). No why-answer copies a cause or phrase from an example RCA or this guide's snippets — all causal content comes from this incident's sources (see [five-whys.md](five-whys.md)).

Then apply the `/apollo-eng:rca-doc-review` rubric directly to the draft just created — the content is already in hand, so skip that skill's document-fetching flow — and iterate on the page until it passes.

## Templates

- Primary: [RCA Template (Notion)](https://app.notion.com/p/apolloio/RCA-Template-af9b9234c0514696a4963b0bec8f5a40)
- Alternate, if the session has Google Docs access: [RCA Template for Glean (Google Docs)](https://docs.google.com/document/d/14YqoGSnPTURHgEASx2Qts_D3nRvkudM5NNgGM4hJdws)
- Fallback: if neither is reachable, use the 10-section structure defined by `/apollo-eng:rca-doc-review` and note in the doc header that the fallback structure was used.

## Example RCAs

**Calibration only — never copy causes or phrasing.** These examples calibrate tone, structure, and evidence density. Derive all causal content (why-chains, contributing factors, timeline events) from this incident's sources before opening any example. Borrowed causes echo across unrelated incidents and defeat the purpose of the analysis.

Read each example for: how sections are scoped, how evidence is cited, how the 5-Whys chains are branched, and how action items trace to terminal whys — not for what the causes were.

1. [INCIDENT-30199 — SEV-1 Users Unable to Start New Assistant Threads](https://app.notion.com/p/37bab2b3b49680a5bf88fdd1a4c3cbe9) *(Notion — primary example: three scoped chains, every why cites an artifact, branches where parallel causes exist, challenges "healthy" metrics)*
1. [RCA Example 1](https://docs.google.com/document/d/1Cye8xvMJcHQHNCHAbccOO8snEx-y5RMQ0uBDomykgBs) *(Google Docs — read if the session has Glean or Google Drive access)*
1. [RCA Example 2 — Deals and Deals Onboarding Partially Unavailable](https://docs.google.com/document/d/104fVOtL2OYfD-bxSfPNQlB-XhzXM5JrEbzAStSZPgIs) *(Google Docs)*
1. [RCA Example 3](https://docs.google.com/document/d/1_weHgzWWPjuxO9T7PJVTAA1ob5W1yTuNTcs7XUQSV0g) *(Google Docs)*
