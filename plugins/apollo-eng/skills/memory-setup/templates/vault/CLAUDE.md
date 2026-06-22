# Vault Working Rules

This vault is the working directory for Claude Code session capture and operational memory. Codex and Antigravity may append compatible session entries when configured, but Claude Code is the primary workflow.

## Navigation

Read `index.md` first (token-efficient entry point). Do not glob or traverse without a clear purpose.

Navigate 2-hop: `index.md` → `wiki/<topic>/index.md` → article

## Memory Structure

- **memory/** — durables (facts, projects, references)
- **sessions/** — daily logs written by client hooks or importers; see `sessions/YYYY-MM-DD.md`
- **raw/** — inbox; librarian agent files daily
- **incidents/**, **runbooks/**, **handoffs/**, **recipes/** — operational templates and quick reference
- **wiki/** — topic-organized articles

## Rules

- Do NOT generate folder CLAUDE.md files.
- All durable memory lives in the vault; do not scatter across repos or configs.
