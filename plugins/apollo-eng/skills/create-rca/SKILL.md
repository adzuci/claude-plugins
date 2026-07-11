---
name: create-rca
description: Draft an RCA doc in the Notion Post Mortems database from Slack thread(s), a Zoom transcript, and a Jira incident. Run via /apollo-eng:create-rca.
disable-model-invocation: true
---

# Create RCA

Draft a complete Root Cause Analysis document as a new page in Apollo's Post Mortems database in Notion, reconstructed from the incident's Slack thread(s), Zoom transcript, and Jira INCIDENT ticket. The role prompt, drafting rules, health check, and example RCAs live in [references/drafting-guide.md](references/drafting-guide.md) — read it before drafting. To review an existing RCA instead, use `/apollo-eng:rca-doc-review <url>`; for a database-wide status report, use `/apollo-eng:rca-report`.

## Workflow

1. **Gather inputs.** If not already provided, ask for them in this order:
   - Slack thread(s): "Paste one or more Slack thread URLs." Verify each thread is actually readable before drafting; if one is not (usually the bot is not in that channel), name the failing thread and ask the user to `/invite` the bot to that channel or paste the thread contents. Never draft from partial sources silently — any source that stayed unreadable must be named in the doc.
   - Zoom transcript: "Please provide the transcript for better context (you can reach out to the on-call commander for access to the Zoom recording)." Optional — the user may skip it.
   - Jira INCIDENT link — ask only if it isn't already obvious from the Slack thread.
1. **Preflight connectors.** Note which optional connectors are available and continue without the missing ones.
   - **Notion** (required): Confirm write access via Notion MCP tools or the REST API at `api.notion.com`. If unavailable, stop and tell the user to connect Notion — never draft into a void or fabricate a page.
   - **Glean** (optional): Check for Glean MCP tools (document read/search) — Glean is often how the Google Docs template and example RCAs are reachable.
   - **PagerDuty** (optional): Check for PagerDuty MCP tools or direct access to `api.pagerduty.com`.
   - **Grafana** (optional): Check for Grafana MCP tools.
1. **Read the sources.** The Slack thread(s) carry asynchronous updates, questions, and decisions; the Zoom transcript carries the real-time debugging discussion and reasoning; the Jira ticket is authoritative for structured details — incident summary, severity, affected components, resolution status. When establishing the impact window: (a) the **authoritative impact start** is the alert timestamp in the monitoring channel (e.g. `#eng-infrastructure-alerts`), not the status-page incident creation time, which reflects when someone first published a public update and may lag impact by hours; (b) the **authoritative impact end** is the status-page incident RESOLVED time — always fetch the incident URL rather than inferring resolution from other signals; (c) verbal duration estimates from Zoom calls must be cross-referenced against BetterStack and PagerDuty timestamps before use — they often reflect queue backlog depth or other proxy signals, not confirmed customer impact.
1. **Enrich from monitoring (optional).** If PagerDuty MCP tools are available — or api.pagerduty.com is reachable directly (plain `curl` against the REST API works where PagerDuty credentials are injected into the environment; write a small script only if the environment needs one) — pull the incident's PagerDuty alerts and timeline (alert firing/ack/resolve times plus incident/alert URLs). If Grafana MCP tools are available, collect links to the dashboards relevant to the affected components. Fold both into the timeline and evidence. Degrade gracefully: if neither is available, continue without them. When reviewing PagerDuty data, note that a **PagerDuty auto-resolve** does not indicate a fix — it is commonly triggered by load subsidence or end-of-business traffic drop. Annotate it in the timeline as "PagerDuty auto-resolved — not a true fix" and continue tracking customer impact through the status-page incident independently. Document any resulting blind spot as a Contributing Factor.
1. **Read the RCA template and internalize its structure.** Primary: the [RCA Template in Notion](https://app.notion.com/p/apolloio/RCA-Template-af9b9234c0514696a4963b0bec8f5a40). Alternate, if the session has Google Docs access: the [RCA Template for Glean](https://docs.google.com/document/d/14YqoGSnPTURHgEASx2Qts_D3nRvkudM5NNgGM4hJdws). Follow it strictly for structure and required headings. If both are unreachable, fall back to the 10-section structure defined by `/apollo-eng:rca-doc-review` (same plugin) and note in the doc header that the fallback structure was used.
1. **Draft the RCA** per [references/drafting-guide.md](references/drafting-guide.md) — role, drafting rules, timeline format (timezone-labelled delta timestamps; every Slack or PagerDuty reference in the timeline must be a link), placeholder convention, and example RCAs for tone and depth. Derive the 5-Whys chains from incident evidence first; consult examples only afterward for tone and structure (see [references/five-whys.md](references/five-whys.md)). If the incident had a status-page post, align the impact window with it and link it (see [references/status-page.md](references/status-page.md)).
1. **Create the page** in the [Post Mortems database](https://app.notion.com/p/apolloio/Post-Mortems-f2b6544bfd394a34a1365430590ead57) via the Notion tools. Discover the database schema at runtime — do NOT assume property names — and set whatever properties exist (title, surface/team, severity, incident date, owner).
1. **Self-verify before handoff.** The doc must pass both: (a) the health check in the drafting guide, and (b) a review against the `/apollo-eng:rca-doc-review` rubric — apply that rubric directly to the page just created (the content is already in hand; do not re-run that skill's document-fetching flow) and iterate on the page until it passes. Then return the Notion URL plus a one-line summary of the review result.
1. **Hand off to the author.** Share the Notion URL and ask the author to: (1) review and fill any "Information not available in provided context." placeholders they can, (2) assign owners and due dates to the action items, and (3) flip Status to "Written Complete" when the doc is ready for EM review. Then add: "If you noticed anything unclear, wrong, or missing in the skill workflow during this run, mention it — this skill is continuously improved from real runs, and a one-line note now saves the next person's time."

## Workflow Contract

- **Deterministic (this skill provides)**: input-gathering order and wording, template and database locations, timeline format and linking rules, the exact missing-information placeholder, the one-new-page rule, the self-verification gate.
- **Agent judgment**: reconstructing the timeline and decision-making from Slack/Zoom, filling each template section from the sources, schema-to-property mapping, deciding whether the Jira link is already obvious from the thread.
- **Human (incident owner / RCA author)**: supplies the sources, verifies facts and fills the remaining placeholders, owns presenting the RCA.

## Safety

Creates exactly ONE new page in the Post Mortems database. Never edit, move, or delete existing Notion pages; all edits during self-verification iteration are confined to the page this run just created. Content comes only from the provided sources — never invent facts. If Notion access is missing, stop and say so instead of drafting into a void.

## Checklist

- [ ] Notion write access confirmed before any drafting
- [ ] Template structure followed strictly (all required headings present)
- [ ] Missing details use the exact placeholder "Information not available in provided context."
- [ ] Timeline uses the delta format, and every Slack/PagerDuty reference in it is a link
- [ ] Exactly one new page created; no other pages touched
- [ ] "Affected Components", "Contributing Factors", and "Resolution/Mitigation Steps" are present as standalone named headings — not folded into or embedded in the 5 Whys analysis
- [ ] Draft passed the drafting guide's health check and the `/apollo-eng:rca-doc-review` rubric
- [ ] No unconfirmed causal theories stated as fact; hypotheses labeled "(Hypothesis — unconfirmed)"
- [ ] No AI tool attribution in timeline; role-based attribution used throughout
- [ ] Every 5-Whys answer cites a source artifact; no answer copies causes or phrasing from example RCAs
- [ ] Action items: 4–6 items, Priority column (P1/P2/P3), deployed fixes marked as done
- [ ] Notion URL and one-line review summary returned

## Further Reading

- [references/drafting-guide.md](references/drafting-guide.md) — role prompt, drafting rules, timeline format, health check, templates, and example RCAs
- [references/on-call-commanders.md](references/on-call-commanders.md) — how call commanders work at Apollo and where to reach them
- [references/status-page.md](references/status-page.md) — Apollo's status page process and how RCAs should reference it
- `/apollo-eng:rca-doc-review` — the quality rubric this skill verifies the draft against
- `/apollo-eng:rca-report` — weekly status report over the Post Mortems database
