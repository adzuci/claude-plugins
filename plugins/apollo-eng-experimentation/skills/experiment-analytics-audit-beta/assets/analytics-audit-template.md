# Analytics Audit — {{experiment short name}}

<!-- The audit file Stages A and C deliver, and the skeleton for a Notion export
when the team wants one. Teams on the Experiment ERD template have this as a
pre-created page with an inline Experiment Events database:
https://app.notion.com/p/apolloio/Analytics-Audit-752883bcb695462e818b2d808d89181f
The table below mirrors its columns. Layout and rules:
references/audit-doc-format.md. Plain words throughout: no working statuses,
no grades. -->

> **Can we measure this experiment yet? {{Yes / Not yet: {{N}} things to fix first}}**
> {{Each blocker as one plain sentence.}}

> **TL;DR** {{3–4 lines: which events carry the experiment, the properties that
> answer what, where, and which arm, and the intent-vs-success rule of thumb.}}

## Experiment events

| Action | Event Name | Trigger | Properties | Description | Status | Amplitude Link |
|---|---|---|---|---|---|---|
| | | | | | {{Preexisting / New}} | {{catalog link, blank for New}} |

## Open questions

- {{question}} — {{engineer / DS / PM}}

<details>
<summary>How this was checked</summary>

- **Built on:** {{pre-analysis plan}}{{ · exposure-design hand-over}}
- **Replaces:** {{prior audit and date, or "first audit"}}
- **Branch or commit:** {{sha or branch}}
- **Code searches:** {{the greps and file reads behind the findings}}
- **Amplitude:** {{project id, lookups and volume pulls, with dates}}
- **Snowflake:** {{queries run, or "not needed"}}
- **Metric split from:** {{DB entry Metrics tables / {{name}} on {{date}}}}

</details>
