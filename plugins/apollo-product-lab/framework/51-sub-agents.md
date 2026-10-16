# 51: Sub-agents: when to delegate, and the guards

> Decision 2026-10-08, updated 2026-10-13 after review. Long harness sessions run out of context
> because research, wide code lookups and lens work happen inline in the main session. This doc says
> what goes to a sub-agent, and puts hard limits on depth, budget and retries so delegation can never
> run away.

## 1. Delegate these

A sub-agent has its own context window. Its tool output never enters the main session; only its
short report does. Use one for:

- **Research**: Glean, Notion, Jira, web or competitor lookups for a stage.
- **Wide code lookups**: tracing a code path across many files, the current behaviour map (doc 43
  §4), finding every caller of a function.
- **Independent lenses**: each council lens (doc 34) is already one sub-agent.
- **Independent checks**: per-edge contradiction checks (`artifact-audit`) and scoped per-PR checks.
- **Per-slice builds**: one slice owner per slice, each in its own git worktree (doc 20 §4).

Keep inline: one file read, one exact search, anything the next step needs verbatim, every human
question and decision, and the final pre-push verification. The main session always reads the diff and
runs the required checks before a push, as required by doc 48 §2.

Each sub-agent writes its detail to a file (a snapshot, a lens file, a notes file under the run) and
returns at most about 2,000 tokens: the conclusion, the file path, and anything left open.

## 2. Guards

These hold for every harness skill and agent, on every host.

1. **Depth at most 2.** The main session is depth 0. A depth-1 sub-agent may spawn sub-agents once;
   a depth-2 sub-agent never spawns. If a task seems to need depth 3, stop and ask the person.
2. **Every brief states its depth.** The first line of every sub-agent brief is
   `Sub-agent depth: <n> of 2.` A depth-2 brief adds:
   `Do not spawn sub-agents. Do not run claude -p, codex exec or any other agent CLI.`
   A sub-agent whose brief has no depth line treats itself as depth 2.
3. **Width is bounded by budget, not a fixed count. Concurrency 20 is non-overridable.** One
   dispatch is sized by the stage's token budget: the profile's `council_budget` for a council
   round (default 600k tokens) and for any skill that runs the same council-shaped dispatch
   (`artifact-audit` per-edge agents, `harness-intake` research fan-out); the profile's
   `build_review_budget` for a build or review pass (default 200,000 tokens). Doc 46's 15,000-character
   target is a prompt-size rule, not a token budget. Before dispatching, use the one estimate rule
   of `harness-council` step 3b: `input words × 1.35 + 30k per lens for instructions and tool schemas, × 1.5 headroom for tool reads`, summed over the briefs plus one retry. If that
   estimate goes over the stage's token budget, stop and ask the person for a go-ahead with the
   count, the estimated tokens and the reason. **The platform concurrency limit (20) is the hard stop
   and nobody overrides it:** a dispatch of more than 20 sub-agents in parallel is refused regardless
   of any go-ahead; split the dispatch into waves instead. A council of 8–10 lenses is normal and
   does not need a go-ahead **only when its estimate fits inside the budget**; an erd or plan
   council on backend code picks about 8 lenses by default (architecture, infra, backend, db-perf,
   research, adversary, plus competitive and AI opportunity when product-visible), with an
   owning-team lens or QA taking it to 10, and that fits inside the default `council_budget`
   without asking.
4. **One retry.** A sub-agent that fails, times out or returns something its file does not match is
   re-run once. A second failure is reported to the person, never looped.
5. **Never re-delegate your own brief.** A sub-agent does not hand the task it was given, or a
   restatement of it, to another sub-agent. It delegates only a smaller, different part. Violation
   example: a depth-1 agent given "trace every caller of `foo`" spawning a depth-2 agent with the
   same brief; it may instead spawn one scoped to a single module.
6. **Agent CLIs count as sub-agents, with one leaf exception for cross-family review.** `claude -p`
   and `codex exec` start a new agent, so they count toward the depth. The main session may run
   them as depth-1 sub-agents. **A depth-1 sub-agent may also run exactly one cross-family review
   CLI on its own artifact** (for example, a domain agent asking Astra through `codex exec` to
   review the code it just wrote, or `council-adversary` reaching the other family): the CLI is
   treated as a leaf — it never spawns further sub-agents, its tokens and minutes are counted in
   the stage budget and recorded in the ledger with `--note cross-family-review`, and it does not
   add a depth level. The depth-1 agent must put an explicit no-spawn line as the first line of
   the leaf's prompt: `Leaf cross-family review. Do not spawn sub-agents. Do not run claude -p, codex exec or any other agent CLI.` A second cross-family review from the same depth-1 agent,
   any CLI call from a depth-2 agent, and any other `claude -p` or `codex exec` call from a
   depth-1 agent, are all forbidden.
7. **Harness agent types cannot spawn.** The agents in `agents/` have no Agent tool. Keep it that
   way: adding one needs a decision record and an update to this doc. The cross-family review CLI
   of guard 6 is a `Bash` call to `codex exec` / `claude -p`, not an Agent tool call, so it
   remains available to the agent types that have `Bash` in their tool list.
8. **Budget still applies.** Sub-agent tokens count toward the stage's budget (the profile's
   `council_budget` for a council round, or `build_review_budget` for build and review). The
   ledger records them per sub-agent, including the leaf cross-family review of guard 6.

The platform's own limits (depth 3, concurrency 20) are a backstop, not the plan. A plan that needs
them is the wrong plan (doc 14 §Limit 1).
