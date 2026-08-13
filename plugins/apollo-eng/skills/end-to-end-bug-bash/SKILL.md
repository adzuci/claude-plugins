---
name: end-to-end-bug-bash
description: >
  Run a full manual QA campaign end-to-end: research a feature (or a Notion initiatives board)
  from whatever references exist, generate a test plan and log bugs directly in Notion (in the
  team's real squad DB, alongside the test plan), execute against a live environment, and — only if
  explicitly requested — file confirmed bugs to Jira. Includes a campaign rollup for multi-feature
  runs.
disable-model-invocation: true
---

# End-to-End Bug Bash — Research → Test Plan → Execute → Report → File

## When to use this skill

Invoke explicitly when the user wants to hand over just a set of references (a bug-bash/feature
page, a Notion initiatives board, an ERD/PRD/Figma/Jira/PR, or just a feature description) and have
everything else — test planning, execution, Notion test plan + bug logging, and (if asked) Jira
filing — happen without them separately pasting a scenario into a different skill. Matches requests
like "run a full QA campaign on X", "test this feature end to end and log bugs", "do a bug bash for X
and execute it", "run manual QA against this initiatives board", or "find bugs in X and file tickets
under epic Y".

**Do NOT use for:**

- Writing automated Playwright test code — use `playwright-testing`; this skill's own
  `E2E-AUTOMATION-HANDOFF.md` output is what feeds that skill afterward.
- Generating test cases without executing them — use `bug-bash-generator` directly.
- Executing a scenario the user has already written out themselves — use `manual-test-execution`
  directly, no research phase needed.

You orchestrate the full manual-QA lifecycle in one run, reusing two existing skills' mechanics
rather than reimplementing them: **`bug-bash-generator`**'s documentation-analysis and Notion-write
techniques for Phase 1-2, and **`manual-test-execution`**'s browser-driving mechanics for Phase 3.
This skill adds the connective tissue those two don't cover on their own: flexible (not hard-gated)
research intake, squad-scoped Notion test plan + bug logging (the default, every run), and
campaign-level rollups. Jira filing is available but always opt-in, never automatic.

**Reference docs** (read when the workflow step points to them):

| Doc | Path |
| --- | ---- |
| Example output (real, condensed excerpts) | `references/example-output.md` |
| **Notion ID index (read first — points at the phase-specific files below)** | `references/notion-bug-bash-conventions.md` |
| Squad matching (Phase 0.2) | `references/notion-squad-matching.md` |
| Test Plan page + Test Case DB rows (Phase 2) | `references/notion-test-plan-and-cases.md` |
| Test Case status write-back (Phase 4.0) | `references/notion-test-case-status.md` |
| Test Case + Bugs DB evidence attachment (Phase 4) | `references/notion-bugs-and-evidence.md` |
| Bug report format, secondary artifact (Phase 4) | `references/bug-report-template.md` |
| Campaign rollup format (Phase 5) | `references/master-summary-template.md` |
| Automation handoff format (Phase 5) | `references/automation-handoff-template.md` |
| Jira filing rules — opt-in only (Phase 4.3) | `references/jira-filing-rules.md` |
| ERD schema-level test-gen pass (Phase 1) | `${CLAUDE_PLUGIN_ROOT}/skills/bug-bash-generator/references/erd-proposed-delta-pass.md` |
| Runtime automation risk checklist (Phase 1) | `${CLAUDE_PLUGIN_ROOT}/skills/bug-bash-generator/references/automation-risk-checklist.md` |
| Notion test-case upload convention (Phase 2, reused as-is) | `${CLAUDE_PLUGIN_ROOT}/skills/bug-bash-generator/references/notion-upload-format.md` |
| Multi-agent/shared-account operational lessons | `playwright/reports/ai_manual/manual-testing-playbook.md` (leadgenie-repo-specific; only present when running against that repo) |

______________________________________________________________________

## Unified checklist (order of operations)

- [ ] **Phase 0 — Intake:** determine scope (single feature vs. campaign), confirm the squad DB match
  (hard gate for Phase 2), gather whatever reference links exist (docs, Notion, Jira, Slack
  channels — project *and* PR-review — GitHub PRs, or anything else), confirm the MCP connections
  those references actually require (Notion always, Jira only if/when filing is requested),
  environment tier + URL, primary credentials, plan tier / feature flag / credit prerequisites,
  integration credentials, multi-user credentials, and backend access level — all once, upfront.
  Do not hard-stop on missing links.
- [ ] **Phase 1 — Research (per feature):** analyze whatever sources are actually available.
- [ ] **Phase 2 — Test plan (per feature):** reuse an existing in-scope Notion Test Plan/Test Case
  when the user asks to execute it. Otherwise, draft cases in chat, get one go-ahead, then create the
  real Notion Test Plan page (in the confirmed squad) plus Test Case DB rows.
- [ ] **Phase 3 — Execute (per feature):** drive the UI with `playwright-cli` per
  `manual-test-execution`'s gates and rules, using the Phase 2 test plan as the scenario source.
- [ ] **Phase 4 — Evidence + bug logging (Notion always; Jira only on explicit request):** update every
  executed Test Case DB row's `AI Status` with the real outcome and upload its run evidence,
  then log every genuine bug as a
  Notion Bugs DB row (full write-up in `content`, real screenshot/video/scrubbed-trace attached to
  `Files & media`/`Screenshot`) under this feature's Test Plan page — unconditionally, every run. Write the
  secondary local `bug-report-<feature-slug>.md` alongside it. Jira filing never happens here
  by default — it's a standalone action available any time it's explicitly requested afterward.
- [ ] **Phase 5 — Campaign rollup:** write `MASTER-SUMMARY.md` and `E2E-AUTOMATION-HANDOFF.md`,
  including the default "Bugs logged to Notion" section and, only if Jira was actually requested
  and used this campaign, a "Jira tickets filed" section.

______________________________________________________________________

## Phase 0 — Intake

**Ask everything in one consolidated round, not one question at a time.** 0.2 through 0.10 below
define *what's needed*, not a sequential script — collect all of it via a single round-trip (one
message out, one reply in), per the intake mode chosen below. Only the hard content/approval gates
later (squad-ambiguity resolution, the Phase 2 go-ahead when new test cases will be created,
third-party authentication, and the Phase 4 bug-logging confirmation) remain separate stops. For
Apollo-owned test environments, an explicit request to run/execute/test plus a complete environment
URL and usable primary credentials is the start authorization; do not ask for another "start"
confirmation.

### 0.1 Resolve scope + intake mode

Infer both from the request before asking anything:

1. **Scope:** a single bug-bash/feature/test-case page or one feature description means **single
   feature**; a database/board or explicit multi-feature request means **campaign**. Ask only when
   the supplied source genuinely supports both interpretations.
1. **Intake mode:** default to **Touchless**. Use **Guided** only when the user requests a form or
   wants to provide inputs manually.

In Touchless mode, resolve as much of 0.2-0.10 as possible yourself first (crawl references, check
tool/session state, apply safe defaults), then ask once for only what genuinely could not be
determined. **Touchless never means "guess and proceed"** — missing exact URLs or passwords, an
ambiguous squad match, and third-party credentials are still asked, bundled into one final round.
Never re-ask for a value already supplied in the current conversation.

Resolve scope first:

- **Single feature:** proceed straight to 0.2.
- **Campaign:** fetch the board via Notion MCP (`notion-fetch` for the data-source ID, then one
  `notion-query-database-view` call — page_size 100, paginate on `has_more` — per the
  `notion-bugs-and-tests` skill's query rules). Confirm with the user which statuses are in scope
  (e.g. "Done or Implementing"). **Status can lag reality** — for anything ambiguous, cross-check
  Jira/Slack before committing to in/out of scope, and document that check. Then loop Phases 1-4
  once per in-scope feature before Phase 5.

### Guided mode: the consolidated template

Send this as **one message**, filled in with the feature/campaign name, and ask the user to reply
with everything they have in one go (skip lines that don't apply — don't wait for each to be
answered individually):

```markdown
To get started, reply with everything you have in one message (skip anything that doesn't apply):

**Squad:** [name — I'll match it against the real Teams DB and confirm]

**References:** Notion PRD/ERD page, Jira epic, Figma link, GitHub PR(s), Slack project channel,
Slack PR-review channel, anything else (docs/meeting notes)

**Environment:** staging or production? Exact base URL: (if this looks VPN-gated, I'll check
reachability now and ask you to connect before we go further)

**Login:** [email/username]
**Password:** [I will not echo, log, or store this — or reply "I'll log in myself" instead]

**Feature flag / plan tier / credit prerequisites:** [anything that applies, or "none"]

**Third-party integration credentials** (if this touches Salesforce/HubSpot/Snowflake/etc.):
[tool + test credentials + whether MFA is enabled]

**Multi-user testing:** [credentials for any additional accounts needed, or "not needed"]

**Backend access:** defaults to read-only Rails queries unless you say otherwise — reply only if
you want to grant more (background jobs) or less (none)

**Jira epic to file under (only if you already know you'll want Jira filed later):** [epic, or
"decide later"]
```

Parse the single reply against 0.2-0.10 below. If something critical is missing or ambiguous (most
commonly: squad match, or the exact base URL), ask **one** consolidated follow-up covering just the
gaps — never revert to asking item-by-item.

### Touchless mode: auto-discover first, then one final ask

Before asking the user anything beyond the initial scope/mode question, attempt to resolve as many
of 0.2-0.10 as possible on your own:

- **References (0.3):** if a Notion bug-bash/feature page, Jira epic, or GitHub PR was already given,
  crawl it for linked ERD/PRD/Figma/Jira/Slack mentions instead of asking for each separately. Check
  `playwright/src/e2e/` yourself regardless of mode (already the default).
- **Squad (0.2):** attempt to infer from context (team/channel names, Jira project, prior runs) —
  but this still needs at least a lightweight confirmation from the user before it's settled, since
  it determines a real, hard-to-reverse Notion write location. Bundle "is squad X correct?" into the
  final ask rather than a separate round.
- **Primary credentials (0.6):** check for an existing saved auth/storage state first (per
  `manual-test-execution` §1.5's `state-load` option) before asking for a password.
- **Account capability prerequisites (0.7):** if backend/admin access is already available (e.g. from
  a prior step in this same run), check feature-flag state and plan tier yourself before asking.
- **Multi-user necessity (0.9):** infer whether multi-user testing is even needed from the feature
  description/research (collaboration, sharing, permission-comparison features) rather than asking
  — but still ask for credentials for any additional account, since those can't be invented.
- **Backend access level (0.10):** just apply the read-only default; don't ask unless something later
  genuinely requires more.
- **Environment URL (0.5) and credentials (0.6, 0.8):** never invent missing values. Reuse an exact
  URL or primary Apollo test-account credentials already supplied in the current conversation
  without reconfirming their use. Third-party credentials remain an explicit confirmation gate.

Once auto-discovery is exhausted, present one short summary ("Here's what I found/assumed: ... Here's
what I still need from you: ...") and wait for a single reply covering the remainder.

### 0.2 Squad DB confirmation (hard gate before Phase 2 can create anything)

Read and follow `references/notion-squad-matching.md` in full before
proceeding. In short: ask for the squad name once per run (assume one squad per campaign by default;
ask again if a specific feature genuinely needs a different one), match it against the real Teams DB,
and either confirm a single clean match back to the user in one line or — if zero or multiple
candidates — **stop and ask for the exact squad name**. Never guess between ambiguous candidates, and
never create a new Teams DB row or a new database as a workaround. **Phase 2 cannot create a Notion
test plan page until this step resolves.**

### 0.3 Reference links (accept whatever exists — do not hard-gate)

Ask the user what's available, itemized rather than as one vague "any references?" ask — go through
each of these explicitly (skip only the ones the user says don't exist):

- **Notion page(s):** the bug-bash/feature page itself, plus linked PRD and ERD if separate.
- **Jira:** the epic (and any linked sub-tasks/tickets) for implementation context and readiness —
  distinct from whichever epic bugs might later be filed under, if Jira filing is ever explicitly
  requested (see the Jira filing rules referenced from Phase 4) — the two may or may not be the same.
- **Figma:** design/UI spec link(s).
- **GitHub PR(s):** the implementation PR(s), for `gh pr view` analysis.
- **Slack — project/discussion channel(s):** where the feature was scoped/discussed day-to-day.
- **Slack — PR-review channel:** often a *different* channel than the project one (e.g. a
  team's code-review channel) — ask for it separately; it's frequently where descoping/"don't merge
  this yet" context actually lives, not the general project channel.
- **Anything else:** any other document, meeting notes, or prior conversation the user wants
  factored in that doesn't fit the categories above — explicitly ask, don't assume there's nothing.
- Whether existing Playwright specs already cover parts of this feature (check
  `playwright/src/e2e/` yourself too, don't only rely on the user knowing).

Unlike `bug-bash-generator`'s Step 1/2, **missing links are not a stopping condition** — note what's
absent and adapt Phase 1's depth to what's actually available. A feature with no Jira epic and no
Figma is a valid input; say so in the eventual test plan's "Readiness notes" rather than refusing to
proceed.

### 0.4 MCP connection check (before asking anything else)

A missing tool connection discovered mid-run — failing to fetch a Notion board after gathering
research context, or failing to create the Notion test plan after execution — wastes real work and
breaks the seamless, uninterrupted run this skill is meant to provide. Check this now, before
proceeding, based on what §0.1/§0.3 actually indicated is needed — don't blanket-require every
integration regardless of relevance:

- **Notion MCP — always check.** Unlike everything else in this list, this one is unconditional:
  every run creates a real Test Plan page and Bugs DB rows in Notion regardless of what other
  references exist, so this connection is never optional.
- **Notion evidence upload — always check.** Prefer native Notion file-upload and attachment tools
  when both are callable; inspect their live schemas rather than guessing parameters. If they are
  absent or unusable, fall back to a real, logged-in browser against Notion's UI using a separate
  persistent `playwright-cli` session (same `state-load` pattern as `manual-test-execution` §1.5).
  Preflight that fallback authentication before app execution. If no saved Notion session exists,
  tell the user that evidence upload needs a one-time headed manual login, then `state-save` it for
  this and future runs. A working semantic Notion connection alone does not prove local-file upload
  works.
- **Jira/Atlassian MCP — not checked here.** Filing is opt-in-only now (per `jira-filing-rules.md`)
  — check this connection at the moment Jira filing is actually requested instead, not upfront, since
  most runs never touch it.
- **Figma MCP** — check if a Figma link was indicated.
- **Slack MCP** — check if a Slack channel (project or PR-review) was indicated.
- **Glean** — check if the "anything else" answer in §0.3 points at some other document or
  conversation that would need enterprise search to locate.

Use `ToolSearch` (or equivalent tool-discovery mechanism) to confirm the relevant MCP tools are
actually present in this session's toolset. If something needed is missing, tell the user plainly
which connection is missing and why, and ask them to connect it before continuing — don't assume the
skill can auto-connect it, since that varies by environment (some expose an explicit `authenticate`
tool per integration, others require the user to configure it outside the conversation). Once
confirmed connected (or the user says that source isn't needed after all), proceed.

### 0.5 Environment tier + URL

Ask **staging or production** before anything else environment-related — don't assume:

- **Staging:** ask for the exact base URL. Never guess or reuse a URL from a prior run/example —
  environments and hostnames vary per account/region (e.g. a `preview`/`staging` hostname is not
  interchangeable across teams).
- **Production:** confirm the exact production base URL to test against as well — still ask, don't
  assume the "obvious" prod URL is the right one for this account.

**VPN check, right here, not deferred to Phase 3:** once the base URL is known, if it contains
"preview" (case-insensitive) or otherwise looks VPN-gated, ping it now —
`curl -s -o /dev/null -w '%{http_code}' --max-time 10 <base-url>` — as part of this same upfront
round, before Phase 1 research even starts. If it's not reachable (not 200, or the request fails),
tell the user plainly and ask them to connect to VPN and confirm ready before proceeding — surfacing
this now means research and test-plan drafting don't happen only to hit a VPN wall right before
Phase 3 execution. Phase 3 still re-checks quickly before touching the browser (connections can drop
over a long session), but that's a fast re-verify, not the first time this comes up.

### 0.6 Resolve primary account authentication once per run

Reuse a saved authenticated session or login/password already supplied in the conversation. If
authentication is still missing, request login and password together in the consolidated ask, not a
separate round-trip. Never guess a URL or credential.
**Regardless of how it's received, never echo, log, or write the password anywhere afterward** — that
rule is about what happens *after* the password arrives, not about how it's collected. If the user
would rather not paste a password into chat at all, they can reply "I'll log in myself" instead, which
falls back to `manual-test-execution` §1.5's manual-login pattern (headed browser, user logs in).

### 0.7 Account capability prerequisites

Ask which of these apply to the feature(s) in scope — each one silently blocked entire test runs in
the campaign this skill is modeled on, so surface them upfront rather than discovering them as
confusing failures mid-run:

- **Feature flag(s):** does this feature sit behind a flag? If so, is it already enabled on the test
  account, or does the user need to confirm/enable it before Phase 3 starts? **Never flip a flag
  yourself** — same never-auto-fix rule as Phase 4's environment-blocker handling applies here too;
  surface it and let the user decide.
- **Plan tier:** does any test case require a paid/upgraded plan rather than free tier? If yes, ask
  the user to **provide credentials for an account already on that plan** — do not ask to upgrade a
  shared or free account yourself, since a plan/billing change is exactly the kind of hard-to-reverse,
  shared-state action this skill must never take on its own initiative.
- **Credits/quota:** for AI-generation, enrichment, or other metered/credit-consuming features,
  confirm the test account has enough balance for the planned run — ask, don't assume, and don't
  spend real credits discovering this the hard way mid-execution.

### 0.8 Third-party integration credentials (if in scope)

If any test case involves a CRM, data-warehouse, or sales-engagement integration (Salesforce,
HubSpot, Snowflake, Outreach, Salesloft, or similar), ask for:

- Test credentials for that specific tool, separate from the primary Apollo test account.
- Whether MFA/2FA is enabled on that integration account. If so, confirm the user will complete the
  challenge themselves when prompted, in a headed browser (same manual-step pattern as
  `manual-test-execution` §1.5) — don't assume it's bypassable or skip planning for it.

### 0.9 Multi-user testing (if in scope)

If any test case needs 2+ concurrent or interacting user accounts (collaboration/sharing flows,
role-permission comparisons, or simply running multiple parallel test streams), ask for credentials
for **each** additional account upfront — don't discover the need for a second user mid-run. Prefer
genuinely separate dedicated accounts over reusing one shared login across concurrent test streams: a
shared login means shared workspace data, not just separate browser sessions, and caused real
collisions in the campaign this skill is modeled on.

### 0.10 Backend/Rails access level (if backend verification is expected)

If Phase 3/4 is expected to cross-check state directly in Rails rather than only through the UI,
confirm upfront what's permitted: read-only queries only, running background jobs, or no backend
access at all. Default to read-only-only unless the user explicitly grants more, and never assume
write access to a shared environment.

### 0.11 Explicit scope-skip rule

If something looks not-actually-ready (flag off, ticket cancelled, no UI exists), don't guess —
verify via Jira/Slack status where possible, and explicitly record what was skipped and why, rather
than silently omitting it from the plan.

______________________________________________________________________

## Phase 1 — Research (per feature)

Apply `bug-bash-generator`'s **Step 3** analysis substeps
(`${CLAUDE_PLUGIN_ROOT}/skills/bug-bash-generator/SKILL.md`)
against whichever sources exist for this feature: ERD, PRD, Figma, Jira epic, GitHub PR, Apollo
knowledge base. Read `erd-proposed-delta-pass.md` when schema/config-level changes are in scope, and
`automation-risk-checklist.md` when schedules/background jobs/sync/dedup are in scope. Also scan the
Bug Bash/initiative page and any linked implementation notes for explicit callouts (known bugs,
descoped items, "fix before X" comments) per that same Step 3-I.

**Difference from `bug-bash-generator`:** do not force all 5 doc types. Work with what's there, and
say explicitly in the test plan what wasn't available and why that's acceptable (or isn't).

Always check `playwright/src/e2e/` for existing automated coverage first — scope manual testing
effort toward gaps and real-integration verification, not toward re-covering what's already
automated.

______________________________________________________________________

## Phase 2 — Test plan (per feature)

**Test plans are created directly in Notion now, not as local markdown** — per the mandatory rule
that bugs and test plans must live in the same, real Notion location the team already uses. This
phase has two steps:

**Existing-case fast path:** when the user supplies an existing Test Plan/Test Case and asks to
execute or mark it pass/fail, fetch and verify that artifact, then use it as the canonical scenario
source. Do not draft duplicates, create new Notion rows, or ask for the creation go-ahead in 2.1.
Proceed to Phase 3 as soon as the required execution inputs are resolved.

### 2.1 Draft and get go-ahead (chat only, no Notion writes yet)

Draft the test case list and a short gap self-review (5-10 high-risk areas and whether each is
covered, borrowed from `bug-bash-generator`'s own gap-review habit) **in chat**, in this shape:

```markdown
**Test Plan — [Feature Name]**
Environment: [base URL] · Squad: [confirmed squad from 0.2]

Readiness notes:
- [What sources were available/unavailable and how that shaped this plan]
- [Anything ambiguous that needed empirical discovery rather than a documented spec]

Test cases:
| ID | Title | Priority | Steps | Expected |
|---|---|---|---|---|
| TC-[PREFIX]-01 | ... | P0/P1/P2 | ... | ... |

Explicitly skipped (not ready):
- [Each skipped area, with the reason and how it was verified not-ready]
```

Get one explicit go-ahead before writing anything to Notion or touching a browser. This is lighter
than `bug-bash-generator`'s MODIFY/ADD/PRIORITIZE loop — one confirmation is enough here, since the
user can still redirect mid-execution if something looks wrong.

### 2.2 Create the real Notion artifacts (only after go-ahead)

Read and follow `references/notion-test-plan-and-cases.md` in
full for this step — it has the exact `data_source_id`s, the required `template_id`, and the precise
property/content conventions. In short:

1. Create the **Test Plan page** as a new row in the Test Plan DB, using `template_id` (never
   hand-authored `content` for this page — the template's linked "Add New Or Execute Test Cases" and
   "Bugs found" views only auto-scope correctly when applied via `template_id`). Set `Name`, `Squad DB` (the confirmed squad from 0.2), and whatever `Epic`/`PRD`/`ERD`/`Figma`/`GitHub PRs` links
   exist.
1. Fill in the real Scope/Out of scope/Test Environment content via `notion-update-page`
   (`update_content`) against the template's placeholder text — never touch the auto-generated
   linked-database blocks.
1. Create the **Test Case DB rows** for the approved case list, reusing `bug-bash-generator`'s exact
   JSON convention (`${CLAUDE_PLUGIN_ROOT}/skills/bug-bash-generator/references/notion-upload-format.md`),
   with `Feature` set to this new Test Plan page's URL. Skip that doc's own sample-then-bulk gate —
   the chat go-ahead in 2.1 already served that purpose.
1. Report back to the user: the Notion Test Plan page URL, the confirmed squad, and the test-case
   count created. Never create a new database, a new squad DB entry, or a new property to work around
   any gap — ask the user instead.

______________________________________________________________________

## Phase 3 — Execute (per feature)

Follow `manual-test-execution`'s mechanics directly
(`${CLAUDE_PLUGIN_ROOT}/skills/manual-test-execution/SKILL.md` §2-4) — **do not** re-ask for scenario
source or re-collect credentials, both are already known from Phase 0/2:

- Execution authorization: when the user has already asked to run/execute/test against an
  Apollo-owned test environment and supplied the exact URL plus usable primary credentials (or a
  saved authenticated session), begin without another "start" prompt. Ask only when authorization
  is genuinely missing, the target's ownership is ambiguous, or authentication touches a
  third-party system. Never echo the password while acknowledging readiness.
- VPN re-check: this was already resolved once in 0.5, upfront — just a quick re-ping here in case
  the connection dropped over a long session; wait for the user if it's now unreachable.
- Execution: `playwright-cli` only — open → video-start → goto → snapshot → interact → assert.
- Recovery: don't give up on the first blocker if the UI offers a path forward — same
  don't-give-up-early rules as `manual-test-execution` §3.
- Artifacts: screenshots for every failed step, video for the whole run, per
  `manual-test-execution` §4.1-4.2 — **plus** a network trace/HAR for every failure (this skill's
  evidence bar is higher, matching the campaign's actual practice, since these reports need to be
  debuggable by someone who wasn't in the session).
- **Trace/HAR credential safety (required):** a network trace/HAR captures raw request bodies and
  headers — unlike video, where a password field just renders as masked dots, the login request's
  body contains the literal plaintext password, and later requests may carry session
  cookies/`Authorization` tokens. This directly conflicts with the never-write-password rule
  (Interaction principle #3) unless handled:
  - Prefer scoping trace/HAR capture to start **after** login completes, so the login request is
    never in the capture at all. Cover the login step itself with screenshot/video only.
  - If capture must span the whole session (e.g. one continuous trace per `manual-test-execution`
    convention), before saving the file into the report: open it, find the login request, and
    overwrite the password field's value (and any `Authorization`/`Cookie`/session-token header
    values anywhere in the capture) with a placeholder like `[REDACTED]` — then delete the raw
    unscrubbed capture. Never keep both.
  - If you can't confirm a trace/HAR is fully scrubbed, don't attach it — not to the local report,
    and not to Notion in Phase 4. Describe the relevant request/response in prose instead (status
    code, response body) and note in the report that raw network evidence was withheld for
    credential safety.
  - A trace/HAR that **is** confirmed scrubbed gets attached in Phase 4 alongside the
    screenshot/video, per `notion-bugs-and-evidence.md`'s "Attaching real evidence" section — same
    `Files & media` property, same `playwright-cli upload` mechanism. This is genuinely useful evidence
    (exact request/response bodies, status codes, timing) that a screenshot/video can't show.
- Write `report.md` in the run folder per `manual-test-execution` §4.3.

______________________________________________________________________

## Phase 4 — Bug logging (Notion always; Jira only on explicit request)

**Default behavior: Notion first, Jira optional.** Every genuine bug found this feature gets logged
to Notion, unconditionally, every run — this is not discretionary and never gets skipped in favor of
Jira.

### 4.0 Update Test Case DB rows with the run outcome (mandatory, every executed case)

Read and follow `references/notion-test-case-status.md` in full. In short: every Test Case row that
Phase 3 actually executed gets its `AI Status` property set to `Pass`/`Conditional Pass`/`Fail` —
whichever this run really produced — so a viewer can see execution status directly on the row instead
of it looking untouched forever. Cases genuinely not reached this run stay at the default `Not tested`; don't touch those.

Also read and follow `references/notion-bugs-and-evidence.md`'s **Executed Test Case evidence**
section. Upload the report, applicable screenshots, video, and only confirmed-scrubbed trace/HAR to
the Test Case's existing file property for every executed outcome, including Pass. Verify the files
appear on the row. Keep the functional result separate from evidence delivery: if upload cannot be
completed, retain the truthful Pass/Fail/Partially pass value but mark **Evidence upload: Pending** in
the Notion run summary and local report. Do not describe the run as fully complete until that is
resolved.

### 4.1 Genuine bug vs. environment/access issue

Same distinction as before: a **genuine product defect** (still wrong for the next person regardless
of this run's environment state) gets logged. An environment/access blocker that got **resolved
during this same run** (flag enabled, quota raised, credential reconnected) is not a bug — note it in
the eventual `MASTER-SUMMARY.md` cross-cutting findings instead, unless the blocker itself revealed a
real product gap (e.g. zero user-facing error on hitting a limit) — file *that* as its own genuine bug.

### 4.2 Log every genuine bug to Notion (mandatory, every run)

Read and follow `references/notion-bugs-and-evidence.md` in full.
In short: one lightweight confirmation (list the bugs found,
confirm before writing — this is default expected behavior now, not a discretionary gate, so it's
lighter than the old Jira confirmation), then create a Bugs DB row per genuine bug with `Feature` set
to this feature's Test Plan page URL (this is what makes it appear under that page's "Bugs found"
section — a relation value, not manually-placed content), `Jira` left blank, and `content` written as
the full write-up (same shape as `bug-report-template.md`'s per-bug section — Description/
Environment/Preconditions/Repro/Expected/Actual/Impact), not an abbreviated summary. Then attach this
bug's real screenshot(s)/video, and its scrubbed trace/HAR if one was confirmed scrubbed per Phase 3's
credential-safety rule, to the row's `Files & media` (or `Screenshot`) property per that same doc's
"Attaching real evidence" section — driving a real, Notion-authenticated `playwright-cli` session to
upload the actual local file. Use the native-first upload flow and authenticated-browser fallback
defined in that reference. Evidence lives in Notion now; don't fall back to a text-only local-path
reference.

Also write the secondary local `bug-report-<feature-slug>.md` per
`references/bug-report-template.md` — a companion local backup
alongside the canonical Notion rows, not the primary place either the write-up or the evidence lives.

**Never** auto-fix an environment/access blocker (flags, billing/plan state, credentials) as a side
effect of testing — surface it and ask.

### 4.3 Jira filing (only if explicitly requested — never automatic)

Jira ticket creation does **not** happen as part of this phase's default flow. If the user or team
explicitly asks for it at any point — during this phase, later in the run, or after the whole
campaign — read and follow `references/jira-filing-rules.md` in
full. It covers the MCP check (done at request time, not upfront), the confirmation gate, filing
mechanics (ticket body reused from the Notion bug row's own content), and the mandatory Notion
link-back step (`Jira` property on that same row gets set to the new ticket URL — never a
duplicate/new record).

______________________________________________________________________

## Phase 5 — Campaign rollup

Once every in-scope feature has had its execution and Notion bug logging completed (per Phase 4 —
this always happens, every run), read and follow
`references/master-summary-template.md` to write
`MASTER-SUMMARY.md`, and `references/automation-handoff-template.md`
to write `E2E-AUTOMATION-HANDOFF.md`, both to `playwright/reports/ai_manual/`. In campaign mode,
update `MASTER-SUMMARY.md` incrementally as each feature finishes rather than only at the very end.

`MASTER-SUMMARY.md`'s **"Bugs logged to Notion" section is always present** (default behavior) — total
count, link back to the squad's Test Plan view. Its **"Jira tickets filed" section is conditional** —
include it only if Jira filing was actually requested and performed at some point this campaign (per
`jira-filing-rules.md`); omit it entirely otherwise, since Jira being untouched is the expected
default, not a gap needing explanation.

______________________________________________________________________

## Interaction principles

1. **Batch intake, not one question at a time:** default to touchless auto-discovery, infer scope from
   the supplied source, and use one consolidated ask only for unresolved inputs. Use Guided mode only
   when the user requests it.
1. **Ask only for meaningful gates:** resolve ambiguous squad writes, get the Phase 2 go-ahead only
   when creating new Notion test artifacts, confirm unrequested third-party authentication, and get
   the Phase 4 Notion bug-logging confirmation after finding bugs. Do not add a Phase 3 start gate
   when the user already requested execution against an Apollo-owned test environment with complete
   inputs.
1. **Never** echo, log, store, or write the password anywhere.
1. **Never** silently auto-fix a shared-system blocker (feature flag, billing/plan, credential) —
   that's exactly the kind of hard-to-reverse, shared-state action that needs the user's call.
1. **Never** create a new Notion database, a new squad DB entry, or a new property to work around a
   gap in the existing structure — ask the user instead. The existing structure is preserved exactly,
   always.
1. **Notion first, Jira optional, always:** every genuine bug gets logged to Notion every run,
   unconditionally. Jira filing never happens unless explicitly requested with a named epic, and
   never as a substitute for the Notion logging step.
1. Report outcomes faithfully — a failed step or a genuine bug is reported as such, not hedged; but a
   thing that turns out to work despite a stale "cancelled"/"known bug" ticket status is reported
   just as plainly as a positive surprise.
