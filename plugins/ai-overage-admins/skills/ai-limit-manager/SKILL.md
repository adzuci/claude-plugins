---
name: ai-limit-manager
description: Manage per-engineer Claude and Codex monthly spend limits. Looks up an engineer by email, reads their current Claude (Anthropic Admin API) and Codex (ChatGPT Admin API) limits, applies a requested change, and posts a Slack reply to the original request. Handles redistribution within $1,050 automatically. Activate when Ahmed asks to update an engineer's Claude or Codex limit, or says things like "handle this request", "process this limit change", "move $X from Claude to Codex for <person>".
---

# AI Limit Manager

Update a specific engineer's Claude and/or Codex monthly spend limits, then post a Slack reply confirming the change.

## When to Activate

- "Handle this request" (with a Slack link or screenshot of a limit request)
- "Move $X from Claude to Codex for <person>"
- "Set <person>'s Claude limit to $X"
- User runs `/ai-limit-manager`

## API Units — IMPORTANT

| API | Amount field | Unit | Conversion |
|---|---|---|---|
| Anthropic (Claude) | `amount` | cents | $1 = 100 units. Read: divide by 100. Write: multiply by 100. |
| ChatGPT (Codex) | `limit` (credits) | credits | 1 credit = $0.04. Read: divide by 25. Write: multiply by 25. Workspace default: 12,500 credits = $500/mo. |

## Keys (from 1Password)

Both keys must be fetched fresh each run:

```bash
ANTHROPIC_ADMIN_KEY=$(op read "op://Employee/Anthropic Admin Key/credential" \
  --account apolloio.1password.com | sed 's/^\*\*//' | tr -d '[:space:]' | sed 's/\\//g')

CHATGPT_ADMIN_KEY=$(op item get "ChatGPT Admin API token" \
  --account apolloio.1password.com --reveal --fields password | tr -d '[:space:]')
```

ChatGPT workspace ID: `72b65336-8eaa-4620-9aff-625ca7bfca7d`

## Tier Rules

Total = requested Claude + requested Codex.

| Total | Action |
|---|---|
| ≤ $1,050 | Auto-approve — apply both changes immediately, post confirmation to Slack |
| $1,051 – $2,000 | Ask engineer to run `/claude-usage-export` + `/roi-dashboard` and tag their Director |
| > $2,000 | Same skills, tag Himanshu Gahlot |

## Slack reactions

If the request came from a Slack thread/message:

- As soon as you start looking at the request, react to the original message with `eyes` (`mcp__claude_ai_Slack__slack_add_reaction`, channel_id + message_ts of that message).
- Once the change has been applied (or the request has been fully handled, e.g. escalated per the tier rules) and reported to Ahmed, react to the same message with `white_check_mark`.

## Steps

### 1. Parse the request

Extract from the message (screenshot or text):

- Engineer's name/email
- What they're asking: redistribution (move $X from A to B) or increase (raise limit to $X)
- Implied new Claude limit and new Codex limit

If the email isn't obvious, search by name:

```bash
curl -s "https://api.anthropic.com/v1/organizations/spend_limits/effective?limit=1000" \
  -H "anthropic-version: 2023-06-01" \
  -H "x-api-key: $ANTHROPIC_ADMIN_KEY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for e in data.get('data', []):
    actor = e.get('actor') or {}
    name = (actor.get('name') or '').lower()
    if '<search_term>' in name:
        print(actor.get('email_address'), e['scope']['user_id'], e['amount'])
"
```

### 2. Look up current limits

**Claude (Anthropic):**

```bash
curl -s "https://api.anthropic.com/v1/organizations/spend_limits/effective?limit=1000" \
  -H "anthropic-version: 2023-06-01" \
  -H "x-api-key: $ANTHROPIC_ADMIN_KEY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for e in data.get('data', []):
    actor = e.get('actor') or {}
    if actor.get('email_address','').lower() == '<email>':
        print('anthropic_user_id:', e['scope']['user_id'])
        print('claude_limit:', e['amount'])
        print('mtd_spend:', e['period_to_date_spend'])
"
```

**Codex (ChatGPT):**

```bash
WORKSPACE_ID="72b65336-8eaa-4620-9aff-625ca7bfca7d"
curl -s "https://api.chatgpt.com/v1/manage/workspaces/${WORKSPACE_ID}/usage_limits/users?query=<email>" \
  -H "Authorization: Bearer $CHATGPT_ADMIN_KEY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for u in data.get('data', []):
    if u.get('email','').lower() == '<email>':
        effective = u.get('effective_monthly_usage_limit', {}).get('limit', {})
        print('chatgpt_user_id:', u['id'])
        print('codex_limit:', effective.get('limit'))  # credits = USD
        print('mtd_usage:', u.get('current_month_usage'))
"
```

### 3. Calculate new limits

**Current split** — ask Ahmed for the engineer's current Claude and Codex USD allocations if not obvious from the API. Do NOT use the API's group/tier limit as the personal allocation; the group limit is a ceiling, not their assigned budget.

For a redistribution ("move $X from Claude to Codex"):

```
new_claude = current_claude - X
new_codex  = current_codex  + X
```

For a direct set ("set Claude to $Y"):

```
new_claude = Y
new_codex  = unchanged
```

**Enforce $1,050 rule:** Total (new_claude + new_codex) must equal $1,050 for standard engineers. If the request would push total above $1,050, treat it as a Tier 2/3 increase — do not auto-approve.

Check tier: `total = new_claude + new_codex`

### 4. Apply changes (Tier 1 only)

**Update Claude** (convert USD → cents: multiply by 100):

```bash
NEW_CLAUDE_CENTS=$((new_claude_usd * 100))
curl -s -X POST "https://api.anthropic.com/v1/organizations/spend_limits" \
  -H "anthropic-version: 2023-06-01" \
  -H "x-api-key: $ANTHROPIC_ADMIN_KEY" \
  -H "content-type: application/json" \
  -d "{\"amount\": \"$NEW_CLAUDE_CENTS\", \"scope\": {\"type\": \"user\", \"user_id\": \"<anthropic_user_id>\"}, \"period\": \"monthly\"}"
```

**Update Codex** (convert USD → credits: multiply by 25, since 1 credit = $0.04):

```bash
WORKSPACE_ID="72b65336-8eaa-4620-9aff-625ca7bfca7d"
NEW_CODEX_CREDITS=$((new_codex_usd * 25))
curl -s -X PATCH "https://api.chatgpt.com/v1/manage/workspaces/${WORKSPACE_ID}/usage_limits/users/<chatgpt_user_id>" \
  -H "Authorization: Bearer $CHATGPT_ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"override_monthly_usage_limit\": {\"limit\": $NEW_CODEX_CREDITS, \"type\": \"limited\"}}"
```

### 5. Report results

Print a clean summary:

```
✅ Done for <name> (<email>)
   Claude:  $<old_claude> → $<new_claude>/mo
   Codex:   $<old_codex>  → $<new_codex>/mo
```

If a Slack thread link was provided, tell Ahmed what to post as a reply (or ask if he wants you to post it via the Slack API).
