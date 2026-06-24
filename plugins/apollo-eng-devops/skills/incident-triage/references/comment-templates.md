# Jira Comment Templates

**All comments are proposals.** The skill prints these in a `proposed-comment` block under each ticket key and waits for explicit `approve <KEY>` before calling `addCommentToJiraIssue`. There is no "approve all comments" path.

Keep proposals to ≤ 3 sentences. Reporters are more likely to respond to two sentences than two paragraphs.

Placeholders in `{CURLY_CASE}` are populated at runtime from `apollo-dev-teams.yml` (via `team-lookup.md`) and the finding body. Never hardcode team names, slack channels, or lead handles into a template.

## ask-reporter

> Thanks for filing this. To route it correctly we need a bit more context:
>
> - Which service or surface is affected?
> - Is this reproducible, or was it a one-time event? If reproducible, steps please.
> - Any linked PD incident, alert, or dashboard?
>
> I'll re-triage once we have those. If we don't hear back in 5 business days I'll close this as `No Action`.

## reroute-to-team

> Rerouting to {TEAM_DISPLAY_NAME} ({SLACK_CHANNEL}) based on CODEOWNERS for {AFFECTED_PATH}. cc @{TEAM_LEAD_HANDLE}. Context: {ONE_LINE_REASON}. Original assignee can re-assign back with a comment if this is wrong.

## reroute-uncertain

> Possible reroute to {TEAM_DISPLAY_NAME} — CODEOWNERS in `{REPO}` references `@apolloio/{SLUG_FROM_CODEOWNERS}`, which is {NOT_IN_REGISTRY_OR_FUZZY_MATCH}. Did you mean {BEST_GUESS_TEAM}? Leaving the assignee unchanged pending confirmation. Hygiene note: CODEOWNERS in `{REPO}` may need updating.

## ask-em-to-route

Use when assigning to an EM because the owning IC is unknown — you need the EM to delegate rather than investigate themselves.

> @{EM_NAME} — routing this to you for direction. This looks like it falls under {TEAM_NAME} territory ({BRIEF_REASON}: e.g. `packs/{x}` CODEOWNERS, Search Platform pack). Could you point it to the right engineer? Happy to reroute or close if there's a better home.
>
> @{CC_NAME} — tagging you as well. {ONE_SENTENCE_SPECIFIC_QUESTION}

## soft-cross-team-routing

Use when routing outside your team and pack ownership is uncertain — hedges the assignment and explicitly invites correction.

> @{NAME} — routing this your way as it looks like it may fall under {PACK_OR_TEAM} territory. {ONE_LINE_DIAGNOSIS}. A likely fix would be {FIX_HYPOTHESIS} — though I may be misreading the pack ownership. Happy to reroute if this belongs elsewhere. Advice on whether to fix, reroute, or close appreciated.

## dup-merge (posted on the non-canonical ticket)

> Closing as a duplicate of {CANONICAL_KEY}, which has more context (linked PR, reproduction steps). Please follow that ticket for updates. If you believe this is a separate issue, reopen with the difference and I'll re-triage.

## cve-not-vulnerable

> Triaged {CVE_OR_FINDING_ID} (current severity: {SEV}).
>
> We are not vulnerable: {ONE_SENTENCE_REASON}.
>
> Evidence: {GLEAN_OR_PR_LINKS}.
>
> Proposing severity downgrade to {NEW_SEV} / close as `Won't Do`. cc @{SECURITY_OWNER} for confirmation.

## cve-defer-within-sla

> Triaged {CVE_OR_FINDING_ID}. Vulnerable code path is reachable but risk is bounded ({REASON}: e.g. internal-only, behind auth, no public exploit). MTTR SLA for {SEV} is {WINDOW} ({MTTR_NOTION_LINK}); we are within it. Deferring to {SPRINT_OR_MILESTONE}, owner: @{TEAM_LEAD_HANDLE}. Will revisit if exploit lands or scope changes.

## cve-context-downgrade

> Triaged {CVE_ID} (raw CVSS: {CVSS}). The vulnerable path is `{PATH}`, which is {CONTEXT}: e.g. CI tooling / scripts / non-production. Proposing context-adjusted severity {NEW_SEV} per the CVSS context-adjustment policy in the triage runbook. Evidence: {LINKS}. cc @{SECURITY_OWNER}.

## kodem-false-positive

> Reviewed the Kodem flag at `{PATH}:{LINE}`. The flagged call is gated downstream by {GUARD_REFERENCE} (Glean: {LINK}). Proposing this as a Kodem false positive. Note: audited the surrounding actions to confirm the gating pattern holds across the file — see {AUDIT_NOTES}. cc @{SECURITY_OWNER} to confirm before close.

## orca-accepted-risk

> Triaged Orca alert {ORCA_ALERT_LINK} on `{RESOURCE}` ({ACCOUNT}). The configuration is intentional: {REASON_WITH_LINK_TO_DESIGN_DOC_OR_PRIOR_TICKET}. Proposing close as `Accepted Risk` with re-review at {NEXT_REVIEW_DATE}. cc @{SECURITY_OWNER}.

## bugcrowd-acknowledged

> Acknowledging Bugcrowd finding {BUGCROWD_ID}. Confirmed reproduction against {ENV}. Rerouting to {TEAM_DISPLAY_NAME} ({SLACK_CHANNEL}) per CODEOWNERS for `{PATH}`; owner @{TEAM_LEAD_HANDLE} will respond within the MTTR SLA window for {SEV}. Not downgrading — manual pen-test evidence stands.

## panther-handoff

> Panther alert from rule `{RULE_NAME}` on host `{HOSTNAME}` (user `{USER}`). Endpoint detection — rerouting to {CORP_ENG_OR_IT_TEAM} for handling. No infra-side action proposed unless the rule is updated to flag a workload.

## linked-pd-resolved

**When to use:** only when **all** of these hold: (a) PD resolved *after* a human ack or comment, (b) 7+ days of Jira silence with no open follow-up, (c) single one-shot firing (no `Again`/`Recurring` signal), (d) priority is P3/P4. For P2+ with no RCA, recurring alerts, or unclear root cause, use `pd-resolved-rca-or-close` instead. For auto-resolved PDs with no human touch, use `linked-pd-auto-resolved`. Closing a PD on its own does **not** mean the Jira closes — see [`pd-alerts.md`](pd-alerts.md) → "PD status reconciliation."

> Linked PD ({PD_URL}) is resolved as of {TIMESTAMP}. Closing this Jira and assigning to @{RESPONDER_TEAM} for any follow-ups noted in the PD postmortem.

## pd-resolved-rca-or-close

**When to use:** default for PD-resolved tickets that aren't strict same-shift duplicates and don't meet the clean-one-shot bar for `linked-pd-resolved`. Preserves the operational signal without forcing a premature close.

> Linked PD ({PD_URL}) auto-resolved {TIMESTAMP}, but no RCA was recorded on this Jira. Routing to @{TEAM} to either confirm the root cause is fixed (and close) or open a postmortem ticket. If this alert fires again on the same surface, please link the new ticket with `Relates` so we consolidate rather than re-open.

## pd-assign-responder

> Linked PD ({PD_URL}) is `acknowledged` by @{PD_RESPONDER}. Assigning this Jira to them and transitioning to In Progress so the ticket tracks the live response. If you'd rather hand off, reassign and leave a comment.

## pd-investigation-in-flight

> Linked PD ({PD_URL}) has human activity ({ACK_OR_COMMENT_SUMMARY} at {TIMESTAMP}) — investigation is in flight. Transitioning this Jira to In Progress to reflect the live work. Not closing: PD state ≠ Jira state, and the human follow-up loop (root cause, runbook, postmortem) belongs here.

## linked-pd-auto-resolved

> Linked PD ({PD_URL}) auto-resolved at {TIMESTAMP} with no human ack or comments — looks like a flap or auto-recovery. Leaving this Jira Open for someone to decide whether to investigate or to tune the alert. Not closing.

## pd-recurring-runbook-gap

> This alert has fired {N} times in the last {WINDOW} ({PRIOR_KEYS}). Not a duplicate — recurring failure mode with no linked runbook. Proposing INFRA ticket to write one; will link from here once filed.

## pd-tune-this-alert

> Alert has fired {N} times in {WINDOW} with median resolution time < {THRESHOLD}. Flagging as a potential tuning candidate (false positives or auto-recovering condition). cc @{ALERT_OWNER} for sign-off before any rule change.

## runbook-gap

> No runbook found for this failure mode (Glean returned no relevant doc). Filed {INFRA_KEY} to write one — link it from the postmortem.

## no-action-close

> Closing as `No Action`: {REASON}. Reopen if it recurs with reproduction steps and I'll route it.
