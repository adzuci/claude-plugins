---
name: slackout
description: Send an approved task to Apollo Slack bots and perform bounded, one-shot thread checks.
disable-model-invocation: true
argument-hint: <grafana|claude|operator|jarvis>[,...] <prompt> | check <thread>
---

# Slackout

Offload a task to an Apollo Slack bot when the user wants visible, asynchronous work in Slack. Every post wakes a bot and may cost money, so send only after explicit authorization and always return the thread link.

## Usage

```text
/apollo-eng-devops:slackout operator Review https://github.com/apolloio/example/pull/123
/apollo-eng-devops:slackout grafana Investigate service errors from 14:00Z to 15:00Z
/apollo-eng-devops:slackout check https://apolloio.slack.com/archives/C0AQGTVKJCT/p1234567890123456

$slackout operator Review https://github.com/apolloio/example/pull/123
$slackout check C0AQGTVKJCT/1234567890.123456
```

Targets are `grafana`, `claude`, `operator`, and `jarvis`. A comma-separated list sends one root message per distinct target.

## Constants

- Default channel: `C0AQGTVKJCT` (`#devops-todo-dump`, public). Use another channel only when the user specifies it.
- Claude: `<@U0A9YEALDCK>`
- Grafana: `<@U0AL5LA8YTX>`
- Apollo Operator: `<@U0ABEQ94H7Z>`
- Jarvis has no direct Slack user; route it through Apollo Operator as `Ask Jarvis ...`.

## Authorization And Routing

- A direct request to post, send, ask, or have a target perform work authorizes one root message for that target. A request to draft does not authorize sending.
- If you materially expand the task beyond the user's wording, show the final prompt and wait for approval.
- Never include secrets, credentials, customer data, or private source excerpts that are unnecessary for the task.
- When the user did not explicitly choose Slackout, prefer a bounded local read-only tool call for a simple query. Prefer Slackout when local access is blocked, the bot has context unavailable locally, work should proceed asynchronously, or the reasoning should be visible to teammates.
- State `Tried locally: <attempt>, blocked by <reason>.` when Slackout follows a failed local attempt.

Use `operator` for repository, PR, CI, or general coding work. Use `grafana` for logs and metrics when the Grafana bot's cloud context is needed. Use `claude` for a visible second opinion. Use `jarvis` for analytics questions that specifically need Jarvis.

## Build The Prompt

Include only relevant items:

1. The repository, PR, service, namespace, or project.
1. A UTC time window for operational investigations.
1. What is already known or ruled out.
1. One exact question or requested outcome.
1. The permitted mutation scope. Default to `Read-only, no changes.` unless the user explicitly authorized edits.
1. `Reply in this thread with evidence and links.`

For PR review, ask for findings ordered by severity, verified file and line links, validation gaps, and a clear approve/request-changes verdict. Do not ask the bot to merge, push, or modify the PR unless the user separately authorized that action.

## Send

Use the connected Slack tools. In Codex, prefer the Slack app's `slack_send_message` and `slack_read_thread`; in Claude Code, use the equivalent Slack MCP tools. Discover the available tool rather than hard-coding a server-specific tool prefix.

Send one root message per target:

| Target | Message |
| --- | --- |
| `claude` | `<@U0A9YEALDCK> <prompt>` |
| `grafana` | `<@U0AL5LA8YTX> <prompt>` |
| `operator` | `<@U0ABEQ94H7Z> <prompt>` |
| `jarvis` | `<@U0ABEQ94H7Z> Ask Jarvis <prompt>` |

Use `channel_id: C0AQGTVKJCT` unless overridden. Enable application-link unfurls when the tool supports them. Do not create relay replies or duplicate root messages.

After sending, record and return:

- `channel_id`
- root `thread_ts`
- the immutable permalink returned by Slack, or `https://apolloio.slack.com/archives/<channel_id>/p<thread_ts without the dot>`
- `last_seen_ts`, initially the root `thread_ts`

If Slack returns an ambiguous result, do not retry blindly. Search the target channel for the exact unique prompt, confirm whether it posted, and send at most once.

## Watch The Thread

Read the thread once immediately with detailed output and `oldest: <last_seen_ts>`. Ignore the user's root post, link previews, generic progress checklists, and `Long running task paused` notices.

Classify the result:

- `DONE`: the bot posted a final response.
- `NEEDS_INPUT`: the bot asked the user a question or requires a UI action.
- `PENDING`: there is no substantive new bot response.

When a native asynchronous wait or monitoring facility is available, wait about 90 seconds and perform another single read. Run at most six rounds, stop on new user input, and never use a foreground shell polling loop. If no wait facility is available, return `PENDING` with the permalink after the first read. If Slack shows a Continue button, tell the user to click it; do not claim to have clicked it.

Relay the result in at most eight bullets with important numbers, IDs, and links. Preserve the newest reply timestamp as `last_seen_ts`.

## Check Mode

`check` never posts. Accept either a Slack thread URL or `<channel_id>/<thread_ts>`.

For a Slack URL, use `thread_ts` from the query string when present. Otherwise convert the path segment `p1234567890123456` to `1234567890.123456`. Read the thread once using its root timestamp, classify it with the rules above, and return the digest and permalink.
