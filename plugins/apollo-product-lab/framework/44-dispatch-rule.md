# 44. Dispatch rule: every lens runs on the model its role names, and we check who answered

> Why (Akansh, 2026-10-08): sessions ran almost entirely on the base model (Opus). shunt was up and
> routed `gpt-6-astra` to Codex, but only `council-adversary` and `council-synthesizer` named that model.
> Reviewer agents and ad-hoc `general-purpose` dispatches inherited the base model, and Astra reviews
> were run by hand through `codex exec`. A lens on the author's model family is not an independent
> review, and nothing reported that it was not.

## 1. The rule

1. **Resolve the role first.** Before dispatching any lens or review, look up its role in
   `models/model-registry.yml` (`roles:`), then dispatch through the agent whose frontmatter `model:`
   matches that role's primary. The table in §4 is the current mapping.
1. **Never dispatch a lens as `general-purpose`.** A `general-purpose` agent runs on the session's base
   model. When the main session spawns review work, it uses the named reviewer agents
   (`backend-reviewer`, `db-perf`, `security-reviewer`, `infra-lens`, `council-adversary`, ...). If no
   agent exists for the role, either add one with the right `model:` or run the role's CLI recipe (§3);
   do not borrow `general-purpose`.
1. **Agent files load at session start.** An agent added or edited during a session is not in that
   session's roster (doc 37 §1). Dispatch the old type with "read the newer agent file first" in the
   brief, or use the CLI recipe, and say which in the record.
1. **The model in a request is not evidence.** After each lens, record the model that served it (§2) in
   the snapshot's `produced_by` or the envelope's `served_by`.

## 2. Checking who answered

- **Through shunt** (any agent with `model: gpt-6-astra`, and every Anthropic request when
  `ANTHROPIC_BASE_URL` points at shunt): dispatch the cross-family lens alone (no other lens in flight
  that could request the same model), then run
  `bash "${CLAUDE_PLUGIN_ROOT}/scripts/served-models.sh" --since <dispatch start> --until <end> --expect <model> --effort <level> --sole`.
  It reads the shunt log (`$(brew --prefix)/var/log/shunt.log`, or `SHUNT_LOG`), prints one row per
  family, model, provider and status for the window, and prints the model route's effort from the
  shunt config. The log carries no per-subagent id (sub-agents share the parent's `session_id`), so the
  window is the only attribution: `--sole` is your assertion that this lens ran alone. A hit must also come
  through the model's provider (`codex` for `gpt-*`, overridable with `--provider`), and `--effort`
  must equal the route effort in the shunt config. Exit codes: 0 served; 5 effort mismatch (record
  the served effort); 3 not served (tag the lens `independence: same-family` only if its answers came from an
  Anthropic row, otherwise `unknown`); 4 ambiguous (no `--sole`: `unknown`); 2 no log or no requests
  (`unknown`). Timestamps are UTC; a start in whole seconds begins at `.000000`, an end in whole
  seconds covers the whole second. The script cannot prove the lens's final answer came from those
  requests; that is what `--sole` asserts. For several cross-family lenses in parallel, use `codex exec` per lens instead, whose stderr header is per run.
- **Through `codex exec`** (not via shunt, so not in that log): the first lines of codex's stderr name
  `model:`, `provider:` and `reasoning effort:`; keep that log beside the output and copy the three
  values into the record.
- **No log at all** (shunt not installed): `independence: unknown`, never independent.

Verified 2026-10-08: `council-adversary` (frontmatter `model: gpt-6-astra`) dispatched with a read-only
probe from a Claude Code session whose `ANTHROPIC_BASE_URL` is shunt 0.45.1. It answered "gpt-6-astra,
OpenAI" and quoted `SidekiqPersisted::EventDispatcher` from the repo file. `served-models.sh --expect gpt-6-astra --sole` over its window printed three `openai gpt-6-astra codex 200` requests and exited 0 (4,
ambiguous, without `--sole`); the orchestrating session's own requests in the same window were `anthropic claude-opus-5-5`.

## 3. Recipes when no agent fits or shunt is down

| Need | Recipe |
|---|---|
| Astra xhigh review of a design (doc 17 §6.3) | `codex exec -m gpt-6-astra -c 'model_reasoning_effort="xhigh"' -c 'sandbox_mode="read-only"' --skip-git-repo-check - < brief.md > out.md 2> err.log` in the background; poll `out.md` size, do not stream |
| Astra lens on a PR (infra, adversary) | same, effort `high`; the brief asks for the envelope between `<<<ENVELOPE` and `ENVELOPE>>>` because the read-only sandbox cannot write files |
| Sol at a chosen effort | `codex exec -m gpt-5.6-sol -c 'model_reasoning_effort="<low|medium|high>"' ...` |
| Anthropic lens from Codex (host swap, doc 35) | `claude -p --model claude-fable-5-1 --allowedTools 'Read,Grep,Glob,Bash(git *)' < brief.md` |
| OpenAI unreachable | the role's `fallback` in the registry, tagged `independence: same-family`, and the human gate is told |

Every brief in this table follows doc 46 §4 and §5: the diff (pass 2: the delta), the specific question
and file pointers, no pasted file bodies, 15,000 characters or fewer, at most two passes per artifact.
Log `wc -c` of the brief with `append.py --prompt-chars`.

shunt sets effort per route in `shunt.toml.example`: Astra runs at xhigh and Sol at medium. Use `codex exec`
when a lens needs an effort different from its route.

## 4. Role to agent to model (2026-10-08)

| Role (registry) | Agent | `model:` | Family |
|---|---|---|---|
| `route.labelling` | `product-orchestrator` | haiku | anthropic |
| `review.code.generic` (backend) | `backend-reviewer` (leadgenie `.claude/agents/`) | sonnet | anthropic |
| `review.code.generic` (db) | `db-perf` (leadgenie) | sonnet | anthropic |
| `review.code.security` | `security-reviewer` (leadgenie) | fable | anthropic |
| `review.code.synthesis` | `pr-tech-lead-synthesizer` (leadgenie) | sonnet | anthropic |
| `review.infra` | `infra-lens` (this plugin) | gpt-6-astra | openai via shunt |
| `review.adversary` (erd, plan, design) | `council-adversary` (this plugin) | gpt-6-astra | openai via shunt |
| `synthesize.council` | `council-synthesizer` (this plugin) | gpt-6-astra | openai via shunt |
| `decide.architect` | initiative `<x>-architect` | opus | anthropic |
| `build.implement` | `implementer` (this plugin) | sonnet (5.5) | anthropic |
| `build.implement.complex` | `implementer-complex` (this plugin) | opus (5.5) | anthropic |

Implementation follows the same rule as lenses, minus the independence check: resolve the role, dispatch
the agent whose `model:` matches, record who served it. Doc 48 §2 says when a slice escalates to Opus.

The Anthropic reviewers stay on Anthropic models on purpose: they are many, they run on every PR, and
their checks are written down. The cross-family read on a PR is the `infra-lens` and the Codex
adversary; on a design it is Astra xhigh (doc 17 §6.3).

## 5. What the eval showed

A replay of a past Ads backend review (the findings a senior reviewer left after our reviewers had
passed the stack, scored on 2026-10-08; the run-specific fixtures are kept out of the plugin, and new
misses enter through the learning loop of doc 43) measured recall 0.13 before and 0.45 after (0.08 and 0.23 on held-out items), on different inputs, so
the difference is not all due to the rules. Three lessons
for dispatch:

- The backend reviewer went from 7 items to 20 with the rules in its agent file and to 23 with the IP
  check lines also pasted into the brief. First-wave transcripts showed reviewers told only to
  "load the patterns doc" mostly did not open it, so the supervisor pastes the checks (the replay
  runner did the same) rather than trusting the agent to load the file.
- The cross-family infra lens found 8 items no Anthropic reviewer did, but none of the held-out ones;
  it is worth its cost on medium and high changes, not as a substitute for the domain reviewers.
- An agent file edited mid-session is not the one that runs (§1 rule 3); the replay dispatched the old
  types with "read the newer agent file first", and that has to be stated in the record.
