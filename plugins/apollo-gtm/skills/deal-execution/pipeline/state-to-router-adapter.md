# State-to-Router Adapter

## Purpose

This adapter bridges the schema gap between state-extractor's domain-agnostic state object and bounded-action-router's routing-optimized input contract. It is a mechanical transform, not a reasoning step. Every field BAR expects is either directly mapped from SE output, deterministically derived from SE fields, or injected from system context. The adapter adds no interpretation and makes no routing decisions.

## When to Use

Run this adapter whenever state-extractor output feeds bounded-action-router. Skip it when BAR receives pre-formatted input from another source that already conforms to BAR's input contract.

---

## Transform Table

Every BAR input field, with its derivation from SE output.

### §1 Object Metadata

| BAR Field | Transform Type | Derivation |
|---|---|---|
| `state_id` | **Injection** | Generate as `se_{input_type}_{ISO8601_timestamp_compact}_{4_random_hex}`. Example: `se_email_thread_20250713T1422Z_a3f1`. |
| `source_type` | **Direct map** | `state_object.input_type` → `source_type`. No value change. |
| `timestamp` | **Injection** | Current UTC time in ISO 8601 at moment of adapter execution. |
| `freshness` | **Injection** | Requires `input_originated_at` from system context (the timestamp of the original input, not extraction time). Compute: if age ≤ 1 hour → `current`; ≤ 24 hours → `recent`; > 24 hours → `stale`. If `input_originated_at` is unavailable → `unknown`. |
| `parser_confidence` | **Aggregation** | Collect all `confidence` values across SE arrays (`actors`, `timeline`, `known_facts`, `inferred_points`, `requests`, `decisions`, `open_loops`, `constraints`, `dependencies`, `risk_flags`, `escalation_flags`). Map: high=1.0, medium=0.5, low=0.0. Compute weighted mean where weight = 1.0 for `requests`, `decisions`, `constraints`, `risk_flags`; weight = 0.5 for all others. If no confidence values exist (minimal schema with empty arrays) → `low`. Round to nearest band: ≥ 0.7 → `high`; ≥ 0.4 → `medium`; < 0.4 → `low`. |

#### Worked Example: Skewed Distribution

SE produces: 20 actors (each `confidence: medium`), 1 request (`confidence: low`), no other arrays populated.

| Array | Count | Mapped Value | Weight | Weighted Sum | Weighted Count |
|---|---|---|---|---|---|
| `actors` | 20 | 0.5 each | 0.5 | 20 × 0.5 × 0.5 = 5.0 | 20 × 0.5 = 10.0 |
| `requests` | 1 | 0.0 | 1.0 | 1 × 0.0 × 1.0 = 0.0 | 1 × 1.0 = 1.0 |
| **Totals** | | | | **5.0** | **11.0** |

Weighted mean = 5.0 / 11.0 = 0.455 → rounds to `medium` (≥ 0.4).

This result is correct for routing: the state has substantial structure (20 identified actors) with one low-confidence request. The single bad request does not collapse the entire confidence to `low` because the actor extraction was reliable. If the concern is specifically about request quality, that surfaces through `decision_ready` (→ `not_ready` due to low request confidence) and through the epistemic tag on `requested_outcome` (→ `assumed`), not through the aggregate parser confidence.

Contrast: if the distribution were 1 actor (`confidence: high`, weight 0.5) and 20 requests (all `confidence: low`, weight 1.0), the weighted mean = (0.5×0.5 + 20×0.0×1.0) / (0.5 + 20.0) = 0.012 → `low`. The high-weight items dominate when they are the majority, which is the intended behavior: many low-confidence routing-critical fields should collapse confidence.

### §2 Intent and Interaction State

| BAR Field | Transform Type | Derivation |
|---|---|---|
| `primary_intent` | **Direct map** | `state_object.primary_question_or_problem` → `primary_intent`. If null → `"No explicit intent identified"`. |
| `intent_explicitness` | **Derivation** | If `primary_question_or_problem` is null → `unknown`. Else: find any `requests[]` entry where `epistemic_status` is `explicit` and the request text overlaps with `primary_question_or_problem` (shares a subject noun or verb) → `explicit`. If no explicit request matches but `requests[]` exists with `epistemic_status: inferred` → `inferred`. If only `implied` requests exist → `implied`. If `requests[]` is empty → determine from `inferred_points[]`: if any inferred point references a question or problem → `inferred`; else → `unknown`. |
| `response_expected` | **Derivation** | TRUE if any `requests[]` entry has `status: open` AND `requested_of` is non-null. FALSE if `requests[]` is empty or all requests have `status: fulfilled` or `status: declined`. If all open requests have `requested_of: null` → TRUE (conservative default: open request implies expectation). |
| `decision_ready` | **Derivation** | Start with `ready`. Downgrade to `partial` if: `unknowns[]` has ≥ 1 entry, OR any `dependencies[]` entry exists with `confidence` ≠ `high`, OR `signals.ambiguity_level` is `medium`. Downgrade to `not_ready` if: `unknowns[]` has ≥ 3 entries, OR `signals.ambiguity_level` is `high`, OR > 50% of `constraints[]` have `confidence: low`. |
| `thread_stage` | **Derivation** | Map from `signals.decision_stage`: `discovery` → `early`; `evaluation` or `negotiation` → `midstream`; `pending_approval` or `execution` → `late`; `post_decision` → `complete`; `unknown` → `unknown`. If `signals.decision_stage` is absent → `unknown`. |
| `requested_outcome` | **Derivation** | Take the first `requests[]` entry where `status: open`, ordered by: `epistemic_status: explicit` first, then `confidence: high` first. Return its `request` string. If no open requests → null. |

### §3 Actors and Authority

| BAR Field | Transform Type | Derivation |
|---|---|---|
| `sender` | **Derivation** | Search `actors[]` for an entry whose `role` contains "sender", "author", "requester", or "initiator" (case-insensitive substring match). Return `{name, role}`. If no match, use the first actor in the array. If `actors[]` is empty → `{name: "unknown", role: "unknown"}`. |
| `recipient` | **Derivation** | Search `actors[]` for an entry whose `role` contains "recipient", "responder", "assignee", or "owner" (case-insensitive substring match). Return `{name, role}`. If no match, search `requests[]` for the most frequent `requested_of` value and look up that name in `actors[]`. If still no match → `{name: "unknown", role: "unknown"}`. |
| `authority_level` | **Injection** | Must be provided in system context. If absent → `unknown`. The adapter never infers authority from text. |

### §4 Open Items

| BAR Field | Transform Type | Derivation |
|---|---|---|
| `unresolved_questions` | **Direct map** | `state_object.unknowns[]` → `unresolved_questions[]`. Reshape: `{question: unknowns[].field_or_question, reason: unknowns[].reason}`. |
| `unresolved_dependencies` | **Aggregation** | Merge two sources. (1) `dependencies[]` → include all entries. Reshape: `{dependency: dependencies[].dependency, blocks: dependencies[].blocks, status: "unmet", confidence: dependencies[].confidence}`. (2) `open_loops[]` where `blocker` is non-null → append as `{dependency: open_loops[].blocker, blocks: open_loops[].item, status: "unmet", confidence: open_loops[].confidence}`. Deduplicate by `dependency` string (keep higher confidence on collision). |

### §5 Constraints

See **Constraint Type Mapping** section below for type translation. Reshape each SE `constraints[]` entry:

```yaml
- constraint: constraints[].constraint
  type: constraints[].type  # 1:1 passthrough — SE type IS the BAR type
  source: constraints[].source_or_basis
  epistemic_status: constraints[].epistemic_status
  confidence: constraints[].confidence
```

With the 1:1 constraint type mapping (v3.0.3), SE types pass through directly as BAR types. No separate `_constraint_source_type` field is needed because no lossy transformation occurs.

Additionally, inject synthetic constraints:
- If `dependencies[]` is non-empty → add one constraint per dependency: `type: dependency`, `constraint: dependencies[].dependency`, `confidence: dependencies[].confidence`.
- If `parser_confidence` (computed above) is `low` → add: `type: confidence`, `constraint: "Overall parser confidence is low"`, `confidence: low`.
- If `unknowns[]` has ≥ 3 entries → add: `type: data_completeness`, `constraint: "{N} unresolved questions remain"`, `confidence: medium`.

### §6 Risk Indicators

See **Risk Aggregation** section below.

### §7 Epistemic Tags

See **Epistemic Status Passthrough** section below.

### §8 Signals

See **Signal Derivation** section below.

---

## Constraint Type Mapping

### SE type → BAR type

| SE Constraint Type | BAR Constraint Type | Notes |
|---|---|---|
| `time` | `time` | Direct map. |
| `policy` | `policy` | Direct map. |
| `legal` | `legal` | Preserved (was: collapsed to policy). |
| `budget` | `budget` | Preserved (was: collapsed to scope). |
| `technical` | `technical` | Preserved (was: collapsed to dependency). |
| `relationship` | `relationship` | Preserved (was: collapsed to reversibility). |
| `logistical` | `logistical` | Preserved (was: collapsed to scope). |
| `unknown` | `unknown` | Preserved (was: collapsed to scope). |

### BAR types not produced by SE constraint mapping

These BAR constraint types are never output by SE's `constraints[]` and must be derived from other SE fields:

| BAR Constraint Type | Derivation Source |
|---|---|
| `authority` | Injected from system context via `authority_level`. If `authority_level` is `limited` or `none` → inject constraint: `type: authority`, `constraint: "System authority is {authority_level}"`. |
| `dependency` | From SE `dependencies[]` array (see §5 above). Note: `technical` SE constraints are no longer mapped to `dependency` (v3.0.3); they pass through as `type: technical`. |
| `confidence` | From computed `parser_confidence`. If `low` → inject constraint. |
| `channel` | From SE `input_type`. If `input_type` suggests channel restriction (e.g., `email_thread` implies email channel) → inject: `type: channel`, `constraint: "Input channel is {input_type}"`, `confidence: high`. Only inject if system context flags channel restrictions as relevant; otherwise omit. |
| `data_completeness` | From SE `unknowns[]` count (see §5 above). |

---

## Signal Derivation

| BAR Signal | Derivation | Fallback |
|---|---|---|
| `urgency` | **Direct map.** `signals.urgency` → `urgency`. | `unknown` |
| `ambiguity` | **Direct map + rename.** `signals.ambiguity_level` → `ambiguity`. If SE value is `unknown` → map to `high` (conservative: unknown ambiguity is treated as high). | `high` |
| `tension` | **Direct map + rename.** `signals.conflict_level` → `tension`. If SE value is `unknown` → map to `low`. | `low` |
| `task_density` | **Derivation.** Count = len(`requests[]`) + len(`open_loops[]`) + len(`decisions[]` where `status` ≠ `final`). If count ≤ 2 → `low`; 3–5 → `medium`; ≥ 6 → `high`. | `low` |
| `decision_readiness` | **Derivation.** Reuse `decision_ready` from §2. Map: `ready` → `ready`; `partial` → `partial`; `not_ready` → `not_ready`. | `not_ready` |
| `expectation_of_response` | **Derivation.** If `response_expected` (from §2) is FALSE → `none`. If TRUE: count open requests. 1 → `low`; 2–3 → `medium`; ≥ 4 → `high`. Additionally, if `signals.urgency` is `high` → upgrade by one level (low→medium, medium→high). | `none` |
| `interaction_frame` | **Derivation.** If `signals.emotional_tone` is `tense`, `conflicted`, or `negative` → `relational`. If all `requests[]` have `epistemic_status: explicit` and `signals.emotional_tone` is `neutral` → `transactional`. Otherwise → `ambiguous`. BAR has its own fallback if this field is absent, so `ambiguous` is safe. | `ambiguous` |

---

## Risk Aggregation

All derived from SE `risk_flags[]`.

| BAR Field | Derivation |
|---|---|
| `overall_risk` | If `risk_flags[]` is empty → `low`. Else: map each entry's `confidence` (high=1.0, medium=0.5, low=0.25). Take the maximum value. ≥ 0.7 → `high`; ≥ 0.4 → `medium`; < 0.4 → `low`. Rationale: risk is dominated by the worst credible flag, not averaged. |
| `compliance_risk` | Filter `risk_flags[]` where `type` ∈ {`compliance`, `legal`, `safety`}. If none → `low`. Else: apply same max-confidence logic as `overall_risk`. |
| `relationship_risk` | Filter `risk_flags[]` where `type` ∈ {`relational`, `reputational`}. If none → `low`. Else: apply same max-confidence logic as `overall_risk`. |
| `contradiction_present` | TRUE if any of: (1) `risk_flags[]` contains `type: factual_uncertainty` with `confidence` ≠ `low`, OR (2) any `decisions[]` entry has `status: disputed`, OR (3) `parser_notes.ambiguities` has ≥ 2 entries. FALSE otherwise. If `risk_flags` and `decisions` are both empty and `parser_notes` is absent → FALSE. |

---

## Epistemic Status Passthrough

### Preserved tags

SE attaches `epistemic_status` to: `actors`, `timeline`, `known_facts`, `inferred_points`, `requests`, `decisions`, `constraints`. These tags pass through unchanged on any field that carries them into BAR's output. The adapter does not modify existing epistemic tags.

### Enum extension

SE uses: {explicit, inferred, implied, unknown}. BAR expects: {explicit, inferred, implied, disputed, assumed, missing, unknown}.

Derivation of extended tags:
- `disputed`: If SE marks a field's `epistemic_status` as any value BUT a sibling field (e.g., a `decisions[]` entry) has `status: disputed` referencing the same subject → override to `disputed`.
- `assumed`: If a field's `epistemic_status` is `inferred` AND `confidence` is `low` → upgrade to `assumed`. Rationale: low-confidence inference is functionally an assumption.
- `missing`: If a BAR field is derived from an SE field that is null, empty, or absent → tag as `missing`.

### Routing-level epistemic tags

For BAR fields that do not exist in SE (derived fields), attach epistemic status based on derivation source:

| BAR Field | Epistemic Tag Rule |
|---|---|
| `primary_intent` | Inherit from `primary_question_or_problem`. If SE field was null → `missing`. |
| `intent_explicitness` | `inferred` (always derived). |
| `response_expected` | `inferred` if derived from requests; `assumed` if using conservative default. |
| `decision_ready` | `inferred` (always compound derivation). |
| `thread_stage` | Inherit from `signals.decision_stage` epistemic quality. If mapped from known SE value → `inferred`; if SE value was `unknown` → `unknown`. |
| `requested_outcome` | Inherit from the source `requests[]` entry's `epistemic_status`. If no open request → `missing`. |
| `sender` | Inherit from matched `actors[]` entry's `epistemic_status`. If no match → `assumed`. |
| `recipient` | Same as `sender`. |
| `authority_level` | `explicit` if injected from system context; `missing` if absent. |

---

## SE Fields Not Consumed by BAR

These SE output fields are passed through in a `_se_passthrough` object appended to the adapter output. Downstream skills may consume them; BAR ignores them.

| SE Field | Reason for Passthrough |
|---|---|
| `schema_name` | Metadata. Useful for audit trail. |
| `domain` | BAR is domain-agnostic. Downstream L4 skills (message-os, GEN-SE) consume domain. |
| `source_summary` | Prose summary. Useful for L4 message composition. |
| `actors[]` (full) | BAR uses only sender/recipient. Full actor graph is needed by L4. |
| `timeline[]` | BAR has no timeline input. L4 may reference chronology. |
| `known_facts[]` | BAR has no facts input. L4 and L2B consume facts. |
| `inferred_points[]` | Same as known_facts. |
| `decisions[]` | Consumed indirectly (for `contradiction_present`, `task_density`), but full array passed through. |
| `open_loops[]` | Consumed indirectly (for `unresolved_dependencies`, `task_density`), but full array passed through. |
| `escalation_flags[]` | BAR computes escalation internally. Passed through for audit. |
| `candidate_action_classes[]` | SE's suggestion. BAR computes its own. Passed through for comparison/audit. |
| `parser_notes` | Consumed indirectly (for `contradiction_present`). Full object passed through for audit. |
| `signals.emotional_tone` | Consumed indirectly (for `interaction_frame`). Passed through for L4. |
| `signals.decision_stage` | Consumed for `thread_stage` derivation. Passed through for reference. |

---

## Edge Cases

### Minimal schema mode

When SE produces minimal schema output (empty arrays, minimal signals):

1. All aggregation-based fields (`parser_confidence`, `overall_risk`, `compliance_risk`, `relationship_risk`) default to their lowest/safest value (`low`).
2. `contradiction_present` → FALSE.
3. `decision_ready` → `not_ready` (no data to assess readiness).
4. `task_density` → `low` (count = 0).
5. `response_expected` → FALSE (no requests).
6. `sender` and `recipient` → `{name: "unknown", role: "unknown"}`.
7. All derived epistemic tags → `missing` or `unknown`.

### Empty arrays

An empty array is not an error. It means SE found nothing for that category. Treat `[]` identically to the field being absent: use the default/fallback value.

### Uniformly low confidence

When every `confidence` field across all SE arrays is `low`:

1. `parser_confidence` → `low`.
2. Inject a `confidence` constraint (see §5).
3. `decision_ready` → `not_ready`.
4. All `assumed`-upgrade rules in epistemic extension apply aggressively (every `inferred` + `low` → `assumed`).
5. `overall_risk` remains as computed from `risk_flags` (low confidence on risk flags means the risks themselves are uncertain, not that overall risk is low).

### Null primary_question_or_problem

1. `primary_intent` → `"No explicit intent identified"`.
2. `intent_explicitness` → `unknown`.
3. `requested_outcome` derivation proceeds from `requests[]` independently.

### System context absent

When no system context is provided (no `input_originated_at`, no `authority_level`):

1. `freshness` → `unknown`.
2. `authority_level` → `unknown`.
3. No `authority` constraint injected.
4. No `channel` constraint injected.

---

## Output Contract

The adapter produces exactly BAR's input contract. Schema:

```yaml
adapted_state:
  # §1 Object Metadata
  state_id: string
  source_type: string
  timestamp: string  # ISO 8601
  freshness: current | recent | stale | unknown
  parser_confidence: high | medium | low

  # §2 Intent and Interaction State
  primary_intent: string
  intent_explicitness: explicit | inferred | implied | unknown
  response_expected: boolean
  decision_ready: ready | partial | not_ready
  thread_stage: early | midstream | late | complete | unknown
  requested_outcome: string | null

  # §3 Actors and Authority
  sender: {name: string, role: string}
  recipient: {name: string, role: string}
  authority_level: full | limited | none | unknown

  # §4 Open Items
  unresolved_questions:
    - question: string
      reason: string | null
  unresolved_dependencies:
    - dependency: string
      blocks: string | null
      status: string
      confidence: high | medium | low

  # §5 Constraints
  constraints:
    - constraint: string
      type: time | policy | legal | budget | technical | relationship
            | logistical | unknown | authority | dependency | confidence
            | channel | data_completeness
      source: string | null
      epistemic_status: explicit | inferred | implied | disputed
                        | assumed | missing | unknown
      confidence: high | medium | low

  # §6 Risk Indicators
  overall_risk: low | medium | high
  compliance_risk: low | medium | high
  relationship_risk: low | medium | high
  contradiction_present: boolean

  # §7 Epistemic Tags
  epistemic_tags:
    primary_intent: explicit | inferred | implied | disputed
                    | assumed | missing | unknown
    intent_explicitness: inferred
    response_expected: inferred | assumed
    decision_ready: inferred
    thread_stage: inferred | unknown
    requested_outcome: explicit | inferred | implied | missing
    sender: explicit | inferred | implied | assumed | unknown
    recipient: explicit | inferred | implied | assumed | unknown
    authority_level: explicit | missing

  # §8 Signals
  signals:
    urgency: low | medium | high | unknown
    ambiguity: low | medium | high
    tension: low | medium | high
    task_density: low | medium | high
    decision_readiness: ready | partial | not_ready
    expectation_of_response: none | low | medium | high
    interaction_frame: transactional | relational | ambiguous

  # Passthrough
  _se_passthrough:
    schema_name: string
    domain: string
    source_summary: string
    actors: []
    timeline: []
    known_facts: []
    inferred_points: []
    decisions: []
    open_loops: []
    escalation_flags: []
    candidate_action_classes: []
    parser_notes: {}
    signals_raw: {}
```
