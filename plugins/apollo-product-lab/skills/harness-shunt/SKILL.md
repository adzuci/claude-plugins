---
name: harness-shunt
description: Set up, check, turn on or turn off shunt, the local model gateway that lets a Claude Code agent with model gpt-6-astra or gpt-5.6-sol run on OpenAI through your Codex login, so the council's adversary and synthesizer come from a second model family. Works in the Claude Code CLI and the Claude Desktop Code tab (local sessions); reports honestly that it cannot run in claude.ai/code or Cowork. Activate on "set up shunt", "second model family", "is shunt running", "route through shunt", "turn shunt off", or /harness-shunt [setup|status|on|off].
---

# harness-shunt

Read first: `${CLAUDE_PLUGIN_ROOT}/framework/37-model-bridge-and-context-budget.md` §1–3 and
`${CLAUDE_PLUGIN_ROOT}/framework/models/shunt.toml.example`. shunt (github.com/pleaseai/shunt) is a
proxy on `http://127.0.0.1:3001`: every `claude-*` model passes through to Anthropic untouched; the ids
listed in its `[[routes]]` (gpt-6-astra, gpt-5.6-sol) go to OpenAI through `codex login`. It is a laptop
process. No secrets are involved: the OpenAI side is your Codex session, the Anthropic side is your Claude
login.

## Where this works

| Host | Works? | Why |
|---|---|---|
| Claude Code CLI | yes | any launch; routing comes from `~/.claude/settings.json`, not the shell |
| Claude Desktop, Code tab, local or SSH session | yes | same engine, same settings file; the Desktop app does not inherit your shell exports, which is why this skill writes the setting instead of telling you to `export` |
| claude.ai/code, Desktop cloud sessions, Cowork | no | there is no localhost; the council falls back per doc 34 §3 (Glean on prd/design, same-family on code kinds) and tags the memo |

Say which row applies before doing anything: `[ -n "$CLAUDE_CODE_REMOTE" ]` or no writable `~/.claude`
means a cloud host; stop and say so.

## `status` (also the default with no argument)

Run, in one Bash call:

- `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3001/` → 200 means running.
- `test -f ~/.config/shunt/shunt.toml && grep -E '^model' ~/.config/shunt/shunt.toml` → the routed ids.
- `python3 -c "import json;print(json.load(open('$HOME/.claude/settings.json')).get('env',{}).get('ANTHROPIC_BASE_URL'))"` → routed when it prints `http://127.0.0.1:3001`.
- `codex login status` (or `codex --version` if that subcommand is missing) → the OpenAI side.

Report one of: **routed** (200 + setting present), **running but not routed** (200, setting absent),
**not running** (no 200), **not installed** (no toml). For "running but not routed" offer `on`.

## `setup`

Ask for a confirmation at each step; run nothing without it.

1. `command -v codex || npm i -g @openai/codex`, then `codex login` (the person completes the browser step).
   1b. The Codex plugin for Claude Code, if `claude plugin list | grep -q codex@openai-codex` fails: `/plugin marketplace add openai/codex-plugin-cc`, `/plugin install codex@openai-codex`, `/reload-plugins`, then `/codex:setup`. This gives the council `/codex:adversarial-review` and `/codex:review` as the OpenAI route that needs no gateway, and it is the fallback when shunt is down. Do not enable the plugin's review gate (`--enable-review-gate`): it loops Claude and Codex and drains limits.
1. `brew install pleaseai/tap/shunt`.
1. `mkdir -p ~/.config/shunt && cp "${CLAUDE_PLUGIN_ROOT}/framework/models/shunt.toml.example" ~/.config/shunt/shunt.toml` (skip if a toml exists; show a diff instead).
1. `shunt --config ~/.config/shunt/shunt.toml --check` (or `shunt check`) to validate the file, `brew services start shunt`, then the curl above must print 200. Note: shunt's README calls `[[routes]]` legacy and prefers `[[upstreams]]` + `[models.upstream_model]`; the shipped example still uses routes because they work with the brew build. Keep effort on each route (`gpt-6-astra` xhigh, `gpt-5.6-sol` medium), not on `[providers.codex]`.
1. Run `on` below.
1. Prove it: dispatch one tiny Agent with `model: gpt-6-astra` (the `council-adversary` agent, brief "reply with the model and vendor serving you in one line") and record what came back. Only a reply naming OpenAI counts as routed; write `host_routes.shunt: routed <date>` in `~/.claude/harness-profile.yml`.

## `on`

Write, with a Python one-liner that preserves everything else in the file, `env.ANTHROPIC_BASE_URL = "http://127.0.0.1:3001"` into `~/.claude/settings.json`. Claude Code applies `env` from the settings file
however it was launched (docs: env-vars, "In settings files"), so the Desktop Code tab picks it up too. Tell
the person two documented side effects of a non-first-party base URL: MCP tool search is off unless
`ENABLE_TOOL_SEARCH=true` is also set (set it, shunt forwards requests unchanged), and Remote Control is
disabled while routed. A running session applies the change on save; agents dispatched after that route.

## `off`

Remove `env.ANTHROPIC_BASE_URL` and `env.ENABLE_TOOL_SEARCH` from `~/.claude/settings.json` (a settings
file cannot unset, so removal takes effect at the next launch; say that), and offer `brew services stop shunt`. Use `off` when shunt is down and you need Anthropic-only sessions to work: with the setting present
and shunt stopped, every request fails, which is the one failure mode of routing from settings rather than
from the shell.

## Hard rules

- Never paste a token or key; both sides log in through their own browser flows.
- Never write `ANTHROPIC_BASE_URL` into a project `.claude/settings.json`; it is per person.
- Report `routed` only after step 6's reply names OpenAI. A 200 from curl proves the proxy, not the route.
