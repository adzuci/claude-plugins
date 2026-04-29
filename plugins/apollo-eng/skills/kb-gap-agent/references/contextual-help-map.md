# Contextual Help Map

How `*ContextualHelp.tsx` files map product surfaces to KB articles — the primary signal for KB gap detection.

______________________________________________________________________

## What Are ContextualHelp Files?

Every major product surface in Apollo has a corresponding `*ContextualHelp.tsx` file that powers the in-app
help sidebar. These files are the primary map between product UI and KB articles.

**Location:** `assets/app/components/contextual-sidebar/`

**Naming pattern:** `[SurfaceName]ContextualHelp.tsx`

Examples:

- `SettingsIntegrationsContextualHelp.tsx` → integrations settings surface
- `EnrichContextualHelp.tsx` → CSV/bulk enrichment surface
- `SequencesContextualHelp.tsx` → sequences feature
- `HomeContextualHelp.tsx` → home dashboard

**Total:** 50+ files covering most major product areas

______________________________________________________________________

## File Structure Pattern

Every ContextualHelp file follows this structure:

```typescript
// eslint-strict
// ts-strict

import KB from 'app/constants/KnowledgeBaseArticles';
import messages from './SurfaceContextualHelp.messages';
// ... other imports

function useArticles() {
  const intl = useIntl();
  return [
    {
      title: intl.formatMessage(messages.articleTitle),
      description: intl.formatMessage(messages.articleDescription),
      href: KB.ArticleConstantName,  // ← This is the KB article mapping
    },
    {
      title: intl.formatMessage(messages.anotherTitle),
      href: KB.AnotherArticle,
    },
    // ...
  ];
}
```

Each `href: KB.XxxYyy` entry is a direct surface-to-KB-article mapping.

______________________________________________________________________

## How to Find Relevant ContextualHelp Files

### Step 1: From a changed container/component name

When you have a changed file path like `assets/app/containers/settings/integrations-settings/SalesforceContainer.tsx`:

```bash
# Extract the meaningful part of the path
CONTAINER="integrations-settings"

# Search for ContextualHelp files that reference this container area
grep -rl "integrations\|salesforce\|crm" assets/app/components/contextual-sidebar/ \
  --include="*Help.tsx" -i

# Returns: SettingsIntegrationsContextualHelp.tsx, SettingsSalesforceContextualHelp.tsx, etc.
```

### Step 2: From a team's owned file patterns

When you have `files_owned` from `apollo-dev-teams.yml`, extract container patterns:

```bash
# Given owned paths like: containers/settings/integrations-settings/
# Extract the last meaningful directory segment
PATTERN="integrations-settings\|crm\|salesforce\|hubspot"

grep -rl "$PATTERN" assets/app/components/contextual-sidebar/ --include="*Help.tsx"
```

### Step 3: Direct file path matching

If you know the surface name exactly:

```bash
# Find by surface name in file name
ls assets/app/components/contextual-sidebar/ | grep -i "integrations\|salesforce"
# → SettingsIntegrationsContextualHelp.tsx
# → SettingsSalesforceContextualHelp.tsx
# → SettingsHubspotContextualHelp.tsx
```

______________________________________________________________________

## Extracting KB Article IDs from ContextualHelp Files

Once you have the relevant files, extract which KB articles they reference:

```bash
# Extract all KB.* constant usages from a ContextualHelp file
grep "KB\." assets/app/components/contextual-sidebar/SettingsIntegrationsContextualHelp.tsx \
  | grep "href" \
  | grep -oP 'KB\.\w+'
```

Then look up each constant in `KnowledgeBaseArticles.ts` to get the article ID:

```bash
grep "ArticleConstantName:" assets/app/constants/KnowledgeBaseArticles.ts
# → ArticleConstantName: `${url}/articles/4409226361229-Article-Title`
# Extract ID: 4409226361229
```

______________________________________________________________________

## Surface → ContextualHelp File Map (Key Surfaces)

| Product Surface | ContextualHelp File | Notes |
|---|---|---|
| Home / Dashboard | `HomeContextualHelp.tsx` | |
| Search / Prospecting | `SearchContextualHelp.tsx` | |
| Sequences | `SequencesContextualHelp.tsx` | |
| Enrichment | `EnrichContextualHelp.tsx` | CSV enrichment |
| Settings: Integrations | `SettingsIntegrationsContextualHelp.tsx` | |
| Settings: Salesforce | `SettingsSalesforceContextualHelp.tsx` | |
| Settings: HubSpot | `SettingsHubspotContextualHelp.tsx` | |
| Settings: Mailboxes | `SettingsMailboxesContextualHelp.tsx` | |
| Settings: Others | `SettingsOthersContextualHelp.tsx` | |
| Conversations | `ConversationSetUpContextualHelp.tsx` | |
| Templates | `TemplatesContextualHelp.tsx` | |

**Full list:** Run `ls assets/app/components/contextual-sidebar/*Help.tsx`

______________________________________________________________________

## When No ContextualHelp File Exists

If a changed container has no matching ContextualHelp file, report it explicitly:

```
⚠️ No ContextualHelp file found for container: [container-name]
This may mean:
  1. The feature ships without in-app help (KB article may also be missing)
  2. The ContextualHelp file exists under a different name
  3. This is a new surface that needs a ContextualHelp file + KB article

Recommendation: Check if a KB article exists for this feature by searching the Zendesk index.
```

______________________________________________________________________

## Detecting New Routes Without KB Coverage

Check `routes.tsx` for new `FeatureFlagWrapper` routes that don't have a corresponding ContextualHelp:

```bash
# Find feature-flag-wrapped routes
grep -n "FeatureFlagWrapper\|featureFlagWrapper" assets/app/routes.tsx | grep "path"

# For each new route path, check if a ContextualHelp file exists for that surface
# e.g. path="/sequences/new-feature" → check for *SequencesContextualHelp.tsx or *NewFeatureContextualHelp.tsx
```

______________________________________________________________________

## Invisible Articles: KB Site ↔ Code Cross-Reference

Articles that exist on the KB site but are NOT referenced in any ContextualHelp file or `KnowledgeBaseArticles.ts`:

**Note:** The script below is a conceptual reference showing the detection logic. Claude executes this
as a bash tool call (`python3 -c "..."` inline) — it is not a standalone runnable file.

```python
import json

# Load cache
with open('.kb-cache/articles-index.json') as f:
    zendesk_articles = json.load(f)

# Load all article IDs referenced in code
import re, glob

with open('assets/app/constants/KnowledgeBaseArticles.ts') as f:
    kb_constants = f.read()
code_ids = set(re.findall(r'/articles/(\d+)', kb_constants))

# Also scan ContextualHelp files for any hardcoded article refs (rare but possible)
for path in glob.glob('assets/app/components/contextual-sidebar/*Help.tsx'):
    with open(path) as f:
        code_ids.update(re.findall(r'/articles/(\d+)', f.read()))

# Find invisible articles
live_ids = {str(a['id']) for a in zendesk_articles}
invisible = [a for a in zendesk_articles if str(a['id']) not in code_ids]

print(f"Total on site: {len(zendesk_articles)}")
print(f"Referenced in code: {len(code_ids & live_ids)}")
print(f"Invisible (on site, not in code): {len(invisible)}")
```

Run the script above against the live cache to get a current list — the set changes as new articles
are published and new KB constants are added to `KnowledgeBaseArticles.ts`.
