# Promo Packet — Tools & Connectors

This file defines how to search connected tools for evidence about the nominee.
The skill reads it during Step 3 (connector pre-flight) to determine which
sources to check. **Update this file — not SKILL.md — when a tool is added or
its access method changes.**

## Classification Framework

Every connected tool falls into one of three classes. Apply these rules to
listed tools and to any connector you encounter that isn't listed.

| Class | Who it applies to | What to do |
| --- | --- | --- |
| **Core** | Every nominee | Include in the pre-flight report. Search it. If unavailable, say so and invite the manager to paste anything relevant. |
| **Function-specific** | Nominees in a matching role only | Search only when the nominee's role matches. Skip silently — never surface as a gap. |
| **Excluded** | No one | Never read data from this tool, even if a connector exists. Do not mention it to the manager. |

### Classifying an unlisted connector

If a connector is available that isn't in the table below, classify it on the
spot using these rules:

- **HRIS, HR records, payroll, or benefits system** → Excluded
- **Collaboration, messaging, docs, wikis, or knowledge base** → Core
- **Meeting notes or call recording** → Core (meetings capture decisions,
  feedback, and ownership moments not recorded elsewhere)
- **Engineering tools** (issue tracking, source control, CI/CD) → Function-specific (Engineering)
- **Sales, CRM, or revenue tools** → Function-specific (GTM: Sales, SDR)
- **Support or customer-success tools** → Function-specific (Customer Support / CS)
- **Unclear** → Treat as Core; surface whatever you find and let the manager
  decide if it's useful

## Known Tools

| Tool | What to search for | Class | Access |
| --- | --- | --- | --- |
| **Glean** | Preferred starting point — search broadly across Slack, Notion, Google Docs, and more, then fetch the underlying source. Requires a separate license; may not be enabled for every manager. | Core | connector |
| **Slack** | Kudos in #kudos and #eoq-celebration; project and team channels; cross-functional threads showing the nominee's influence | Core | connector + Glean |
| **Notion** | Project pages, OKR/KR ownership, 1:1 notes, DRI assignments, decisions the nominee drove | Core | connector + Glean |
| **Google Drive** | 1:1 notes, metrics trackers, project write-ups, past performance review docs | Core | connector + Glean |
| **Granola** | Meeting notes — especially 1:1s, team syncs, and cross-functional sessions where the nominee spoke, decided, or was recognised | Core | connector |
| **Jira** | Tickets, epics, and stories the nominee owned, created, or contributed to | Function-specific (Engineering) | connector |
| **GitHub** | PRs authored and reviewed, issues, commits — evidence of technical craft and cross-team influence | Function-specific (Engineering) | connector |
| **Salesforce / Apollo CRM** | Deal ownership, pipeline data, and activity history for quota-carrying roles | Function-specific (GTM: Sales, SDR) | connector + Glean |

## Notes

- **Glean is the workhorse — when available.** It spans Slack, Notion, and
  Google Docs, so it surfaces evidence even when individual connectors aren't
  enabled. For `connector + Glean` tools, prefer the direct connector and use
  Glean to catch the rest.
- **Glean may not be enabled.** It requires a separate license. If unavailable,
  fall back to direct connectors and invite the manager to paste anything those
  can't reach. Report Glean as ❌ without implying the pack can't proceed.
- **Function-specific tools are skipped silently.** Don't mention Jira, GitHub,
  or Salesforce unless the nominee's role matches — not even as a gap.
- **HRIS and HR data are always excluded.** This covers any HR, payroll, or
  benefits system regardless of name. Do not read HR records, even if a
  connector is active.
