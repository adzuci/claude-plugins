# Setup Mode

Use this reference for `setup` before a support shift or first live ticket.

## Goal

Help an EM confirm their support workspace is ready:

- Intercom conversation details are visible and useful.
- Glean Support Rep Assistant can be called through the CLI.
- Granola recipes are installed if the EM uses Granola.
- A personal closeout Intercom macro exists.
- Text Blaze snippets are configured with the EM's name substituted in.
- The EM knows what to paste when tools are unavailable.

## First-Run Defaults

For a first-time Claude Code user, recommend `~/code` as the workspace, then select **Trust**. When the app offers a working mode, recommend **Auto** for the support shift. Mention Co-work only when the user asks about it; it can pause for repeated approvals.

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

Text Blaze snippets:
<ready-to-paste bodies for /hello, /higoal, /intro, /bye, /nudge — EM's name substituted>

Text Blaze install offer:
<if not installed: step-by-step walkthrough from text-blaze-snippets.md>

CLI/MCP nudges:
<Intercom, Granola, Glean, Google Sheets, Slack status and install/auth guidance.
For any MCP that is missing, show both paths side by side:
  Claude CLI: claude mcp add --transport http <name> <url>
  ChatGPT Codex CLI: codex mcp add <name> --url <url>; codex mcp login <name>
  Desktop app: Settings → MCP Servers → Add server (Transport: HTTP, URL: <url>)
Do not show the Claude CLI path for a Codex user.>

How to use during a ticket:
<short sequence from intro to live to recap>
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

## Setting Up Personal Macros

Personal macros are user-scoped and only visible to you. They let you trigger standard reply text, tags, and close actions from the Intercom composer without retyping. Verify your macros exist in Intercom **Settings → Macros → Personal Macros** before a shift. Do not apply macros automatically — always confirm the route first.

**How to create a personal macro:**

1. In Intercom, open **Settings → Macros**.
1. Click **New macro**.
1. Set the scope to **Personal** (not Team).
1. Name it, add a message body, and optionally add tag or status actions.
1. Save. The macro appears in the composer under your name.

**Wave 2 templates:** The following patterns worked well during the Wave 2 rotation. Name them `[Your Name] Intro + Call` etc. — the name prefix keeps your personal macros easy to find in the search list. Substitute your own name in both the macro name and the message body.

| Macro | When to use | Body | Actions |
| --- | --- | --- | --- |
| `[Name] Intro + Call` | Default first reply — customer has a clear question or goal | "Hi {{First name}}, I'm [Name], a Product Advocate here to help. Could you share a bit more about your goal, or if it's easier, I'm happy to jump on a quick call and work through it with you." | Tags: Live Call - Screenshare Offered, Live Call Offered |
| `[Name] Intro + Review Stall + Call` | First reply when you need a few minutes to review the account before responding | "Hi {{First name}}, I'm [Name], a Product Advocate here to help however I can. Please give me a few minutes to review your request and account. After that, I'm happy to jump on a quick call and work through it with you live." | Tags: Live Call - Screenshare Offered, Live Call Offered |
| `[Name] Intro + Not Working + Call` | First reply when the customer reports something broken or not working | "Hi {{First name}}, I'm [Name], a Product Advocate here to help. I can see something isn't working the way it should, and I want to get that sorted for you. If it's easier, I'm happy to jump on a quick call and work through it with you live." | Tags: Live Call - Screenshare Offered, Live Call Offered |
| `[Name] You're Welcome` | Closing after the customer confirms they're satisfied | "You're welcome, {{First name}}! Really glad we could get that sorted for you. I'd appreciate it if you're able to rate your experience and hope you have a great rest of your day!" | Close, Set ticket state to Resolved |
| `[Name] Close Out` | Closing without a prior exchange (e.g. no-reply or auto-resolve) | Close action only | Close, Set ticket state to Resolved |

**How to add tag actions to a macro:** In the macro editor, click `+` next to an existing tag → **Add an action** → **Tag conversation** → search `Live Call` and select the tag. Repeat for each tag. Tags fire automatically when the macro is sent.

**Survey nudge rule:** `[Name] You're Welcome` already includes a soft personal nudge ("I'd appreciate it if you're able to rate your experience"). The bot then fires the CSAT rating prompt automatically on close. Do not add a second explicit survey ask in the same message — one personal nudge is warm; two asks back-to-back feel pushy.

**First-touch speed rule:** Send your first reply within 2 minutes of PA assignment — even if you don't have the answer yet. Use `[Name] Intro + Review Stall + Call` when you need time to investigate. A fast acknowledgement with your name prevents the customer from feeling abandoned and stops the snooze bot from firing unnecessarily.

## Text Blaze Snippets

Text Blaze is a Chrome extension that expands keyboard shortcuts into reply text across any browser tab. See `text-blaze-snippets.md` for installation steps and the full snippet list.

**Before presenting snippets:** if the EM's name is not already known from context, ask: "What's your name?" Substitute it into every snippet body before outputting — the goal is ready-to-paste text, not a template to edit.

**If Text Blaze is not installed:** offer to walk through setup: "Would you like me to walk you through adding these to Text Blaze?" If yes, follow the installation steps in `text-blaze-snippets.md` step by step.

**Wave 2 snippet bodies (substitute [Name] before output):**

| Shortcut | When to use | Ready-to-paste body |
| --- | --- | --- |
| `/hello` | Default first reply — reviewing the issue | Hi! Thanks for reaching out. I'm [Name], one of our Product Advocates. I'm reviewing your issue now, if it's easier, I'm happy to jump on a quick call and work through it with you. |
| `/higoal` | First reply when customer has a goal to share | Hi there, I'm [Name], a Product Advocate here to help. Could you share a bit more about your goal, or if it's easier, I'm happy to jump on a quick call and work through it with you. |
| `/intro` | Simple intro, no call offer needed | Hi, thank you for reaching out. I am [Name] from our Product Advocate team and am happy to assist you. |
| `/bye` | Closing after customer confirms satisfied | You're welcome! Really glad we could get that sorted for you. I'd appreciate it if you're able to rate your experience and hope you have a great rest of your day! |
| `/nudge` | On a call when you cannot hear the customer | Hi there! Just checking if our connection is still working. Is everything okay on your end? Let me know if you need any assistance. Looking forward to staying connected! |

Note: `/bye` has no first-name substitution, so it works identically in both Text Blaze and Intercom macros.

## Docs And Setup Links

- Glean Support Rep Assistant: `https://app.glean.com/chat/agents/90b93c53b44840d5b25a7836d4042304`
- Granola recipes docs: `https://docs.granola.ai/help-center/getting-more-from-your-notes/recipes`
- GodMode Lumos request: `https://app.lumosidentity.com/app_store?domainAppId=1559192`
- Zendesk Lumos request, if Wave 2 requires it: `https://app.lumosidentity.com/app_store?domainAppId=1791886`
- IKB: `https://apolloikb.zendesk.com/hc/en-us?brand_id=33894388979213`
- Text Blaze snippets and install guide: `text-blaze-snippets.md` — Chrome extension for keyboard-shortcut reply text. Cannot insert `{{First name}}` dynamically; use Intercom macros when first-name substitution is needed. Chrome Web Store: `https://chromewebstore.google.com/detail/text-blaze-templates-and/idgadaccgipmpannjkmfddolnnhmeklj`

## Shift Usage

1. Run `setup` before the shift.
1. Use `intro` for the first response.
1. Keep using `live` when a chat turns into a call or gets complex.
1. Use the Granola `/Stall` or `/Deescalate` recipe when notes show the interaction is stuck, unclear, blocked, or emotionally heated.
1. Use `macro-suggest` only when the route is clear.
1. Use `recap` or `wrapup` immediately after the interaction.
1. Use `report --date today --html` at the end of the day.
