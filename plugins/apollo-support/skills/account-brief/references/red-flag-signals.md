# Red-Flag Signals

A catalog of account risk signals with tiered severity and explicit thresholds.
Account Managers use these to spot trouble early.

## Core Discipline

Trace every flag to an explicit source value. Never invent a signal, a count, or
a threshold breach. Each raised flag must name the field or query it came from
and the value that crossed the threshold. If you cannot point to a source value,
do not raise the flag; note it as `unknown / needs checking` instead. When a
source is unavailable, say the signal could not be evaluated rather than assuming
it is clear.

Thresholds below are defaults. Treat them as parameters an AM can tune, not as
hardcoded business rules. Do not embed real ARR figures, account counts, report
ids, or org identifiers here; keep everything generic.

## Tiers

- **P0**: urgent, act today. Renewal or churn risk, or a customer-facing outage
  the account has escalated.
- **P1**: important, act this week. SLA breaches and negative trends that will
  become P0 if ignored.
- **P2**: watch. Early or soft signals worth noting in the brief.

## Signal Catalog

| Signal | Source field / threshold | Tier |
| --- | --- | --- |
| Exec escalation on the account | An escalation flagged by leadership or a customer exec, present in the ticket or CRM note | P0 |
| At-risk renewal | Salesforce renewal risk field set to at-risk (or equivalent), or renewal date inside the next N days with an open blocker | P0 |
| Open P0 ticket | Any support ticket at severity P0 that is still open | P0 |
| Open P1 ticket aging past SLA | A P1+ ticket open longer than its SLA target (default: P1 older than 3 business days) | P1 |
| Ticket volume spike | Open or net-new ticket count above the account's recent baseline (default: 2x the trailing weekly average) | P1 |
| Negative CSAT | A CSAT response below the account's threshold (default: any 1 or 2 out of 5), or a downward CSAT trend | P1 |
| Repeated reopen | The same ticket or issue reopened more than once (default: 2 or more reopens) | P1 |
| Usage decline | A sustained drop in product usage versus the account's baseline (default: down 25% or more over the trailing period) | P2 |
| First-response SLA miss | First response later than the SLA target on a recent ticket | P2 |
| Stale open ticket with no owner | An open ticket with no assigned owner past the triage window | P2 |

## Raising A Flag

For each flag included in the brief, record:

- `tier`: P0, P1, or P2.
- `signal`: the catalog name.
- `detail`: the concrete value that crossed the threshold (for example, "P1
  ticket #123 open 5 business days, SLA 3").
- `source`: where the value came from (for example, "Snowflake ticket query" or
  "Salesforce renewal_risk field"). Mark Unverified when it came from a paste
  rather than a live query.

Order flags P0 first. The renderer sorts by tier automatically, but keep the
detail specific so a reader can act without re-deriving the finding.
