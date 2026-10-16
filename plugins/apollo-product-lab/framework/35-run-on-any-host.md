# 35 — Running the harness in Claude Code, Codex, or a script

The agent and skill files are the program. Three runtimes execute them; the differences are listed
so nobody discovers them mid-run.

| Concern | Claude Code | Codex CLI | `claude -p` script |
|---|---|---|---|
| Agents | `.claude/agents/*.md` natively | `AGENTS.md` sections, generated from the Claude sources by `scripts/gen-codex-agents.sh` (never hand-edit; CI drift check as in fabric-studio) | `--agent` not available; pass the agent file content as the prompt |
| Skills | `.claude/skills/*/SKILL.md` | `.agents/skills/` generated the same way; plugins per user in `~/.codex/config.toml` | inline |
| Model routing | frontmatter `model:`; non-Anthropic ids through shunt (doc 32) | Codex's own model (OpenAI); Anthropic models unreachable | `--model <id>`; non-Anthropic ids through shunt with the env flags in doc 32 §3 |
| Deny hooks (gates) | `PreToolUse` with exit 2 | one-time trust prompt for committed hooks; verify deny semantics before relying on a gate (doc 13 §7) | none; gates are advisory, say so in the snapshot |
| Snapshots and ledger | identical files | identical files | identical files |
| Figma / Fabric Studio | Figma connector available | Figma not available on Codex; design lenses run in Claude Code | n/a |

## Generating the Codex view

`scripts/gen-codex-agents.sh` writes `AGENTS.harness.md`: one section per `.claude/agents/*.md` with
its name, description, surfaces and the body, plus a pointer to the model registry. Fabric Studio's
`scripts/gen-codex.sh` is the reference pattern (committed output, CI fails on drift). Do not overwrite
the repo's root `AGENTS.md`, which has other owners; link the generated file from it.

## What must be true on every host

- The snapshot discipline (doc 33): the run is resumable from disk on any host.
- The registry (doc 32) is the only place a model id lives.
- A gate that cannot deny on a host is recorded as advisory in that run's snapshots.
- Where there is no working tree to write (claude.ai chat, a cloud sandbox), the record lives in Notion
  in the same schema (doc 45), so it is still resumable and can be copied back to disk.

## Host table (2026-09-21)

| | Claude Code | Codex |
|---|---|---|
| Base model recommended by onboarding | Fable 5.1 (keep your current one if you say so) | gpt-6-astra, effort xhigh for design and review, medium for routine slices |
| Adversary family | OpenAI via shunt (`gpt-6-astra` or `gpt-5.6-sol`) | Anthropic via detached `claude -p --model claude-fable-5-1` with read-only tools |
| Glean family | MCP `glean_default` | same server in the Codex MCP config |
| Skills | `/apollo-product-lab:<skill>` | same skills from the same plugin (`codex plugin install apollo-product-lab`) |
| Agents | Claude Code sub-agents | generated `AGENTS.harness.md` view (`scripts/gen-codex-agents.sh`); lenses run as separate `codex exec` calls whose input and output are files |
| Second-family setup | `brew install pleaseai/tap/shunt`, copy `shunt.toml.example`, `brew services start shunt`, `export ANTHROPIC_BASE_URL=http://127.0.0.1:3001`, `codex login` | `npm i -g @anthropic-ai/claude-code`, `claude login` |

The record on disk (doc 33) is identical on both hosts, which is what lets one person run the council in
Claude Code and another read the memo in Codex.

## Where the plugin loads (2026-09-22, from the Claude Code docs)

| Surface | Plugin loads? | How | Limits |
|---|---|---|---|
| Claude Code CLI | yes | `claude plugin install apollo-product-lab@apollo-plugins` (marketplace already registered by leadgenie's `.claude/settings.json`) | none |
| Claude Desktop, **Code** tab, local or SSH | yes | same engine and same config files as the CLI; nothing extra | Fabric Studio does not work from the Desktop Code tab (observed 2026-09-22, Akansh; parked, cause not investigated). Designers use the CLI for Fabric Studio work; everything else is unaffected |
| claude.ai/code and Desktop **cloud** sessions | yes, but not from the repo | a cloud session ignores the repo's `enabledPlugins` and `extraKnownMarketplaces`. Enable the plugin for your claude.ai account (Desktop → Extend Claude Code) or have the org turn it on; it then loads as `apollo-product-lab@synced` with skills, agents, hooks and MCP servers | repo hooks and `.mcp.json` load only in single-repo sessions; shunt is a laptop process, so the second family there is `claude -p`/`codex exec` only if the sandbox has them, otherwise the adversary lens is tagged `independence: same-family` |
| claude.ai/code **while the PR is a draft** (not yet on any marketplace claude.ai syncs) | yes, by upload | `python3 plugins/apollo-product-lab/scripts/package.py --only plugin` from the branch (writes `dist/apollo-product-lab.zip` with a `BUILD` file) and upload it at claude.ai/code → Customize → Plugins → Upload. The uploader wants `.claude-plugin/plugin.json` at the archive root (a wrapping folder fails validation) and rejects skill descriptions containing anything shaped like an XML tag, so placeholders in `description:` lines are UPPERCASE words, never `<like-this>`; no top-level `bin/`, scripts live in `scripts/`. It loads as `apollo-product-lab@synced` with skills, agents, hooks and MCP servers. Re-upload after each push; the upload does not track the branch | same cloud limits as the row above. There is no shunt and no Codex plugin in the sandbox, so the council step 3b probe finds no OpenAI route: on prd and design the adversary runs on the **Glean family** by chat (`independence: unknown` until the Model Hub model is confirmed); on erd, plan and pr it is the same-family Anthropic fallback, tagged, with Glean at most a labelled second reading; the synthesizer runs on Opus tagged same-family. Read a memo produced this way as a not-yet-independent review, and rerun the council from a laptop with shunt before the human decision when the change is product-size |
| claude.ai **chat** (and Desktop Chat) | skills only, since 2026-10-09 | upload the six chat Skills built by `scripts/package.py` (`dist/skills/*.zip`) under Settings → Capabilities → Skills, with code execution on; add Notion, Figma and Glean as claude.ai connectors | no Agent tool, no hooks, no working tree: storage is `notion` for records and profile (doc 45), lenses run one after another in the thread and the memo is tagged `degraded: in-thread lenses`; rerun a product-size council from a Code surface before deciding. Cowork was not tried |
| Codex CLI | skills yes | `codex plugin install apollo-product-lab` from the marketplace in `.codex/config.toml`; agents come from `AGENTS.harness.md` (above) | whether Codex honours the plugin's hooks and `.mcp.json` is unconfirmed; treat both as Claude Code only until someone runs the cold-start proof (doc 41 §4) in Codex |

Before #292 merges, point the marketplace at the branch instead of `main`: in `~/.claude/settings.json`
(not the repo's) add `"apollo-plugins-harness": { "source": { "source": "github", "repo": "apolloio/claude-plugins", "ref": "akansh/harness-split-1" } }` under `extraKnownMarketplaces`, or run
`/plugin marketplace add https://github.com/apolloio/claude-plugins.git#akansh/harness-split-1`, then
install `apollo-product-lab@apollo-plugins-harness`. Remove that marketplace after the merge so one copy
loads. Sources: code.claude.com/docs/en/cloud-environments, /desktop, /plugins-reference#synced-plugins,
/plugin-marketplaces.
