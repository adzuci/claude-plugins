---
name: apollo-cli-agent-workflows
description: 'Use when someone is building a GTM agent that needs Apollo data or Apollo actions: account discovery, buying committee mapping, enrichment, record staging, tasks, paused sequence staging, usage reporting, or analytics. Bootstrap the CLI first if missing or unauthenticated.'
disable-model-invocation: true
---

# Apollo CLI Agent Workflows

## Purpose

Help an AI assistant do useful Apollo work from the terminal. Setup is a prerequisite, not the main event.

The assistant checks whether the native Apollo CLI is ready, installs it if needed, verifies authentication, then proceeds to the requested Apollo workflow with approval gates for any side effects.

## Use When

- Build a GTM agent that needs Apollo data.
- Find accounts or contacts for an ICP.
- Map buying committees at target accounts.
- Enrich one approved person or company.
- Stage contacts or accounts for review.
- Create seller tasks or next-best-action queues.
- Stage contacts in a sequence with paused status.
- Pull usage, credit, or analytics data.
- Set up Apollo CLI only because one of those workflows needs it.

Do not proceed if the assistant cannot run terminal commands and the user cannot paste terminal output back into chat.

## Bootstrap First

Before any Apollo workflow, check the CLI and auth state:

```bash
command -v apollo || true
apollo --version
apollo auth whoami
```

If `apollo` is missing, install with the fastest available path:

```bash
brew install apolloio/apollo-io-cli/apollo-io-cli
```

That command taps the Apollo formula and installs the CLI in one step.

If Homebrew is not available, load the first-run checklist for macOS binary, Linux binary, Windows PowerShell, or source install commands.

If `apollo auth whoami` fails, auth is not ready. Run:

```bash
apollo auth login
apollo auth whoami
```

Never work around failed auth. Fix it before running search, enrichment, record changes, sequence actions, tasks, or reporting.

## Setup Modes

Choose the first mode that works:

| Mode | Use when |
| --- | --- |
| Direct-run | The assistant can run terminal commands in the target environment, including Cowork-style setup where the user does not manually open a terminal. |
| Guided-paste | The user can run terminal commands and paste output back into chat. |
| Export-backed | The CLI cannot run. Use Apollo exports or pasted JSON for planning only. |

## Workflow Routing

Route to the highest-value GTM job first:

| GTM agent job | Apollo value | First safe proof |
| --- | --- | --- |
| ICP account discovery | Find companies that match the target market | Read-only company search |
| Buying committee mapping | Find likely personas inside target accounts | Read-only people search by domain and title |
| Data enrichment | Fill missing person or company details | One approved enrichment |
| CRM or list staging | Create reviewable records for sellers | Small approved JSON file, no sequence action |
| Outbound prep | Turn qualified contacts into seller work | One approved task or paused sequence staging |
| Signal monitoring | Use news, hiring, or account changes as triggers | Read-only company news or jobs lookup |
| Reporting | Show credit, usage, or workflow impact | Usage or analytics readout |

Load the workflow templates when the user asks what the agent should actually do with Apollo data.

## Core Rules

1. Bootstrap first: check install, install if missing, login if needed, verify with `apollo auth whoami`.
1. Use only the native Apollo CLI.
1. Use command help as the source of truth when syntax differs.
1. Treat enrichment, credit spend, record changes, task creation, call logging, deal creation, sequence changes, and sends as approval-gated.
1. For sequence contact staging, default to paused status and confirm sender details before any sequence action.
1. Never print API keys, cookies, tokens, private credential files, or secret environment variables.

## Command Plan

Before any approval-gated command, show:

```markdown
## Apollo CLI Plan

Goal:
Assistant workspace:
Setup mode:
Apollo auth state:
Read-only commands:
Approval-gated commands:
Expected side effects:
Credit risk:
Send risk:
Data-change risk:
Stop path:
Evidence to capture:
Verdict: GO | HOLD
```

## Support References

Load only what is needed:

- `references/client-first-run.md`: non-Homebrew install commands, assistant setup, auth troubleshooting, and starter prompt.
- `references/command-surface.md`: Apollo command groups and approval-gated actions.
- `references/workflow-templates.md`: high-value GTM agent use cases and first tests.
