# skills

Central repository for Agent Skills at Apollo.

**Note:** This repo is currently an experiment used to explore how we could potentially use skill packs for [Claudathon — Build Claude Commands & Skills](https://www.notion.so/apolloio/Claudathon-Build-Claude-Commands-Skills-312ab2b3b4968076b5a7e32f8d8ef76f?source=copy_link).

## Where do skills go at Apollo?

There are three places you can store Claude skills depending on your use case:

1. **Here** — This repo (`apolloio/skills`) is the central place for shared skills and skill packs that apply across Apollo.

2. **In repo-specific skill folders** — If a skill is only relevant to a specific repository, place it in that repo's `.claude/skills` directory. Examples:
   - [`apolloio/devops/.claude/skills`](https://github.com/apolloio/devops/tree/master/.claude/skills)
   - [`apolloio/leadgenie/.claude/skills`](https://github.com/apolloio/leadgenie/tree/master/.claude/skills)

3. **In `~/.claude/skills`** — For personal skills that are specific to your local development environment and not meant to be shared with the team.

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

To add a skill to an existing plugin (e.g. `apollo-eng-pack`):

1. Copy `template/SKILL.md` to `plugins/<plugin-name>/skills/<skill-name>/SKILL.md`.
2. Set the YAML frontmatter: `name` (lowercase, hyphenated) and `description` (what the skill does and when to use it).
3. Replace the body with your instructions. Optionally add supporting files in the same skill directory.

To add a **new skill pack**, copy `template-plugin/` to `plugins/<pack-name>/`, edit its `.claude-plugin/plugin.json`, and register the plugin in `.claude-plugin/marketplace.json`. See [CONTRIBUTING.md](CONTRIBUTING.md) for full steps.

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

## References

- [Agent Skills specification](https://agentskills.io/specification) — Format and conventions for skill files
- [Apollo Claude Skills Library](https://www.notion.so/apolloio/Claude-Skills-Library-2fbab2b3b4968002a11ad055663f0b05?source=copy_link) — Notion library of skills and ideas
