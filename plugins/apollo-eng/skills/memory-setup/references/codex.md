# Codex Session Capture

Use this compatibility reference when `memory-setup` is invoked from Codex, or when the user explicitly asks to connect Codex sessions to the Claude-first vault.

## Source Data

Codex stores local sessions as JSONL:

```text
~/.codex/sessions/YYYY/MM/DD/rollout-<ISO>-<uuid>.jsonl
```

Each line is a JSON object. Treat rollout files as read-only.

Relevant records:

- `type == "session_meta"`: first-line metadata with `cwd`, `originator`, `cli_version`, `timestamp`, `id`, and optional `git` fields.
- `type == "event_msg"` and `payload.type == "token_count"`: cumulative token usage. Use the last record in the rollout for final totals.
- `type == "event_msg"` and `payload.type in {"user_message", "agent_message"}`: turn volume. Count both.
- `~/.codex/session_index.jsonl`: optional index of `{id, thread_name, updated_at}`.

## Lifecycle

Codex does not expose the same Claude Code `SessionEnd` hook contract. Prefer a pull-based importer that runs from cron/launchd or a Codex notify/turn lifecycle if the installed version exposes one.

Importer requirements:

- Maintain an idempotency state file at `~/.codex/.vault-ingested`.
- Skip session ids already present in that state file.
- Never print transcript content, secrets, keys, or tokens found in rollout files.
- Append to `<vault>/sessions/YYYY-MM-DD.md`, creating the daily front matter if missing.
- Use a Codex source label so entries can coexist with Claude entries.

Entry shape:

```markdown
## <HH:MM> — <basename of cwd> (codex)
- **source:** codex
- **cwd:** `<cwd>`
- **branch:** `<git branch>`
- **session:** `<id>`
- **tokens:** codex: <output_tokens> out / <input_tokens + cached_input_tokens> in (<reasoning_output_tokens> reasoning, <msg count> msgs)
```

Summary extraction should be local and terse: use the tail of `agent_message` text to produce max 8 Did/Decisions/Blockers/Next bullets. If no useful agent prose is available, omit the summary section instead of inventing one.

## Validation

Run dry-run first against the most recent sessions:

```bash
python3 scripts/codex_session_importer.py --vault <vaultpath> --limit 3 --dry-run
```

Only after the user approves the preview should the importer append and update `~/.codex/.vault-ingested`.
