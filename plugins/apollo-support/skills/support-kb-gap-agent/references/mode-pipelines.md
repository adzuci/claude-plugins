# Mode Pipelines — support-kb-gap-agent

Bundled reference shipped under `./references` for `/apollo-support:support-kb-gap-agent`.

## Timing — Required for Every Run

At the start of every run, before any other step:

```bash
SKILL_START=$(date +%s)
RUN_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")   # Capture actual UTC timestamp — use for all [ISO date] fields
```

At the end of every run, just before following the post-run Notion flow:

```bash
SKILL_END=$(date +%s)
SKILL_DURATION=$(( SKILL_END - SKILL_START ))
# Use $SKILL_DURATION as the Duration (s) value in the Usage Tracker row
```

______________________________________________________________________

## Branch Diff (P0)

**Input variants — detect which is provided:**

| Input | How to get changed files |
|---|---|
| `git diff <default-branch>...HEAD` (current branch) | `DEFAULT=$(git rev-parse --abbrev-ref origin/HEAD \| sed 's/origin\///'); git diff $DEFAULT...HEAD --name-only` |
| GitHub PR URL (`github.com/.../pull/NNN`) | `gh pr diff NNN --name-only --repo apolloio/leadgenie` |
| PR number only (e.g. `PR 78694`) | `gh pr diff 78694 --name-only --repo apolloio/leadgenie` |

For PR URL input, also fetch PR metadata for context:

```bash
gh pr view 78694 --repo apolloio/leadgenie --json title,body,author,headRefName
```

Use the PR title and body as additional context when summarizing code changes (Rule 4 Step A).

```
1. Detect input type → get changed file names via git or gh CLI (see table above)
2. Filter to KB-relevant paths (see mandatory-rules.md Rule 2)
3. If no relevant files changed → report "No KB-relevant files changed in this PR/branch."
4. For each relevant changed file:
   a. grep -rl the container/component name in assets/app/components/contextual-sidebar/
   b. Read matched ContextualHelp files → extract KB.* constants used
5. Load .kb-cache/articles-index.json (refresh if stale)
6. Fetch full article body for the extracted article IDs (Rule 3)
7. For each article: pre-summarize code change + article (Rule 4)
   — include PR title/body as part of Step A when available
8. Compare summaries → identify gaps
9. Generate gap report → output (see output-format.md)
10. Follow [post-run-notion.md](post-run-notion.md) to create the Usage Tracker database row, or write `.kb-cache/usage-log.jsonl` only if Notion MCP is unavailable.
```

**Edge cases:**

- No KB-relevant files in diff → report "No KB-relevant paths changed."
- Changed file has no matching ContextualHelp → flag as "No ContextualHelp exists for [container] — KB article may be missing."
- New `FeatureFlagWrapper` in routes.tsx → flag as "New feature-gated route detected — KB article likely needed."

______________________________________________________________________

## Time-Scoped (P0)

```
1. Parse time range from user input (e.g. "past 2 weeks" → --since="14 days ago")
2. git log --since='X days ago' --name-only --diff-filter=ACMR --format="" | sort -u
3. Filter to KB-relevant paths (same as branch diff)
4. Continue with same pipeline as Branch Diff (steps 3–10 above)
```

Time expression parsing:

- "past week" / "last week" → `--since="7 days ago"`
- "past 2 weeks" / "last 2 weeks" → `--since="14 days ago"`
- "past month" / "last month" → `--since="30 days ago"`
- "since [date]" → `--since="YYYY-MM-DD"`

______________________________________________________________________

## Surface-Scoped (P0)

```
1. Identify team slug from user's surface input:
   grep -A 10 -i "[surface-name]" surface-owners.yml
2. Get owned files and routes for that team:
   grep -n "name: '[team-slug]'" apollo-dev-teams.yml
   → Read ONLY that team's section (~50–100 lines)
   → Extract files_owned and routes_owned
3. Find ContextualHelp files for the owned containers:
   grep -rl "[container-pattern]" assets/app/components/contextual-sidebar/
4. Extract KB.* constants from matched ContextualHelp files
5. Load .kb-cache/articles-index.json (refresh if stale)
6. Fetch full article body for extracted article IDs
7. Compare articles against owned code files for gaps
8. Optional: check if any KB articles from the index have titles clearly matching this surface's in-product features AND aren't linked from ContextualHelp → flag as INVISIBLE_ARTICLE (LOW confidence only). Do NOT flag guides, best practices, or troubleshooting articles.
9. Generate gap report → output
10. Follow [post-run-notion.md](post-run-notion.md) to create the Usage Tracker database row, or write `.kb-cache/usage-log.jsonl` only if Notion MCP is unavailable.
```

______________________________________________________________________

## Doc-Driven (P0)

```
1. Collect inputs (prompt user for any missing):
   - PRD: Notion URL → fetch via mcp__claude_ai_Notion__notion-fetch
   - ERD: repo path or Notion URL → search documentation/ folder if not provided
   - Jira epic: epic key (e.g. ENG-1234) → fetch via mcp__claude_ai_Atlassian__getJiraIssue

2. Parse PRD → extract:
   - Feature name and description
   - User-facing behaviors described
   - Acceptance criteria

3. Parse ERD/Jira → extract:
   - Technical implementation details
   - Scope of changes

4. Read implementation code for affected surfaces:
   grep -rl "[feature-name]" assets/app/containers/ assets/app/components/
   → Read matched files (limit to 3–5 most relevant)

5. Detect PRD↔Code drift:
   - Features described in PRD but NOT found in code → NOT_IMPLEMENTED
   - Code changes not described in PRD → UNDOCUMENTED_ADDITION
   - Features described differently in PRD vs code → BEHAVIOR_DRIFT

6. For each confirmed-implemented feature:
   - Check if KB articles exist covering this feature
   - If yes → compare and find gaps (same pre-summarize approach)
   - If no → flag as MISSING_KB_ARTICLE

7. Generate:
   - Gap report (drift + missing KB coverage)
   - KB draft: suggested new article or update text for each gap
   → output
8. Follow [post-run-notion.md](post-run-notion.md) to create the Usage Tracker database row, or write `.kb-cache/usage-log.jsonl` only if Notion MCP is unavailable.
```

For full PRD/ERD/Jira parsing patterns, see: [prd-erd-patterns.md](prd-erd-patterns.md)

______________________________________________________________________

## Quick Audit (P1 — ZERO AI, ZERO TOKENS)

Static analysis only. No git, no comparison, no AI. Completes in seconds.

```
1. Read assets/app/constants/KnowledgeBaseArticles.ts
2. Extract all article IDs from URL constants (regex: /\/articles\/(\d+)/)
3. Load .kb-cache/articles-index.json (refresh if stale — this is the only API call)
4. Build set of live Zendesk article IDs from index

5. STALE_REFERENCE check:
   IDs in constants but NOT in live Zendesk index → flag as STALE_REFERENCE
   Expected: 13 stale refs (see kb-registry-guide.md)

6. BROKEN_PLACEHOLDER check:
   URLs containing literal text like "ARTICLE_ID" (not a number) → flag as BROKEN_PLACEHOLDER
   Pattern: grep "ARTICLE_ID" in constant values
   Expected: 4 broken entries (KB.SetUpDKIM, KB.SetUpSPF, KB.SetUpDMARC, KB.FormBuilderLearnMore)

7. INVISIBLE_ARTICLE check (informational stat only):
   Count live Zendesk IDs NOT in constants → report as aggregate stat
   e.g. "112 of 272 KB articles are not linked from product code (this is normal — many are guides/best practices)"
   Do NOT flag each one as an individual action item. Do NOT investigate each one.

8. HARDCODED_URL check:
   grep -r "knowledge.apollo.io" assets/ --include="*.tsx" --include="*.ts" \
     --exclude="KnowledgeBaseArticles.ts" --exclude-dir="__tests__"
   Flag any matches → HARDCODED_URL (should use KB.* constant instead)
   Expected: at least 1 (AB59AdvancedDialerOrgBanner.tsx line 11)

9. MISSING_KB_TODO check:
   grep -r "TODO.*KB\|TODO.*knowledge\|TODO.*article" assets/ --include="*.tsx" --include="*.ts" \
     --exclude-dir="__tests__"
   Flag any matches → MISSING_KB_ARTICLE
   Expected: at least 1 (FinderRuleConfigEmptyState.tsx ~line 59)

10. ESLINT_GAP check:
    grep -r "TODO.*ESLint\|TODO.*enforce.*KB\|TODO.*openKBLink" assets/common/utils/
    Flag any matches → INFRASTRUCTURE_GAP
    Expected: 1 (kbLinkUtils.ts line 9 — missing ESLint rule for openKBLink)

Output: structured report with counts per category. No AI, no article comparison.
Then follow [post-run-notion.md](post-run-notion.md) to create the Usage Tracker database row, or write `.kb-cache/usage-log.jsonl` only if Notion MCP is unavailable.
```

______________________________________________________________________

## Batch (P1)

```
1. Read all surface names from surface-owners.yml:
   grep "^  - name:" surface-owners.yml | sed 's/.*name: //'
2. For each surface → run Surface-Scoped pipeline
3. After all surfaces complete → generate aggregate summary:

# KB Audit Summary — Full Batch — [date]
## Headline: [X] gaps found across [N] surfaces in [time]
## Aggregate Numbers
- Surfaces audited: N
- Total articles checked: N of 272
- Total gaps found: N (X HIGH, Y MEDIUM, Z LOW)
- Stale references: N
- Invisible articles: N
## Per-Surface Breakdown (table)

4. Follow [post-run-notion.md](post-run-notion.md) to create the Usage Tracker database row, or write `.kb-cache/usage-log.jsonl` only if Notion MCP is unavailable.
```

______________________________________________________________________

## KB Index Cache

**Location:** `.kb-cache/articles-index.json`
**Format:** `[{ "id": 12345, "title": "...", "updated_at": "...", "html_url": "..." }]`

**Cache logic:**

1. Check if `.kb-cache/articles-index.json` exists
1. Check file mtime — if < 24 hours, use cached index
1. If stale or missing → fetch fresh using the Python script in [kb-registry-guide.md](kb-registry-guide.md) → "Extracting Index to Cache File". It paginates until empty page, skips drafts, and saves `[{ id, title, updated_at, html_url }]` to `.kb-cache/articles-index.json`.
1. Force refresh: if user says "fresh data" or "refresh cache" → delete index and re-fetch

**Fetching full article content** (do this for ONLY 3–10 articles per run):

```bash
curl -s "https://knowledge.apollo.io/api/v2/help_center/en-us/articles/[ARTICLE_ID].json" \
| python3 -c "import sys,json; a=json.load(sys.stdin)['article']; print(a['title']); print(a['updated_at']); body=a['body']; import re; print(re.sub('<[^>]+>', ' ', body))"
```

Or strip HTML with sed:

```bash
BODY=$(curl -s "https://knowledge.apollo.io/api/v2/help_center/en-us/articles/[ARTICLE_ID].json" | python3 -c "import sys,json; print(json.load(sys.stdin)['article']['body'])")
echo "$BODY" | sed 's/<[^>]*>//g' | tr -s ' \n'
```

**Usage tracking** — after every run, follow [post-run-notion.md](post-run-notion.md) to create the Usage Tracker database row with the full report as page content. Append a JSONL line to `.kb-cache/usage-log.jsonl` only when Notion MCP is unavailable:

```json
{"date":"2026-04-07T10:00:00Z","mode":"branch-diff","scope":"feature/my-branch","articles_checked":5,"gaps_found":{"high":1,"medium":2,"low":1},"stale_refs":0,"cache_hit":true,"est_token_cost":"$0.35","output":"notion"}
```
