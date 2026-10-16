# 18 — Traceability against the original brief

> Does the design still do what was asked? Checked before moving to BUILD.
> Three outcomes per line: **covered**, **deviated** (deliberate, with a reason), or **gap** (not done).

## Scorecard

| # | Original requirement | Status | Where it lives |
|---|---|---|---|
| 1 | Researcher agent, to research if required | **Covered** | Stage B, four evidence types. "If required" is the existence precondition |
| 2 | PM builds PRD if required | **Covered** (late) | Stage C: four analysts, then a PRD author. This was missing until §2.1 of doc 17 |
| 3 | Design builds a prototype if required | **Covered**, refined | Stage D: read Figma → generate in Fabric Studio → check. Figma is canonical, Fabric Studio (`apolloio/fabric-studio`) is the workbench since 2026-09-18; Claude Design was the first workbench and was replaced because it imitated Fabric instead of using it |
| 4 | Staff eng + tech lead + EM + architect review | **Deviated** | Stage E: four reviewers decomposed by *what they check*, not by title. EM role preserved as the orchestrator/DRI |
| 5 | Share and consolidate each other's points, take each other's approval | **Deviated** | Consolidation via the orchestrator; mutual approval deliberately minimised |
| 6 | Once plan approved, back to PM and design for approval | **Covered** | Cycle routing table: E-panel scope findings → C, design findings → D |
| 7 | Engineers: frontend, backend, **devops** — multiple agents, e.g. 2 FE + 3 BE | **Partial — devops is a gap** | Stage F has slice owners, contract keeper, integrator. **No devops or infra surface exists anywhere** |
| 8 | QA agents: bug bash, test every flow from UX and functionality | **Partial** | Stage G named and composed from existing skills, but never designed in depth |
| 9 | Code review agents, reusing the existing review framework | **Covered** | `backend-reviewer`, `frontend-reviewer`, `security-reviewer`, `db-perf`, `pr-tech-lead-synthesizer` |
| 10 | Review agents consolidate and mutually agree via approvals | **Deviated** | Same as #5 |
| 11 | "If required" means only when it does not already exist | **Covered** | Existence precondition plus the author/gap-fill mode split, applied consistently across FIND, Specify and Design |
| 12 | All of it needs human approvals | **Covered** | G0, G1a, G1b, G2a, G2b, G3, G4, G5, enforced by hooks the model cannot override |
| 13 | Learn from pushback; possibly another agent for it | **Deviated + unbuilt** | Stage H designed, ledger schema written, **not wired**. Built as a mechanism, not an agent |
| 14 | Explore existing open-source frameworks | **Covered** | BMAD-METHOD, GitHub Spec Kit, MetaGPT, ChatDev researched; what was taken and what was rejected is recorded |

## The three deviations, and why

### #4 — seniority titles replaced by what each reviewer checks

Asked for: staff engineer, tech lead, EM, architect.
Built: seam reviewer, data-model reviewer, failure-mode reviewer, blast-radius reviewer.

**Reason.** Four titles reviewing the same artifact produce correlated judgment. Strong role framing measured statistically indistinguishable from baseline, and persona injection showed no improvement across tasks. Four job titles on one model is four articulate agents agreeing.

Decomposing by *what is checked* gives genuinely different questions with different evidence — which is the shape that actually works.

**The EM role is not lost.** It became the orchestrator: staffing, sequencing, unblocking, adjudicating disputes. That is what the role does; it was the wrong thing to model as a reviewer.

> **Resolved 2026-09-06.** This deviation was partly a misreading. What was meant is PR-review-style push-back: different models reading the same work and raising objections. That is fully supported and is now specified in [19-adversarial-review](./19-adversarial-review.md). The rule is **agents may block, not bless** — a finding is checkable and useful, an approval is unfalsifiable and degrades the next reviewer. Autonomy comes from auto-block on deterministic failures and auto-pass when checks pass with no evidenced findings; only genuine disagreement escalates. The text below records the original reasoning.

### #5 and #10 — agents do not approve each other

Asked for: agents share points, consolidate, and take each other's approval.
Built: agents produce; **artifacts** cross-check each other; the orchestrator consolidates; disagreement escalates to a human.

**Two reasons, one structural and one measured.**

Structural: sub-agents cannot message each other. There is no channel. Consolidation has to pass through the supervisor regardless of what we would prefer.

Measured: on high-quality work, **83% of agentic reviewer errors were false approvals**. And an upstream agent asserting "this is correct" measurably collapses downstream detection — labelling work as already-verified dropped detection by up to 93.5pp in one test. So mutual approval is not merely weak, it is actively harmful: each approval degrades the next reviewer.

What replaced it: reviewers blinded from each other and from upstream verdicts, one mandated adversary, escalate on disagreement rather than vote it away, and — the part that actually works — **three artifacts covering one fact beat three agents opining on it**, because documents written at different times by different people fail independently in a way same-model agents do not.

### #13 — learning is a mechanism, not an agent

Asked for: possibly another agent to learn from pushback.
Built: a ledger that records every rejection, routed into domain-owner knowledge files.

**Reason.** An agent that learns is hard to audit — you cannot diff what it concluded. A ledger is a file: appendable, reviewable, and it doubles as the eval corpus. And the field's evidence points the same way; the pattern with real support is rules derived from accepted human outcomes stored as a version-controlled file, not weights.

**Caveat, stated plainly: this is designed and not wired.** The schema exists, nothing writes to it yet, and until it does the harness does not learn.

## The two real gaps

> **Closed 2026-09-06.** Specified as the deployment surface in [20-build-stage](./20-build-stage.md) §6, with five deliverables produced *during* BUILD: rollout plan with flag and kill switch, migration sequencing, feature-specific monitoring, runbook, and capacity/cost. Plus §7, which hands those to the existing on-call harness — a feature is done when on-call can handle it, not when it merges. Original text below.

### Gap 1 — devops and infrastructure are absent

The brief named "frontend, backend, devops." There is no devops surface in any archetype, no infra reviewer in Stage E, and no deployment concern anywhere in Stage F.

What is missing concretely:

- **Rollout strategy** — feature flag, percentage ramp, kill switch
- **Migration sequencing** — which migration runs when, and what is not safe to run concurrently
- **Monitoring and alerting for the new feature** — not generic observability, but "what does broken look like for this thing"
- **Runbook** — what on-call does when it breaks at 3am
- **Capacity and cost** — new queries, new workers, new external API quota

Blast-radius review touches migrations and reindexes, so the *risk* is partly visible. But nothing plans the rollout or hands anything to on-call. For a team that already runs an on-call autopilot, that is a strange hole.

**Recommendation: fold this into the BUILD deep dive** rather than making it a separate stage. Deployment is part of shipping, not a phase after it.

### Gap 2 — QA is named but not designed

Stage G is listed as "wraps `end-to-end-bug-bash`, reviewer sub-agents" and has never been worked through. The brief asked for two distinct things and only one is obviously covered:

- **Functional testing** — does it do what the acceptance criteria say
- **"Test every flow from UX"** — can a person actually complete the task

The second is closer to usability validation than to functional QA, and it needs the design's required-state list to test against. Worth its own deep dive after BUILD.

## What this means for BUILD

Two of the fourteen lines are genuine gaps, and one of them (devops) belongs inside BUILD. So the next deep dive should cover Stage F **plus** the deployment surface, rather than treating them separately.

The three deviations are all in the same direction: **less trust in agents evaluating agents, more trust in artifacts and deterministic checks.** That is a real departure from the brief's mental model, and it is the single most important thing to agree or reject before going further — because everything from Stage E onward is built on it.
