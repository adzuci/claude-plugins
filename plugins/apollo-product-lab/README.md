# apollo-product-lab

The product-development harness: PM, design, architecture, engineering, QA and research lenses on different model families, deterministic stage snapshots, a council with a human decision record, and onboarding for every persona.

Not the same as `apollo-product` (product management, roadmap and lifecycle processes). This plugin runs the build harness: lenses, council and run records.

## Renamed

This plugin was formerly `apollo-product-harness` (and `apollo-eng-harness`). To move to the new name: uninstall the old one in the scope it was installed in (`claude plugin uninstall apollo-product-harness@apollo-plugins`, or `apollo-eng-harness@apollo-plugins`, adding `--scope project` or `--scope local` if it was installed there), refresh the marketplace (`claude plugin marketplace update apollo-plugins`), then `claude plugin install apollo-product-lab@apollo-plugins`.

## Quickstart

Never used the harness? Start with the six-step guide (Claude Code and Codex, while the PR is open): <https://app.notion.com/p/3e3ab2b3b49681ee86eefd10d1755937>

```
claude plugin install apollo-product-lab@apollo-plugins
cd <your product repo>      # leadgenie, or any repo with a .ai/ directory
claude
/apollo-product-lab:harness-onboard
```

Onboarding asks where you are running it, who you are, where stage updates go (Jira, Notion or both),
solo or team, which initiative, what size of work, which sources you need, and whether you have a second
model family. It sets up the MCP servers you ticked (the
plugin ships Notion, Atlassian, Slack, Glean, Figma, Claude Design, Sentry, Amplitude and Grafana in `.mcp.json`; each logs in on first use, and an uploaded plugin shows them as one-click connectors. Playwright is opt-in: `claude mcp add playwright -- npx -y @playwright/mcp@latest`),
offers optional px0 setup for code-review personas only after a real signed-off pin exists, writes
`~/.claude/harness-profile.yml`, and ends with the one command you run next. The shipped placeholder pin
means onboarding currently records px0 as unavailable and does not install it. A session started
without a profile prints a one-line reminder to run it.

Where it runs: every surface below (see Install By Surface). Where there is no working tree (claude.ai
chat, cloud sandboxes) the run record and your profile live in Notion in the same schema as the
`.ai/` files (`storage: notion`, `framework/45-web-mode-and-storage.md`). Earlier notes: Claude Code CLI and the Claude Desktop Code tab load it from the marketplace; claude.ai/code
and Desktop cloud sessions load it only when it is enabled on your claude.ai account (synced plugin);
Desktop Chat and Cowork cannot run it. Until #292 merges, add the marketplace at
`https://github.com/apolloio/claude-plugins.git#akansh/harness-split-1`, or for claude.ai/code build
`dist/apollo-product-lab.zip` with `scripts/package.py` (manifest at the archive root) and upload it under Customize → Plugins (no shunt there: the adversary runs on
Glean for PRD and design reviews with independence marked unknown, and same-family for code reviews, and the memo says so). Details in
`framework/35-run-on-any-host.md`. In team mode every skill that writes to `.ai/<initiative>/` pulls
before reading and pushes after writing through `scripts/record-sync.sh`, so nobody works from a stale
snapshot (doc 41).

Builds come out as small PRs: about 15 review files each, 30 at most, enforced by the review gate.
When an approved px0 pin is configured and a person opts in, a PR can get a local review link after
the current-head gate passes. One combined draft PR with the `Need_Preview_Env`
label deploys a preview for manual testing. It is never merged (framework doc 20 §8b, §8f, §8g).
Research and wide lookups go to sub-agents, nested at most 2 deep (doc 51).

| Skill | What it does |
|---|---|
| `harness-shunt` | set up, check, turn on or off the second model family (Codex plugin + shunt); installed by default at onboarding for every non-design persona; writes the route into your user settings so the Desktop Code tab is covered |
| `harness-onboard` | Where you run it (sets `storage: local \| notion`), persona (incl. end to end), Jira/Notion update tracker, solo/team, base model for your host, connectors actually connected, shunt, workbench, profile |
| `harness-intake` | One sentence of intent → the plan for your role: size, artifacts, mandatory role grill, checks, sources, first command |
| `product-harness-init` | Bootstrap an initiative (product) or a feature run inside one |
| `harness-snapshot` | Write or read the deterministic per-stage record; team sync rules |
| `harness-escape` | Learning loop: scan harness-stamped PRs and Notion pages for findings after a gate passed, let the initiative's maintainer adjudicate them, write the fix with a replay fixture (doc 43); runs its scan at the start of intake and snapshot read |
| `harness-council` | Product, UX, architecture, backend, QA, research and adversary lenses on different model families; memo; `decide` records the human choice |
| `design-diff` | Fabric Studio prototype vs production gap list with a state matrix |
| `artifact-audit` | Stage A: contradictions across PRD, estimate, register, design |
| `code-review` | Backend, frontend, security and db-perf reviewers plus a tech-lead synthesizer on a PR; writes `.harness/reviews/<pr>/<head_sha>.json` and triages every must-triage finding (fix, wont_fix or deferred with a reason) before a human is asked; delta review for new commits |
| `slice-fit` | Classify plan slices as agent-ownable / with review / human |

## Review gate

`scripts/pr-ready.py` and a `PreToolUse` hook stop a PR from being marked ready, getting a human reviewer or merging until the AI review ran on the current head and its findings are triaged. Modes `warn` (default, still requires triage) and `block`; see `framework/50-review-gate.md`. Add `.harness/` to the repo's `.gitignore`.

## Process checks

Four advisory scripts cover preview state, CI diagnosis, stacked branches and evidence in status reports:

```bash
python3 scripts/preview-status.py --pr 123
python3 scripts/ci-doctor.py --pr 123
python3 scripts/stack-sync.py --tip feature-top
python3 scripts/verify-claims.py report.md
```

They accept `--json` and use exit 0 for clear, 1 for needs action and 2 for an error. They install no
hooks and never push. See `framework/52-process-scripts.md`.

## Install By Surface

| Surface | Install | Storage | Not available there |
|---|---|---|---|
| Terminal (Claude Code CLI) | `claude plugin install apollo-product-lab@apollo-plugins` (before the PR merges: `/plugin marketplace add https://github.com/apolloio/claude-plugins.git#akansh/harness-split-1`, then install `apollo-product-lab@<that marketplace>`), then `/apollo-product-lab:harness-onboard` in the product repo | local `.ai/`, profile in `~/.claude/` | nothing |
| Claude Desktop, Code tab | same as the terminal (same engine and config), or upload `dist/apollo-product-lab.zip` under Customize → Plugins | local | Fabric Studio previews (use the CLI for those) |
| claude.ai/code (and Desktop cloud sessions) | build `dist/apollo-product-lab.zip` (below), upload it at claude.ai/code → Customize → Plugins → Upload, or enable the synced plugin on your account once it is on the marketplace; then `/apollo-product-lab:harness-onboard` and answer "claude.ai/code" | Notion record pages; profile on a private Notion page | shunt and the Codex plugin (adversary falls back to Glean or same-family, tagged), Fabric Studio previews, Playwright against VPN previews, docker |
| claude.ai chat | build `dist/skills/*.zip` (below), upload each under Settings → Capabilities → Skills with code execution on; connect Notion, Figma and Glean in Settings → Connectors; then say "onboard me to the harness" | Notion only | no Agent tool (lenses run in the thread, memo tagged `degraded`), no hooks, no git; `design-diff`, `harness-shunt`, `harness-escape` and `slice-fit` are not packaged for chat (`product-harness-init` is, and bootstraps the initiative in Notion) |

Build both packages from the repo root (only git-tracked or trackable files go in; nothing is written
outside `dist/`, which is ignored):

```bash
python3 plugins/apollo-product-lab/scripts/package.py            # dist/apollo-product-lab.zip and dist/skills/*.zip
python3 plugins/apollo-product-lab/scripts/package.py --only plugin
python3 plugins/apollo-product-lab/scripts/package.py --only skills
```

The plugin zip has `.claude-plugin/plugin.json` at the archive root and a `BUILD` file with the commit
(`-dirty` when the plugin folder had uncommitted changes). Each chat Skill zip is one folder with
`SKILL.md` (frontmatter reduced to `name` and `description`, plugin-root paths made relative), the
framework docs, the agent briefs and `scripts/storage.py`, `scripts/post-update.py` and
`scripts/grill-check.py`, and `scripts/verify-claims.py`. Moving a run from Notion back to a repo:
`scripts/storage.py from-notion <fetched page> --initiative <slug>` per record page (doc 45 §3.4).

## Updating a Zip Install

A plugin uploaded as a zip (Claude Desktop, claude.ai) does not update itself. Every session starts
with a line like `[apollo-product-lab 1.0.0 build 07d1aeb] ...`: the version and the commit it was built
from. To update:

1. Build the zip from the latest `akansh/harness-split-1` branch (`main` once merged), from the repo
   root, so the `BUILD` file records the commit:

   ```bash
   python3 plugins/apollo-product-lab/scripts/package.py --only plugin
   ```

2. In Claude Desktop or claude.ai/code, replace the uploaded plugin under Customize, Plugins. For
   claude.ai chat, re-upload the changed Skills from `dist/skills/`.

3. Restart Claude Desktop. The new version shows on the next session-start line.

The shipped `.mcp.json` lists only remote OAuth servers and holds no credential. Playwright is not in it
because it starts a local `npx` process with every session; add it only if you need it:
`claude mcp add playwright -- npx -y @playwright/mcp@latest`. Build zips from git as above so no
developer-local configuration rides along.

The hook and skills resolve the repo root first. Outside any git repo (for example Desktop with no
checkout) they run in no-repo mode and skip repo, git, gh and `.ai` steps. In a repo with no `.ai/` at
its root they say the harness is not initialised there, and intake can bootstrap it.

Agents: `product-orchestrator` (router), `council-adversary` and `council-synthesizer` (OpenAI gpt-6-astra
through shunt), `slice-contract-keeper`, `slice-integrator`, `product-reviewer`.

The framework itself (docs 12–53, platform rules, model registry, templates, ledger tooling, reviews) is under
`framework/`; the index is `framework/index.md`. Product artifacts never live here: they live in the
product repo under `.ai/<initiative>/` (framework doc 41).

Reference instance: Apollo Ads Audience Sync M1 in `apolloio/leadgenie` (`.ai/ads-builder/`).
