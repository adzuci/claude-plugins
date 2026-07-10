# Help Mode

Use this reference when the user runs `help` to check connector status and get setup guidance.

## Steps

1. Run `python3 scripts/check_dependencies.py` for Glean CLI status.
1. Probe each MCP connector with the lightest possible live call to confirm actual availability:
   - **Intercom**: call `mcp__Intercom__list_companies` with `per_page: 1`. This is a lightweight metadata list — no search engine involved. Any response (including an empty list) = connected; an empty list is normal for new or test workspaces and does not indicate a problem. Tool error or unavailability = not connected.
   - **Granola**: call `mcp__Granola__get_account_info`. Success = connected. Tool error or unavailability = not connected.
   - Google Drive/Sheets and Slack: cannot be probed without a target document or channel. Mark as "unverified — check MCP settings."
1. Build the status table and list which modes are affected.
1. If Intercom is not connected, emit setup guidance and ask whether the user wants to walk through it now.

## Output Shape

```text
## Connector Status

| Connector    | Status      | Impact if missing                                                 |
| ------------ | ----------- | ----------------------------------------------------------------- |
| Intercom MCP | <status>    | Required: live, intro, monitor, recap, triage, deescalate        |
| Granola MCP  | <status>    | Optional: recap Feedback field; paste notes/transcripts instead  |
| Glean CLI    | <status>    | Optional: product Q&A; Glean MCP/search as fallback              |
| Google Drive | Unverified  | Optional: calibration rubric Google Sheets source                |
| Slack        | Unverified  | Optional: escalation thread lookups                              |

## Modes Available Now
<list modes that are fully functional and any that are degraded>

## Setup Guidance
<include only for connectors that are not connected or are unverified>
```

## Setup Guidance Text

**When Intercom is not connected:**

```text
Intercom MCP is required for most modes. To connect it, use whichever path matches your environment:

CLI (terminal):
  claude mcp add --transport http intercom https://mcp.intercom.com/mcp

Desktop app (Claude Code app or Codex web UI):
  Settings → MCP Servers → Add server
  Transport: HTTP  |  URL: https://mcp.intercom.com/mcp  |  Name: intercom

After adding, confirm with a conversation ID or URL.
Or run `/apollo-eng-leadership:intercom-assistant setup` for the full pre-shift checklist.

Would you like help walking through the Intercom setup now?
```

**When Granola is not connected:**

```text
Granola MCP is optional. All modes work without it, but the Feedback field in recap
is omitted and Granola meetings cannot be fetched automatically.

CLI (terminal):
  Follow Granola's published MCP install docs, then run: claude mcp add granola

Desktop app (Claude Code app or Codex web UI):
  Settings → MCP Servers → Add server and follow the Granola MCP install instructions.

Alternatively, paste call notes or a transcript directly into any mode.

Would you like help setting up Granola?
```

**When Glean CLI is missing:**

```text
Glean CLI is not on PATH. Product and how-to questions will fall back to Glean MCP
search rather than the Support Rep Assistant output.
Install/authenticate the Glean CLI: run `glean auth login` or set `GLEAN_API_TOKEN`.
```
