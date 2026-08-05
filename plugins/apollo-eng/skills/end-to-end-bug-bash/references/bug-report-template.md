# Bug Report Format (Phase 4 — secondary/companion artifact)

**Notion is the canonical bug record now** (per `notion-bugs-and-evidence.md`'s Bugs DB rows,
created for every genuine bug, every run, unconditionally) — and it's self-sufficient: each row's
`content` carries the same full write-up as this file's per-bug section (Description/Environment/
Preconditions/Repro/Expected/Actual/Impact), and the real screenshot(s)/video get attached directly to
that row's `Files & media`/`Screenshot` property, not just referenced by path. This local
`bug-report-<feature-slug>.md`, in `playwright/reports/ai_manual/`, is a **secondary, companion
artifact** — a local backup with the same detail, not a place someone needs to go to see the full
picture. Say so plainly when this file is produced rather than implying it's the primary record.

This schema is lifted directly from the AI Sheets QA campaign (`bug-report-web-search-ai-models.md`
and siblings in that same folder) — it's already been proven to produce reports someone else can
debug from without re-running the repro themselves. Don't invent a different shape.

## File header

```markdown
# Bug Report — [Feature Name]

**Run date (UTC):** [ISO date]
**Base URL:** [environment URL]
**Run ID / evidence folder:** `playwright/reports/ai_manual/[run_id]/` (report: [report.md](./[run_id]/report.md))
**Scope tested:** [link to the Notion Test Plan page + which Test Case DB IDs this run covered]

## Run summary

- **Pass:** [count] ([which IDs])
- **Fail:** [count] ([which IDs] — see bugs below)
- **Skip:** [count]
- **Not-found:** [count]

**Headline finding:** [1-3 sentences — the single most important thing this run discovered, positive
or negative. Say plainly if the feature works better or worse than expected.]
```

## Per-bug section

Repeat for each genuine bug found this run (see `jira-filing-rules.md` for what counts as "genuine"
vs. an environment/access issue that doesn't get this treatment):

```markdown
## BUG-[FEATURE-PREFIX]-[NN]: [One-line description of the failure, not the fix]

- **Severity:** [P0/P1/P2/P3] ([Critical/High/Medium/Low]) — [why this severity, one clause]
- **Environment:** [URL], account [login/email — never password]
- **Preconditions:** [exact state needed to reproduce — data, flags, account type]

### Repro steps

1. [Numbered, exact — not "navigate to the feature," but the literal clicks/fills/selects taken]
...

### Expected

[What should have happened]

### Actual

[What actually happened — include exact error text, response codes, or observed values. Quote real
UI copy/error messages verbatim rather than paraphrasing.]

### Impact

[Who hits this and how badly — one or two sentences. Call out any security/data-integrity/silent-failure
angle explicitly, since those change severity and filing priority.]

### Evidence

- Screenshot: [`path`](relative link)
- Video: [`path`](relative link)
- Trace/HAR (scrubbed — see redaction rule below): [`path`](relative link)
```

## Non-bug findings section

Close the file with anything worth tracking that isn't a standalone bug (minor UX gaps, things that
turned out to be working-as-intended, confirmed non-issues) — same pattern as the campaign's
"Non-bug findings worth tracking" sections. Keep these out of the Jira-filing list entirely.

## Rules

- Quote real UI copy and real error text — don't paraphrase what the app said.
- If a fix was confirmed (e.g., a flag got enabled, a retry succeeded), say so plainly rather than
  leaving ambiguity about current state.
- Cross-model/cross-path comparisons (e.g., "same input succeeded via path B") are strong evidence —
  include them when you have them, they turn "seems flaky" into "confirmed transient, not permanent."
- One bug ID per distinct failure mode. Don't fold two unrelated failures into one bug entry just
  because they were found in the same test case.
- **Never attach an unscrubbed trace/HAR — to this file or to Notion.** Unlike video (where a
  password field just renders as masked dots), a network trace/HAR contains the raw login request
  body — the plaintext password — plus any session cookies/`Authorization` headers from later
  requests. Attaching one unscrubbed would violate the never-write-password rule. See `SKILL.md`
  Phase 3's trace/HAR credential-safety rule for how to scope or redact capture before it ever reaches
  this file or the Notion Bugs DB row's `Files & media` property. If a capture can't be confirmed
  scrubbed, don't attach it anywhere — describe the relevant request/response in prose instead.
