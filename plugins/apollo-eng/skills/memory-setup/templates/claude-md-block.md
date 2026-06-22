<!-- BEGIN memory-setup (apollo-eng) -->

## Memory: Session Capture + Vault

Maintain a git-backed Obsidian vault for session capture and knowledge retention.

**Vault location:** `{{VAULT}}`

### Navigation & Structure

Read `index.md` first (token-efficient entry point). Do not glob or traverse without a clear purpose.

Navigate 2-hop: `index.md` → `wiki/<topic>/index.md` → article

**Folder purposes:**

- **memory/** — durables: `facts.md` (prefs, patterns), `projects.md`, `references.md`
- **sessions/** — YYYY-MM-DD.md daily logs, auto-written by the SessionEnd hook (stub + Haiku AI summary)
- **raw/** — inbox (librarian agent files daily)
- **incidents/** — incident reports and postmortems
- **runbooks/** — operational runbooks; drift templates to spot divergence from reality
- **handoffs/** — oncall handoff templates (open alerts, risky changes, customer threads)
- **recipes/** — quick-reference command snippets (symptom → tool → command)
- **wiki/** — topic-organized knowledge articles

### Vault Working Rules

- Do NOT generate folder CLAUDE.md files.
- All durable memory lives in the vault; do not scatter memory across repos or configs.
- SessionEnd hook auto-writes to `sessions/YYYY-MM-DD.md` after each session exit.

<!-- END memory-setup (apollo-eng) -->
