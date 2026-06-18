# Setup Mode

Use this reference for `setup` before a support shift or first live ticket.

## Goal

Help an EM confirm their support workspace is ready:

- Intercom conversation details are visible and useful.
- Glean Support Rep Assistant can be called through the CLI.
- Granola recipes are installed if the EM uses Granola.
- A personal closeout Intercom macro exists.
- The EM knows what to paste when tools are unavailable.

## Output Shape

```text
Setup checklist:
<checked / missing / needs user action>

Intercom conversation panel:
<what to pin or keep visible>

Granola recipes:
<wrap-up, stall, and deescalate recipes>

Personal Intercom macro:
<macro name and body>

CLI/MCP nudges:
<Intercom, Granola, Glean, Google Sheets, Slack status and install/auth guidance>

How to use during a ticket:
<short sequence from intro to monitor to recap>
```

## Intercom Details To Pin Or Keep Visible

Before a shift, open a real or practice conversation and make sure these are easy to find:

- Customer name and email.
- Company/account.
- Conversation type: chat, email, billing, tech, support, or unknown.
- Owner/assignee and team.
- User ID and team/account ID when available.
- Plan tier, seats, ARR, trial/core/paid state when available.
- Browser/referral URL or relevant technical metadata when useful.
- Recent/previous conversations and repeated friction.
- GodMode or account panel access path.
- Composer location and Reply vs Note distinction.

If a detail is not visible, do not infer it. Mark it as needing Intercom/GodMode verification.

## Granola Recipes

Add the recipes from `granola-recipes.md` if the EM uses Granola:

- `/Wrap-up`: after-call/chat summary that mirrors `recap-recipe.md`.
- `/Stall`: stuck, unclear, or blocked support interactions.
- `/Deescalate`: frustrated or stuck customer replies.

If not using Granola, keep `granola-recipes.md` available and paste notes/transcripts directly into the skill.

## Personal Closeout Macro

Create a personal Intercom macro named:

```text
<name> Closeout
```

Suggested body:

```text
I'll go ahead and close this out, but feel free to reply here if anything else comes up.
```

Do not apply the macro automatically from this skill. The skill can remind the EM when it is appropriate.

## Docs And Setup Links

- Glean Support Rep Assistant: `https://app.glean.com/chat/agents/90b93c53b44840d5b25a7836d4042304`
- Granola recipes docs: `https://docs.granola.ai/help-center/getting-more-from-your-notes/recipes`
- GodMode Lumos request: `https://app.lumosidentity.com/app_store?domainAppId=1559192`
- Zendesk Lumos request, if Wave 2 requires it: `https://app.lumosidentity.com/app_store?domainAppId=1791886`
- IKB: `https://apolloikb.zendesk.com/hc/en-us?brand_id=33894388979213`

## Shift Usage

1. Run `setup` before the shift.
1. Use `intro` for the first response.
1. Use `monitor` when a chat turns into a call or gets complex.
1. Use the Granola `/Stall` or `/Deescalate` recipe when notes show the interaction is stuck, unclear, blocked, or emotionally heated.
1. Use `macro-suggest` only when the route is clear.
1. Use `recap` or `wrapup` immediately after the interaction.
1. Use `report --date today --html` at the end of the day.
