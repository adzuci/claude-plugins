# Pantheon DAG Schema — Phase F Primitive

> **Status**: Phase F primitive contract. Specifies the multi-step harness DAG schema; implementation lands Phase F MVP.
>
> **Binding**: when descriptors gain the `dag:` block (Phase F), this schema defines node kinds, edge semantics, persistent run-state, and execution rules.

---

## Why DAG, not single-skill

Phase A–E harnesses are single-skill: one trigger fires one skill, which fans out to ≤N sub-agents, which return findings to one synthesizer. That's a star, not a DAG.

A DAG is required to model real engineering team workflows:
- "Frontend reviewer + backend reviewer run in parallel, THEN tech-lead synthesizes, THEN if escalated, route to human, THEN on resolution route to merge-checker."
- "Incident triage runs first; if root cause is DB, fan out to db-perf agent; otherwise fan out to app agent; merge findings; page on-call."
- "Capacity plan runs daily; on breach, fan out to forecast agent + cost agent; synthesizer decides; if approved, file JIRA; if rejected, archive plan."

Star topology can't express:
- Sequential dependencies between sub-agents
- Conditional fan-out
- Loops with break conditions ("re-review until approved or 3 attempts")
- Persistent intermediate state across nodes

DAG is the abstraction that fits.

---

## Schema: descriptor `dag:` block

```yaml
spec:
  dag:
    nodes:
      - id: fe_review
        kind: skill_invocation
        skill: code-review
        skill_version: v2.1.4
        config:
          scope: frontend
        inputs_from: [trigger]
        outputs_to: [synthesize]

      - id: be_review
        kind: skill_invocation
        skill: code-review
        skill_version: v2.1.4
        config:
          scope: backend
        inputs_from: [trigger]
        outputs_to: [synthesize]

      - id: db_perf_review
        kind: skill_invocation
        skill: db-perf-reviewer
        skill_version: v0.9.3
        inputs_from: [trigger]
        outputs_to: [synthesize]
        run_if: "trigger.diff.touches_path('app/models/**') OR trigger.diff.touches_path('packs/*/models/**')"

      - id: synthesize
        kind: synthesizer
        synthesizer_version: v1.0.0
        inputs_from: [fe_review, be_review, db_perf_review]
        outputs_to: [route_decision]

      - id: route_decision
        kind: gate
        gate_kind: deterministic
        condition: |
          if synthesize.verdict == 'APPROVE': goto post_approval
          elif synthesize.verdict == 'ESCALATE_HUMAN': goto human_review
          else: goto post_changes_requested
        outputs_to: [post_approval, human_review, post_changes_requested]

      - id: human_review
        kind: human_gate
        timeout_hours: 48
        on_timeout: escalate_secondary
        outputs_to: [post_approval, post_changes_requested]

      - id: post_approval
        kind: output_emission
        target: github_pr_comment
        template: approval_comment.md.j2
        terminal: true

      - id: post_changes_requested
        kind: output_emission
        target: github_pr_review
        template: changes_requested.md.j2
        terminal: true

    edges:
      # Edges are derived from node `outputs_to`. Explicit edges are only needed
      # when a single node fans into multiple downstream nodes with conditions
      # not expressible in the destination's `inputs_from`.
      - from: synthesize
        to: route_decision
        # implicit: derived from outputs_to

    entry_nodes: [fe_review, be_review, db_perf_review]
    max_wall_time_seconds: 1800       # whole-DAG cap; harness-level
    max_total_cost_usd: 5.00
```

---

## Node kinds

| Kind | Purpose | Required fields |
|---|---|---|
| `skill_invocation` | Run a registered skill | `skill`, `skill_version`, optional `config` |
| `synthesizer` | Aggregate ≥2 sub-agent outputs (per `synthesizer-contract.md`) | `synthesizer_version` |
| `gate` (deterministic) | Conditional routing using only structured fields | `gate_kind: deterministic`, `condition` (DSL) |
| `gate` (ai_assisted) | Conditional routing using a small LLM call to interpret unstructured signal | `gate_kind: ai_assisted`, `prompt_template`, `decision_enum` |
| `human_gate` | Block until human action; emit Slack/email | `timeout_hours`, `on_timeout` |
| `output_emission` | Terminal-ish: write to Slack/JIRA/GitHub | `target`, `template`; usually `terminal: true` |
| `feature_memory_write` | Explicit append (most writes are implicit from skill/synthesizer) | `entry_kind`, `payload_template` |
| `loop` | Re-execute a sub-DAG until break condition or max iterations | `body: [<node_ids>]`, `break_condition`, `max_iterations` |

Each kind has a strict input/output contract. The runtime validates at descriptor parse time.

---

## Edge semantics

Edges are typed:
- **Data edges** (default): downstream node reads upstream's output as input
- **Control edges** (from gates): downstream is enabled only if gate selects it

A node's `inputs_from` lists upstream nodes whose output it reads. The runtime materializes the upstream output into the input envelope under that node id (e.g., `inputs.fe_review`, `inputs.be_review`).

Conditional execution (`run_if`) skips a node entirely. Skipped nodes contribute nothing downstream; the synthesizer sees them as "not run" rather than "output unavailable".

---

## Gate DSL (deterministic gates)

```
condition := python_subset_expression
expression := comparison | logical | dotted_access | function_call
allowed_functions := str.startswith, str.endswith, str.contains,
                     touches_path, has_severity_at_least,
                     all, any, len
```

Allowed inputs to gate expressions: structured fields from upstream nodes. Free-form text fields are NOT accessible to deterministic gates (use `ai_assisted` if needed).

Examples:
```
synthesize.verdict == 'APPROVE'
synthesize.confidence < 0.6
trigger.diff.touches_path('app/models/**')
any(f.severity == 'blocker' for f in synthesize.findings_kept)
```

The DSL is intentionally bounded — full Python in gates becomes an attack surface and a debugging nightmare.

---

## AI-assisted gates

```yaml
- id: triage_root_cause
  kind: gate
  gate_kind: ai_assisted
  inputs_from: [incident_summary]
  prompt_template: triage_root_cause.j2
  decision_enum: [db_root_cause, app_root_cause, infra_root_cause, unclear]
  on_unclear: human_gate
  outputs_to: [db_diagnose, app_diagnose, infra_diagnose, human_review]
```

AI gates produce ONE enum value from a finite list. They never emit free-form. The decision is logged to `analytics.harness_dag_decisions` for audit.

---

## Persistent run-state

Each DAG run has a state object persisted at every node boundary:

```json
{
  "run_id": "harness-pr-review-2026-04-28-abc",
  "feature_id": "apolloio/leadgenie#87432",
  "tenant_id": "apolloio",
  "current_state": "awaiting_human_review",
  "node_states": {
    "fe_review": {"status": "completed", "output_ref": "..."},
    "be_review": {"status": "completed", "output_ref": "..."},
    "db_perf_review": {"status": "skipped", "reason": "run_if=false"},
    "synthesize": {"status": "completed", "output_ref": "..."},
    "route_decision": {"status": "completed", "selected": "human_review"},
    "human_review": {"status": "pending", "deadline": "2026-04-30T..."}
  },
  "started_at": "...",
  "last_transition_at": "..."
}
```

State is checkpointed to `analytics.harness_dag_runs`. Crashed runs resume from the last checkpoint, NOT from scratch — this is the difference from a fire-and-forget skill chain.

---

## State machine derivation (Phase F primitive F4)

The DAG implicitly defines a state machine:
- States = `{node.id : {pending, running, completed, skipped, failed}}` × terminal selection
- Transitions = edge traversals
- Terminal states = nodes with `terminal: true`

The descriptor validator emits a state-diagram artifact (Mermaid or DOT) for each DAG. This is the visualization for `11-phase-f-scoping.md`'s "tech-lead pipeline" diagram.

---

## Cost attribution per node

Each node's wall-time, tokens, and dollar cost are tagged in `analytics.harness_runs.cost_breakdown`:

```json
{
  "fe_review": {"wall_ms": 12000, "tokens": 8200, "cost_usd": 0.18},
  "be_review": {"wall_ms": 14000, "tokens": 9800, "cost_usd": 0.22},
  "synthesize": {"wall_ms": 4000, "tokens": 3000, "cost_usd": 0.07},
  ...
}
```

This composes with `cost_forecast.p95` from the descriptor — but at NODE granularity, not just whole-harness. Drift on a single node is detectable.

---

## Failure semantics

| Failure | Behavior |
|---|---|
| Node `failed` (skill error, MCP timeout, etc.) | Run state = `failed`; no downstream nodes execute; synthesizer (if downstream) sees the failure; final emission is degraded report per `mcp_failure_mode` |
| Node `failed` with `retry: {max: N, backoff: ...}` declared | Retry per policy; only mark `failed` after exhaustion |
| `human_gate` timeout | Execute `on_timeout` branch (escalate_secondary, post_default, etc.) |
| Whole-DAG `max_wall_time_seconds` exceeded | Cancel in-flight nodes; emit timeout report; mark run `timeout` |
| Whole-DAG `max_total_cost_usd` exceeded | Same as wall-time; cost-cap is a hard gate |

DAG retries do NOT auto-retry the whole DAG. A whole-DAG re-run is a NEW trigger that creates a new run_id with the same feature_id. Feature memory carries the connection.

---

## Cycle detection

The runtime asserts at parse time that the DAG is acyclic, EXCEPT inside a `loop` node. Any cycle outside a `loop` is a descriptor error.

`loop` nodes have explicit `max_iterations` (cap) and `break_condition` (DSL expression). The runtime hard-stops at `max_iterations` regardless of break condition.

---

## Composition with other Phase F primitives

| Primitive | Interaction |
|---|---|
| F1 Synthesizer | One node kind; `kind: synthesizer` |
| F3 Feature memory | Nodes can declare `feature_memory.read` per the read API |
| F4 State machine | The DAG IS the state machine; no separate F4 schema |
| F5 Stand-up harness | Reads `analytics.harness_dag_runs WHERE current_state matches stuck-pattern` |

---

## Eval corpus (Phase F MVP)

`eval/dag/` ships with ≥20 cases:
- 5 cases: linear DAG (skill → synth → emit) end-to-end
- 5 cases: parallel fan-out (3 skills → synth) with agreement
- 3 cases: parallel fan-out with disagreement (synth escalates → human_gate)
- 2 cases: conditional `run_if` skips a node correctly
- 2 cases: gate routes to correct branch (deterministic)
- 1 case: ai_assisted gate routes correctly with decision logged
- 1 case: human_gate timeout fires `on_timeout`
- 1 case: cost cap exceeded mid-DAG; correct cancellation

Replay-eval gate: precision ≥0.90 on routing decisions; 100% on cycle-detection and cost-cap invariants.

---

## Anti-patterns

- **Free-form Python in gates.** DSL only. Free-form is an injection vector and unauditable.
- **Implicit edges via shared state.** Edges flow through `inputs_from` only. No "node B reads a magic global written by node A".
- **DAG-level retries that re-execute the whole DAG.** Per-node retries are explicit; whole-DAG re-runs are NEW triggers.
- **Loops without `max_iterations`.** Always bounded. Even `break_condition` can fail; the iteration cap is the safety.
- **Gating on free-form text from an upstream node.** Use `ai_assisted` gate explicitly so the LLM call is logged + costed.
- **Treating `human_gate` as cheap.** Every human gate is a 24h+ latency cost. DAGs should minimize them.

---

## Phase F MVP exit requirements

- [ ] `dag:` block parsed + validated by Pantheon descriptor schema
- [ ] All 8 node kinds implemented in runtime
- [ ] `analytics.harness_dag_runs` table with checkpoint resume
- [ ] State-diagram artifact emitted on descriptor parse
- [ ] PR-review-with-tech-lead-synthesis vertical proof-point shipped using DAG end-to-end
- [ ] Eval corpus ≥20 cases passing
- [ ] Cycle-detection and cost-cap unit tests in runtime
