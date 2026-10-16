# Synthesizer Agent Contract — Phase F Primitive

> **Status**: Phase F primitive contract. Specifies the interface; implementation is Phase F MVP work.
>
> **Binding**: when the descriptor schema gains the `synthesizer:` block (Phase F), this contract defines its inputs, outputs, decision rubric, and disagreement-escalation behavior.

---

## What a synthesizer is

A synthesizer is a first-class agent type that takes outputs from N sub-agents and produces ONE recommendation with reasoning trace and explicit dissent annotation. It is the "tech lead" role in a team-of-agents.

A synthesizer is NOT:
- A manager. It doesn't direct sub-agents; it reads their outputs.
- An autonomous decider. It always escalates to a human on substantive disagreement.
- A meta-skill. It's a primitive — declared in the Pantheon descriptor, not a SKILL.md.

---

## Inputs

The synthesizer receives a structured envelope per run:

```yaml
synthesizer_input:
  artifact:
    kind: pull_request           # pull_request | incident | feature_spec | …
    id: "apolloio/leadgenie#87432"
    summary: "<artifact body, redacted per value-patterns.md>"
    diff_url: "https://api.github.com/repos/apolloio/leadgenie/pulls/87432.diff"
  refs: {head: "<sha>", stack_tip: "<sha or null>"}
  snapshot_root: "<run_dir>/snapshots"   # git show <ref>:<file> for every cited file; the only evidence source
  sub_agent_outputs:
    - role: frontend-reviewer
      version: v2.1.4
      verdict: APPROVE | REQUEST_CHANGES | BLOCK
      confidence: 0.0..1.0
      findings:
        - severity: blocker | major | minor | nit
          category: <skill-defined>
          file: assets/...
          line: 42
          ref: "<sha the reviewer read the file at>"
          claim: "<one-sentence finding>"
          evidence: "<quoted snippet or rule-citation>"
      narrative: "<≤500 word reasoning>"
    - role: backend-reviewer
      version: v1.7.0
      verdict: REQUEST_CHANGES
      confidence: 0.78
      findings: [...]
      narrative: "..."
    - role: db-perf-reviewer
      version: v0.9.3
      verdict: BLOCK
      confidence: 0.91
      findings:
        - severity: blocker
          category: index_scan_risk
          claim: "Query on contacts.email without index; T0 collection"
          evidence: "..."
      narrative: "..."
  feature_memory:
    feature_id: "apolloio/leadgenie#87432"
    prior_decisions:
      - run_id: pr-review-bot-2026-04-22-...
        synthesizer_verdict: REQUEST_CHANGES
        kept_findings: [...]
        author_response: "addressed in commit f3a9c"
    prior_runs_count: 3
  rubric_overrides: []   # per-harness customizations; usually empty
```

Required fields: `artifact`, `sub_agent_outputs` (≥2 entries; synthesizer doesn't fire on single-reviewer runs).

---

## Decision rubric

The synthesizer applies a standard rubric in priority order:

0. **Severity floor (applied before everything else).** Drop every finding whose `severity ∈ {nit, minor}` into `findings_dropped` with `dropped_reason: "severity_below_floor"` BEFORE evaluating any other rule, **unless its `category ∈ {correctness, compliance, data_loss, wiring, test_gap, perf, repo_convention}`**: those are kept and rendered at the reviewer's severity (they count toward the verdict only at `major`). Only `blocker` and `major` findings influence the verdict.

   Why the exemption (2026-10-08): on the Ads backend stack the reviewers found the limit-before-sort bug, a spec that stubbed the unit under test, and one-by-one upserts, filed them `minor`/`nit`, and the floor dropped them; a human found them a week later (a past Ads backend review, doc 44 §5).

   Two carve-outs:
   - **Cluster exception**: if ≥3 `minor`/`nit` findings share the same `category` AND span ≥2 files, promote ONE consolidated finding to `major` (`promoted_from: cluster`). This catches systemic issues without spamming.
   - **Author opt-in**: if the PR carries the label `review:all-findings`, lift the floor and keep `minor`/`nit` findings too. Default is OFF — reviewers must opt in to thoroughness.

   Rationale: false positives on nice-to-haves are the dominant failure mode of automated reviewers — they erode trust and train authors to ignore the bot. A small number of high-signal comments is strictly better than a thorough audit.

1. **Any sub-agent reports a blocker with confidence ≥0.85** → verdict = `BLOCK`. Cite the agent + finding.
2. **Two or more sub-agents report `REQUEST_CHANGES` and findings overlap** (same file/line region or same category) → verdict = `REQUEST_CHANGES`. Consolidate findings.
3. **Sub-agents report different non-blocker verdicts** (e.g., one APPROVE, one REQUEST_CHANGES on `major`) → verdict = `REQUEST_CHANGES`, but flag as `synthesizer_low_confidence: true` for human review. (Note: post-floor, "non-blocker" means `major` only — `minor`/`nit` already dropped.)
4. **Sub-agents report contradicting blockers** (one says BLOCK on perf, another says APPROVE without seeing the perf finding) → escalate to `ESCALATE_HUMAN` (do NOT auto-decide). This is the disagreement gate.
5. **All sub-agents APPROVE** → verdict = `APPROVE`.
6. **All remaining findings (post-floor) are `major` with confidence <0.85 AND no overlap across sub-agents** → verdict = `APPROVE`. Surface the findings inline but do not block; isolated `major` from a single reviewer is advisory. **Except** a `major` in `correctness`, `compliance`, `data_loss` or `wiring`: verdict `REQUEST_CHANGES` with `synthesizer_low_confidence: true`.

The rubric is intentionally simple. Phase F MVP picks this; Phase F refines via eval corpus.

---

## Outputs

```yaml
synthesizer_output:
  verdict: APPROVE | REQUEST_CHANGES | BLOCK | ESCALATE_HUMAN
  confidence: 0.0..1.0
  rationale: "<≤200 word synthesis>"
  findings_kept:
    - source_role: db-perf-reviewer
      finding_id: "<sub-agent's finding ID>"
      kept_reason: "blocker on T0 collection; rule cap_review_size_at_400_lines"
  findings_dropped:
    - source_role: frontend-reviewer
      finding_id: "<sub-agent's finding ID>"
      dropped_reason: "duplicate of backend-reviewer's finding on same file"
  dissent:
    - role: frontend-reviewer
      stance: APPROVE
      synthesized_stance: REQUEST_CHANGES
      explanation: "FE reviewer didn't see the backend regression on line 412 of api.controller.ts"
  feature_memory_writes:
    - kind: synthesizer_decision
      payload: { verdict: ..., confidence: ..., kept_findings_count: ... }
  human_escalation_payload:    # only if verdict == ESCALATE_HUMAN
    summary: "Sub-agents disagree on perf risk; need human read"
    dissent_table: "..."       # markdown table of role|verdict|claim
    suggested_decider: "<team handle from CODEOWNERS for affected files>"
```

The output is single-source-of-truth for downstream consumers (PR comment template, feature_memory writer, downstream harness nodes in a DAG).

---

## Disagreement gate (the load-bearing piece)

The synthesizer ESCALATES to a human when:

- Two sub-agents reach contradicting hard verdicts (BLOCK vs APPROVE on the same artifact)
- Confidence delta between two sub-agents on the same finding > 0.30
- A sub-agent reports a `severity: blocker` that another sub-agent's narrative explicitly endorses as safe
- The synthesizer's own confidence is < 0.60

Escalation never auto-decides. The escalation payload (`human_escalation_payload`) is rendered into a Slack-ready summary so the human deciding doesn't re-read 5 review threads.

**Bias toward escalation**: false escalations are cheap (a human glances and approves); missed escalations are expensive (a regression ships). Phase F eval threshold: disagreement-escalation precision ≥ 0.95.

---

## Audit trail

Every synthesizer run emits to `analytics.synthesizer_decisions`:

| Column | Type | Purpose |
|---|---|---|
| `run_id` | string | Tied to harness_runs |
| `artifact_kind` | string | pull_request / incident / etc. |
| `artifact_id` | string | |
| `synthesizer_version` | string | semver |
| `sub_agent_count` | int | |
| `verdict` | enum | |
| `confidence` | float | |
| `escalated` | bool | |
| `dissent_count` | int | |
| `prior_decisions_consulted` | int | from feature_memory |
| `wall_time_ms` | int | |
| `tokens_used` | int | |
| `human_decider_login` | string | populated if escalated and resolved |
| `human_resolution_at` | timestamp | when human decided |
| `human_resolution_verdict` | enum | for eval scorecard: did synthesizer guess correctly? |

The `human_resolution_verdict` is the eval ground-truth for synthesizer precision. After 90 days of human-resolved escalations, we have a real-world precision number.

---

## Eval corpus (Phase F MVP requirement)

`eval/synthesizer/` ships with ≥30 cases:

- 10 cases where all sub-agents agree → assert verdict matches; assert no escalation
- 10 cases with minor disagreement → assert verdict = `REQUEST_CHANGES` with consolidated findings
- 5 cases with hard disagreement → assert verdict = `ESCALATE_HUMAN`
- 5 adversarial cases (one sub-agent fabricates a finding) → assert synthesizer drops fabricated finding whose snapshot contradicts it
- 3 cases where the cited file exists only at `stack_tip` or is absent from the working tree → assert the finding is kept (checked against its ref's snapshot, or `evidence_unverified: true` when there is none), never dropped

**Evidence rule.** The synthesizer checks evidence only against `snapshot_root/<ref>/<file>`, never the
working tree. It drops a finding for evidence only when the snapshot exists and contradicts the claim;
a missing snapshot, unknown ref or out-of-range line keeps the finding with `evidence_unverified: true`.

Replay-eval gate: precision ≥ 0.85 on verdict, precision ≥ 0.95 on disagreement detection.

---

## Anti-patterns

- **Synthesizer that "splits the difference."** Never average between BLOCK and APPROVE. Either escalate or pick a side with clear rationale.
- **Synthesizer that ignores prior decisions.** If feature_memory shows the same finding was raised + addressed in run N-1, the synthesizer must read that and not re-raise.
- **Synthesizer with no dissent annotation.** Even on APPROVE, if any sub-agent dissented, capture it. Hidden dissent breaks audit.
- **Multiple synthesizers per harness run.** One synthesizer per run; that's the "single tech lead" property.
- **Synthesizer making decisions outside its rubric.** The rubric is the contract. New decision types require descriptor + rubric update + eval cases.

---

## Composition with other Phase F primitives

| Primitive | Interaction |
|---|---|
| F2 Pantheon DAG | Synthesizer is one node type; DAG schema defines `kind: synthesizer` |
| F3 Feature memory | Synthesizer reads prior decisions; writes synthesizer_decision entries |
| F4 State machine | Synthesizer's verdict drives state transitions (APPROVE → ready_to_ship **only when `incomplete_roles` is empty**, ESCALATE → blocked_on_human; an INCOMPLETE role never reaches ready_to_ship) |
| F5 Stand-up harness | Stand-up reads `analytics.synthesizer_decisions WHERE escalated = true AND human_resolution_at IS NULL` to surface stuck items |

---

## Phase F kickoff requirements

- [ ] This contract ratified by SSG
- [ ] Synthesizer eval corpus ≥30 cases scaffolded
- [ ] Decision rubric reviewed by 2+ engineers (FE + BE) for completeness
- [ ] `analytics.synthesizer_decisions` schema landed
- [ ] Vertical proof-point (PR-review-bot synthesizer) DAG drafted
