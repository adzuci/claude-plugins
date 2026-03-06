# skills

This repo is a place to add [skills and plugins](https://code.claude.com/docs/en/plugins) for Claude Code. We may host it as a [private plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces#private-repositories) so teams can install and use these plugins across multiple repos.

**Note:** This repo is currently an experiment used to explore how we could potentially use plugins for [Claudathon — Build Claude Commands & Skills](https://www.notion.so/apolloio/Claudathon-Build-Claude-Commands-Skills-312ab2b3b4968076b5a7e32f8d8ef76f?source=copy_link).

## Where do skills go at Apollo?

There are three places you can store Claude skills depending on your use case:

1. **In our central skill repository** — This location is yet to be determined but could be in [the claude-bootstrapper repo](https://github.com/apolloio/claude-bootstrapper/tree/main/skills) or this repo; this repo can be used as a [private marketplace](https://code.claude.com/docs/en/plugin-marketplaces#private-repositories) so they’re available across Apollo.

1. **In repo-specific skill folders** — If a skill is only relevant to a specific repository, place it in that repo's `.claude/skills` directory. Examples:

   - [`apolloio/devops/.claude/skills`](https://github.com/apolloio/devops/tree/master/.claude/skills)
   - [`apolloio/leadgenie/.claude/skills`](https://github.com/apolloio/leadgenie/tree/master/.claude/skills)

1. **In `~/.claude/skills`** — For personal skills that are specific to your local development environment and not meant to be shared.

## Skills

<!-- SKILL-INVENTORY-START -->

| Plugin | Command | Description |
| --- | --- | --- |
| apollo-eng | `/apollo-eng:bug-bash-generator` | Generate bug bash test cases from a Notion bug bash page and write them to a Notion test case database. Activate when user asks to generate bug bash test cases, create bug bash tests, or mentions bug bash generation. |
| apollo-eng | `/apollo-eng:learn-from-chat` | Review the current conversation to identify user corrections, preferences, and patterns, then save them to Claude Code memory. Activate when the user says "learn from this chat", "learn from chat", "what did you learn", or "update your memory from this conversation". |
| apollo-eng | `/apollo-eng:plan-from-jira` | Fetches a Jira ticket using the Jira MCP, analyzes the requirements, and generates a structured implementation plan. Activate when the user provides a Jira issue key and asks to plan or implement it, says "plan from jira", "plan this ticket", or "create a plan for <TICKET-ID>". |
| apollo-eng | `/apollo-eng:pr-description` | Generate a clear PR title and description from the current branch's changes. Use when the user asks to fill the PR template, generate a PR description, prepare a PR, create a pull request, or before running gh pr create. |
| apollo-eng | `/apollo-eng:product-ship-post` | Generate product ship room posts for Slack announcements. Activate when user asks to write a ship post, product ship room post, release notes, or feature launch announcement. |
| apollo-eng | `/apollo-eng:security-review` | Perform security audit of Ruby controllers for IDOR vulnerabilities. Activate when user asks for security review, IDOR check, or authorization audit. |

<!-- SKILL-INVENTORY-END -->

## Repository Structure

```text
.claude/
    settings.json
.claude-plugin/
    marketplace.json
template/
    .claude-plugin/
        plugin.json
    skills/
        example/
            SKILL.md
plugins/
    apollo-eng/
        .claude-plugin/
            plugin.json
        skills/
            pr-description/
                SKILL.md
```

## How to use in Claude Code

**When you work in this repo:** `.claude/settings.json` is configured so the **apollo-skills** marketplace is offered and **apollo-eng** is enabled for this project. The first time you open the repo, Claude Code may prompt you to add the marketplace; after you install the plugin once, it stays enabled here.

1. **Add the marketplace** (one-time, in Claude Code):

   ```text
   /plugin marketplace add git@github.com:apolloio/skills
   ```

1. **Install a plugin**

   - From the UI: **Browse and install plugins** → **apollo-skills** → **apollo-eng** → Install now
   - Or run: `/plugin install apollo-eng@apollo-skills`

1. **Use a skill**
   Mention it in chat (e.g. “Use the pr-description skill to generate a PR description”) or run a command: `/apollo-eng:pr-description`

Skills from this marketplace can also be used in Claude.ai and the API when those products support plugin marketplaces.

## Adding a new skill

1. **Copy the skill template**
   Copy `template/skills/example/SKILL.md` to your plugin’s skills folder:

   ```text
   plugins/<plugin-name>/skills/<skill-name>/SKILL.md
   ```

   Example: `plugins/apollo-eng/skills/my-skill/SKILL.md`.

1. **Set frontmatter**
   In the YAML at the top of `SKILL.md`:

   - **name**: Lowercase, hyphenated (e.g. `my-skill`). This is the skill name users invoke.
   - **description**: One line describing *what* the skill does and *when* Claude should use it (include trigger terms so the agent can discover it).

1. **Write the body**
   Replace the placeholder with real instructions. You can add optional supporting files (e.g. `reference.md`, scripts) in the same skill directory.

1. **If the skill lives in a new plugin**
   Copy the whole `template/` folder to `plugins/<pack-name>/`, then follow “Adding a new plugin” below and register the plugin in `.claude-plugin/marketplace.json`.

## Adding a new plugin

If you need a new plugin (e.g. a separate pack for product or infra):

1. **Copy the template**
   Copy the `template/` folder to `plugins/<pack-name>/` (e.g. `plugins/apollo-product-pack/`).

1. **Edit the plugin manifest**
   In `plugins/<pack-name>/.claude-plugin/plugin.json`, set `name`, `description`, and `version`.

1. **Register in the marketplace**
   In `.claude-plugin/marketplace.json`, add an entry to the `plugins` array:

   ```json
   {
     "name": "<pack-name>",
     "source": "./plugins/<pack-name>",
     "description": "Short description of the pack"
   }
   ```

1. **Validate**
   From the repo root, run `claude plugin validate .` or in Claude Code run `/plugin validate .` to check the marketplace and plugin config.

1. **Add or edit skills**
   Use the steps in “Adding a new skill” above, with `<plugin-name>` = your new pack name. Replace or add skills under `plugins/<pack-name>/skills/`.

Plugins namespace skill commands as `/plugin-name:skill-name`.

### Suggesting this marketplace from other repos

To have Claude Code suggest this marketplace when someone works in another repo (e.g. `leadgenie` or `devops`), add this to that repo’s `.claude/settings.json` (not in this repo). Check [Claude Code plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces) for the current schema:

```json
{
  "extraKnownMarketplaces": {
    "apollo-skills": {
      "source": {
        "source": "github",
        "repo": "apolloio/skills"
      }
    }
  }
}
```

Then users can install plugins with `/plugin install apollo-eng@apollo-skills` from that project.

## References

- [Agent Skills specification](https://agentskills.io/specification) — Format and conventions for skill files
- [Apollo Claude Skills Library](https://www.notion.so/apolloio/Claude-Skills-Library-2fbab2b3b4968002a11ad055663f0b05?source=copy_link) — Notion library of Apollo skills and ideas
