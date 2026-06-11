---
name: which-model
description: Manual-invocation only. Look up available AI coding models in Claude Code, Cursor, Windsurf, and Codex, compare recent benchmarks, and recommend which models to use for specific coding workflows. Run via /apollo-eng-devops:which-model.
disable-model-invocation: true
---

# Which Model

Report on available models across AI coding tools, recent benchmarks, and recommendations.

This skill is intentionally direct-invocation only. Do not activate from natural-language model-selection questions unless the user explicitly invokes `/apollo-eng-devops:which-model`.

## Instructions

When activated, perform these steps:

1. **Search for current model lists** — web-search each tool's docs for the latest available models:

   - Claude Code: `docs.claude.com model configuration`
   - Cursor: `cursor.com/help/models-and-usage/available-models`
   - Windsurf: `docs.windsurf.com chat/models` and `docs.windsurf.com plugins/cascade/models`
   - Codex: `developers.openai.com/codex/models`

1. **Search for benchmark data** — web-search for recent results:

   - `SWE-bench Verified leaderboard <current year>`
   - `AI coding model benchmarks comparison <current year>`

1. **Search for new releases** — web-search for models released in the past 7 days:

   - `new AI model releases this week <current date>`

1. **Compile the report** using the template below.

## Report Template

```markdown
# AI Coding Model Report — <date>

## Available Models by Tool

### Claude Code
| Alias | Model | Context | Notes |
|-------|-------|---------|-------|
| (populate from search) |

### Cursor
| Model | Provider | Notes |
|-------|----------|-------|
| (populate from search) |

### Windsurf
| Model | Type | Notes |
|-------|------|-------|
| (populate from search) |

### Codex
| Model | Context | Notes |
|-------|---------|-------|
| (populate from search) |

## Benchmark Snapshot

| Model | SWE-bench Verified | SWE-bench Pro | Notes |
|-------|-------------------|---------------|-------|
| (populate from search) |

## Recommendations

| Use Case | Recommended Model | Why |
|----------|------------------|-----|
| Daily coding / autocomplete | (best speed/quality ratio) | |
| Complex refactors / architecture | (strongest reasoning) | |
| Quick edits / simple tasks | (fastest / cheapest) | |
| Long-context sessions | (best with large contexts) | |
| Multi-file agentic tasks | (best agentic benchmark) | |

## New Releases (Past 7 Days)

| Model | Provider | Release Date | Key Details |
|-------|----------|-------------|-------------|
| (populate from search) |

## Notes
- Benchmarks are point-in-time; re-run this skill for fresh data
- Model availability varies by plan tier and region
- Some researchers have raised contamination concerns with SWE-bench Verified; consider Pro scores as a complementary signal
```

## Tips

- Always web-search live data — do not rely on training knowledge for model lists or scores
- If a model just launched and has no benchmarks yet, note that explicitly
- Flag any models that were deprecated or removed since the last check
