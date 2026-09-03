---
name: create-amplitude-experiment
description: Create an Amplitude experiment with Apollo's required bucketing, targeting, and leadgenie code scaffolding.
disable-model-invocation: true
---

# Amplitude Experiment Setup

Direct-invocation only. Run against a `apolloio/leadgenie` checkout:

```text
/apollo-eng-experimentation:create-amplitude-experiment
/apollo-eng-experimentation:create-amplitude-experiment "Monthly Recap Modal At 1k" growth-conversion
```

Both arguments are optional and map to Step 1's first two inputs (experiment name, owning
team). Anything not passed is inferred from context or asked for.

Enforce Apollo's experiment standards and avoid the most common mistakes:

- Wrong bucketing unit (corrupts the experiment beyond fixing)
- Key format mismatches between code and Amplitude (loses days of data)
- Missing deployments (experiment never reaches users)

## Step 0: Check Amplitude MCP

Before doing anything else, verify the Amplitude MCP is connected by calling `get_amplitude_context`.

Tool names carry a client-specific prefix (Claude Code exposes this as
`mcp__amplitude__get_amplitude_context`), so match on the suffix rather than an exact string, and
treat any available Amplitude tool as proof of a live connection. Only if **no** Amplitude tool is
available at all, stop immediately and tell the user:

> **Amplitude MCP is not connected.**
> Please run `/mcp` in Claude Code and connect the Amplitude MCP server before using this skill.
> Once connected, restart the skill.

## Step 1: Collect Inputs

Gather the following. Take anything passed as a slash-command argument first, then infer from
context (branch name, open files, conversation), and only ask for what is still missing:

| Input | Required | Default |
|-------|----------|---------|
| Experiment name (human-readable) | Yes | — |
| Description | Optional | — |
| Team (for `config/experiments/<team>.yml`) | Yes | — |
| Links | Recommended | — |
| Variants (optional) | No | `['control', 'treatment']` |

Variants default to `['control', 'treatment']` unless the user requests custom or multi-variant names. If they don't mention variants, proceed with the default without asking.

**Links** accepts multiple entries with a label prefix, e.g.:

- `jira https://apollopde.atlassian.net/browse/ABC`
- `notion https://www.notion.so/apolloio/XYZ`
- `design https://figma.com/...`

Parse each as `{url, title}` — capitalize the prefix as the title ("Jira Ticket", "Notion Doc", "Design Doc"). If no prefix, infer the title from the URL domain.

If any required inputs are missing and can't be inferred, ask before proceeding in a single plain-text question that collects all missing items at once. Aim for minimal back-and-forth.

Use this exact prompt format so users can copy/paste a blank form (required → recommended → optional):

```
Please provide the experiment details in plain text.
- Experiment name: human-readable, e.g., "Free to Paid Upgrade Modal"
- Team (required): for config/experiments/<team>.yml
- Links (recommended): JIRA ticket, Notion doc, design doc, etc.
- Description (optional): what the experiment tests

Copy following to be filled out:
- Experiment name:
- Team:
- Links:
- Description:
```

## Step 2: Generate and Validate the Experiment Key

Convert the experiment name to a kebab-case string (lowercase words joined by hyphens). This
kebab-case string is what you will set as the `key` value in the `activeExperiments` entry in
`assets/types/experiments.ts` (see Step 4). There is no automatic conversion from the enum value.

**Version numbers / acronyms:** keep them as single tokens the way they read, e.g.
`SeasonedFreeUserDialogV2` → `seasoned-free-user-dialog-v2` (not `...-v-2`). Proceed with the
computed key without confirmation.

Set `amplitudeKey` to the computed kebab key by default. If the user provides an explicit Amplitude key or you're attaching to an existing experiment in Amplitude, use that key instead.

**Uniqueness check:** Read `assets/types/experiments.ts` and verify the proposed enum key (PascalCase) and value (camelCase) don't already exist.

**PascalCase enum key → camelCase enum value** — the enum value is the same string in camelCase:

- `FreeToPaidUpgradeModal` → `'freeToPaidUpgradeModal'`
- `SeasonedFreeUserDialogV2` → `'seasonedFreeUserDialogV2'`

Legacy entries exist where enum values don't follow this convention. Do not copy them for new experiments — always use the camelCase value for new entries.

Show the user: `EnumKey = 'enumValue'` and the `amplitudeKey` before moving on.

## Step 3: Create the Experiment, Then Attach Links (2 MCP calls, +1 on duplicate recovery)

Use two calls: `use_amp_experiments` with `action: create` first, then `use_amp_flags` with `action: update` to attach links (if any). Deployments are set manually in the Amplitude UI after creation. If the create call fails with a duplicate-key error, recover the existing experiment via `search_amp_entities` and continue with the flag update if links were provided.

MCP schema constraints (from the live tool):

- Only these top-level fields are accepted: `projectIds`, `key`, `name`, `description`, `variants`, `evaluationMode`, `bucketingKey`, `links`, `deploymentIds`, `projectMetrics`. Unknown fields trigger `invalid input syntax for type json`.
- `links` must be `{url, title}` with valid URI strings for `url`. **Do not send them on the create call; attach via `use_amp_flags` instead.**
- `bucketingKey` accepts only `user_id`, `device_id`, or `amplitude_id`. Anything else fails input validation before the call leaves the client. Omit it — see "Bucketing" below.
- `search_amp_entities` takes `queries` (an array), not `query`. A stray `query` is dropped without an error and the search silently returns generic relevance results instead of your experiment.

### Call 1 — `use_amp_experiments` / `action: create` (no links)

```json
{
  "action": "create",
  "projectIds": ["168367"],
  "key": "<amplitudeKey>",
  "name": "<human-readable name>",
  "description": "<description>",
  "variants": [{ "key": "control" }, { "key": "treatment" }],
  "evaluationMode": "remote"
}
```

Replace the `variants` array with the user-provided variant keys if they requested custom or multi-variant names.

Capture the returned `flagId` and the experiment config `id`/`experimentId` for building the Amplitude URL. The URL uses the config `id`/`experimentId`, not the `flagId`.

### Duplicate-key recovery — `search_amp_entities` (only if the create call fails or IDs are missing)

```json
{
  "entityTypes": ["EXPERIMENT"],
  "queries": ["<amplitudeKey>"]
}
```

Pick the result whose key matches `<amplitudeKey>` exactly. Use its `flagId` for the flag update and its config `id`/`experimentId` for the Amplitude URL. Do not re-run the create call after recovering. If no result matches exactly, stop and report the original create error rather than guessing at a near match — acting on the wrong `flagId` edits someone else's experiment.

### Call 2 — `use_amp_flags` / `action: update` (attach links only)

```json
{
  "action": "update",
  "flagId": "<flagId from the create call or search>",
  "links": {
    "add": [
      { "url": "https://apollopde.atlassian.net/browse/ABC", "title": "Jira Ticket" },
      { "url": "https://www.notion.so/apolloio/XYZ", "title": "Notion Doc" }
    ]
  }
}
```

**Bucketing is a manual step - MCP cannot set it.** Apollo is a team product, so all users on a team must see the same variant. Getting this wrong corrupted the AI Full Email Variable experiment beyond fixing.

Two settings control it, and the MCP tools expose neither in a usable form. The **bucketing key** is the property hashed to pick a variant; `use_amp_experiments` restricts it to `user_id`, `device_id`, and `amplitude_id`, and its own description states that group-level bucketing "requires bucketingGroupType and is not supported via MCP yet". The **bucketing unit** (`User` vs `Group`, on the Targeting tab's advanced/cog settings) controls what exposures and stat-sig are counted over; no MCP field touches it at all. Amplitude defaults both to user-level, and `Group` requires the Accounts add-on beta.

Setting the unit to `Group` in the UI updates the key as well - Apollo's account-bucketed experiments store `group_name`. That single manual step is what protects the team-consistency guarantee, so do not treat the experiment as correctly bucketed until it is done. See the manual step in Step 5.

**Why `projectIds: ["168367"]`:** This is the Staging Amplitude project. Never use a different project ID without explicit confirmation. Note: the MCP parameter is `projectIds` (array), not `projectId`.

**Links:** Include all links provided by the user in the `use_amp_flags` call. Omit the `links` block entirely if none were provided.

## Step 4: Scaffold the Codebase

Make three additions, all sorted alphabetically:

### 1. `assets/types/experiments.ts` — Enum entry

Add to `ExperimentNames` (keep alphabetically sorted by key):

```typescript
MyNewExperiment = 'myNewExperiment',
```

### 2. `assets/types/experiments.ts` — activeExperiments entry

Add to `activeExperiments` (keep alphabetically sorted). Set `key` to the explicit kebab-case
Amplitude key as a string literal — it must match the Amplitude key and the YAML `amplitude_key`
exactly:

```typescript
[ExperimentNames.MyNewExperiment]: {
  variants: ['control', 'treatment'] as const,
  key: 'my-new-experiment',
},
```

Replace the `variants` array with the user-provided variant keys if they requested custom or multi-variant names.

### 3. `config/experiments/<team>.yml` — Ownership entry

Add under the `experiments:` key (alphabetically):

```yaml
my-new-experiment:
  amplitude_key: 'my-new-experiment' # intentionally matches the YAML key
  name: 'My New Experiment'
  code_ref: 'ExperimentNames.MyNewExperiment'
```

Use the same kebab key that was created in Amplitude.

If the team name has a slight typo, do a best-guess match against existing files under `config/experiments/` (e.g. `growth-conversion` → `config/experiments/growth-conversion.yml`) and proceed with that file.

## Step 5: Output Summary

Print a confirmation block. Use the experiment config `id`/`experimentId` from the create call or `search_amp_entities` (not `flagId`) for the Amplitude link:

```
Experiment created: my-new-experiment
Amplitude link: https://app.amplitude.com/experiment/apollo-io/168367/config/<experimentId>/settings

⚠️ Manual steps required (through Amplitude UI):
1. Deployments, check **Project API Key**, **staging-server**, **staging-client**
2. Set rollout to 100% in Amplitude UI
3. Targeting: include `account_id != 551e3ef07261695147160000` to exclude the Apollo's team
4. Bucketing: on the Targeting tab advanced settings (cog), set the Bucketing Unit to account/**Group**. MCP can set neither the bucketing key nor the unit; Amplitude defaults both to user-level, which splits teammates across variants.
5. Set statistical preferences in Amplitude UI:
  - Confidence Level: **90%** (default is 95%, recommended 90%, don't get lower than 80% — lower to reach statsig faster)
  - Bonferroni Correction: **Off** (Amplitude default is On — disable to speed up statsig)

ℹ️ Before launching:
  1. Add metrics (primary, secondary) in Amplitude UI or pass to Data Science team member to do that
  2. Ensure targeting is configured in Amplitude UI (on top of excluded Apollo's team account_id)
  3. If you change variant names or add more variants in Amplitude UI, update `activeExperiments` to match
```
