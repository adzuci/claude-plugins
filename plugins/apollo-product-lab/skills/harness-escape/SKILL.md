---
name: harness-escape
description: "Find, adjudicate and fix escapes: findings on harness-built PRs and pages that changed the approach or found a defect after a gate passed. Modes: scan, adjudicate, fix, report (framework doc 43 section 2)."
disable-model-invocation: true
---

# Harness escape

An **escape** is a finding by a person or a bot on a harness artifact, after a gate passed, that
changes the approach or finds a defect. Nits are not escapes. A changed requirement is recorded
separately. Read `${CLAUDE_PLUGIN_ROOT}/framework/43-learning-loop-and-review-defaults.md` §2 first.

**Storage first** (doc 45 §2). Before any read or write of the record, resolve the mode: a session with no Bash and no Write tool is `notion`; otherwise run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/storage.py" detect` (with `--surface` from the profile's `surface:`, and `--profile <file>` when the profile came from Notion) and print its `say` line once. In `notion` mode every `.ai/<initiative>/...` path in this file names a record page under the initiative's records root (doc 45 §3): write with `storage.py to-notion` and the `notion-create-pages` call it prints, read with `notion-fetch` then `storage.py from-notion`, append ledger events with `storage.py ledger-entry`, and skip git, gh, local `shasum` and `record-sync.sh` (Notion is already shared). In `local` mode the rest of this file applies unchanged; on claude.ai/code, where the profile came from Notion, export `HARNESS_PROFILE=<the fetched profile file>` before any `record-sync.sh` call so team sync sees it (doc 45 §4).

Usage:

```
/apollo-product-lab:harness-escape scan [initiative]
/apollo-product-lab:harness-escape adjudicate <candidate-id> escape|not|changed-requirement
/apollo-product-lab:harness-escape fix <escape-id>
/apollo-product-lab:harness-escape report [initiative] [--month yyyy-mm]
```

`harness-intake` and `harness-snapshot read` run the scan mode at their start by reading this file
and following it.

**Repo state.** Resolve the repo root first with `git rev-parse --show-toplevel` (doc 43 §10); every `.ai/` path is relative to that root, not to the current subfolder. No git repo, or no `.ai/<initiative>/` under the root: say "escapes need .ai/<initiative>/ in a repo; skipped" in one line and stop. Do not run gh or write files.

## Scan mode

Collects candidates. It never edits a rule, a lens or a check. Run it after the team sync (the caller
pulls first), never before.

1. **State.** Read `.ai/<initiative>/escapes/state.yml`. It holds one cursor per source, not one global
   timestamp: `prs: {<number>: <newest comment or review time collected>}`,
   `notion: {<page id>: <newest comment time collected>}`, `search_since: <time>`, and `pending:` (a list
   of sources a previous scan could not finish). An absent file means 30 days ago for every source.
   The initiative is the argument, else the profile's `default_run` prefix, else every
   `.ai/*/harness-manifest.md` under the repo root.
2. **Find stamped PRs** (stamp: `Harness run: <initiative>/<run-id>` in the PR body, doc 20 §8c):
   `gh search prs --repo <owner>/<repo> "\"Harness run: <initiative>/\"" --updated ">=<search_since date>" --limit 20 --json number,url,updatedAt,state`.
   The repo is the root's `origin`. Put `pending` PRs first. At most 20 PRs per scan; any PR found but
   not scanned is added to `pending`, and the report says how many.
3. **Pull findings per PR**, people and bots both, **every page**:
   `gh api --paginate repos/<owner>/<repo>/pulls/<n>/reviews`, `.../pulls/<n>/comments`,
   `.../issues/<n>/comments`. Keep items newer than that PR's cursor. Wrap each call in `timeout 5`
   (`gtimeout 5` on macOS with coreutils) when that command exists. A call that fails or times out
   leaves that PR's cursor where it was and adds the PR to `pending`; it is not retried in the same scan.
4. **Notion pages.** If the Notion connector is present, search for the footer
   `Harness run: <initiative>/` and read every page of comments on pages edited since their cursor. If
   the connector is absent, add `notion` to `pending` and say so in the report.
5. **Later revisions.** For each snapshot in `runs/*/index.md` with a newer superseding snapshot, add
   one candidate naming both files.
6. **Dedupe and filter.** The source id is the PR comment or review id, or the Notion comment id.
   Skip any source id already in `candidates.md`. Drop pure nits (formatting, typos, naming with no
   behaviour change) and comments by the PR author. Keep approach changes, requested-changes reviews,
   defects and bot findings.
7. **Write only on change.** If there are new candidates, append one row each to
   `.ai/<initiative>/escapes/candidates.md`:
   `| id | source id | source (PR url#comment or Notion page) | author kind (person / bot) | quote (one line) | artifact | run | status: open |`.
   Ids are `c<n>`, increasing. Advance each source's cursor only to the newest item actually
   collected, update `pending`, and set `search_since` only if the search itself succeeded. If nothing
   changed, write nothing, so the initiative stays clean for the next sync.
8. **Share at the next boundary.** Do not commit or push from the scan. The changed files go out with
   the run's next record write (`record-sync.sh push`, which commits all of `.ai/<initiative>/`).
9. **Report** one line: candidates added, PRs scanned, sources pending. Do not adjudicate.
   At this boundary, run `post-update.py --stage H.escape --summary <that-line> --links <candidate-record-links> --initiative <initiative> --run <run-id> --event <stage-event-id> --agent <stage-agent> --outcome <stage-outcome> --profile <profile>` and execute every call in its JSON plan.

## Adjudicate mode

Only the maintainer named in `harness-manifest.md` (`escape_maintainer:`, the initiative's EM by
default) adjudicates. If the person running this is not that maintainer, say so and stop. If the field
is missing or `unowned`, adjudicate nothing: ask "Who adjudicates escapes for this initiative? Usually
the EM.", write the answer into `harness-manifest.md`, and continue only if that person is the one
running this. Candidates stay `open` until then.

- `escape`: assign `e<n>`, name the owning stage (the stage whose declared job covered the finding)
  and whether that stage had the evidence at the time. If it did not, the escape is recorded but not
  counted against the gate.
- `not`: record the reason in one line.
- `changed-requirement`: move the row to `.ai/<initiative>/escapes/changed-requirements.md`.

Update the row's status. For an escape, append one Stage H ledger event
(`python3 ${CLAUDE_PLUGIN_ROOT}/framework/ledger/append.py <initiative> --stage H.escape --outcome rejected ...`,
evidence = the escape id and source) and route it as a rejection to the owning stage
(`agents/product-orchestrator.md`, "Routing rejections").
Run `post-update.py --stage H.escape --summary <adjudication-summary> --links <escape-source> --initiative <initiative> --run <run-id> --event <stage-event-id> --agent <stage-agent> --outcome <stage-outcome> --profile <profile>` and execute its JSON plan.

## Fix mode

1. Read the escape and its source. Choose the cheapest fix that would have caught it, in this
   order: an executable check (spec, cop, CI job); a row in the source checkout's `framework/platform-rules.md` with a
   real source; a lens checklist row in doc 34 or the lens agent; an owning-team trigger.
2. Verify the source says what the rule says. If it does not, soften the rule or do not add it.
3. Write the escape record in the source checkout's `plugins/apollo-product-lab/framework/eval/escapes/` per its README.
4. **Replay**, only if the originals are archived (artifact bytes, repo revision, evidence,
   instructions, model and tool settings): run the old and new check on the defective case, its
   corrected version, and one held-out variant. Executable checks run once; model checks run 3
   times. Record detection and false-alarm counts. Without the originals, mark the record
   `kind: retrospective` and write "retrospective case, not replay".
5. **Write into a source checkout, never the installed plugin.** Framework files live in the
   `apollo-product-lab` plugin of `apolloio/claude-plugins`. Find or make a checkout of that repo
   (not `~/.claude/plugins/...`, which is the installed copy and is replaced on update), create a
   branch, write the record and the rule there, and propose a PR. Every write in this mode goes to
   that checkout's `plugins/apollo-product-lab/framework/`, never to `${CLAUDE_PLUGIN_ROOT}`.

## Report mode

From `candidates.md`, the escape records and the ledger: escapes per run by owning stage, false
alarms per check, rework PRs (closed and rebuilt, or reopened for an approach change), and open
candidates older than 14 days. One table, then three lines on what changed since last month.

## Hard rules

- Collection never edits rules. Only `fix` writes a fix, and only after `adjudicate` said `escape`.
- Bot findings are kept. A review bot catching a missed secret is an escape.
- A gate is not blamed for evidence it never had.
- No names of reviewers in escape records; use roles ("a senior reviewer").
- Bounded: 20 PRs per scan, 5 seconds per network call where the tool allows.
