# Format reference — Macro Funnel section

## The doc's own instructions

The Macro Funnel template carries these instructions at the top of every section. They're the
contract you're writing against.

> **Goal:** Quick, high-signal check-in on only experiments driving our key metrics. Keep it
> short, metric-focused, and action-oriented: what's live, what shipped, what concluded, what's
> next, and any blockers.
>
> **What isn't a hit?** It's not a project, or BAU, or homework, or something you'd skip over.
> It's okay to not have any hits this week. No deep dives or homework, just the hits.
>
> **Top 3 Hits.** Pick your top 3 hits to share. Tell us why they're the most important
> (testing/learning). Label each with one of: 🏁 **Concluded:** / 🚀 **Launched/Kicked:** /
> 🔬 **Live:** / 🔁 **Coming Up:** / 🚩 **Blockers / Flags:**
>
> **Notable Mentions.** Still list experiments which are hits, just not in the Top 3. We will
> only discuss the Top 3.
>
> **💡Top Takeaway.** One line: biggest learning or momentum driver this week.

Note the emoji list is prescriptive. Every bullet gets one.

## Worked example — Growth Conversion

This is a real week, tightened to the format. Notice: three hits with a verdict or a number in
each, five mentions that are mostly one line, and a takeaway that hands the room an action.

```markdown
## Growth Conversion

**Top 3 Hits**

1. 🏁 **Concluded:** [Streamline End of Trial Modal](https://app.notion.com/p/Streamline-End-of-Trial-Modal-32fab2b3b49681f588eccbf5855d5baf) — Won after 21 days: +18.4% new customers (92.6% sig), +28.2% new ARR (96% sig), +678% admin request gate clicks. Launched Jul 29.
2. 🔬 **Live:** [Trial Preview Flyout on Upgrade Button Hover](https://app.amplitude.com/experiment/apollo-io/241072/config/1208574/activity) — 27 days in, 10.8k teams exposed. Trending positive (+10.3% new customers, +31.8% annual purchases) but may not reach sig. Re-evaluating Thursday.
3. 🚀 **Launched:** [Re-enable manual basic trials](https://app.notion.com/p/Re-enable-manual-basic-trials-3a7ab2b3b49681a39af8f93892cbb6ab) — Went live today after the freemail-exclusion rework. Watching trial CVR on the non-freemail cohort.

**Notable Mentions**

- 🚩 **Blockers / Flags:** [Advanced Dialer add-on direct purchase at gate](https://app.notion.com/p/Advanced-Dialer-add-on-direct-purchase-at-gate-33cab2b3b49681bda29ef00a60ed5e5d) — Off track. QA before rollout slipped a week on my end.
- 🔁 **Coming Up:** [End of trial simplified /upgrade flow](https://app.notion.com/p/End-of-trial-simplified-upgrade-flow-380ab2b3b4968055a829d5cdb64bc647) — Target Aug 6. Revising on early feedback.
- 🔁 **Coming Up:** [HubSpot Starter CRM in-app offer](https://app.notion.com/p/HubSpot-Starter-CRM-in-app-offer-3a6ab2b3b496818b9093e64f7789b3f0) — Target Aug 10. Content drafted, needs design before build. Waiting on the customer list.
- 🔁 **Coming Up:** [CSV Enrichment Try Before You Buy Preview](https://app.notion.com/p/CSV-Enrichment-Try-Before-You-Buy-Preview-344ab2b3b49681a1aa3bfddaafd18358) — Target Aug 12. Ready to build.
- 🔁 **Coming Up:** [Trial Getting Started Springboard + Checklist](https://app.notion.com/p/Trial-Getting-Started-Springboard-Checklist-344ab2b3b4968148b188ee8ad62140d2) — Target Aug 12. Looking for a smaller checklist version while the joint onboarding-questions work lands.

**💡Top Takeaway**

- The non-admin request flow is the ripest follow-up we have: pitch us your best ideas.
```

## What a weak version of the same week looks like

Useful to recognize, because these are the failure modes that actually show up.

- **Four hits, or three where the third is "Ready to build."** The third slot is where padding
  hides. Cutting it is a valid, often better, answer.
- **Bare initiative names.** No link means nobody in the room can check the claim.
- **A stat dump.** "+18.4% new customers, +28.2% new ARR, +678% gate clicks, 92.6% / 96% / 100%
  sig, 10.8k exposed, 21 days" in one line. Pick the one or two that carry the verdict.
- **Coming Up repeated verbatim from last week.** If nothing changed, it isn't news.
- **A takeaway that floats free.** "Lots of momentum this quarter" doesn't come from any bullet
  above it and gives the room nothing.
