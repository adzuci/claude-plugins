# Example Output

A complete run for `/apollo-eng:best-model-for-use-case optimize cost for the Magic Column prompt`.
Numbers come from a live Artificial Analysis pull on 2026-10-09 — they show the format, not current
prices or scores.

## What the Skill Established First

- **Use case:** Magic Column field generation — one structured answer per table row, batch.
- **Current model:** `gemini-3.1-flash-lite` in the dapi LLM config. AA row: "Gemini 3.1 Flash-Lite",
  `id` `598190f8-dc9c-4fea-a7ea-4b81c402ab18` (AA slug `gemini-3-1-flash-lite-preview`).
- **Quality axis:** `ifbench` (strict instruction and format following). Not a valid `sort_by`, so
  candidates were pulled with `sort_by: intelligence_index` and ranked on `ifbench` from the results.
- **Token profile:** ~55,000 input / ~300 output per call. Input dominates, so per-call cost is used,
  not blended price.
- **Weights:** "optimize cost" → Q .30 / L .10 / C .60.
- **Quality floor:** current `ifbench` 0.772 − 5% → 0.733.
- **Constraints:** user answered "None".
- **Calls:** 3 `list_models` calls (Google, OpenAI, Anthropic), no `get_model` per finalist.

## Output

```
Use case: Magic Column field generation   |   Quality axis: ifbench (floor 0.733)   |   Weights: Q .33 / C .67
Token profile: ~55,000 in / ~300 out per call
Latency axis dropped: only 1 of 4 ranked models has AA speed data (current model has none).
Weights renormalized from Q .30 / L .10 / C .60.

| Rank | Model                           | ifbench | $/call  | Q    | C    | Score |
|------|---------------------------------|---------|---------|------|------|-------|
|  1   | Gemini 3.1 Flash-Lite (current) | 0.772   | $0.0142 | 1.00 | 1.00 | 1.00  |
|  2   | Gemini 3.5 Flash (High)         | 0.763   | $0.0852 | 0.67 | 0.29 | 0.41  |
|  3   | Gemini 3.1 Pro Preview          | 0.771   | $0.1136 | 0.97 | 0.00 | 0.32  |
|  4   | Gemini 3.5 Flash (Medium)       | 0.746   | $0.0852 | 0.00 | 0.29 | 0.19  |

Insufficient data (no ifbench yet — not scored):
| Model                       | Released   | Intelligence Index | $/call  | tok/s | Missing          |
|-----------------------------|------------|--------------------|---------|-------|------------------|
| Gemini 3.8 Flash (High)     | 2026-09-02 | 40.9               | $0.0424 | 124   | ifbench, tau2    |
| GPT-6.1 Sol (Medium)        | 2026-09-29 | 47.8               | $0.1130 | 51    | ifbench, gpqa    |
| Claude Sonnet 5.5 (Xhigh)   | 2026-09-28 | 51.9               | $0.1130 | 97    | ifbench, gpqa    |

Excluded:
- gpt-oss-20b (High) — ifbench 0.651, below floor 0.733 ($0.0039/call)
- GPT-5.6 Sol (Max) — ifbench 0.727, below floor 0.733
- Gemini 2.5 Flash Preview (Sep '25) — $0 price on AA (deprecated)
- Gemma 4 31B — $0 price on AA (open weights; include only if self-hosting)
```

- **Recommendation:** stay on Gemini 3.1 Flash-Lite. It leads `ifbench` and is the cheapest model
  above the floor; nothing beats it on these weights.
- **Runner-up:** Gemini 3.5 Flash (High) — 0.009 lower `ifbench` at 6.0× the cost per call.
- **Cheaper option:** gpt-oss-20b is 0.27× the cost, but its `ifbench` is 16% below current, so the
  floor excluded it. Lower the floor only if the format errors are acceptable.
- **Watch:** Gemini 3.8 Flash costs 3.0× current, but has a much higher Intelligence Index (40.9 vs 15.6) and
  measured speed. Re-run once AA publishes its `ifbench`.
- **Caching:** Magic Column uses prompt caching; AA has no cache pricing, so real per-call costs are
  lower for every model with a cached system prompt. No config change suggested.
