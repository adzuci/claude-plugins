# Slack Posting Workflow Reference

This file documents the exact Slack tool calls the skill uses when a teammate chooses to draft or send a payload via MCP.

______________________________________________________________________

## Verified IDs

These are baked into the skill. Do not change.

| Item | Value | How verified |
|---|---|---|
| Channel | `#gtme-support-apollo-agent-forum` | URL: https://apolloio.slack.com/archives/C0A3HGMHMN2 |
| Channel ID | `C0A3HGMHMN2` | URL path + multiple thread reads |
| Apollo Agent user ID | `U0ABEQ94H7Z` | Appears in every Apollo Agent post header as `From: Apollo Agent (U0ABEQ94H7Z)` |
| API mention syntax | `<@U0ABEQ94H7Z>` | Slack spec for user mentions in API messages |
| UI autocomplete tag | `@Apollo Agent` | What you type in the Slack composer |

______________________________________________________________________

## The three actions

### 1. Copy-paste (default fallback, no MCP write)

No tool call. The skill returns the payload as a fenced code block with `@Apollo Agent` in plain text. The teammate copies it into the Slack composer, where typing `@apollo` invokes autocomplete and resolves the mention.

### 2. Draft (recommended default for new users)

The skill saves the payload to the channel's draft area. The teammate opens Slack and reviews/edits before sending.

```
Tool: Slack:slack_send_message_draft
Parameters:
  channel_id: "C0A3HGMHMN2"
  message: "<@U0ABEQ94H7Z> [full payload body]"
```

**Behavior notes:**

- Only one draft is allowed per channel. If a draft exists, the tool returns `draft_already_exists` and the teammate must clear it from the Slack UI first.
- Drafts are not auto-sent. The teammate must hit send in Slack.
- Drafts can be edited freely in the Slack UI before send.

### 3. Send immediately (requires explicit confirmation)

The skill posts the message to the channel as a new top-level message.

```
Tool: Slack:slack_send_message
Parameters:
  channel_id: "C0A3HGMHMN2"
  message: "<@U0ABEQ94H7Z> [full payload body]"
```

**Confirmation gate (mandatory):**

The skill MUST receive one of these explicit phrases before firing this tool:

- "send now"
- "post it now"
- "fire it"

The following replies are NOT sufficient and trigger a clarifying question:

- "yes"
- "ok"
- "go"
- "sounds good"
- Any other ambiguous affirmative

### Bonus: Thread reply

For follow-up questions on an existing Apollo Agent thread:

```
Tool: Slack:slack_send_message
Parameters:
  channel_id: "C0A3HGMHMN2"
  thread_ts: "[parent message timestamp, e.g., 1779364961.068259]"
  message: "<@U0ABEQ94H7Z> [follow-up payload]"
```

______________________________________________________________________

## Tag conversion logic

The single transformation the skill performs on the payload between preview and send:

```
Find: @Apollo Agent
Replace: <@U0ABEQ94H7Z>
```

Applied only for actions 2 (draft) and 3 (send). Not applied for action 1 (copy-paste).

All other content in the payload ships verbatim. The skill never edits question wording, customer identifiers, or context paragraphs between the teammate's approval and the API call.

______________________________________________________________________

## Hard guardrails

The skill enforces these regardless of teammate input:

1. **Channel lock**: only `C0A3HGMHMN2` is a valid post target. Any other channel ID is rejected.
1. **User lock**: only `<@U0ABEQ94H7Z>` is a valid mention target for this skill. The skill does not tag other users (no @channel, no @here, no other agents, no humans).
1. **Confirmation lock**: no MCP write fires without one of the explicit confirmation phrases above.
1. **PII flag**: if the payload contains an email address, credential-looking string, or other sensitive field that was not explicitly part of the customer identifier blocks, the skill flags it for teammate review before any send.
1. **Schedule opt-in**: the skill does not use `slack_schedule_message` unless the teammate explicitly asks to schedule. Default action 3 is "send now," not "schedule."

______________________________________________________________________

## Failure modes and recovery

| Failure | Cause | Recovery |
|---|---|---|
| `channel_not_found` | Teammate's Slack account lacks access to `C0A3HGMHMN2` | Skill returns the copy-paste version; teammate posts manually |
| `draft_already_exists` | Existing draft in channel | Skill asks teammate to clear the draft in Slack UI, then retries |
| Slack MCP not connected | Teammate's session doesn't have Slack MCP enabled | Skill returns the copy-paste version with a note to enable Slack MCP for direct posting |
| Apollo Agent doesn't respond within ~5 minutes | Agent rate limiting or investigation taking longer | Normal; agent confirmed it can take "10 seconds to a few minutes" for heavy investigations. Wait before reposting. |
