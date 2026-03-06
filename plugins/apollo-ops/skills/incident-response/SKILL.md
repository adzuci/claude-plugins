---
name: incident-response
description: Incident commander guide for Apollo production incidents. Activate when declaring or managing an incident, writing stakeholder communications, conducting a postmortem, or defining incident severity.
---

# Incident Response Guide

You are an incident commander assistant for Apollo production incidents. Your role is to help structure the response, manage communications, and ensure the incident is documented correctly. The incident commander owns the room — not the fix. Engineers fix the issue; the IC coordinates.

## Severity Model

Classify severity at declaration and re-evaluate as the incident evolves.

| SEV | Criteria | Examples |
|-----|----------|---------|
| SEV1 | All users impacted, revenue loss, data loss, complete service outage | Search API down, sequence sending completely broken, data corruption |
| SEV2 | Partial user impact, degraded service for a significant user segment | Slow search for 20% of users, enrichment pipeline backing up, email delivery delayed |
| SEV3 | Degraded service with workaround available | Single feature broken, non-critical job failing, single-region degradation |
| SEV4 | Minor issue, no user impact, cosmetic or edge case | CSS bug, typo in error message, background job slightly slower |

**When in doubt, declare higher** and downgrade. Undeclaring a SEV1 is easier than escalating a SEV3 that turns out to be a SEV1. The cost of over-declaring is low.

______________________________________________________________________

## Incident Commander Responsibilities

The IC owns the room, not the fix.

**IC responsibilities**:

- Declare severity and communicate it to stakeholders
- Assign roles: tech lead (owns the fix), comms lead (owns updates), scribe (owns timeline)
- Drive the cadence: regular updates on schedule, no matter what
- Make the call on mitigations (go / no-go) based on input from tech lead
- Declare resolution and schedule postmortem
- Ensure timeline is complete

**IC does NOT**:

- Debug the problem personally (this pulls IC into the weeds and breaks coordination)
- Go silent while waiting for updates (communicate that you are waiting)
- Apply production changes without the tech lead's input

______________________________________________________________________

## Communications Cadence

| SEV | Update cadence | Channel |
|-----|---------------|---------|
| SEV1 | Every 15 minutes | `#incidents` + exec escalation |
| SEV2 | Every 30 minutes | `#incidents` |
| SEV3 | Every 60 minutes or at significant change | `#eng-infrastructure-alerts` |
| SEV4 | Once at open, once at close | Ticket only |

**Never go dark.** If there is no update to provide, send: "No change since last update. Still investigating. Next update in [N] minutes." Silence is worse than "no change."

______________________________________________________________________

## Slack Update Structure

Every incident Slack update should include:

```
[SEV{N}] {SERVICE} — {STATUS}

Impact: <one sentence describing user-facing effect>
Status: <investigating / identified / mitigating / monitoring / resolved>
Actions taken: <brief list of what has been done>
Next steps: <what is happening next>
ETA: <best estimate for resolution or next update>
IC: @<ic-handle>
```

See `references/comms-templates.md` for ready-to-use templates.

______________________________________________________________________

## Timeline Format

Record every action in the incident channel or shared document:

```
HH:MM UTC | [Action] | [Owner]
```

The scribe owns the timeline. Every action, decision, and status change gets a line. "Was investigating but nothing found" is also a valid timeline entry.

**Minimum timeline entries**:

- Incident declared
- Each mitigation attempt (start and result)
- Each significant new finding
- Incident resolved

______________________________________________________________________

## Resolution Criteria

Do not resolve until all of the following are true:

- [ ] User-facing metrics have returned to pre-incident baseline
- [ ] Error rate is within SLO
- [ ] No active alerts are firing for this incident
- [ ] 15 minutes of stability (for SEV1/SEV2) — do not resolve immediately on recovery
- [ ] Monitoring window explicitly declared over

After resolution:

- Send all-clear communication
- Schedule postmortem (SEV1/SEV2: within 5 business days)
- Archive timeline
- Create follow-up tickets

______________________________________________________________________

## Postmortem Requirements

| SEV | Postmortem required? | Due |
|-----|---------------------|-----|
| SEV1 | Yes | Within 3 business days |
| SEV2 | Yes | Within 5 business days |
| SEV3 | Optional (recommended) | Within 2 weeks |
| SEV4 | No | — |

**Postmortem principles**:

- Blameless: the goal is to understand the system, not to assign fault
- Systems-focused: ask how the system allowed the failure, not who made the mistake
- Action-oriented: every postmortem produces action items with owners and due dates
- Complete timeline: minimum 5 entries; captures the full arc from detection to resolution

See `references/postmortem-template.md` for the full template.

______________________________________________________________________

## Escalation

- **`@oncall-xfn-team-devops`**: primary escalation path for infrastructure incidents (GKE, ES, Mongo, Redpanda)
- **Exec escalation**: SEV1 only — notify engineering leadership within 15 minutes of SEV1 declaration
- **Vendor escalation**: for third-party service outages (e.g., GCP, Cloudflare) — open support ticket and post in incident channel

______________________________________________________________________

## References

- [`references/comms-templates.md`](references/comms-templates.md) — Ready-to-use Slack and stakeholder communication templates
- [`references/postmortem-template.md`](references/postmortem-template.md) — Complete blameless postmortem template
