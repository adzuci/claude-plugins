# Synthesizer contract (code-review supervisor)

The interface between the `code-review` supervisor, the reviewer sub-agents (`backend-reviewer`,
`db-perf`, `security-reviewer`, `frontend-reviewer`) and `pr-tech-lead-synthesizer`. The general
contract is `framework/references/synthesizer-contract.md` in this plugin; this
file is the operational version for PR review and wins where they differ.

## 1. Reviewer brief (supervisor to each reviewer)

| Field | Required | Meaning |
|---|---|---|
| `pr` | yes | PR number, or `local` for a branch diff |
| `diff_path` | yes | file holding the unified diff, `*.rbi`, `sorbet/**` and lockfiles already removed |
| `head_ref` | yes | sha of the PR head the diff was taken at; reviewers read code with `git show <head_ref>:<path>` |
| `base_ref` | yes | sha the diff is against |
| `stack_tip_ref` | for stacked PRs | sha of the top of the stack; wiring checks (field readers, reachability, state exits) run here |
| `infra_patterns_path` | yes | absolute path to `apollo-infra-patterns.md` (default `${CLAUDE_PLUGIN_ROOT}/framework/apollo-infra-patterns.md`) (IP1 to IP17) |
| `static_context_path` | if the repo has one | the repo's own review context, if present (leadgenie: `.ai/apollo-review-bot/static-review-context.md`) |
| `quality_rules_path` | if the repo has one | the repo's code-quality rules, if present (leadgenie: `.ai/apollo-review-bot/code-quality-rules.md`) |
| `design_path` | when one exists | the ERD or design doc, with its Load model (framework doc 17 §6.2) |
| `output_path` | yes | where the reviewer writes its envelope |

## 2. Reviewer envelope (each reviewer returns or writes)

```json
{
  "role": "backend-reviewer | db-perf | security-reviewer | frontend-reviewer | infra-lens",
  "version": "vX.Y.Z",
  "pr": 107058,
  "refs": {"head": "<sha>", "stack_tip": "<sha or null>"},
  "served_by": "<model that answered, if known; else null>",
  "loaded": ["static-review-context", "code-quality-rules", "apollo-infra-patterns"],
  "verdict": "APPROVE | REQUEST_CHANGES | BLOCK | INCOMPLETE",
  "confidence": 0.0,
  "findings": [
    {
      "severity": "blocker | major | minor | nit",
      "category": "<see §3>",
      "file": "packs/ads/app/services/ads/ledger_check.rb",
      "line": 166,
      "claim": "one sentence",
      "ref": "<sha the reviewer read this file at: head or stack_tip>",
      "evidence": "file:line facts the reviewer opened and checked",
      "rule_id": "IP1 | SC3 | M32 | B23 | null",
      "fix": "the concrete change"
    }
  ],
  "narrative": "<= 500 words",
  "handoff_signals": {}
}
```

`line` is on `head_ref`. A finding without `file`, `line`, `severity` or `claim` is dropped as malformed. A PR-level finding uses `file: "PR"` and `line: 0`; it is well formed and the synthesizer keeps it.

**Supervisor envelope.** The supervisor's own hygiene checks (H1 to H3, SKILL.md step 4b) are passed to the synthesizer as one more envelope with `role: "supervisor-hygiene"` and the same shape as a reviewer envelope; its findings are PR-level (`file: "PR"`, `line: 0`) unless a changed file and line exist. It is not a required reviewer for rule 0b.

**Rule field mapping.** Envelopes carry `rule_id`; the review record (SKILL.md step 8) carries the same value as `rule`. The supervisor maps envelope `rule_id` to record `rule` and accepts a finding that already uses `rule`.
`loaded` lists the convention files the reviewer actually opened; a missing entry is reported as
`unverified` in the narrative, not silently skipped.

## 3. Category vocabulary

| Category | Use for | Floor |
|---|---|---|
| `correctness` | wrong result in production (limit before sort, double count, wrong rows, retry on duplicate key) | exempt |
| `compliance` | consent, opt-out, suppression, deletion, first-party gates | exempt |
| `data_loss` | a write that can lose or corrupt data | exempt |
| `wiring` | a field with no reader, a branch no input reaches, a state with no exit, a feature not connected (IP13, IP14, IP16) | exempt |
| `test_gap` | a spec that stubs the unit under test, a path with no spec (IP15) | exempt |
| `perf` | N+1, per-item writes, fan-out, job args, Redis as record, concurrency, heavy work in a request (IP1 to IP9, IP16) | exempt |
| `repo_convention` | repo conventions (snake_case JSON, `belongs_to`, `except:` filters, sort before cap, validate once) | exempt |
| anything else (`style`, `naming`, `docs`, reviewer-specific ids) | polish | dropped below `major` |

"Exempt" means a `minor` or `nit` in that category is kept and rendered at the severity the reviewer
gave. It counts toward the verdict only at `major` or above.

## 4. Synthesizer rubric (summary; `pr-tech-lead-synthesizer.md` is the implementation)

0. Severity floor: drop `nit`/`minor` unless the category is exempt (§3), the cluster exception
   applies, or the PR carries `review:all-findings`.
   0b. Any required reviewer `INCOMPLETE` → `ESCALATE_HUMAN`.
1. A `blocker` at confidence ≥ 0.85 → `BLOCK`.
1. Two `REQUEST_CHANGES` with overlapping findings → `REQUEST_CHANGES`, merged. Two findings overlap only when they share a file and an overlapping line range (or the same PR-level evidence) and describe the same defect; never merge on category alone.
1. Mixed non-blocker verdicts → `REQUEST_CHANGES`, `synthesizer_low_confidence: true`.
1. Contradicting hard verdicts → `ESCALATE_HUMAN`.
1. All `APPROVE` → `APPROVE`.
1. A single-reviewer `major` below 0.85 with no overlap → `APPROVE` with the finding advisory, except
   in `correctness`, `compliance`, `data_loss` or `wiring`, which give `REQUEST_CHANGES` with
   `synthesizer_low_confidence: true`.

The synthesizer checks a finding's evidence only against the snapshot the supervisor wrote with
`git show <ref>:<file>` into `snapshot_root/<ref>/<file>`, never against the working tree. It drops a
finding only when that snapshot exists and contradicts the claim; a missing snapshot keeps the finding
with `evidence_unverified: true`. It never writes files. The supervisor persists its output.

## 5. Who served each lens

After the run the supervisor records, per reviewer, the model that served it (`served_by`) using the
harness check `scripts/served-models.sh` (reads the shunt log for this session and time window). A lens
that asked for `gpt-6-astra` and was served by an Anthropic model is tagged `independence: same-family`.
