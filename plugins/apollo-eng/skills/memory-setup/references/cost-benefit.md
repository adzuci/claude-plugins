# Cost-Benefit: Session-Memory System

## What Installs

| Component | Where | Purpose |
|-----------|-------|---------|
| `<name>-vault/` | `<parent>/` | Git-backed Obsidian vault (capture layer) |
| `claudian` plugin | `<vault>/.obsidian/plugins/claudian/` | Vault-aware context sidebar in Obsidian |
| `obsidian-git` plugin | `<vault>/.obsidian/plugins/obsidian-git/` | Git sync from within Obsidian |
| Claude `session-end.sh` | `~/.claude/hooks/` | Claude Code SessionEnd hook script |
| Claude hook entry | `~/.claude/settings.json` | Registers hook with Claude Code |
| Claude memory block | `~/.claude/CLAUDE.md` | Teaches future Claude sessions where the vault is |
| Codex importer state | `~/.codex/.vault-ingested` | Tracks which Codex rollout ids were appended |
| Antigravity importer state | `~/.gemini/antigravity/.vault-ingested` | Tracks which Antigravity conversations were appended |

## Token Cost Per Session

| Item | Cost | Notes |
|------|------|-------|
| Claude Haiku summary (warm cache hit) | ~1¢ | Cache-read of global CLAUDE.md + skill catalog already warm |
| Claude Haiku summary (cold, first session of the day) | ~4¢ | ~35 k-token cache-create on the headless `claude -p` invocation |
| Claude per-model token line | **FREE** | Pure `jq` on the already-archived transcript — no API call |
| Codex token line | **FREE** | Reads the last cumulative `token_count` in the local rollout JSONL |
| Codex summary | Usually free/local | Derive tersely from `agent_message` text when available; omit when not derivable |
| Antigravity token line | Unavailable locally | Do not invent token totals unless a future local schema exposes them |
| Vault recall | On-demand, bounded | index.md-first 2-hop; you load only what you read; cached after first read |

**Estimate at ~5 sessions/day, ~60% substantive:** ~$1.50–2.50/month.

A Claude session is "substantive" (and triggers a Haiku summary) when it has at least 600 characters of prose content and 2 or more user turns. Short tool-only or trivial sessions exit early. Codex and Antigravity importers should also skip trivial sessions, but they should prefer local summary extraction over another model call.

## Comparison: claude-mem

| | This system | claude-mem (thedotmack) |
|-|-------------|------------------------|
| Summary model | Haiku (cheapest) | Premium model (Sonnet/Opus) |
| Trigger | Opt-in (substantive sessions only) | Automatic, every session |
| Cost shape | Flat ~1–4¢/session | Grows with memory store size |
| Estimated monthly | ~$1.50–2.50 | ~$3–9+ |
| Context injection | On-demand vault reads | Automatic full-transcript compression injected each session |
| Context pollution | None (you choose what to load) | Store injected regardless of relevance |
| Semantic vector recall | No | Yes (claude-mem's main advantage) |

**Bottom line:** this system is roughly 2–4× cheaper, and cost is opt-in and flat rather than automatic and growing. The trade-off: claude-mem offered semantic vector recall (fuzzy similarity search across your history). This system does not — vault search is structural (folder + filename), not semantic.

## Why It Is Worth It

- Session summaries surface decisions and blockers without requiring manual note-taking.
- The per-model token line gives precise cost attribution per session at zero incremental cost.
- The vault is git-backed: diffs, rollback, and remote sync all work out of the box.
- macOS-tuned v1; degrades gracefully on Linux/WSL (hook works; Obsidian GUI steps may differ).
