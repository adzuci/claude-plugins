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

## Plugin Inventory

See [SKILL_INVENTORY.md](SKILL_INVENTORY.md) for the full generated skill command inventory.

<!-- PLUGIN-INVENTORY-START -->

| Plugin | Description | Skills |
| --- | --- | ---: |
| `apollo-eng` | Shared engineering skills for Apollo repos | 14 |
| `apollo-eng-devops` | DevOps, SRE, and production reliability skills for Apollo engineers | 16 |
| `apollo-analytics` | Apollo Analytics Copilot — answers data questions using governed Snowflake metrics, runs product debriefs, generates account profiles, and surfaces weekly strategic insights. | 12 |
| `apollo-eng-leadership` | Cowork skills for engineering managers — OKR reporting, eng metrics, and planning | 6 |
| `apollo-gtm` | Go-to-market strategy, sales enablement, and demand generation | 5 |
| `apollo-it` | IT management, infrastructure, security, and support | 7 |
| `apollo-product` | Product management, roadmap, and lifecycle processes | 1 |
| `apollo-eng-fabric-surfaces` | Skills specific to the Fabric Surfaces team | 4 |
| `apollo-rnd` | Research and development skills for Apollo R&D | 2 |
| `apollo-gtm-systems` | Apollo's GTM Systems concierge. | 4 |
| `apollo-legal` | End-to-end contract review for Apollo's Commercial Legal team. | 3 |
| `apollo-people` | People Enablement skills for Apollo employees — performance reviews, career development, and growth tools | 5 |
| `apollo-marketing` | Apollo's internal brand copilot. | 1 |
| `apollo-gtm-enablement` | Creates facilitator-ready enablement decks for Apollo's GTM teams (Sales, CS, Product). | 2 |
| `apollo-risk` | Privacy and compliance skills for Apollo's Legal Risk team — DSR response drafting, privacy queue triage, and regulatory compliance workflows. | 1 |
| `apollo-corpsec` | Apollo IT CorpSec skills: device & managed-endpoint policy, external storage rules, a device-rules FAQ, and policy exception requests. | 4 |
| `apollo-talent` | Talent Acquisition skills for Apollo's TA team — company knowledge for candidate briefings and project planning tools for TA initiatives. | 2 |
| `apollo-procurement` | Procurement & Finance Operations assistant — answers questions about travel & expense (Navan), procurement intake (Zip), accounts payable, corporate cards (Ramp/Brex), and contracts (IronClad) by grounding every answer in the canonical FAQ. | 1 |
| `apollo-accounting` | Accounting and finance skills for Apollo's Finance team — contract clause analysis, ASC 606 revenue recognition assessment, and Ironclad contract review workflows. | 1 |

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
  workflows/  # CI: lint, validate, tests, bump-version, skill-pr-review, update-skill-inventory
  scripts/    # Helper scripts used by workflows (update-skill-inventory, bump_plugin_versions)
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

This repo uses [Conventional Commits](https://www.conventionalcommits.org/) to drive automatic semver tagging via `.github/workflows/bump-version.yml`. On every push to `main`:

1. Finds the latest `vMAJOR.MINOR.PATCH` tag
1. Scans commit subjects and bodies since that tag
1. Picks the highest-impact bump: **major** (`feat!:` / `BREAKING CHANGE`), **minor** (`feat:`), **patch** (`fix:` and other releasable types)
1. Skips tagging entirely for non-releasing types: `chore`, `docs`, `ci`, `style`, `test`
1. Pushes an annotated tag and creates a GitHub Release with auto-generated notes
1. Bumps the `version` in each changed plugin's Claude and Codex `plugin.json` using the same semver rules, based on the commits that touched that plugin (via `.github/scripts/bump_plugin_versions.py`)

Both the repo-wide tag and the per-plugin manifest versions are bumped automatically — you do not need to edit `plugin.json` versions by hand. The per-plugin bump is derived from scoped Conventional Commits, so commit with a plugin scope (e.g. `feat(apollo-people): ...`) and touch that plugin's files.

The README plugin inventory and `SKILL_INVENTORY.md` are auto-updated by CI on merge — do not edit them manually.

**Branch convention:** Feature branches use the format `<user>/<ticket>-description` (e.g. `adzuci/ABC-123-add-bump-version-workflow`) and are merged to `main` via pull request.

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
