---
name: standup
description: Draft concise daily, weekly, or custom-range standups from Jira and Obsidian evidence. Invoke with /productivity:standup or /standup.
disable-model-invocation: true
---

> Sync note: fixture copy of `plugins/productivity/skills/standup/SKILL.md`. Keep the body byte-identical to the source and regenerate whenever the real skill changes. Do not hand-edit here.

# Standup

Build a paste-ready personal status update plus a private quick-close queue. Never post or change ticket status without a separate explicit request.

## Usage

```text
/standup daily
/standup weekly
/standup custom 2026-07-01 2026-07-15
```

Use the previous working day for `daily`, the previous calendar Monday through Sunday for `weekly`, and explicit inclusive dates for `custom`. Use the user's local timezone.

## Resolve Sources

Resolve the vault from an explicit path, `$VAULT`, `~/.config/adzuci-productivity/config.json`, then `~/obsidian-vault`. Ask when none exists.

Check these bounded sources:

1. **Jira accomplishments:** issues assigned to the current user that reached Done during the range. Include other updated issues only when their history or a corroborating source proves an accomplishment.
1. **Jira in flight:** current-user issues in an active status. Preserve keys, status, and links.
1. **Backlog:** read only `backlog.md`. Use `Done This Week` for accomplishments and `In Progress`, `Waiting`, and actionable Inbox items for current work.
1. **Daily evidence:** read date-bounded files under `reports/daily-wrapup/`, `daily-wrapup/`, and `sessions/`. Prefer explicit accomplishments, decisions, completed goals, and open loops.

Use exact date bounds in Jira queries. If Jira is unavailable, mark the run incomplete rather than treating the backlog as Jira truth.

Use these JQL shapes with calculated absolute dates:

```text
assignee = currentUser() AND statusCategory = Done AND resolved >= "START" AND resolved < "END_EXCLUSIVE"
assignee = currentUser() AND statusCategory != Done ORDER BY updated DESC
```

For an inclusive custom end date, set `END_EXCLUSIVE` to the following day.

## Reconcile

- Deduplicate by Jira key, URL, then normalized task text.
- Prefer completed outcomes over activity descriptions.
- Put ongoing work under `In flight`, even when meaningful progress happened last week.
- Do not claim completion from an old or unchecked backlog item.
- Preserve source links when they fit without harming readability.

Flag a **quick close** only when current evidence shows the remaining action should take under five minutes, such as transitioning an already-shipped ticket, checking off an already-completed task, or sending a prepared acknowledgment. State the exact final action. Never infer effort from title or age alone.

## Draft

Put the main copy in one code block:

```text
Last week
- <completed outcome>

In flight
- <current outcome, next step, or blocker>
```

For `daily`, use `Yesterday` and `Today`; for `custom`, use `Completed` and `In flight`.

The copy block must satisfy both limits:

- fewer than 90 words,
- fewer than eight bullets.

Use no more than five accomplishment bullets and two in-flight bullets. Omit empty headings. Run `scripts/check_standup.py --file <draft-file>` against the copy block before returning it.

Default to Slack-compatible `<url|KEY>` links in the copy block. Use another destination's native link format only when the user names that destination.

After the copy block, add:

- `Quick closes (<5m)` with zero to three evidence-backed actions,
- a one-line source coverage note naming unavailable or stale sources.

These private notes are outside the paste-ready copy and do not count toward its limits.

## Save Scheduled Runs

For scheduled runs, save the full result to `<vault>/reports/standup/YYYY-MM-DD-<mode>.md`. Include the date range, source coverage, copy block, quick closes, and generation timestamp. Preserve existing files unless rerunning the same date and mode; then replace the generated report idempotently.

Use the caller's native scheduler. A Monday weekly schedule should invoke:

```text
/standup weekly
```

Do not schedule duplicate equivalent jobs. Do not auto-post the result.
