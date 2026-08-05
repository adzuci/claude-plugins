---
name: manual-test-execution
description: >-
  Execute manual test scenarios against a running web app by driving the UI with
  playwright-cli, producing an auditable report.md + failed-step screenshots + video under
  playwright/reports/ai_manual/[run_id]/, and (when scenarios come from Notion) writing the
  run summary and _AI-tested_ status back to each Test case page via the Notion MCP.
  Use whenever the user asks to "run manual tests", "execute manual test scenarios",
  "manual test execution", "run the test plan", "run test cases from Notion",
  "AI-execute these test cases", "test this scenario in the browser", or pastes a Notion
  test-plan/test-case URL and asks to execute/verify it against an environment. Also
  trigger on "run P0s from this page", "verify this flow manually", or any request to
  drive a manual QA scenario end-to-end in a real browser and produce a test report.
  Do NOT use for writing automated Playwright test code (use playwright-testing) or for
  merely reading/listing bugs and test cases from Notion (use notion-bugs-and-tests).
---

# Manual Test Execution — AI-Driven Manual QA Runs

You execute **manual test scenarios** by driving the UI with **`playwright-cli` only** (see the `playwright-cli` skill for command reference). Follow this checklist precisely for consistent, secure, and reportable runs.

Migrated from `.cursor/commands/manual-test-execution.md`. Canonical usage doc:
[Manual Test Execution – Usage Documentation](https://www.notion.so/apolloio/30bab2b3b496813cb43fe736302f9158).

## Unified checklist (order of operations)

- [ ] **Scenario source:** Notion URL → ask test types (P0/P1/P2/All), fetch via Notion MCP. Else → ask user for scenario text (steps + expected results).
- [ ] **Credentials:** Reuse the base URL, login, password, or saved authenticated session already supplied in the current conversation; ask only for missing values. **Never echo or log the password** (use only for typing into the UI). Offer the manual-login alternative (§1.5).
- [ ] **Execution authorization:** An explicit request to run/execute/test against an Apollo-owned test environment, together with the exact URL and usable authentication, authorizes browser execution. Do not ask for a redundant "start" confirmation. Keep an explicit confirmation gate for third-party authentication, ambiguous ownership, or when the user has not actually asked to execute.
- [ ] **VPN gate:** If base URL contains `preview` (case-insensitive), `curl -s -o /dev/null -w '%{http_code}'` it. If not 200, ask the user to enable VPN and wait for "ready".
- [ ] **Execute:** `playwright-cli` only (open → goto → snapshot → click/fill/type → wait → assert via snapshot). Start video recording first. No other browser/automation tools.
- [ ] **Artifacts:** Failed-step screenshots → `playwright/reports/ai_manual/[run_id]/screenshots/`; video → `.../video/`; full run → `.../report.md`.
- [ ] **Notion evidence capability (Notion source only):** Before app execution, verify native Notion
  local-file upload tools are callable or preflight an authenticated Notion browser fallback. Do not
  assume semantic page-write access can upload local files.
- [ ] **Report:** PASS / FAIL / PARTIAL; document every step and every issue. Never guess URL, login, or password — ask if missing.
- [ ] **Notion Test case pages (only when scenario source was Notion):** After **each** executed case,
  **mandatorily** (1) append an "AI Manual test run summary (AI-executed)" section with Run ID, date,
  result, steps, brief summary, and evidence-upload state; (2) set the **`_AI-tested_`** property to
  **Pass**, **Partially pass**, or **Fail** for THIS run — never leave a stale value; and (3) upload
  the report, applicable screenshots, video, and only confirmed-scrubbed trace/HAR to the existing
  Test Case file property. Skip entirely when the scenario was user-provided.
- [ ] **Notion test plan / workflow status (Notion source only):** If the Test case or parent test plan exposes workflow status properties (e.g. **QA in progress**, **In progress**, **In review**), update them with the run lifecycle. Ask the user once which property names to use if ambiguous.

______________________________________________________________________

## 1. Input handling — gather before any browser actions

Use **AskUserQuestion** only for unresolved structured choices that materially affect execution. Collect missing free-text inputs (URLs, login) in chat, but reuse values already present in the conversation.

### 1.1 Determine the scenario source

- **Notion page URL provided** → fetch scenarios via **Notion MCP**.
- **No Notion URL** → ask for the test scenario text (steps + expected results) in chat.

### 1.2 If a Notion page URL is provided

1. **Resolve which cases to execute:** if the user supplied a specific Test Case or already named the
   priorities/types, use that scope. For a broader Test Plan with no selection, ask once for P0, P1,
   P2, or All.
1. **Fetch scenarios efficiently:** if the page embeds a test-case database, follow the `notion-bugs-and-tests` skill's query rules — `notion-fetch` the page to get the data-source ID, then **one `notion-query-database-view` call** (`page_size: 100`, paginate on `has_more`) rather than fetching case pages one-by-one. Fetch individual case pages only for the cases you will actually execute (you need their step details and page IDs for the write-back).
1. If priority markers are missing/ambiguous, map: **P0** = critical path / must-run; **P1** = important non-blocking; **P2** = nice-to-have / edge cases. Document mapping assumptions in the report.

### 1.3 Resolve base URL + credentials

First inspect the current conversation and available saved authentication state. Ask once for only
the missing items:

1. **Base URL** — "Please provide the base URL for this test environment (e.g. https://app.example.com)." Never guess URLs.
1. **Login** — "Please provide the login (email or username) for the test user relevant to this scenario."
1. **Password** — "Please provide the password for the test user. I will not echo it back."

Use the password only for typing into the UI via `playwright-cli fill`. Never print it in output, reports, shell commands visible in logs, or Notion.

For an Apollo-owned test environment (including Apollo staging or preview hosts), supplied primary
test-account credentials are authorization to authenticate for the requested test. Do not ask the
user to reconfirm credential use. Treat third-party credentials separately: confirm before using
them unless the user explicitly requested that exact third-party login in the same execution request.

### 1.4 Parse scenarios into executable steps

Whether from Notion or chat, extract for each scenario:

- **Preconditions** (user exists, feature flag, seeded data)
- **Step list** with explicit UI actions
- **Expected results per step** (what you will assert)
- **Stop conditions:** abort immediately on P0 failure; continue past P1/P2 failures unless continuing becomes impossible (document why).

### 1.5 If the user declines to share a password

Explain you need it only to type into the app and that you won't store or echo it. If they still decline, use the manual-login path: note it during input gathering, complete the VPN check (§2), open a **headed** browser with `playwright-cli open --headed <base-url>` (default is headless — the user can't see or interact with it), ask the user to log in themselves in the visible browser window, and continue from the post-login state once they confirm. (You may also offer `playwright-cli state-load auth.json` if they have a saved storage state.)

______________________________________________________________________

## 2. Execution authorization + conditional VPN check

1. **Execution authorization:** If the user explicitly asked to run/execute/test, the target is an Apollo-owned test environment, and the exact URL plus usable authentication are available, proceed directly. A separate browser-start confirmation is not required. Ask once before browser actions only when the user has not requested execution, target ownership is ambiguous, or third-party authentication is required and was not explicitly authorized.
1. **VPN gate:** If the base URL contains the substring `"preview"` (case-insensitive):
   - `curl -s -o /dev/null -w '%{http_code}' --max-time 10 <base-url>` before any navigation.
   - **Not 200 (or request fails):** tell the user: "The URL contains 'preview' and the base URL is not reachable. Please enable VPN (or ensure you are on the correct network) and reply 'ready' to proceed." Wait for confirmation; optionally re-ping; only then proceed.
   - **200:** don't mention VPN; proceed.
1. URL without "preview": no ping, no VPN mention.

______________________________________________________________________

## 3. Execution — playwright-cli only

- **Use only `playwright-cli`** for all test actions (see the `playwright-cli` skill). Do not use any other browser or automation tool for the test itself.
- **Typical flow per run:**
  1. `playwright-cli open` then `playwright-cli video-start` (record the whole run).
  1. `playwright-cli goto <base-url>` and log in (fill login/password using snapshot refs).
  1. Per step: **snapshot → interact (click/fill/type/select/press) using exact refs → wait → assert** by re-reading the snapshot (and screenshots at key points).
  1. After actions that change the page (submit, navigation), take a fresh snapshot before the next interaction.
  1. At the end: `playwright-cli video-stop playwright/reports/ai_manual/[run_id]/video/run.webm` then `playwright-cli close`.
- **Best practices:** prefer semantic, stable targets (roles, labels, test ids) exposed by the snapshot; prefer waiting for content over fixed sleeps.
- **Recovery — do not give up early (required):**
  - Do **not** stop on the first missing element or empty state if the UI offers a path forward (e.g. "No AI sheet found", "Create…", empty lists with **Add**/**New** buttons).
  - Re-read the latest snapshot after each failure; treat visible copy, banners, and primary buttons as instructions — if the page explains how to create the missing resource, perform that flow and retry the original step.
  - Only stop when the scenario says abort, the blocker has no actionable UI path after a reasonable attempt (document what you tried), or continuing would violate credential/security rules.
  - In `report.md` under **Issues encountered**, note recovery attempts (what you read, what you clicked, outcome) before marking a step **Fail**.

______________________________________________________________________

## 4. Reporting + artifacts

### 4.1 Artifact locations (required)

At run start, create a run id via `date -u +%Y%m%d-%H%M%S`: `ai_manual-test-YYYYMMDD-HHMMSS`.

All artifacts under `playwright/reports/ai_manual/[run_id]/`:

- **Screenshots:** `screenshots/` — failed steps named `stepNN-FAILED-[slug].png`
- **Video:** `video/`
- **Report:** `report.md`

### 4.2 Screenshot capture rules (required)

- On **every failed step**, immediately `playwright-cli screenshot --filename=playwright/reports/ai_manual/[run_id]/screenshots/stepNN-FAILED-[slug].png`.
- For transient UI failures (tooltips, hover menus, toasts), take **two** screenshots: immediately after the action, and again after 1–2 seconds.

### 4.3 Report template (write to `report.md`)

```markdown
## Manual Test Execution Report

**Date (UTC):** [ISO date/time]
**Run ID:** [run_id]
**Base URL:** [URL – never include password or credentials]
**Scenario source:** Notion / User-provided
**Notion page:** [URL if used, else "N/A"]
**Selected test types:** P0 / P1 / P2 / All (if Notion used, else "N/A")
**Test user login:** [login only]

### Summary

- **Status:** PASS / FAIL / PARTIAL
- **Steps executed:** [number]
- **Steps passed:** [number]
- **Steps failed:** [number]

### Steps executed

| Step | Priority | Action | Expected | Result     | Notes | Artifact                 |
| ---- | -------- | ------ | -------- | ---------- | ----- | ------------------------ |
| 1    | P0/P1/P2 | ...    | ...      | Pass/ Fail | ...   | [screenshot path if any] |

### Issues encountered

- [Each issue: element not found, wrong state, timeout, wrong content, etc. Include step number, what was observed, and recovery attempts. "None" if clean.]

### Screenshots / artifacts

- **Screenshots folder:** [path]
- **Video:** [path]
- **Report file:** [path]
- [Each screenshot path with a short description.]

### Notion test cases update

- [Notion source: per executed case — link + what was appended + `_AI-tested_` value set + attached
  filenames + evidence state (`Uploaded` or `Pending: reason`). User-provided source: "N/A — scenario
  was user-provided; no Notion pages to update."]

### Recommendations

- [Optional: fixes for failures, scenario improvements, re-run suggestions.]
```

Status meaning — **PASS:** all steps completed and expectations met. **FAIL:** one or more critical steps failed or expected content missing. **PARTIAL:** mixed results where partial success is meaningful. Fill every section.

### 4.4 Notion write-back (required when scenario source is Notion)

For **each** executed Test case page, in the same session as the run completes:

1. **Append** a section **"AI Manual test run summary (AI-executed)"** with: Run ID, Date (UTC), Base URL, Result (PASS/FAIL/PARTIAL), steps executed/passed/failed, a short bullet summary, and **Evidence upload: Uploaded** with filenames or **Evidence upload: Pending** with the exact blocker (use `notion-update-page`).
1. **Set the `_AI-tested_` status property** — allowed values: **Not tested**, **Partially pass**, **Pass**, **Fail**. Map: all critical expectations met → Pass; mixed → Partially pass; blocked or critical miss → Fail. Never finish a Notion-sourced run without writing this for every executed case; treat a stale value from a prior run as a bug and fix it. If the property doesn't exist on the database, create it (Status type) via `notion-update-data-source`.
1. **Upload real evidence to the Test Case row.** Read and follow
   `${CLAUDE_PLUGIN_ROOT}/skills/end-to-end-bug-bash/references/notion-bugs-and-evidence.md`'s
   **Executed Test Case evidence** section. Do this for Pass, Fail, and Partially pass outcomes. Never
   replace the attachment with a local path in page text. If upload is blocked, preserve the truthful
   functional result, record **Evidence upload: Pending** in both Notion and `report.md`, and do not
   claim the run is fully complete.
1. **Test plan / QA workflow status:** when the case or parent test plan exposes **In progress**, **QA in progress**, **In review**, or similar, align them with the run lifecycle (in-progress while testing; in-review or the team's "testing complete" equivalent when done). If multiple properties could apply, ask the user once which to drive. Note status changes in the report's Notion section.

When the scenario was user-provided, skip all Notion updates.

______________________________________________________________________

## 5. Interaction principles

1. **Touchless by default:** reuse supplied context, auto-discover safe prerequisites, and consolidate only genuinely missing inputs into one ask.
1. **No redundant start gate:** the user's execution request authorizes browser actions on the specified Apollo-owned test environment when required inputs are complete. Preserve confirmation for third-party authentication or genuinely ambiguous authorization.
1. **Never** echo, log, store, or write the password anywhere (output, report, Notion, shell history-visible commands).
1. Report outcomes faithfully — a failed step is a Fail with evidence, not a hedge.
