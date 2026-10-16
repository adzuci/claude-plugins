# 37 — The Gemini/DeepSeek bridge is shunt config, and models are chosen by input size

> Answers three questions from 2026-09-19: can OpenAI review with repository access (yes, no new
> auth), can we pick a model by context window (yes, now a registry rule), and what "build the
> Gemini/DeepSeek bridge" actually is (a shunt provider block plus two logins, not a service).

## 1. Repository access for non-Anthropic reviewers

The council's first adversary ran as a detached `claude -p --tools ''` job and saw only excerpts.
That was a harness choice, not a limit of the model. shunt routes a Claude Code **agent** whose
frontmatter says `model: gpt-6-astra`, and an agent has whatever tools its file grants. So:

- `${CLAUDE_PLUGIN_ROOT}/agents/council-adversary.md` (model `gpt-6-astra`, tools Read/Grep/Glob/Bash) reviews
  against the real code, specs, and index definitions, cites `path:line`, and writes its snapshot.
- `${CLAUDE_PLUGIN_ROOT}/agents/council-synthesizer.md` (same model, Read/Bash) reads only lens snapshots.
- Nothing to authorise: shunt already reuses the existing `codex login`.
- Agent files are read at session start: a newly added `council-*.md` is dispatchable from the next
  Claude Code session, not the current one. The council skill checks the roster and falls back to the
  CLI recipe (with `--allowedTools Read,Grep,Bash(...)`, not `--tools ''`) when the agent is absent. The detached `claude -p`
  path stays as the fallback when shunt is down, tagged `excerpt-only` in the snapshot.

**Verified 2026-09-19:** `claude -p --model gpt-6-astra --allowedTools "Read,Grep,Bash(git rev-parse:*),Bash(ls:*)"`
through shunt ran `git rev-parse`, read `packs/ads/app/models/ads/sync_operation.rb`, and quoted its three
`index(` lines with correct line numbers (41, 42, 45), identifying itself as GPT-6 Astra. Repository access for a
non-Anthropic reviewer is measured, not assumed. Recipe detail: pass the prompt on stdin (`< prompt.txt`);
under `nohup` the positional prompt argument is not seen. macOS has no `timeout`; use a `kill -0` wait loop.

## 2. Choosing a model by context window

Every model in `models/model-registry.yml` now carries `context_window` with a sourcing tier. The
`selection.by_input_size` rule: estimate tokens (words × 1.35, or bytes ÷ 4); use the role's
primary unless the input exceeds 60% of its window; then the role's `long_window` alternative
(Gemini 2.5 Pro or Flash at 1M, then Astra at the 400k we run it with); then chunk per file with a
merge step. Never truncate silently. The estimate, the chosen model, and the reason go into the
snapshot frontmatter so a reader can see why a lens ran where it did.

Where a long window earns its cost: a whole-pack review (PRD + constraint register + ERD + code in
one call), research digests over many vendor pages, first-pass audits of a large document graph. The
council's research lens, which died twice at 200k on tool output, is the first customer: it routes
to Gemini Flash when the digest is large and, on any model, writes rows after every question and caps
each tool result at about 4k tokens.

## 3. Three families: Anthropic, OpenAI, and Glean

Apollo holds no direct account with Google for Gemini or with DeepSeek (decision 2026-09-20), so there
is no shunt route and no CLI login for either. That does not make them unusable: **Glean** is Apollo's
approved way to reach them, and the registry treats Glean as a third family with its own capabilities:

| Capability | Tools | Used by |
|---|---|---|
| Research over the internal record and the web | `glean_default.chat`, `search`, `read_document`, `Brave_Actions_web_search` | research lens, competitive lens, corroboration |
| People | `employee_search` | owners, reviewers, stakeholders |
| Images | `create_image`, `edit_image` | diagrams, mocks, deck images |
| Publishing | `upload_artifact` (HTML, paper, slides, spreadsheet), `share_artifact` | decks and dashboards for an audience outside Claude |

Glean chooses the model behind these calls, so the record says `glean/glean-assistant`, never "Gemini".
It counts as an independent family for research and competitive lenses; it cannot be a code reviewer
because it has no repository tools. **DeepSeek** has no lane at all until a vendor approval exists.

**Effort is part of the route.** OpenAI has two models here: `gpt-6-astra` (xhigh for the decisions that
are expensive to get wrong: ERD, plan, PRD adversary, synthesis) and `gpt-5.6-sol` (medium for the PR
adversary, low for research digests). shunt sets effort per route; a lens that needs a different effort
than its model route runs as a `codex exec -c model_reasoning_effort=<level>` call.

**Hosts swap the roles, not the framework.** In Claude Code the base model is Fable 5.1 and the adversary
is OpenAI through shunt; in Codex the base model is Astra and the adversary is Fable through `claude -p`.
Onboarding recommends the base model for the host and lets the person keep their current one.

**Glean as adversary (2026-09-22).** Glean can play the adversary lens by chat on prd and design. On the code-facing kinds it is not an adversary: the 2026-09-22 head-to-head (reviews/glean-adversary-probe-2026-09-22.md) found half the defects and two false ones, because it reasons only over the operator's excerpts and reads the repository through its index at `master`; there it is at most a labelled second reading. The served model is whatever the Model Hub says (GPT-5, Gemini or Claude Sonnet) and is unrecorded today, so the lens is tagged `independence: unknown`; confirming the Model Hub setting is the one action that turns it into a real third reviewer family. DeepSeek is not in Glean's Model Hub list, so it still has no lane.

## 3b. The operator's own context window (Ravi and Akansh, 2026-09-22)

Plain version. The chat you are typing in has a memory limit. Well before that limit is reached, at
roughly half to 60% of it in our runs, answers get worse: the model repeats itself, forgets a decision
made an hour ago, and starts working from a paraphrase of the task instead of the task. When the limit
is finally hit, the tool compresses the whole conversation into a summary it wrote itself. That summary
is where facts get lost. So the framework does not treat the limit as the problem; it treats the 60%
point as the moment to stop and reload from the record.

**What happens by default** (set at onboarding; nothing to remember):

1. **Compaction fires at about 60%, not at the limit.** Onboarding writes it into the host config:
   Claude Code `autoCompactWindow` at about 0.6 × the model's window (the `/autocompact` command
   saves it; 100K minimum); Codex `model_auto_compact_token_limit` at about 0.6 × the window, plus
   `tool_output_token_limit` so one huge tool result cannot fill it. The person can change or undo
   either; the default is on.
1. **After a compaction the record is reloaded for you.** The session-start hook fires again with
   `source: compact` and prints the run's `index.md`, the newest snapshot's stage, decisions, open items
   and gate status, and the latest decision record, straight into the model's context. The summary the
   tool wrote is still there, but the model continues from the files, which is what
   `/harness-snapshot read` would have shown. No command to type.
1. **Heavy reading happens off to the side.** When the harness needs to read a lot (a council lens
   reading a design and the code, a research pass over Glean and the web, a search across many files),
   it does that in a separate agent with its own memory, and only the result file's path comes back
   into your chat. Your conversation stays short because the bulk never entered it. The same idea
   applies to you: resume from `index.md` and snapshots, which are 300–800 words each, not from the
   documents they summarise.

**What is still yours:** the hook cannot see your live percentage, so if `/context` (Claude Code) or the
Codex status line shows you at 60% in the middle of a stage, finish by writing that stage's snapshot from
what is established, then let the compaction happen. Finishing "one more thing" past 70% is how the e027
misattribution happened (a past Ads M1 build). And the 60% is a team observation from Ads M1 and the first team runs,
not a vendor figure; if a later run shows a different cliff, change the number in the profile, not the rule.

## 3c. Which model a session actually runs on

The profile's `base_model` is a **record and a recommendation**, not an override. The interactive session
runs on whatever the host was told: in Claude Code, `/model` in the session wins, then `--model`, then
`ANTHROPIC_MODEL`, then the `model` key in a settings file (which is what `/model` with Enter writes); in
Codex, `model` and `model_reasoning_effort` in `~/.codex/config.toml`, or the session's own `/model`
choice. Council lenses are unaffected by the session's setting: each lens is a separate call with the
registry's model and effort pinned (`model:` in the agent file through shunt, or
`codex exec -c model_reasoning_effort=xhigh`), so an Astra-medium session still gets an Astra-xhigh
adversary. What runs at the session's effort is the operator's own work: authoring, edits, the
synthesis you do by hand. Onboarding therefore offers to write the recommended base model into the host
config, and records `base_model: kept: <model>` when the person prefers their own. If the session and the
profile disagree, the session is right about what ran; fix the config, not the record.

## 3d. Tool read caps

When a read tool truncates an artifact (a past Ads M1 build hit a 256 KiB cap on a ~290 KB design file),
get the whole artifact another way before editing, and never edit and push a truncated copy: the push
would ship the truncation.

## 4. What stays true

Never route a whole session through a non-Anthropic model (doc 22 §8.2); route discrete calls whose
input and output are files. A reviewer never shares the author's family. A model id lives in the
registry and in agent frontmatter, nowhere else.
