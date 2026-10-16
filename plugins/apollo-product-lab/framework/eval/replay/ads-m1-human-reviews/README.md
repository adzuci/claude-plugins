# Ads M1 human-review replay eval

Measures how many past human review comments our AI code reviewers (backend-reviewer, frontend-reviewer, security-reviewer, db-perf) would have caught, so every checklist or rule change can be scored before it ships.

## What it measures

Each case is one human review comment on an apolloio/leadgenie WO-1174 (Apollo Ads M1) PR that a static reviewer should have caught (`preventable_by: static-reviewer` in the mining table). A case records the PR, the exact head commit the human reviewed (`commit_id`), the base sha, file and line, a short excerpt, the category, and the rule ids that should have fired. No diffs, no full comment bodies, no secrets.

A reviewer finding catches a case when:

- same file, line within +-8 (review-body and issue-comment cases are file-level: any file), and
- the finding cites one of the case's rule ids (`rule` or `rule_id`); or, when it cites no rule, it has the same canonical category and its claim shares a meaningful token with the case excerpt.

Each finding catches at most one case (greedy, smallest line distance first), so one finding near three comments counts once.

Cases with `rule_gap: true` had no checklist rule when mined (28 of 187). They can only match by category, so they are reported separately and do not count against the pass bar.

Noise is the count of findings that match no case. It is not a precision metric: a finding with no human comment may still be right.

Schema: `review_replay_case` in `../cases.schema.json`.

## Run

```bash
cd plugins/apollo-product-lab/framework/eval/replay/ads-m1-human-reviews
OUT=/tmp/ads-replay            # any scratch dir

# 1. Build per-group diffs and reviewer briefs (needs gh auth). --pr and --limit narrow the run.
python3 run_replay.py prepare --out $OUT [--pr 106754] [--limit 5]

# 2. For each group in $OUT/groups.json, read <group>/brief.md and dispatch the listed reviewer
#    agents (named agent types, in parallel, per code-review skill). Each writes its findings JSON
#    to the path in the brief. The briefs hold no human comments; do not add them.

# 3. Score
python3 run_replay.py score --runs $OUT     # writes $OUT/report.md and report.json

python3 -m unittest                          # matcher, routing and scoring tests
```

`prepare` groups cases by (PR, commit_id). Diffs come from `gh api compare base...commit_id` with `*.rbi`, `sorbet/**`, lockfiles and generated files removed. Routing matches the code-review skill. Re-running `prepare` with another `--pr` adds to the same `groups.json`.

The report gives overall recall, recall where a rule exists, recall for rule-gap cases, recall per rule id, per category, per PR, the list of misses with comment urls, and the noise count.

## Pass Bar

The report passes when recall is at least 0.8 on cases whose rule exists and the declined-case false-positive rate is at most 0.15 (override with `--max-fp-rate`). This replay is run manually and does not gate merges until CI exists. Rule-gap recall is reported separately: a gap case missed means the rule must be written, while a rule-exists case missed means the rule or its wording is not working.

## Adding cases

Cases come from the learn-from-review loop: each new human comment that a static reviewer should catch becomes a case, with the rule ids that should have caught it (empty when the rule does not exist yet; once the rule lands, update `expected_rules` and clear `rule_gap`). `build_cases.py --mining <mining.md>` rebuilds the file from a mining table plus the GitHub API and is how the first 187 were produced; hand-appended lines must satisfy the schema (the unit test checks every line).

Known limit: a finding that flags the right line with a different category and no rule id counts as a miss. Reviewers must emit rule ids.

## Block And Warn Tiers

`python3 build_tiers.py` labels every case by what we did after the human comment:

- `fixed`: the commented lines changed in a PR commit made after the comment (comparison starts at the first PR commit after the comment's `created_at`, not at the reviewed commit), or our reply says so.
- `declined`: our reply says we are not doing it (won't, keeping, intentional and similar).
- `deferred`: our reply says follow-up, ticket, later or defer, and the lines did not change.
- `unknown`: everything else, including a failed API or compare call and acknowledgements such as "looking into it". A failure never becomes `declined`.

`outcomes-overrides.json` holds audited labels with a reason and is applied last. The script writes `outcomes.json` and `rule-tiers.json`, which `scripts/pr-ready.py` reads. Use `python3 build_tiers.py --from-outcomes` to rebuild tiers from stored outcomes without GitHub access. Use `python3 build_tiers.py --relabel-stored` to reclassify stored replies and movement flags, then rebuild both generated files without GitHub access.

A rule with any fixed case blocks. A category blocks when it is a must-triage category, or when a fixed case in that category is `blocker` or `major`; otherwise its learned tier warns. Deferred and unknown outcomes do not create warn tiers. Category keys use `category:<canonical>`.

On the stored Ads M1 history: 100 fixed, 20 declined, 67 unknown. There are 67 blocking rule/category keys and 9 warning keys (B14, B40, B45, M5, M15, P10, plus the design, docs and security category fallbacks).

## Scoring

`run_replay.py score` reads `outcomes.json`. Fixed and deferred cases are recall cases. Declined cases are "should not flag" and determine the false-positive gate. Unknown cases are reported separately.

## Limits

This is a regression corpus, not held-out evidence. `apollo-infra-patterns.md` contains examples taken from these same reviews, so recall here shows the rules still catch what they were written from, not how they will do on new PRs. Scoring the whole pipeline through synthesis and triage remains future work.
