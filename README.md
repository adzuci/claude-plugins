# skills

This repo is a place to add [skills and plugins](https://code.claude.com/docs/en/plugins) for Claude Code. We may host it as a [private plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces#private-repositories) so teams can install and use these plugins across multiple repos.

**Note:** This repo is currently an experiment used to explore how we could potentially use skill packs for [Claudathon — Build Claude Commands & Skills](https://www.notion.so/apolloio/Claudathon-Build-Claude-Commands-Skills-312ab2b3b4968076b5a7e32f8d8ef76f?source=copy_link).

## Where do skills go at Apollo?

There are three places you can store Claude skills depending on your use case:

1. **Here** — This repo (`apolloio/skills`) is where we add shared skills and plugins; the repo can be used as a [private marketplace](https://code.claude.com/docs/en/plugin-marketplaces#private-repositories) so they’re available across Apollo.

2. **In repo-specific skill folders** — If a skill is only relevant to a specific repository, place it in that repo's `.claude/skills` directory. Examples:
   - [`apolloio/devops/.claude/skills`](https://github.com/apolloio/devops/tree/master/.claude/skills)
   - [`apolloio/leadgenie/.claude/skills`](https://github.com/apolloio/leadgenie/tree/master/.claude/skills)

3. **In `~/.claude/skills`** — For personal skills that are specific to your local development environment and not meant to be shared.

## Repository Structure

```
.claude-plugin/
    marketplace.json
template/
    SKILL.md              # Copy this when adding a new skill
template-plugin/         # Copy this when adding a new skill pack
plugins/
    apollo-eng-pack/
        .claude-plugin/
            plugin.json
        skills/
            pr-description/
                SKILL.md
```

## Adding a new skill

1. **Copy the template**  
   Copy `template/SKILL.md` into your plugin's skills folder:
   ```
   plugins/<plugin-name>/skills/<skill-name>/SKILL.md
   ```
   Example: `plugins/apollo-eng-pack/skills/my-skill/SKILL.md`.

2. **Set frontmatter**  
   In the YAML at the top of `SKILL.md`:
   - **name**: Lowercase, hyphenated (e.g. `my-skill`). This is the skill name users invoke.
   - **description**: One line describing *what* the skill does and *when* Claude should use it (include trigger terms so the agent can discover it).

3. **Write the body**  
   Replace the placeholder with real instructions. You can add optional supporting files (e.g. `reference.md`, scripts) in the same skill directory.

4. **If the skill lives in a new plugin**  
   Add a new folder under `plugins/` with the same structure as an existing plugin, then follow "Adding a new skill pack" below and register the plugin in `.claude-plugin/marketplace.json`.

## Adding a new skill pack (plugin)

If you need a new plugin (e.g. a separate pack for product or infra):

1. **Copy the plugin template**  
   Copy the `template-plugin/` folder to `plugins/<pack-name>/` (e.g. `plugins/apollo-product-pack/`).

2. **Edit the plugin manifest**  
   In `plugins/<pack-name>/.claude-plugin/plugin.json`, set `name`, `description`, and `version`.

3. **Register in the marketplace**  
   In `.claude-plugin/marketplace.json`, add an entry to the `plugins` array:
   ```json
   {
     "name": "<pack-name>",
     "source": "./plugins/<pack-name>",
     "description": "Short description of the pack"
   }
   ```

4. **Add skills**  
   Use the steps in "Adding a new skill" above, with `<plugin-name>` = your new pack name.

## How to Use Skill Packs

Inside Claude Code while working in a repo (e.g. `leadgenie`):

**1. Add the marketplace** (points at this central repo):

```
/plugin marketplace add apolloio/skills
```

This registers `apolloio/skills` as a plugin marketplace, exactly how [`anthropics/skills`](https://github.com/anthropics/skills) tells you to register their repo.

**2. Install the plugin from that marketplace:**

```
/plugin install apollo-eng-pack@apollo-skill-packs
```

This uses the `plugin@marketplace` form — the same pattern shown in both the marketplace docs and the `anthropics/skills` README.

**3. Use a skill:**

```
/apollo-eng-pack:pr-description
```

Plugins namespace skill commands as `/plugin-name:skill-name`.

### Prompting the marketplace in other repos

To have Claude Code suggest this marketplace when someone works in another repo (e.g. `leadgenie` or `devops`), add this to that repo’s `.claude/settings.json` (not in this repo):

```json
{
  "extraKnownMarketplaces": {
    "apollo-skill-packs": {
      "source": {
        "source": "github",
        "repo": "apolloio/skills"
      }
    }
  }
}
```

Then users can install plugins with `/plugin install apollo-eng-pack@apollo-skill-packs` when they trust that project. See [Require marketplaces for your team](https://code.claude.com/docs/en/plugin-marketplaces#require-marketplaces-for-your-team) in the Claude Code docs.

## References

- [Agent Skills specification](https://agentskills.io/specification) — Format and conventions for skill files
- [Apollo Claude Skills Library](https://www.notion.so/apolloio/Claude-Skills-Library-2fbab2b3b4968002a11ad055663f0b05?source=copy_link) — Notion library of skills and ideas
