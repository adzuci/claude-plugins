---
name: local-model-pick
description: Manual-invocation only. Recommend an Ollama model from a Mac's memory budget and optionally pull it after confirmation. Run via /local-ai:local-model-pick.
argument-hint: '[--pull]'
disable-model-invocation: true
---

# Local Model Pick

Choose a conservative Ollama model for the current Apple Silicon Mac. This is a
starting point for experimentation, not a performance benchmark.

## Workflow

1. Read the current model pages before treating a name, size, context window, or
   capability as current:

   - [Qwen3-Coder](https://ollama.com/library/qwen3-coder)
   - [gpt-oss](https://ollama.com/library/gpt-oss)
   - [Qwen3](https://ollama.com/library/qwen3)

1. Resolve the bundled script relative to this skill directory and run it with
   no arguments. This is read-only:

   ```bash
   scripts/local_model_pick.sh
   ```

1. Report total memory, currently available memory, the recommended model,
   model download size, and whether the current headroom is sufficient.

1. Ask for confirmation before downloading model weights. After confirmation:

   ```bash
   scripts/local_model_pick.sh --pull
   ```

## Defaults

| Total memory | Starting model | Published download size |
| --- | --- | --- |
| 64 GB or more | `qwen3-coder:30b` | 19 GB |
| 48–63 GB | `gpt-oss:20b` | 14 GB |
| 32–47 GB | `qwen3:14b` | 9.3 GB |
| Under 32 GB | `qwen3:8b` | 5.2 GB |

The thresholds intentionally leave room for the operating system, browser,
editor, build tools, and model context. Download size is not peak resident
memory. Reduce context length or choose a smaller model when memory pressure is
high.

When using PAIR, run this on the host only. The client should not install an
engine or model weights unless local serving is intentional.
