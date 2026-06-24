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

Print one resolved line before collecting evidence:

```text
window=<daily|weekly> since=<ISO8601> until=<ISO8601> shift_tz=America/New_York outgoing_oncall=<caller> pd_rotation=DevOps format=<text|html>
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

### Text Mode

Keep the report short, link-first, and action-oriented. Prefer one compact table over many
sections. Use Markdown links for PD, Slack, Grafana, Jira, and Notion pages when URLs are
available. Keep IDs visible in link text.

```markdown
## On-call handoff - <daily|weekly> - <window>

Scope: DevOps PD rotation, <caller>, <shift window>. Non-DevOps rotations excluded unless directly connected.

### Must know
- <up to 3 bullets the next on-call must know>

### Handoff items
| Item | State | Evidence | Possible next step |
| --- | --- | --- | --- |
| <linked alert/thread/ticket> | <active/resolved/noisy> | <linked PD/Slack/Grafana/Notion> | <owner + action> |

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
- Possible next steps: <1-3 short changes to reduce next week's PD/Slack load, or "none">
- FYI: <optional one-line context only if useful>
```

Use links and IDs verbatim. Mark confidence as `confirmed`, `likely`, or `unknown` when the
evidence is incomplete. Keep non-DevOps rotations out of the main sections unless they
create a DevOps action. Do not include an "Excluded" section in the report. Cap the handoff
table at 5 rows; summarize lower-value noise in one sentence. Keep possible next steps
brief; prefer one action sentence over process narration.

### HTML Mode

When `html` or `--html` is passed, create a Claude artifact with MIME type `text/html` that
contains the same evidence and recommendations as text mode. It must work in Cowork:

- create the artifact in the conversation; do not save a local HTML file unless the caller
  explicitly asks for a file;
- use one gathered report model for both text and HTML so the analysis does not diverge;
- use self-contained HTML with inline CSS only;
- do not use remote scripts, remote fonts, CDNs, local files, or external assets;
- optimize the first viewport for the next on-call: a short headline, active/repeated
  issues, and immediate actions;
- keep the tool/source area compact. Use icon-led chips such as `Current state: Slack, PD, Jira` and `References: Grafana, Notion, GitHub PRs`; do not add a `Mode: read-only` chip
  or verbose source-audit prose;
- call the handoff action column "Possible next step", not "Next action";
- add `title` hover text to Slack thread, PagerDuty, and Jira incident links when rendering
  HTML so a reader can tell what each evidence link represents before opening it;
- include a compact "Runbooks / skills" section that lists runbooks or guidelines updated
  during the window, relevant runbooks referenced but not updated, and any operational
  skills added. Include relevant GitHub Actions / deployment workflow runbooks when they
  explain a handoff item. Avoid source-mechanics phrasing such as "Glean showed"; state the
  page/update directly. Do not add filler sentences saying guidance was merely "referenced
  as existing guidance";
- in weekly mode, include a compact "Fatigue telemetry" section with PagerDuty alert counts
  and Slack message/thread counts for NAM and IST Monday-start weeks. Do not bury the
  interpretation: call out the top load driver and the smallest next action;
- omit an "Excluded" card/section. If excluded context matters, keep it to a single FYI
  line;
- make links visually obvious and keep the artifact scannable on mobile and desktop.

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

## Reuse These Skills

- `/apollo-eng-devops:oncall review` for the PD recurrence/no-runbook first pass. Note its PD
  scan always uses a fixed seven-day, now-anchored lookback, so use it only as a
  recurrence/no-runbook signal — re-scope the results to the resolved daily/weekly window
  (and any backdated `--date`) before summarizing, rather than adopting its seven-day window.
- `/apollo-eng-devops:incident-triage report` and `pd-reconcile` rules for Jira/PD update
  proposals.
- `/apollo-eng-devops:grafana-observability` for alert actionability, RED/USE checks, and
  runbook annotation expectations.
- `/apollo-eng-devops:logs-ingestion-rate` only when the alert matches that specific
  Grafana Cloud logs ingestion rate alert.
