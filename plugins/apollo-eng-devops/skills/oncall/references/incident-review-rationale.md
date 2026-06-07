# Why review the last week of incidents (and what to look for)

The weekly incident review is the cheapest reliability investment on-call makes. Its
purpose is not to re-litigate each page — it's to find the two patterns that compound:
**recurring failures with no fix** and **incidents with no runbook**.

## The argument (make this case every week)

- **A recurring alert with no runbook is repeated toil.** Each firing restarts diagnosis
  from zero. If an alert fired three times this week, surfacing it once and writing a
  runbook (or a fix) converts every future page into a 2-minute lookup — or eliminates it.
  This is the single highest-leverage thing a rotation does between incidents.
- **An incident with no linked runbook/RCA is an undocumented failure mode.** The next
  responder — maybe you at 3am next month — inherits zero context. A runbook ticket now is
  cheaper than a cold-start investigation later.
- **Quiet growth becomes a SEV1.** The email-3 outage's disk was at 70%+ for two weeks
  with no warning page. Reviewing trends weekly catches the slow burn while mitigation is
  still cheap (see the gameday `disk-saturation` card).

## What `incident_review.py` flags

- **Recurring** — the same alert (title normalized to drop `[FIRING:N]` markers) firing
  across a span **> 24h**. A >24h span distinguishes a recurring failure mode from a
  same-day flap/duplicate. This heuristic mirrors the duplicate-vs-recurring logic in
  `apollo-eng-devops/skills/incident-triage/references/pd-alerts.md`.
- **No runbook** — incidents whose body/notes contain no runbook / RCA / postmortem /
  `notion.so` link.

## Turning a finding into action

- **Recurring + no runbook** → propose an INFRA ticket for a runbook (draft the body; do
  not create until the owner agrees). Link the recurring incidents as `Relates`.
- **Recurring + has runbook but still firing** → the runbook isn't a fix. Propose tuning
  the alert or escalating for a real fix.
- **One-off, high blast radius** → confirm an RCA exists; if not, that's the gap.

For deeper triage of the Jira INCIDENT queue (routing, PD-state reconciliation), hand off
to the `incident-triage` skill — this review is the lightweight weekly skim, not full
triage.
