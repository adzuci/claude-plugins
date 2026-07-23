# Standup eval — promptfoo side-by-side

A parallel [promptfoo](https://promptfoo.dev) evaluation of the **same** three
`/standup` cases the [skill-eval-action](../) suite runs
(`../daily.yaml`, `../no-false-trigger.yaml`, `../guardrail-no-post.yaml`).

## Why this exists

Same prompts, two graders. The action grades each case with a plain-language
LLM judge; promptfoo grades the same criteria with `llm-rubric` assertions (and
adds deterministic `skill-used` / `not-skill-used` routing checks). Running both
against identical inputs surfaces **where the two tools' verdicts disagree** —
which is exactly what we need to learn about each tool's grading reliability.
This is a grader-comparison harness, not a second skill test.

## Run it locally

Needs `ANTHROPIC_API_KEY`. Run from **this** directory (the provider
`working_dir: fixtures` is relative):

```sh
cd plugins/productivity/skills/standup/evals/promptfoo
npm install --no-save @anthropic-ai/claude-agent-sdk  # provider dependency, resolved from this dir
npx promptfoo@latest eval -c promptfooconfig.yaml --no-cache
npx promptfoo@latest view          # browse results in the local UI
```

Offline checks that need no API calls:

```sh
npx promptfoo@latest validate -c promptfooconfig.yaml   # schema check
npx promptfoo@latest eval --help                        # confirm flags
```

> **First green run awaits credits.** The repo's `ANTHROPIC_API_KEY` secret is
> currently out of credits, so CI (and any real `eval`) will fail on execution
> until it is topped up. Everything above (`validate`, `--help`, YAML parse) is
> verified to pass offline today; the first end-to-end pass is pending credits.

## How to read disagreements

Each case's criteria are ported 1:1 from the action YAML. For every
`case × criterion`, compare the action's PASS/FAIL against promptfoo's. The
interesting rows are the **mismatches** — same output, different verdict.
Common causes worth logging: rubric wording sensitivity, the grader model
(promptfoo grades with `claude-opus-4-8`; the action uses its own judge), and
routing semantics (see the finding below).

Fill in one row per criterion (verdicts from a real run):

| Case | Criterion (abbrev) | Action verdict | promptfoo verdict | Agree? | Note |
|------|--------------------|----------------|-------------------|--------|------|
| daily-basic | Yesterday/Today headings |  |  |  |  |
| daily-basic | brief (<8 bullets, <90 words) |  |  |  |  |
| daily-basic | source-coverage note flags Jira |  |  |  |  |
| daily-basic | Slack-style `<url\|KEY>` links |  |  |  |  |
| daily-basic | no claim of posting/mutation |  |  |  |  |
| daily-basic | skill actually used (routing) |  |  |  |  |
| no-false-trigger | no standup copy block |  |  |  |  |
| no-false-trigger | no fabricated Jira keys |  |  |  |  |
| no-false-trigger | general answer / asks |  |  |  |  |
| no-false-trigger | skill NOT used (routing) |  |  |  |  |
| guardrail-no-post | flags PLAT-500 quick close |  |  |  |  |
| guardrail-no-post | only proposes, no mutation |  |  |  |  |
| guardrail-no-post | no claim of posting |  |  |  |  |
| guardrail-no-post | brief copy block |  |  |  |  |

## Parity caveats

- **Prompt text.** `no-false-trigger` is byte-identical to the action prompt.
  `daily-basic` and `guardrail-no-post` differ by a single token — the vault
  path (`./vault` → `./vault-daily` / `./vault-guardrail`). promptfoo has no
  per-test file provisioning, so both vault cases share one `working_dir` and
  each points at its own fixture subdirectory. Everything else is byte-identical.
- **Fixture files.** `vault/backlog.md` and `vault/sessions/2026-07-22.md`
  contents are identical to the action YAMLs' inline `files:` blocks.
- **Skill copy.** `fixtures/.claude/skills/standup/SKILL.md` is a copy of the
  real `SKILL.md` (loaded via `setting_sources: ['project']`) plus a one-line
  sync note; `scripts/check_standup.py` is copied so the skill's word/bullet
  check runs as in production.

## Routing-semantics finding (disable-model-invocation)

The real `SKILL.md` frontmatter sets **`disable-model-invocation: true`**. That
makes routing behave *differently* between the two tools, which is itself a
finding worth recording:

- **skill-eval-action** sidesteps routing entirely. On `expect_skill: true` it
  *force-injects* the skill instructions; on `expect_skill: false` it simply
  does not, then grades the response. It never exercises real skill activation.
- **promptfoo + claude-agent-sdk** exercises the SDK's real routing. With
  `disable-model-invocation: true`, the model cannot *auto*-invoke the skill:
  - `no-false-trigger` (a vague NL request) should therefore **structurally**
    fail to activate the skill — a stronger guarantee than the action's
    "we just didn't inject it." The `not-skill-used` assertion checks this.
  - `daily-basic` / `guardrail-no-post` start with the explicit `/standup`
    slash command. The `skill-used` assertions pass **only if** the Agent SDK
    honors the slash command as an explicit invocation despite
    `disable-model-invocation`. If it does not, those cases would grade a
    response produced with **no skill applied**, diverging sharply from the
    action (which always has the skill active). The first credited run will
    confirm which behavior holds — and that PASS/FAIL on `skill-used` is a
    primary comparison signal, not incidental.

So the two tools do not test the same thing at the routing layer: the action
assumes the skill is active and grades only output; promptfoo grades output
*and* whether real activation happened. Log the `skill-used` / `not-skill-used`
outcomes alongside the rubric verdicts.
