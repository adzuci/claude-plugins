# Contribution Guidelines

**Owner:** Bridie Meredith
**Updated:** 2026-03-31

Rules and heuristics for anyone (AE, DS, Analytics team member) contributing to the `analytics-copilot` repo. Read this before adding files, editing domain knowledge, or writing queries. Violations slow down Jarvis and create cleanup work for Bridie.

______________________________________________________________________

## Protected Files — Don't Touch Without Clearance

These files are load-bearing for Jarvis and the plugin. Edits require explicit sign-off from Bridie or Leo.

| File | Why it's protected |
|---|---|
| `CLAUDE.md` (root) | Agent identity and session behavior — bad edits break every session |
| `domain/jarvis_characters.md` | Character protocol — only Leo/Bridie can modify |
| `scripts/sync-jarvis.sh` | Controls what gets pushed to Jarvis — wrong edits break the plugin |
| `domain/SYNC_MANIFEST.md` | The authoritative record of the sync pipeline |
| `plugin/` (entire directory) | Plugin ships to Claude Enterprise — changes have real user impact |
| `sql/lu_saved_metrics.sql` | Metric registry backing the plugin — any change breaks exec queries |
| `data-catalog/glossary_entries.md` | Shared vocabulary — renaming terms breaks Jarvis reasoning |

**If you're not sure whether a file is protected, ask Bridie before editing it.**

______________________________________________________________________

## Sanity Checks Before You Commit

### 1. No personal names in shared file paths

`domain/` and `data-catalog/` are team-owned. Do not create files like:

- `domain/leo_analysis.md` ❌
- `data-catalog/bridie_notes.md` ❌

Personal context belongs in `teammates/<firstname_lastname>/`. If your analysis is worth sharing, generalize it and move it to `domain/` with a topic name.

### 2. No duplicate directories

The directory structure is intentional. Before creating a new folder, check that it doesn't already exist under a slightly different name.

Common traps:

- `domain/metrics/` doesn't exist — metrics live in `metrics/` at the root
- `domain/data-catalog/` doesn't exist — catalog lives in `data-catalog/` at the root
- `teammates/bridie/` vs `teammates/bridie_meredith/` — always use `firstname_lastname`

When in doubt: `ls` first.

### 3. Register new domain files immediately

If you create a file in `domain/`, add an entry to `domain/index.md` **in the same commit**. Files that aren't indexed are invisible to Jarvis and other teammates.

Format:

```markdown
### [`your_file.md`](your_file.md)
**Owner:** Your Name | **Updated:** YYYY-MM-DD

One sentence: what this file covers.

Key facts:
- Bullet of the most important fact
- Another key fact or gotcha

**Read if:** [specific trigger — what question/task would make someone need this]
```

### 4. Don't silently overwrite definitions

If your new content contradicts something already in `domain/`, log the conflict in `domain/CONFLICTS.md` before committing. Don't just overwrite — the previous definition might be in production queries.

### 5. Validate Snowflake queries before running

Run the validator on every query:

```bash
python3 scripts/validate_query_tables.py "<SQL>"
```

Exit 0 = proceed. Exit 1 = stop, follow the instructions in the output. No exceptions.

New table you need isn't in the catalog? Add a `data-catalog/context/<TABLE_NAME>.md` entry first, then run again.

### 6. Use the right schema tier

`ANALYTICS_DATAPLATFORM` > `ANALYTICS_DB.ANALYTICS` > legacy/playground. When both have a table you need, use the higher tier. If you're unsure which tier a table is in, check `data-catalog/context/<TABLE_NAME>.md`.

______________________________________________________________________

## Adding Knowledge Files

### Where things go

| Content type | Location |
|---|---|
| Domain knowledge (methodology, strategy, definitions) | `domain/` |
| Table documentation | `data-catalog/context/<TABLE_NAME>.md` |
| OKR metric definitions | `metrics/` |
| Glossary terms | `data-catalog/glossary_entries.md` |
| Personal analysis, notes, context dumps | `teammates/<firstname_lastname>/` |
| Reusable SQL patterns | `domain/sql_patterns.md` |
| Meeting transcripts | `teammates/<firstname_lastname>/meeting_transcripts/` |

### Promoting personal work to domain knowledge

If something you wrote in `teammates/` is useful to everyone:

1. Generalize it (remove personal specifics)
1. Move or copy it to `domain/`
1. Register it in `domain/index.md`
1. If it should flow to Jarvis, add it to `domain/SYNC_MANIFEST.md` and `scripts/sync-jarvis.sh`, then run `/sync-jarvis`

### 7. Propose scorecard eval questions when adding knowledge

Whenever you add a new table to the catalog (`data-catalog/context/`), register a new domain file, or add a skill that exposes new queryable data, check whether the new knowledge creates an opportunity for a Jarvis eval test case.

**Ask yourself:**

- Does this table have a join gotcha Jarvis could get wrong? → **guardrail** test case
- Does this table answer a question an exec might ask? → **point_in_time** or **trend** test case
- Does this table have a column that's easy to misinterpret? → **guardrail** test case

**If yes:** add a draft test case to `domain/scorecard/question_bank.yaml` in the same PR, or flag it for Bridie in the PR description. Format: follow existing entries in the question bank (test_id, question, category, difficulty, source_priority, expected, guardrails).

**If no:** that's fine — not every table needs a test case. But the question should be asked every time.

### Draft vs. active

Working drafts that aren't validated belong in `domain/pending_definitions.md` or named with `_draft` suffix. Don't add unvalidated content to Jarvis's live knowledge base — it will give wrong answers to executives.

______________________________________________________________________

## Syncing to Jarvis

Only files explicitly listed in `scripts/sync-jarvis.sh` flow to `jarvis/knowledge/`. Most personal files and WIP docs should not be synced.

**To add a file to the sync:**

1. Confirm the content is validated and team-owned (not personal)
1. Add a row to `domain/SYNC_MANIFEST.md`
1. Add a `cp` line to `scripts/sync-jarvis.sh`
1. Run `/sync-jarvis`
1. Get Bridie to review if the file touches Tier 1 content

**Never edit `jarvis/knowledge/` files directly.** Synced files will be overwritten on the next run.

______________________________________________________________________

## Push & Review Policy

### Your own directory — push freely

Changes scoped entirely to `teammates/<your_name>/` (personal notes, context dumps, meeting transcripts, worklogs) can be committed and pushed directly to main. No review needed.

### Everything else — get a review

Any change outside your personal directory requires review before merging:

- `domain/` — domain knowledge, methodologies, definitions
- `data-catalog/` — table docs, glossary
- `metrics/` — OKR metric definitions
- `sql/` — foundation table DDLs
- `scripts/` — automation scripts
- `plugin/` — plugin system prompt, registry, MCP config
- Root files (`CLAUDE.md`, `OPERATIONS.md`, etc.)

**Exception:** Leo and Bridie can push directly to main anywhere in the repo.

**Why:** Shared files affect every session and can break Jarvis if wrong. Your personal directory is yours — no one else depends on it.

### How to request review

Open a PR. Tag `@bridie-meredith` for domain/data-catalog/metrics changes, `@leo-liu` for strategy or plugin changes. Keep PRs small and scoped — one topic per PR.

______________________________________________________________________

## Commit Message Convention

```
feat(area): short description of what was added
docs(area): short description of what was documented
fix(area): short description of what was corrected
refactor(area): restructure without changing content
```

`area` = the subsystem: `domain`, `data-catalog`, `metrics`, `sql`, `plugin`, `jarvis`, `eval`, `scripts`

If your commit touched a synced file and you ran `/sync-jarvis`, say so:

```
docs(domain): add contribution guidelines
- registered in domain/index.md, SYNC_MANIFEST.md, sync-jarvis.sh
- synced to jarvis/knowledge/
```

______________________________________________________________________

## Who to Ask

| Question | Ask |
|---|---|
| Is this the right table? | Bridie |
| Can I edit this protected file? | Bridie or Leo |
| My metric definition conflicts with an existing one | Bridie |
| Snowflake access / MCP setup | Deepak Kumar |
| OKR metric definitions (NRR, FTP, activation) | Adhiraj Yadav |
| Product taxonomy / portfolio questions | Leo Liu |
