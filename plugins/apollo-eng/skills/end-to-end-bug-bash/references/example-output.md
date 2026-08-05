# Example Output (Real, Condensed Excerpts)

These are trimmed excerpts from an actual completed run of the campaign this skill is modeled on
(`playwright/reports/ai_manual/` in the leadgenie repo, from before test plans and bugs moved into
Notion) — not fabricated placeholders. They exist to calibrate tone and level of detail — the same
substance now goes into the Phase 2.1 chat draft and the real Notion Test Plan/Bugs DB pages instead
of a local file; the full templates in this same `references/` folder and
`notion-test-plan-and-cases.md`/`notion-bugs-and-evidence.md` define the current required structure.
Don't copy these verbatim — every run's actual findings will differ.

## Test plan excerpt (originally local markdown, now the Phase 2.1 chat draft / Notion page content)

```markdown
# Test Plan — AI Sheets: Web Search AI Models

**Environment:** master staging — `https://app-master.preview.staging-gcp.apollo.io/#/`
**Scope:** `Web Search AI Models` (Notion status **Done**, no Jira epic linked — small scope)

## Readiness notes

- **No Jira ticket could be traced for this initiative** — the Notion page's Jira field is empty,
  and targeted Jira searches for "web search" / "perplexity" / "reasoning model" didn't surface a
  matching epic. Treat this test plan as based on the Notion problem statement alone.
- Because there's no ticket to cross-check against, the first job here is empirical discovery:
  confirm what actually exists today before writing bug reports against assumptions.

## Test cases

| ID | Title | Priority | Steps | Expected |
|---|---|---|---|---|
| TC-WSM-01 | Discover current model options for a web-search-capable AI column | P0 | 1. Create an AI-prompt column. 2. Look for any "search the web" toggle. 3. Open the model picker. | Document exactly what models are offered — this is exploratory, record findings even if the answer contradicts the initiative's own premise. |
| TC-WSM-02 | OpenAI reasoning model with web search actually returns grounded results | P0 | If an OpenAI reasoning model is selectable with web access enabled, create a column with a prompt requiring current information and run it. | Output reflects real web-sourced information, not a hallucinated answer — spot-check at least one result manually. |
```

Notice: steps are concrete UI actions, not vague descriptions; the readiness note says plainly what
was missing (no Jira epic) and how that shaped the plan, rather than blocking on it.

## Bug report excerpt (`bug-report-<feature>.md`)

```markdown
## BUG-WSM-01: OpenAI reasoning model + Web Access has a high transient failure rate vs. Anthropic on identical inputs

- **Severity:** P2 (Medium) — feature functions and failures are retryable, but the failure rate is
  high enough to undercut the initiative's core goal, and the error message has a minor info-leak.
- **Environment:** master staging — `https://app-master.preview.staging-gcp.apollo.io/#/`
- **Preconditions:** A studio/sheet with People Search data (any rows with a Company Name column).

### Repro steps

1. Log in and go to AI Studio (`#/builder`).
2. Create a new studio via **People search** → filter Job Titles: "CEO" → limit result to 20.
3. Click **Add column → AI column**, select model **OpenAI GPT-5.5**, leave **Allow Web Access** on.
4. Prompt: `What is the most recent funding round for {{Company Name}}? Include your source.`
5. Save & run first 10 rows. Wait for all cells to finish.
6. Repeat steps 3-5 with model **Anthropic Claude Sonnet 4.6** for direct comparison.

### Actual

**OpenAI GPT-5.5 + Web Access:** 6 of 10 cells succeeded with real, cited answers. **4 of 10 cells
failed outright** with the generic message `Failed to generate content for user 63320d648e9dc400a3ae4229`
— a 40% failure rate on this sample. **Anthropic Claude Sonnet 4.6, same 10 rows:** 10 of 10 succeeded,
including all 4 rows that failed for OpenAI. Manually retrying a failed OpenAI row succeeded on the
very next attempt, confirming the failures are transient, not permanent or input-specific.

### Evidence

- Screenshot (OpenAI mixed results): [`.../tc-wsm02-openai-gpt55-results-mixed-success-failure.png`](...)
- Video: [`.../video/run.webm`](...)
```

Notice: exact error text quoted verbatim (not paraphrased), a cross-model comparison used as evidence
that a failure is genuinely transient rather than "seems flaky," and severity justified in one clause
rather than left implicit.

## Campaign summary excerpt (`MASTER-SUMMARY.md`, campaign mode only)

```markdown
## Cross-cutting findings (apply across multiple features)

1. **Access/environment blockers found — all but one now resolved mid-campaign:**
   - **`AI_SHEETS_RND` feature flag — now resolved.** Was disabled, blocking 10 of 16 Sheet
     Automation test cases; enabled for this team mid-campaign, and a full re-test confirmed the
     flag was the real blocker (9 of 9 re-tested cases became fully executable).

3. **Jira/Notion status cannot be trusted at face value — verified case-by-case this session:**
   - AIS-1406 (Sheet Automation schedule overview): Jira said "DevReady," Slack showed it was
     explicitly told "don't merge it."
   - **Lesson for future runs:** always verify empirically; ticket status is a hint, not ground truth.
```

Notice: blockers that got resolved mid-run are called out explicitly (and, per `jira-filing-rules.md`,
are *not* filed as bugs), and a lesson is stated plainly enough that a future run of this skill could
act on it directly.
