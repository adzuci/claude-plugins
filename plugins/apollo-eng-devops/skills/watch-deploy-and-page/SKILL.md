---
name: watch-deploy-and-page
description: Manual-invocation only. Confirm a leadgenie commit is actually live in prod, judge the transaction it targeted, and page only on a confirmed regression. Run via /apollo-eng-devops:watch-deploy-and-page.
argument-hint: <pr-number|sha|--branch> --transaction <name> [--deployment <name>] [--page <recipient>|--no-page]
disable-model-invocation: true
allowed-tools:
  - Bash
  - Read
  - Skill
  - AskUserQuestion
  - mcp__grafana__query_prometheus
  - mcp__grafana__get_dashboard_panel_queries
---

# Watch Deploy And Page

**Invoke directly.** This skill reads production and can wake a human, so it never auto-activates.

One pass = **check and decide**. It answers three questions in order and stops at the first
unresolved one:

1. Is the target commit actually running in prod? (not "did CI go green")
1. Did the transaction it targets get better, worse, or move within noise?
1. Does that warrant waking a human?

This skill is deliberately **not** a poll loop. It is one idempotent check. The caller decides
whether to run it once or on a schedule — see [Running it unattended](#running-it-unattended).

Everything here is read-only against prod. Nothing in this skill applies, patches, scales, or
rolls anything back.

## Usage

```text
/apollo-eng-devops:watch-deploy-and-page <pr-number|sha|--branch> --transaction <name> [flags]
```

| Argument | Default | Meaning |
| --- | --- | --- |
| `<pr-number>` / `<sha>` / `--branch` | required | What to watch: a leadgenie PR number, an explicit commit SHA, or the current branch's PR |
| `--transaction <name>` | required | New Relic / spanmetrics transaction to judge the outcome by |
| `--deployment <name>` | `rails-api` | Which prod deployment carries the change |
| `--page <recipient>` | the invoking user | Who a confirmed regression pages |
| `--no-page` | off | Report only; never page, even on `REGRESSION` |

```text
/apollo-eng-devops:watch-deploy-and-page 103067 --transaction 'Controllers::Api::V1::FooController#bar'
/apollo-eng-devops:watch-deploy-and-page --branch --transaction 'Controllers::Api::V1::FooController#bar' --no-page
```

## Step 0 — Preflight

Run this every invocation. It is four cheap local commands; there is no "already set up" marker
to trust, because every one of these can go stale between runs (kubeconfig switched, `gh` token
expired, prod VPN down) and a stale green flag on an unattended watch means silent failure.

Print one line:

```text
Tools: gh [ok/missing]  kubectl prod [ok/missing]  Grafana [ok/missing]  page route [ok/missing]  repo [<path>]
```

| Check | Command | Required for |
| --- | --- | --- |
| `gh` authenticated | `gh auth status` | Steps 0–1 — hard requirement |
| Prod cluster reachable | `kubectl --context gke_indigo-lotus-415_us-central1-c_prod -n leadgenie get deployment <name> -o name` | Step 2 — hard requirement |
| Grafana MCP | `mcp__grafana__get_dashboard_panel_queries` available in session | Step 3 |
| Paging route | the `page` skill is installed and its route is verified | Step 4 |

**Anything missing: name what is missing, name the fix, and stop or degrade explicitly.** Do not
fail silently and do not skip a step without saying so. Read
[`references/setup.md`](references/setup.md) for the per-tool fix and hand the caller the exact
command. Degradation rules:

- No `gh` or no prod context: **stop.** There is no verification path without them.
- No Grafana: continue to Step 2, then report `live, performance unverified`. Never page.
- No paging route: continue, but say up front that a `REGRESSION` will be **reported, not sent**.
  If the caller is arming an unattended watch, treat this as a **hard stop** — an unattended watch
  with no working page route is a watch that wakes nobody.

**Resolve the repo, never assume a checkout path.** Prefer `gh -R apolloio/leadgenie ...` for
every `gh` call so the skill works from any directory. The only step that needs a local clone is
the ancestry check in Step 2:

```bash
git rev-parse --show-toplevel                       # cwd is already the repo?
git -C "$REPO" remote get-url origin | grep -q apolloio/leadgenie
```

If cwd is not a leadgenie checkout, use `$LEADGENIE_DIR` when it is set, otherwise **ask** for the
path. Do not guess `~/code/apolloio/leadgenie`.

## Step 1 — Resolve inputs and find the deploy runs

Two things must be pinned before anything else. Never proceed on a guess.

**Target commit** — the merge commit on `master` that carries the change:

```bash
gh -R apolloio/leadgenie pr view <number> --json mergeCommit,state,title -q '.mergeCommit.oid, .state, .title'
git rev-parse <sha>                                                    # explicit SHA
gh pr view --json mergeCommit,state -q '.mergeCommit.oid, .state'      # --branch, from the checkout
```

An unmerged PR has no merge commit. Say so and stop — there is nothing to watch yet.

**Target transaction** — the caller must supply it. If they did not, ask once; do **not** infer it
from the diff, and do **not** silently skip Step 3. A watch that verifies a deploy but never
checks the metric is not this skill.

**Deployment** — any leadgenie workload whose container image is tagged with the commit SHA.
`rails-api` is the default and covers most backend/Ruby changes; `app` carries frontend bundles,
and the other Rails surfaces have their own deployments. Do not trust a name from memory — the
`Production deployment` workflow deploys what is under `kubernetes/production/` in the leadgenie
checkout, so read the values filenames there (or `kubectl get deploy -n leadgenie`) and confirm
the exact name in the preflight read. State which one you picked.

If the change does not land in a SHA-tagged leadgenie deployment at all — ingress, proxy, or
infra config deployed from another repo — this skill cannot verify it. Say so and stop rather
than grading an unrelated deployment.

Then list the runs:

```bash
gh -R apolloio/leadgenie run list --workflow "Production deployment" --limit 20 \
  --json databaseId,headSha,status,conclusion,createdAt,displayTitle
```

Find the run whose `headSha` equals the target commit, plus every run created **after** it. Real
output from this repo, in one 90-minute window:

| headSha | status | conclusion |
| --- | --- | --- |
| `955e639b` | in_progress | — |
| `58a59740` | completed | **failure** |
| `cc027120` | completed | **cancelled** |
| `7f208ace` | completed | **failure** |
| `9cb866dc` | completed | success |

That is the normal shape, not an outage. Three consecutive non-success deploys is routine here.

**The failure mode this skill exists for:** the run for your exact commit can fail on a flaky spec
while a *later* commit's run succeeds and carries your change along anyway. So a `failure` on the
target commit's own run is **not** a terminal answer. Keep evaluating later runs until one that
includes the target commit succeeds. Only report "not live" — never "deploy failed, done".

For a run still going, `gh -R apolloio/leadgenie run view <databaseId> --json jobs,status` shows
which job it is sitting in; useful for the ETA line in the report, not for the verdict.

## Step 2 — Verify against the cluster, not against CI

A green workflow means the pipeline finished, not that the pods are serving your code. Read what
is actually running:

```bash
kubectl --context gke_indigo-lotus-415_us-central1-c_prod -n leadgenie \
  get deployment rails-api -o jsonpath='{.spec.template.spec.containers[0].image}'
# us-docker.pkg.dev/indigo-lotus-415/us.gcr.io/rails:955e639b382e181b842366f51cc8bb6d7d8fda96
```

The tag is the full 40-char commit SHA. Strip everything through the last `:`.

**Do not treat that tag alone as proof.** In the sample above, `rails-api` was already carrying
`955e639b` while that commit's workflow run was still `in_progress` — the image gets set before
the rollout is complete and before the run can fail. The kubectl read tells you *which commit* is
being rolled out; the workflow run tells you *whether that rollout finished*. You need both.

Compare by ancestry, never by string equality — the deployed commit is usually **later** than
yours and still contains it:

```bash
git -C "$REPO" fetch origin master --quiet
git -C "$REPO" merge-base --is-ancestor <target-sha> <deployed-sha>   # exit 0 => target is live
```

If `<deployed-sha>` is not in the local object store, `git -C "$REPO" fetch origin <deployed-sha>`
first; an "unknown revision" error is a missing object, not a negative answer, and must never be
read as one.

**Live** requires both: ancestry holds **and** the workflow run for `<deployed-sha>` (or a later
one that also contains the target) has `conclusion: success`. Anything else is "not live yet" —
report the state and stop. Do not run Step 3 against a deploy that has not landed; you would be
grading the old code.

Also confirm the rollout itself settled:

```bash
kubectl --context gke_indigo-lotus-415_us-central1-c_prod -n leadgenie \
  rollout status deployment/<deployment> --timeout=10s
```

A non-zero exit here means pods are still cycling. Not live.

Both reads above use the deployment resolved in Step 1 — `rails-api` in the sample output, not
always.

## Step 3 — Compare the metric before and after

Only once Step 2 says live. Use the deploy's completion time as `T`.

- **before** window: `T-2h` → `T`
- **after** window: `T` → `now`, and require **at least 30 minutes** of post-deploy data. Less than
  that is not a measurement; report "live, too early to judge" and let the next pass decide.

Grafana is the primary source. Datasource UID `eeloo3k56g9vkd` (self-hosted Mimir, spanmetrics),
dashboard `plat-1365-apdex`. Fetch the panel queries once with
`mcp__grafana__get_dashboard_panel_queries` and **reuse the dashboard's own expressions**,
substituting only environment, transaction, and window — its Apdex definition (satisfied ≤300ms,
tolerating ≤1000ms, excluding HTTP 429/500) is the definition Apollo's Apdex alerting already
uses, and an invented metric name produces a number nobody can reconcile. Then two
`mcp__grafana__query_prometheus` calls, one per window.

Budget: **four Grafana calls total.** If Grafana is unreachable, New Relic (Apdex or median
response time for the same transaction) is an acceptable substitute if that MCP is authorized in
the session. If neither is reachable, report "live, performance unverified" — that is a legitimate
outcome. Never page on an unverified metric.

For a deeper Apdex triage after this skill returns a verdict, hand off to
`/apollo-eng-devops:check-apdex`. Do not re-derive its triage here.

### Verdict

| Condition | Verdict |
| --- | --- |
| Apdex drops **> 0.05** (or p50 rises **> 25%**) vs before | **REGRESSION** |
| Metric moves within those bounds, either direction | **NOISE** |
| Metric improves beyond them | **IMPROVED** |
| Throughput on the transaction changed by more than ~2x | **INCONCLUSIVE** |

The throughput row matters and is the easiest to skip: an Apdex number computed over a tenth of
the traffic is measuring a different population, not a regression. Say `INCONCLUSIVE` rather than
manufacturing a verdict from it.

Sanity-check the *before* window too. If the transaction was already degraded before the deploy,
the change simply did not work — that is a `FAILED FIX` report, not a regression the deploy
caused, and the distinction changes who needs to look at it.

## Step 4 — Decide whether to page

**Page only on `REGRESSION`.** Not on a failed deploy run (later runs routinely carry the change),
not on `INCONCLUSIVE`, not on `NOISE`, not on a deploy that is merely slow. This is a wake-up, and
the credibility of the whole watch depends on it never firing for something the recipient would
rather have read over coffee. `--no-page` suppresses the send entirely; still report the verdict.

To page, invoke the `page` skill (`Skill` tool, `skill: "page"`) with the resolved recipient —
default is the invoking user, `--page <recipient>` overrides. That skill owns route selection,
the verified-notification check, and the approval gate. **Do not hand-roll a `pd` call**, and do
not page a shared rotation for what is one engineer's own deploy watch.

If the `page` skill is not installed (preflight said `page route [missing]`), report the
regression prominently and say plainly that no page was sent and why. Never silently downgrade to
a weaker channel — see [`references/setup.md`](references/setup.md) for getting a route set up.

Hand it a one-line message under 200 chars, no markdown:

```text
apdex regression after <sha7> deploy: <transaction> 0.94 -> 0.78 https://github.com/apolloio/leadgenie/pull/<n>
```

Approval rules are the `page` skill's, not this one's. An interactive run must get explicit
approval before the send. An unattended watch must have captured that approval **at arm time**,
with recipient, route, exact message, and blast radius shown.

On every other verdict: report, do not page.

## Step 5 — Report

Five lines, in this order. Each is a fact someone acting on this needs:

1. Target commit + PR, and the deployed commit it landed under (name both when they differ).
1. Whether it is live, and how you know — the run id and conclusion, and the kubectl image.
1. Deploy runs that failed on the way, and that they did not block the change. Silence here reads
   as a clean deploy and misleads.
1. Metric before → after, window lengths, and the verdict.
1. Whether a page was sent, or explicitly that none was warranted or none was possible.

If you stopped early, say which step and what the next pass will look for.

## Running It Unattended

The skill is one check. The scheduling belongs to the caller. Three ways, in preference order:

**`/loop`** — the environment's own recurring-prompt mechanism, and the right default for a watch
you will be around for:

```text
/loop 10m /apollo-eng-devops:watch-deploy-and-page <pr-number> --transaction "<name>"
```

**Background agent** — for a long watch that should survive your attention wandering. Spawn it with
`Agent` (`run_in_background: true`) and tell it explicitly: run this skill on an interval, stop on
the first terminal verdict, page only on `REGRESSION`, and report the verdict when it stops.

**Shell watcher** — only when the watch must outlive the session, and only when the `page` skill is
installed; without it there is nothing for the watcher to fire. Use that skill's watcher template
verbatim: it already carries the repeat-guard flag file, the loud send-failure, and the
`caffeinate -i -s` wrapper that keeps the laptop from sleeping through the very failure it is
watching for. Do not re-derive that logic here. A local watcher without `caffeinate` pages into a
silence indistinguishable from success.

Whichever wrapper: **cap it.** A deploy that has not landed in 3 hours is its own finding — report
that, do not keep polling for a day.

## Guardrails

- Do not call a deploy live because CI went green, or because the kubectl tag matches.
- Do not give up on the first failed run for the target commit.
- Do not compare SHAs with `==` instead of `git merge-base --is-ancestor`.
- Do not page on a failed deploy run, an inconclusive metric, or an unverified one.
- Do not judge a deploy on under 30 minutes of post-deploy data.
- Do not run any non-read-only `kubectl` verb. Diagnosis only; remediation is a human decision.
- Do not assume a checkout path or a paging recipient. Resolve both, or ask.

## References

- [`references/setup.md`](references/setup.md) — Per-tool preflight fixes: `gh`, the prod kubectl
  context and VPN, Grafana MCP, and getting a paging route that actually notifies
