# Post-Run: Update Notion Metrics & Tracking

**Usage Tracker database:** `33aab2b3b49680bfa5cce2a75dfe7c4d`
**Data source ID:** `351ab2b3-b496-804e-a8b1-000bca13a9c1`
**Metrics & Tracking page:** `33aab2b3b496801abf3bc8fdebee2fac`

**If Notion MCP is unavailable: skip this entire section.** Write data to `.kb-cache/usage-log.jsonl` only (see Step 3).

### Pre-flight: Verify Notion database access

Before any Notion write, verify access:

```
Use: mcp__claude_ai_Notion__notion-fetch
Input: { "id": "33aab2b3b49680bfa5cce2a75dfe7c4d" }
```

**If this fails** (permission error, page not found, or timeout):

1. Tell the user: "Cannot access the Kb Gap Agent Usage Tracker database. Ask the page owner to open the Metrics & Tracking page in Notion → Share → add the 'Claude' integration connection."
1. Fall back to Step 3 (graceful degradation).
1. Do NOT retry or prompt the user to re-authenticate — the fix is a one-time page share action in Notion.

______________________________________________________________________

## Step 1 — Create database row with full gap report (every run, mandatory)

Create a single row in the **Kb Gap Agent Usage Tracker** database. The page content of the row
**is** the full gap report — no separate child page needed.

**Pre-step: look up the engineer's Notion user ID** (the `Engineer` column is a Person property):

1. Get the engineer's name and email from git:
   ```bash
   git config user.name
   git config user.email
   ```
2. Search Notion users by name first:
   ```
   Use: mcp__claude_ai_Notion__notion-get-users
   Input: { "query": "<git config user.name>" }
   ```
3. If no match, search by email:
   ```
   Use: mcp__claude_ai_Notion__notion-get-users
   Input: { "query": "<git config user.email>" }
   ```
4. Use the returned `id` (UUID) as the `Engineer` property value.
5. If both lookups return no match (e.g. running from cloud with no git identity), **omit `Engineer`
   from the properties entirely** — do not pass a name string or empty string.

Call `mcp__claude_ai_Notion__notion-create-pages` with this exact JSON shape — `pages` **must**
be an array, and `parent` is a top-level sibling of `pages`:

```json
{
  "parent": {
    "type": "data_source_id",
    "data_source_id": "351ab2b3-b496-804e-a8b1-000bca13a9c1"
  },
  "pages": [
    {
      "properties": {
        "Run Date": "<ISO datetime — this is the title field>",
        "Engineer": "<Notion user UUID from notion-get-users lookup — omit this key if lookup fails>",
        "Mode": "<branch-diff | time-scoped | surface-scoped | doc-driven | quick-audit | batch>",
        "Scope": "<scope description>",
        "PR / Branch": "<PR number or branch name — branch-diff and time-scoped only; omit for other modes>",
        "Duration (s)": <number>,
        "Articles Checked": <number>,
        "Gaps Found (H)": <number>,
        "Gaps Found (M)": <number>,
        "Gaps Found (L)": <number>,
        "Stale Refs Found": <number>,
        "Cache Hit": "<YES or NO>",
        "Est. Token Cost ($)": <number — no $ sign, e.g. 0.04>,
        "Output Type": "notion",
        "Errors": "<None or description>",
        "Notes": "<1–2 sentence summary of key findings>"
      },
      "content": "<full gap report markdown — becomes the body of the database row page>"
    }
  ]
}
```

**Notes:**
- `Total Gaps` is auto-calculated by Notion formula (H + M + L) — do NOT include it in properties.
- Property values must be JSON primitives: strings for text/select, numbers for numeric fields.
- For quick-audit: still create the row with all metrics; include the structured audit findings
  (stale refs list, broken placeholders, hardcoded URLs, etc.) as the `content`.

Save the returned page URL — this is both the database row and the gap report page.

______________________________________________________________________

## Step 2 — Update Stale Reference Tracker (when stale refs are detected)

Run this step if the mode is `quick-audit`, or if any mode detected `STALE_REFERENCE` findings.

**Fill "Used In (Component)" for open stale refs:**

For each stale ref that still has "—" in the "Used In" column, grep the codebase to find which
component imports or references that constant:

```bash
grep -r "KB\.[ConstantKeyName]" assets/ --include="*.tsx" --include="*.ts" \
  --exclude="KnowledgeBaseArticles.ts" --exclude-dir="__tests__" -l
```

Known stale constants to check (use the quick-audit dynamic detection as source of truth; list
below is a reference baseline):

- `KB.ApolloDemo` (10316295330573)
- `KB.VerifyContactList` (10619188727309)
- `KB.MailboxWarmupIndex`, `KB.MailboxWarmup` (13152369727117)
- `KB.WarmupSetup` (32192100794893)
- `KB.SupportedEmailServiceProviders`, `KB.SupportedMailboxProviders` (4409140697101)
- `KB.LinkedInAutomation`, `KB.ProspectLinkedInWithExtension` (4409229262093)
- `KB.SetTaskPriority` (4409230986765)
- `KB.UseCRMEnrichmentToImproveCustomerEngagement` (4413126477709)
- `KB.SaveContactsToList` (4413837150605)
- `KB.RestAPI` (4415734629773)
- `KB.SupportTicketHistory` (4420566059789)
- `KB.AvoidSameContactMultipleSequences` (4423642868493)
- `KB.EngagementOverview` (5492860902669)

Update the Notion Stale Reference Tracker table row → fill "Used In (Component)" with file path(s).
If the constant is not referenced anywhere → fill "Used In" with `None — safe to remove`.

**Mark resolved stale refs as 🟢 Resolved:**

A stale ref is **resolved** when the constant key is no longer present in `KnowledgeBaseArticles.ts`.

```bash
grep "ApolloDemo:" assets/app/constants/KnowledgeBaseArticles.ts
# If no output → constant was removed → mark as Resolved
```

```
Use: mcp__claude_ai_Notion__notion-update-page
Update the Stale Reference Tracker row for [Constant Key]:
  Status: 🟢 Resolved
  Resolution: Removed constant  (or Updated to new article ID if a replacement was added)
  Resolved By: [git config user.name]
  Date: [today's date]
```

______________________________________________________________________

## Step 3 — Graceful degradation (Notion MCP unavailable)

- Skip Steps 1 and 2 entirely
- Write all data to `.kb-cache/usage-log.jsonl` (already done)
- Inform the user: "Notion MCP unavailable — run data saved to `.kb-cache/usage-log.jsonl`. Add a row to the Kb Gap Agent Usage Tracker database manually if needed."
- Print the row values so the user can paste them manually:
  ```
  Run Date: [date] | Engineer: [name] | Mode: [mode] | Scope: [scope] | PR/Branch: [or —]
  Duration: [s]s | Articles: [N] | Gaps: [H]H/[M]M/[L]L | Stale Refs: [N] | Cache: [Yes/No]
  Cost: $[X.XX] | Output: notion | Errors: [None or description] | Notes: [summary]
  ```

______________________________________________________________________

## What is NOT auto-updated (manual by Evgeny)

These sections require human judgment — filled by the PM/KB team after reviewing the output:

- **Gap Accuracy Validation** — whether each gap is genuine (✅ Yes / ❌ False Positive / 🟡 Partial)
- **Feedback Log** — qualitative feedback from engineers and KB team
- **Weekly Rollup Metrics** — aggregate manually each week
- **Success Metrics Dashboard** — update monthly
- **Roadmap** — update manually at milestones
