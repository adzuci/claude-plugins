# Plugin GUI Fallback

Use these steps if `scripts/install_plugins.py` exits nonzero or cannot reach GitHub.

## Manual Installation Steps

1. Open **Obsidian** and open (or create) your vault folder.
1. Go to **Settings** (gear icon) → **Community plugins**.
1. If Restricted mode is on, click **Turn off Restricted mode** and confirm.
1. Click **Browse**.
1. Search for **Claudian** → click Install → click Enable.
1. Search for **Obsidian Git** (by Vinzent03) → click Install → click Enable.
1. If Obsidian shows a trust prompt for either plugin, click **Trust and enable**.

## Where Files Land

After installation, each plugin's files are in:

```
<vault>/.obsidian/plugins/<plugin-id>/
  manifest.json
  main.js
  styles.css   (optional)
```

Plugin IDs are `claudian` and `obsidian-git`.

The enabled plugin list is stored in:

```
<vault>/.obsidian/community-plugins.json
```

## Verify

After enabling both plugins:

- **Claudian:** a sidebar panel should be visible in Obsidian.
- **Obsidian Git:** `Git: Commit all changes` and `Git: Push` should appear in the command palette (Cmd+P on macOS).

Return to the skill's Step 6 once plugins are installed.
