# PRD & ERD Patterns

How to fetch and parse inputs for doc-driven mode (PRD + ERD + Jira epic → KB gap + drift report).

______________________________________________________________________

## Input Collection

Ask the user for these 3 inputs (prompt for any that are missing):

| Input | How Provided | Fallback if Missing |
|---|---|---|
| **PRD** | Notion URL (e.g. `https://www.notion.so/apolloio/Feature-Name-abc123`) | Required — prompt user |
| **ERD** | Repo path (`documentation/[feature].md`) or Notion URL | Search `documentation/` folder; ask if ambiguous |
| **Jira Epic** | Epic key (e.g. `ENG-1234`) or URL | Search PRD content for ticket references; ask if not found |

______________________________________________________________________

## Reading the PRD

### Via Notion MCP

```
Use: mcp__claude_ai_Notion__notion-fetch
Input: { "url": "https://www.notion.so/apolloio/Feature-Name-abc123" }
```

**What to extract from the PRD:**

1. **Feature name and one-line description** — what this feature does for users
1. **User-facing behaviors** — what users can do with this feature (these become KB article topics)
1. **Acceptance criteria** — what "done" looks like (these tell you what the code should implement)
1. **Success metrics** — helps prioritize which gaps matter most
1. **Out of scope** — explicitly excluded things (don't flag as gaps)
1. **Screenshots/wireframes** — describes the intended UI (compare against ContextualHelp)

**What to IGNORE in the PRD (don't send to Claude for analysis):**

- Engineering implementation details (database schema, API design)
- Team member names, slack channels, sprint details
- Historical comments and revision history
- Lengthy background context sections

**Summarize PRD to ~300 tokens before comparing:**

```
Feature: [name]
User-facing behaviors:
  1. User can [behavior A]
  2. User can [behavior B]
  3. [behavior C]
Acceptance criteria: [3-5 key criteria]
Out of scope: [explicit exclusions]
```

### PRD Fallback (Notion MCP unavailable)

Ask the user to paste the key sections:

> "Notion MCP is not available. Please paste the PRD's 'What' and 'User Stories' / 'Acceptance Criteria' sections."

______________________________________________________________________

## Reading the ERD

### From Repository

ERDs are typically in `documentation/[feature-name].md` or `documentation/[team]/[feature].md`.

```bash
# Search for ERDs related to the feature
git diff --name-only HEAD~10..HEAD -- 'documentation/*.md' | head -20
# Or by feature keyword:
grep -rl "[feature-name]" documentation/ --include="*.md"
```

**What to extract from the ERD:**

1. **Data model changes** — new fields, new models (tells you what the backend stores)
1. **API endpoints** — new or changed endpoints (tells you what the frontend can call)
1. **Behavioral notes** — constraints, rules, edge cases
1. **Integration points** — external systems affected

**Summarize ERD to ~150 tokens before comparing:**

```
ERD: [feature name]
New models/fields: [list]
New API endpoints: [list]
Key constraints: [list]
```

### ERD Fallback

If no ERD exists in the repo and user can't provide one:

- Proceed with PRD + Jira only
- Note in the output: "No ERD found — drift analysis based on PRD and Jira only"

______________________________________________________________________

## Reading the Jira Epic

### Via Atlassian MCP

```
Use: mcp__claude_ai_Atlassian__getJiraIssue
Input: { "issueIdOrKey": "ENG-1234" }
```

**What to extract from the epic:**

1. **Linked child tickets** — the individual tasks that make up the epic
1. **Ticket statuses** — which parts are Done vs In Progress vs To Do (affects what's actually implemented)
1. **Ticket titles** — reveal what sub-features were built
1. **Comments** — may reveal scope changes, removed features, or design decisions

**For each child ticket, check status:**

- `Done` / `Closed` → assumed implemented → check for KB article
- `In Progress` → partially implemented → flag as uncertain
- `To Do` / `Backlog` → not implemented → mark as NOT_IMPLEMENTED (skip KB check)

**Summarize Jira to ~150 tokens:**

```
Epic: ENG-1234 — [title]
Done tickets: [list of titles]
In Progress: [list]
Not started: [list — these are NOT_IMPLEMENTED by definition]
```

### Jira Fallback

If Jira epic key is unknown:

1. Search the PRD for ticket references: `grep -i "ENG-\|AIAPPS-\|JIRA\|ticket" [prd-text]`
1. If not found, ask the user: "What's the Jira epic key for this feature?"

______________________________________________________________________

## Drift Detection Logic

### Step 1: Build the "expected implementation" list

From PRD behaviors + Done Jira tickets:

```
Expected: [list of user-facing features that should be implemented]
```

### Step 2: Check each expected feature against the code

```bash
# For each expected feature, search for evidence in the codebase
grep -rl "[feature-keyword]" assets/app/containers/ assets/app/components/ \
  --include="*.tsx" --include="*.ts" -l
```

If found → feature is implemented → check KB article coverage
If NOT found → flag as `NOT_IMPLEMENTED`

### Step 3: Check code for features NOT in PRD

```bash
# Look for new containers, components, or feature flag wrappers
# added in recent commits related to this epic
git log --all --oneline | grep -i "[feature-name]\|ENG-1234"
git diff [base-commit]...HEAD --name-only | grep "containers/\|components/"
```

If code exists for something not in the PRD → flag as `UNDOCUMENTED_ADDITION`

### Step 4: KB Coverage Check

For each implemented feature:

1. Search `KnowledgeBaseArticles.ts` for the feature name
1. Search ContextualHelp files for the surface
1. Search Zendesk article index titles for the feature name
1. If no KB article found → `MISSING_KB_ARTICLE` (HIGH confidence)
1. If KB article found → fetch body → compare against implementation → find gaps

______________________________________________________________________

## Generating KB Drafts

For each `MISSING_KB_ARTICLE` or `NEW_FEATURE` finding, suggest a KB article draft:

```markdown
## Suggested KB Article: [Feature Name]

**Title:** [Suggested title, e.g. "Use [Feature Name] in Apollo"]
**Category:** [Suggested category based on related articles]
**Related articles:** [IDs of similar existing articles for reference]

### Suggested Outline:
1. Overview — What [feature name] does and when to use it
2. Prerequisites — What users need before getting started
3. [Step-by-step section based on user behaviors from PRD]
4. [Second step section]
5. FAQs / Troubleshooting
6. Related resources

### Key points to cover (from PRD/code analysis):
- [Specific user-facing behavior 1]
- [Specific user-facing behavior 2]
- [Edge case or constraint users should know about]

**Confidence:** HIGH / MEDIUM
**Evidence:** [PRD section + code file that confirms this feature exists]
```

______________________________________________________________________

## Output for Doc-Driven Mode

The doc-driven output includes two additional sections beyond the standard gap report:

```markdown
## 📊 PRD ↔ Code Drift

### NOT_IMPLEMENTED
Features described in PRD that have no code evidence:
| Feature | PRD Reference | Status |
|---|---|---|
| [feature] | [PRD section] | Jira ticket To Do / No code found |

### UNDOCUMENTED_ADDITION
Code changes not described in PRD (may still need KB article):
| Feature | Code Evidence | PRD Coverage |
|---|---|---|
| [feature] | [file:line] | Not in PRD |

### BEHAVIOR_DRIFT
Features described differently in PRD vs code:
| Feature | PRD Says | Code Does | Implication |
|---|---|---|---|
| [feature] | [description] | [observed behavior] | KB should reflect [X] |

## 📝 KB Article Drafts
[One draft outline per MISSING_KB_ARTICLE finding]
```
