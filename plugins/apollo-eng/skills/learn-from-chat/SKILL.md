---
name: learn-from-chat
description: Review the current conversation to identify user corrections, preferences, and patterns, then save them to Claude Code memory. Activate when the user says "learn from this chat", "learn from chat", "what did you learn", or "update your memory from this conversation".
---

# Learn From Chat

Review the current conversation to extract user preferences, corrections, and workflow patterns, then persist them to Claude Code memory files.

## When to Activate

- User says "learn from this chat", "learn from chat", or "/apollo-eng:learn-from-chat"
- User asks "what did you learn" or "create rules from our conversation"
- User asks to "update your memory" based on the conversation

## Instructions

### 1. Scan the Conversation

Look for:

- **Explicit corrections**: "no, do it this way", "don't do X", "always do Y"
- **Repeated preferences**: code style, git workflow, communication style
- **Rejected suggestions**: what you proposed that the user rejected, and why
- **Approved approaches**: things that differed from your initial instinct but the user preferred

### 2. Group Findings into Themes

Examples: git workflow, TypeScript fix approach, PR process, code style, communication preferences.

### 3. Check Existing Memory

Read `MEMORY.md` and any topic files in the memory directory to avoid duplicates. If a finding overlaps with an existing entry, propose **updating** it rather than duplicating it.

### 4. Draft and Present

For each proposed memory update, show:

- **File**: e.g., `MEMORY.md` or a topic file like `git-workflow.md`
- **Action**: New entry or update to existing
- **Full content**: The exact text to write

### 5. Wait for Confirmation

**Do NOT write any memory without explicit user approval.** Present all drafts first and wait for a "yes" or similar confirmation.

### 6. Write Approved Memory

Write to the project memory directory (check `MEMORY.md` for the path, typically `.claude/projects/<project>/memory/`).

For small preferences, add to `MEMORY.md`. For larger topics, create a dedicated topic file (e.g., `git-workflow.md`) and link to it from `MEMORY.md`.

## Memory Format

```markdown
## Topic Name

- Concise, actionable preference or rule
- Another preference

See [topic-file.md](topic-file.md) for details.
```

## Guidelines

- **Don't duplicate**: Update existing entries instead of creating overlapping ones
- **Keep it concise**: Under 50 lines per topic, actionable, not verbose explanations
- **Focus on corrections**: Prioritize things the AI got wrong or the user explicitly corrected — not general best practices the AI already knows
- **One theme per file**: Each topic file should cover a single, focused area
- **MEMORY.md stays short**: Put detailed notes in topic files, keep MEMORY.md as a summary index
