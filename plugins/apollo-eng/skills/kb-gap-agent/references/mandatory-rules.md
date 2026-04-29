# Mandatory Rules — kb-gap-agent

All 8 rules are NON-NEGOTIABLE. Follow on EVERY invocation.

______________________________________________________________________

## Rule 1: GREP-NOT-READ for large files

NEVER read these files in full:

- `apollo-dev-teams.yml` (~8,900 lines) → grep for the target team section only
- `assets/app/routes.tsx` (~2,900 lines) → grep for `FeatureFlagWrapper` or specific paths only
- `assets/app/components/contextual-sidebar/*ContextualHelp.tsx` → read ONLY files matching changed containers

```bash
grep -rl "container-name" assets/app/components/contextual-sidebar/
```

______________________________________________________________________

## Rule 2: NAMES-ONLY DIFF

ALWAYS use `--name-only` first. Then filter to KB-relevant paths ONLY:

- `assets/app/containers/`
- `assets/app/components/contextual-sidebar/`
- `assets/app/constants/KnowledgeBaseArticles.ts`
- `assets/app/routes.tsx`
- `assets/app/components/feature-gates/`

Discard: test files (`*.test.*`, `*.spec.*`), config files, types, utils, SCSS.
Read actual diff content **only** for files that map to KB articles.

______________________________________________________________________

## Rule 3: INDEX-ALL, FETCH-FEW

- Maintain a local cache at `.kb-cache/articles-index.json` with lightweight index: `[{ id, title, updated_at, html_url }]`
- Cache TTL: 24 hours (check file mtime). Fetch fresh if stale or if user says "fresh data".
- Fetch full article `body` for ONLY the 3–10 articles affected by the current scope.
- ALWAYS strip HTML before processing:
  ```bash
  echo "$body" | sed 's/<[^>]*>//g' | tr -s ' \n'
  ```
- Token math: 272 articles × 2,000 words ≈ $5–10 naive. 5 articles × 1,200 words stripped ≈ $0.05 optimized.

______________________________________________________________________

## Rule 4: PRE-SUMMARIZE BEFORE COMPARING (CRITICAL)

NEVER send raw diff + raw article body and ask "find gaps." ALWAYS pre-process:

**Step A — Summarize code change (~100 tokens):**

```
File: CsvEnrichmentOptions.tsx
Added: waterfall phone toggle (lines 42–58)
Added: new prop run_waterfall_phone: boolean
Modified: enrichment options UI to include phone waterfall section
```

**Step B — Summarize article content (~150 tokens):**

```
Article: Use CSV Enrichment (ID: 4409226361229)
Last updated: 2025-11-15
Sections: Overview, Upload CSV, Map Fields, Run Enrichment, View Results
Key topics: email enrichment, company enrichment, CSV upload
Does NOT mention: waterfall, phone enrichment, multiple providers
```

**Step C — Compare summaries with a specific question:**

```
What user-facing features in the code change are NOT documented in the KB article?
List each with evidence.
```

Per-comparison cost: ~300 tokens optimized vs ~5,000 tokens raw.

______________________________________________________________________

## Rule 5: CONCISE OUTPUT BY DEFAULT

- Default: one line per gap with type + confidence level.
- Only expand with evidence, suggested text, and file references if user asks "show details" or "expand gap N."

______________________________________________________________________

## Rule 6: ENGINEERING OWNER — HIGH CONFIDENCE FINDINGS ONLY

Every **HIGH confidence** finding MUST include the owning team and the most likely individual engineer.
Skip for MEDIUM and LOW confidence gaps to save tokens.

**Steps (in order):**

1. `git log --format="%an|%ae|%s" --all -5 -- "<affected-file>"` for the primary code evidence file
1. Skip bot/mechanical commits (i18n extraction chunks: `NOTICKET: i18n chunk`, `apolloio-ci`); use the first non-bot author
1. If git history is shallow or all commits are bot commits → search GitHub PRs via CLI:
   ```bash
   gh pr list --search "[component-name]" --repo apolloio/leadgenie --state merged --limit 10 \
     --json number,title,author,url,body
   ```
   Pick the PR that **created** the feature (not a later refactor/i18n bot pass). Read the PR author.
1. Fall back to team ownership from `apollo-dev-teams.yml` / `surface-owners.yml` only if both git log and GitHub PR search yield nothing
1. Always include the EM (engineering manager) from the team entry

**Required format:**

```
**Engineering owner:**
- **Team:** [Team name] (Jira: PROJECT, Slack: #channel, EM: Name @handle)
- **Most likely person:** **Name** (@github) — [context: PR link, ticket, date]
```

If multiple authors:

```
- **Most likely person:** **original-author** (@handle) — built feature in PR [#N](url) `[TICKET]` (date); most recent: **recent-author** (@handle) in PR [#M](url) `[TICKET]` (date)
```

If individual is truly unresolvable:

```
- **Most likely person:** unknown — shallow git history + no matching GitHub PRs found; recommend `git blame` on GitHub
```

______________________________________________________________________

## Rule 7: FULL URLS — MANDATORY (NON-NEGOTIABLE)

Every reference to a KB article or in-product page MUST include the complete URL.

**KB articles:** Always render as a markdown link with the full `knowledge.apollo.io` URL:

```
[Article Title](https://knowledge.apollo.io/hc/en-us/articles/ARTICLE_ID) (ID: ARTICLE_ID)
```

- Use `html_url` from the articles-index cache — never construct manually
- In tables, use the markdown link format in the Title/Article column

**In-product pages:** Always show the full `app.apollo.io` URL:

```
https://app.apollo.io/#/ROUTE
```

- Settings pages: `https://app.apollo.io/#/settings/[section]`
- Analytics: `https://app.apollo.io/#/analytics`
- Sequences: `https://app.apollo.io/#/sequences`
- Deals: `https://app.apollo.io/#/deals`
- Plays/Workflows: `https://app.apollo.io/#/plays`

**Never write:**

- ❌ `article 4409226361229` / ❌ `ID: 4409226361229` (bare ID)
- ❌ `/settings/content-center` (bare path)
- ❌ `app.apollo.io/settings/...` (missing `#/`)

**Always write:**

- ✅ `[Use CSV Enrichment](https://knowledge.apollo.io/hc/en-us/articles/4409226361229) (ID: 4409226361229)`
- ✅ `https://app.apollo.io/#/settings/content-center`

______________________________________________________________________

## Rule 8: NAVIGATION PATH — INCLUDE IN EVERY FINDING

Every finding MUST tell the reader exactly how to navigate to the in-product location.

**Standard gaps:**

```
**Where to verify:**
- Navigate: Settings → Integrations → CRM → Salesforce → Contacts
- Direct link: https://app.apollo.io/#/settings/integrations/crm/salesforce/contacts
- KB help link shown in: SettingsSalesforceContextualHelp.tsx → open the ? help sidebar on that page
```

**For `INVISIBLE_ARTICLE`:**

```
**Where to verify:**
- This article is NOT currently linked from the product UI
- Suggested surface: Settings → Integrations (based on article title)
- Direct link to suggested surface: https://app.apollo.io/#/settings/integrations
```

**For `STALE_REFERENCE` / `BROKEN_PLACEHOLDER`:**

```
**Where to verify:**
- Code location: assets/app/constants/KnowledgeBaseArticles.ts → KB.[ConstantKey]
- Used in: [component file path]
- No product navigation needed — this is a code-level fix
```

**IMPORTANT: Always derive deep links from `routes.tsx` — do NOT guess.** The lookup table below covers
common top-level patterns, but for sub-pages (e.g. CRM tabs like Pull, Error Logs, Authentication)
you MUST grep `routes.tsx` to build the full path.

```bash
# Example: find the exact route for Salesforce error logs
grep -n "error-logs\|activities\|authentication\|contacts\|accounts\|leads\|opportunities" assets/app/routes.tsx | head -20
```

**Key route pattern — CRM integrations use `/crm/:crmId`:**

- Salesforce: `/settings/integrations/crm/salesforce` (NOT `/settings/integrations/salesforce`)
- HubSpot: `/settings/integrations/crm/hubspot` (NOT `/settings/integrations/hubspot`)
- Sub-tabs: `/crm/:crmId/contacts`, `/crm/:crmId/error-logs`, `/crm/:crmId/authentication`, `/crm/:crmId/activities`, `/crm/:crmId/sequences`, `/crm/:crmId/accounts`, `/crm/:crmId/leads`, `/crm/:crmId/opportunities`

**ContextualHelp → navigation path lookup table:**

| ContextualHelp pattern | Navigation path | Deep link |
|---|---|---|
| `SettingsSalesforce*` | Settings → Integrations → Salesforce | `https://app.apollo.io/#/settings/integrations/crm/salesforce` |
| `SettingsHubspot*` | Settings → Integrations → HubSpot | `https://app.apollo.io/#/settings/integrations/crm/hubspot` |
| `SettingsIntegrations*` | Settings → Integrations | `https://app.apollo.io/#/settings/integrations` |
| `SettingsMailboxes*` | Settings → Mailboxes | `https://app.apollo.io/#/settings/mailboxes` |
| `SettingsChromeExtension*` | Settings → Integrations → Chrome Extension | `https://app.apollo.io/#/settings/integrations/chrome-extension` |
| `Sequences*` | Sequences | `https://app.apollo.io/#/sequences` |
| `Enrich*` | Enrich | `https://app.apollo.io/#/enrich` |
| `Home*` | Home | `https://app.apollo.io/#/home` |
| `Search*` | Search / Prospecting | `https://app.apollo.io/#/search` |
| `Conversations*` | Conversations | `https://app.apollo.io/#/conversations` |
| `Templates*` | Templates | `https://app.apollo.io/#/templates` |
| `Deals*` | Deals | `https://app.apollo.io/#/deals` |
| `Analytics*` | Analytics | `https://app.apollo.io/#/analytics` |
| `Tasks*` | Tasks | `https://app.apollo.io/#/tasks` |

**CRM sub-page deep links** (append to `/settings/integrations/crm/:crmId`):

| Sub-page | Path suffix | Example full link (Salesforce) |
|---|---|---|
| Contacts (default) | `/contacts` | `https://app.apollo.io/#/settings/integrations/crm/salesforce/contacts` |
| Contact stages | `/contacts/stages` | `https://app.apollo.io/#/settings/integrations/crm/salesforce/contacts/stages` |
| Accounts | `/accounts` | `https://app.apollo.io/#/settings/integrations/crm/salesforce/accounts` |
| Leads | `/leads` | `https://app.apollo.io/#/settings/integrations/crm/salesforce/leads` |
| Opportunities | `/opportunities` | `https://app.apollo.io/#/settings/integrations/crm/salesforce/opportunities` |
| Activities | `/activities` | `https://app.apollo.io/#/settings/integrations/crm/salesforce/activities` |
| Error Logs | `/error-logs` | `https://app.apollo.io/#/settings/integrations/crm/salesforce/error-logs` |
| Authentication | `/authentication` | `https://app.apollo.io/#/settings/integrations/crm/salesforce/authentication` |
| Sequences | `/sequences` | `https://app.apollo.io/#/settings/integrations/crm/salesforce/sequences` |

If no match in tables above → grep routes.tsx:

```bash
grep -i "[component-keyword]" assets/app/routes.tsx | grep "path="
```

**In gap tables,** include compact form in "Where to Verify" column:

```
Settings → Integrations → Salesforce → Error Logs ([direct link](https://app.apollo.io/#/settings/integrations/crm/salesforce/error-logs))
```
