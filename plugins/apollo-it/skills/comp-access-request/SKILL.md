---
name: comp-access-request
description: >-
  Self-service access requests for Apollo employees. Use whenever someone needs
  access to any tool or app — Lumos, GitHub, Glean, Snowflake, Godmode, Jira,
  Slack channels, Google Groups, and more. Also handles GitHub org access
  (apolloio), Lumos request status checks, and access escalations to IT.
---

# Access Request — Employee Self-Service

> **Live reference:** Read the [IT AI Agent Reference](https://www.notion.so/apolloio/352ab2b3b49680d090a4e8aa254b9143) Notion page using the Notion connector and use the **Tool Access** table from there for Step 2. If the page is unavailable, direct the user to ask in `#it-help-desk` for the current tool access information.

Hey! 👋 I can help you get access to the tool you need. Let me walk you through it.

______________________________________________________________________

## Step 1 — Try Lumos first (it's the fastest way)

Almost all tool access at Apollo goes through **Lumos** — it's our self-service catalog.

1. Go to **[app.lumos.app](https://app.lumos.app)**
1. Search for the tool you need
1. Click **"Request Access"**
1. Fill in a short business justification (why you need it)
1. Your manager will get a notification to approve
1. Once approved, access is provisioned automatically for most tools ✅

> 💡 **Can't find the tool in Lumos?** Let me know which tool and I'll help you figure out the right path.

______________________________________________________________________

## Step 2 — Common tools and how they work

Use the **Tool Access** table from the IT AI Agent Reference page fetched above. IT keeps this list current — always use those values.

______________________________________________________________________

## Step 3 — Already requested in Lumos but still no access?

This happens sometimes. Here's how to check:

1. Go back to [Lumos](https://app.lumos.app) and check the status of your request
1. **"Waiting for approval"** → Your manager hasn't approved it yet. Send them a reminder!
1. **"Approved"** but no access → Provisioning may have failed. Ping `#it-help-desk` with your ticket number
1. **No request found** → It may not have gone through. Re-submit and tag your manager

______________________________________________________________________

## When to escalate to IT

Ping `@it-help` in `#it-help-desk` (or I'll open a ticket for you) if:

- The tool isn't in Lumos at all
- You were approved more than **2 business days** ago and still have no access
- You need access **urgently** (blocking your work right now)
- You need access for a **contractor** (extra provisioning steps may apply)
- You need to request access **on behalf of someone else**

Before invoking `it-human-escalation`, always tell the user which condition triggered the escalation and what was already attempted. For example:

> It looks like [tool] isn't available in Lumos, so I can't walk you through self-service for this one. Let me open a ticket with IT directly.

or:

> You were approved more than 2 business days ago and still don't have access — this means provisioning likely failed. Let me escalate this to IT.

Then invoke the `it-human-escalation` skill with the full context.

______________________________________________________________________

## Need something else?

- **Can't log in to Lumos?** → That's an Okta/SSO issue, not an access issue — ask me about login problems instead
- **Can't log in** to a tool you already have access to? → Ask me about login issues
- **Need a permission upgrade** (like Godmode or admin)? → Same flow through Lumos
- **New tool not in the catalog?** → I'll help you open a request to get it added

______________________________________________________________________

## 🐙 GitHub Access — Special Setup

GitHub doesn't go through Lumos — it has a mandatory email-linking prerequisite before IT can add you to the org. Load `references/github-setup.md` for the full step-by-step instructions.
