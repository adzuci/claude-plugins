# Incident Communications Templates

Ready-to-use templates for incident communications. Replace `{{VARIABLES}}` with actual values before sending.

Variables used in templates:

- `{{SEV}}` — severity level (1, 2, 3)
- `{{IMPACT}}` — one-sentence user-facing impact description
- `{{AFFECTED_SERVICES}}` — comma-separated list of affected services
- `{{STATUS}}` — current status (investigating / identified / mitigating / monitoring / resolved)
- `{{ETA}}` — estimated time to resolution or next update
- `{{IC}}` — incident commander @handle
- `{{ACTIONS}}` — brief list of actions taken
- `{{NEXT_STEPS}}` — what is happening next
- `{{ROOT_CAUSE}}` — brief root cause summary (for resolution template)
- `{{DURATION}}` — incident duration (e.g., "47 minutes")

______________________________________________________________________

## Template 1: Incident Declaration

Post in `#incidents` (SEV1/SEV2) or `#eng-infrastructure-alerts` (SEV3).

```
[SEV{{SEV}}] INCIDENT DECLARED — {{AFFECTED_SERVICES}}

Impact: {{IMPACT}}
Status: Investigating
IC: {{IC}}

Timeline:
{{HH:MM}} UTC | Incident declared SEV{{SEV}} | {{IC}}

Next update in {{ETA}}.
```

______________________________________________________________________

## Template 2: Status Update

Post on cadence: every 15 min (SEV1), 30 min (SEV2), 60 min (SEV3).

```
[SEV{{SEV}}] UPDATE — {{AFFECTED_SERVICES}}

Impact: {{IMPACT}}
Status: {{STATUS}}

Actions taken:
- {{ACTIONS}}

Next steps: {{NEXT_STEPS}}
ETA: {{ETA}}
IC: {{IC}}
```

If there is nothing new to report, still send an update:

```
[SEV{{SEV}}] UPDATE — {{AFFECTED_SERVICES}}

No change since last update. Still investigating {{NEXT_STEPS}}.
IC: {{IC}}
Next update in {{ETA}}.
```

______________________________________________________________________

## Template 3: Resolution Announcement

Post in the same channel as the declaration.

```
[SEV{{SEV}}] RESOLVED — {{AFFECTED_SERVICES}}

Impact: {{IMPACT}}
Duration: {{DURATION}}
Root cause (preliminary): {{ROOT_CAUSE}}
Status: Resolved — monitoring for stability

Timeline summary:
[paste condensed timeline]

Follow-up:
- Postmortem scheduled: [date/time]
- Follow-up tickets: [links or TBD]

IC: {{IC}}
Thank you to everyone who helped.
```

______________________________________________________________________

## Template 4: Stakeholder Summary (Non-Technical Audience)

For exec or cross-functional stakeholders who need context without technical detail.

```
Subject: [SEV{{SEV}}] Service Incident — {{AFFECTED_SERVICES}} — {{STATUS}}

Summary:
We experienced a service disruption affecting {{IMPACT}}.

Duration: {{DURATION}}
Services affected: {{AFFECTED_SERVICES}}
User impact: {{IMPACT}}

What happened: [2-3 sentence plain English explanation]

Current status: {{STATUS}}

What we are doing next: {{NEXT_STEPS}}

We will share a full postmortem by [date]. Questions? Contact {{IC}}.
```

______________________________________________________________________

## Template 5: Escalation

Use when you need to escalate to `@oncall-xfn-team-devops` or engineering leadership.

```
Escalating SEV{{SEV}} incident.

Current situation: {{IMPACT}}
Services affected: {{AFFECTED_SERVICES}}
Time since declaration: [N] minutes
Actions taken so far: {{ACTIONS}}
Why escalating: [specific blocker or need — e.g., need DB access, need GCP support ticket, need exec awareness]

IC: {{IC}}
Incident channel: [link to thread]
```

______________________________________________________________________

## Template 6: All-Clear / Extended Monitoring

Use after resolution when declaring a monitoring window before fully closing.

```
[SEV{{SEV}}] MONITORING — {{AFFECTED_SERVICES}}

Mitigation applied. Monitoring for {{ETA}} before declaring fully resolved.
Metrics are returning to baseline.

If no further degradation: incident will be declared resolved at [time].
IC: {{IC}}
```

______________________________________________________________________

## Apollo-Specific Communication Notes

- **`#eng-infrastructure-alerts`**: This channel already has high alert volume. Use the structured template format so updates are distinguishable from automated alerts. Include severity tag in brackets at the start of every message.
- **Saturday 17:00 UTC**: The weekly staging ES restore runs at this time. If you see ES alerts around this time in staging, check this before declaring an incident.
- **`@oncall-xfn-team-devops`**: Primary escalation for infra incidents. Always escalate SEV1 immediately; do not wait to diagnose first.
- **Comms cadence is mandatory**: Even if the incident is complex and moving fast, send the scheduled update. "Still investigating, no change" is a valid update and better than silence.
