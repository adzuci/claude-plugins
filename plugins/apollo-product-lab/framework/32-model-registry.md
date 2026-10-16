# 32 — Model registry: one harness, many model families, any host

> Extends doc 13 (routing rationale) and doc 22 (token routing). This is the operational mapping the
> agents and skills actually read. Source of truth is `models/model-registry.yml`; this doc explains it.

## 1. Three things the registry decides

1. **Which family does a role run on** (capability and cost tier).
2. **Which family reviews it** (independence: a reviewer never shares the author's family).
3. **How a model is reached from the host you happen to be in** (Claude Code, Codex CLI, `claude -p`
   scripts). The agent file never changes; only the route does.

## 2. Families and reachability (2026-09-18)

| Family | Models | Reached via | Status |
|---|---|---|---|
| Anthropic | `claude-fable-5-1` (Fable 5.1), `claude-opus-5-5` (Opus 5.5), `claude-sonnet-5-5` (Sonnet 5.5), `claude-haiku-4-5-20251001` | native in Claude Code; `claude -p --model <id>` in scripts | measured in production |
| OpenAI | `gpt-6-astra` (effort `xhigh` for reviews) | **shunt** route `gpt-6-astra → provider codex` (uses `codex login`); or `codex exec` directly | used for ADR-P2 review and cross-vendor code review (ledger e025) |
| Google | Gemini | **Glean Assistant** (`glean_default.chat`) is backed by a Glean-chosen model with **no model parameter** [P, tested 2026-09-10]; a model-selectable route needs a bridge (MCP server or small service) | corroboration lane only; selectable route **not wired** |
| DeepSeek | DeepSeek | same as Gemini: only if Glean or a bridge exposes it | **not wired** |
| Internal record | Glean Assistant RAG over Slack, Docs, GitHub, Jira | `glean_default.search` / `chat` | wired; independent *system*, not a selectable model |

**Data-handling gate (doc 13 §4):** routing internal documents to a second vendor is a use-case approval,
not a vendor approval. OpenAI via Codex is approved for code and design review in this repo; check
before sending a constraint register or customer data anywhere else.

## 3. Host-agnostic execution

The agent and skill files are the program; the host is a runtime. Three runtimes are supported:

| Host | How an agent's `model:` resolves | Notes |
|---|---|---|
| Claude Code (interactive) | `model: fable \| opus \| sonnet \| haiku` natively; `model: gpt-6-astra` **only when shunt is running** (`brew services start shunt`, `ANTHROPIC_BASE_URL=http://127.0.0.1:3001`) | the normal case |
| Claude CLI script (`claude -p`) | same ids; for non-Anthropic ids add `CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT=1 CLAUDE_CODE_MAX_CONTEXT_TOKENS=400000 --tools '' --max-turns 3`, run detached (`nohup … & disown`) | the Astra review recipe |
| Codex CLI | reads `AGENTS.md` and `.codex/config.toml`; agents are generated from the Claude sources (doc 35) | hooks with deny semantics are the portability gate (doc 13 §7) |

Rule: **never hard-code a model id inside a skill body.** Skills name a *role* (`review.adversary`,
`build.slice-owner`); the registry maps the role to a family and a fallback; the agent frontmatter
carries the resolved id so the host can read it.

## 4. Role → family mapping

See `models/model-registry.yml`. The shape:

```yaml
roles:
  review.adversary:
    primary: openai/gpt-6-astra      # must differ from the author family
    fallback: anthropic/fable-5-1     # only if the author was not Anthropic
    independence: family != author.family
```

Independence is checked at dispatch by the council skill (doc 34): if the only reachable reviewer
shares the author's family, the finding is tagged `same-family` and the human is told, instead of the
harness silently blessing its own work.

## 5. Adding a model or a provider

1. Add the family and route to `models/model-registry.yml` with `status: unwired | wired | measured` and a
   `reachability` note with a date and [P]/[S]/[U] tier.
2. If reached through shunt, add a `[[routes]]` block to `models/shunt.toml.example` and to your local
   `~/.config/shunt/shunt.toml`.
3. Run the capability protocol in doc 13 §6 before changing any `measured` row.
4. Never route a full session through a non-Anthropic model (doc 22 §8.2); route discrete calls (a
   review, an extraction) whose input is a file and whose output is a snapshot.
