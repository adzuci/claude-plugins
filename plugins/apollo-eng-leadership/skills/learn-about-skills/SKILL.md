---
name: learn-about-skills
description: Explain how Cowork skills and plugins work in Apollo's shared skills marketplace. Use when the user asks how Cowork skills work, wants to browse or understand shared plugins, or wants help writing a new skill and opening a PR to add it to apolloio/skills.
---

# Learn About Skills

Teach the user how Apollo's shared skills marketplace works, then help them contribute to it if they want to.

## Explain the model

Start by explaining, in plain language:

- A **plugin** is a named package of related skills, such as `apollo-eng` or `apollo-eng-devops`
- A **skill** is an individual workflow invoked inside a plugin, such as `/apollo-eng:pr-description`
- This repo is a shared marketplace of plugins under `plugins/`
- Each skill lives in its own folder and must include a `SKILL.md` with `name` and `description` frontmatter

Keep the explanation concrete. Use one or two examples from this repo so the user can see what a real plugin and skill look like.

## Ask the next question

After the overview, ask:

> Do you want to learn how to write one?

If the user says no, stop after pointing them to the relevant plugin or skill examples.

## If they want to write one

Guide them through the contribution flow:

1. Decide whether the new skill belongs in an existing plugin or a new plugin.
1. Choose a short hyphenated skill name and a trigger-rich description that says what the skill does and when to use it.
1. Create the folder layout under `plugins/<plugin-name>/skills/<skill-name>/SKILL.md`.
1. Keep `SKILL.md` concise. Put only the core workflow in the file and move large references into separate files when needed.
1. If they are creating a new plugin, add `.claude-plugin/plugin.json`, a short plugin `README.md`, and a marketplace entry in `.claude-plugin/marketplace.json`.
1. Open a branch, commit the change, and create a PR against `apolloio/skills`.

## Coaching points

- Emphasize that the `description` field is the main trigger for automatic activation, so it should include explicit "when to use" language.
- Recommend imperative instructions in the body.
- Recommend examples only when they materially improve execution.
- Point people at existing plugins in this repo as the best source of patterns.

## Output expectations

When helping the user contribute a skill:

- Tell them whether it should be a skill in an existing plugin or a new plugin
- Propose the folder structure
- Draft the `SKILL.md` frontmatter and body
- Mention any marketplace or README updates needed
- Offer to prepare the branch and PR changes in this repo

## Useful references

Link people to these resources when they want more examples, background, or submission context:

- Claudathon overview and submission context: <https://www.notion.so/apolloio/Claudathon-Build-Claude-Commands-Skills-312ab2b3b4968076b5a7e32f8d8ef76f>
- Anthropic intro to agent skills: <https://anthropic.skilljar.com/introduction-to-agent-skills>
- Example discussion on skill design and usage: <https://x.com/trq212/status/2033949937936085378>
