---
name: incident-triage
description: Manual-invocation only. Triage Jira INCIDENT tickets. Run via /apollo-eng-devops:incident-triage.
---

# Incident Triage

**Invoke directly.** This skill is not auto-activated. Run it as a slash command: `/apollo-eng-devops:incident-triage [args]`. The short description above is intentional — it keeps the skill out of Claude's auto-routing context across unrelated sessions.

You are triaging Jira `INCIDENT` (and adjacent `SEC` / `INFOSEC` / `ITBS`) tickets on behalf of the user. The queue is a mix — most volume is PagerDuty/Grafana alerts, but security findings, customer-reported degradations, and manual escalations all land here too. Your job is to classify each ticket, propose an action, and never mutate Jira without explicit per-row approval.

Audience: any Apollo engineer.

**Optimize for speed and correctness, in that order.** Concise scan first → ask batched questions → act. Don't autonomously charge into investigation paths the user can confirm or skip in one yes/no.

## Arguments

The slash command accepts positional and named arguments. All are optional — with no args, the skill prompts via `AskUserQuestion`.

```
/apollo-eng-devops:incident-triage [<mode>] [<scope>] [--team <slug>] [--jql "<JQL>"] [--filter <id>] [--limit <N>] [--dry-run]
```

| Argument | Values | Default | Meaning |
| ------------------- | ------------------------------------------------- | -------------------------------- | -------------------------------------------------------------------- |
| `<mode>` (pos. 1) | `report` / `triage` / `pd-reconcile` | prompt | What kind of pass to run |
| `<scope>` (pos. 2) | `unassigned` / `mine` / `team` / `custom` | `unassigned` (DevOps default) | Which JQL slice to fetch |
| `--team <slug>` | An `apollo-dev-teams.yml` slug | resolved via identity | Override the team for `team` scope |
| `--jql "<JQL>"` | A raw JQL string | — | Forces `scope = custom`. Quote it. |
| `--filter <id>` | A Jira filter id | `11741` when `scope = unassigned` | Override the filter for `unassigned` or `custom` scope |
| `--limit <N>` | Integer | 50 | Cap rows fetched (the triage table gets unreadable past ~30) |
| `--dry-run` | flag | off | Forbid all Jira writes even after approval — for demos and previews |

Examples:

- `/apollo-eng-devops:incident-triage` → prompts for mode + scope
- `/apollo-eng-devops:incident-triage report` → report mode, DevOps unassigned queue
- `/apollo-eng-devops:incident-triage triage mine` → triage mode, my assigned tickets
- `/apollo-eng-devops:incident-triage triage team --team @apolloio/engagement-platform` → team mode for a specific team
- `/apollo-eng-devops:incident-triage pd-reconcile unassigned --limit 20` → PD reconciliation on the unassigned queue, capped at 20
- `/apollo-eng-devops:incident-triage triage custom --jql "project = INCIDENT AND labels = bugcrowd AND statusCategory != Done"` → triage all open Bugcrowd findings

Argument parsing happens at preflight. If positional args are ambiguous (e.g. unknown token in slot 1), the skill asks rather than guessing.

## Ticket classes

The first thing the skill does for every ticket is classify it. Each class has its own reference for extraction and routing.

| Class | Signals | Reference |
| ---------------------- | ------------------------------------------------------------------------------------------ | -------------------------------------------------------- |
| **PD / Grafana alert** | Title `[FIRING:N]` / `[RESOLVED:N]`; PD URL in body; reporter is a PD service account | [`references/pd-alerts.md`](references/pd-alerts.md) |
| **Security finding** | Label `kodem` / `orca` / `bugcrowd` / `panther` / `claude-security`; reporter is Security Automation | [`references/finding-sources.md`](references/finding-sources.md) |
| **Customer report** | Reporter is Support / GTM / external; body describes user-visible symptom | Symptom triage — see Workflow step 8 |
| **Manual / runbook ask** | Reporter is an engineer; body is a request or follow-up | Symptom triage — see Workflow step 8 |
| **Auto-classifier filing** | Reporter is `Apollo Agent` or `Quality Engineering` (svc account) | [`references/internal-tooling.md`](references/internal-tooling.md) |
| **No-class hygiene** | None of the above signals fire | Propose reporter clarification (`ask-reporter`) |

A ticket can be in more than one class. Pick the **strongest** class — manual review (Bugcrowd / claude-security / customer-named-impact) outranks automation (Kodem / Orca / PD / Panther). Auto-classifier filings always need verification — see `internal-tooling.md`.

## Recognition first, investigation second

Before fetching anything beyond the ticket list, scan each ticket for vendor names, exception classes, file paths, host patterns. Match against [`references/vendors.md`](references/vendors.md) and [`references/internal-tooling.md`](references/internal-tooling.md). Recognition collapses multiple investigation hops into one:

- Ticket mentions `Crawler::SearchEngineLinkedinPersonUpdaterWorker` → see `vendors.md` Shifter entry → known failure shape is "we self-spammed Shifter," verify with one Tempo rate query before assuming upstream outage.
- Ticket cites `remaining_export_credits` Redis key or `guard_for_sufficient_api_credits` → see `vendors.md` Redis Cloud entry → credit-gate 422, not an enrichment bug.
- Ticket from QE with `flaky_test` label → see `internal-tooling.md` Pantheon entry → read the failure quote in the description before trusting the label.

**Investigation only kicks in when recognition fails or contradicts the visible evidence.** Even then, ask before going deep — see "Investigation gating" below.

## Comment discipline: propose, never post

This is the load-bearing rule of the skill.

- Every proposed comment is shown inline in the numbered routing table (the "Proposed comment" column / sub-line), not in separate blocks. Each row has a number the user references to approve, reject, or revise.
- `addCommentToJiraIssue` is **never** called without an explicit `approve <n>` from the user **in the same session**.
- There is no "approve all comments" path. Comments are approved per row.
- `update <n>: <new text>` revises a row's comment before posting; re-print the row, still gated on a later `approve <n>`.
- Assignee changes (`editJiraIssue` setting `assignee`) follow the same per-row approval rule — but **PD-responder batch assignments** are an explicit exception, see "PD-assignment batching" below.
- Status transitions and issue links may be batched but only against rows the user has named (e.g. `approve all duplicates`, `approve 3,5`).
- Keep proposed comments to ≤ 3 sentences. Reporters respond to short messages.

If the user asks to "just post them," do not comply silently — re-print the numbered table and ask for one explicit confirmation naming the rows.

## Honesty over confidence

Wrong-but-confident routes cost more turns than "I'm not sure, let me verify." If a route depends on facts you don't have (current team allocation, recent CODEOWNERS change, vendor failure mode), say so and propose a yes/no investigation step. Routes proposed at low confidence must be marked `?` in the table.

## Modes

| Mode | Reads | Writes | Use when |
| -------------- | --------------------------------------------------------------------------- | --------------------------------- | --------------------------------------------------------------------------------- |
| `report` | Jira, Glean, PD (if available), Grafana (if available) | None | Stand-up summary, status check, exec readout |
| `triage` | Jira, Glean, PD (if available), Grafana (if available), GitHub (CODEOWNERS), `apollo-dev-teams.yml` | Jira (after per-row confirmation) | Weekly review session — default mode |
| `pd-reconcile` | Jira, PD read access (MCP or `pd` CLI, required), `apollo-dev-teams.yml` | Jira (after per-row confirmation) | Sync open Jira tickets with their linked PD incidents — assign responders + transition states |

### `pd-reconcile` mode

A focused pass for the PD/Grafana alert class only. Requires PD read access (MCP or `pd` CLI) per [`references/pd-access.md`](references/pd-access.md); if neither is usable, refuse and print the install command. The skill does not guess at PD state from Jira-side signals.

Workflow:

1. Find open Jira tickets in the chosen scope with a PD link (`pagerduty.com/incidents/` URL in description or comments, or label `pagerduty`). PD URLs often live in `description`/`comment`, which the compact field list omits — for `pd-reconcile` discovery, fetch `description` (and the last few comments) on the scoped rows so PD-linked tickets aren't missed. This is the one place the "don't fetch description by default" rule is relaxed, because PD links are the thing being discovered.
1. For each, fetch PD status and any PD notes/comments — via the MCP (`get_incident`, `list_log_entries`) when authorized, otherwise via the `pd` CLI (`pd rest get -e /incidents/<ID>`, `pd incident:notes -i <ID>`).
1. Before proposing any close/resolve transition, extract any Slack URL from the PD notes/log entries and follow it to confirm the context — verify there are no open action items in the thread. If a Slack link exists but can't be read, downgrade the proposal from Close to "Ask assignee to confirm + close" (see [`references/pd-alerts.md`](references/pd-alerts.md) → "Confirm Slack context before closing").
1. Apply the proposal table in [`references/pd-alerts.md`](references/pd-alerts.md) → "PD status reconciliation."
1. Print one numbered, compact row per ticket: PD status, PD responder (if any), proposed Jira assignee, proposed transition, any proposed comment inline, and a one-line reason.
1. **Batch the PD-responder assignments** — see "PD-assignment batching" below.
1. Stage all writes; require approval per row (`approve <n>`, `update <n>: …` to revise a comment first) or per batch as appropriate.

## Scope → JQL

Each scope resolves to JQL at preflight (see Arguments table for selection):

| Scope | JQL shape |
| ------------ | ------------------------------------------------------------------------------------------------------------- |
| `unassigned` | `filter = <id>` (default `11741`; override via `--filter`) |
| `mine` | `assignee = currentUser() AND project in (INCIDENT, SEC, INFOSEC, ITBS) AND statusCategory != Done` |
| `team` | Resolved from `--team` slug or identity-resolved slugs; maps to Jira component/team field per registry |
| `custom` | The string passed via `--jql`, or a filter via `--filter` |

## Required and Optional Tools

**Required**:

- Atlassian MCP (`searchJiraIssuesUsingJql`, `getJiraIssue`, `editJiraIssue`, `transitionJiraIssue`, `addCommentToJiraIssue`, `createIssueLink`, `atlassianUserInfo`).
- Glean MCP (`search`, `read_document`, `chat`) — reachability checks, runbook lookups, PR summaries.
- GitHub MCP or `gh` CLI (`get_file_contents`, `get_me`, `get_teams`) — CODEOWNERS resolution and identity.

If any of these are missing, stop and print the install command (see `devops` skill's "Setup" section). All three (Atlassian, Glean, GitHub) are hard requirements — do not attempt to triage without them.

**Optional but valuable**:

- **PagerDuty read access (MCP or `pd` CLI)** — required for `pd-reconcile` mode. Detect the MCP state — authorized / auth-failing (`401`/`403` → unavailable, don't loop-retry) / absent — then prefer the read-only `pd` CLI over re-adding the MCP. Full procedure and install commands: [`references/pd-access.md`](references/pd-access.md). If neither is usable and any ticket links to PD, flag PD-linked tickets as "needs PD verification" and continue in degraded mode.

- **Grafana MCP** — enables Tempo TraceQL queries, Prometheus metric queries, dashboard fetches, Loki log queries. Many investigation paths collapse from "ask the user to look" → "fetch the rate inline" when Grafana is available. **Check this at preflight** — see workflow step 2.

## Investigation gating: cheap vs deep

When Grafana MCP is available, distinguish cheap auto-fetch from deep ask-first investigation:

- **Cheap (auto on relevant tickets, no permission needed)**:

  - Single `rate()` query over a stated window
  - Single histogram quantile (`histogram_quantile`)
  - One dashboard summary or panel image
  - One trace lookup by ID
  - One PD `get_incident` + `list_log_entries` on a referenced PD URL
  - One `gh api commits` query for recent activity on a named file

- **Deep (ask y/n before running)**:

  - Multi-query Tempo TraceQL searches across a large time window
  - Loki log scans
  - Exemplar walking across many traces
  - Sift investigations
  - Reading multiple files via `getJiraIssue` with full body + comments (use compact field list by default; ask before expanding)
  - Recursive CODEOWNERS / `apollo-dev-teams.yml` reorg verification beyond what's already in [`references/team-state-2026.md`](references/team-state-2026.md)

Format the ask as a yes/no with the exact query named:

> "Pull the rate of `*.shifter.io` outbound from Tempo for 17:30–18:30 UTC May 22? (y/n)"

Multiple investigation steps in flight → batch them into one `AskUserQuestion` block with all the y/n options.

## PD-assignment batching

In `pd-reconcile` mode (and any triage pass with ≥3 PD-linked tickets), after fetching PD status, scan once for the "PD-acked, Jira-unassigned" set. Ask the entire batch in one `AskUserQuestion`:

> "These N tickets had PD responders but no Jira assignee. Assign the PD ack-er in all of them? [Yes / Per-row review / Skip]"

Same pattern for "PD-resolved, Jira-stale ≥7d → propose Close":

> "These M tickets have resolved PDs with prior human ack and no Jira activity ≥7d. Close them as No Action? [Yes / Per-row / Skip]"

If the user picks "Per-row," fall back to standard one-at-a-time approval flow. If "Yes," execute the batch and report per-ticket outcomes.

## Compact field list

Default field set for `searchJiraIssuesUsingJql` and `getJiraIssue`:

```
["summary", "status", "priority", "labels", "components",
 "created", "updated", "reporter", "assignee", "customfield_10114",
 "customfield_10020"]
```

(`customfield_10114` = Impacted Team. `customfield_10020` = Sprint.)

**Do not fetch `description` or `comment` by default** — those are what blow past token limits. Only fetch them on tickets you've identified as the "needs decision" set (typically ≤10 tickets per pass). Exception: `pd-reconcile` discovery needs `description`/`comment` to find PD URLs — see the `pd-reconcile` workflow above.

## Workflow

Work through these steps in order. Print intermediate output as you go — silence is worse than verbosity in a triage session.

### 1. Parse arguments

Echo the resolved arg set: `mode=triage scope=mine limit=50 dry-run=false` — so a misparse is visible before any Jira call. If args are ambiguous, ask.

### 2. Preflight: MCP availability table

Print a single-line MCP table:

```
Tools: Atlassian ✅  GitHub ✅  Glean ✅  PagerDuty ✅  Grafana ✅  (cloudId resolved)
```

- Detect PD read access per the three MCP states in [`references/pd-access.md`](references/pd-access.md) — authorized / auth-failing (`401`/`403` → treat as unavailable, don't loop-retry) / absent — then check `command -v pd` for the CLI fallback, preferring the `pd` CLI over re-adding the MCP.
- For `pd-reconcile`, PD read access is **required**; if neither the authorized MCP nor the `pd` CLI is usable, stop and print the CLI install command.
- For other modes, note any missing optionals in the table.
- If Grafana is absent, the skill will not auto-fetch metric/trace data — fall back to "describe what you'd want to investigate" without the data.
- If `--dry-run` is set, print a one-line banner.

### 3. Identity resolution

Determine the user's team slugs per [`references/team-lookup.md`](references/team-lookup.md). Cache for the session. If unresolvable and `team` or `mine` scope is selected, ask once.

### 4. Load registry + team-state

Fetch `apollo-dev-teams.yml` once at preflight from `https://raw.githubusercontent.com/apolloio/leadgenie/master/apollo-dev-teams.yml`. Read field names dynamically. Cache for the session. **Also load [`references/team-state-2026.md`](references/team-state-2026.md)** — that file overrides registry routing decisions where annotated.

### 5. Fetch the queue

Call `searchJiraIssuesUsingJql` with the scope's JQL and the compact field list. Do not fetch description/comments yet.

### 6. Classify + recognize per ticket

For each ticket, in this order:

1. Classify into one of the ticket classes (PD alert / Security finding / Customer report / Manual ask / Auto-classifier filing / No-class).
1. Scan the title + labels for vendor / internal-tooling recognition signals. Match against [`vendors.md`](references/vendors.md) and [`internal-tooling.md`](references/internal-tooling.md).
1. Tag any rows where recognition contradicts the auto-classifier's `Impacted Team` (Apollo Agent default) — those need verification before routing.

### 7. Concise scan output

**Print a 1-screen summary, not a full table yet.** The "Urgent now" list (≤ 5 items) is tickets matching any of these urgency signals, computable from the compact field list plus recognition:

- PD status `triggered` or `acknowledged` right now — **only if PD status was fetched** (pd-reconcile mode, or after a PD-status pass; see note below). PD ack-state does not live in compact Jira fields.
- Priority `Highest` / `High` AND age < 7 days.
- Active in-the-wild exploitation referenced in description or comments (only for rows whose body has been fetched).
- Source label `bugcrowd` or `claude-security` (manual security findings — trust them).
- Customer report from a named GTM/Support escalator with reproduction.
- Comments in the last 24h from a non-reporter (only for rows whose comments have been fetched).
- MTTR SLA window remaining < 3 days (per `cve-triage.md`, for security findings only).

Format:

```
Resolved: mode=<x> scope=<y> ... (1 line)

Urgent now (≤5):
- KEY1 — one-line
- KEY2 — one-line

Counts: PD/Grafana ×N, Security ×M, Customer ×P, Manual ×Q, No-class ×R
Status mix: Reported ×N, Triage ×M, ...
Unassigned: N

Recognized patterns:
- 3 tickets touch Shifter — likely the recurring self-spam pattern (see vendors.md)
- 2 tickets are QE-filed flaky_test labels — read descriptions before trusting (see internal-tooling.md)

PD-batched questions ready: N PD-acked-but-unassigned, M PD-resolved-stale.
```

**PD ack/resolved counts require PD status.** The PD-batched line and the PD-acked entries in the urgent list only appear once PD status has been fetched via `get_incident` — i.e. in `pd-reconcile` mode (step 1 fetches it), or after a PD-status pass on the PD-linked subset. In plain `triage`/`report` mode the compact scan can only surface *PD-linked* counts (from labels/URLs), not ack-state; if PD status hasn't been fetched, omit the PD-batched line and surface the PD-linked subset as "needs PD verification" instead.

Then **stop** and ask:

```
AskUserQuestion:
1. "Walk the full routing table now, or focus on the urgent set first?"
2. "<if PD status fetched and N ≥ 3> Run the PD-assignment batch question now?" [yes/no]
3. "<if relevant Grafana investigation queued> Pull <specific query> from Grafana?" [yes/no]
```

All in one `AskUserQuestion` block. No table yet.

### 8. Per-class context extraction (only on rows the user wants to action)

After the user picks scope, fetch description + comments only for the rows in scope (urgent set, batched PD set, or full queue if requested). Apply:

- **PD alert** → service group + PD service + metric snapshot (see `pd-alerts.md`). If recognition flagged a vendor pattern, follow the vendor entry's triage step.
- **Security finding** → source label, repo, affected paths, severity context (see [`finding-sources.md`](references/finding-sources.md)).
- **Customer report / manual ask** → reporter team, named service, repro signal. If none of these is present, propose `ask-reporter`.
- **Auto-classifier filing** → **read the description's failure quote before trusting the label** (see `internal-tooling.md`).

### 9. OWASP bucketing (security findings only)

Per [`owasp-ranking.md`](references/owasp-ranking.md). PD alerts and customer reports do not get OWASP bucketing.

### 10. Duplicate detection

Per [`duplicate-heuristics.md`](references/duplicate-heuristics.md). Stage `Duplicate` issue links — don't write yet.

### 11. Keep or reroute

For each ticket, decide per [`reroute-rules.md`](references/reroute-rules.md). **Cross-check route candidates against three sources, in order**:

1. CODEOWNERS (file-level ownership in the affected repo)
1. `apollo-dev-teams.yml` (current team rosters — `packs_owned`, `files_owned`)
1. [`team-state-2026.md`](references/team-state-2026.md) (recent reorgs, "functionally on X" annotations, override notes)

When sources disagree, **the team-state file wins for routing decisions** *where it explicitly addresses the pack/path/team* — but always explain the override in the proposed-comment so the user can validate. Two guards from [`reroute-rules.md`](references/reroute-rules.md): (1) if team-state is silent on the path, fall back to CODEOWNERS; (2) if the team-state entry looks stale (>90 days old) or contradicts active evidence (recent commits from engineers it claims have moved), drop to confidence `low`, mark the row `?`, and ask the user rather than routing on the stale snapshot. Outcomes: `Work this sprint`, `Loop in @team`, `Reroute → @team`, `Assign PD responder`, `Close (PD resolved)`, `Ask reporter`, `Mark FP`, `Close (no action)`, `Mark duplicate of <KEY>`. Routing rationale is one short clause; if you can't write it in a clause, the row is `?`.

### 12. Security CVE / finding handling

For security findings, run the reachability flow in [`cve-triage.md`](references/cve-triage.md).

### 13. Numbered routing table (only after step 7's questions are answered)

```
| # | Key | Title | Class | Age | Sev | Proposed action | Owner | Proposed comment | Reason | Confidence |
```

Number rows `1, 2, 3…`. Put each row's proposed comment text in the `Proposed comment` column verbatim (use a sub-line under the row if it's too long to fit) — the user reads it here, not in a separate block. For security findings, add an `OWASP` column. For PD alerts, the `Reason` column should reference the PD service or service-group tag. For vendor-recognized rows, the `Reason` should name the vendor entry being applied.

### 14. Confirm and write

Ask the user to approve rows by number. Accept `approve 1,3`, `approve all duplicates`, `approve PD-batch`, or `update <n>: <new text>` to revise a comment before posting (re-print that row, still gated on a later `approve <n>`). For each approved row/batch, execute the staged writes and print the new state. Never batch writes without naming the rows or batch.

**Sprint awareness**: when staging an assignment, default to adding the ticket to the current active sprint of the team's `jira_default_project`. Look up via `searchJiraIssuesUsingJql` with `project = <KEY> AND sprint in openSprints()` once per session and cache.

**If `--dry-run` was set**, print what would be written for each approval but do not call any Jira write tool.

### 15. Runbook gap

If a ticket has no linked runbook and Glean finds nothing relevant, propose a draft INFRA ticket body (do not create — confirm first).

### 16. End-of-pass gate

Once approved writes are done, **ask before writing the summary**:

> "Triage actions complete: N assigned, M commented, P routed. Anything else to action in this pass? (y/n)"

If the user says yes, loop back to step 7. If no, proceed to summary.

### 17. Summary (format-aware)

Ask the user once how they want the summary:

```
AskUserQuestion: "Summary format?"
Options: "Slack post (numbered bullets)" / "Jira ticket comment" / "Stand-up readout (terse)" / "Skip — just give me counts"
```

Then write the summary in that format. Default counts to include: `assigned`, `rerouted`, `commented`, `closed`, `merged as duplicate`, `deferred`, `flagged hygiene`. One-line followup for the next review.

### 18. Skill-improvement offer (post-summary)

If the session surfaced something the skill should have known but didn't — stale CODEOWNERS, missing vendor entry, "this exception name lies," a team reorg the registry hasn't caught up to — offer:

> "I noticed `<X>` would've routed faster if `<reference file>` knew about `<Y>`. Want me to draft a PR adding it? (y/n)"

If yes, propose the diff against the relevant reference file, run `mdformat`, and offer `gh pr create` against `main`. Use branch name `chore/incident-triage-<reference-file>-update` and PR title `chore(incident-triage): update <reference file>` per the repo's Conventional Commits convention. If no, suggest the user file it as an issue.

Make this offer at most once per session.

## Running From Slack

The skill is invocation-agnostic; it just calls MCPs. From Slack via the Apollo Claude bridge:

- Trigger with the same phrases ("triage incidents", "triage my findings").
- Confirmations come back as Slack replies. The skill should post the routing table as a Slack snippet (collapsed code block) when the table exceeds 10 rows.
- MCP setup prompts won't help in Slack — print a one-line note instead and continue in degraded mode.

## Output Discipline

- Always print the numbered routing table — with proposed comments inline — before requesting writes. Approval is by row number (`approve 1,3`); `update <n>: …` revises a comment first. The one exception is the **PD-responder batch** (see "PD-assignment batching" and Comment-discipline): those assignee/transition writes are approved via the batched `AskUserQuestion` in step 7 and don't produce free-text comments, so they don't require the routing table first. They still require explicit batch approval — they are never written silently.
- Cite Jira keys, never paraphrase tickets without the key.
- Cite Glean URLs verbatim when claiming a CVE is unreachable or a runbook exists. Do not invent links.
- Confidence is `high` / `med` / `low` and reflects how much you'd bet on the routing being correct without a reporter conversation. Vendor-recognized routes can start at `high`; auto-classifier-only routes start at `med` until verified.
- Never bake team slugs into output — read them from the registry at runtime. If a CODEOWNERS slug isn't in the registry, follow the rename-fallback in `team-lookup.md`. If the registry contradicts `team-state-2026.md`, the team-state file wins.

## Known Limitations

- **Transition denials**: Claude Code's auto-mode permission classifier may inconsistently deny `transitionJiraIssue` calls, citing "malformed payload" or "agent-inferred parameter" even when the `{"id": "<n>"}` payload was just fetched from `getTransitionsForJiraIssue` and is identical to a payload that succeeded in the same batch. When this happens:
  - Note which keys were denied and continue executing the rest of the approved batch.
  - For each denied transition, print a one-line fallback: `Open <KEY> in Jira and click "<transition name>" in the workflow menu.`
  - Do NOT loop-retry — the classifier's decision is per-call and retries waste tokens.
  - At wrap-up, suggest the user add a permission rule for `mcp__atlassian__transitionJiraIssue` to their settings if these denials become common.
- The link + comment from a `Mark duplicate` action are durable even without the transition — the canonical-ticket signal isn't lost when a transition is denied, just the status change.
- **Pantheon bot races**: when staging a comment/assignee change on a ticket the Pantheon bot is also working, the bot may close/transition the ticket mid-write (see INCIDENT-29450 in session history). Detect a write that lands on a now-closed ticket and skip remaining staged writes for that ticket; surface to the user.

## Examples

### Example 1 — report mode, concise scan

**User**: "Give me a report on the INCIDENT queue."

**Assistant**:

```
Tools: Atlassian ✅  GitHub ✅  Glean ✅  PagerDuty ✅  Grafana ✅
Resolved: mode=report scope=unassigned limit=50

Urgent now (3):
- INCIDENT-512 — ES cluster red, 2h old, linked PD-9012 (acknowledged)
- INCIDENT-28885 — IDOR in TeamsController catchall, label `bugcrowd`
- INCIDENT-501 — CVE-2025-1234 in `nokogiri`, label `kodem`, MTTR SLA 4d

Counts: PD/Grafana ×11, Security ×3, Manual ×0
Status mix: Reported ×9, Triage ×5
Unassigned: 14

Recognized patterns:
- 2 PD alerts mention Cloudflare 5XX — check our origin error rate first
- 1 security finding is in CI tooling path (apply CVSS context downgrade)
```

No writes performed. Want the routing table, or to dig into one of the urgent rows?

### Example 2 — triage mode, mine scope

**User**: "Triage my findings."

**Assistant**:
*[Identity: adam.blackwell → @apolloio/devops, @apolloio/sre per GitHub teams. Confirmed.]*

I found 6 tickets assigned to you. Routing table:

| # | Key | Title | Class | Sev (raw → adj) | OWASP | Proposed action | Owner | Proposed comment | Reason | Confidence |
| - | -------------------- | -------------------------------------- | ---------------- | --------------- | ----- | ------------------- | ---------- | ---------------- | -------------------------------------------- | ---------- |
| 1 | INCIDENT-27148 | Same `secret_key_base` prod/staging | Manual ask | P4 → P2 | A02 | Work this sprint | @your-team | — | Cross-env secret parity = floor at P2 | high |
| 2 | INCIDENT-28083-clone | Axios HTTP splitting in leadgenie/scripts | Security finding | P1 → P4 | A03 | Comment + downgrade | — | *(below)* | CI tooling path, CVSS context-adjusted | high |

Row 2 comment: Triaged CVE-2026-40175 (raw CVSS: 10.0). The vulnerable path is `scripts/jira-incident-failed-tests/`, which is CI tooling — not a production serving path. Proposing context-adjusted severity P4 per the CVSS context-adjustment policy. Evidence: <glean-link>. cc @security-owner.

Reply `approve 2` to post + downgrade, or `update 2: <new text>` to revise the comment first. Nothing is posted until you do.

### Example 3 — pd-reconcile with PD-batch

**User**: `/apollo-eng-devops:incident-triage pd-reconcile unassigned`

**Assistant**:

```
Tools: Atlassian ✅  PagerDuty ✅  GitHub ✅  Glean ✅  Grafana ✅
Resolved: mode=pd-reconcile scope=unassigned limit=50

PD-linked tickets in scope: 18
Fetching PD status for each...

PD-acked but Jira-unassigned: 4
- INCIDENT-29126 → Hari Vanga
- INCIDENT-28896 → on-call-devops
- INCIDENT-28847 → Marcelo Mendonca
- INCIDENT-28888 → Hari Vanga

PD-resolved, Jira stale ≥7d: 7

AskUserQuestion:
1. "Assign PD ack-ers to the 4 unassigned tickets? [Yes / Per-row / Skip]"
2. "Close the 7 stale PD-resolved tickets? [Yes / Per-row / Skip]"
```

After user picks "Yes" on both, execute the batches and print the per-ticket outcomes. No tables of proposed comments needed for these standard PD-reconcile actions — the templates are in `pd-alerts.md`.

### Example 4 — recognition-first triage

**User**: "Triage incidents."

**Assistant**:

```
... [concise scan above] ...

Recognized patterns:
- INCIDENT-29534 is `Crawler::SearchEngineLinkedinPersonUpdaterWorker`. Per vendors.md (Shifter entry), this is the recurring self-spam pattern. The exception name "Something is wrong with VPN setup" misleads — real cause is usually our outbound rate exceeding Shifter tolerance.

AskUserQuestion:
1. "Pull rate({span.net.peer.name=~'.*shifter\\.io'}) for the alert window from Tempo? (y/n)"
2. "Walk the rest of the routing table?"
```

If user says y/n to the Shifter query, fetch it inline and confirm or refute the recognition before staging a route.

### Example 5 — rename fallback

**User**: "Triage them."

**Assistant**:
*\[For INCIDENT-29001, CODEOWNERS in `apolloio/leadgenie` points to `@apolloio/platform-engagement` for the affected path, but that slug is not in `apollo-dev-teams.yml`. Fuzzy match: `engagement-platform` at 0.83.\]*

| # | Key | Proposed action | Proposed comment | Confidence |
| - | --- | --- | --- | --- |
| 1 | INCIDENT-29001 | Confirm reroute (`?`) | Possible reroute to Engagement Platform — CODEOWNERS in `leadgenie` references `@apolloio/platform-engagement`, not in `apollo-dev-teams.yml` (closest: `engagement-platform`, 0.83). Did you mean Engagement Platform? Assignee unchanged pending confirmation; CODEOWNERS may need updating. | low |

*(Abbreviated table — the `Title`/`Class`/`Age`/`Sev` columns from the canonical step-13 format are omitted here for brevity.)*

Row marked `?` confidence `low`. Will not auto-reroute. `approve 1` to post, `update 1: …` to revise.

## References

- [`references/vendors.md`](references/vendors.md) — Upstream-vendor recognition index. Shifter, Redis Cloud, MongoDB Atlas, Cloudflare, etc. Use for fast recognition before investigation.
- [`references/internal-tooling.md`](references/internal-tooling.md) — Pantheon, Apollo Agent classifier, jira-bot. Trust-description-not-labels rules.
- [`references/team-state-2026.md`](references/team-state-2026.md) — Org snapshot. BE Platform + DevOps rosters with "functionally on X" annotations. CRM Platform → deals-intelligence reorg, FE Platform → fabric-surfaces split. Overrides registry routing.
- [`references/pd-alerts.md`](references/pd-alerts.md) — PD/Grafana FIRING alerts: identification, extraction, PD status reconciliation, routing
- [`references/pd-access.md`](references/pd-access.md) — PD read access: MCP states (401/403 handling), `pd` CLI fallback, install commands
- [`references/finding-sources.md`](references/finding-sources.md) — Security source labels (Kodem, Orca, Bugcrowd, Panther, claude-security): per-source extraction
- [`references/team-lookup.md`](references/team-lookup.md) — Identity resolution, CODEOWNERS lookup, rename fallback
- [`references/owasp-ranking.md`](references/owasp-ranking.md) — OWASP Top 10 with Apollo context, for security finding severity ranking
- [`references/cve-triage.md`](references/cve-triage.md) — Security reachability flow, CVSS context adjustment, MTTR SLA
- [`references/reroute-rules.md`](references/reroute-rules.md) — Keep-vs-reroute decision matrix across all classes
- [`references/duplicate-heuristics.md`](references/duplicate-heuristics.md) — Grouping near-duplicate tickets (PD flapping, security source dedup)
- [`references/comment-templates.md`](references/comment-templates.md) — Proposed-comment templates
- [`references/architecture.md`](references/architecture.md) — End-to-end flow diagram, source-of-truth wiring, when this skill is right vs wrong
- [`references/external-links.md`](references/external-links.md) — Canonical Notion docs (MTTR SLA, IR policy, runbooks) and known doc gaps
- [`references/contributing.md`](references/contributing.md) — How to file fixes when the skill misroutes or proposes a bad comment
