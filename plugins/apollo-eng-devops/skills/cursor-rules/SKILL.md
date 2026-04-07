---
name: cursor-rules
description: Export Apollo skills as Cursor rules (.mdc files) into a project's .cursor/rules/ directory. Activate when the user wants to use Apollo skills in Cursor, asks to set up Cursor rules, export skills to Cursor, or mentions cursor-rules or .mdc.
---

# Export Apollo Skills to Cursor Rules

> **Official Cursor rules docs:** <https://docs.cursor.com/context/rules>
>
> **Important:** Cursor rules are project-scoped files at `.cursor/rules/*.mdc` inside a project directory.
> There is no supported global file path (e.g. `~/.cursor/rules`). To set global rules, use
> **Cursor Settings → Rules** in the UI.

## Step 1 — Locate the Apollo skills repository

Check in this order and stop at the first match:

1. The current working directory is the `apolloio/skills` repo (contains `plugins/` and `.claude-plugin/`)
1. `~/.apollo-plugins/` exists and contains `plugins/`
1. Ask the user: "Where is your local clone of apolloio/skills? (or I can clone it for you)"
   - If they want it cloned: `git clone git@github.com:apolloio/skills.git ~/.apollo-plugins`

Store the resolved path as `SKILLS_REPO`.

## Step 2 — Show available skills and ask which to export

Dynamically enumerate skills from the filesystem:

```bash
find "$SKILLS_REPO/plugins" -path "*/skills/*/SKILL.md" \
  | sed "s|$SKILLS_REPO/plugins/||; s|/skills/|  |; s|/SKILL.md||" \
  | sort \
  | column -t -s '  ' -N 'Plugin,Skill'
```

Display the output as a table, then ask:

> Which skills would you like to export? You can say:
>
> - `all` — every skill above
> - a plugin name like `apollo-eng` or `apollo-eng-devops` — all skills in that plugin
> - specific skill names like `pr-description, incident-response`

## Step 3 — Ask for the target project directory

Ask:

> Which project should I install the Cursor rules into?
> (Press Enter to use the current directory: `<cwd>`)

Store as `TARGET_PROJECT`. Verify `TARGET_PROJECT` is a directory. Create `TARGET_PROJECT/.cursor/rules/` if it does not exist.

## Step 4 — Convert and write each selected skill

For each selected skill at `SKILLS_REPO/plugins/<plugin>/skills/<skill>/SKILL.md`:

1. Parse the YAML frontmatter to extract `description`.
1. Strip the frontmatter block from the body (everything after the closing `---`).
1. Write `TARGET_PROJECT/.cursor/rules/<plugin>-<skill>.mdc` with this structure:

```
---
description: <description from SKILL.md>
alwaysApply: false
---

<body from SKILL.md>
```

**Frontmatter field meanings** (from Cursor docs):

| Field | Effect |
| ----------- | ------------------------------------------------------------------------------------------------ |
| description | Shown to the agent so it can decide when to apply the rule; required for "Agent Requested" mode |
| globs | Auto-attaches when matching files are in context (omit if not file-type-specific) |
| alwaysApply | `true` injects the rule into every session; use `false` to let the agent decide |

## Step 5 — Confirm

Print a summary:

```
✓ Exported 4 rules to /path/to/project/.cursor/rules/

  apollo-eng-pr-description.mdc
  apollo-eng-security-review.mdc
  apollo-eng-devops-incident-response.mdc
  apollo-eng-devops-systematic-debugging.mdc

To activate a rule manually in Cursor chat, type @rule-name.
To make a rule always active, set alwaysApply: true in its frontmatter.
See: https://docs.cursor.com/context/rules
```
