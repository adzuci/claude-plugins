---
name: oncall-handoff
description: Manual-invocation only. Produce a daily or weekly DevOps PagerDuty handoff focused on the outgoing caller's on-call shift, using Slack, PD, Grafana, Jira, and Notion/Glean evidence. Run via /apollo-eng-devops:oncall-handoff.
argument-hint: "[daily|weekly] [html|--html] [--date YYYY-MM-DD] [--days N]"
disable-model-invocation: true
---

# On-Call Handoff

Produce a concise handoff for the outgoing DevOps on-call. The goal is to set the next
DevOps on-call up for success, reduce MTTR, protect uptime, and turn repeated toil into
process improvements.

This skill is read-only by default. It proposes follow-up work, comments, runbook changes,
and guideline updates, but it does not mutate Slack, PagerDuty, Grafana, Jira, or Notion
unless the caller later gives explicit approval for a separate action.

## Invocation

```text
/apollo-eng-devops:oncall-handoff [daily|weekly] [html|--html] [--date YYYY-MM-DD] [--days N]
```

Defaults:

| Argument | Default | Meaning |
| --- | --- | --- |
| `daily` / `weekly` | `daily` | Handoff window. |
| `--days N` | `1` for daily, `7` for weekly | Overrides the lookback window. |
| `--date YYYY-MM-DD` | today | Window end date in the caller's local timezone. |
| `html` / `--html` | off | Render a shareable Claude artifact instead of only text. |

Assume the caller is the outgoing DevOps on-call for the selected window unless they name a
different owner. Resolve the caller's DevOps rotation and shift window from PagerDuty when
possible. If PagerDuty is unavailable and no exact shift window is supplied, ask for the
shift window rather than applying a person-specific default. Adam-specific fallback details
live in [`references/adam-defaults.md`](references/adam-defaults.md) and apply only when
the caller is Adam or explicitly requests that fallback. Even for Adam, PagerDuty is
preferred; the reference file is a last-resort fallback for runs where PagerDuty cannot
resolve the shift.

Daily mode should focus on the caller's most recent or current on-call shift, not the
entire company's last 24 hours. Weekly mode may look across seven days, but it must still
prioritize the caller's DevOps rotation and clearly separate in-shift DevOps work from
supporting context. Weekly mode must also include on-call fatigue telemetry for the
Monday-start week containing the requested date, using both NAM and IST shift calendars.

## Preflight

### Daily Window Resolution

When resolving "today's" shift window for `daily` mode without an explicit `--date`, do not
assume the current calendar date's shift is the right one:

- Compute the caller's current time in the shift timezone (`shift_tz`, default
  `America/New_York`).
- If today's shift window start is still in the future relative to now, the shift has not
  started yet: resolve to the immediately prior calendar day's shift (the most recently
  *completed* shift), not the not-yet-started one.
- If now falls inside today's shift window, use today's in-progress shift as-is.
- If now is after today's shift end, today's now-completed shift is correct as-is.
- When PagerDuty is available, cross-check this resolution against the caller's actual
  on-call schedule (`/oncalls`) for the window in question. If PagerDuty disagrees with the
  computed window, state the mismatch in preflight rather than silently trusting the static
  default (see `references/adam-defaults.md`).
- An explicit `--date` always wins; skip this fallback when `--date` is supplied.
- Carry the same completed / in-progress / not-yet-started distinction into the report
  itself (see Output below) — it is reader-facing context, not just an internal preflight
  check. Weekly or multi-shift reports label each covered shift this way individually.

Print one resolved line before collecting evidence:

```text
window=<daily|weekly> since=<ISO8601> until=<ISO8601> shift_tz=America/New_York outgoing_oncall=<caller> pd_rotation=DevOps format=<text|html>
```

When the resolved window is not the naive "today's calendar date" shift, append a short
reasoning clause so the fallback is visible, for example:

```text
window=daily since=2026-08-20T14:00:00Z until=2026-08-21T02:00:00Z shift_tz=America/New_York outgoing_oncall=Adam pd_rotation=DevOps format=text (resolved to previous shift: current time precedes today's shift start)
```

Then print a compact tool table:

```text
Tools: Slack <ok/missing>  PagerDuty <pd-cli/mcp/missing>  Grafana <ok/missing>  Jira <acli/mcp/missing>  Notion/Glean <ok/missing>
```

If PagerDuty or Jira is missing, add one concise setup/fallback line after the tool table:

```text
Setup: pd missing -> install @pagerduty/cli + pd login; Jira using MCP fallback; see references/cli-setup.md.
```

Use the best available read path:

- During preflight, read [`references/cli-setup.md`](references/cli-setup.md) and check
  whether `pd` and `acli` are installed/authenticated before collecting PagerDuty or Jira
  evidence. If either CLI is missing or unauthenticated, do not install or authenticate
  during the handoff unless the caller explicitly approves a separate setup action; instead,
  show the install/auth hint and use an available MCP fallback when present.

- **Slack**: read/search channels and threads through the Slack connector when available.
  For weekly fatigue counts, prefer the local Slack CLI path described in
  [`references/oncall-fatigue.md`](references/oncall-fatigue.md); use connector reads or
  saved JSON as a fallback and label those counts approximate.

- **PagerDuty**: prefer the existing `oncall` skill's `pd` CLI setup; use a PagerDuty MCP
  only if it is already available. If neither works, mark live PagerDuty current-state
  checks incomplete and continue from Slack/Jira/Glean evidence.

- **Grafana**: use the Grafana MCP for dashboard summaries, panel evidence, Prometheus, or
  Tempo only when an alert needs current context.

- **Jira**: prefer Atlassian CLI reads when available:

  ```bash
  acli jira workitem view <KEY> --fields key,issuetype,summary,status,assignee,priority,updated --json
  acli jira workitem search --jql "<JQL>" --fields key,issuetype,summary,status,assignee,priority,updated --json
  ```

  Use Jira MCP/read tools as a fallback when they are already available, then Glean/Notion
  indexed Jira results as a degraded fallback. Keep the path visible in the tool table
  (`Jira acli`, `Jira mcp`, `Jira via Glean`, or `Jira missing`).

- **Notion/Glean**: use Notion or Glean search/read for runbooks and on-call guideline gaps.

If a source is unavailable, say exactly what was not checked and continue with degraded
confidence. Do not invent evidence.

## Scope and Source Order

Start with the caller's DevOps on-call scope and only widen when the evidence connects
directly to DevOps ownership, customer impact, a Sev0/Sev1 incident, or a handoff action.

Use the source order, channel list, scope exclusions, and runbook/guideline checks in
[`references/source-order.md`](references/source-order.md). The guideline target is
`DevOps / Infrastructure Oncall Guidelines` (`32fab2b3b49680699bf1c1191364dc30`); if the
link breaks, search Notion/Glean by that title and ID.

In weekly mode, also read [`references/oncall-fatigue.md`](references/oncall-fatigue.md)
and run the fatigue helper before writing the report:

```bash
python3 plugins/apollo-eng-devops/skills/oncall-handoff/scripts/oncall_fatigue.py \
  --week-of <YYYY-MM-DD> \
  --output-json /tmp/oncall-fatigue.json \
  --markdown /tmp/oncall-fatigue.md
```

The helper counts DevOps PagerDuty alerts and Slack CLI-visible message volume in
`#xfn-h-devops`, `#incident-response-sev0-sev1`, and the DevOps alert stream
(`#eng-infrastructure-alerts` / `#infrastructure-alerts`, used as the current
`#devops-alerts` alias). It buckets the Monday-start week by NAM (`America/New_York`,
10:00-22:00) and IST (`Asia/Kolkata`, 08:30-20:30) calendars.

For weekly reports, search Notion/Glean for runbooks or guidelines updated during the
Monday-start week and classify them as:

| Result | Proposal |
| --- | --- |
| Updated related runbook/guideline | Mention what changed and which alert/request it helps. |
| Good runbook found but not updated | Propose linking it from the alert/Jira/PD context. |
| Partial or stale runbook found | Propose the exact update needed. |
| No runbook found | Propose creating a stub runbook or INFRA ticket. |
| Search unavailable | Mark as unverified and include the missing access/tool. |

Also inspect the plugin/skill repository for new or changed operational skills under
`plugins/apollo-eng-devops/skills` during the window when local git history is available.
If local history is incomplete, search GitHub PRs in `apolloio/claude-plugins` and relevant
runtime repos such as `apolloio/leadgenie` for skill PRs created or updated during the
window. Mention skills only when they plausibly reduce on-call toil or improve incident
response. Do not write a generic "none found" skill row unless GitHub PRs were checked and
there were genuinely no relevant operational skill changes.

## Output

### Report Content Model

Both text and HTML reports share one content model — gather the evidence once, then render it
per mode. Only include areas 4-8 when the window actually has content for them; a quiet
single-incident (or zero-incident) day can skip Deployments, Investigations, and Toil cleanup
entirely and stay a short report.

1. **Header** — org/rotation/caller, plus each covered shift's short local date and whether it
   is completed, in-progress, or not-yet-started (the same distinction Preflight's Daily
   Window Resolution computes).
2. **Stats** — high-urgency count, low-urgency count, resolved-same-day count, still-open /
   active-gap count. Purely numeric, scannable at a glance.
3. **Must know** — 3-5 bullets, in this order: the most urgent/open item first, the most
   recent significant event next, then toil/recurring items, then a source-confidence caveat
   if one affects trust in the above.
4. **Incidents** — the full in-window PD incident table (uncapped; see Verification in
   [`references/source-order.md`](references/source-order.md)), plus a short root-cause note
   per incident (e.g. "traced to X, closed out in-thread, no action needed" vs "still needs
   follow-up").
5. **Deployments** — production-deployment channel failures and any DevOps-relevant thread in
   the window; see the Deployments channel step in
   [`references/source-order.md`](references/source-order.md).
6. **Investigations** — one entry per active cross-cutting investigation that spans 2+ linked
   tickets/threads: a relationship diagram, a plain-language root cause, a recommendation, and
   an explicit "what couldn't be verified" note naming any unavailable tool (Cloudflare, New
   Relic, live Slack, etc.) rather than silently omitting the limitation.
7. **Toil cleanup** — triggers when the same alert produced 3+ near-identical open tickets: a
   ticket inventory, a consolidation plan (canonical ticket + duplicate links, per the
   existing convention in
   [`incident-triage/references/duplicate-heuristics.md`](../incident-triage/references/duplicate-heuristics.md)
   rather than a new one), and a runbook stub draft if Notion/Glean search confirms none
   exists.
8. **Gaps & runbooks** — the existing gap logic, plus a "Source confidence" note per source
   (live / degraded / unavailable and why — e.g. the Slack Fallback caveat in
   [`references/cli-setup.md`](references/cli-setup.md)).
9. **Footer** — the provenance line (see HTML Mode).

### Text Mode

Keep the report short, link-first, and action-oriented. Prefer one compact table over many
sections. Use Markdown links for PD, Slack, Grafana, Jira, and Notion pages when URLs are
available. Keep IDs visible in link text.

Show the handoff window in short local-date form in the human-facing header and Must-know
area (e.g. `Aug 20, 10:00-22:00 ET`), not raw ISO8601. ISO8601 stays in the machine-readable
preflight line and in evidence-table timestamps where precision matters. Label each covered
shift as `completed`, `in-progress`, or `not-yet-started` in the header, mirroring the Daily
Window Resolution outcome.

```markdown
## On-call handoff - <daily|weekly> - <caller> - DevOps

<Aug 20, 10:00-22:00 ET - completed> [one line per covered shift in weekly/multi-shift mode]

Scope: DevOps PD rotation, <caller>, <shift window>. Non-DevOps rotations excluded unless directly connected.

Stats: <H> high-urgency · <L> low-urgency · <R> resolved same day · <G> open gaps

### Must know
- <most urgent / still-open item>
- <most recent significant event>
- <toil / recurring item>
- <source-confidence caveat, only if one affects trust in the above>

### Handoff items
| Item | State | Evidence | Possible next step |
| --- | --- | --- | --- |
| <linked alert/thread/ticket> | <active/resolved/noisy> | <linked PD/Slack/Grafana/Notion> | <owner + action> |

### Incidents in window
| Time | Urgency | Service | Link |
| --- | --- | --- | --- |
| <local time> | <high/low> | <PD service> | <linked PD incident> |

Add a one-line root-cause note under this table for any incident worth explaining (e.g.
"traced to X, closed out in-thread, no action needed" vs "still needs follow-up"). If the
resolved window truly had zero PD incidents, keep this table but state which queries
confirmed it, e.g. "0 incidents (DevOps-scoped and company-wide cross-check both agree)"
instead of a bare "zero incidents" line.

### Deployments
Include only when the deployments channel had a DevOps-relevant failure or thread in the window.
- <production-deployment channel failure or thread, with link>

### Investigations
Include only when 2+ linked tickets/threads form an active cross-cutting investigation.
- <name> — <plain-language root cause>. Recommendation: <recommendation>. Not verified: <unavailable tool(s), or "none">.

### Toil cleanup
Include only when the same alert produced 3+ near-identical open tickets.
| Ticket | Summary | Status | Canonical / duplicate |
| --- | --- | --- | --- |
| <linked ticket> | <summary> | <status> | <canonical or "duplicate of <canonical>"> |
- Consolidation plan: <canonical ticket + proposed duplicate links, per `incident-triage/references/duplicate-heuristics.md`>
- Runbook stub: <proposed stub, or "existing runbook found: <link>">

### Fatigue telemetry
| Surface | NAM week | IST week | Read |
| --- | ---: | ---: | --- |
| PagerDuty alerts | <count / in-shift / off-shift> | <count / in-shift / off-shift> | <what this means> |
| #xfn-h-devops messages | <count / thread count> | <count / thread count> | <request-load read> |
| #incident-response-sev0-sev1 messages | <count / thread count> | <count / thread count> | <incident-load read> |
| #eng-infrastructure-alerts messages | <count / thread count> | <count / thread count> | <alert-noise read> |

### Gaps / notes
- Runbook/guideline gaps: <linked proposal or "none found">
- Runbooks / skills: <runbooks or guidelines updated/referenced during the window; new skills added, or "none found">
- Source confidence: <per-source live/degraded/unavailable note, e.g. "Slack: no live access, reconstructed from Jira-linked threads per the Slack Fallback order">
- Possible next steps: <1-3 short changes to reduce next week's PD/Slack load, or "none">
- FYI: <optional one-line context only if useful>
```

Use links and IDs verbatim. Mark confidence as `confirmed`, `likely`, or `unknown` when the
evidence is incomplete. Keep non-DevOps rotations out of the main sections unless they
create a DevOps action. Do not include an "Excluded" section in the report. Cap the
**Handoff items** table at 5 rows; summarize lower-value noise in one sentence. The
**Incidents in window** table is not subject to that cap — it exists so a reader can verify
the incident count and urgency mix themselves. Omit **Deployments**, **Investigations**, and
**Toil cleanup** entirely on a quiet day rather than printing "none" for all three; keep
possible next steps brief and prefer one action sentence over process narration.

### HTML Mode

When `html` or `--html` is passed, create a Claude artifact with MIME type `text/html` that
contains the same evidence and recommendations as text mode. It must work in Cowork:

- create the artifact in the conversation; do not save a local HTML file unless the caller
  explicitly asks for a file;
- use one gathered report model for both text and HTML so the analysis does not diverge;
- use self-contained HTML with inline CSS only;
- do not use remote scripts, remote fonts, CDNs, local files, or external assets;
- structure the first viewport as: an eyebrow (org / rotation / caller), a title, and a
  subtitle stating each covered shift's short local date (e.g. `Aug 20, 10:00-22:00 ET`) and
  whether it is completed, in-progress, or not-yet-started; a stat row of small cards for
  high-urgency count, low-urgency count, resolved-same-day count, and still-open/active-gap
  count; then a "Must know" card with an accent-colored left border holding 3-5 bullets
  ordered per the Report Content Model above (most urgent/open item, most recent significant
  event, toil/recurring items, then any source-confidence caveat). Keep this whole viewport a
  short scannable summary;
- make tabs the **default** layout once there is enough content to warrant them, not merely
  an allowed option: **Incidents** (the full, uncapped in-window incident table plus a
  root-cause note per incident), **Deployments**, one tab per active **Investigation**, and
  **Toil cleanup**, plus an always-present **Gaps & runbooks** tab. A quiet single-incident
  (or zero-incident) day may stay a single panel instead of tabs — don't force empty tabs;
- in each Investigation tab, include a Mermaid relationship diagram
  (`<pre class="mermaid">...</pre>`) showing how the linked tickets/threads connect, a
  plain-language root-cause writeup, a recommendation, and an explicit "what couldn't be
  verified" subsection naming which tools were unavailable (Cloudflare, New Relic, live
  Slack, etc.) rather than silently omitting the limitation;
- in the Toil cleanup tab, include a ticket inventory table, a consolidation plan (canonical
  ticket plus duplicate links, following the existing convention in
  `incident-triage/references/duplicate-heuristics.md` rather than inventing a new one), a
  Mermaid tree diagram (canonical -> duplicates), and a runbook stub draft when Notion/Glean
  search confirms none exists. Keep this tab's language about any named person's open ask
  neutral and outcome-focused (see Safety Rules) — do not draft a "please respond" nudge
  inside the report;
- when the on-call alias tag sweep (see `references/source-order.md`) returns results, show
  deployment-failure-related mentions first and collapse the rest behind a
  `<details>`/`<summary>` labeled with the total count, so incidental pings don't dominate the
  view. Note plainly if the search tool indicated more results existed than were pulled;
- keep the tool/source area compact. Use icon-led chips such as `Current state: Slack, PD, Jira` and `References: Grafana, Notion, GitHub PRs`; do not add a `Mode: read-only` chip
  or verbose source-audit prose;
- call the handoff action column "Possible next step", not "Next action";
- add `title` hover text to Slack thread, PagerDuty, and Jira incident links when rendering
  HTML so a reader can tell what each evidence link represents before opening it;
- in the Gaps & runbooks tab, include a compact "Runbooks / skills" section that lists
  runbooks or guidelines updated during the window, relevant runbooks referenced but not
  updated, and any operational skills added, plus a "Source confidence" subsection listing
  each source's live/degraded/unavailable status and caveats (e.g. "Glean's Slack index has
  real gaps — an exact permalink not found there means 'not indexed,' not 'didn't happen,'"
  per the Slack Fallback section in `references/cli-setup.md`). Include relevant GitHub
  Actions / deployment workflow runbooks when they explain a handoff item. Avoid
  source-mechanics phrasing such as "Glean showed"; state the page/update directly. Do not
  add filler sentences saying guidance was merely "referenced as existing guidance";
- in weekly mode, include a compact "Fatigue telemetry" section (its own tab, or folded into
  Gaps & runbooks) with PagerDuty alert counts and Slack message/thread counts for NAM and
  IST Monday-start weeks. Do not bury the interpretation: call out the top load driver and
  the smallest next action;
- omit an "Excluded" card/section. If excluded context matters, keep it to a single FYI
  line;
- make links visually obvious and keep the artifact scannable on mobile and desktop;
- include a small, muted footer stating which skill/invocation produced the artifact (e.g.
  `Generated by /apollo-eng-devops:oncall-handoff daily DevOps 10-10pm html`) plus a one-line
  note on how to regenerate or correct it (e.g. re-invoke the skill with corrected
  `--date`/window args, or where to raise a correction).

## Safety Rules

- Propose, do not mutate, during the handoff pass.
- Never close Jira just because PD resolved. PD state is alert state; Jira state is the
  human follow-up loop.
- Require Slack thread confirmation before proposing close/no-action for a resolved PD.
- Do not create Jira tickets, Jira comments, PD overrides, Slack posts, Grafana changes, or
  Notion pages without a later explicit approval naming the item.
- For missing runbooks, propose linking, updating, or creating one. Do not create the page
  or ticket during the initial handoff.
- If the on-call guideline has a gap, suggest the update text or ticket body rather than
  editing the guideline directly.
- These reports are routinely shared with named colleagues mentioned in them. When
  describing a pending ask or unresolved toil involving a specific named person, keep the
  language neutral and outcome-focused (what's open, what's next) — do not draft, embed, or
  imply a "please respond" follow-up message addressed at that person inside the report
  itself. Any such nudge is a separate, human-sent message, not report content. This matters
  most in the Toil cleanup area.

## Reuse These Skills

- `/apollo-eng-devops:oncall review` for the PD recurrence/no-runbook first pass. Note its PD
  scan always uses a fixed seven-day, now-anchored lookback, so use it only as a
  recurrence/no-runbook signal — re-scope the results to the resolved daily/weekly window
  (and any backdated `--date`) before summarizing, rather than adopting its seven-day window.
- `/apollo-eng-devops:incident-triage report` and `pd-reconcile` rules for Jira/PD update
  proposals. Its `duplicate-heuristics.md` reference is the existing convention for
  canonical-ticket selection and `Duplicate`/`Relates` issue links — reuse it for the Toil
  cleanup consolidation plan rather than inventing a new dedupe convention.
- `/apollo-eng-devops:grafana-observability` for alert actionability, RED/USE checks, and
  runbook annotation expectations.
- `/apollo-eng-devops:logs-ingestion-rate` only when the alert matches that specific
  Grafana Cloud logs ingestion rate alert.
