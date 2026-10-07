# Analytics Verification — {{experiment short name}}

<!-- The report file Stage B delivers. Offer to update the Stage A audit
where it lives; never assume. Classification and landing definitions:
references/verification-checks.md. Plain words throughout. -->

> **Does the build match the audit? {{Yes / Yes after {{N}} fixes / No: {{N}} gaps}}**
> {{Each gap as one plain sentence. That is the whole verdict.}}

## Events

Landing: ✅ verified in Amplitude · 🟡 staging only, not launched yet · ⏳ cannot
be verified until launch.

| What the user does / event | vs the audit | Both arms? | Landing | Amplitude |
|---|---|---|---|---|
| {{action — `Event Name`}} | {{built as specced / drifted: what / missing, built this run / extra}} | {{yes / what differs}} | {{✅ / 🟡 / ⏳}} | {{catalog link, or —}} |

{{One short note under the table per row that needs more than a cell: the exact
drift quoted from both sides, the variant condition found, the staging volume
pulled with date.}}

## Fixed in this run

{{Per approved fix: the event, what was built in one line, and the commit or
draft PR link. "None" if the build matched.}}

## Deferred

{{Gaps not fixed here and why: needs a spec from the team, belongs to another
PR, waiting on launch to verify. Each with an owner.}}

## Audit rows to update

{{Per row: before → after (Amplitude link added, name or trigger corrected to
the build, properties as they arrive, New → Preexisting). "None" if the audit
is current. Written to the audit: {{yes, where / no, left as is}}.}}

## Open questions

- {{question}} — {{engineer / DS / PM}}

<details>
<summary>How this was checked</summary>

- **Audit parsed from:** {{Notion link / pasted table / file, and date}}
- **Branch or commit verified:** {{sha or branch}}
- **Code searches:** {{the greps and file reads behind the classifications}}
- **Amplitude:** {{project(s), lookups, volume pulls and per-arm splits, with
  dates}}
- **Checks run on applied fixes:** {{test and typecheck commands, or "no fixes
  applied"}}

</details>
