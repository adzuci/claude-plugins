---
name: incident-triage
description: Manual-invocation only. Triage Jira INCIDENT tickets. Run via /apollo-eng-devops:incident-triage.
---

# Incident Triage

**Invoke directly.** This skill is not auto-activated. Run it as a slash command: `/apollo-eng-devops:incident-triage [args]`. The short description above is intentional — it keeps the skill out of Claude's auto-routing context across unrelated sessions.

You are triaging Jira `INCIDENT` (and adjacent `SEC` / `INFOSEC` / `ITBS`) tickets on behalf of the user. The queue is a mix — most volume is PagerDuty/Grafana alerts, but security findings, customer-reported degradations, and manual escalations all land here too. Your job is to classify each ticket, propose an action, and never mutate Jira without explicit per-row approval.

Audience: any Apollo engineer.

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
| **Customer report** | Reporter is Support / GTM / external; body describes user-visible symptom | Symptom triage — see Workflow step 7 |
| **Manual / runbook ask** | Reporter is an engineer; body is a request or follow-up | Symptom triage — see Workflow step 7 |
| **No-class hygiene** | None of the above signals fire | Propose reporter clarification (`ask-reporter`) |

A ticket can be in more than one class (a security finding can also be a customer report). The skill picks the **strongest** class — manual review (Bugcrowd / claude-security / customer-named-impact) outranks automation (Kodem / Orca / PD).

## Comment discipline: propose, never post

This is the load-bearing rule of the skill.

- Every proposed comment is printed in a fenced block tagged `proposed-comment` under its ticket key.
- `addCommentToJiraIssue` is **never** called without an explicit `approve <KEY>` from the user **in the same session**.
- There is no "approve all comments" path. Reroute comments require approval per ticket.
- Assignee changes (`editJiraIssue` setting `assignee`) follow the same per-row approval rule.
- Status transitions and issue links may be batched but only against rows the user has named (e.g. `approve all duplicates`, `approve INCIDENT-503, INCIDENT-507`).
- Keep proposed comments to ≤ 3 sentences. Reporters respond to short messages.

If the user asks the skill to "just post them," do not comply silently — print the full list of proposed comments and ask for one explicit confirmation that names the keys.

## Modes

The skill takes one optional argument. If none is given, ask which mode and which scope.

| Mode | Reads | Writes | Use when |
| -------------- | --------------------------------------------------------------------------- | --------------------------------- | --------------------------------------------------------------------------------- |
| `report` | Jira, Glean, PD (if available) | None | Stand-up summary, status check, exec readout |
| `triage` | Jira, Glean, PD (if available), GitHub (CODEOWNERS), `apollo-dev-teams.yml` | Jira (after per-row confirmation) | Weekly review session |
| `pd-reconcile` | Jira, PagerDuty (required), `apollo-dev-teams.yml` | Jira (after per-row confirmation) | Sync open Jira tickets with their linked PD incidents — assign responders + transition states |

### `pd-reconcile` mode

A focused pass for the PD/Grafana alert class only. The mode requires the PagerDuty MCP — if it's not available, refuse to run and print the install command. The skill does not guess at PD state from Jira-side signals.

Workflow:

1. Find open Jira tickets in the chosen scope with a PD link (`pagerduty.com/incidents/` URL in description or comments, or label `pagerduty`).
1. For each, fetch PD status (`get_incident`) and any PD notes/comments (`list_log_entries`).
1. Apply the proposal table in [`references/pd-alerts.md`](references/pd-alerts.md) → "PD status reconciliation." Key rules:
   - **Closing a PD does not close the Jira.** A PD closes when the alerting condition stops; the Jira represents human follow-up.
   - **An ack on PD means investigation is in flight** → propose Jira `In Progress` + assignee = PD responder.
   - **Comments on PD mean investigation is in flight** → same.
   - Auto-resolved PD with no human touch → leave Open + summary comment; do not close.
   - Resolved PD with prior human ack + 7+ days of Jira silence → propose Close (No Action).
1. Print one row per ticket: PD status, PD responder (if any), proposed Jira assignee, proposed transition, and a one-line reason citing the PD signal.
1. Stage all writes; require per-row `approve <KEY>` before executing.

Use cases: catching up after on-call rotation handoff, weekly hygiene on the PD-linked subset of the queue, finding tickets that need to move to In Progress because someone is already responding on PD.

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
- GitHub MCP (`get_file_contents`, `get_me`, `get_teams`) — CODEOWNERS resolution and identity.

If any of these are missing, stop and print the install command (see `devops` skill's "Setup" section). Do not attempt to triage without Jira + GitHub.

**Optional**: PagerDuty MCP. Detect by checking whether `list_incidents` / `get_incident` are available. If absent **and** any ticket links to or mentions PagerDuty (URL contains `pagerduty.com/incidents/` or body contains `PD-`), print this once, then continue in degraded mode:

> Some tickets reference PagerDuty incidents but the PagerDuty MCP isn't connected. To enable auto-resolution of closed PDs, run:
>
> ```bash
> claude mcp add --transport sse -s user pagerduty https://mcp.pagerduty.com/sse
> ```
>
> Without it, I'll flag PD-linked tickets as "needs PD verification" instead of proposing an auto-close.

## Workflow

Work through these steps in order. Print intermediate output as you go — silence is worse than verbosity in a triage session.

1. **Parse arguments** per the Arguments section. Fill missing values via `AskUserQuestion` only when the chosen mode requires them (e.g. `pd-reconcile` doesn't need `--team`). Echo the resolved arg set back to the user as a one-line confirmation: `mode=triage scope=mine limit=50 dry-run=false` — so a misparse is visible before any Jira call.

1. **Preflight**: confirm Atlassian + Glean + GitHub tools are present. Detect PD MCP. For `pd-reconcile`, the PD MCP is **required** — if absent, stop and print the install command. For other modes, PD MCP is optional; note degraded mode if applicable. If `--dry-run` is set, print a one-line banner so all subsequent "approve" prompts make clear no writes will happen.

1. **Identity resolution**: determine the user's team slugs per the procedure in [`references/team-lookup.md`](references/team-lookup.md). Cache for the session. If unresolvable and the user picked `team` or `mine` scope, ask once via `AskUserQuestion`.

1. **Fetch `apollo-dev-teams.yml`** once at preflight from `https://raw.githubusercontent.com/apolloio/leadgenie/master/apollo-dev-teams.yml`. Read field names dynamically — do not assume schema. Cache for the session only.

1. **Fetch the queue**: call `searchJiraIssuesUsingJql` with the scope's JQL. For `unassigned`, use `filter = 11741`. Pull these fields per ticket: `summary`, `description`, `status`, `priority`, `labels`, `components`, `created`, `updated`, `reporter`, `assignee`, `issuelinks`, `comment` (last 3).

1. **Classify each ticket** into one of the classes in the table above. PD/Grafana alerts are the largest class — check `[FIRING:` titles and PD URLs first. Security findings are identified by source label. The rest fall to symptom triage.

1. **Skim for urgency before anything else**: print a short "Urgent now" list (≤ 5 items) of tickets matching any of:

   - PD status `triggered` or `acknowledged` right now (per `pd-alerts.md`).
   - Priority `Highest` / `High` AND age < 7 days.
   - Active in-the-wild exploitation referenced in description or comments.
   - Source label `bugcrowd` or `claude-security` (manual security findings — trust them).
   - Customer report from a named GTM/Support escalator with reproduction.
   - Comments in the last 24h from a non-reporter.
   - MTTR SLA window remaining < 3 days (per `cve-triage.md`, for security findings only).

   Stop and ask the user if they want to handle the urgent list first or continue to the full table. Do not skip this step — it's the part of the review that actually matters.

1. **Reconcile linked PagerDuty incidents** per [`references/pd-alerts.md`](references/pd-alerts.md). For each PD-linked ticket: fetch PD status (if MCP available). Resolved PDs with stale Jiras are candidates for auto-close; acknowledged PDs are candidates for assigning to the responder; triggered PDs go to the urgent list. Stage actions, don't write yet.

1. **Extract per-class context**:

   - **PD alert** → service group + PD service + metric snapshot (see `pd-alerts.md`).
   - **Security finding** → source label, repo, affected paths, severity context (see [`references/finding-sources.md`](references/finding-sources.md)).
   - **Customer report / manual ask** → reporter team, named service, repro signal. If none of these is present, propose `ask-reporter`.

1. **For security findings only**: bucket by OWASP per [`references/owasp-ranking.md`](references/owasp-ranking.md). PD alerts and customer reports do not get OWASP bucketing.

1. **Detect duplicates**: see [`references/duplicate-heuristics.md`](references/duplicate-heuristics.md). PD alerts dedupe heavily (same flapping condition firing repeatedly) — be aggressive but careful. Security findings dedupe per source. Group candidates and pick a canonical ticket per group. Stage `Duplicate` issue links — don't write yet. Note: automated + manual verification pairs link as `Relates`, not `Duplicate`.

1. **Keep or reroute**: for each ticket, decide per [`references/reroute-rules.md`](references/reroute-rules.md). PD alerts route by PD service or service-group tag; security findings route by CODEOWNERS in the affected repo; customer reports route by named service. Validate any resulting team slug against `apollo-dev-teams.yml` (see [`references/team-lookup.md`](references/team-lookup.md)). Outcomes: `Work this sprint`, `Loop in @team`, `Reroute → @team`, `Assign PD responder`, `Close (PD resolved)`, `Ask reporter`, `Mark FP`, `Close (no action)`, `Mark duplicate of <KEY>`. Routing rationale is one short clause; if you can't write it in a clause, the row is `?`.

1. **Security CVE / finding handling**: for security findings, run the reachability flow in [`references/cve-triage.md`](references/cve-triage.md). The default outcome is **not** "patch immediately" — it's "is the vulnerable code reachable, and does CVSS need context adjustment?" Use Glean to check.

1. **Print the table** (always, before any writes):

   ```
   | Key | Title | Class | Age | Sev | Proposed action | Owner | Reason | Confidence |
   ```

   For security findings, add an `OWASP` column. For PD alerts, the `Reason` column should reference the PD service or service-group tag.

1. **Print proposed comments** for each row that has one, in `proposed-comment` fenced blocks tagged with the ticket key. Do not collapse them — the user needs to read them before approving.

1. **Confirm and write**: ask the user to approve rows. Accept formats like `approve INCIDENT-123, INCIDENT-141` or `approve all duplicates`. For each approved row, execute the staged Jira writes (`addCommentToJiraIssue`, `editJiraIssue`, `transitionJiraIssue`, `createIssueLink`) and print the new state. Never batch writes without naming the rows. **If `--dry-run` was set**, print what would be written for each approval but do not call any Jira write tool.

1. **Runbook gap**: if a ticket has no linked runbook and Glean finds nothing relevant, propose a draft INFRA ticket body (do not create — confirm first).

1. **Wrap up**: print a summary with counts (`kept`, `rerouted`, `closed`, `commented`, `merged as duplicate`, `deferred`, `flagged hygiene`) and a one-line followup for the next review.

## Running From Slack

The skill is invocation-agnostic; it just calls MCPs. From Slack via the Apollo Claude bridge:

- Trigger with the same phrases ("triage incidents", "triage my findings").
- Confirmations come back as Slack replies. The skill should post the routing table as a Slack snippet (collapsed code block) when the table exceeds 10 rows.
- MCP setup prompts won't help in Slack — print a one-line note instead and continue in degraded mode.

## Output Discipline

- Always print the routing table **and** the proposed comments before requesting writes.
- Cite Jira keys, never paraphrase tickets without the key.
- Cite Glean URLs verbatim when claiming a CVE is unreachable or a runbook exists. Do not invent links.
- Confidence is `high` / `med` / `low` and reflects how much you'd bet on the routing being correct without a reporter conversation.
- Never bake team slugs into output — read them from the registry at runtime. If a CODEOWNERS slug isn't in the registry, follow the rename-fallback in `team-lookup.md`.

## Known Limitations

- **Transition denials**: Claude Code's auto-mode permission classifier may inconsistently deny `transitionJiraIssue` calls, citing "malformed payload" or "agent-inferred parameter" even when the `{"id": "<n>"}` payload was just fetched from `getTransitionsForJiraIssue` and is identical to a payload that succeeded in the same batch. When this happens:
  - Note which keys were denied and continue executing the rest of the approved batch.
  - For each denied transition, print a one-line fallback: `Open <KEY> in Jira and click "<transition name>" in the workflow menu.`
  - Do NOT loop-retry — the classifier's decision is per-call and retries waste tokens.
  - At wrap-up, suggest the user add a permission rule for `mcp__atlassian__transitionJiraIssue` to their settings if these denials become common.
- The link + comment from a `Mark duplicate` action are durable even without the transition — the canonical-ticket signal isn't lost when a transition is denied, just the status change.

## Examples

### Example 1 — report mode, default scope

**User**: "Give me a report on the INCIDENT queue."

**Assistant**:
*[Fetches filter 11741, no writes]*

**Urgent now (3)**

- `INCIDENT-512` — ES cluster red, 2h old, linked PD-9012 (acknowledged)
- `INCIDENT-28885` — IDOR in TeamsController catchall, label `bugcrowd`, manual finding
- `INCIDENT-501` — CVE-2025-1234 in `nokogiri`, label `kodem`, MTTR SLA: 4 days remaining

**Full queue (14 unassigned)** *(table omitted)*

No writes performed. Want me to switch to triage mode?

### Example 2 — triage mode, mine scope

**User**: "Triage my findings."

**Assistant**:
*[Identity: adam.blackwell → @apolloio/devops, @apolloio/sre per GitHub teams. Confirmed.]*

I found 6 tickets assigned to you. Routing table:

| Key | Title | Source | Sev (raw → adj) | OWASP | Proposed action | Owner | Reason | Confidence |
| -------------------- | -------------------------------------- | ------ | --------------- | ----- | ------------------- | ---------- | -------------------------------------------- | ---------- |
| INCIDENT-27148 | Same `secret_key_base` prod/staging | manual | P4 → P2 | A02 | Work this sprint | @your-team | Cross-env secret parity = floor at P2 | high |
| INCIDENT-28083-clone | Axios HTTP splitting in leadgenie/scripts | kodem | P1 → P4 | A03 | Comment + downgrade | — | CI tooling path, CVSS context-adjusted | high |

```proposed-comment INCIDENT-28083-clone
Triaged CVE-2026-40175 (raw CVSS: 10.0). The vulnerable path is `scripts/jira-incident-failed-tests/`, which is CI tooling — not a production serving path. Proposing context-adjusted severity P4 per the CVSS context-adjustment policy in the triage runbook. Evidence: <glean-link>. cc @security-owner.
```

Reply `approve` with keys to act on. Nothing is posted until you do.

### Example 3 — PD alert reconciliation

**User**: "Triage incidents." *(default scope, unassigned queue)*

**Assistant**:
*[Of 18 unassigned tickets, 12 are PD alerts. PD MCP available — fetching status for each.]*

**Urgent now (2)**

- `INCIDENT-29126` — `[FIRING:1] High 5XX error count [Infra] Cloudflare` — PD `triggered` 8 min ago
- `INCIDENT-28896` — `[FIRING:1] Potential Sev1 in progress [Infra] APM & Traces` — PD `acknowledged`, responder @on-call-devops

**PD-resolved cleanup candidates (7)**

| Key | Title | PD Status | Resolved | Proposed action |
| --- | --- | --- | --- | --- |
| INCIDENT-28847 | Request Errors Count [Infra] Cloudflare | resolved | 6d ago | Close (no action) + `linked-pd-resolved` comment |
| INCIDENT-28888 | High Errors from Cloudflare Tunnel Pods | resolved | 5d ago | Close (no action) |
| ... |

**Recurring (link as Relates)**

- INCIDENT-29054 + INCIDENT-28316 — same Sidekiq crawler worker alert, fired Apr 8 and May 1. Not duplicates — recurring failure mode. Propose runbook gap.

Reply `approve all PD-resolved` to batch-close the 7 stale rows, or name specific keys. Nothing posted until you approve.

### Example 4 — rename fallback

**User**: "Triage them."

**Assistant**:
*\[For INCIDENT-29001, CODEOWNERS in `apolloio/leadgenie` points to `@apolloio/platform-engagement` for the affected path, but that slug is not in `apollo-dev-teams.yml`. Fuzzy match: `engagement-platform` at 0.83.\]*

```proposed-comment INCIDENT-29001
Possible reroute to Engagement Platform — CODEOWNERS in `leadgenie` references `@apolloio/platform-engagement`, which is not in `apollo-dev-teams.yml` (closest match: `engagement-platform`, similarity 0.83). Did you mean Engagement Platform? Leaving assignee unchanged pending confirmation. Hygiene note: CODEOWNERS in `leadgenie` may need updating.
```

Row marked `?` confidence `low`. Will not auto-reroute.

## References

- [`references/pd-alerts.md`](references/pd-alerts.md) — PD/Grafana FIRING alerts: identification, extraction, PD status reconciliation, routing
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
