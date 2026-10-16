# Hard-Rule → Eval-Case Coverage Matrix — Canonical Reference

> **Status**: framework-canonical. Closes Phase E hardening workstream E0.3.
>
> **Binding**: every `guardrails.hard_rules` entry in a Pantheon descriptor MUST have ≥1 covering eval case. The descriptor schema validator rejects PRs that add a `hard_rule` without a covering case.

---

## Why this exists

Every `hard_rule` in a descriptor is a load-bearing invariant — "never quarantine 50%-failure tests in 24h", "never auto-page", "never recommend monotonic shard key". If the rule is real, an eval case must prove it fires. Otherwise the rule is aspiration, not enforcement.

Currently the link between `hard_rules` and eval cases is honor-system. This reference + CI validator make it mechanical.

---

## Coverage matrix format

Each harness descriptor has a sibling file: `<descriptor>.coverage.yaml`. Example for `pr-review-bot`:

```yaml
descriptor: pantheon-descriptors/pr-review-bot.yaml
last_validated: 2026-04-28
hard_rules:
  - rule: never_review_without_pr_context
    covering_cases:
      - skill: code-review
        case_id: code-review-c7-empty-context-refusal
    last_passing_run: 2026-04-28T03:01:00Z
    support: 12
  - rule: never_post_security_finding_in_public_thread
    covering_cases:
      - skill: code-review
        case_id: code-review-c12-security-finding-private-only
      - skill: code-review
        case_id: code-review-c13-security-finding-redaction
    last_passing_run: 2026-04-28T03:01:00Z
    support: 8
  - rule: cap_review_size_at_400_lines
    covering_cases:
      - skill: code-review
        case_id: code-review-c5-large-pr-truncation
    last_passing_run: 2026-04-28T03:01:00Z
    support: 15
```

Each rule must have ≥1 case. Each case must have a `last_passing_run` timestamp from `eval/last-run.json`. Support is the number of times the case has run successfully across all eval runs in the past 90 days.

---

## Schema validator

CI runs `scripts/validate-coverage.sh` which:

1. Parses every `*.yaml` in `pantheon-descriptors/`
2. Extracts `guardrails.hard_rules`
3. For each rule, looks up the matching `<descriptor>.coverage.yaml`
4. Asserts every rule has ≥1 covering case
5. Asserts every covering case exists in the corresponding `eval/cases.json`
6. Asserts `last_passing_run` is within the past 90 days (warn) or 180 days (fail)
7. Asserts `support` ≥ 3 (warn) or ≥ 1 (fail)

Validator output:

```
[PASS] pr-review-bot: 9 rules, 14 covering cases, 0 stale
[FAIL] oncall-triage-bot: 5 rules, 8 covering cases, 1 stale (cap_wall_time_60s_internal: last_passing_run > 180d)
```

CI fails on any FAIL. Warnings produce a comment on the PR but don't block.

---

## Quarterly drift check

Even if the static matrix is green, eval cases can rot — a refactor to the skill might silently make a case pass-by-accident rather than pass-by-design. Quarterly drift check:

1. Re-runs every covering case against current skill version
2. Compares: was the rule the determining factor in the case's pass/fail outcome?
3. Flags rules whose covering cases now pass for unrelated reasons (false coverage)

The drift check uses scorer introspection — the scorer logs WHICH `expected_check` decided pass/fail. If the rule isn't the deciding check anymore, coverage is suspect.

Drift report lands in `analytics.coverage_drift` and is reviewed in the next SSG meeting.

---

## Adding a new hard_rule (workflow)

1. Engineer adds `hard_rule: foo` to descriptor in PR
2. CI validator fails: "hard_rule 'foo' has no covering case"
3. Engineer adds eval case (or cases) to skill's `eval/cases.json` whose `expected_checks` exercises the rule
4. Engineer adds entry to `<descriptor>.coverage.yaml` linking rule → case
5. Engineer runs replay-eval; CI confirms `last_passing_run` populated
6. PR ready for review

This is intentionally friction-y. A `hard_rule` is a permanent commitment; making it cheap to add and expensive to violate is the goal.

---

## Removing a hard_rule (workflow)

Removing a rule from a descriptor requires:

1. Engineer opens PR removing the rule
2. PR description explains: why is this rule no longer needed? What replaced it?
3. PR description preserves the rule + its coverage-yaml entries in a "REMOVED" section for audit
4. SSG sign-off (rule removal is a governance event)

Coverage matrix entries for the removed rule are archived to `<descriptor>.coverage.archive.yaml`, never deleted.

---

## Anti-patterns

- **Catch-all eval case ("c0-out-of-scope") covering 5 rules.** A single negative case is not coverage. Each rule needs a positive case where the rule is the deciding factor.
- **Rule phrased as a goal, not a behavior.** "always_be_helpful" is not a hard_rule; "never_emit_pii_in_slack" is. If you can't write an eval case for it, it's not a hard_rule.
- **Stale `last_passing_run`.** A rule whose covering case hasn't run in 6 months is not enforced. Either run it or admit the rule is dead.
- **Multiple rules covered by the same single case.** Some overlap is fine, but each rule should have ≥1 case where IT is the deciding factor.

---

## Phase E migration

Phase E builds the coverage matrix for all 4 in-scope harnesses by:

1. Listing each `hard_rule` from each descriptor
2. Identifying existing eval cases that cover it
3. Adding new eval cases for any uncovered rule
4. Committing `<descriptor>.coverage.yaml` per harness

Estimated gap: each harness has 5–8 hard_rules; current eval corpora cover ~60% of them. Phase E closes the remaining 40% with new cases.

---

## Phase E exit requirements

- [ ] `<descriptor>.coverage.yaml` exists for all 4 in-scope harnesses
- [ ] All hard_rules have ≥1 covering case
- [ ] `scripts/validate-coverage.sh` passes in CI
- [ ] Quarterly drift check job scheduled
- [ ] Phase F rule-additions automatically required to add coverage
