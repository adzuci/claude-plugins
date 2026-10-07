# Weekly Mode

Full procedure for `--weekly <team>`, loaded by `SKILL.md`. Paths such as `references/...` are relative to the skill directory.

`--weekly <team>` drafts the team's reply in its weekly OKR thread by copying the format of the team's own last human-written post. Everything team-specific (channel, poster, trackers, metrics, targets) comes from the team file; these steps never assume a team, quarter, metric, or Jira site.

Manual runs ask at most one question (missing team file, missing or ambiguous parent, already posted, or metric values to paste). If several apply, combine them into that one message, except: if the update is already posted, ask only "draft anyway?" first and ask for metric values only after a yes, so no one pastes for a draft they will not use. `--routine` runs never prompt and end with one line: draft link plus gaps.

## W0 -- Fix the Dates

Compute these once from today's date and reuse them everywhere:

- **Reporting week**: the last completed Monday-Saturday week. On Monday 2026-10-05 that is 2026-09-28 to 2026-10-03.
- **Week start**: that Monday. **Data through**: the last complete day in that week (the Saturday, or yesterday if earlier).
- **Prior week**: the Monday-Saturday week before it, used for trend metrics.
- **Current period**: derive the quarter or period label from the template post, the team's current OKR tracker, or the date, in that order. Never reuse a period label from a source whose dates have already ended.

## W1 -- Load the Team File

Read `references/weekly-teams.md`, match `<team>` case-insensitively against the Team and Aliases columns, then read the linked file under `references/weekly-teams/`. Use only the fields that file defines. Fields marked `TODO` count as missing.

If there is no row or the required Slack fields are missing: manual asks once for the channel, parent search phrase, and poster; routine stops with `Skipped: <team> has no team file`.

## W2 -- Find the Anchor Parent and Template Post

1. Search the team's channel with `slack_search_public_and_private` for the parent search phrase, last 30 days, bots included. Do not filter parents by author: a `[Scheduled message]` parent may have no author at all. If search returns no parent, read the channel with `slack_read_channel` for the same 30 days and match the phrase in message text.
1. The newest matching thread parent is the anchor. Human, bot, and authorless `[Scheduled message]` parents are all valid. Its `ts` is the draft `thread_ts`.
1. Read the anchor thread, then up to 2 earlier parents (max 3 total). The template is the newest reply across those threads that meets all of:
   - author is the team file's poster Slack user ID (email, if shown, ends in `apollo.io`)
   - not a bot (`slack-bots.com` address) and not a scheduled message
   - has at least 2 bold or italic headers, or a status emoji (filters out nudges), unless the team file sets a `Template filter hint`, which replaces this check
1. The template may sit under an older parent. The draft still goes to the anchor `thread_ts`, never to the thread the template came from.
1. If the template is in the anchor thread itself, this week's update is already posted: manual asks whether to draft anyway; routine stops with `Already posted: <permalink>`. When drafting anyway, warn that the draft goes to a thread that already holds the post, and use the previous post (the newest qualifying reply from the earlier parents) as the baseline for the Risks comparison and for carried-over Next 2 weeks items, never the already-posted reply itself.
1. If no template is found, use `references/weekly-template-fallback.md`.

Copy the template's section order, header style (italic vs bold, trailing colons), bullet style (including nested bullets), and link style. Only the content changes. If a header names a period (for example "Big rocks, rest of <period>"), replace the label with the current period from W0.

If Slack search or read fails, stop. If no parent exists in 30 days: manual asks for a thread permalink; routine aborts with `No <phrase> parent in the last 30 days`. If two parents look equally current, manual asks which one; routine uses the newest.

## W3 -- Gather Evidence (Bounded)

**Work tracker.** If the team file's tracker is Jira, run exactly these 3 queries with any available `searchJiraIssuesUsingJql` tool (a plugin Atlassian MCP or the claude.ai Atlassian connector both work; if one is unauthenticated, use the other before degrading). Pass the team file's Jira host as `cloudId`, request only `fields: summary,status,priority,updated,resolutiondate,created`, and `maxResults: 20`. The created and resolved bounds live in the JQL.

```text
1. project in (<JIRA_PROJECTS>) AND resolved >= "<WEEK_START>" AND created >= -365d ORDER BY resolved DESC
2. project in (<JIRA_PROJECTS>) AND statusCategory = "In Progress" AND status != "<BLOCKED_STATUS>" AND updated >= -14d ORDER BY priority DESC, updated DESC
3. project in (<JIRA_PROJECTS>) AND status = "<BLOCKED_STATUS>" AND updated >= -30d ORDER BY updated DESC
```

`<WEEK_START>` is the W0 week start, not a rolling 7 days. Query 1 has no upper bound on purpose: wins resolved after the data-through day but before the draft date (for example the following Monday) count, because the draft goes out after the week ends. Query 2 excludes the blocked status because many Jira sites put it in the In Progress category. If the tracker is another tool (for example Notion), open at most 10 items linked from the template with any tool that reads it and record their current status. If no tool works, keep the template's items, mark them `status not verified`, and add a Gaps line.

**Metrics.** If the team file maps no metrics, skip this and do not ask. Never call a skill marked `disable-model-invocation: true` through the Skill tool. For each metric in the team file:

- Manual run: print the exact slash commands from the team file with the W0 window filled in, for both the reporting week and, for trend metrics, the prior week. Spend the one allowed question asking the user to paste the values, list each required value from the team file's metric table (window, component, and any incident count), and name the team's manual source. Use only pasted values. When a source shows a rounded headline and a more precise figure, ask for the precise one and state which window it covers.
- Routine run: write `<metric>: unavailable` in the draft and a `Gaps:` entry naming the command to run.
- If a model-invocable metric skill runs but fails (VPN, Grafana/Snowflake access), write `<metric>: unavailable (<reason>)`.

A trend claim needs the prior-week value. Without it, report the current value only. Never fill a value from memory or from the template.

**Highlights.** If the team file names a highlights source, read it with `response_format: detailed` so you capture each message `ts` for the source map. Use the latest post whose first line (trimmed) matches the team file's header regex, not the newest bot message. If none matches, omit highlights.

**Targets.** Read KR targets from the team file, which records last-known values with provenance, and confirm them against the team's current OKR tracker when it is readable. Templates and trackers carry stale numbers: a "Baseline" column or a second target column is the prior period's baseline, never current status or the current target. Never present a baseline as current. If a target is unknown or unconfirmed, say so instead of picking a color.

## W4 -- Write the Draft

**Status header.** Pick a status color only when observed values beat or miss confirmed targets, or the current tracker's status column states it for the reporting period. Color scale: green when every confirmed target is met; yellow when a target is missed but still reachable by the end of the period; red only when the period target is out of reach. Test reachability from period-to-date values: compute the average the remaining weeks would need to hit the target, and call it out of reach if that exceeds the best weekly value seen this period (or the metric's possible maximum). A count cap (for example at most N incidents) is out of reach once the count exceeds N. If period-to-date values are unavailable, use yellow and add a Gaps line `reachability not verified`. If the tracker's status column states a different color, show it as the tracker's status next to the observed one. Show the one-line reasoning in the Why section. Otherwise replace the template's status line, in its own header style, with `<Team> OKR Status: pending metrics`. If the template has a "Why <color>?" section, retitle it `Why pending?` and list the missing inputs; if not, add `Why pending?` right after the status line. Never output a status emoji for a pending status, and never copy the template's color.

**Wins and risks.** Put wins under the template's wins section (for example Highlights or Shipped), highlights-source wins first, then work-tracker items resolved in the reporting week (Jira query 1, or verified tracker items) only if the highlights source does not already cover them. If the highlights source lists risks, add a Risks section right after the wins section, in the template's header style. Drop empty asks lines such as "Open asks: none".

**Selection rules.**

- Verify each cited ticket's resolved date (`resolutiondate`) before listing it (query 1 results, or `getJiraIssue` for keys only the highlights source cites). Drop highlights items resolved before the reporting week: stale items are not highlights.
- Drop rollover closes: tickets resolved on the week-start day with no comments or status changes earlier in the week (a sprint-rollover close, not that week's work). Also drop items already listed in the previous post.
- Skip tickets resolved while still in an In Review status, and tickets created more than a year ago.
- Check every "done", "merged", or "hardened" claim against the ticket's current status and any comments from the week start through today (not only the reporting week). If something failed after merge, report the failure, not the win.
- Next 2 weeks: the template's still-open items, plus at most 2 new high-priority in-progress items from Jira query 2 when the tracker is Jira. No "in progress" suffixes.
- Risks: list only risks that are new or changed since the template post's Risks section (new, escalated, newly blocked, newly unblocked, or with a changed plan or date). Do not repeat unchanged open P1s or long-standing blocked items (created more than 14 days ago and already in the previous post; judge by created date and comments, since bulk sprint updates make `updated` unreliable); if nothing is new or changed, omit the Risks section. When a risk is unchanged but still material, point to the prior post in one short line only if the user asks for it.
- Hedging: apply hedge wording only to goals that are not committed (stretch, unsized, not in the current sprint or plan, or dependent on an open decision). Mark them with the template's own hedge marker, or `[reach goal]` if it has none. Committed work gets plain wording with no hedges, and the draft states the commitment status, not a guess. If commitment is unclear, treat it as committed and note the doubt in the Gaps line.
- 3-4 bullets per section. Merge related items into one bullet. Carried-over Next 2 weeks items from the template are exempt from the cap (up to 5); new items still count.

**Format.**

- Slack mrkdwn only. No em dashes.
- One blank line before every section header; Slack renders headers tight otherwise.
- State the data-through date for every metric.
- Jira links as `<https://<JIRA_HOST>/browse/KEY|KEY>`.
- Mark every gap inline. Routine runs add a final `Gaps:` line for anything skipped.

## W5 -- Create the Slack Draft

Call `slack_send_message_draft` with the team file's `channel_id`, the W4 draft text as `message`, and the anchor `thread_ts`. Give the user the thread link, formatted `https://<workspace>.slack.com/archives/<channel_id>/p<thread_ts without the dot>` (`<workspace>` comes from the team file), and tell them to review and press Enter. Never call `slack_send_message`.

Slack allows one draft per channel, including thread drafts. If the result is `draft_already_exists`, do not retry, overwrite, or delete the existing draft. Print the draft in a fenced block and tell the user to send or clear the existing draft in that channel, then rerun. Routine runs record `Gaps: draft_already_exists` in the final line. Do not post gaps or summaries anywhere else.

## W6 -- Optional Vault Copy

Resolve the vault from `--vault PATH`, else `OKR_REPORT_VAULT_DIR`, else `OBSIDIAN_VAULT`. If none is set or the path is not an existing directory, skip silently and print `Vault: not configured`.

Otherwise write `<vault>/weekly/<team>/<YYYY-MM-DD>.md` with the exact draft text and a source map: template post permalink, anchor parent permalink, Jira queries run, metric commands and windows (with pasted values and who supplied them), highlights post link and `ts`, and gaps.
