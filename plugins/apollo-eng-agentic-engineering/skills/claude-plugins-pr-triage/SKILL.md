---
name: claude-plugins-pr-triage
description: Triage all open apolloio/claude-plugins PRs into easy approvals, stale closure candidates, and high-ROI work; read-only, with an optional HTML report.
disable-model-invocation: true
---

# Claude Plugins PR Triage

Build a current, read-only triage of open pull requests in `apolloio/claude-plugins`.
Never approve, close, merge, comment on, label, or modify a pull request in this skill.

## Usage

```
/apollo-eng-agentic-engineering:claude-plugins-pr-triage
/apollo-eng-agentic-engineering:claude-plugins-pr-triage --html
```

Default output is Markdown in the chat. With `--html`, also write one self-contained
HTML file and report its path. See `references/html-report.md`.

## Collect Evidence

1. Verify `gh` is installed and authenticated. Get the current user with
   `gh api user --jq .login`; call them "you" below.
1. Run `python <skill-dir>/scripts/collect_prs.py` (add `--table` for TSV). One bulk
   `gh pr list --json` with commits or checks hits the GraphQL node limit, so the
   helper lists PRs, then fetches commits, checks, reviews, changed paths, and
   CODEOWNERS per PR. If it fails, fall back to per-PR `gh pr view <n> --json commits,statusCheckRollup,latestReviews` and `gh pr diff <n> --name-only`.
   Fields and rules:
   - `last_commit_date` replaces `updatedAt` in the Updated column (labels and draft
     toggles move `updatedAt`). `stale_candidate` means the last commit is before the
     cutoff printed in the header (today minus 42 days).
   - `checks`: failing = any failed, timed-out, cancelled, or action-required run or
     errored status; pending = any run not completed; else green. Contexts with no
     conclusion (for example CodeRabbit) are ignored.
   - `owners`: union of CODEOWNERS owners over changed paths (most specific entry wins,
     `*` default). Shared files (README, inventory, manifests, `.github/*`, release
     files, `tests/test_marketplace.py`) are ignored unless they are the only changes.
   - `stacked_on`: from `baseRefName` (base not `main`), with the parent PR number when
     found. Do not infer stacking from PR bodies.
   - `approvals_newer_than_head`: an approval submitted after the last commit.
1. For PRs you authored that are non-draft, use Glean once per PR (query
   `claude-plugins pull/<n>`, `app: slack`, `updated: past_2_weeks`, `num_results: 3`)
   to find a Slack review-ask thread. Treat unrelated threads as none found. Record the
   link, who was asked, and last activity. Replies and reactions may not be exposed:
   then say "activity unknown" rather than guessing. Dormant means no replies or
   reactions for 3+ business days, or no thread. If Glean is unavailable, say so.
1. For likely recommendations, read current reviews and unresolved substantive
   comments. Conflicts, failed checks, change requests, and high-confidence review
   findings are blockers. An old approval does not cover a rewritten head
   (`latestReviews` has no commit oid, so compare review `submittedAt` to the head commit
   date; the helper gives `approvals_newer_than_head`). Unresolved threads:
   `gh api graphql -f query='query($n:Int!){repository(owner:"apolloio",name:"claude-plugins"){pullRequest(number:$n){reviewThreads(first:50){nodes{isResolved isOutdated path comments(first:1){nodes{author{login} body}}}}}}}' -F n=<n>`.
   Count threads with `isResolved` false and `isOutdated` false.
1. Use concrete dates. Report unavailable fields as unknown, never healthy.

## Classify

Recommend a PR in a group only when evidence supports it:

- **Easy to approve**: non-draft, mergeable, checks green, no unresolved substantive
  findings, small or straightforward enough for a bounded review. A PR that still needs
  a code-owner review counts if otherwise green; green bot release PRs qualify. Large
  approved PRs go to "Ready" with the size noted. Separate truly ready PRs from
  near-ready ones that need one specific fix.
- **Stale and can be closed**: abandoned or superseded work with no recent owner
  motion. A draft or conflicted branch is only a hint, not the evidence. Phrase closure
  as a recommendation, never as certainty about owner intent.
- **High ROI**: likely organizational value relative to the work needed to review and
  land it. Rank by impact, reach, risk reduction, and remaining effort. High ROI does
  not mean ready; name the blockers.

**Complexity is never a reason to close.** Size, difficulty, a large diff, merge
conflicts, or failing checks alone do not make a PR stale; they mean it needs a split,
a rebase, or a fix. Recommend closure only for abandonment (no owner activity for 6+ weeks) or supersession (name the PR or `main` change that
replaced it). Valuable big PRs belong in **High ROI** with the blocker named.

Last owner activity = last commit by a non-bot author, or a reply by the author; ignore
bot and CI commits. Stale needs the last commit before the cutoff and no author reply or
stated intent. For an approved but abandoned PR, recommend asking the author, not
closing. Approved drafts by other authors go under **High ROI** with "mark ready" as the
action.

PRs opened by a bot on your behalf count as yours. You cannot approve your own PRs. Never put a PR you authored in **Easy to approve**. If
it is non-draft and otherwise ready, list it under **Ready for you to request review**
and say who to ask (owning team from CODEOWNERS, or a requested reviewer). Your own
`nudgy-ignore` PRs stay here, marked "no nudge". If a dormant
review-ask thread exists, recommend bumping it (link it); otherwise recommend asking in
the owning team's channel. Do not post the ask.

**Drafts are never review asks.** Do not put a draft in **Ready for you to request
review** or recommend asking or bumping for one. A near-ready draft you authored goes in
a single **Drafts to promote** line ("mark ready, then ask").

Avoid padding groups. Judge each PR on its own merits. Note a dependency (for example
"stacked on #244") inside that PR's own row, but never group PRs into one row or one
verdict. A `wip` label means never easy-approve; `nudgy-ignore` means never nudge others' PRs.

## Output

Be concise: short rows, no prose paragraphs. One row per PR.

- Open with one line: snapshot date, open count, and a caveat only if `updatedAt` is
  unreliable (then use last-commit dates).
- One table per group with columns
  `PR | What it does | Author | Owner | Opened | Updated | Why / blocker`.
  PR is a link like `[#321](url)`. "What it does" is one plain-language clause (about 10
  words) on what the PR adds or changes, from the PR body or diff, not a restatement of
  the title. Dates are `YYYY-MM-DD`. Label notes go in the last column, only when
  present, as backticked labels. Mark your own PRs `(you)` after the author. Stacked
  PRs say "stacked on #N" from the helper's `stacked_on`. Keep "Why / blocker" to about
  12 words; in **Ready for you to request review** it may add one "Ask" clause with a
  Slack link.
- Abbreviate owners and define once (for example D = devops, AE = agentic-engineering).
- Never collapse PRs into one row or write "various". Mark PRs you authored.
- Omit empty groups (say "none" in one line only for Easy to approve).
- End with at most five numbered actions, one line each (merge related actions into one
  line), ordered: merge-ready, review asks, drafts to promote, owner pings for stale.
  Then
  "No GitHub state was changed."
