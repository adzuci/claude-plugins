# Postmortem Template

Blameless postmortem template for Apollo production incidents. Complete within 3 business days (SEV1) or 5 business days (SEV2).

**Postmortem principles**:

- Blameless: the system failed, not a person
- Systems-focused: ask how the system made failure possible or inevitable
- Action-oriented: every postmortem must produce concrete action items with owners and due dates

______________________________________________________________________

## Incident Metadata

| Field | Value |
|-------|-------|
| Incident ID | INC-YYYY-MM-DD-[SEV][N] |
| Severity | SEV[1/2/3] |
| Date/time declared | HH:MM UTC, YYYY-MM-DD |
| Date/time resolved | HH:MM UTC, YYYY-MM-DD |
| Duration | [N] hours [N] minutes |
| User impact | [Description of user-facing effect] |
| Services affected | [List of affected services] |
| Incident commander | [Name / @handle] |
| Tech lead | [Name / @handle] |
| Participants | [Names / @handles] |
| Postmortem author | [Name / @handle] |
| Postmortem reviewers | [Names / @handles] |

______________________________________________________________________

## Timeline

HH:MM UTC format. Minimum 5 entries. Capture the full arc: first signal → investigation → mitigation → resolution.

| Time (UTC) | Event | Owner |
|------------|-------|-------|
| HH:MM | [First signal or alert fired] | [Owner] |
| HH:MM | [Incident declared] | [IC] |
| HH:MM | [First hypothesis formed] | [Owner] |
| HH:MM | [Root cause identified] | [Owner] |
| HH:MM | [Mitigation applied] | [Owner] |
| HH:MM | [Metrics returning to baseline] | [Owner] |
| HH:MM | [Incident declared resolved] | [IC] |

Add as many rows as needed. Include dead ends and failed mitigation attempts — they are important for learning.

______________________________________________________________________

## Impact Summary

**User-facing impact**: [What did users experience? Be specific. "Users in the EU region could not complete sequence enrollments for 47 minutes."]

**Quantified impact**:

- Number of users affected: [N or estimated range]
- Number of failed requests / jobs / operations: [N]
- Revenue impact: [estimate or "unknown"]
- SLO impact: [which SLO, by how much]

______________________________________________________________________

## Root Cause

### What happened

[2-4 sentence plain English description of the root cause. No blame. Focus on the technical failure.]

### 5 Whys

Work backwards from the user-facing symptom to the root cause. Add more levels as needed.

1. **Why did users experience [symptom]?** Because [X].
1. **Why did [X] happen?** Because [Y].
1. **Why did [Y] happen?** Because [Z].
1. **Why did [Z] happen?** Because [W].
1. **Why did [W] happen?** Because [root cause].

### Contributing factors

Factors that made the incident worse, longer, or harder to detect (not root cause, but contributed):

- [Contributing factor 1]
- [Contributing factor 2]
- [Contributing factor 3]

______________________________________________________________________

## Detection

- **How was the incident detected?** [Alert / user report / manual observation / monitoring]
- **Detection lag**: [Time between incident start and first alert or detection]
- **Could monitoring have caught this sooner?** [Yes/No — if yes, explain what was missing]
- **Alert quality**: [Was the alert actionable? Did it have a runbook? Was the severity correct?]

______________________________________________________________________

## Response Assessment

### What worked well

- [Thing 1 that worked well in the response]
- [Thing 2 that worked well]

### What was slow or difficult

- [What caused delays in investigation or mitigation?]
- [What information was hard to find?]
- [What steps required manual intervention that could have been automated?]

### What was confusing

- [What was unclear about the system behavior during the incident?]
- [What runbook steps were missing or wrong?]
- [What communication gaps occurred?]

______________________________________________________________________

## SLO Impact

| SLO | Target | Measured during incident | Error budget consumed |
|-----|--------|-------------------------|-----------------------|
| [Service] availability | [N]% | [N]% | [N]% of [window] budget |
| [Service] p99 latency | < [N]ms | [N]ms avg during incident | — |

**Error budget remaining after incident**: [N]% of [30-day / monthly] window.

If error budget is now at risk or exhausted, reliability work should be prioritized in the next sprint.

______________________________________________________________________

## Action Items

Every action item must have an owner, due date, and category.

| # | Action item | Owner | Due | Category |
|---|-------------|-------|-----|----------|
| 1 | [Action description] | [@handle] | [YYYY-MM-DD] | [prevent / detect / mitigate / process] |
| 2 | [Action description] | [@handle] | [YYYY-MM-DD] | [prevent / detect / mitigate / process] |
| 3 | [Action description] | [@handle] | [YYYY-MM-DD] | [prevent / detect / mitigate / process] |

**Category definitions**:

- **prevent**: eliminates the root cause so this cannot happen again
- **detect**: improves monitoring or alerting so the next occurrence is caught faster
- **mitigate**: reduces the impact or duration of the next occurrence (better runbook, automation)
- **process**: improves team process, communication, or documentation

______________________________________________________________________

## Blameless Retrospective Prompts

Use these questions to guide the postmortem discussion. These are questions about the system, not about individuals.

1. What information did we have (or not have) that would have prevented this incident?
1. What made this incident harder to detect than it should have been?
1. What made this incident harder to mitigate than it should have been?
1. If this incident occurs again tomorrow, will we catch it faster? Mitigate it faster? If not, what needs to change?
1. Which action items from previous postmortems, if completed, would have prevented this incident?
1. What toil (manual work) did this incident create that should be automated?
1. Was the right team notified at the right time? If not, what needs to change in the escalation path?
1. Did the runbook help? If not, what was missing or wrong?
