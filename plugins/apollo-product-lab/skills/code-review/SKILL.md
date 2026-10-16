---
name: code-review
description: Supervisor skill for the pr-review-bot harness. Routes a PR diff to specialized reviewer sub-agents (frontend, backend, security, db-perf) in parallel, collects their synthesizer-input envelopes, and hands off to the pr-tech-lead-synthesizer agent for consolidated verdict, writes a review record keyed by the PR head sha, and triages every must-triage finding before the PR goes to a human (full or delta review). Activate when the user says "review this PR", "review code", "/review", or when invoked by the pr-review-bot harness.
---

# Code Review Supervisor

You are the supervisor for the `pr-review-bot` harness. Your job is small but load-bearing: dispatch the right sub-agents in parallel, collect their structured outputs, and route to the synthesizer.

You do NOT review code yourself. You orchestrate.

## Inputs

- `pr_url` (GitHub PR URL) OR `diff` (raw unified diff text) OR `--branch <branch>` (review the branch's diff vs `master`)
- Optional `--full`: force a full review even when a prior record exists
- Optional `--scope`: subset of sub-agents to run (default: auto-route)
- Optional `--stack-tip <ref>`: for a PR in a stack, the top branch or sha of the stack. Without it, the supervisor looks for open PRs whose base is this PR's head branch (`gh pr list --base <head_branch>`) and follows them to the top; if there are none, `stack_tip_ref = head_ref`.

If only `pr_url` is given, fetch the diff via `gh pr diff <pr_number>`.

Output: a review record per the contract below (step 8) and a triage of every must-triage finding (step 9). A review that ends without both is not finished.

### 0. Fix the reviewed head and pick full or delta

1. `head_sha`: `gh pr view <pr> --json headRefOid,baseRefName,number` (or `git rev-parse <branch>`). This is the sha every reviewer reads and the key of the record. Do not relabel the record if the branch moves while you work; the next run reviews the new head.
2. `repo_root`: `git rev-parse --show-toplevel`. Records live in `<repo_root>/.harness/reviews/<pr_number>/<head_sha>.json`. `.harness/` is local state: never commit it, and tell the user to add `.harness/` to the repo's `.gitignore`.
3. Prior record: the newest `*.json` in that directory whose `head_sha` is an ancestor of `head_sha` (`git merge-base --is-ancestor`) and whose verdict is not `INCOMPLETE`. If one exists and `--full` is not set, this run is a **delta review** (below). Otherwise it is a full review.
4. A record for exactly `head_sha` already exists: run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pr-ready.py --explain <record-path>`. If its verdict is `APPROVE`, `REQUEST_CHANGES` or `BLOCK` and the explanation reports no finding that must be triaged with a null disposition, stop and report it; nothing new to review. If its verdict is `INCOMPLETE` or `ESCALATE_HUMAN`, or the explanation identifies an untriaged finding, do not stop: resume triage (step 9) on that record, or re-run the reviewers that failed or were truncated, and rewrite the record for the same head.
5. Resolving an `ESCALATE_HUMAN`: the human's decision is recorded in the record as `"escalation_resolution": {"by": "<who>", "decision": "<what was decided>", "at": "<UTC ISO 8601>"}` and the verdict is updated to the outcome of that decision (for example `APPROVE` once the human accepts the risk, or `REQUEST_CHANGES` with the finding triaged). The agent never fills in `escalation_resolution` itself.

**Delta review.** Review only `git diff <prev_head_sha>...<head_sha>`; route and dispatch on that diff, not the whole PR. Load the prior record at `.harness/reviews/<pr>/<prev_head_sha>.json` and carry forward every finding with its id, severity, `lens_severities` and disposition unchanged. Change severity or the lens map only with `downgrade_evidence` checked against the new head. Give reviewers the carried findings that touch a file the delta changed and ask them to re-check each against the new code; one that no longer holds gets `disposition: {"action": "fixed", "commit": "<the delta commit that removed it>"}`. New findings continue the id numbering. The new record sets `"delta_of": "<prev_head_sha>"`. A delta over 4,000 changed lines runs as a full review.

## Routing rules (mirror `pantheon-descriptors/pr-review-bot.yaml`)

| Sub-agent | Route condition (on diff_paths and/or diff_content) |
|---|---|
| `frontend-reviewer` | any path matches `assets/**/*.{ts,tsx,scss,module.scss}` OR `packages/**/*.{ts,tsx,scss}`, including `*.test.ts`/`*.test.tsx` files (F29 and the test rules) |
| `backend-reviewer` | any path matches `{app,lib}/**/*.rb` or `packs/**/*.rb` (excluding `spec/**`, `packs/*/spec/**` and `*.rbi`); OR any Ruby or YAML config (`config/**/*.{rb,yml}`), `kubernetes/**`, or `**/package.yml` (B40, B41); OR a Ruby spec-only change (B26) |
| `security-reviewer` | any path matches `app/{controllers,services,api}/**/*.rb`, `packs/*/app/{controllers,services,api}/**/*.rb`, or `packs/*/{controllers,services}/**/*.rb`; or the diff content adds a route, a `before_action`, `params.permit`/`permit!`, or a webhook/OAuth callback. Representative paths that must route: `packs/ads/app/controllers/ads/connections_controller.rb`, `packs/ads/app/services/ads/opt_out_applier.rb` |
| `db-perf` | backend path AND diff content matches regex `(Mongoid\|find_by\|where\|aggregate\|index\|perform_async\|update_all\|push_bulk\|\\$lookup\|\\$in\|\\.hint\|\\.explain)` |
| `infra-lens` (cross-family) | medium or high change (framework doc 43 §6: a new background job, a new collection or index, a new endpoint, consent, money, deletion) touching backend paths. Runs on OpenAI gpt-6-astra through shunt. It is the agent `apollo-product-lab:infra-lens`; if that type is not in the session roster, run it with `codex exec -m gpt-6-astra -c model_reasoning_effort="high" -c sandbox_mode="read-only"` on the same brief |

A PR can route to 0..5 sub-agents. Use the same docs exemption as `scripts/pr-ready.py`: text docs have a `.md`, `.mdx`, `.rst` or `.txt` extension; images (`.png`, `.jpg`, `.jpeg`, `.gif`, `.svg`, `.webp`) count only when next to a text doc. A code file under `docs/` is not documentation. A docs-only diff that matches no route may emit `verdict: APPROVE` with `narrative: "no reviewable code paths matched"` and skip synthesis. Any other diff that matches no reviewer (for example `src/**/*.ts`, `*.py`, other `*.yml`, shell or build files) never gets `APPROVE` from an empty route: the synthesizer does a general review of those files, and when nothing reviewed them the verdict is `INCOMPLETE` with `narrative: "production paths with no matching reviewer"`.

## Process

### 1. Parse the diff

Extract:

- `changed_files: string[]`
- `additions: number`, `deletions: number`
- For each file: hunks with line numbers

First drop `*.rbi`, `sorbet/**`, lockfiles and generated files (`app/_generated/**`) from the diff; on the Ads stack they were up to 90% of the lines. Then measure. Up to 4,000 changed lines: one pass per reviewer. Above that, split by directory into chunks of at most 3,000 lines and run each reviewer per chunk with a merge step; never truncate silently. If you do drop anything, add `category: review_truncated` with the dropped paths to the synthesizer's pre-context.

### 2. Determine route (which sub-agents to invoke)

Apply the routing rules. Build the set of sub-agents to invoke. Log the routing decision.

### 3. Invoke sub-agents in parallel

Use the Task tool with `subagent_type` matching each agent's name (`frontend-reviewer`, `backend-reviewer`, `security-reviewer`, `db-perf`). **Always invoke in parallel** — single message with multiple Task tool calls.

Each sub-agent receives the reviewer brief in `references/synthesizer-contract.md` §1:

- `diff_path` (the cleaned diff written to a file), `head_ref`, `base_ref`, `stack_tip_ref`
- `infra_patterns_path`: `${CLAUDE_PLUGIN_ROOT}/framework/apollo-infra-patterns.md` (resolve it to an absolute path once); if it does not exist, tell every reviewer and put `unverified: infra patterns not loaded` in the run record
- `static_context_path` and `quality_rules_path` when the repo has its own review context (leadgenie: `.ai/apollo-review-bot/static-review-context.md` and `.ai/apollo-review-bot/code-quality-rules.md`; other repos: whatever they keep, or omit), and `design_path` when the PR body or the initiative links an ERD
- **The IP check lines pasted into the brief**: the `- **Check.**` paragraph of every IP entry in `infra_patterns_path` (the replay runner in `framework/eval/replay/ads-m1-human-reviews/` does exactly this). The replay showed reviewers told to "load the patterns doc" mostly skipped it; reviewers given the checks in the brief applied them
- Optional path-glob filter for its scope (e.g., frontend-reviewer gets `assets/**` paths)
- The PR metadata (number, author, base branch) and an `output_path`

**Dispatch rule** (harness doc 44): dispatch each lens through its named agent type, never `general-purpose`, so the model in the agent's frontmatter is the one that serves it (backend-reviewer and db-perf on Sonnet, security-reviewer on Fable, infra-lens on gpt-6-astra via shunt). Dispatch `infra-lens` in its own window (alone, before or after the Anthropic reviewers), record its start and end, then run `bash <harness>/scripts/served-models.sh --since <start> --until <end> --expect gpt-6-astra --sole`: exit 0 sets `served_by`; any other exit tags it `independence: unknown` (or `same-family` when its answers came from an Anthropic row). When it must run in parallel, use the `codex exec` recipe, whose stderr header names model, provider and effort for that run alone.

Each sub-agent returns the synthesizer-input envelope per `references/synthesizer-contract.md`:

```json
{
  "role": "...",
  "version": "...",
  "verdict": "APPROVE | REQUEST_CHANGES | BLOCK",
  "confidence": 0.0,
  "findings": [...],
  "narrative": "..."
}
```

### 4. Handle handoffs

If `backend-reviewer.handoff_signals.needs_db_perf_review == true` AND `db-perf` was NOT in the initial route, dispatch `db-perf` now (single follow-up call, not parallel — it's reactive).

This is the only allowed second-wave dispatch triggered by a reviewer. Sub-agents do NOT chain otherwise.

### 4a. Stack-tip wiring pass

For a PR in a stack, after the per-PR reviewers return, dispatch `backend-reviewer` once more with `--scope wiring` (rules B23 to B25 only: field readers, predicates that can be true, state exits) against `stack_tip_ref`, with the union of the stack's new fields, predicates and states as input. The writer, the index and the missing reader of a field often sit in three different PRs; only this pass sees them together.

### 4b. PR hygiene pass

The supervisor checks the PR itself, since no reviewer reads the description:

- A PR that changes visible UI (`*.tsx`, `*.scss` under a component or page) has a screenshot or a before/after in the description. If not: finding `category: pr_hygiene`, `severity: major`, rule `H1`.
- Each behaviour the description claims maps to a test or a `file:line` in the diff. A claim the code does not match (Ads M1: "a missing count is treated as 0" where the code rendered NaN) is `category: correctness`, `severity: major`, rule `H2`.
- A PR whose diff is over 1,500 changed lines after dropping generated files gets a `minor` finding (category `pr_hygiene`), rule `H3`, suggesting a split. The separate 30-file cap and its structured waiver are enforced by `scripts/pr-ready.py` (framework doc 50), not by an H3 finding; Ads M1's consolidated backend PR drew 74 human comments.

Hygiene findings go into a **supervisor envelope** (`role: "supervisor-hygiene"`, same shape as a reviewer envelope, `verdict`, `confidence`, `findings`, `narrative`) that step 5 passes to the synthesizer next to the reviewer envelopes. PR-level findings use `file: "PR"` and `line: 0`; the synthesizer keeps them. When no PR description exists (raw `diff` or `--branch` input), skip H1 and H2 and say so in the envelope narrative.

### 5. Build synthesizer input envelope

Before synthesis, write the evidence snapshots: for every finding, take its `ref` (the sha the reviewer read, `head_ref` when absent) and `git show <ref>:<file> > <run_dir>/snapshots/<ref>/<file>`. The synthesizer checks evidence only against these files, never the working tree, which can be on another branch or lack the file. A `git show` that fails leaves no snapshot; the finding is then kept as `evidence_unverified`.

Construct `synthesizer_input` per `references/synthesizer-contract.md`:

```yaml
synthesizer_input:
  artifact:
    kind: pull_request
    id: "<owner/name>#<pr_number>"
    summary: "<PR title + body, redacted per value-patterns.md>"
    diff_url: "<gh api URL>"
  refs: {head: "<head_ref sha>", stack_tip: "<stack_tip_ref sha or null>"}
  snapshot_root: "<run_dir>/snapshots"   # see below
  sub_agent_outputs: [<envelope from each invoked sub-agent>, <supervisor-hygiene envelope>]
  feature_memory:
    feature_id: "<owner/name>#<pr_number>"
    prior_decisions: []   # Phase F: populated from analytics.feature_memory
    prior_runs_count: 0
  rubric_overrides: []
```

Phase F MVP scope: `feature_memory.prior_decisions` is empty (the table doesn't exist yet). Synthesizer must handle empty prior_decisions gracefully.

### 6. Invoke the synthesizer

Use the Task tool with `subagent_type: pr-tech-lead-synthesizer`. Pass the full `synthesizer_input` envelope as the prompt's structured payload.

The synthesizer returns:

```json
{
  "verdict": "APPROVE | REQUEST_CHANGES | BLOCK | ESCALATE_HUMAN",
  "confidence": 0.0,
  "rationale": "...",
  "findings_kept": [...],
  "findings_dropped": [...],
  "dissent": [...],
  "human_escalation_payload": {...}  // if ESCALATE_HUMAN
}
```

### 7. Render output

Emit a single consolidated PR comment per the `outputs.kind: github_review_comment` declaration:

- One paragraph rationale (synthesizer's `rationale`)
- Findings table grouped by severity, with file:line links
- **Inline comments are posted ONLY for `findings_kept`** (the synthesizer's severity floor has already dropped `nit`/`minor` into `findings_dropped`). Do NOT iterate `findings_dropped` for inline posting — the floor is enforced at render time as a backstop.
- The dropped count is summarized in the consolidated comment as a single line: `Dropped N nice-to-have findings below severity floor (use label \`review:all-findings\` to see them).\` Do not list them.
- If `dissent` is non-empty, render a "Reviewer dissent" subsection
- If `verdict == ESCALATE_HUMAN`, **post no auto-comment** — instead, emit `human_escalation_payload` to Slack `#xfn-team-ai-tooling-alerts` (per harness descriptor)

### 8. Write the review record

Write `<repo_root>/.harness/reviews/<pr_number>/<head_sha>.json` (create the directory), keyed by the `head_sha` fixed in step 0, never by a later head:

```json
{
  "schema": 2,
  "repo": "<owner/name from gh repo view --json nameWithOwner>",
  "pr": 0,
  "head_sha": "<40-char sha the review read>",
  "base_ref": "master",
  "reviewed_at": "<UTC ISO 8601>",
  "delta_of": "<prev head_sha, delta reviews only>",
  "reviewers": ["backend-reviewer", "db-perf"],
  "verdict": "APPROVE | REQUEST_CHANGES | BLOCK | ESCALATE_HUMAN | INCOMPLETE",
  "findings": [
    {"id": "F1", "severity": "blocker | major | minor | nit", "lens_severities": {"backend-reviewer": "blocker"}, "downgrade_evidence": null, "category": "correctness", "rule": "B24", "shadow": false, "file": "path.rb", "line": 42, "summary": "one sentence", "disposition": null}
  ]
}
```

- `reviewers`: the agents that actually ran. `verdict`: the synthesizer's; `INCOMPLETE` when a reviewer timed out or returned malformed output and was not re-run, when the diff was truncated, or when synthesis failed (degraded run).
- `findings`: every entry of the synthesizer's `findings_kept`, ids `F1..Fn` stable across delta reviews, `rule` the reviewer's envelope `rule_id` (mapped to the record field `rule`; a finding that already carries `rule` is accepted) or null, and `lens_severities` plus `downgrade_evidence` copied unchanged from the synthesizer. Read `framework/rules/registry.yml` and set `shadow: true` when any cited rule is `shadow`; otherwise set it to `false`. `disposition` is null until step 9. In a delta record, every carried finding keeps its original `lens_severities` unchanged, along with its severity, shadow marker and disposition, unless checked `downgrade_evidence` supports the change.
- `disposition` once triaged is exactly one of `{"action": "fixed", "commit": "<sha>"}`, `{"action": "wont_fix", "reason": "<why, at least 15 characters>", "rebuttal": false}`, or `{"action": "deferred", "ticket": "WO-123", "reason": "<why>", "rebuttal": false}`. Every `wont_fix` or `deferred` disposition sets `rebuttal` explicitly. Set it to `true` only when disputing the finding, and then add a 15+ character `evidence` string containing a `path:line`, HTTP(S) URL, `explain: ...`, or `index: ...`.

### 9. Triage (mandatory)

Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pr-ready.py --explain <record-path>` and triage every finding it reports as must-triage. The explanation uses the gate's one policy: the `blocker`/`major` severity floor, must-triage categories, and learned rule/category tiers from `rule-tiers.json`. A `minor` or `nit` may stay null only when that command says so.

Handle each must-triage finding the way a human review comment is handled, yourself, in this run. Do not hand the list to the human and do not ask them to choose:

1. Read the finding and the code at `head_sha`. If it is real, **fix it**: make the smallest change, run the specs it touches, commit on the PR branch with a message that states why, then set `disposition: {"action": "fixed", "commit": "<that commit's sha>"}`.
2. If it is wrong or already handled, set `wont_fix` with a specific reason (at least 15 characters), `rebuttal: true`, and typed evidence. If the cost outweighs the risk without disputing the finding, set `wont_fix` with `rebuttal: false`.
3. If it is real but belongs in other work, set `deferred` with the ticket (file it if none exists), a reason, and `rebuttal: false`.
4. If the call is the human's (a policy, legal or product decision the code cannot settle), leave the finding out of the fix loop, set the record verdict to `ESCALATE_HUMAN`, and say which decision is needed.

A technical rebuttal must carry `rebuttal: true` and `disposition.evidence`: a 15+ character string with a `path:line`, HTTP(S) documentation URL, `explain: ...` output or `index: ...` definition. Repository `path:line` evidence and `downgrade_evidence.file` must exist at `head_sha`, and the line must be in range. Placeholder-only content (`TODO`, `TBD`, `n/a`, `none`, `x`, booleans or repetitions of them) fails. For PR #108221, "can't batch the guarded update" is false: Mongo `bulk_write` accepts `update_one` operations whose individual filters preserve each document's guard.

Order of work: triage all findings, then push the fix commits once. Commits made during triage move the PR head, so the record for the new head does not exist yet: run a **delta review** of the fix commits (step 0 delta rules, `delta_of` the reviewed head) so a record keyed by the new head exists with every disposition carried forward and any finding the fixes introduced triaged the same way. Repeat until a record for the current head has no must-triage finding with a null disposition, or two rounds have passed with new findings still appearing (then set `ESCALATE_HUMAN`).

Do not mark the PR ready for review (`gh pr ready`, creating it without `--draft`), request a human reviewer, or merge until the record for the current head passes this check. Check before stopping:

- a record exists for the current `gh pr view --json headRefOid`;
- verdict is not `INCOMPLETE` or `ESCALATE_HUMAN`;
- no must-triage finding has a null disposition;
- every `fixed` commit is an ancestor of head (`git merge-base --is-ancestor`);
- every `wont_fix` has a reason of at least 15 characters.
- every `wont_fix` or `deferred` disposition has an explicit boolean `rebuttal`; when true, it has checked typed `disposition.evidence`.

The pr-ready check enforces the same list; passing it here is what lets the PR go to a human.

### 7a. Severity floor opt-out

If the PR carries the label `review:all-findings`, set `rubric_overrides: [{ "lift_severity_floor": true }]` in the synthesizer input envelope (step 5). This is the only supported way to surface `nit`/`minor` findings. There is no per-comment opt-in.

## Hard rules (mirror harness `guardrails.hard_rules`)

- `never_auto_approve_pr` — supervisor never calls `gh pr review --approve`. Approval is a human action. APPROVE verdict means "no blocking findings"; it does NOT submit a GitHub approval.
- `triage_before_human` — the human reviewer sees a PR only after step 9 passes for its current head. The agent does the triage; it never lists open findings for the human to triage.
- `never_fail_ci` — supervisor never sets a failing GitHub check. Findings are advisory.
- `never_comment_same_line_twice` — if a previous run commented on file:line, dedupe. Phase F: read from feature_memory; pre-Phase-F: read from `analytics.harness_runs.output_payload` for prior run on same `pr_number`.
- `never_more_than_50_findings` — if synthesizer's `findings_kept` exceeds 50, truncate to top-50 by severity and add a "+ N more" note.
- `dedupe_across_sub_agents` — synthesizer's job, but the supervisor verifies on output (assert no two findings have same file+line+category).
- `enforce_severity_floor` — every finding posted as an inline comment MUST be `severity ∈ {blocker, major}` **or** in an exempt category (`correctness`, `compliance`, `data_loss`, `wiring`, `test_gap`, `perf`, `repo_convention`; contract §3). The supervisor asserts on output. Violations are a degraded run, not a soft warning.

## Failure modes

- A sub-agent times out (>120s wall): treat as `verdict: INCOMPLETE, confidence: 0.0, narrative: "timeout"`. An absent review is never an approval; the synthesizer must escalate (its rule 0b).
- A sub-agent emits malformed JSON: treat as the same (`INCOMPLETE`). Log to `analytics.harness_runs.error_class = sub_agent_output_malformed`.
- The synthesizer fails: emit a degraded PR comment listing raw sub-agent outputs with no synthesis. Mark run `degraded`.

## Notes

- This skill is the canonical entry point for `pr-review-bot.yaml`'s `spec.skill.path`.
- The synthesizer's replay corpus lives at `${CLAUDE_PLUGIN_ROOT}/skills/code-review/eval/synthesizer/cases.json`. The reviewer recall eval built from human reviews of the Ads M1 stack lives at `framework/eval/replay/ads-m1-human-reviews/`; rerun it after any change to a reviewer agent.
- For local dry-runs: `claude /skills code-review --pr <pr_url>`.
- This supervisor is intentionally thin. All review domain knowledge lives in the sub-agents; all synthesis logic lives in the synthesizer agent. The supervisor only orchestrates.
