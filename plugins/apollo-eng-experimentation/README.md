# apollo-eng-experimentation

Amplitude experiment lifecycle skills: create an experiment, build the dashboard that
measures it, and clean it up once it ships.

## Scope: `apolloio/leadgenie` Only

These skills read and write LeadGenie-specific files (`assets/types/experiments.ts`,
`config/experiments/<team>.yml`) and target Apollo's Amplitude projects (`241072` prod,
`168367` staging). They will not do anything useful in another repo.

That is a deliberate exception to the marketplace's "codebase-specific skills stay in the
repo" rule. They previously lived in `apolloio/leadgenie/.claude/skills/`, where every
LeadGenie session paid their routing-context cost whether or not the engineer runs
experiments. Moving them here makes them opt-in, and gives Codex users access they did not
have before — `.claude/skills/` is Claude-only.

## Skills

| Invoke command | Purpose |
|---|---|
| `/apollo-eng-experimentation:create-amplitude-experiment` | Create an experiment with Apollo's required bucketing and targeting, then scaffold the registry and ownership YAML |
| `/apollo-eng-experimentation:experiment-metrics-dashboard` | Build an Amplitude dashboard that complements the standard Analysis View, from an experiment name, branch, or PR |
| `/apollo-eng-experimentation:experiment-cleanup` | Remove a shipped experiment, keep the winning code path, open the cleanup PR |

## Invocation Is Manual Only

All three skills set `disable-model-invocation: true`. They never enter routing context,
and the model will not pick them up from a phrase like "clean up experiment FooBar". Run
them as slash commands and pass the experiment reference as an argument.

## Migrating From The LeadGenie Repo Skills

These used to auto-activate from natural language in `apolloio/leadgenie`. If you used them
before, this is what changes.

**1. Install the plugin (once).**

| Client | Command |
|---|---|
| Claude Code | `/plugin`, pick `apollo-plugins` → `apollo-eng-experimentation` |
| Codex | `codex plugin install apollo-eng-experimentation` |

LeadGenie already registers the `apollo-plugins` marketplace for both clients
(`.claude/settings.json`, `.codex/config.toml`), so there is nothing else to configure. If
Codex does not see the marketplace, run `codex plugin marketplace add apolloio/claude-plugins`.

**2. Replace the phrase you used to type.**

| What you used to say | What to run now |
|---|---|
| "create an experiment" / "set up an A/B test" | `/apollo-eng-experimentation:create-amplitude-experiment` |
| "create an experiment called Foo for team growth-conversion" | `/apollo-eng-experimentation:create-amplitude-experiment "Foo" growth-conversion` |
| "create a dashboard for experiment FooBar" | `/apollo-eng-experimentation:experiment-metrics-dashboard FooBar` |
| "monitor experiment for this PR" | `/apollo-eng-experimentation:experiment-metrics-dashboard <PR url, number, or branch>` |
| "clean up experiment FooBar" | `/apollo-eng-experimentation:experiment-cleanup FooBar` |
| "remove experiment ExperimentNames.FooBar" | `/apollo-eng-experimentation:experiment-cleanup FooBar` |

Experiment references are accepted in any form the registry uses — `FooBar`,
`ExperimentNames.FooBar`, `fooBar`, or the kebab Amplitude key.

**3. Nothing else moved.** Behavior, prompts, and outputs are unchanged, and they still
operate on the same LeadGenie files. `experiment-cleanup` still labels its PR
`claude-experiment-cleanup`.

## Prerequisites

- A local `apolloio/leadgenie` checkout, and `gh` authenticated (see `/apollo-eng:gh-setup`).
- The Amplitude MCP. Most Claude users already have it enterprise-provisioned; if so,
  disable this plugin's `amplitude` server to avoid duplicate tools. Codex users get it
  from the plugin's `.mcp.json`.

## Typical Flow

1. `create-amplitude-experiment` — create on staging (`168367`), scaffold the code.
1. Ship and test on staging, then create the prod experiment.
1. `experiment-metrics-dashboard` — build the prod (`241072`) dashboard from the PR.
1. Read out, pick a winner.
1. `experiment-cleanup` — delete the losing branch and the experiment plumbing.
