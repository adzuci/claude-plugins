---
name: ai-limit-manager
description: Manage per-engineer Claude and Codex monthly spend limits. Looks up an engineer by email, reads their current Claude (Anthropic Admin API) and Codex (ChatGPT Admin API) limits, applies a requested change, and posts a Slack reply to the original request. Handles redistribution within USD 1,500 automatically. Activate when Ahmed asks to update an engineer's Claude or Codex limit, or says things like "handle this request", "process this limit change", "move $X from Claude to Codex for <person>".
---

# AI Limit Manager

Update a specific engineer's Claude and/or Codex monthly spend limits, then post a Slack reply confirming the change.

## When to Activate

- "Handle this request" (with a Slack link or screenshot of a limit request)
- "Move $X from Claude to Codex for <person>"
- "Set <person>'s Claude limit to $X"
- User runs `/ai-limit-manager`
- User runs `/ai-limit-manager setup` — see [Setup](#setup) below; run this first if you have never used this skill

## Setup

Run `/ai-limit-manager setup` before your first limit change. Four steps.

### 1. CLI tools

```bash
for c in op curl python3; do
  command -v "$c" >/dev/null && echo "ok   $c" || echo "MISSING $c"
done
```

`op` is the 1Password CLI: `brew install 1password-cli`.

### 2. 1Password CLI access

Symptom: `error initializing client: You are not currently signed in`.

Fix: **1Password desktop app -> Settings -> Developer -> "Integrate with 1Password CLI"**. `op` then unlocks by biometrics from any shell.

`eval $(op signin)` is NOT enough. It exports a per-shell `OP_SESSION_*` variable, and an agent runs each command in a fresh shell, so the next call is signed out again.

Verify:

```bash
op account list   # expect the apolloio account
op vault list     # expect Employee among the vaults
```

### 3. The two credential items

Both live in the `Employee` vault on `apolloio.1password.com`:

| Tool | 1Password reference |
|---|---|
| Claude | `op://Employee/Anthropic Admin Key/credential` |
| Codex | `op://Employee/OpenAI Admin Key/credential` |

**The item type decides the field name** — this is the most common setup failure:

| Item type | Secret field |
|---|---|
| API Credential | `credential` |
| Secure Note / Login / Password | `password` |

Use **API Credential**. If you see `does not have a field 'credential'`, the item is the wrong type. Older setups may name the Codex item `ChatGPT Admin API token` with a `password` field — confirm, do not guess:

```bash
op item get "Anthropic Admin Key" --account apolloio.1password.com \
  --vault Employee --format json | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('category:', d.get('category'))
for f in d.get('fields', []):
    print('  %-12s has_value=%s' % (f.get('label'), bool(f.get('value'))))
"
```

That prints labels only. Never echo, cat, or paste a credential value.

### 4. Getting the credentials

**Claude — Admin key (`sk-ant-admin01-...`).** Three different Anthropic credentials get confused here, and only one works:

| Credential | Prefix | Works for spend limits? |
|---|---|---|
| Admin key (Claude Console) | `sk-ant-admin01-` | **Yes** |
| Workload key | `sk-ant-api03-` | No |
| Compliance key (claude.ai admin panel) | `sk-ant-api01-` | No |

Compliance keys from `claude.ai/admin-settings/api-access` only carry `read:compliance_*` scopes and cannot read `/v1/organizations/spend_limits`. Admin keys are minted in the Claude Console (platform.claude.com) by an Organization **Owner/Admin**.

> **Trap.** If you open platform.claude.com and are not already a member of Apollo's Console org, you get sent to `/create` — an onboarding wizard asking "How will you use the Claude API?". **Stop there.** Completing it creates a brand-new, unrelated organization whose keys see none of Apollo's engineers. You need an invite to the existing org, not a new one.

**Codex — ChatGPT admin token.** From the ChatGPT enterprise workspace admin console. Workspace ID `72b65336-8eaa-4620-9aff-625ca7bfca7d`.

**If you cannot mint these yourself** — the common case — ask the current owner of Apollo's Anthropic Console org to invite you as Admin, or raise it in **#it-help-desk**. Do not obtain org-wide credentials informally.

These keys grant read/write over *every* engineer's spend limit. Installing this plugin does not grant access to them.

### Troubleshooting

| Symptom | Cause |
|---|---|
| `You are not currently signed in` | Desktop CLI integration not enabled (step 2) |
| `does not have a field 'credential'` | Item is a Secure Note/Login, not an API Credential |
| `isn't an item in the "Employee" vault` | Item missing, or wrong vault/name |
| `{"type":"authentication_error","message":"invalid x-api-key"}` | Key is `sk-ant-api03-`/`sk-ant-api01-`, not `sk-ant-admin01-` |
| A section prints nothing and exits 0 | An API error with no `data` key — the lookup snippets below guard against this |

## API Units — IMPORTANT

| API | Amount field | Unit | Conversion |
|---|---|---|---|
| Anthropic (Claude) | `amount` | cents | USD 1 = 100 units. Read: divide by 100. Write: multiply by 100. |
| ChatGPT (Codex) | `limit` (credits) | credits | 1 credit = USD 0.04. Read: divide by 25. Write: multiply by 25. Workspace default: 12,500 credits = USD 500/mo. |

## Keys (from 1Password)

Both keys must be fetched fresh each run:

```bash
# Item titles, vaults and field labels differ between admins, so try
# candidates in order rather than hardcoding one reference.
#
# WARNING: never use positional parameters here. Skill args are shell-expanded
# into this file, so a literal dollar-one becomes the caller's first argument.
# Named variables only.

ANTHROPIC_REFS=(
  "op://Employee/Anthropic Admin Key/credential"
  "op://Private/Anthropic Admin Key/credential"
  "op://Employee/Anthropic Admin Key/password"
  "op://Private/Anthropic Admin Key/password"
)
CHATGPT_REFS=(
  "op://Employee/OpenAI Admin Key/credential"
  "op://Private/ChatGPT Admin API token/credential"
  "op://Employee/ChatGPT Admin API token/credential"
  "op://Private/ChatGPT Admin API token/password"
  "op://Employee/ChatGPT Admin API token/password"
)

resolve_secret() {
  local ref val
  for ref in "${RESOLVE_REFS[@]}"; do
    val=$(op read "$ref" --account apolloio.1password.com 2>/dev/null | tr -d '[:space:]')
    if [ -n "$val" ]; then printf '%s' "$val"; return 0; fi
  done
  echo "ERROR: could not resolve ${RESOLVE_LABEL}. Tried: ${RESOLVE_REFS[*]}" >&2
  return 1
}

RESOLVE_LABEL="Anthropic admin key"; RESOLVE_REFS=("${ANTHROPIC_REFS[@]}")
ANTHROPIC_ADMIN_KEY=$(resolve_secret) || exit 1

RESOLVE_LABEL="ChatGPT admin token"; RESOLVE_REFS=("${CHATGPT_REFS[@]}")
CHATGPT_ADMIN_KEY=$(resolve_secret) || exit 1

# Validate shape before any API call, so a config fault does not look like a
# network fault. Only admin keys can reach /v1/organizations/.
case "$ANTHROPIC_ADMIN_KEY" in
  sk-ant-admin*) : ;;
  sk-ant-*) echo "ERROR: this is a standard Anthropic API key, not an org Admin key (need sk-ant-admin*). Admin endpoints will 401." >&2; exit 1 ;;
  *) echo "ERROR: unrecognized Anthropic key shape." >&2; exit 1 ;;
esac
```

ChatGPT workspace ID: `72b65336-8eaa-4620-9aff-625ca7bfca7d`

If a candidate still will not resolve because the secret sits in a custom field
whose id is a random string, the label-matching syntax is
`op item get "<title>" --reveal --fields label=password`. Bare `--fields password`
matches the field **id**, not the label, and fails with
`"password" isn't a field in the "<title>" item`.

## Tier Rules

> **Maintainers:** write dollar figures as `USD 1,500`. Never write a dollar sign
> immediately followed by a digit. Skill args are shell-expanded into this file, so that
> pattern is replaced by the caller's positional argument. Invoked as
> `/ai-limit-manager setup this skill`, the old figures rendered as `this,050` and
> `skill,000`, silently corrupting the authorization thresholds. Backslash escapes are
> stripped by mdformat, and backticks expand and then try to run the substituted text as
> a command, so spell amounts with `USD` instead. Never use positional parameters in the
> code blocks either; use named variables.

Total = requested Claude + requested Codex.

| Total | Action |
|---|---|
| ≤ USD 1,500 | Auto-approve — apply immediately, post confirmation to Slack |
| USD 1,501 – USD 2,000 | AI Overage admin runners approve directly. No Director needed. May ask for an efficiency report first — see the dedupe rule below. |
| USD 2,001 – USD 2,500 | Director approval |
| > USD 2,500 | Patrick Sullivan (patrick.sullivan@apollo.io) |

If the requester is themselves at or above Director, escalate to their manager
instead — and note that the top two bands can collapse to the same person.

### Asking for an efficiency report

`/claude-usage-export` or `/apollo-eng:deep-insights` — either one, not both.

**Check before asking.** Search #engineering-ai-overages for a prior request to
this person. If they were already asked to run one within the last month, do not
ask again — use what they already produced. Repeatedly asking the same engineer
for the same report is how this process earns a reputation as a tollbooth.

Source of truth: [AI Token Strategy](https://app.notion.com/p/apolloio/AI-Token-Strategy-37eab2b3b496817ab42ee977a22503fc?source=copy_link).
Re-read it before applying — these numbers change, and the doc wins over this table.

## Slack reactions

Limit requests are raised in **#engineering-ai-overages** (`C0AUGJSSGMA`).

Everything in this section is conditional. If the skill was invoked without a
permalink, or the Slack MCP is not authorized, there is no thread to react to and
no message to post — skip the reactions and print the draft reply for the admin to
paste. Never block a limit change on Slack being reachable.

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
curl -sS "https://api.anthropic.com/v1/organizations/spend_limits/effective?limit=1000" \
  -H "anthropic-version: 2023-06-01" \
  -H "x-api-key: $ANTHROPIC_ADMIN_KEY" | python3 -c "
import sys, json
d = json.load(sys.stdin)
if 'error' in d:
    print('FATAL: Anthropic API error:', json.dumps(d['error']), file=sys.stderr); sys.exit(1)
rows = [e for e in d.get('data', [])
        if ((e.get('actor') or {}).get('email_address') or '').lower() == '<email>']
if not rows:
    print('FATAL: no spend-limit entry for <email>', file=sys.stderr); sys.exit(1)
for e in rows:
    print('anthropic_user_id:', e['scope']['user_id'])
    print('claude_limit_usd :', int(e['amount']) / 100)
    print('mtd_spend_usd    :', (e.get('period_to_date_spend') or 0) / 100)
"
```

**Codex (ChatGPT):**

```bash
WORKSPACE_ID="72b65336-8eaa-4620-9aff-625ca7bfca7d"
curl -sS "https://api.chatgpt.com/v1/manage/workspaces/${WORKSPACE_ID}/usage_limits/users?query=<email>" \
  -H "Authorization: Bearer $CHATGPT_ADMIN_KEY" | python3 -c "
import sys, json
d = json.load(sys.stdin)
if 'error' in d:
    print('FATAL: ChatGPT API error:', json.dumps(d['error']), file=sys.stderr); sys.exit(1)
rows = [u for u in d.get('data', []) if (u.get('email') or '').lower() == '<email>']
if not rows:
    print('FATAL: no ChatGPT user for <email>', file=sys.stderr); sys.exit(1)
for u in rows:
    eff = u.get('effective_monthly_usage_limit') or {}
    credits = (eff.get('limit') or {}).get('limit')
    print('chatgpt_user_id  :', u['id'])
    print('codex_limit_usd  :', credits / 25 if credits is not None else None)
    print('limit_source     :', (eff.get('source') or {}).get('kind'))
    print('allocation       :', 'OVERRIDE' if u.get('override_monthly_usage_limit') else 'INHERITED (%s)' % ((eff.get('source') or {}).get('kind')))
    print('mtd_usage_usd    :', u.get('current_month_usage'))
"
```

### 3. Calculate new limits

**Current split** — ask Ahmed for the engineer's current Claude and Codex USD allocations if not obvious from the API. Do NOT use the API's group/tier limit as the personal allocation; the group limit is a ceiling, not their assigned budget.

Read the lookup output before assuming. If the Codex lookup shows:

```
limit_source : workspace_default
has_override : False
```

then that number is the workspace default every engineer inherits (12,500 credits = USD 500), **not** this person's allocation. Ask for the real split.

Note that `override_monthly_usage_limit` can come back as `{}` as well as `null` —
test it for truthiness, not `is not None`.

**Writing an override is not a neutral act.** It detaches the engineer from the
workspace default permanently: if the default later moves, they stay pinned at
whatever you set. Prefer leaving people on the default unless the request
genuinely requires a personal allocation.

The policy doc has not published a per-tool default split for the USD 1,500 total — the split it lists still sums to the old USD 1,050. So there is currently no default to fall back on: confirm the split, every time.

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

**Enforce the USD 1,500 rule:** For a pure redistribution the total is unchanged, so the tier never moves. For an increase, the total (new_claude + new_codex) must stay at or under USD 1,500 to auto-approve; above that, consult the tier table. Note this is a ceiling, not an equality — a total below USD 1,500 is fine.

**A redistribution is all-or-nothing.** If one side cannot be applied (bad credential, API error), do NOT apply the other. Half of a +$X/-$X swap leaves the engineer strictly worse off than before they asked.

Check tier: `total = new_claude + new_codex`

**Check utilization before escalating.** The lookups print month-to-date spend for
both tools. If someone is at or near 0% of their current limit, ask what the
increase is for before starting any approval chain — a bigger ceiling does not
help someone who is not hitting the current one. This is a friendly question, not
a gate.

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

**Update Codex** (convert USD → credits: multiply by 25, since 1 credit = USD 0.04):

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

## Slack reply templates

**Style: fewest words that do the job, and friendly.** No tier names, no policy recitation, no explaining the rules back at the person. They asked for tokens; answer about tokens.

Applied (≤ USD 1,500):

```
Hi @name — done! Claude USD 550 → USD 555/mo, Codex USD 500 → USD 495/mo 🎉
```

Needs an efficiency report (USD 1,501 – USD 2,000):

```
Hi @name, we can get you those tokens — when you get a moment, can you run
`/claude-usage-export` or `/apollo-eng:deep-insights`?
```

Above USD 2,000:

```
Hi @name, we can get you those tokens — over USD 2,000 needs a quick written
justification for @Patrick Sullivan. Can you jot down the impact?
```

Counter-example — do not write this:

> Hi @name — this one's a true increase rather than a redistribution, so it crosses the USD 1,500 auto-approve line and needs a quick sign-off. Two things when you get a moment: 1. Run `/claude-usage-export` 2. Run `/apollo-eng:deep-insights`. Then tag your approver. Happy to apply it the moment that's a yes.

Same information, four times the words, and it makes the engineer read our process instead of answering their question.
