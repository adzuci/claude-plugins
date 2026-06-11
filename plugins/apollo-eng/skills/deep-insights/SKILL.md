---
name: deep-insights
description: Manual-invocation only. Deep-analyze local Claude Code sessions into a self-contained HTML burn report (per-session token-waste, weekly burn trend, team-level config recs). Run via /apollo-eng:deep-insights.
disable-model-invocation: true
argument-hint: '[--since 7d|24h|30d|all] [--sessions N] [--project-hash HASH]'
allowed-tools: Bash Workflow Read Write
compatibility: Claude Code only — requires the Workflow tool (unavailable in Cowork/Codex)
---

# /deep-insights — Deep session analysis

**Manual invocation only** (`disable-model-invocation: true`). This is a deliberate, paid operation —
it fans out dozens of subagents and costs a few dollars per run — so it never auto-activates, and its
frontmatter `description` is kept short on purpose so the skill does not bloat model-routing context in
unrelated sessions. Run it explicitly: `/apollo-eng:deep-insights [args]`.

Analyze the local Claude Code transcripts under `~/.claude/projects` and produce a **self-contained,
readable HTML report** (written to `~/.claude/deep-insights/reports/` and opened in the browser) with two sections
written as readable sentences for a human:

1. **Burn vs output** (the lead) — *was the spend worth what it produced?* A ledger of the top-burn
   sessions, each carrying three orthogonal dimensions: **ROI** (was the price fair — worth-it /
   overpriced / wasted) and **outcome** (did durable work result — landed / partial / dropped), both
   *judged* by a reviewer, plus **efficiency** (how much spend was avoidable churn — lean / loose /
   thrashy), *computed deterministically* from revert/re-read/thrash/cache-break signals rather than
   guessed by a model. Each session gets a blunt one-line verdict; the section closes with an overall
   "of ≈$X, roughly how much bought work that landed and was worth the price vs exploration / thrash /
   abandoned effort." Grounded in deterministic per-session signals: commits, edits, files touched,
   test runs, reverts.
1. **Team harness** — concrete shippable changes (settings.json / CLAUDE.md / hook / skill / script /
   config), each with a **paste-ready artifact**, that move the *burn* needle: cut re-ingest on long
   sessions, gather org context up-front (a Glean-first rule for cross-team tasks), reduce churn.

Findings are graded for **materiality** — trivial token amounts, low-ROI micro-habits, and expected
behavior (e.g. repeated `cd /abs &&` prefixes, required because cwd resets between Bash calls) are not
reported. The report is **week-oriented**: a deterministic burn chart shows spend and churn
week-by-week (cost split by efficiency), and the summary reads the trend across weeks. The heavy
lifting is a **Claude Code Workflow that fans out one reviewer per session** (flagged ∪ top-spend); a
cheap deterministic pre-pass keeps that fan-out surgical, and per-session reviewer findings are
**cached as leaves** under `~/.claude/deep-insights/cache/` keyed by a content fingerprint — so an
unchanged session is never analyzed twice across runs. A deterministic renderer turns the structured
result into the HTML (no LLM tokens for formatting).

## Steps

**Step 1 — Parse arguments** from `$ARGUMENTS`: `--since` (default `7d`; accepts `24h`/`30d`/`all`),
`--sessions N` (cap), `--project-hash HASH` (restrict to one project dir). For `all`, omit `--since`.

**Step 2 — Run the enumerator** (deterministic pre-pass). It lives in this skill's directory; use its
absolute path. It writes full detail to a temp file and prints a compact work-list to stdout:

```sh
node <skill-dir>/enumerate_sessions.mjs --since 7d > /tmp/insights/compact.json 2> /tmp/insights/summary.txt
```

Show the user the stderr summary line (session/prompt/token counts + flag tallies). If it reports
**0 flagged episodes**, stop and say the window was clean — suggest a wider `--since`.

**Step 3 — Build the workflow args** (small — a few KB; do NOT load the full work-list into context).
Also pull the most recent history snapshot (for the trend line) and today's date, since the workflow
cannot read the clock or the filesystem, and pass the leaf-cache dir + the per-session fingerprints
so each reviewer can self-check its cache:

```sh
mkdir -p ~/.claude/deep-insights/cache ~/.claude/deep-insights/reports /tmp/insights
PREV=$(tail -n 1 ~/.claude/deep-insights/history.jsonl 2>/dev/null || echo null)
CACHE=~/.claude/deep-insights/cache
# Real autocompaction settings — so the synth never recommends turning on what's already on.
ENV=$(jq -c '{autoCompactEnabled, autoCompactWindow}' ~/.claude/settings.json 2>/dev/null || echo '{}')
jq -c --argjson prev "${PREV:-null}" --arg date "$(date +%F)" --arg cache "$CACHE" \
     --argjson env "$ENV" \
  '{worklistPath: .worklist_path, since: .since, totals: .totals, model_mix: .model_mix,
    flag_counts: .flag_counts, sessions_by_spend: .sessions_by_spend, by_week: .by_week,
    fingerprints: .fingerprints, cacheDir: $cache, env: $env,
    session_meta: (reduce (.sessions[], .sessions_by_spend[]) as $s ({}; . + {($s.session): {week: $s.week, project: $s.project}})),
    sessions: ([.sessions[].session] + [.sessions_by_spend[].session] | unique),
    prev: $prev, date: $date}' \
  /tmp/insights/compact.json > /tmp/insights/wf_args.json
N=$(jq '.sessions | length' /tmp/insights/wf_args.json)   # fan-out count, for the integrity check
echo "wrote workflow args: $N sessions → /tmp/insights/wf_args.json"
```

`totals` now also carries `compaction` (how many times sessions actually compacted + how many
cache-breaks were post-compaction vs resume/idle cold re-ingests) and `opusplan` (Opus spend +
plan-mode usage); both ride the `totals` passthrough, so the synth can diagnose cache-break burn
correctly (it is usually resume/idle re-ingest, **not** "never compacted") and judge an `opusplan`
recommendation. **Write the args to the file — do NOT inline them into the Workflow call** (see Step 4).

The fan-out covers **flagged sessions ∪ top-spend sessions** — the biggest burners matter most for
the burn-vs-output verdict even when they carry no cost-faux-pas flag. Each reviewer first reads
`<cacheDir>/<session>__<fingerprint>.json`; on a hit it returns that leaf verbatim and skips analysis,
so only new or changed sessions cost tokens. `session_meta` (per-session week + project) lets the
synthesis ground each week's narrative only in the sessions that actually fall in that week, and `env`
(the user's real autocompaction settings) keeps it from recommending a setting already enabled.

**Step 4 — Drive the fan-out workflow.** Invoke the **Workflow** tool with the bundled script and a
**tiny** args object that points at the file from Step 3 — pass the `argsFile` path and the integrity
count `N`, **never the inlined ~18 KB blob** (hand-transcribing it is error-prone — a flipped
session-id hash silently mis-keys the cache or drops a session):

```
Workflow({ scriptPath: "<skill-dir>/insights_workflow.js",
           args: { argsFile: "/tmp/insights/wf_args.json", expectSessions: <N> } })
```

The workflow's first agent `cat`s the file back (scripts can't touch the filesystem) and validates it
against `expectSessions`, then proceeds. (Inlining the full object still works for debugging — if
`sessions` is already present the loader is skipped.)

The workflow spawns one reviewer per session (cache hit → returns the cached leaf; miss →
confirms/discards the pre-flags, quoting verbatim and reading only targeted transcript lines), then a
synthesis stage aggregates everything with the week-by-week burn. It returns
`{ one_screen, burn_analysis, team_harness, by_week, fresh_findings, snapshot }`. `burn_analysis` has
an `overall_verdict` (week-aware), a `weekly` array (one narrative headline per week), and a
per-session ledger (cost + ROI/outcome + the deterministic efficiency label + verdict); `by_week` is
the deterministic chart data; `fresh_findings` are the leaves to cache (Step 6); each `team_harness`
item carries `target_path` + `ready_to_apply`.

**Step 5 — Render the HTML report and open it.** The deliverable is a self-contained, readable HTML
file — not a terminal dump. First build the self-cost footer (a skill that audits token spend must
disclose its own): read the workflow's `<usage>` from the completion notification (`agent_count`,
`subagent_tokens`) and the workflow return's `cost_basis` (the exact agent/model split: N reviewers on
the reviewer model, 1 synth on Opus, 1 loader on Haiku). Use
[`references/cost-estimation.md`](references/cost-estimation.md) for the approximate blended cost
calculation, and label it `≈` because the harness does not expose per-model token counts. Then write the
workflow's full return object to a temp file and run the bundled deterministic renderer (no LLM tokens —
it just templates the structured fields into HTML):

```sh
# /tmp/insights/result.json = the FULL workflow return (incl. by_week + fresh_findings)
# Compose the agent split from cost_basis, e.g. "15 Sonnet reviewers · 1 Opus synth · 1 Haiku loader".
FOOT="─ this analysis: ≈\$<cost> · <subagent_tokens/1000>k agent-tok · <agent_count> agents · <cost_basis split>"
OUT=~/.claude/deep-insights/reports/report-$(date +%F).html
# Prior snapshot for run-over-run deltas. Step 6 appends THIS run, so the tail is still the previous run.
tail -n 1 ~/.claude/deep-insights/history.jsonl 2>/dev/null > /tmp/insights/prev.json || echo null > /tmp/insights/prev.json
node <skill-dir>/render_report.mjs /tmp/insights/result.json --out "$OUT" --footer "$FOOT" --prev /tmp/insights/prev.json
open "$OUT"   # macOS; use xdg-open on Linux
```

After opening, print to the terminal only the one-line `burn_analysis.overall_verdict` headline plus the
report path — no other preamble or commentary. The HTML leads with the **week-by-week burn chart**
(spend split by efficiency), then the burn ledger (color-coded ROI / outcome / efficiency badges) and the
team-harness recommendations
(each with a collapsible, copy-to-clipboard `ready_to_apply` block).

**Step 6 — Persist the snapshot and cache the leaves.** Append the trend baseline, and write each
fresh per-session finding to the leaf cache so the next run reuses it (the renderer wrote
`result.json` in Step 5; pass the enumerator's fingerprint map so the cache keys match):

```sh
echo '<the snapshot object, compact JSON>' >> ~/.claude/deep-insights/history.jsonl
node <skill-dir>/cache_write.mjs /tmp/insights/result.json \
  --cache-dir ~/.claude/deep-insights/cache --fingerprints /tmp/insights/compact.json
```

**Step 7 — Offer to ship the fixes.** The full breakdown is already saved (the HTML report). Offer
once: "Want me to apply any of the team harness recommendations? I can write the paste-ready artifacts
(`ready_to_apply`) to their `target_path`." If they pick a `team_harness` item, write its
`ready_to_apply` to `target_path` (for `CLAUDE.md`/`settings.json`, **append/merge** — never clobber;
Read first); for a repo-level artifact, follow the repo's PR convention rather than committing to
`main`.

## Notes

- **Token efficiency is the point** — never `cat` whole transcripts. The enumerator + per-session
  `jq` slices keep cost bounded; reviewers `sed -n` only the lines they must confirm. The fan-out
  reviewers run on **Sonnet** (set in the workflow); only the single synthesis call uses the stronger
  model. A skill that flags Opus-on-small-tasks should not itself burn Opus on dozens of agents.
- Cost figures are **approximate** (list-price `$/Mtok`), labelled `≈`; treat them as relative.
- **Efficiency is computed, not judged.** The lean/loose/thrashy label is a deterministic function of
  signals the enumerator already extracts (reverts + per-episode reread/thrash/cache-break flags,
  normalized per prompt with a short-session floor) — the enumerator emits it, the workflow merges it
  onto the ledger after synthesis, and neither the reviewers nor synth opine on it. This came out of a
  probe: polling Haiku 10× and Sonnet 5× on identical inputs, Haiku *coin-flipped* the churniest
  session (5 loose / 5 thrashy) and both models tagged the cleanest session "loose" — voting denoises
  variance but not that shared bias. A free, reproducible threshold beats both, and it frees the
  reviewers to spend judgment on ROI and outcome, where it actually adds value.
- **Reviewer model defaults to Sonnet** (overridable via `args.reviewerModel`) for the two *judged*
  dimensions, ROI and outcome. An A/B vs Haiku showed Haiku diverging on the highest-stakes call — it
  flipped one session from "fix landed" to "wasted, fix doesn't work" (a checkable fact, not a
  shading). Haiku reviewers are ~3× cheaper, so `reviewerModel: "haiku"` is fine for a quick throwaway
  pass, but Sonnet is the default because the burn-vs-output verdict is the whole point.
- **Leaf caching makes re-runs cheap.** Each reviewer's finding is cached at
  `~/.claude/deep-insights/cache/<session>__<fingerprint>.json`; the fingerprint encodes an
  analysis-logic version plus the session's prompt count, cost, and last-activity time, so a *changed*
  session re-analyzes while an unchanged one is returned verbatim without spending tokens. The first
  `--since 30d` run pays full freight; later runs (or a widened window that overlaps) mostly hit cache.
  Bumping `ANALYSIS_VERSION` in the enumerator (done whenever reviewer logic changes) rolls every
  fingerprint so stale findings can't be served under new logic. Stale fingerprints from grown sessions
  are harmless orphans — delete the cache dir to force a clean re-analysis.
- **Week-oriented.** The enumerator buckets every session into its ISO week and emits `by_week` (cost
  split by efficiency); the renderer draws the burn chart from it and the synthesis writes a one-line
  read per week plus a week-aware overall verdict. The chart leads the report.
- The enumerator deliberately **over-flags**; the reviewers are the precision filter. Trust confirmed
  counts (in the workflow log) over raw `flag_counts`.
- **Commit count is a noisy outcome signal** — work is routinely committed in a *different* session,
  by the human by hand, or squashed later, so zero commits does NOT mean nothing landed. Both the
  reviewers and the synthesis are told never to read "un-anchored / dropped" from a low commit count;
  landing is judged from whether the work completed and stuck in the session arc.
- **Compaction advice is environment-aware.** The SKILL passes the user's real `autoCompactEnabled` /
  `autoCompactWindow`, so the synthesis never recommends "enable autocompaction" when it is already on.
  When compaction-related burn shows up it names the correct lever — a smaller window, `/clear` between
  unrelated tasks, shorter-lived sessions — because autocompaction caps live context but does **not**
  keep the prompt cache warm, so every resume still pays a cold re-ingest of the (capped) context.
- **Week narratives are grounded, not guessed.** `session_meta` tags every finding with its ISO week +
  project and the synthesis gets a per-week digest; it may only attribute a build/topic to a week that
  has a reviewed session in its bucket — no cross-week or salience-driven attribution.
- A full 30d run fans out ~dozens of agents and costs real tokens on the FIRST pass — scope with
  `--since 24h` or `--sessions N` for a quick look; the leaf cache makes subsequent runs much cheaper.
- **The skill eats its own dog food.** It runs the fan-out on Sonnet, reads transcripts surgically
  (never `cat`), caches per-session findings so no session is analyzed twice, renders the HTML
  deterministically (zero LLM tokens for formatting), discloses its own run cost (Step 5 footer),
  tracks its own trend over time (Step 6 history), and ships paste-ready fixes rather than just prose
  (Step 7) — practicing the cost discipline, tool hygiene, and follow-through it recommends to the team.
- **Claude Code only — not Cowork/Codex.** The engine is the `Workflow` tool (the per-session fan-out),
  which only exists in Claude Code; and the transcript source `~/.claude/projects` is not present in the
  Cowork sandbox. A future port would drop the fan-out to a sequential loop and mount the transcripts via
  `request_cowork_directory` (see the `apollo-gtm` task-tracker pattern) — out of scope here; the skill
  declares the boundary rather than half-supporting it.
