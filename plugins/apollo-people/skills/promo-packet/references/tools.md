# Promo Packet — Tools & Connectors

This lists which tools the skill searches for evidence about the nominee, what
each is for, and who it's relevant to. **Update this file — not SKILL.md —
when a tool is added, removed, or its access method changes.**

The skill reads this file to drive the connector pre-flight check and choose
which sources to search. Relevance is based on the **nominee's** department,
confirmed in Step 1 intake. Only search tools listed here.

## How to read this table

- **Access** tells the skill how to reach the tool:
  - `connector` — a Claude connector the manager enables at
    [claude.ai/customize/connectors](https://claude.ai/customize/connectors).
  - `connector + Glean` — reachable via a direct connector or through Glean;
    prefer the direct connector (richer results) and use Glean as a fallback.
  - `paste` — not searchable; the manager must paste content into the chat.
  - `excluded` — do not read data from this tool, even if a connector exists.
- **Relevance** is `core` (search for every nominee), a named department or
  function (search only when the nominee's role matches; skip silently — never
  surface it as a gap to the manager), or `excluded` (never search).

## Tools

| Tool | What it is | What to use it for | Relevance | Access |
|---|---|---|---|---|
| **Glean** | Apollo's enterprise search across Slack, Notion, Google Docs, and more | Preferred starting point — search broadly, then fetch the underlying source. Requires a separate license; may not be enabled for every manager. | core | connector |
| **Slack** | Messaging | Kudos and recognition in #kudos and #eoq-celebration; project/team channels; cross-functional threads that show the nominee's influence | core | connector + Glean |
| **Notion** | Docs & project wiki | Project pages, OKR/KR ownership, 1:1 notes, DRI assignments, decisions the nominee drove | core | connector + Glean |
| **Google Drive** | Docs & sheets | 1:1 notes, metrics trackers, project write-ups, past performance review docs | core | connector + Glean |
| **Jira** | Issue tracking | Tickets, epics, and stories the nominee owned, created, or contributed to | Engineering | connector |
| **GitHub** | Source control | PRs authored and reviewed, issues, commits — evidence of technical craft and cross-team influence | Engineering | connector |
| **Salesforce / Apollo CRM** | CRM | Deal ownership, pipeline data, and activity history for quota-carrying roles | GTM (Sales, SDR) | connector + Glean |
| **Darwinbox** | HRIS | Do not read HR data from this tool. | excluded | excluded |

## Notes

- **Glean is the workhorse — when available.** It spans Slack, Notion, and
  Google Docs, so it surfaces evidence even when individual connectors aren't
  enabled. For `connector + Glean` tools, prefer the direct connector and use
  Glean to catch the rest.
- **Glean may not be enabled.** It requires a separate license. If unavailable,
  fall back to direct connectors and invite the manager to paste anything those
  can't reach. Report Glean as ❌ without implying the pack can't proceed.
- **Department-specific tools are skipped silently.** If the nominee isn't in
  Engineering, don't mention Jira or GitHub at all — not even as a gap.
- **Darwinbox is off-limits.** Do not read HR data, even if a connector exists.
- **Add new department tools here, not in SKILL.md.** If a new function-specific
  connector becomes relevant (e.g. a support ticketing system for Customer
  Support), add a row to this table with the correct relevance label.
