---
name: best-model-for-use-case
description: Recommend the best LLM for a specific use case by scoring candidates on quality, latency, and cost via the Artificial Analysis MCP.
argument-hint: "<use case description, path to system prompt/config, or 'optimize cost|latency|quality for <feature>'>"
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash, WebSearch, WebFetch, AskUserQuestion, mcp__artificial-analysis__list_models, mcp__artificial-analysis__get_model
---

# Best Model for a Use Case

Pick the model that best fits one concrete use case. The output is a **ranked table** of candidate
models scored on **quality, latency, and cost**, sorted by a **composite score whose weights
reflect what the user is optimizing for**. Never hand-wave — every number comes from the Artificial
Analysis MCP or from tokens you actually counted.

## Prerequisites

Requires the `artificial-analysis` MCP. If `mcp__artificial-analysis__list_models` or
`mcp__artificial-analysis__get_model` are unavailable, tell the user to:

1. Get their own API key at <https://artificialanalysis.ai>. There is no shared Apollo team key.
1. Install the MCP with that key, then restart:

```bash
claude mcp add artificial-analysis -e AA_API_KEY=<your-key> -- npx -y artificial-analysis-mcp@1.0.1
```

The MCP is a community package, not published by Artificial Analysis — keep the version pinned.

## Usage

```
/apollo-eng:best-model-for-use-case optimize latency for the Magic Column prompt
/apollo-eng:best-model-for-use-case dapi/prompts/my_feature_system_prompt.md
/apollo-eng:best-model-for-use-case what model should I use for this search ranking feature?
```

Work the phases in order. If no use case was provided, start with Phase 0. Otherwise go straight
to Phase 1 — a recommendation built on a misunderstood use case is worse than none.

______________________________________________________________________

## Phase 0 — Intake (run only when no use case was provided)

If the user invoked the skill with no argument, or the argument is too vague to act on, do **not**
guess — run this intake flow before proceeding.

### Step 1 — Ask for the use case

Use `AskUserQuestion` to ask:

> What is the use case? Describe it in plain language, or share a link / file path to the system
> prompt, feature spec, or code that powers it.

Accept any of: a prose description, a file path, a GitHub link, a Jira ticket, or a short
feature name you can look up.

### Step 2 — Verify it is an LLM use case

Once you have a description or artifact, check whether an LLM is actually involved:

- If the answer is clearly yes (e.g. "we call GPT-4o to classify this", there's a system prompt,
  or you find a model client call in the code) — proceed.
- If it is unclear, ask once: "Does this feature make calls to an LLM?" If no, stop and tell the
  user this skill only applies to LLM-powered features.

### Step 3 — Find and confirm the current model

Before doing any analysis, identify the current model:

1. Search the codebase (Grep/Glob) for the feature name, prompt file, or config key to locate
   the LLM call site. Read the surrounding config to extract the provider's model name.
1. If the user already stated a current model (e.g. "we're using GPT-4o"), verify it matches
   what you found in the code. If they match, confirm it back. If they differ, surface the
   discrepancy — don't silently pick one.
1. If you cannot find it in code, ask the user directly: "What model is currently powering this?"

Only proceed to Phase 1 once the current model is confirmed.

______________________________________________________________________

## Phase 1 — Understand the use case deeply

Goal: know (a) what the model actually has to do, (b) which benchmark measures it, (c) the
token profile (input vs. output size), and (d) how latency-sensitive it is.

1. **Read what the user gave you.** If they passed a path, `Read` it. If they described a feature,
   locate it with `Grep`/`Glob`. Read the **full system prompt** and any available
   examples (inputs + expected outputs).
1. **Find the current model + where it's wired.** Grep for the feature name or prompt filename to
   find the LLM client/config call site. Note the current model's **exact provider model name**
   (e.g. `gemini-3.1-flash-lite`), any reasoning-effort setting, temperature, max
   tokens, whether prompt caching is on, and whether the call is single-shot or agentic.
1. **Pick the primary benchmark.** Decide what the use case mostly stresses and pick the one AA
   benchmark from the table below that best measures it. Say which one and why. It drives both the
   Quality axis and the quality floor — a model's other benchmark scores don't count.
1. **Closed-set classification?** If the task picks from a fixed list of labels, mention that a
   fast non-LLM classifier may be worth evaluating alongside the LLMs, then continue.
1. **Estimate the token profile.** Count system-prompt tokens (~chars/4), estimate typical live
   input and typical output length from examples. Blended price lies when input dwarfs output
   (classify/extract) or vice-versa (long generation) — use actual token counts for cost.
1. **Gauge latency sensitivity.** Interactive/streaming → TTFT dominates. Long generation or batch
   → throughput (tokens/sec) dominates. Agentic multi-turn → both compound per turn.

If the current model is unclear after the walkthrough, state what you found and ask — don't guess.

### Quality dimension → benchmark field

Fields in each model's `benchmarks`. Where a row lists two, pick the one more candidates have
scores for:

| Use case is mostly… | Primary benchmark field(s) |
|---|---|
| General assistant / reasoning | `intelligence_index` |
| Coding / code generation | `coding_index`, `livecodebench` |
| Agentic / tool use / multi-turn | `tau2`, `terminalbench_hard` |
| Math / quantitative | `math_index`, `aime_25` |
| Hard science / expert QA | `gpqa`, `hle` |
| Broad knowledge recall | `mmlu_pro` |
| Strict instruction / format following | `ifbench` |
| Long-context retrieval/reasoning | `lcr` |

Use `intelligence_index` as a fallback when no sharper benchmark fits.

______________________________________________________________________

## Phase 2 — Confirm weights, quality floor, and constraints

The composite score is `w_quality·Q + w_latency·L + w_cost·C`, weights summing to 1.

- **Stated target** ("make it cheaper", "cut latency", "highest quality") — infer the weights and
  state them back before scoring. Never zero out quality — a cheap model that fails the task saves
  nothing.
- **No stated target** — default to `{quality 0.5, cost 0.25, latency 0.25}` and say so.
- **Ambiguous** — use `AskUserQuestion` with: Quality-first, Cost-first, Latency-first, Balanced.
  Ask once only.

**Quality floor.** Default to the current model's score on the primary benchmark minus 5% relative
(e.g. current `ifbench` 0.772 → floor 0.733). State it alongside the weights; the user can change
it. Min–max scoring hides how far behind a model is — the worst in the set scores Q = 0 however bad
it is — so without a floor a cheap or fast model can win on quality it doesn't have. If the current
model has no score on the primary benchmark, ask the user for a floor.

**Constraints.** Before scoring, ask with `AskUserQuestion` whether the user wants to set any
constraints; "None" is a valid answer. Name the common kinds so they know what's possible:

- Creator or model deny-list (e.g. "no Kimi")
- Provider allow-list, or "must be callable from our stack"
- Hosting region (e.g. US-hosted only)
- Context window minimum or max price per call

AA has no hosting or region data. Check those in the provider's docs with `WebSearch`/`WebFetch`, or
mark the model "unverified" — don't guess. The floor and constraints filter the candidate set;
weights rank what survives.

Default weight suggestions by stated intent:

| Intent | Q | L | C |
|---|---|---|---|
| "optimize cost" | 0.30 | 0.10 | 0.60 |
| "optimize latency" | 0.35 | 0.55 | 0.10 |
| "best quality" | 0.65 | 0.25 | 0.10 |
| Balanced (default) | 0.50 | 0.25 | 0.25 |

______________________________________________________________________

## Phase 3 — Build the candidate set

The MCP downloads AA's full catalog on every call, and `list_models` already returns pricing, speed,
and benchmarks for each row. Score straight from `list_models` output — do not call `get_model` per
finalist. One to three calls per run keeps usage well under AA's free-tier daily request cap.

1. **Pull candidates** with `list_models`, one call per creator in scope, `limit` ~15. `sort_by`
   accepts only `intelligence_index`, `coding_index`, `math_index`, `mmlu_pro`, `gpqa`, the price
   fields, `speed`, `ttft`, and `release_date`. When the primary benchmark is not one of these (e.g.
   `ifbench`, `tau2`, `lcr`), sort by `intelligence_index` and rank by the primary benchmark from the
   results.
1. **Identify models by `id`.** Every row has a stable UUID `id`; names and slugs change. `get_model`
   matches on slug substring, so `get_model("gemini-3-1-flash-lite")` silently returns
   `gemini-3-1-flash-lite-preview`. Match rows on `id` and show the name only as a label. Use
   `get_model` only when the creator is unknown, and confirm its returned `name` is the model you
   meant.
1. **Baseline row.** Find the current model's AA row and record its `id`. If the AA name differs from
   the provider model name in code, confirm the match with the user. If the current model is
   fine-tuned, internal, or otherwise not in AA:
   - It has a public base model → score the base as `<base> (proxy for current)` and say the
     fine-tune may behave differently.
   - No base model → mark the baseline "not in AA", rank candidates without it, and state plainly
     that no comparison against the current model is possible.
1. **Shortlist ~5–10** realistic candidates. Include at least one "cheaper/faster, slightly lower
   quality" option and one "higher quality, pricier" option so the trade-off is visible.
1. **Bucket each shortlisted model:**
   - **Ranked** — has the primary benchmark and a non-zero price.
   - **Insufficient data** — missing the primary benchmark. Common for models released in the last
     few weeks, which are often the ones the user is asking about — keep them; Phase 5 lists them
     below the table.
   - **Excluded** — below the quality floor, ruled out by a constraint, or `$0` price (deprecated,
     preview, or open-weights listing) unless the user self-hosts. Keep the reason for each.

______________________________________________________________________

## Phase 4 — Score

Normalize each raw metric to [0,1] across the candidate set (min–max, 1 = best). Show the formula
and raw numbers so the ranking is auditable.

**Quality (Q)** — the primary benchmark only, higher is better:

```
Q = (q − q_min) / (q_max − q_min)
```

**Cost (C)** — lower is better. Prefer per-call cost from the Phase-1 token profile:

```
cost_per_call = (input_tokens · price_input + output_tokens · price_output) / 1e6
C = (cost_max − cost) / (cost_max − cost_min)
```

Fall back to `price_blended` only when no token profile is available (say so). If prompt caching is
on, note that it further favors large-system-prompt models; AA doesn't expose cache pricing — flag
it, don't invent numbers.

**Latency (L)** — combine TTFT and throughput per Phase-1 sensitivity:

```
T = (ttft_max − ttft) / (ttft_max − ttft_min)   # lower ms = better
S = (s − s_min) / (s_max − s_min)                 # higher tok/s = better
L = a·T + (1−a)·S
```

`a` = 0.6 interactive / 0.2 long-generation / 0.5 default.

**Composite:** `Score = w_quality·Q + w_latency·L + w_cost·C`

Guard rails:

- AA reports some unmeasured values as `0`, not `null`. Treat `tokens_per_second == 0` and `$0`
  prices as missing — never as the slowest model or a free one.
- `null` metrics are missing, never 0.
- Missing axis: every ranked row must be scored on the same axes, or composites stop being
  comparable. If fewer than three ranked rows have latency data, drop the latency axis for the whole
  table, renormalize the remaining weights to sum to 1, and say so. Otherwise move rows lacking
  latency data to "Insufficient data".
- Degenerate axis (max = min): normalizes to a constant — note it, don't let it silently swing
  rankings.
- Apply the quality floor and constraints as hard filters *before* normalizing, not as soft
  penalties.

______________________________________________________________________

## Phase 5 — Present

Output one ranked table sorted by composite score descending. Mark the current model `(current)`.
Include raw metrics and the composite so the user can re-weight if they disagree.

```
Use case: <one line>   |   Quality axis: <benchmark> (floor <x>)   |   Weights: Q .50 / L .25 / C .25
Token profile: ~<in> in / ~<out> out per call

| Rank | Model            | Quality (raw) | $/call  | TTFT ms | tok/s | Q    | L    | C    | Score |
|------|------------------|---------------|---------|---------|-------|------|------|------|-------|
|  1   | …                | …             | …       | …       | …     | …    | …    | …    | …     |
|  2   | … (current)      | …             | …       | …       | …     | …    | …    | …    | …     |
```

Below the table, list **Insufficient data** models with the raw numbers AA does have and which
fields are missing — no composite. Then list excluded models with the reason for each.

Follow with ≤6 lines:

- **Recommendation** — top-scoring model, and whether it beats current enough to switch.
- **Trade-off** — what you'd give up (e.g. "+8% quality but 2.3× cost").
- **The switch** — exact config change: the provider's API model name, not the AA slug (AA
  `gemini-3-1-flash-lite-preview` is Google `gemini-3.1-flash-lite`), plus the reasoning-effort
  setting an AA variant implies (`(High)`, `(Medium)`), and any caveats on caching or max tokens.
  Take the name from the codebase's model config. If it isn't there, look it up in the provider's
  model docs with `WebSearch`/`WebFetch`.
- If nothing beats the current model on the chosen weights, say so plainly and show the runner-up.
- If an insufficient-data model looks promising on what AA does have, say so and suggest re-running
  once AA publishes the primary benchmark.

See [references/example-output.md](references/example-output.md) for a complete run.

Do not edit any config unless the user explicitly asks — this skill recommends; it does not switch.
