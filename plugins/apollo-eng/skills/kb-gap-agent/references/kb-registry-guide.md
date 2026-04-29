# KB Registry Guide

Reference for working with the Apollo KB data sources: Zendesk API and `KnowledgeBaseArticles.ts`.

______________________________________________________________________

## Source 1: Zendesk JSON API (Primary — No Auth Required)

### Fetching the Article Index

The index is all articles with lightweight metadata only. Paginate until no more pages are returned (100 per page).

**Endpoint:**

```bash
curl -s "https://knowledge.apollo.io/api/v2/help_center/en-us/articles.json?per_page=100&page=1"
```

**To build the full cache:** use the Python script in the "Extracting Index to Cache File" section below — it is more robust than a bash loop for handling JSON with spaces and network errors.

Response shape:

```json
{
  "articles": [
    {
      "id": 4409226361229,
      "title": "Use CSV Enrichment",
      "updated_at": "2025-11-15T10:30:00Z",
      "html_url": "https://knowledge.apollo.io/hc/en-us/articles/4409226361229",
      "body": "<p>Full HTML content...</p>",
      "draft": false,
      "promoted": false
    }
  ],
  "count": 272,
  "next_page": "...page=2",
  "page_count": 3
}
```

**For the cache index, store only:** `id`, `title`, `updated_at`, `html_url`
**Never cache full `body`** — fetch on demand.

### Extracting Index to Cache File

```bash
# Paginate until empty page and merge into .kb-cache/articles-index.json
python3 -c "
import urllib.request, json, urllib.error

articles = []
page = 1
while True:
    url = f'https://knowledge.apollo.io/api/v2/help_center/en-us/articles.json?per_page=100&page={page}'
    try:
        with urllib.request.urlopen(url) as r:
            data = json.load(r)
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f'Warning: fetch failed for page {page}: {e}')
        break
    batch = data.get('articles', [])
    if not batch:
        break
    for a in batch:
        if not a.get('draft', False):
            articles.append({'id': a['id'], 'title': a['title'], 'updated_at': a['updated_at'], 'html_url': a['html_url']})
    page += 1

with open('.kb-cache/articles-index.json', 'w') as f:
    json.dump(articles, f, indent=2)
print(f'Cached {len(articles)} articles')
"
```

### Fetching Full Article Body

Fetch full body only for articles you need to compare (3–10 per run):

```bash
# Fetch single article body, stripped of HTML
curl -s "https://knowledge.apollo.io/api/v2/help_center/en-us/articles/4409226361229.json" \
  | python3 -c "
import sys, json, re
data = json.load(sys.stdin)
a = data['article']
print(f'Title: {a[\"title\"]}')
print(f'Updated: {a[\"updated_at\"]}')
body = re.sub('<[^>]+>', ' ', a['body'])
body = re.sub(r'\s+', ' ', body).strip()
print(body[:3000])  # limit to 3000 chars (~750 tokens) for pre-summarization
"
```

### Checking if Article ID Exists

```bash
# Returns 200 if exists, 404 if deleted
curl -s -o /dev/null -w "%{http_code}" \
  "https://knowledge.apollo.io/api/v2/help_center/en-us/articles/4409226361229.json"
```

Or simply check against the cached index:

```python
live_ids = {a['id'] for a in articles_index}
is_live = 4409226361229 in live_ids  # True = article exists
```

______________________________________________________________________

## Source 2: KnowledgeBaseArticles.ts (Supplement — 64% Coverage)

**Location:** `assets/app/constants/KnowledgeBaseArticles.ts`

**Role:** Maps descriptive constant names to full KB article URLs. Used throughout the app.
Only covers articles linked from the product UI (173 of 272 total — 64% coverage).

### Structure

```typescript
const url = 'https://knowledge.apollo.io/hc/en-us';

const KB = {
  Home: url,
  GetStartedGuide: `${url}/categories/4409129885197-Get-Started`,
  // Feature areas organized as nested groups:
  CsvEnrichment: `${url}/articles/4409226361229-Use-CSV-Enrichment`,
  WaterfalEnrichment: `${url}/articles/9876543210123-Waterfall-Enrichment-Overview`,
  // ...
};

export default KB;
```

### Extracting Article IDs from Constants

```python
import re

with open('assets/app/constants/KnowledgeBaseArticles.ts') as f:
    content = f.read()

# Extract numeric article IDs from URLs
# Matches: /articles/4409226361229-Article-Title or /articles/4409226361229
ids = re.findall(r'/articles/(\d+)', content)
# Also extract category IDs if needed
# cat_ids = re.findall(r'/categories/(\d+)', content)

# Extract constant keys and IDs together
entries = re.findall(r'(\w+):\s*`\$\{url\}/articles/(\d+)', content)
# entries = [('CsvEnrichment', '4409226361229'), ...]
```

### Detecting Broken Placeholders

```python
# Find URLs with placeholder text instead of numeric IDs
placeholders = re.findall(r'(\w+):\s*`\$\{url\}/articles/([A-Z_]+_ARTICLE_ID[^`]*)`', content)
# Or simply:
broken = [line for line in content.split('\n') if 'ARTICLE_ID' in line and '/articles/' in line]
```

The quick-audit mode's BROKEN_PLACEHOLDER check detects these dynamically (pattern: grep `ARTICLE_ID`
in constant values) — no static list is maintained here.

Note: DKIM/SPF/DMARC have real articles via `KB.DkimDmarcSpfSetup` and `KB.EmailDomainAuth`.

### Stale References

The quick-audit mode's STALE_REFERENCE check detects these dynamically by comparing
`KnowledgeBaseArticles.ts` article IDs against the live Zendesk index. No static list is
maintained here — see `post-run-notion.md` → "Stale Reference Tracker" for the current
tracked set.

______________________________________________________________________

## Cache Management

**Cache location:** `.kb-cache/articles-index.json`

**Check cache freshness:**

```bash
# Check if cache is less than 24 hours old
if [ -f .kb-cache/articles-index.json ]; then
  CACHE_AGE=$(( $(date +%s) - $(stat -f %m .kb-cache/articles-index.json 2>/dev/null || stat -c %Y .kb-cache/articles-index.json) ))
  if [ "$CACHE_AGE" -lt 86400 ]; then
    echo "Cache is fresh (${CACHE_AGE}s old)"
  else
    echo "Cache is stale — refresh needed"
  fi
fi
```

Or in Python:

```python
import os, time, json

cache_path = '.kb-cache/articles-index.json'
cache_age = time.time() - os.path.getmtime(cache_path) if os.path.exists(cache_path) else float('inf')
cache_is_fresh = cache_age < 86400  # 24 hours in seconds
```

**Force refresh triggers:** User says "fresh data", "refresh cache", "ignore cache", "latest data"

______________________________________________________________________

## Usage Log Format

Append a JSONL line to `.kb-cache/usage-log.jsonl` after every run:

```json
{
  "date": "2026-04-07T10:00:00Z",
  "mode": "branch-diff",
  "scope": "feature/waterfall-enrichment",
  "articles_checked": 5,
  "gaps_found": {"high": 1, "medium": 2, "low": 1},
  "stale_refs": 0,
  "cache_hit": true,
  "est_token_cost": "$0.35",
  "output": "notion",
  "notion_page_url": "https://notion.so/apolloio/..."
}
```

Mode values: `branch-diff` · `time-scoped` · `surface-scoped` · `doc-driven` · `quick-audit` · `batch`
Output values: `notion` · `local-md`
