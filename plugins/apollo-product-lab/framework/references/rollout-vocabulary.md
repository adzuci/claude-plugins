# Rollout Vocabulary — Framework Canonical Reference

> **Status**: framework-canonical. Closes Phase C SRE blocker "rollout vocabulary is inconsistent across descriptors" (`dry_run`, `dark_launch`, `canary`, `pilot`, `limited`, `gradual`, `full` were used interchangeably).
>
> **Binding**: every Pantheon harness descriptor MUST express its rollout in one of the four phases below. Custom verbs are rejected by the descriptor schema validator.

---

## The four canonical rollout phases

| Phase | Definition | Side effects | Audience | Gate to next phase |
|---|---|---|---|---|
| **`dry_run`** | Skill runs end-to-end and emits all outputs **as artifacts** (logs, snowflake rows, draft Slack/JIRA/PR bodies) but does NOT post to external systems. | None visible to end users. All outputs land in `analytics.harness_runs` with `dry_run: true`. | Skill maintainer + harness owner | Maintainer reviews ≥10 dry-run artifacts; precision ≥ skill threshold; FPR ≤ skill threshold. |
| **`pilot`** | Skill runs live on a **hand-picked subset** — specific repo/team/service IDs enumerated explicitly in the descriptor. Outputs are real (Slack posted, JIRA filed, PR commented) but bounded. | Real outputs visible to pilot audience only. | Hand-picked team(s), usually owner team + 1 partner team | Pilot review meeting confirms zero-blocker + audience opt-in to expand. |
| **`limited`** | Skill runs live on a **rule-based subset** (e.g., "all PRs from team X", "all SEV-2/3 incidents", "only opt-in via label"). Larger than pilot but still bounded. | Real outputs visible to all users in the rule scope. | Subset of org defined by predicate | Limited-phase replay-eval over real production traffic for ≥7 days; no SEV-1 attributable to harness; no cost overrun. |
| **`full`** | Skill runs live across the **entire production scope**. No subset filter. | Real outputs visible to entire user base / org. | Everyone in scope | None (this is steady state). To go beyond `full` (e.g., add new MCP servers, new sub-agents) you create a new harness or a new version. |

---

## Banned synonyms

| Old verb seen in descriptors | Maps to | Why banned |
|---|---|---|
| `dark_launch` | `dry_run` | Ambiguous — some teams used it to mean "no Slack but real DB writes." Use `dry_run` (no external writes) instead. |
| `canary` | `pilot` or `limited` (depending on size) | "Canary" implies traffic-percentage routing, which most harnesses don't support — they're event-driven. Use `pilot` for hand-picked, `limited` for rule-based. |
| `beta` | `limited` | Used to mean "opt-in users." That's `limited` with the predicate "opt-in label/flag." |
| `gradual` | sequence of `limited` rows with widening predicates | Not a phase, it's a rollout schedule. Express as multiple `limited` weeks. |
| `gated` | `limited` with `require_human_approval_for` | Gating is a guardrail, not a phase. |
| `full_launch` | `full` | Just say `full`. |

---

## Descriptor schema

Every Pantheon harness must include a `rollout:` block with these exact keys:

```yaml
rollout:
  week_1: { phase: dry_run,  scope: "<scope-string>" }
  week_2: { phase: pilot,    scope: "<scope-string>", audience: ["<team>", "<team>"] }
  week_3: { phase: limited,  scope: "<scope-string>", predicate: "<rule>" }
  week_4: { phase: full,     scope: "<scope-string>" }
```

`phase` is the binding enum. `scope` is human description. `audience` (pilot only) and `predicate` (limited only) make the bound concrete.

Skipping a phase is allowed only with a documented rationale field:

```yaml
rollout:
  week_1: { phase: dry_run, scope: "..." }
  week_2: { phase: full, scope: "...", skip_pilot_limited_rationale: "Read-only metrics harness; no external side effects in any phase." }
```

The descriptor validator rejects `skip_*_rationale` of fewer than 30 characters.

---

## Phase-to-guardrail mapping

| Phase | `dry_run` flag | `auto_pause_on_budget_exceeded` | `require_human_approval_for` | Replay-eval gate |
|---|---|---|---|---|
| `dry_run` | true | true (still trip on cost) | n/a | required to ship to `pilot` |
| `pilot` | false | true | typically `[merge_pr, send_page]` etc. | precision ≥ skill threshold |
| `limited` | false | true | scoped to destructive actions | live FPR ≤ skill threshold over 7d |
| `full` | false | true | scoped to destructive actions | none additional; ongoing monitoring |

---

## Examples (reference how the four in-scope harnesses express it)

### pr-review-bot

```yaml
rollout:
  week_1: { phase: dry_run, scope: "all PRs, log-only", }
  week_2: { phase: pilot,   scope: "ai-tooling team PRs only", audience: ["ai-tooling"] }
  week_3: { phase: limited, scope: "frontend-platform + ai-tooling", predicate: "team in ['frontend-platform','ai-tooling']" }
  week_4: { phase: full,    scope: "all teams" }
```

### oncall-triage-bot

```yaml
rollout:
  week_1: { phase: dry_run, scope: "all SEV-3 incidents" }
  week_2: { phase: pilot,   scope: "SRE team incidents only", audience: ["sre"] }
  week_3: { phase: limited, scope: "all teams, SEV-2 and below", predicate: "incident.severity in ['SEV-2','SEV-3']" }
  week_4: { phase: full,    scope: "all incidents including SEV-1" }
```

### capacity-plan-checker

```yaml
rollout:
  week_1: { phase: dry_run, scope: "platform team PRs only" }
  week_2: { phase: pilot,   scope: "3 hand-picked features", audience: ["platform"] }
  week_3: { phase: limited, scope: "opt-in via label, all teams", predicate: "labels.contains('Need_Capacity_Review')" }
  week_4: { phase: full,    scope: "mandatory for SEV-2+ blast radius", predicate: "blast_radius >= 'SEV-2' OR labels.contains('Need_Capacity_Review')" }
```

### flaky-test-quarantiner

```yaml
rollout:
  week_1: { phase: dry_run, scope: "all tests, log only" }
  week_2: { phase: pilot,   scope: "eng-productivity team's own tests", audience: ["eng-productivity"] }
  week_3: { phase: limited, scope: "all playwright tests org-wide", predicate: "test_kind == 'playwright'" }
  week_4: { phase: full,    scope: "all playwright + vitest tests" }
```

---

## Migration guidance for existing descriptors

The four in-scope Phase C descriptors used inconsistent free-text scopes without an explicit `phase` enum. Phase D batch tightening (Task #18) adds the `phase` field to each. The descriptor validator (`pantheon-descriptors/README.md` checklist item 7) enforces presence.

When migrating:
1. Read the existing `week_N: { dry_run: bool, scope: ... }` row.
2. If `dry_run: true` → `phase: dry_run`.
3. If scope names ≤ 1 team explicitly → `phase: pilot`, copy team list to `audience`.
4. If scope is a rule ("opt-in via label", "all SEV-2 and below") → `phase: limited`, encode rule as `predicate`.
5. If scope is "all" / "everyone" / "mandatory" → `phase: full`.

---

## Anti-patterns

- **Going from `dry_run` straight to `full`** without pilot/limited unless harness is read-only AND has the `skip_pilot_limited_rationale` field with substantive justification.
- **Calling something `full` while still gated by a feature flag.** That's `limited`.
- **Naming a fifth phase** ("`extended_pilot`", "`super_canary`"). Reject in code review. The four phases are deliberately small.
- **Using `phase: pilot` with `audience: ["all-engineering"]`.** That's `limited` with predicate `team is not null` — pilot requires a hand-picked, named list ≤3 teams.

---

## Legacy `dry_run:` boolean vs canonical `phase: dry_run`

> **Phase D batch-1 SRE major**: descriptors carry both a top-level `guardrails.dry_run: bool` AND a `rollout.week_N.phase: dry_run`. They are NOT equivalent and the precedence rule must be explicit.

### Precedence rule

When a harness is in any rollout phase:

1. **`rollout.week_N.phase`** is the **rollout-schedule** field — declares "what audience and what side effects this week."
2. **`guardrails.dry_run: bool`** is the **runtime override** — declares "regardless of schedule, suppress all external writes for this run."

The runtime override **wins**. If `guardrails.dry_run: true` is set:
- Harness runs end-to-end producing artifacts to `analytics.harness_runs`
- ALL external outputs (Slack, JIRA, GitHub, PagerDuty) are suppressed
- This is true even if `rollout.week_4.phase: full` (in steady state)

### When each is set to `true`

| Scenario | `rollout.phase` | `guardrails.dry_run` | Outcome |
|---|---|---|---|
| Initial rollout week 1 | `dry_run` | `true` | No external writes; both fields agree |
| Rollout week 2 (pilot) | `pilot` | `false` | External writes for pilot audience only |
| Steady state | `full` | `false` | All writes live |
| Emergency suppression | `full` (unchanged) | flipped to `true` | All writes suppressed without rolling back rollout phase |
| Per-team incident response | `full` (unchanged) | `true` for ≤24h | Same as above with TTL |

### Why both fields exist

Removing one is tempting but wrong:

- **Why not collapse `dry_run` boolean into `phase`?** Because emergency suppression should NOT require editing the rollout schedule. The runtime override is operationally simpler — flip one bool, file a JIRA, restore later. Collapsing them would couple "this week's rollout intent" with "is the harness currently writing."
- **Why not collapse `phase: dry_run` into the boolean?** Because the rollout schedule is a multi-week artifact; week 1 being `dry_run` is a planning statement, separate from "today's runs are suppressed."

### Audit query

The Pantheon descriptor validator surfaces a warning whenever `guardrails.dry_run: true` is set with `rollout.week_<current>.phase` not `dry_run`. The warning prompts the harness owner to file a JIRA explaining the override (so emergency suppressions don't become permanent without a paper trail).

```
WARN: harness X has guardrails.dry_run=true but current rollout phase is 'full'.
      This is a runtime override. File a JIRA explaining + setting an end date.
```

---

## Eval coverage

Phase D adds an eval case to `framework-phase-review/eval/` that:
1. Loads each descriptor in `pantheon-descriptors/`.
2. Asserts `rollout` block exists, has 4 phases, each row uses canonical `phase` enum.
3. Asserts `pilot.audience` ≤ 3 teams.
4. Asserts `limited.predicate` is non-empty.

Failure on any of these blocks the phase exit.
