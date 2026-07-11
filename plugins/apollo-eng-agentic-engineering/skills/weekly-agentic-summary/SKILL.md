---
name: weekly-agentic-summary
description: Generate a weekly accomplishment summary for the Agentic Engineering team from the #team-agentic-engineering-internal Slack channel, organized by project.
disable-model-invocation: true
---

# Weekly Agentic Engineering Summary

Generate a per-project summary of what the team accomplished over the last 7 days (default) from the team Slack channel, then optionally post it back to the channel.

**Channel:** `#team-agentic-engineering-internal` → `C0AMBB0563X`

## Steps

### 1. Determine the time window

Default to the **last 7 days**. If the user specifies a different window (e.g. "last 2 weeks", "since Monday"), use that. Compute the oldest epoch timestamp:

```bash
date -v-7d +%s
```

### 2. Load Slack tools

Tools are deferred — load them with ToolSearch before calling:

```
select:mcp__claude_ai_Slack__slack_read_channel,mcp__claude_ai_Slack__slack_read_thread,mcp__claude_ai_Slack__slack_send_message
```

### 3. Read the channel

Call `slack_read_channel` with `channel_id=C0AMBB0563X` and `oldest=<epoch from step 1>`, `limit=100`. Paginate with the returned cursor if there are more messages in the window.

### 4. Read the Sup standup threads

The **Sup** bot (`U040MU881AP`) posts a daily "submitted responses for Agentic Engineering Standup" message. Read each Sup thread in the window with `slack_read_thread`.

Each person's answer is posted as a per-person app reply whose visible Q&A ("What have you completed…?" plus the response) lives in the message's **`attachments`** array (the quoted block), not in the top-level `text`. Any read that returns only `text` comes back empty — that is why naive reads of Sup threads look blank.

To get the content:
- Pull each Sup thread's replies via `conversations.replies(channel, thread_ts)` and parse `attachments[*].text` (and `blocks[]` if present). That text is the literal standup answer.
- The reply's author maps to the person, which gives you owner attribution for free.
- This requires the bot to be a **member of `#team-agentic-engineering-internal`** and a token with `channels:history`.

**Fallback:** if attachments are not returned by your read path, reconstruct accomplishments from the **substantive channel messages** instead (PR announcements, "shipped/live" posts, demos, status updates, Nudgy merge celebrations) and note to the user that the Sup answers could not be read directly.

### 5. Identify the substantive signals

Pull real accomplishments from messages like:
- "shipped / live / merged" announcements and demos
- PR review requests + Nudgy merge celebrations (which repo → which project)
- Status updates, architecture decisions, metrics/dashboard launches
- Anything cc'ing leadership or marked with 🚀/🔥/✅ reactions

Filter out pure noise: PTO notices, "has joined/left the channel", survey reminders, channel-admin chatter (unless notable as Team Ops).

### 6. Organize by project

Group accomplishments under project headers with an owner line. Recurring projects (map repos/keywords → project):
- **🤖 Nudgy Bot** — `ai-tool-slack-bot` repo, PR review nudging _(Ibrahim Wynters)_
- **🔍 Review Bot** — leadgenie review-bot, code search, comment acceptance _(Brandon Renfrow)_
- **♻️ Recovery Bot** — PR / CI failure recovery _(Michał Garapich)_
- **🧪 Predictive Testing / Test-Impact-Analysis** _(Anmol Dhingra)_
- **🎯 Intent Verification Agent** _(Ryan Harrs)_
- **🏛️ Pantheon (platform)** — `pantheon` / `pantheon-agents` repos _(Marcelo Mendonca)_
- **📊 Metrics & Observability** — Snowflake/BQ agent metrics, dashboard _(Brandon Renfrow)_
  - Dashboard link: <<https://app.snowflake.com/streamlit/apolloorg/apollo/#/apps/DBT_DEVELOPMENT_DB.DBT_ADHOC.AGENTIC_ENGINEERING_DASHBOARD%7CAgentic> Engineering Dashboard>
- **🛠️ Simple Agent & Team Ops** — `simple-agent` repo, Kanban, demos, surveys

Add/rename project sections as the channel evolves — these are starting points, not a fixed list. Infer owner from who posted/championed the work.

### 7. Present the draft

Show the full summary to the user in the chat first. Use this structure:

```
# Agentic Engineering — Weekly Update (<start> – <end>)

## <emoji> <Project>
_Owner: <name>_
- <accomplishment with PR # / link where available>
...

_Note: <PTO / holidays / context that affected output this week>_
```

Keep bullets concrete (PR numbers, costs, durations, what shipped). Surface PTO/holidays as a closing note so dips in output read correctly.

### 8. Post (only when asked)

Posting to the channel is outward-facing — only post when the user explicitly says to (e.g. "post it", "send to channel"). Otherwise leave it as a chat draft.

**Before posting, check whether this week's update already exists — using the messages already fetched in Step 3, no extra API call.** Look for a message authored by this bot whose first line matches the header `# Agentic Engineering — Weekly Update (<start> – <end>)` with a date range overlapping the current window. If one exists, do **not** post again: return its message link and tell the user the update for this week is already posted. Only repost if the user explicitly asks to ("repost", "force", "post anyway").

When posting, use `slack_send_message` with `channel_id=C0AMBB0563X`. Always begin the posted message with the `# Agentic Engineering — Weekly Update (<start> – <end>)` header line so future runs can detect it. Slack formatting notes:
- Use `_italic_` for owner lines, `*bold*` for emphasis.
- Use Slack link syntax `<url|label>` for links, NOT markdown `[label](url)`.
- Return the resulting message link to the user.
