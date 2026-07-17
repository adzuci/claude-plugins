---
name: todo
description: Add one or more persistent todos, reminders, follow-ups, or action items to an Obsidian Kanban backlog. Use when the user invokes /productivity:todo or asks to capture work in their backlog.
disable-model-invocation: true
---

# Todo

Capture durable tasks in the configured vault's `backlog.md` under `## Inbox`. Keep daily goals separate.

## Clarification Gate

Ask one concise question before writing only when the answer would materially change the task, for example:

- The task has no clear action or outcome.
- A person, artifact, vendor, or destination could refer to multiple real targets.
- The request contains an unresolved pronoun or shorthand that cannot safely be preserved as written.
- The user asks for a due date, owner, or priority but does not provide enough information.

Do not ask for optional metadata merely because it is absent. If the task is understandable and useful as written, add it immediately. Preserve unfamiliar proper nouns and source links instead of inventing expansions.

## Normalize

- Start each task with a concrete verb when a light rewrite preserves intent.
- Keep separate requested tasks as separate cards.
- Prefix tasks with `URGENT —` only when the user explicitly says they are urgent.
- Preserve dates, owners, ticket keys, and links.
- Do not convert the task into a tomorrow-only goal or a Jira issue unless asked.

## Write

Resolve the vault in this order: an explicit path, `$VAULT`, `~/.config/adzuci-productivity/config.json`, then `~/obsidian-vault`. Ask for the path if the resolved vault does not exist.

Resolve the bundled `scripts/append_todo.py`, then run:

```bash
python3 <skill-dir>/scripts/append_todo.py \
  --vault "${VAULT:-$HOME/obsidian-vault}" \
  --items "<one item per line>" \
  [--urgent]
```

Use `--dry-run` first only when an existing item may need promotion or the user's selection is ambiguous.

The script creates missing Kanban headings, adds new items idempotently, and promotes an existing matching item to urgent instead of duplicating it.

## Report

Return the tasks added, promoted, or already present and the updated backlog path. Do not refresh, deploy, or publish another system unless the user asks.
