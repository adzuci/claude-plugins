# Notion Connector Reference

Use this reference when the user wants the skill to create the Ideation Log entry in Notion, or when the observation context may live in meeting notes.

## Ideation Log Target

- Database URL: <https://app.notion.com/p/apolloio/76d67d55da054cb3b9b22a68e98cd44a?v=f627bb7835a5465fbb6c3e789c869ddf&source=copy_link>
- Data source ID, if already available from a prior fetch: `8687283d-1e9b-4ef4-a3af-f0cc72f112b2`

Always fetch the database before creating pages if the connector supports it. Use the returned schema as the source of truth for exact property names, allowed select values, and whether a property is single-select or multi-select.

## Creating the Entry

Use the Notion connector to create a page under the Ideation Log data source. If the connector is unavailable, draft the entry and recap with the database link so the user can paste it manually.

Set these defaults unless the user says otherwise:

- `Status`: `New`
- `Linked KR`: `KR 1.4 — Ideation Capture`
- `Escalated to Product?`: unchecked
- `Date`: today's date

## Wave Lookup

Check memory first for the user's wave assignment before asking or fetching.

If the wave is still unknown after checking memory, fetch the EM Customer Care Rotation page **once**, read the user's wave, save it to memory, and do not fetch again this session:

- URL: <https://app.notion.com/p/apolloio/EM-Customer-Care-Rotation-353ab2b3b49681bfa742e8b8de7a37b2>

Known assignments (from memory — verify against the page if stale):

- Adam Blackwell → Wave 2

Use `Ideation Log (Your Name) - <3-8 word observation>` as the `Observation Title`. The word-count check in `check_idea_entry.py` strips this prefix automatically.

Use a compact page body:

```markdown
## Observation
<what happened, with the specific customer/support evidence>

## Why it matters
<customer, support, product, or engineering impact>

## Suggested next step
<owner/team/action>

## Related context
Source conversation: <Intercom conversation URL if available>
```

## Clarification Rule

If the observation lacks enough detail to choose core fields or make the entry actionable, ask one focused clarification question before creating the Notion page.

Ask for the missing field that most affects routing:

- Product area, if ownership is unclear.
- Observed customer/support behavior, if the evidence is vague.
- Impact, if prioritization is impossible.
- Likely owner or next step, if the entry cannot be routed.

## Image Upload via PAK

Notion personal API keys are approved for this workflow. Use `scripts/upload_notion_image.py` to upload local screenshots and append them as image blocks on the Ideation Log page.

### One-Time Setup

1. Create an integration at <https://www.notion.so/profile/integrations> → **New integration** → workspace: Apollo, type: Internal. Copy the `ntn_...` secret.
1. Grant it access to the Ideation Log: open the database in Notion → **⋯** → **Connections** → add your integration. Uploads fail with 404 without this step.
1. `pip install requests` if not already installed.
1. Export the key as `NOTION_PAK`. Two options:

Plain (simplest — key sits in your dotfile):

```bash
echo 'export NOTION_PAK=ntn_paste_here' >> ~/.zshrc
```

1Password (key never touches disk; requires the `op` CLI signed in):

```bash
# Store the key as a Secure Note (e.g. "my-notion-pak") in 1Password first, then:
notion_pak() {
  export NOTION_PAK=$(op read "op://<vault>/<item>/notesPlain" 2>/dev/null)
  [ -n "$NOTION_PAK" ] && echo "NOTION_PAK set" || { echo "op read failed"; return 1; }
}
```

Add the function to `~/.zshrc` and run `notion_pak` once per terminal session. A lazy function is deliberate: `op` auth is interactive, so an eager `export` at the top of your dotfile would prompt on every new shell.

**Claude Code caveat:** `op` cannot run from Claude's sandboxed shell (the biometric/desktop-app auth prompt never fires, so it silently returns empty). Run `notion_pak` yourself in your terminal before starting a Claude session that needs uploads. Verify without exposing the key: `[ -n "$NOTION_PAK" ] && echo set`.

**Typical flow:**

```bash
# After creating the Notion page — page ID is the 32-hex segment ending the URL path
# (strip any ?v=... query string first; those are view/database IDs, not the page ID)
python3 scripts/upload_notion_image.py screenshot.png --page-id <notion_page_id>
```

Without `--page-id`, the script prints the `image_block` JSON so you can append it separately.

**URL-based images:** Pass directly to the Notion MCP — no PAK or script needed.

**Fallback when PAK is not configured:** Create the entry with a `Screenshot pending` note and advise the user to paste the screenshot into the Notion page manually.

## Granola MCP

Use Granola MCP only as an optional context source when available. Do not make it a dependency for the skill.

Use Granola when:

- The user says the observation came from meeting notes, Granola notes, support rotation debriefs, or a recorded discussion.
- The user asks you to find support-rotation ideas from recent notes.
- You need exact wording from a conversation before writing the observation.

Suggested Granola flow:

1. Use `query_granola_meetings` for open-ended searches across meeting notes.
1. Use `list_meetings` and `get_meetings` when the user gives a date range or likely meeting title.
1. Use `get_meeting_transcript` only when exact quotes or verbatim wording are needed.

When Granola returns citation links, preserve them in your reasoning and include the relevant source link in the recap when it helps the user verify the observation. Do not block entry creation if Granola is unavailable or returns no relevant notes; ask the user for the missing observation details instead.
