# TapData / Mason

This file is a routing aid, not an ownership declaration. Verify current vendor coverage
and availability before depending on it for urgent work.

## Context

TapData is Apollo's MongoDB consulting partner. Mason More is the clearest recurring
TapData contact in recent Mongo operational threads.

Use TapData/Mason for cluster-internal Mongo questions, especially:

- balancer behavior
- shard draining or chunk migration
- range deleter and orphan cleanup
- stale config / mongos routing questions
- replication lag patterns
- major topology changes
- low-confidence root-cause analysis where app query evidence is insufficient

Prefer `#eng-devops-mongo` for TapData questions so the answer becomes searchable for the
team. Use DMs only when there is an existing private vendor workflow or an incident
commander explicitly chooses that route.

## Evidence-backed contact

- Mason More: Slack `mason.tapdata`, user id `U040ATU6RGU`, Engineering Consultant.

## Useful source links

These are point-in-time evidence links that may expire or move; confirm the current thread
or contact before relying on them.

- TapData coordination thread:
  `https://apolloio.slack.com/archives/C02AER97N82/p1779899686818969`
- Email cluster incident thread involving Mason/TapData:
  `https://apolloio.slack.com/archives/CCHSWB3DK/p1779622442449779`
