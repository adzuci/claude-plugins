# 39 — Connectors and tools the harness uses, by persona, with setup

> One catalog. `harness-onboard` reads it to check what a person has and to tell them exactly what
> to set up. A connector is **present** when its tools appear in the Claude Code tool list,
> **installed but unauthenticated** when only its `authenticate` tool appears, **absent** otherwise.
> Secrets never go in chat or in the repo; every login happens in the person's own browser or shell.

| Connector / tool | Kind | What the harness uses it for | Personas | Setup (once) |
|---|---|---|---|---|
| **Claude Code** | host | runs agents, skills, hooks | all | `claude` in `apolloio/leadgenie`; `.claude/setup-env.sh` runs on session start |
| **Codex CLI** | host / model | `gpt-6-astra` reviews natively; Codex view of agents (doc 35) | engineer, EM | `codex login` (ChatGPT subscription); `codex plugin marketplace add apolloio/claude-plugins` |
| **shunt** (`/harness-shunt setup\|status\|on\|off`; **installed by default** for every non-design persona) | model gateway | routes `gpt-6-astra` only (Gemini is Glean-only, DeepSeek has no lane; doc 37 §3), into Claude Code agents | engineer, EM, anyone running the council | `brew install pleaseai/tap/shunt` (or per README), copy `models/shunt.toml.example` to `~/.config/shunt/shunt.toml`, `brew services start shunt`, `export ANTHROPIC_BASE_URL=http://127.0.0.1:3001` in the shell that launches Claude Code |
| **Fabric Studio** | design workbench | prototypes on `prototype/{you}-{initiative}`, deployed previews, the Design source block | designer, PM, frontend engineer | Apollo VPN; Node 22; run `/apollo-rnd:setup-fabric-studio` (marketplace, installs Node 22, gh, clone) or clone `https://github.com/apolloio/fabric-studio.git` and follow the README paste-in prompt |
| **Claude Design** (workbench option) | MCP `claude-design` | alternative design workbench when a designer prefers it; no code diff | designer | shipped in the plugin's `.mcp.json` (`https://api.anthropic.com/v1/design/mcp`); was `claude mcp add --transport http claude-design https://api.anthropic.com/v1/design/mcp`; record `design_workbench: claude-design` in the profile |
| **Figma** | MCP | read components/tokens first; write survivors back; Code Connect | designer, frontend engineer | shipped in the plugin's `.mcp.json` (`https://mcp.figma.com/mcp`); OAuth on first call |
| **Notion** (connector) | MCP | PRDs, ERD and case-study mirrors, decision pages | PM, EM, designer, engineer | shipped in the plugin's `.mcp.json` (`https://mcp.notion.com/mcp`); login on first call; or `claude mcp add --transport http notion https://mcp.notion.com/mcp` |
| **Glean** | MCP | internal-record corroboration (`search`, `chat`), people, docs; Glean-backed model lane | all | shipped in the plugin's `.mcp.json` (`https://apollo-io-be.glean.com/mcp/default`); login on first call |
| **Atlassian** (Jira/Confluence) | MCP | tickets (WO project), epics, Confluence specs, stage updates | anyone whose tracker is Jira or both | shipped in the plugin's `.mcp.json` (`https://mcp.atlassian.com/v1/mcp`); OAuth on first `atlassianUserInfo` call, or `claude mcp add --transport http atlassian https://mcp.atlassian.com/v1/mcp` |
| **Slack** | MCP | design threads, incident channels, stakeholder updates | all | shipped in the plugin's `.mcp.json` (`https://mcp.slack.com/mcp`, Slack's official server, Streamable HTTP, OAuth; the Claude Code app is already workspace-approved) |
| **Amplitude** | MCP | success metrics with numbers (Stage C), funnels, experiment analysis | PM, analytics | shipped in the plugin's `.mcp.json` (`https://mcp.amplitude.com/mcp`); Apollo's claude.ai connector is the same server, disable one copy; `get_amplitude_context` first |
| **Enterpret** | MCP | voice-of-customer evidence for FIND and the product lens | PM, researcher | claude.ai connector (needs auth) |
| **Sentry** | MCP | error evidence for FIND, VERIFY, on-call routing | engineer, QA, EM | shipped in the plugin's `.mcp.json` (`https://mcp.sentry.dev/mcp/apolloio`, OAuth); narrow to `/apolloio/<project>` for one surface |
| **Grafana** | MCP | dashboards, Prometheus/Loki for BUILD operability and VERIFY | engineer, SRE | shipped in the plugin's `.mcp.json` (`https://grafana-mcp.ops-gcp.apollo.io/mcp`) |
| **Playwright** | MCP | runtime verification against the preview; screenshots for design checks | QA, engineer, designer | opt-in, not in `.mcp.json` because it starts a local process every session: `claude mcp add playwright -- npx -y @playwright/mcp@latest` |
| **GitHub CLI** | CLI | PRs, checks, reruns, run logs | engineer, QA | `gh auth login` |
| **px0** | CLI, local, opt-in | Review each harness PR in the browser, in its own worktree (doc 20 §8f) | engineer, QA, EM, end to end (+ code-writing designers / researchers), **opt-in** | **Opt-in, Security sign-off before first use** (#security-requests). Prefer `brew install px0` for both install and update; otherwise fetch and verify the pinned installer from `framework/models/px0-pin.yml` (fail on checksum mismatch), then `px0 -version`. For a Homebrew install, update with `brew upgrade px0`. For a pinned install, update by bumping `framework/models/px0-pin.yml` and re-running the verified fetch — never `px0 --update` on its own, and never the unpinned `curl ... \| sh` form. |
| **Docker (rails container)** | local | rspec, rubocop, `srb tc`, tapioca | engineer | `docker compose up`; run `srb tc` and `bin/rspec` sequentially (memory) |
| **Snowflake / Windmill / Intercom / Gong** | MCP | optional evidence sources (revenue, people, support, calls) | PM, EM | claude.ai connectors as needed |

Atlassian is required whenever `updates.tracker` is `jira` or `both`, regardless of persona. If the
harmless confirmation call fails, onboarding shows the setup above, records `tracker_blocked: jira`, and
uses Notion for updates until the connector is confirmed.

## Design tools from a claude.ai/code (cloud) session

The cloud sandbox has no VPN, no Node 22 checkout of Fabric Studio, and no local Storybook, so the design
loop is split between what the sandbox can do and what stays on a laptop.

| Tool | From claude.ai/code | What still needs a laptop |
|---|---|---|
| **Claude Design** | works as is: the `claude-design` MCP is a claude.ai service, so `design_workbench: claude-design` is the natural choice for a designer who lives in the browser. `design-diff` reads the exported files it writes to the project | nothing |
| **Figma** | works as is through the claude.ai Figma connector (read frames, tokens, comments; Code Connect) | nothing |
| **Fabric Studio** | the repository is public to the org on GitHub, so the sandbox can clone `apolloio/fabric-studio`, check out `prototype/<you>-<initiative>`, and run `design-diff` on the source (routes, components, copy, imports); `inventory.py` needs only the two checkouts. The deployed preview (`*.staging.apollo-forge.io`) is behind the Apollo VPN, so Playwright cannot open it from the sandbox | opening the preview or the Storyboard in a browser, in-studio comments, pushing prototype changes; and `/apollo-rnd:setup-fabric-studio` (Node 22, VPN) |
| **Storybook** (leadgenie) | `pnpm storybook` runs inside the sandbox against the cloned repo, and the Playwright MCP (opt-in, added as in the table above) can screenshot `http://localhost:6006` there, so the design check of a built component works | nothing, once the sandbox has finished `pnpm install` |
| **Preview environment** (`Need_Preview_Env`) | the preview URL is VPN-only, so the Verify stage's Playwright run against it does not work from the sandbox | run `harness-snapshot write G.verify` from a laptop, or accept `unverified` on the runtime rows and say so in the memo |

`harness-onboard` asks where you are running (question 0); on a cloud host it records `host: claude-code-cloud`
and `storage: notion`, writes the profile to a private Notion page, skips the shunt and Fabric Studio
walkthroughs, and says which stages need a laptop. On claude.ai chat the same skills run from uploaded
Skills with Notion as the only store (doc 45).

## Data-handling reminders the onboarding repeats

- Anthropic and OpenAI (via Codex) are approved for code and design review in this repo. Anything
  else, or any new *use case* (customer data, constraint registers), needs the use-case approval in
  doc 13 §4 before it is routed. DeepSeek is a new vendor: approval first.
- Tokens, API keys, OAuth callbacks: set in the shell or the rails container or GSM, never pasted in
  chat, never committed. `.env` and `docker-compose.override.yml` are gitignored.

## The second model family (shunt) is part of onboarding, not optional reading

Onboarding detects shunt and, when the person can use a second family, walks these in order and confirms each:

```
codex login                                   # once; ChatGPT/Codex subscription
brew install pleaseai/tap/shunt
cp ${CLAUDE_PLUGIN_ROOT}/framework/models/shunt.toml.example ~/.config/shunt/shunt.toml
brew services start shunt
curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3001/      # 200
export ANTHROPIC_BASE_URL=http://127.0.0.1:3001                    # in the shell that launches claude
```

The session-start hook reports three states: shunt not installed, shunt running but this session not routed
(`ANTHROPIC_BASE_URL` unset), or routed. Without shunt the council runs single-family and says so.

## MCP servers the plugin ships

`.mcp.json` in the plugin configures Notion, Atlassian, Slack, Glean, Figma, Claude Design, Sentry, Amplitude and Grafana with their standard endpoints (Playwright is opt-in, see its row); each asks for your own login on first call and holds no credential, and in an uploaded or synced plugin they appear under the plugin's Connectors as one-click connects. Enterpret, Intercom, Gong, Snowflake and Google Drive stay claude.ai connectors (no public endpoint or org-internal). If you already had one of the shipped servers configured, disable one copy; `/harness-onboard` flags duplicates.

## Plugins the harness expects installed

| Plugin | Why | Install |
|---|---|---|
| `apollo-product-lab@apollo-plugins` | the harness itself: skills, agents, framework docs (doc 41) | `claude plugin install apollo-product-lab@apollo-plugins` after apolloio/claude-plugins#292 merges; before that, add the marketplace at `#akansh/harness-split-1` (doc 35 "Where the plugin loads"). Cloud and Desktop-cloud sessions need the plugin enabled on your claude.ai account instead; Desktop Chat and Cowork cannot run it |
| `apollo-eng@apollo-plugins` | `mongo-pr-guard`, `plan-from-jira`, `rca-doc-review` | installed (settings.json) |
| `codex@openai-codex` | `/codex:review`, `/codex:adversarial-review`, `codex-rescue` — the second family without shunt; **installed by default** for every non-design persona (onboarding q6) | `/plugin marketplace add openai/codex-plugin-cc` → `/plugin install codex@openai-codex` → `/reload-plugins` → `/codex:setup`; never enable its review gate |
| `apollo-rnd@apollo-plugins` | `prd-one-pager` (PM), `setup-fabric-studio` (designer) | installed 2026-09-19 (`claude plugin install apollo-rnd@apollo-plugins`) |
| `apollo-eng-experimentation@apollo-plugins` | Stage G experiment metrics | installed 2026-09-19 |
| `apollo-analytics@apollo-plugins` | governed metrics for the research lens (needs the Jarvis MCP) | `/plugin install apollo-analytics@apollo-plugins` |

Which skill each stage may call is in [38-skill-reuse-map.md](./38-skill-reuse-map.md).
