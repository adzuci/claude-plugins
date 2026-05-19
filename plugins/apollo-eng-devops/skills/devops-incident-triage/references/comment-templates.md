# Jira Comment Templates

Use these as starting points. Always personalize with the specific ticket key, evidence, and owner before posting. Keep comments short — reporters are more likely to respond to two sentences than two paragraphs.

## ask-reporter

> Thanks for filing this. To route it correctly we need a bit more context:
>
> - Which service or surface is affected?
> - Is this reproducible, or was it a one-time event? If reproducible, steps please.
> - Any linked PD incident, alert, or dashboard?
>
> I'll re-triage once we have those. If we don't hear back in 5 business days I'll close this as `No Action`.

## dup-merge (posted on the non-canonical ticket)

> Closing as a duplicate of {CANONICAL_KEY}, which has more context (linked PR, reproduction steps). Please follow that ticket for updates. If you believe this is a separate issue, reopen with the difference and I'll re-triage.

## cve-not-vulnerable

> Triaged {CVE_ID} (current severity: {SEV}).
>
> We are not vulnerable: {ONE_SENTENCE_REASON}.
>
> Evidence: {GLEAN_OR_PR_LINKS}.
>
> Proposing severity downgrade to {NEW_SEV} / close as `Won't Do`. cc @{SECURITY_OWNER} for confirmation.

## cve-defer-within-sla

> Triaged {CVE_ID}. Vulnerable code path is reachable but risk is bounded ({REASON}: e.g. internal-only, behind auth, no public exploit). MTTR SLA for {SEV} is {WINDOW}; we are within it. Deferring to {SPRINT_OR_MILESTONE}, owner: @{TEAM}. Will revisit if exploit lands or scope changes.

## linked-pd-resolved

> Linked PD ({PD_URL}) is resolved as of {TIMESTAMP}. Closing this Jira and assigning to @{RESPONDER_TEAM} for any follow-ups noted in the PD postmortem.

Use only when **all** of these hold: (a) single one-shot firing, (b) post-resolution behavior observed clean for 24h+, (c) no `Again`/`Recurring` signal in title or related tickets, (d) priority is P3/P4. For anything else (P2+ with no RCA, recurring alerts, or unclear root cause), use `pd-resolved-rca-or-close` below.

## pd-resolved-rca-or-close

> Linked PD ({PD_URL}) auto-resolved {TIMESTAMP}, but no RCA was recorded on this Jira. Routing to @{TEAM} to either confirm the root cause is fixed (and close) or open a postmortem ticket. If this alert fires again on the same surface, please link the new ticket with `Relates` so we consolidate rather than re-open.

Default action for PD-resolved tickets that aren't strict same-shift duplicates. Preserves the operational signal without forcing a premature close.

## runbook-gap

> No runbook found for this failure mode (Glean returned no relevant doc). Filed {INFRA_KEY} to write one — link it from the postmortem.

## no-action-close

> Closing as `No Action`: {REASON}. Reopen if it recurs with reproduction steps and I'll route it.
