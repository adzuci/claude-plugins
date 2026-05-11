---
name: pr-analytics-review
description: Reviews analytics coverage of a pull request — identifies missing events, recommends what to add with code snippets, and specifies how to measure success in Amplitude and Enterpret. Activate when someone shares a PR URL or number and asks what to track, how to know if the feature is working, or how to improve analytics coverage.
---

# PR Analytics Review

## Constants

| Constant | Value |
|---|---|
| Amplitude project ID | `241072` |
| Analytics import | `import zenalytics from 'common/lib/zenalytics'` |
| Taxonomy properties | `kingdom`, `phylum`, `class` — always include all three |
| Fabric Surfaces values | `GROWTH_KINGDOM`, `EXPANSION_PHYLUM` from `app/constants/AnalyticsConstants` |

**Common mistakes:**

| Anti-pattern | What to do instead |
|---|---|
| Assuming an event name is what it sounds like | Always call `get_events` first; read the `description` field |
| Reporting event volume without verifying source | Grep the actual tracking call; verify `source` constant value |
| Using an event name from `get_events` without codebase grep | Grep to confirm what code fires it before using it in any analysis |
| Treating `File Uploaded` as a CSV import event | That event is hardcoded to file attachments on person/company ID pages |

---

## Workflow

Copy and track progress:

```
PR Analytics Review:
- [ ] Step 1: PR read — feature + success moment identified
- [ ] Step 2: Existing tracking audited (zenalytics grep)
- [ ] Step 3: Related Amplitude events found + codebase-verified
- [ ] Step 4: Enterpret qualitative signal checked
- [ ] Step 5: Recommendations written (events + Amplitude + Enterpret)
- [ ] Step 6: Success definition + schedule check-in offered
```

---

### Step 1 — Read the PR

```bash
gh pr view <number> --json title,body,files
gh pr diff <number>
```

Identify: the user action being enabled, the success moment, and which files changed.

---

### Step 2 — Audit Existing Tracking

```bash
grep -r "zenalytics\|\.track(" <changed-files> --include="*.tsx" --include="*.ts"
```

Document: what fires today, what fires on the success moment, what's untracked.

---

### Step 3 — Find Related Amplitude Events

```
mcp__claude_ai_Amplitude__get_events({ projectId: 241072 })
```

Read the `description` field for each candidate.

**⛔ Do not skip:** grep the codebase to confirm what code fires each candidate event before using it. Event names are often misleading — see common mistakes above.

---

### Step 4 — Enterpret Qualitative Signal

```
mcp__claude_ai_Enterpret_Wisdom__search_knowledge_graph({ query: "<feature area>" })
```

Note frequency scores, sentiment, verbatim quotes. If users complain about something with no Amplitude event, that gap is highest priority.

---

### Step 5 — Recommendations

Output three sections:

**A. Events to add** — for each gap: event name (follow `[Area] Action Noun` convention), exact file + handler to fire from, full properties including taxonomy, ready-to-paste snippet:

```typescript
zenalytics.track('Object Sharing People Added', {
  kingdom: GROWTH_KINGDOM,
  phylum: EXPANSION_PHYLUM,
  class: 'Object Sharing Modal',
  mode: 'multi' | 'single',
  selection_count: number,
  select_all_used: boolean,
});
```

Priority-order by impact — success moment event first.

**B. Amplitude monitoring** — specify the exact funnel/charts to create: entry event → success event, segmented by plan tier. State what "good" and "bad" look like numerically.

**C. Enterpret monitoring** — 2–3 queries to run 2–4 weeks post-ship. State what sentiment shift to watch for.

---

### Step 6 — Define Success

End with:

> **2-week check-in target:** `<metric>` should `<direction>` by `<amount>` vs pre-ship baseline. If it doesn't move, suspect `<hypothesis>`.

Offer to schedule a follow-up check-in in 2 weeks to query Amplitude and report whether the metric moved.
