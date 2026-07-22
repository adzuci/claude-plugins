# Cost Estimation Reference

Use this when building the self-cost footer for `/apollo-eng:codex-insights` and when talking
about spend in the report. Codex logs expose **exact token counts**, not dollars, so all
dollar/credit figures are approximate and must be labelled `≈`.

## Tokens → credits → dollars

Apollo's convention (matching the `codexbar` cost script in this skill's renderer):

- `1 credit ≈ 1K tokens` — the enumerator emits `credits = round(total_tokens / 1000)`.
- Enterprise overage rate: `≈$0.04 per credit`. So `≈$X = credits × 0.04`.

Lead with **tokens** (exact) and treat credits/dollars as an approximate, relative overlay.
Never present them as exact accounting.

## Self-cost footer

A skill that audits token spend must disclose its own. The run has three parts:

- **Enumerator** — deterministic Node script; **0 model tokens**.
- **Judgment pass** — the only model-token cost: reading the compact ledger + any targeted
  transcript lines to judge ROI/outcome. Read the session's own usage with `/usage` or `/status`
  if visible; otherwise estimate from the ledger size.
- **Renderer / site bundle** — deterministic Node scripts; **0 model tokens**.

Footer shape (label with `≈`):

```text
≈ this analysis: enumerator 0 model-tok (deterministic) · judgment ≈<N>k tok · rendering 0 tok
```

The point is the same discipline the report recommends: spend tokens on judgment, not on
re-reading setup or formatting.
