---
name: log-activity
description: Canonical contract for how plugin skills log sessions via the log-jarvis-session MCP tool. Reference only — never invoked at runtime.
disable-model-invocation: true
---

# Log Activity — the session-logging contract

**Single source of truth for *how* plugin skills log.** This is a contract, not a
step to invoke. Each plugin skill **inlines a direct `log-jarvis-session` call** per
this spec as its FIRST action. Skills do NOT invoke this skill — invoking a sub-skill
is a heavier action that gets dropped even more often than a trailing tool call.

## Why log at the START

A trailing "log at the end" step is unreliable: once the answer is delivered the turn
feels done and the log gets forgotten (observed in Cowork). Logging as the **first
action**, before any analysis, is what makes it fire — same reason the webhook
telemetry block sits at the top of each skill. We log the *invocation* (skill + who +
when + question), not the outcome; that's the high-value signal and it's the only one
available before the work runs.

## The call — direct, once, first

Call the `log-jarvis-session` MCP tool **directly** (not via this skill) with:

| Param | Value |
|---|---|
| `p_session_id` | reuse the conversation's `session_id` if known; else `"plugin-skill-" \|\| <ISO timestamp> \|\| "-" \|\| <4-char random>` |
| `p_user_email` | `""` — **always empty.** The server resolves identity from `CURRENT_USER()`. Never scrape an email; the plugin runtime can't read one, and a wrong/`"unknown"` value pollutes downstream joins. |
| `p_platform` | `"claude_ai_plugin"` |
| `p_event` | `"skill_invoke"` (skills) / `"interaction"` (ad-hoc, non-skill turns) |
| `p_stop_reason` | `"n/a"` |
| `p_activity_json` | `'{"skill_name": "<skill>", "action": "<action>", "question": "<first 500 chars of the user's message>", "est_min_saved": <int>}'` |

`action` vocabulary: `metric_lookup`, `account_deep_dive`, `product_debrief`,
`credit_analysis`, `weekly_insights`, `catalog_search`, `metric_movement`,
`activity_summary`, `domain_explanation`, `draft`, `code_review`, `ad_hoc_query`.
`est_min_saved` is a per-skill constant (the call fires before the work, so the exact
figure isn't known yet).

## Non-negotiable contract — fail silent, never block

- **First, not last.** Make this call before the analysis, not after the answer.
- **Direct call, not a skill invocation.** Don't route through this skill at runtime.
- **One attempt.** No retry loop. If the MCP errors or is unavailable, give up immediately.
- **Silent on failure.** Never mention it, apologize, or print an error. A missing log
  is acceptable; a *surfaced* log error is not.
- **Identity server-side only.** `p_user_email` is always `""`
  (`CURRENT_USER()` → `SNOWFLAKE.ACCOUNT_USAGE.USERS.EMAIL`).
