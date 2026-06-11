---
name: comp-connector-setup
description: >-
  Initial connector setup guide for the Apollo IT Employee Plugin. Use on first
  interaction with the plugin, or when a user reports features aren't working
  due to missing or misconfigured Jira, Slack, or Notion connectors.
---

# Apollo IT Plugin — Initial Setup & Connector Check

Hey! 👋 Welcome to the Apollo IT Help Desk plugin. Before we get started, I need
to make sure the right connectors are enabled so I can help you fully.

Let me walk you through a quick setup check. This only needs to be done once.

______________________________________________________________________

## What connectors does this plugin need?

This plugin uses three connectors to do its job:

| Connector | What it's used for | Required permissions |
|---|---|---|
| **Jira (Atlassian)** | Create and read IT support tickets in ITSD | Create issues, Read issues |
| **Slack** | Send messages and notifications | Send messages |
| **Notion** | Read IT knowledge base articles | Read content |

______________________________________________________________________

## Step 1 — Check your connector status

In Claude, go to **Settings → Connectors** (or click the connector icon in the chat).

Look for the three connectors below and check their status:

### ✅ Jira (Atlassian)

- **Status needed:** Connected
- **Permissions needed:**
  - ✅ Create issues (required — used to open ITSD tickets on your behalf)
  - ✅ Read issues (required — used to check ticket status)
- **If not connected:** Click **"Connect Atlassian"** and sign in with your `@apollo.io` Google account
- **If connected but missing permissions:** Disconnect and reconnect, making sure to approve both read and write scopes when prompted

### ✅ Slack

- **Status needed:** Connected
- **Permissions needed:**
  - ✅ Send messages (required — used to notify IT agents and post updates)
- **If not connected:** Click **"Connect Slack"** and sign in to the Apollo workspace (`apolloio.slack.com`)
- **If connected but messages aren't sending:** Check that you approved the `chat:write` scope during setup

### ✅ Notion

- **Status needed:** Connected
- **Permissions needed:**
  - ✅ Read content (required — used to look up KB articles and procedures)
  - ⚠️ Write access is **not required** by default — if a skill asks for it, I'll confirm with you first
- **If not connected:** Click **"Connect Notion"** and sign in with your `@apollo.io` account
- **If connected but articles aren't loading:** Make sure the Apollo workspace is selected (not a personal Notion)

______________________________________________________________________

## Step 2 — Verify everything works

Once all three connectors show as connected, type one of the following to confirm:

- `"I need help with access"` → tests the Jira + Notion connectors
- `"Check my Okta login"` → tests the Notion connector
- `"Open a ticket for me"` → tests the Jira connector end-to-end

If something still doesn't work after connecting, see the troubleshooting section below.

______________________________________________________________________

## Troubleshooting

| Problem | Fix |
|---|---|
| **Jira connector connected but tickets aren't being created** | Disconnect and reconnect Jira — make sure to approve *write* permissions (not just read) when the permission screen appears |
| **Slack connector connected but messages aren't sending** | Check that you're connected to the `apolloio` workspace, not a personal workspace |
| **Notion connector connected but can't read articles** | Make sure you selected the Apollo Notion workspace during connection — not a personal workspace |
| **Connector keeps disconnecting** | Your session may have expired — reconnect and check if your `@apollo.io` account is still active in Okta |
| **Don't see the connector option at all** | You may be using a version of Claude without connector support — check with IT (`#it-help-desk`) |

______________________________________________________________________

## Setup complete?

Once all three connectors are green, you're ready to go! Here's what I can help you with:

- 🔐 **Access requests** — Get access to any Apollo tool
- 🔑 **Login issues** — Okta, MFA, Mac locked, password reset
- 🐙 **GitHub access** — Join the Apollo org or get repo access
- 💻 **Hardware requests** — Laptop replacement, peripherals, WFH stipend
- 🎫 **Open IT tickets** — Escalate anything to a human agent in Jira
- 💿 **MDM setup** — Install Iru (Mac) or JumpCloud (Windows)
- 🧭 **Non-IT routing** — Get pointed to the right team for non-IT requests

Just tell me what you need! 🚀

______________________________________________________________________

## Need help with setup?

If you're stuck on any of the connector steps, ping `@it-help` in `#it-help-desk`
and mention "plugin connector setup" — the IT team will help you get configured.
