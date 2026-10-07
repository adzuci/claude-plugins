# apollo-eng-experimentation

Amplitude experiment lifecycle skills: create an experiment, keep its exposure
instrumentation correct, build the dashboard that measures it, and clean it up once it
ships.

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
| `/apollo-eng-experimentation:experiment-exposure-order` | Check that exposure is recorded before the metric event it explains, for both arms and on every path |
| `/apollo-eng-experimentation:experiment-metrics-dashboard` | Build an Amplitude dashboard that complements the standard Analysis View, from an experiment name, branch, or PR |
| `/apollo-eng-experimentation:experiment-cleanup` | Remove a shipped experiment, keep the winning code path, open the cleanup PR |
| `/apollo-eng-experimentation:experiment-pre-analysis-beta` | **Beta** — plan an experiment before launch: metrics, fresh baselines, effect to detect, confidence and power, sample size and runtime, as a chat summary, a plan file, and an offered Experiments DB entry update. Hands off to jarvis `experiment-setup` for independent warehouse verification |
| `/apollo-eng-experimentation:experiment-exposure-design-beta` | **Beta** — plan, review, and fix exposure logic and audience targeting. Run it when setting up an experiment, reviewing exiting exposure/eligibility setup or PR, or re-checking after a scope change. Setup and fixes are offered as a draft PR |

## Experiment Lifecycle Skills (Beta)

Skills that help walk an experiment from idea to a trustworthy launch. Each one is tied to a
lifecycle stage, declared in its frontmatter as `metadata.lifecycle-stage`, and each follows
the same working agreement in
[`references/experiment-lifecycle-conventions.md`](references/experiment-lifecycle-conventions.md):
confirm the skill is the right one, check tools first, collect inputs until the picture is
complete, teach while working, hand over in a fixed shape, review before delivering, and offer
to capture what was learned.

| Skill | Stage | What it hands over |
|---|---|---|
| `experiment-pre-analysis-beta` | Discovery | Metrics, baselines, effect to detect, sample size and runtime, as a plan file plus an offered update to the Experiments DB entry |
| `experiment-analytics-audit-beta` | Discovery, Execution | Before build: which events the experiment needs, which exist, what must be built, and which are at risk of meaning different things per arm. After build: whether the code matches that audit, with gaps fixed on approval and the audit brought up to date |
| `experiment-exposure-design-beta` | Execution | Where exposure fires and who reaches it, planned or reviewed, with setup or fixes offered as a draft PR |
| `experiment-aa-run-verification-beta` | Execution | Whether a running A/A dry run looks healthy: volume, split, and source agreement, as a verdict and a file |
| `experiment-stage-gate-beta` | Gate per lifecycle stage | Whether the experiment is ready to pass a lifecycle gate: the gate's items checked against related artifacts, confirmed by the DRI, with the skill or role that closes each gap, in chat only |

The skills are team-agnostic; the pre-analysis skill
reads per-team standards from its `teams/` folder when one exists.

**How they improve.** At the end of a run a skill may draft an anonymized learning card and,
with the user's approval, open a draft PR that adds it under
[`learnings/`](learnings/README.md). Maintainers fold recurring patterns into the skill. The
skills never edit themselves.

## Invocation

All skills set `disable-model-invocation: true`. They never enter routing
context, and the model will not pick them up from a phrase like "clean up experiment
FooBar". Run them as slash commands and pass the experiment reference as an argument.

`experiment-exposure-order` is the one exception and is natural-language activated. It is
a correctness check on code an engineer is already writing, and the bug it prevents throws
no error, fails no test, and fires no alert, so an engineer who knew to invoke it would
not have written the bug. It can still be run directly as a slash command when reviewing
a diff.

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
1. Write the exposure and metric calls. `experiment-exposure-order` activates on its own
   here, and is worth running by hand over the diff before the PR.
1. Ship and test on staging, then create the prod experiment.
1. `experiment-metrics-dashboard` — build the prod (`241072`) dashboard from the PR.
1. Read out, pick a winner.
1. `experiment-cleanup` — delete the losing branch and the experiment plumbing.
