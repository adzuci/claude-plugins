# 50: The pr-ready review gate

A PR must not be marked ready, handed to a human reviewer, or merged until the AI review has run on the current head and every finding that matters has been dealt with. The gate is `scripts/pr-ready.py`.

## The review record

The `code-review` skill writes one file per review:

`<repo root>/.harness/reviews/<pr_number>/<head_sha>.json`

`.harness/` is local. Add it to the repo's `.gitignore`; never commit it.

```json
{
  "schema": 2, "repo": "apolloio/leadgenie", "pr": 108365, "head_sha": "<40-char sha the review read>",
  "base_ref": "master", "reviewed_at": "2026-10-16T10:00:00Z",
  "reviewers": ["backend-reviewer", "db-perf", "security-reviewer"],
  "size_waiver": {"reason": "mechanical rename cannot be split", "approver": "Name"},
  "verdict": "APPROVE | REQUEST_CHANGES | BLOCK | ESCALATE_HUMAN | INCOMPLETE",
  "findings": [
    {"id": "F1", "severity": "blocker | major | minor | nit", "lens_severities": {"backend-reviewer": "blocker"},
     "downgrade_evidence": null, "category": "correctness | wiring | perf | ...",
     "rule": "B24", "file": "packs/ads/app/services/ads/x.rb", "line": 42,
     "summary": "one sentence", "disposition": null}
  ]
}
```

The gate also counts review files. It excludes the same generated paths as doc 20 §8b. More than 30
blocks in block mode and warns in warn mode unless the current-head record has a valid `size_waiver`.
The waiver is optional; when present it needs a named `approver` and a `reason` of at least 15 characters.

A record counts as a review of the head only when it is valid: `schema` is the integer `1` or `2`; it has a valid string `verdict`, a findings list and a string reviewers list; its `head_sha` equals the head it is filed under; its `repo`, when present, is the PR's repo; and `reviewers` is non-empty unless the diff is docs only. Anything else is treated as no review. Schema 1 remains readable for migration: warn mode accepts it with an instruction to re-run the review, while block mode rejects it. Schema 2 requires every finding's non-empty `lens_severities` map.

Every finding copies the synthesizer's non-empty `lens_severities` map. A structured `downgrade_evidence`
object has `file`, positive integer `line`, and a 15+ character `why`. Its recorded severity is the highest
lens severity unless that evidence explains why the cited snapshot line refutes the higher rating.

A finding is triaged when `disposition` is one of:

- `{"action": "fixed", "commit": "<sha>"}`: the commit must be an ancestor of head.
- `{"action": "wont_fix", "reason": "<why, at least 15 characters>", "rebuttal": false}`
- `{"action": "deferred", "ticket": "WO-123", "reason": "...", "rebuttal": false}`

When `wont_fix` or `deferred` means the finding is technically wrong or already handled, add
`"rebuttal": true` and `evidence`: a 15+ character string containing a `path:line`, HTTP(S) URL,
`explain: ...`, or `index: ...`. Every `wont_fix` and `deferred` disposition sets `rebuttal` to a boolean.
Placeholder-only evidence is invalid. Repository `path:line` references must exist at `head_sha` and
name an in-range line. A narrow keyword detector only emits a warning hint when `rebuttal` is false.

After new commits, a delta review writes a new record for the new head with `"delta_of": "<previous head_sha>"`. The gate loads that sibling record and requires every prior finding to retain its severity and `lens_severities`; a change needs checked `downgrade_evidence`. The evidence file must exist at the new head and its line must be in range.

## What must be triaged

A finding needs a disposition when its severity is `blocker` or `major`, or its category is `correctness`, `compliance`, `data_loss`, `wiring`, `test_gap`, `perf` or `repo_convention`. A minor or nit in any other category may stay untriaged.

## The seven fail reasons

1. No valid record for the current head (the gate says which head the newest record covers and how many commits behind it is).
2. The verdict is `INCOMPLETE` or `ESCALATE_HUMAN`.
3. A must-triage finding has no disposition.
4. A `fixed` disposition names a commit that is not an ancestor of head.
5. A `wont_fix` has no reason.
6. A finding is recorded below a lens's severity without `downgrade_evidence`; the restored severity also controls the severity floor.
7. A `wont_fix` or `deferred` disposition lacks an explicit boolean `rebuttal`, or `rebuttal: true` lacks checked evidence.

(`deferred` without a ticket and reason is also reported, under the same rule as reason 5.)

## Modes

Resolution order: `--mode` flag, then env `HARNESS_PR_READY_MODE`, then `<repo>/.harness/config.json` (`{"pr_ready_mode": "block"}`), then the default `warn`.

- `block`: prints the numbered list and exits 2. In the Claude Code hook this stops the command and shows the list to the model. A `nit` or `minor` whose only triage reason is a learned `docs` or `design` category tier remains a warning.
- `warn`: some problems still block, the rest are shown as context.
  - Always blocks, in both modes: no valid review on the current head, an `INCOMPLETE` or `ESCALATE_HUMAN` verdict, a bad disposition, a severity downgrade without evidence, a technical rebuttal without structured evidence, any untriaged `blocker` or `major` finding (including a lens severity restored by the gate; severity is a floor that no learned tier lowers), and any untriaged finding whose rule or category is in the block tier.
  - The tiers are learned from history: a rule blocks when humans flagged that kind of issue on a past PR and we went on to fix it. A rule or category warns only when every case with a known outcome was declined; cases with an unknown outcome count for nothing. The lookup is the finding's rule id (`rule` or `rule_id`), then `category:<canonical category>`, then the must-triage set. The tiers live in `framework/eval/replay/ads-m1-human-reviews/rule-tiers.json` (rebuilt by `build_tiers.py`); a repo can override them with `<repo>/.harness/rule-tiers.json`.
  - Warn-tier findings do not block. The hook returns them as `additionalContext` (exit 0), which Claude Code shows next to the tool result, and the agent triages each one like a human review comment before asking a human to review.
- Fail closed: if the gate cannot decide (PR not resolvable, `gh` or `git` fails, an error, or the command targets a PR in another repository), block mode exits 2 with the reason, and warn mode adds context saying the gate could not run and why.

When clean it exits 0 with one line.

## Gated commands (Claude Code hook)

`hooks/hooks.json` registers a `PreToolUse` hook on the `Bash` tool running `scripts/pr-ready.py --hook`. It gates:

- `gh pr create` without `--draft` or `-d`
- `gh pr ready` (not `--undo`)
- `gh pr edit ... --add-reviewer`
- `gh pr merge`

The command is split on `&&`, `||`, `;`, pipes, unquoted newlines, backticks, `$( )` and `( )`/`{ }` groups, and each part checked. `env`, `sudo`, `nohup`, `xargs`, `time` and similar wrappers, and `bash -c`/`eval` strings, are looked through. Value flags (`--title`, `--body`, `--add-reviewer` and others) consume the next token, so `--title --draft` is not a draft and `--add-reviewer bob 12` targets PR 12. `-R/--repo owner/name` and PR URLs are honoured: the record is checked only when that repository is the local one, otherwise the gate cannot run. A preceding `cd DIR` in the chain sets the directory. If an earlier `git push` publishes to the resolved PR head branch, the local HEAD is checked; a push to another destination leaves the check bound to the PR's remote head. Bare `git push` is bound through the current branch's upstream.

Block-level problems use exit code 2 with the list on stderr, which Claude Code shows to the model. Warn-level items use `hookSpecificOutput.additionalContext` with exit 0, which appears next to the tool result without blocking: <https://code.claude.com/docs/en/hooks>. The gate fails closed as described under Modes.

## Threat Model

The gate catches honest mistakes by an agent following the workflow: forgetting to review, reviewing an old head, dropping provenance, citing stale or nonexistent snapshot lines, leaving rebuttal intent implicit, leaving a blocker untriaged, or running against the wrong directory or PR. It does not try to stop deliberate evasion such as constructing shell commands to hide a `gh` call or forging review records. Those attacks are out of scope; the provenance, evidence and rebuttal checks validate workflow records rather than make them tamper-proof. The conservative raw-text detector blocks only commands it notices but cannot safely bind to a target. Reviews of this gate should file evasion-only bypasses as minor findings.

### `gh pr create`

The PR does not exist yet, so the record is keyed by branch and head instead of PR number:

`.harness/reviews/branch-<branch>/<head_sha>.json` (a `/` in the branch name becomes `__`).

Either write that record (run the review before creating), or, the usual route, create the PR with `--draft`, run the review there, then `gh pr ready`.

## Other hosts and git hooks

The script has no Claude dependency. Call it by hand or from your own flow:

```
python3 scripts/pr-ready.py --pr 123 --mode block
```

To enforce it on every push, call it from a `lefthook` `pre-push` command (it exits 2 in block mode) and, if you like, set `HARNESS_PR_READY_MODE`.

## Rules added from the Ads M1 rule gaps

The human comments that no rule covered now map to new rules: backend B38 to B46 (locks and reapers, thin workers, staging-only config, pack privacy, outside-API error mapping, provider contracts, stale comments, pack log format, discarded guarded-write counts), frontend F25 to F30 (state across flows, duplicate state, backend value mapping, colour tokens, fixed-time waits, RTK Query and tooltips), db-perf M41 to M44 (Elasticsearch point-in-time, shard key spread, per-item writes, partial-index query bounds), and the code-review skill's hygiene pass H1 to H3 (screenshots on UI PRs, description claims backed by tests, split very large PRs). B42 comes from a production bug, not a comment: a Google 403 for a disabled API marked a working connection expired.
