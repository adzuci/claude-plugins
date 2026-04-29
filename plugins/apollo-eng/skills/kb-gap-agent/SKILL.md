---
name: kb-gap-agent
description: Detect stale, missing, or drifted KB articles. Activate when user mentions KB gaps, stale KB articles, KB audit, KB health, KB update from PRD, documentation coverage, knowledge base drift, check if docs are up to date, or any variation of knowledge base staleness — for a branch, PR, time range, product surface, or full batch.
---

# `kb-gap-agent` — KB Gap Detection & Update Skill

## When to Activate

- User asks about KB gaps, stale KB articles, missing documentation, or KB staleness
- User asks to check a branch, time range, or product surface for KB impact
- User wants a KB draft or update from a PRD, ERD, or Jira epic
- User asks for a "quick KB audit" or static KB health check
- User wants to run across all surfaces ("batch", "full audit")

______________________________________________________________________

## Mode Detection

Detect mode from the user's natural language input:

| Trigger phrases | Mode |
|---|---|
| "my changes", "my branch", "this branch", "current branch", GitHub PR URL (`github.com/.../pull/NNN`), PR number | **Branch diff** |
| "past week", "last 2 weeks", "since [date]", any time range | **Time-scoped** |
| team/surface name: "integrations", "hubspot", "salesforce", "sequences", "enrichment", "AI", etc. | **Surface-scoped** |
| "PRD", "ERD", "epic", Notion URL, Jira ticket key | **Doc-driven** |
| "quick audit", "stale refs", "static check", "health check" | **Quick audit** |
| "all surfaces", "full audit", "batch", "across all teams" | **Batch** |

If ambiguous, ask:

> "Which scope should I check? Options: (1) your current branch, (2) a time range, (3) a product surface/team, (4) from a PRD/ERD, (5) quick static audit, (6) all surfaces"

______________________________________________________________________

## Mandatory Rules (NON-NEGOTIABLE — follow on every run)

Full detail in [references/mandatory-rules.md](references/mandatory-rules.md).

| Rule | Summary |
|---|---|
| **Rule 1: GREP-NOT-READ** | Never read `apollo-dev-teams.yml`, `routes.tsx`, or ContextualHelp files in full — grep only |
| **Rule 2: NAMES-ONLY DIFF** | Always `--name-only` first; discard test/config/scss/utils; read diff content only for KB-relevant paths |
| **Rule 3: INDEX-ALL, FETCH-FEW** | Use `.kb-cache/articles-index.json` (24hr TTL); fetch full body for 3–10 articles max; strip HTML |
| **Rule 4: PRE-SUMMARIZE** | Summarize code change (~100 tokens) + article (~150 tokens) → compare summaries. Never raw diff vs raw body |
| **Rule 5: CONCISE OUTPUT** | One line per gap by default; expand only if user asks |
| **Rule 6: ENGINEERING OWNER** | HIGH confidence only: `git log` → fallback to `gh pr list --search` → fallback to team file. Always include EM |
| **Rule 7: FULL URLS** | Every KB article = `[Title](https://knowledge.apollo.io/hc/en-us/articles/ID) (ID: ID)`. Every in-product page = `https://app.apollo.io/#/route` |
| **Rule 8: NAVIGATION PATH** | Every finding needs `**Where to verify:**` block with Navigate path + direct link + ContextualHelp file. **Always derive deep links from `routes.tsx`** — never guess |

______________________________________________________________________

## Mode Pipelines

Full pipelines, timing, and KB cache logic in [references/mode-pipelines.md](references/mode-pipelines.md) — capture timing per that file.

| Mode | When | Key steps |
|---|---|---|
| **Branch diff** | "my changes" / "this branch" | `git diff $(git rev-parse --abbrev-ref origin/HEAD | sed 's/origin\///')...HEAD --name-only` → filter → ContextualHelp → fetch articles → compare |
| **Time-scoped** | "past week", "since [date]" | `git log --since=...` → same as branch diff |
| **Surface-scoped** | team or surface name | `surface-owners.yml` → team section → ContextualHelp → articles → compare + INVISIBLE check |
| **Doc-driven** | PRD / ERD / Jira epic | Fetch PRD (Notion MCP) + Jira (Atlassian MCP) → code grep → drift detection → KB coverage |
| **Quick audit** | "stale refs", "health check" | Zero AI: static checks — STALE_REFERENCE, BROKEN_PLACEHOLDER, INVISIBLE_ARTICLE, HARDCODED_URL, MISSING_KB_TODO |
| **Batch** | "all surfaces", "full audit" | Run Surface-Scoped for each surface → aggregate summary |

______________________________________________________________________

## Output

Full report format, gap type definitions, and delivery instructions in [references/output-format.md](references/output-format.md).

Gap report structure — **no tables, use task checkbox format**:

- Summary (mode, scope, articles checked, gaps, cost)
- 🔴 HIGH / 🟡 MEDIUM / 🟢 LOW action items as `- [ ]` tasks, each with: Article link, Gap description, Where to verify (with product navigation steps + deep link), Specific change recommendation
- ⚠️ Stale References (quick-audit)
- 📊 PRD ↔ Code Drift (doc-driven)

Deliver to Notion (preferred) or write to `.kb-cache/gap-report-[scope]-[date].md` (fallback).

______________________________________________________________________

## Post-Run: Notion Metrics

Full steps in [references/post-run-notion.md](references/post-run-notion.md).

**Metrics & Tracking page:** `33aab2b3b496801abf3bc8fdebee2fac`

After every run:

1. **Create child page** (all modes except quick-audit) — title: `KB Gap Report — [mode] — [scope] — [date]`
1. **Append Usage Log row** (all modes) — 14 columns including Duration, Output URL, Errors
1. **Update Stale Reference Tracker** — if `STALE_REFERENCE` found, grep for "Used In" component
1. **Graceful degradation** — if Notion MCP unavailable, write to `.kb-cache/usage-log.jsonl` + print row for manual paste

______________________________________________________________________

## Reference Files

| File | Contents |
|---|---|
| [references/mandatory-rules.md](references/mandatory-rules.md) | Full detail for all 8 rules |
| [references/mode-pipelines.md](references/mode-pipelines.md) | All 6 mode pipelines + timing + KB cache + article fetching |
| [references/output-format.md](references/output-format.md) | Gap report template, gap type definitions, output delivery |
| [references/post-run-notion.md](references/post-run-notion.md) | All 3 Notion update steps + graceful degradation |
| [references/kb-registry-guide.md](references/kb-registry-guide.md) | Zendesk API + KnowledgeBaseArticles.ts patterns |
| [references/contextual-help-map.md](references/contextual-help-map.md) | ContextualHelp files → surface → KB article mapping |
| [references/detection-signals.md](references/detection-signals.md) | Signal matrix + confidence levels + known blind spots |
| [references/prd-erd-patterns.md](references/prd-erd-patterns.md) | Doc-driven mode: PRD/ERD/Jira parsing patterns |
