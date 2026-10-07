# Local AI Plugin

Personal, local-first workflows for running open models on hardware you control.

**Companion post:** [Two Macs, One Local Model Pool](https://adzuci.github.io/claude-plugins/local-ai.html)

## Skills

### `/local-ai:pair-setup`

Installs, verifies, pairs, diagnoses, and removes NVIDIA Personal AI Router
(PAIR) on two Apple Silicon Macs. It pins the reviewed PAIR release, verifies
the downloaded disk image and application signature, and keeps routing
verification separate from a basic endpoint health check.

PAIR is experimental. Its current OpenAI-compatible proxy does not preserve
structured tool calls, so use it for plain completion experiments rather than
agent workloads until the upstream issue is fixed.

### `/local-ai:local-model-pick`

Recommends an Ollama model from the Mac's total and currently available memory.
It can optionally pull the chosen model after confirmation. The recommendations
are conservative starting points, not benchmarks.

### `/local-ai:litellm-setup`

Writes a secret-free LiteLLM starter configuration that exposes the PAIR proxy
as a named local route. It can optionally install the reviewed LiteLLM version
inside a dedicated virtual environment; it never installs into the system
Python environment.

## Install

```text
claude plugin marketplace add adzuci/claude-plugins
claude plugin install local-ai@adzuci-plugins
```

For Codex:

```text
codex plugin marketplace add adzuci/claude-plugins
codex plugin add local-ai@adzuci-plugins
```

Then begin with the read-only preflight:

```text
/local-ai:pair-setup host verify
```

## Safety Boundary

- Use machines you own or are explicitly authorized to administer.
- Pair only over a trusted private network while both machines are under your
  control.
- Do not expose PAIR or LiteLLM ports through a router or public reverse proxy.
- Treat model downloads, application installation, service changes, sleep
  changes, and uninstall as explicit mutations that require confirmation.
- Verify remote routing in PAIR's Jobs view. A successful `/v1/models` response
  is not proof that another machine served the request.
