# Apollo Tools & Connectors — ACE Mid-Year Review

This lists which tools the skill searches, what each is for, who it's relevant
to, and how to access it. **Update this file — not SKILL.md — when a tool is
added, removed, or its access method changes.**

The skill reads this file to drive the connector-status step and choose which
sources to search. Only search tools listed here.

## How to read this table

- **Access** tells the skill how to reach the tool:
  - `connector` — a Claude connector the employee enables at
    [claude.ai/customize/connectors](https://claude.ai/customize/connectors).
  - `connector + Glean` — reachable via a direct connector or through Glean;
    prefer the direct connector (richer results) and use Glean as a fallback.
  - `paste` — not searchable by the skill; the employee must paste content
    or links into the chat.
  - `excluded` — do not read data from this tool, even if a connector exists.
- **Relevance** is `core` (search for every employee), a named function
  (search only when the employee's role matches; otherwise skip silently —
  never surface it as a gap), or `excluded` (never search, regardless of role).

## Tools

| Tool | What it is | What to use it for | Relevance | Access |
|---|---|---|---|---|
| **Glean** | Apollo's enterprise search across Slack, Notion, Google Docs, and more | Preferred way to find evidence when available — search broadly, then fetch the underlying source. Requires a separate Glean license; may not be enabled for every employee. | core | connector |
| **Slack** | Messaging | Company-wide recognition in #kudos and #eoq-celebration; plus project/team channels and DMs. (See SKILL.md Slack section for team-specific channel handling.) | core | connector + Glean |
| **Notion** | Docs & project wiki | Project pages, OKR/KR trackers, 1:1 notes, DRI/owner assignments | core | connector + Glean |
| **Google Drive** | Docs & sheets | 1:1 notes docs, metrics trackers, OKR sheets, project decks | core | connector + Glean |
| **CultureAmp** | Performance management & engagement platform | Prior review text, check-in notes, feedback received. This is also where the final review is submitted. | core | paste |
| **Jira** | Issue tracking | Tickets, epics, stories owned/created/contributed to | Engineering | connector |
| **GitHub** | Source control | PRs authored/reviewed, issues, commits | Engineering | connector |
| **Darwinbox** | HRIS (HR system of record) | Do not read HR data from this tool. | excluded | excluded |

## Notes

- **Glean is the workhorse — when available.** It spans Slack, Notion, and
  Google Docs, so it surfaces evidence even when individual connectors aren't
  enabled. For `connector + Glean` tools, prefer the direct connector (richer
  results) and use Glean to catch the rest.
- **Glean may not be enabled.** It requires a separate license. If unavailable,
  fall back to direct Slack/Notion/Google Drive connectors and ask the employee
  to paste anything those can't reach. In Step 2, report Glean as ❌ without
  implying the review can't proceed.
- **CultureAmp can't be searched.** Ask the employee to paste prior review text,
  check-ins, or feedback they want considered.
- **Darwinbox is off-limits.** Do not read HR data from it, even if a connector
  is present.
- **Role-based tools are skipped silently.** For a non-engineering employee,
  don't search Jira/GitHub — and don't mention the absence.
