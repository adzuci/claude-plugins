# skills

Central repository for Agent Skills at Apollo.

## Where do skills go at Apollo?

There are three places you can store Claude skills depending on your use case:

1. **Here** — This repo (`apolloio/skills`) is the central place for shared skills and skill packs that apply across Apollo engineering.

2. **In repo-specific skill folders** — If a skill is only relevant to a specific repository, place it in that repo's `.claude/skills` directory. Examples:
   - [`apolloio/devops/.claude/skills`](https://github.com/apolloio/devops/tree/master/.claude/skills)
   - [`apolloio/leadgenie/.claude/skills`](https://github.com/apolloio/leadgenie/tree/master/.claude/skills)

3. **In `~/.claude/skills`** — For personal skills that are specific to your local development environment and not meant to be shared with the team.

## Repository Structure

```
.claude-plugin/
    marketplace.json
plugins/
    apollo-eng-pack/
        .claude-plugin/
            plugin.json
        skills/
            pr-description/
                SKILL.md
```

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
