# Cost Estimation Reference

Use this reference when building the self-cost footer for `/apollo-eng:deep-insights`.

The Workflow completion notification exposes one aggregate `subagent_tokens` count and `agent_count`, but it does not split those tokens by model. The workflow return includes `cost_basis`, which gives the exact agent composition:

- `reviewers`: one reviewer agent per analyzed session, normally Sonnet.
- `synth`: one synthesis agent, inherited Opus.
- `loader`: one args-loader agent on Haiku when the args file path is used.

Because token counts are aggregated, report self-cost as approximate:

```text
≈$<cost> · <subagent_tokens/1000>k agent-tok · <agent_count> agents · <cost_basis split>
```

Use list-price rough rates only for the blended estimate:

| Model | Rough blended rate |
|---|---:|
| Haiku | ≈$1/Mtok |
| Sonnet | ≈$3/Mtok |
| Opus | ≈$15/Mtok |

Recommended approach:

1. Build the visible agent split from `cost_basis`, for example `15 Sonnet reviewers · 1 Opus synth · 1 Haiku loader`.
2. Estimate the blended dollar cost from the aggregate `subagent_tokens` and the split.
3. Label the result with `≈` because the harness does not expose per-model token counts.
4. Never present the self-cost estimate as exact accounting.
