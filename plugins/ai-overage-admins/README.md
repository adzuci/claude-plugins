# ai-overage-admins

Skills for admins managing engineers' Claude and Codex monthly spend limits.

## Skills

| Invoke command | Purpose |
| --- | --- |
| `/ai-overage-admins:ai-limit-manager` | Look up an engineer's Claude/Codex spend limits, apply a requested change, and post a Slack reply confirming it |

## Access requirement (limitation)

Run `/ai-overage-admins:ai-limit-manager setup` for a step-by-step walkthrough of the
CLI tools, 1Password configuration, credential item names, and how to obtain the
keys (or who to ask). Tier thresholds come from the
[AI Token Strategy](https://app.notion.com/p/apolloio/AI-Token-Strategy-37eab2b3b496817ab42ee977a22503fc?source=copy_link) doc.

`ai-limit-manager` fetches org-wide admin credentials from 1Password at runtime:
the Anthropic Admin API key and the ChatGPT (Codex) Admin API token, both stored
in the `Employee` vault. These are powerful, org-wide credentials — they grant
read/write over every engineer's spend limit, not just the caller's own.

As of this writing, only a small set of admins have 1Password access to those
vault items. The skill will fail 1Password auth for anyone who installs this
plugin without that access. This is expected: the assumption is that only
admins who already hold the underlying API keys will use this plugin and
skill. Extending it to more admins requires separately granting them access to
those 1Password items — installing the plugin alone does not grant it.

## What belongs in ai-overage-admins

- Skills for admins who manage per-engineer AI tool spend limits and need the
  underlying Anthropic/ChatGPT admin credentials to do so

## What does NOT belong in ai-overage-admins

- Skills for engineers checking or reporting their own usage (see
  `apollo-eng-agentic-engineering` or repo-local usage-export skills)
- General engineering-leadership reporting — use `apollo-eng-leadership`
