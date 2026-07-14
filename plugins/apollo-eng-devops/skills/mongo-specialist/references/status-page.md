# Status Page (Better Stack)

Apollo's public status page is managed in Better Stack: <https://uptime.betterstack.com>.
Posting is a customer-facing action — confirm with the incident commander before
publishing, and never post internal detail. `incident-response` owns overall comms
cadence; this is only the status-page mechanics.

## When to post

Post when **either** is true:

- Customer-visible impact is expected to last **> 30 minutes**, or
- Severity is **SEV-2 or higher**.

If impact is brief and already recovering, a status post can create more confusion than
it resolves — use judgment with the IC.

## Update flow

Move the incident through the standard lifecycle, one update per transition:

1. **Identified** — we know there is customer impact and are investigating.
1. **Monitoring** — a fix/mitigation is applied and we are watching for recovery.
1. **Resolved** — impact has cleared and stayed clear for a stability window.

**Backdate the start time** to the actual onset (anchored to a metric/log epoch, not
when someone noticed), so the public timeline matches reality.

## Customer-safe wording

- No internal component or cluster names (no "mongos", "noncustomer cluster", pod names).
- No commit SHAs, deploy/rollback details, or internal ticket IDs.
- Describe **symptom and scope** ("some users experienced errors loading X"), not cause.
- Neutral, factual tone; no speculation on cause until confirmed.

## Example copy

**Identified:**

> We are investigating elevated error rates affecting some users when loading parts of
> the app. Our team is actively working on it. Next update in 30 minutes.

**Monitoring:**

> We have applied a fix and error rates are returning to normal. We are monitoring to
> confirm full recovery. Next update in 30 minutes.

**Resolved:**

> This issue has been resolved. All services are operating normally. We apologize for the
> disruption.

## Optional: Better Stack MCP

If the Better Stack MCP is connected it can draft/post updates programmatically, but
treat status posts as human-approved regardless. Verify with `claude mcp get betterstack`.
