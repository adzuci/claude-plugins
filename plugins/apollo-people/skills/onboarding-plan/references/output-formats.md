# Output Format Instructions

Read this file at Step 6, after the manager confirms the plan content and chooses a delivery format.

## If they choose Notion

Before writing any content, read `references/notion-page-template.md` to understand the exact Notion enhanced markdown syntax — callout format, toggle syntax, color attributes, tab indentation rules, and icon paths. You will need this when updating content after duplication.

Duplicate the Apollo onboarding plan template (page ID: `344ab2b3b49680a7aff6fbbffaf1d571`) with the `notion-duplicate-page` tool. Title the new page "[Role Title] — Onboarding Plan". If the tool errors — for example the page ID no longer resolves — tell the manager the template couldn't be found, ask if they'd like to try again or fall back to the Word doc format, and do not attempt to fabricate a substitute page.

Immediately after duplicating, call `notion-move-pages` to move the new page to the workspace level with no parent page — the duplicate lands inside the same parent folder as the template otherwise.

Then update the following sections using `notion-update-page`'s `update_content` operation with precise `old_str`/`new_str` matching. Before each update, use `notion-fetch` on the duplicated page to get the exact current content to use as `old_str`.

**Overview table — Role row only:**
Replace the empty Role cell value with the role title from the input. Match only the Role row's empty cell as `old_str`. Do not touch any other rows, and do not regenerate or replace the table itself.

**15/30/60 Day Objectives:**
Replace the placeholder `<span color="blue_bg">` checklist items in each subsection (15 Day, 30 Day, 60 Day) with the generated objectives. All replacement content must be tab-indented to stay inside the toggle — refer to `references/notion-page-template.md` for the correct indentation structure. Include success indicators as further-indented sub-bullets under each objective.

**People to meet:**
Replace the placeholder items with the generated people-to-meet list, grouped under bold phase headers (Days 1–15, Days 16–30, Days 31–60). All content must be tab-indented to stay inside the toggle.

**Tactical — Team Resources (if provided):**
If the manager provided team resources in Step 5, add a **Team Resources** heading inside the Tactical section with the resources as a linked list. If no resources were provided, leave the Tactical section exactly as it is in the template.

**Do not modify** the Manager Instructions callout, New Hire Instructions callout, Learning & Development Program section, or the rest of the Tactical section (Meetings/Rituals and Slack Channels).

## If they choose Word doc

Generate a `.docx` file using the docx skill. Structure the document to mirror the template layout, translated into Word format:

1. **Title:** [Role Title] — Onboarding Plan
1. **Overview table** — two-column table with the same rows as the template. Pre-fill Role and the "Your Role and how it connects to Apollo's Success" bullets. Leave other rows blank for the manager to complete.
1. **15/30/60 Day Objectives** — three subsections (15 Day, 30 Day, 60 Day), each with objectives as checklist items and success indicators as indented sub-bullets
1. **Learning & Development Program** — a short paragraph noting that all new hires are assigned an orientation program in Sana within their first 60 days. Link to the correct program based on the role track: the general New Hire Orientation Program (https://apolloio.sana.ai/program/f3b71a34-7970-4d30-93d3-fca74c61653f) for most roles, or note that Sales/Revenue new hires follow the Sales Bootcamp and People Managers follow the People Manager NHO version. Do not attempt to replicate the course catalog.
1. **People to meet** — checklist items with name, title, phase, and purpose note
1. **Tactical** — subsections: "Meetings/Rituals" (blank checklist for the manager to fill in), "Slack Channels" (pre-filled: ai-native-learning, competitors, marketing, engineering), and "Team Resources" if resources were provided in Step 5 (linked list with descriptions). Omit the Team Resources heading if none were provided.

## After delivering, in either format

**In your chat message only (not in the document or Notion page)**, include this block after sharing the link or page:

______________________________________________________________________

**Manager Day 1 Reminders**

- [ ] Send a welcome message in your team's Slack channel introducing your new hire
- [ ] Meet with your new hire on Day 1 to give them a warm welcome and walk through the plan together
- [ ] Provision any role-specific systems and tools
- [ ] Check in at the end of Day 1
