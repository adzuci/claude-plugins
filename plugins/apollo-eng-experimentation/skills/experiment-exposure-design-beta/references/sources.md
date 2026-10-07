# Sources

Internal docs go stale — cite them as "what was documented as of <date>", and always confirm current
behavior with the user and the code.

## Internal (Apollo)

**Mechanics**

- Amplitude Experimentation + Leadgenie (May 2026) — https://app.notion.com/p/365ab2b3b49680998ec7f424d269c7f2
- Experimentation 101 (platform team, 2025) — https://app.notion.com/p/1b9ab2b3b4968024ba06d0ca3b160a2d
- System Diagrams (Jun 2025; partly superseded) — https://app.notion.com/p/113ab2b3b49680269290d2dd6dbba8c6
- Exposure vs Assignment Discrepancy Analysis (May 2026) — https://app.notion.com/p/36cab2b3b4968016b624e6e67bc821a2
- Exposures without Assignments — Spike & Options, ACT-4906 (Aug 2026) — https://app.notion.com/p/3c2ab2b3b4968039895bef704d6f5fe6
- Repo: `documentation/experiments.md`; PR #92934 (exposure console log); PR #102299 (groups payload on `$exposure`)

**Incidents / learnings**

- Experimentation Lifecycle — Issues Encountered so Far (Aug 31 2026) — https://app.notion.com/p/3cdab2b3b49680dab877d44355bd87b5
- Home Hub Reconciliation Rerun — SRM Investigation (Jun 2026) — https://app.notion.com/p/373ab2b3b496806aaef4dd9c40ec9f71
- Default Scoring 2.0 — A/B Experiment (Mar 2026) — https://app.notion.com/p/322ab2b3b49681e4913bf6080328bad4
- Growth Conversion Experiment Learnings (Through Q2 FY27) — https://app.notion.com/p/357ab2b3b4968150b361ffdb64c04977
- Growth Expansion Experiment Learnings (Through Q2 FY27) — https://app.notion.com/p/3c7ab2b3b4968171a3c4ce0b3ce1dd09

**Guidance / checklists**

- [Guide] Experiments: Pre-Launch Checklist for Technical Teams (Sep 2026) — https://app.notion.com/p/20eab2b3b496806da8e9fc378839d992
- How to set up a good experiment (Conversion, Aug 2026) — https://app.notion.com/p/34cab2b3b4968114a727f60946b7f6ee
- Experiment Template V3 (Aug 2026) — https://app.notion.com/p/387ab2b3b49680898747ffb55067a881
- [Guide] Estimating Experiment Duration (Jun 2025) — https://app.notion.com/p/208ab2b3b496804a93fff815d985e4d3
- Growth Acquisition — Experiments Tracker — https://app.notion.com/p/177ab2b3b49680599250c993534ef481

**A/A dry run**

- A/A (Dry Run) Testing deck, Growth Engineering (Aug 2026) — https://docs.google.com/presentation/d/1Zb2tjpAgtT56jqhWGMrbfm32phNWlWRUoz8YOBTk1Tg
- Jira template: "Assess and execute pre-launch exposure dry run (i.e. AA test)" — https://apollopde.atlassian.net/browse/ACT-4490
- Jira template: "Implement exposure point(s)" — https://apollopde.atlassian.net/browse/ACT-4528
- Onboarding Entry Exposure Test (A/A, Sep 2026) — https://app.notion.com/p/3e2ab2b3b4968111818bc37c9121fb70
- ACT-5142 "Check experiment eligibility and record exposure" — https://apollopde.atlassian.net/browse/ACT-5142
- Q3 Deliverables — Quality and Experimentation (Aug 2026) — https://app.notion.com/p/3a0ab2b3b4968089a900dd24790f3c56

## External (for deeper dives — offer, don't dump)

1. Amplitude — Event tracking: assignment vs exposure — https://amplitude.com/docs/feature-experiment/under-the-hood/event-tracking
1. Amplitude — Sample ratio mismatch causes — https://amplitude.com/docs/feature-experiment/troubleshooting/sample-ratio-mismatch
1. Amplitude — Exposures without assignments — https://amplitude.com/docs/feature-experiment/troubleshooting/exposures-without-assignments
1. Amplitude — Remote evaluation (property timing, cohorts) — https://amplitude.com/docs/feature-experiment/remote-evaluation
1. Amplitude — Variant jumping / identity — https://amplitude.com/docs/feature-experiment/troubleshooting/variant-jumping
1. Microsoft ExP — Diagnosing Sample Ratio Mismatch (KDD'19 taxonomy) — https://www.microsoft.com/en-us/research/articles/diagnosing-sample-ratio-mismatch-in-a-b-testing/
1. Microsoft ExP — Patterns of trustworthy experimentation: pre-experiment stage (counterfactual logging, randomization unit) — https://www.microsoft.com/en-us/research/group/experimentation-platform-exp/articles/patterns-of-trustworthy-experimentation-pre-experiment-stage/
1. Spotify Confidence — Trigger analysis (exposure timing, dilution) — https://confidence.spotify.com/blog/trigger-analysis
1. GrowthBook — Troubleshooting experiments (code-level rules) — https://docs.growthbook.io/kb/experiments/troubleshooting-experiments
1. GrowthBook — A/A tests — https://docs.growthbook.io/kb/experiments/aa-tests
1. Eppo — Where to assign (assign next to the branch) — https://docs.geteppo.com/sdks/best-practices/where-to-assign/
1. Kohavi et al. — Five Puzzling Outcomes (A/A, carryover) — https://notes.stephenholiday.com/Five-Puzzling-Outcomes.pdf
1. GrowthBook — Treatment effects: ITT vs LATE, selection bias — https://www.growthbook.io/blog/a-practitioners-guide-to-treatment-effects-in-experimentation-ate-cate-itt-late-att-explained
1. Kohavi, Tang & Xu — *Trustworthy Online Controlled Experiments* (book), ch. on triggering and SRM.

Where external guidance and Apollo practice differ (e.g. server-side exposure on assignment as
denominator), Apollo practice wins for this skill: expose client-side at the first visible divergence,
symmetrically; use a shared routing boundary when routing depends on variant.
