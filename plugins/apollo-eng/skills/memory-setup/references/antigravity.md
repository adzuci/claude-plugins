# Antigravity Session Capture

Use this compatibility reference when `memory-setup` is invoked from Antigravity/Gemini, or when the user explicitly asks to connect Antigravity sessions to the Claude-first vault.

## Source Data

Local Antigravity state has been observed under:

```text
~/.gemini/antigravity/
```

Useful read-only inputs:

- `~/.gemini/antigravity/brain/<conversation-id>/task.md`
- `~/.gemini/antigravity/brain/<conversation-id>/implementation_plan.md`
- `~/.gemini/antigravity/brain/<conversation-id>/*.metadata.json`
- `~/.gemini/antigravity/conversations/<conversation-id>.pb`
- `~/.gemini/antigravity/annotations/<conversation-id>.pbtxt`

Prefer the `brain/<conversation-id>/` markdown and metadata files when they are present. Treat `.pb` files as opaque unless a supported parser is available; do not scrape binary protobufs with ad hoc string matching.

## Lifecycle

Antigravity may expose hooks through:

```text
~/.gemini/config/hooks.json
```

When `SessionEnd` is present, install or update an Antigravity-specific sidecar rather than writing into `~/.claude`. If hooks are absent, use the pull-based importer:

```bash
python3 scripts/antigravity_session_importer.py --vault <vaultpath> --limit 3 --dry-run
```

Install the hook with:

```bash
python3 scripts/install_antigravity_hook.py --vault <vaultpath>
```

Hook merge rules:

- Back up `~/.gemini/config/hooks.json` before writing.
- Append a `SessionEnd` command only when no existing hook has the exact same command.
- Preserve unrelated hook events, matchers, and commands.
- Prefer a command that calls `scripts/antigravity_session_importer.py` with the vault path and no `--dry-run`.

Importer requirements:

- Maintain an idempotency state file at `~/.gemini/antigravity/.vault-ingested`.
- Skip conversation ids already present in that state file.
- Never print transcript content, secrets, keys, or tokens found in local state.
- Append to `<vault>/sessions/YYYY-MM-DD.md`, creating the daily front matter if missing.
- Use an Antigravity source label so entries can coexist with Claude and Codex entries.

Entry shape:

```markdown
## <HH:MM> — <basename of cwd or task title> (antigravity)
- **source:** antigravity
- **cwd:** `<cwd or unknown>`
- **session:** `<conversation-id>`
- **tokens:** antigravity: unavailable locally (<msg count or artifact count> artifacts)
```

Do not invent token totals. If Antigravity exposes token usage in a future local schema, document that schema and update the importer with tests before writing token lines.

## Skills Sharing

Antigravity skills are configured under:

```text
~/.gemini/config/skills
```

If the user wants shared skills, prefer a symlink from the Antigravity skills directory to a maintained source such as `~/.claude/skills`, then keep frontmatter compatible across clients.
