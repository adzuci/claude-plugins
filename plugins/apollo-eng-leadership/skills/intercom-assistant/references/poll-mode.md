# Poll Mode

Use this reference when the user types `poll` or runs `live` without a conversation
link, customer email, or company context. This mode fetches open Intercom conversations
assigned to the current agent and offers a live assessment for any that need a reply.

## Steps

1. Call `mcp__Intercom__search_conversations` to fetch open conversations. Use
   `state:open` as the baseline filter. Limit to 10 results, sorted by last-updated
   descending.
1. For each conversation returned, extract:
   - Conversation ID
   - Customer name and company (if available)
   - First line of the most recent customer message as an issue excerpt
   - Conversation state and approximate time since last update
   - Whether the last message is from the customer (needs reply) or an agent (awaiting
     customer)
1. Render the queue summary table below.
1. For conversations where the last message is from the customer, note them as needing a
   reply.
1. Ask the user which conversation to assess in `live`, or offer to run `live` on the first
   unanswered one automatically.

## Output Shape

```text
## Open Queue — <N> conversation(s)

| #  | Customer       | Company     | Issue (excerpt)           | Last message       |
| -- | -------------- | ----------- | ------------------------- | ------------------ |
| 1  | <name>         | <company>   | <excerpt, max 60 chars>   | <time> — customer  |
| 2  | <name>         | <company>   | <excerpt, max 60 chars>   | <time> — agent     |

<M> conversation(s) need a reply (last message from customer).

Type a row number or paste a conversation ID/URL to assess it in `live`.
```

## Live Trigger

When the user selects a conversation (by row number, ID, or URL), switch to
`references/live-intercom-mode.md` and run `live` on that conversation ID.

When the user asks for the next or first unanswered conversation, run `live` on the first
unanswered conversation in the queue (row 1 or the first row flagged as needing a reply).

## Empty Queue

```text
No open conversations found in your inbox right now.
Paste a conversation URL or ID to assess it in `live`, or try again in a few minutes.
```

## Notes

- This mode is read-only — do not reply, close, tag, or route any conversation.
- If Intercom MCP is unavailable, report the error and suggest running
  `/apollo-eng-leadership:intercom-assistant help` to check connector status.
- If the search returns more than 10 results, note the total count and suggest narrowing
  by adding a filter (e.g. team inbox, assignee) or using a specific conversation URL.
