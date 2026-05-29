---
name: gtme-setup
description: Verify setup and guide users through connector activation and Notion calendar sharing
---

Use the `apollo-gtme-enablement-deck` skill for any Notion searches needed.

Run a complete setup verification for the apollo-gtme-enablement plugin.

## Purpose

This command helps first-time users set up the plugin correctly, and helps existing users troubleshoot connection issues.

## Actions

### Step 1: Welcome & Overview

Show the user:

```
🚀 Apollo GTME Enablement Plugin - Setup Verification

This plugin requires 4 connections to work:
✅ Notion (required) - Read enablement calendars & docs
✅ Google Drive (recommended) - Read training materials
⚠️ Salesforce (optional) - Pull activity & win rate data
⚠️ Gong (optional) - Analyze call recordings & demos

I'll test each connection and guide you through any missing setup.
```

### Step 2: Test Notion Connection

Attempt to search Notion for "enablement" or "training":

**If successful:**

```
✅ Notion connected successfully
```

**If fails:**

```
❌ Notion connection failed

How to fix:
1. Open https://claude.ai/customize/connectors
2. Verify "Notion" is listed and connected; if not, click Connect and sign in with your @apollo.io account
3. Re-run /gtme-setup

If Notion isn't listed even in the connectors panel, ping #it-help-desk — Apollo's enterprise deployment should provision it automatically.
```

### Step 3: Test Notion Calendar Access

Attempt to find enablement/training/launch calendars:

**If found:**

```
✅ Found enablement calendar: [Calendar Name]
```

**If not found:**

```
⚠️ No enablement calendar found

This usually means you haven't shared the calendar with the Notion integration.

How to fix:
1. Open your enablement calendar in Notion
2. Click "Share" (top right)
3. Search for "Apollo Enablement Integration" (or your integration name)
4. Grant "Read" access
5. Run /gtme-setup again to verify

See the /gtme-setup command output for troubleshooting steps.
```

### Step 4: Test Google Drive Connection

Attempt to search Google Drive:

**If successful:**

```
✅ Google Drive connected successfully
```

**If fails:**

```
⚠️ Google Drive not connected

This is optional but recommended. The plugin will work without it, but results will be less complete.

How to fix:
1. Open https://claude.ai/customize/connectors
2. Verify "Google Drive" is listed and connected; if not, click Connect
3. Re-run /gtme-setup
```

### Step 5: Test Salesforce Connection

Attempt to query Salesforce:

**If successful:**

```
✅ Salesforce connected successfully
```

**If fails:**

```
⚠️ Salesforce not connected

This is optional. The plugin will work without it, but enablement decks won't include:
- Win rate data
- Activity metrics
- Top performer stats

How to fix:
1. Open https://claude.ai/customize/connectors
2. Verify "Salesforce" is listed and connected; if not, click Connect
3. Re-run /gtme-setup
```

### Step 6: Test Gong Connection

Attempt to search Gong:

**If successful:**

```
✅ Gong connected successfully
```

**If fails:**

```
⚠️ Gong not connected

This is optional. The plugin will work without it, but enablement decks won't include:
- Real call examples
- What good looks like
- Common failure patterns

How to fix:
1. In Claude Code, run `/mcp` and authenticate with "claude.ai Gong MCP - Corp Eng [Dev]"
2. Re-run /gtme-setup

The Gong MCP is an Apollo-built custom connector; first-time OAuth happens via /mcp rather than the Claude.ai connectors panel.
```

### Step 7: Summary & Recommendations

Show a summary table:

```
📊 Setup Summary

| Connection | Status | Impact |
|---|---|---|
| Notion | [✅/❌] | Required - plugin won't work without this |
| Notion Calendar | [✅/⚠️] | Required - plugin can't find topics without this |
| Google Drive | [✅/⚠️] | Recommended - improves output quality |
| Salesforce | [✅/⚠️] | Optional - adds field evidence |
| Gong | [✅/⚠️] | Optional - adds real call examples |
```

### Step 8: Next Steps

**If all required connections work:**

```
🎉 You're all set!

Next steps:
1. Try your first command: /gtme-init
2. Or specify a topic: /gtme-init "AI Features"
3. Or build a full deck: /gtme-build "Feature Launch"

Use /gtme-init, /gtme-build, or /gtme-run-next to get started.
```

**If any required connections fail:**

```
⚠️ Setup incomplete

Required actions:
1. [List specific failures and how to fix]
2. Run /gtme-setup again after fixing to verify
3. Contact #gtme-enablement if you need help

The plugin will not work until Notion and Calendar access are configured.
```

**If only optional connections are missing:**

```
✅ Minimum setup complete!

You can start using the plugin now, but output quality will improve if you connect:
- [List missing optional connectors]

Run /gtme-setup anytime to re-check your setup.
```

## Resources

At the end, always show:

```
📚 Resources

- Get help: #gtme-enablement (Slack)
```

## Notes

- This command should be run BEFORE first use
- Can also be run anytime to troubleshoot connection issues
- Should provide clear, actionable fix steps for each failure
- Should differentiate between required vs. optional connections
