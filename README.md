# Apollo Skills Marketplace

Apollo's private Claude Code and Codex skills marketplace for building, versioning, and distributing shared workflows across Apollo.

The marketplace is installed by default for all Apollo Claude users and available via `/plugin` in the CLI or `+` -> **Plugins** -> **Add Plugins** in Claude Desktop. Codex pilot users can add the marketplace by running:

```bash
codex plugin marketplace add apolloio/claude-plugins
```

**Questions?** Ask `#ai-native-learning` for general plugin questions, `#xfn-h-agentic-engineering` for engineering plugin content, and `#it-help-desk` for company-wide plugin access.

Marketplace metadata lives in `.claude-plugin/marketplace.json` for Claude Code and `.agents/plugins/marketplace.json` for Codex. Every marketplace change goes through PR review, CI validation, and version control before it reaches users.

## Plugin Components

| Component | Directory | What it does |
| --- | --- | --- |
| Skills | `skills/<name>/SKILL.md` | Reusable workflow instructions invoked directly as `/plugin:skill-name` or triggered by a matching request. |
| Agents | `agents/<name>.md` | Domain-specific subagents with their own instructions and tool restrictions. |
| Hooks | `hooks/hooks.json` | Commands wired to lifecycle events such as `PreToolUse`, `PostToolUse`, or `Stop`. |
| MCP Servers | `.mcp.json` | Tool connections to external systems such as Jira, Notion, GitHub, or databases. |
| Commands | `commands/<name>.md` | Legacy slash-command files. Use `skills/` for new work. |

## Plugin Structure

Most plugins follow this shape; optional folders appear only when needed.

```text
plugins/apollo-eng/
├── .claude-plugin/
│ └── plugin.json # Claude Code manifest: name, description, version
├── .codex-plugin/
│ └── plugin.json # Codex manifest: name, description, version, skills path
├── skills/
│ ├── pr-description/
│ │ └── SKILL.md
│ └── security-review/
│ └── SKILL.md
├── agents/ # Optional
├── hooks/ # Optional
└── .mcp.json # Optional
```

`skills/`, `agents/`, `hooks/`, `commands/`, and `.mcp.json` live at the plugin root. Only `plugin.json` goes inside `.claude-plugin/` and `.codex-plugin/`.

Inside a skill, keep agent-readable prose in `SKILL.md` or `references/`. A skill may also
use `evals/` for machine-executed evaluation fixtures and runner configuration; do not put
runbooks or other prose-only support files there.

## Plugin Inventory

See [SKILL_INVENTORY.md](SKILL_INVENTORY.md) for the full generated skill command inventory.

Weekly OKR update: `/apollo-eng-leadership:okr-report --weekly <team>` (for example `--weekly devops` or `--weekly design-system`) drafts the team's weekly thread reply as a Slack draft for you to review. Add a team by copying `plugins/apollo-eng-leadership/skills/okr-report/references/weekly-teams/_template.md` and listing it in `plugins/apollo-eng-leadership/skills/okr-report/references/weekly-teams.md`.

<!-- PLUGIN-INVENTORY-START -->

| Plugin | Description | Skills |
| --- | --- | ---: |
| `apollo-eng` | Shared engineering skills for Apollo repos | 34 |
| `apollo-eng-devops` | DevOps, SRE, and production reliability skills for Apollo engineers | 37 |
| `apollo-analytics` | Apollo Analytics Copilot — answers data questions using governed Snowflake metrics, runs product debriefs, generates account profiles, and surfaces weekly strategic insights. | 11 |
| `apollo-eng-fraud` | Fraud/abuse-ring investigation skills for Apollo engineering — track blocked-domain abuse rings over time and identify+block new ones with an evidence-backed PR proposal. | 2 |
| `apollo-eng-leadership` | Cowork skills for engineering leadership and customer-care rotation support | 9 |
| `apollo-gtm` | Go-to-market strategy, sales enablement, and demand generation | 11 |
| `apollo-it` | IT management, infrastructure, security, and support | 7 |
| `apollo-support` | Support and Customer Care skills for KB maintenance, customer escalations, and support operations | 3 |
| `apollo-product` | Product management, roadmap, and lifecycle processes | 1 |
| `apollo-eng-fabric-surfaces` | Skills specific to the Fabric Surfaces team | 4 |
| `apollo-rnd` | Research and development skills for Apollo R&D | 3 |
| `apollo-gtm-systems` | Apollo's GTM Systems concierge. | 4 |
| `apollo-legal` | End-to-end contract review for Apollo's Commercial Legal team. | 4 |
| `apollo-people` | People Enablement skills for Apollo employees — performance reviews, career development, and growth tools | 8 |
| `apollo-marketing` | Apollo's internal brand copilot. | 1 |
| `apollo-gtm-enablement` | Creates facilitator-ready enablement decks for Apollo's GTM teams (Sales, CS, Product). | 2 |
| `apollo-risk` | Privacy and compliance skills for Apollo's Legal Risk team — DSR response drafting, privacy queue triage, and regulatory compliance workflows. | 1 |
| `apollo-corpsec` | Apollo IT CorpSec skills: device & managed-endpoint policy, external storage rules, a device-rules FAQ, and policy exception requests. | 4 |
| `apollo-infosec` | Information security skills for Apollo's InfoSec team — security incident response, data exposure investigation, and verifying whether leaked or claimed-stolen data is real, plus secure-coding guidance for all Apollo engineers and builders. | 5 |
| `apollo-talent` | Talent Acquisition skills for Apollo's TA team — company knowledge for candidate briefings and project planning tools for TA initiatives. | 2 |
| `apollo-procurement` | Procurement & Finance Operations assistant — answers questions about travel & expense (Navan), procurement intake (Zip), accounts payable, corporate cards (Ramp/Brex), and contracts (IronClad) by grounding every answer in the canonical FAQ. | 1 |
| `apollo-accounting` | Accounting and finance skills for Apollo's Finance team — contract clause analysis, ASC 606 revenue recognition assessment, and Ironclad contract review workflows. | 1 |
| `apollo-eng-agentic-engineering` | Agentic Engineering team skills | 2 |
| `apollo-eng-experimentation` | Amplitude experiment lifecycle skills for the leadgenie codebase: create, measure, and clean up A/B experiments | 8 |
| `apollo-growth` | Idea capture, brainstorm batching, weekly funnel reporting, and tooling to generalize a personal skill for sharing | 4 |
| `apollo-growth-product` | Growth product workflows: experiment pitch, design, tracking and results, in-product copy, Jira tickets, and business review reporting | 9 |
| `ai-overage-admins` | Skills for admins managing engineers' Claude and Codex monthly spend limits | 1 |
| `herald` | GTM launch package builder: kickoff, brief, positioning, and paid, content, social, and lifecycle artifacts for Apollo PLG launches, scaled by launch tier | 7 |
| `apollo-product-lab` | Product-development harness: multi-lens council on different model families, deterministic stage snapshots, onboarding per persona. | 11 |

<!-- PLUGIN-INVENTORY-END -->

## Skill Scope

Store skills by scope:

1. **This central marketplace** — workflows any Apollo engineer should be able to install. Skills here go through code review, CI, and versioning.

1. **Repo-specific skill folders** — skills only relevant to a specific codebase. Examples:

   - [`apolloio/devops/.claude/skills`](https://github.com/apolloio/devops/tree/master/.claude/skills)
   - [`apolloio/leadgenie/.claude/skills`](https://github.com/apolloio/leadgenie/tree/master/.claude/skills)

1. **`~/.claude/skills`** — personal workflows not meant to be shared.

If you'd use a skill in more than one repo, put it here. If it is codebase-specific, keep it in that repo. If it is personal or experimental, keep it local.

## Making Plugins

Use the repo-local `/add-plugin` skill to create a new top-level plugin from `template/`. The skill owns the detailed steps for copying templates, updating both Claude and Codex manifests, registering both marketplace files, keeping ordering aligned, formatting, and validation.

Use `/remove-plugin` when retiring a plugin so marketplace entries, references, owner communication, and validation are handled together.

## Adding Skills To Plugins

Use the repo-local `/add-skill` skill when adding or updating a skill in an existing plugin. It wraps general `/skill-creator` guidance and adds Apollo-specific checks for frontmatter, direct-only invocation, validation, review readiness, and token efficiency.

Use `/test-skill` when a skill includes scripts or tests. It keeps pytest layout, dependency installation, targeted runs, and marketplace validation consistent.

Use `/remove-skill` when retiring a skill so references, default-install risk, and validation are checked before deletion.

You can also create or edit skills manually:

- Copy `template/skills/example` to `plugins/<plugin-name>/skills/<skill-name>`.

- Set frontmatter `name` to match the skill directory exactly.

- Default to `disable-model-invocation: true` unless natural-language activation is intentional.

- Keep `SKILL.md` concise; put large examples, policies, and scripts in bundled files.

- Run before committing:

  ```bash
  mdformat plugins/<plugin-name>/skills/<skill-name>/SKILL.md
  claude plugin validate .
  python -m pytest tests/test_marketplace.py -q
  ```

  If Codex is installed and exposes plugin validation, also run `codex plugin validate .`; otherwise note that Codex validation was unavailable.

### Configurable Skills

Some skills can't ship with working defaults because they point at one team's Notion databases, Jira projects, or Slack channels. Those skills use a `config.md` sidecar so the same skill works for every team.

A configurable skill has three parts:

- `SKILL.md` with `requires_config: true` in its frontmatter, a `## Configuration` section directly after the frontmatter, and `{{variable_name}}` placeholders wherever a team-specific value belongs.
- `config.md` with a YAML frontmatter block holding every variable, `<UNSET>` for anything the installer must supply, and a Setup Guide below it documenting each one in plain language.
- Optional `references/` files bundled with the skill so it works out of the box, such as a voice guide or a style rubric.

Answers are saved to `~/.claude/plugin-config/<plugin>/<skill>.md`, not back into `config.md`. The shipped `config.md` is replaced whenever the plugin updates, so answers written there would be lost and the installer would be re-asked everything after every release.

On first use the skill reads `config.md` for defaults, layers your saved answers over it, asks for anything still `<UNSET>`, and writes those answers to the user-owned file. An empty string is a real answer meaning "intentionally blank", so the skill won't keep asking about keys you left empty on purpose.

When you write one:

- Extract values an installer would **fill in** (a database ID, a project key, a channel). Leave values they'd **change their mind about** (a word limit, a formatting rule) as literals, since those are the skill's opinion and part of what makes it useful.
- Write each Setup Guide entry for a stranger. Say what the value is, where to find it, and what happens when it's empty.
- Give every placeholder a matching key. A `{{placeholder}}` with no config entry is a bug.
- Don't put secrets in config. Both the shipped `config.md` and the saved answers under `~/.claude/plugin-config/` are plain text with no secret handling.
- Never instruct a skill to write answers into its own `config.md`. That file belongs to the plugin, not the user.

`/apollo-growth:skill-generalizer` automates most of this when you are converting an existing personal skill. It scans a skill folder for hardcoded values, walks you through which to extract, and writes the generalized skill, its `config.md`, and an installer README.

### Reviewing Prompts

Run `/apollo-eng:prompt-review path/to/prompt.md` for a local advisory review.
See the [skill and runnable example](plugins/apollo-eng/skills/prompt-review/SKILL.md).

### Testing Skill Scripts

Skills with Python in `scripts/` should have pytest tests in a sibling `tests/` directory. Use `/test-skill` for the detailed workflow. CI runs `python -m pytest -q` against Python 3.9 and 3.11.

```bash
pip install -r tests/requirements.txt
python -m pytest tests/test_marketplace.py -q
python -m pytest plugins/<plugin>/skills/<skill>/tests -q
```

`tests/test_marketplace.py` also checks marketplace parity, plugin manifests, Codex metadata, skill frontmatter, and cross-plugin skill name uniqueness.

## FAQ

1. **When should I use `CLAUDE.md` or `AGENTS.md` instead of a skill?**
   Use repo instructions to nudge Claude Code or Codex toward the right installed skill. Put reusable workflow steps in the skill itself.

1. **How do I keep skills from taking up too much context?**
   Default to `disable-model-invocation: true`, keep `description` concise, keep `SKILL.md` focused, and move details into bundled files.

1. **How can I learn more about lifecycle management at Apollo?**
   Read [Claude Skills & Plugins v2: Lifecycle Management at Apollo.io](https://app.notion.com/p/apolloio/Claude-Skills-Plugins-v2-Lifecycle-Management-at-Apollo-io-365ab2b3b49681b1b019fbad2da22baa).

## Naming Conventions

Plugins follow the pattern `apollo-<dept>` or `apollo-<dept>-<team-or-topic>`:

| Pattern | Example | When to use |
| --- | --- | --- |
| `apollo-<dept>` | `apollo-eng` | Skills useful across an entire department |
| `apollo-<dept>-<team-or-topic>` | `apollo-eng-devops`, `apollo-eng-leadership` | Skills specific to one team, function, or topic within a department |

Skill names are lowercase, hyphenated, and describe the action: `pr-description`, `incident-response`, `bug-bash-generator`.

Users invoke skills as `/plugin-name:skill-name` (e.g. `/apollo-eng:pr-description`).

## Suggesting This Marketplace From Other Repos

To have Claude Code suggest this marketplace when someone works in another repo, add this to that repo's `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "apollo-plugins": {
      "source": {
        "source": "github",
        "repo": "apolloio/claude-plugins"
      }
    }
  }
}
```

To auto-enable specific plugins in that repo:

```json
{
  "enabledPlugins": {
    "apollo-eng@apollo-plugins": true
  }
}
```

### Auto-Update

This marketplace uses `"autoUpdate": true` so users with the installed marketplace get the latest skills automatically without running `claude plugin update`. Any commit merged to `main` can take effect on consumer machines at next sync, so branch protection, required reviews, and CI validation on `main` are load-bearing controls.

See [Claude Code plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces) for the full schema.

## Managing Plugins in Claude Enterprise

Claude Enterprise owners manage organization plugins in Claude admin settings. Some plugins are installed by default or required for certain groups. To request default installation for a plugin, ask `#it-help-desk`. See the [official Claude plugin management docs](https://support.claude.com/en/articles/13837433-manage-plugins-for-your-organization).

## Repository Structure

```text
.claude/
  settings.json
.claude-plugin/
  marketplace.json
.agents/
  plugins/
    marketplace.json
.github/
  workflows/  # CI: lint, validate, tests, release-please, skill-pr-review, update-skill-inventory
  scripts/    # Helper scripts used by workflows, such as update-skill-inventory
skill-review-rubric.md
template/
  .claude-plugin/
    plugin.json
  .codex-plugin/
    plugin.json
  skills/
    example/
      SKILL.md
plugins/
  apollo-eng/  # Shared engineering skills
    .claude-plugin/
      plugin.json
    .codex-plugin/
      plugin.json
    skills/
      pr-description/
        SKILL.md
  apollo-eng-devops/  # DevOps and SRE skills
    ...
  apollo-it/  # IT skills
    ...
```

## Versioning and Releases

This repo uses [Release Please](https://github.com/googleapis/release-please-action) and [Conventional Commits](https://www.conventionalcommits.org/) to bump plugin versions via `.github/workflows/release-please.yml`. On every push to `main`:

1. Release Please scans commits for each package listed in `release-please-config.json`
1. Creates or updates release PRs with changelogs and version bumps
1. Bumps both Claude and Codex plugin manifests through `extra-files`
1. Creates tags and GitHub Releases when release PRs are merged

Do not edit `plugin.json` versions by hand. Commit with a plugin scope (for example, `feat(apollo-people): ...`) and touch that plugin's files so Release Please can attribute the change.

**Give the pull request a Conventional Commit title as well.** Pull requests are squash-merged, so a PR with more than one commit lands on `main` under its PR title. A title like `Update-skill.md` gives Release Please nothing to parse and the plugin version is never bumped.

The README plugin inventory and `SKILL_INVENTORY.md` are auto-updated by CI on merge — do not edit them manually.

**Branch convention:** Feature branches use the format `<user>/<ticket>-description` (e.g. `adzuci/ABC-123-add-bump-version-workflow`) and are merged to `main` via pull request.

## Stale Pull Request Cleanup

The daily `Clean Up Stale Pull Requests` workflow calls the [reusable stale PR cleanup workflow](https://github.com/apolloio/.github/blob/main/.github/workflows/cleanup-stale-pull-requests-reusable.yml) in `apolloio/.github`, modeled on [leadgenie's cleanup](https://github.com/apolloio/leadgenie/blob/master/.github/workflows/cleanup-stale-branches.yml). It deletes same-repository branches after both the pull request and branch have been inactive long enough; deleting the branch closes its pull request.

- Ready pull requests: 10 days
- Draft pull requests: 30 days
- Pull requests labeled `flaky-test-fix`: 35 days
- Pull requests labeled `keep-open`: never automatically closed

Scheduled runs are dry-runs until the repository variable `STALE_PR_AUTOCLOSE_ENABLED` is set to `true`. Review the workflow summary, label long-running work `keep-open`, then enable the variable. Manual runs default to dry-run and can opt into deletion. Each run deletes at most 10 branches.

## References

- [Claude Code plugin docs](https://code.claude.com/docs/en/plugins) — official plugin creation guide
- [Claude Code marketplace docs](https://code.claude.com/docs/en/plugin-marketplaces) — private marketplace setup
- [Codex plugin docs](https://developers.openai.com/codex/plugins) — official Codex plugin guide
- [Codex plugin build docs](https://developers.openai.com/codex/plugins/build) — Codex plugin and marketplace setup
- [Agent Skills specification](https://agentskills.io/specification) — format and conventions for skill files

## Proposed Roadmap

- Codex company-wide marketplace rollout.
- Deprecation automation for retiring plugins and skills before deletion.
- [Skill and plugin lifecycle management](https://app.notion.com/p/apolloio/Claude-Skills-Plugins-v2-Lifecycle-Management-at-Apollo-io-365ab2b3b49681b1b019fbad2da22baa), including evaluation before broad installation.
