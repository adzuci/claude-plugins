# Native Apollo CLI Command Surface

Use this reference when mapping a use case to native `apollo` commands. Always confirm the installed CLI version with `apollo --help` and command-specific help before execution.

## Command Groups

| Group | Capability | Safe first use |
| --- | --- | --- |
| `auth` | Login, logout, current user | `apollo auth whoami` |
| `users` | User profile and teammate lookup | `apollo users profile --credits --format json` |
| `usage` | Credit usage and rate-limit stats | `apollo usage credits --format json` |
| `email-accounts` | Sender inbox lookup | `apollo email-accounts list --format json` |
| `people` | Search and enrich people | Search first, enrich only after approval |
| `companies` | Search, enrich, get details, jobs | Search or get first, enrich only after approval |
| `contacts` | Create, update, and search contacts | Search first, create or update only after approval |
| `accounts` | Create, update, and search accounts | Search first, create or update only after approval |
| `sequences` | Search, add, remove, or stop contacts | Search first, change contacts only after approval |
| `tasks` | Create, bulk-create, and search tasks | Search first, create only after approval |
| `analytics` | Run report payloads | Validate payload before running |
| `calls` | Log, search, and update call records | Search first, log or update only after approval |
| `deals` | Create, search, and show deals | Search or show first, create only after approval |
| `news` | Search company news | Read-only research support |

## Approval-Gated Commands

Treat these command types as approval-gated:

- Account create, update, or bulk create.
- Contact create, update, or bulk create.
- Person or company enrichment.
- Email lookup that may spend credits.
- Sequence add, remove, stop, or status changes.
- Task creation or bulk creation.
- Call log or update.
- Deal creation.
- Analytics runs that may incur cost or change saved reporting state.

## Sequence Safety

Sequence contact changes can trigger real outbound if the status, sender, or sequence settings are wrong. For a first test, require:

1. Confirmed sequence.
1. Confirmed sender account.
1. Approved contact IDs or approved list.
1. Paused status unless the user explicitly approves active enrollment.
1. A post-run verification read.

## Agent Framing

Use this model:

```text
Assistant proposes the next action.
Apollo CLI performs a named Apollo command.
Command output becomes audit evidence.
Assistant summarizes the result and next gate.
```

Use the CLI for bounded Apollo actions and deterministic command output. Use other connected tools only for context gathering or cross-system coordination.
