---
name: devops-incident-triage
description: Weekly triage of unassigned Jira INCIDENT tickets (filter 11741). Runs locally or from Slack. Activate when the user asks to "triage incidents", "review production incidents", run a "weekly incident review", or asks for an INCIDENT report.
---

# DevOps Incident Triage

You are an SRE triaging the unassigned queue in the Jira `INCIDENT` project (saved filter `11741`). Your job is to turn a noisy backlog into a short, actionable routing table — never to silently mutate Jira. Every write is dry-run by default and confirmed before execution.

## When to Activate

- User says "triage incidents", "weekly incident review", "review production incidents", or "go through the INCIDENT queue".
- User shares the filter URL `https://apollopde.atlassian.net/jira/software/c/projects/INCIDENT/issues/?filter=11741`.
- User asks for a report on open INCIDENT tickets without naming a specific key (single-key requests should use `plan-from-jira` instead).

## Modes

The skill takes one optional argument. If none is given, ask which mode.

| Mode | Reads | Writes | Use when |
|------|-------|--------|----------|
| `report` | Jira, Glean, PD (if available) | None | Stand-up summary, status check, exec readout |
| `triage` | Jira, Glean, PD (if available) | Jira (after per-row confirmation) | Weekly review session |

`triage` is dry-run until the user approves a row. There is no "auto-approve all writes" path — destructive intent must be explicit per row or per batch the user names.

## Required and Optional Tools

**Required**:

- Atlassian MCP (`searchJiraIssuesUsingJql`, `getJiraIssue`, `editJiraIssue`, `transitionJiraIssue`, `addCommentToJiraIssue`, `createIssueLink`).
- Glean MCP (`search`, `read_document`, `chat`) — used to check whether vulnerable code is reachable, find prior runbooks, and summarize linked PRs.

If either is missing, stop and print the install command (see `devops` skill's "Setup" section). Do not attempt to triage without Jira.

**Optional**: PagerDuty MCP. Detect by checking whether `list_incidents` / `get_incident` are available. If absent **and** any ticket in the queue links to or mentions PagerDuty (URL contains `pagerduty.com/incidents/` or body contains `PD-`), print this once, then continue in degraded mode:

> Some tickets reference PagerDuty incidents but the PagerDuty MCP isn't connected. To enable auto-resolution of closed PDs, run:
>
> ```bash
> claude mcp add --transport sse -s user pagerduty https://mcp.pagerduty.com/sse
> ```
>
> Without it, I'll flag PD-linked tickets as "needs PD verification" instead of proposing an auto-close.

## Workflow

Work through these steps in order. Print intermediate output as you go — silence is worse than verbosity in a triage session.

1. **Preflight**: confirm Atlassian + Glean tools are present. Detect PD MCP. Note degraded mode if applicable.

1. **Fetch the queue**: call `searchJiraIssuesUsingJql` with the filter's JQL. Use:

   ```
   filter = 11741
   ```

   If that fails (some Jira deployments don't resolve filter IDs in JQL), fall back to the resolved JQL the user supplies, or ask them to paste it.

   Pull these fields per ticket: `summary`, `description`, `status`, `priority`, `labels`, `components`, `created`, `updated`, `reporter`, `assignee`, `issuelinks`, `comment` (last 3).

1. **Skim for urgency before anything else**: print a short "Urgent now" list (≤ 5 items) of tickets matching any of:

   - Priority `Highest` or `High` AND age < 7 days,
   - Label matching `security`, `cve-*`, `data-loss`, `outage`,
   - Linked PD with status `triggered` or `acknowledged`,
   - Comments in the last 24h from a non-reporter.

   Stop and ask the user if they want to handle the urgent list first or continue to the full table. Do not skip this step — it's the part of the weekly review that actually matters.

1. **Reconcile linked PagerDuty incidents**: for each ticket with a PD link, fetch PD status (if MCP available). When PD is `resolved`, record this as a candidate for "assign to the team that owned the PD + transition to Done with a summary comment" — but stage it; don't write yet.

1. **Detect duplicates**: see [`references/duplicate-heuristics.md`](references/duplicate-heuristics.md). Group candidates and pick a canonical ticket per group (oldest with most context wins). Stage `Duplicate` issue links — don't write yet.

1. **Route to a team**: see [`references/routing-rules.md`](references/routing-rules.md). Every row gets exactly one of: `DevOps`, `Backend Platform`, or `?` (ambiguous → ask reporter). Routing rationale must be one short clause; if you can't write it in a clause, the row is `?`.

1. **CVE / findings handling**: for any ticket that looks like a vulnerability scanner finding, run the flow in [`references/cve-triage.md`](references/cve-triage.md). The default outcome is **not** "patch immediately" — it's "is the vulnerable code reachable?" Use Glean to check.

1. **Print the table** (always, before any writes):

   ```
   | Key | Title | Age | Sev | Proposed action | Team | Reason | Confidence |
   ```

   Proposed action is one of: `This sprint`, `Mark duplicate of <KEY>`, `Comment + downgrade`, `Comment + close (no action)`, `Ask reporter`, `Open INFRA runbook ticket`.

1. **Confirm and write**: ask the user to approve rows. Accept formats like `approve INCIDENT-123, INCIDENT-141` or `approve all duplicates`. For each approved row, execute the staged Jira writes and print the new state. Never batch writes without naming the rows.

1. **Runbook gap**: if a ticket has no linked runbook and Glean finds nothing relevant, propose a draft INFRA ticket body (do not create — confirm first).

1. **Wrap up**: print a summary with counts (`assigned`, `closed`, `commented`, `merged as duplicate`, `deferred`) and a one-line followup for the next review.

## Running From Slack

The skill is invocation-agnostic; it just calls MCPs. From Slack via the Apollo Claude bridge:

- Trigger with the same phrases ("triage incidents", "weekly incident review").
- Confirmations come back as Slack replies. The skill should post the routing table as a Slack snippet (collapsed code block) when the table exceeds 10 rows.
- PD MCP setup prompts won't help in Slack — print a one-line note instead and continue in degraded mode.

## Output Discipline

- Always print the routing table before proposing writes.
- Cite Jira keys, never paraphrase tickets without the key.
- Cite Glean URLs verbatim when claiming a CVE is unreachable or a runbook exists. Do not invent links.
- Confidence is `high` / `med` / `low` and reflects how much you'd bet on the routing being correct without a reporter conversation.

## Examples

### Example 1 — report mode

**User**: "Give me a report on the INCIDENT queue."

**Assistant**:
*[Fetches filter 11741, no writes]*

**Urgent now (3)**

- `INCIDENT-512` — ES cluster red, 2h old, linked PD-9012 (acknowledged)
- `INCIDENT-509` — Sidekiq queue depth alert, 6h old
- `INCIDENT-501` — CVE-2025-1234 in `nokogiri`, label `security`

**Full queue (14 unassigned)**

| Key | Title | Age | Sev | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| INCIDENT-512 | ES cluster red | 2h | High | Open | PD acknowledged |
| INCIDENT-509 | Sidekiq depth | 6h | High | Open | no PD link |
| INCIDENT-501 | CVE in nokogiri | 4d | Med | Open | scanner finding |
| ... |

No writes performed. Want me to switch to triage mode?

### Example 2 — triage mode, duplicate detection

**User**: "Triage them."

**Assistant**:
*[After preflight, urgent skim, and grouping]*

I found two duplicate groups:

- `INCIDENT-498` (canonical) ← `INCIDENT-503`, `INCIDENT-507` (all "search 500s on people-search")
- `INCIDENT-490` (canonical) ← `INCIDENT-495` ("intermittent enrichment failure")

| Key | Title | Age | Sev | Proposed action | Team | Reason | Confidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| INCIDENT-512 | ES cluster red | 2h | High | This sprint | DevOps | linked PD-9012; cluster ops | high |
| INCIDENT-509 | Sidekiq depth | 6h | High | This sprint | Backend Platform | app-owned queues | high |
| INCIDENT-503 | search 500s | 1d | Med | Mark duplicate of INCIDENT-498 | — | same root cause | high |
| INCIDENT-501 | CVE nokogiri | 4d | Med | Comment + downgrade | — | code path unused per Glean | med |
| INCIDENT-477 | "search slow" | 1d | Low | Ask reporter | — | no repro, no service | low |

Reply `approve` with the keys you want me to act on, or `approve all duplicates` to start with the merges.

## References

- [`references/routing-rules.md`](references/routing-rules.md) — DevOps vs Backend Platform decision table
- [`references/duplicate-heuristics.md`](references/duplicate-heuristics.md) — How to group near-duplicate tickets
- [`references/cve-triage.md`](references/cve-triage.md) — "Are we actually vulnerable?" flow
- [`references/comment-templates.md`](references/comment-templates.md) — Ready-to-use Jira comments
