---
name: litellm-setup
description: Manual-invocation only. Create a secret-free LiteLLM route to a local PAIR or Ollama endpoint and optionally install LiteLLM in an isolated environment. Run via /local-ai:litellm-setup.
argument-hint: '[--model MODEL]'
disable-model-invocation: true
---

# LiteLLM Setup

Put a local, authenticated LiteLLM gateway in front of PAIR's OpenAI-compatible
loopback endpoint. PAIR decides which machine serves a request; LiteLLM exposes
a named model route and can translate client protocols.

Read the current [LiteLLM documentation](https://docs.litellm.ai/docs/) and
release notes before installation. The bundled installer pins a specific
version and installs it inside a dedicated virtual environment rather than the
system Python environment.

## Workflow

1. Resolve the bundled script relative to this skill directory and run the
   read-only check:

   ```bash
   scripts/litellm_setup.sh --check
   ```

1. Explain the planned configuration path, virtual-environment path, pinned
   version, local upstream URL, and required environment variables.

1. Ask before writing the configuration. After confirmation:

   ```bash
   scripts/litellm_setup.sh --apply
   ```

1. Ask separately before downloading and installing Python packages. After
   confirmation:

   ```bash
   scripts/litellm_setup.sh --apply --install
   ```

Use `--model <ollama-model>` when the PAIR host serves a different model.

## Secrets

The generated YAML stores environment-variable names, never secret values:

- `LOCAL_AI_PROXY_KEY` is the non-empty upstream key LiteLLM sends to the local
  OpenAI-compatible endpoint. PAIR currently ignores it.
- `LITELLM_MASTER_KEY` protects the local LiteLLM gateway. Generate a strong
  value, keep it out of shell history and source control, and provide it through
  the environment or a secret manager.

Bind LiteLLM to `127.0.0.1`. Do not expose it through a router or public reverse
proxy. A local gateway can translate request formats, but it cannot repair
PAIR's upstream structured-tool-call defect.

## Verify

Start the isolated installation on loopback:

```bash
LITELLM_MASTER_KEY='<secret>' LOCAL_AI_PROXY_KEY='local' \
  ~/.local/share/local-ai/litellm-1.101.0/bin/litellm \
  --config ~/.config/local-ai/litellm/config.yaml \
  --host 127.0.0.1 --port 4000
```

Then list models through LiteLLM using the master key. A successful list proves
the local gateway is responding; use PAIR's Jobs view to prove another machine
served an inference request.
