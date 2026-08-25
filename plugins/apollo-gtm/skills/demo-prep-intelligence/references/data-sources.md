# Data Sources Reference

Detailed query templates, source priority, and SFDC field dictionary for demo-prep-intelligence. Load this file when executing data collection. SKILL.md keeps the high-level workflow; this file holds the operational detail.

## Source Priority

Use sources in this order. If a source fails or returns nothing, note the gap in the brief and continue. Execute all source searches even when an earlier source returns no results; Slack or Gong may contain the usable deal context when SFDC is sparse or missing.

1. Salesforce via Glean — canonical deal record
1. Snowflake, if available — optional structured read-only validation/enrichment
1. Slack dealroom via Glean — current motion, gap-filling
1. Gong via Glean — stakeholder-language proof
1. Gmail with Calendar, when meeting is already scheduled — calendar/email alignment
1. Lightweight web research — account context only

Internal deal context outranks public research. If they conflict, surface the conflict in Open Questions.

## 1. Salesforce via Glean

Primary source. Search Glean with an app filter for Sales Cloud when the tool schema supports it:

```
Glean:search(query="[deal identifier]", app="salescloud")
```

If the input is ambiguous (multiple opportunities returned), stop and ask the user to choose before proceeding.

### Resolving and invoking the Glean tool

Before concluding that Salesforce is unreachable, make a real attempt to locate and invoke the Glean search tool in the live runtime. Glean is not always a discretely named connector — it may surface as a search tool under a server / source id, an MCP tool, or a generic search action.

1. **Locate.** Inspect the available tools/connectors for a Glean search capability (by name containing `glean`, or a search tool whose sources include Sales Cloud / Salesforce). Do not assume the exact tool name; match by capability.
1. **Invoke with the Salesforce app filter** using the opportunity id or account as the query (see the `Glean:search` pattern above). Prefer the opportunity id when the SC supplied one.
1. **Retry once on empty discovery.** If the first attempt returns an empty envelope or no tool is found, retry with a broadened query (account name instead of opp id, or drop the `app` filter) before declaring the transport unavailable. Empty results are not the same as an unreachable tool.
1. **Do not drift.** A Glean search that returns nothing, or the absence of a Glean tool, does NOT authorize treating Notion, Slack, Drive, or web content as the Salesforce opportunity record. Those are separate sources with separate provenance — see “Glean transport unavailable (degraded mode)” below.

### Glean transport unavailable (degraded mode)

This is distinct from “Glean returned thin data” (handled by the envelope/snippet fallback below). This block governs the case where the **Glean search tool itself cannot be invoked** — no such tool is present, it errors, or discovery returns nothing after the retry in “Resolving and invoking the Glean tool”. In that state the Salesforce opportunity record is **NOT resolved**, and the skill must fail into a *tagged fallback*, never fail open.

Required behavior when the Glean transport is unavailable:

1. **Declare the state, once, visibly.** Emit `Source: SFDC via Glean — transport unavailable, opportunity record NOT resolved` in the intake summary. Do not silently proceed as if SFDC was read.
1. **Tagged fallback is allowed, but every field must carry its true provenance.** The skill may still pull deal context from Slack/dealroom (via Glean if reachable, or a Slack connector if present), Notion, Gmail/Calendar, Apollo, and web research — but any field that would normally come from the SFDC record (stage, ARR, close date, MEDDPICC, competition, champion, economic buyer, next step) MUST be tagged with its actual source and confidence, e.g. `[inferred – dealroom]`, `[inferred – Notion]`, or `[assumed]`. Never present a dealroom- or Notion-derived value under an SFDC source label, and never present it as canonical/`[verified]` SFDC fact.
1. **No bare canonical claims.** In degraded mode, no deal fact may appear without an explicit source + confidence tag. A stage, ARR, or MEDDPICC value with no tag, or tagged `Source: SFDC ...` while the record was never resolved, is a provenance defect — treat it as a failure, not a stylistic issue.
1. **Offer the recovery path.** In the Pick Your Path menu (or the degraded intake), include the option for the SC to **paste the opportunity fields** (or the Glean/SFDC result) directly, or to **retry** once Glean/Salesforce is reachable. Pasted values become `[verified – SC-provided]`.
1. **Router flow still applies.** Transport being unavailable does not authorize skipping the assigned-opportunity router default flow. Dealroom context alone is not a substitute for the router’s intake → copyable message → AE sync questions → Pick Your Path sequence; run that flow with degraded, tagged data rather than improvising a free-form answer. (See the Provenance Guard below and the router default flow in `SKILL.md`.)

### Provenance Guard (SFDC fields)

Applies on every path, but is load-bearing whenever the SFDC record is unresolved (degraded mode above) or only partially parsed:

- A field is `[verified]` with an SFDC source label **only if** it was actually read from a resolved Glean/SFDC result (or SC-pasted SFDC content). If the record was not resolved, no field may claim an SFDC source.
- Deal facts sourced from the dealroom, Notion, calendar, email, Apollo, or web must be tagged with that source and an honest confidence (`[inferred – dealroom]`, `[inferred – Notion]`, `[assumed]`), never laundered into an SFDC label or presented as canonical.
- When SFDC-origin fields are unresolved, prefer `Unknown` + an Open Question over an inferred value presented confidently. Inference is allowed but must be visibly tagged as such.
- Do not reason past a required gate (router default flow, Company + Business Understanding Gate, meeting-evidence gate) on the strength of dealroom-inferred context. Inferred context lowers confidence; it does not satisfy a gate that expects resolved/grounded data.

### Glean Result Parsing

Glean search may return semantic snippets or document excerpts rather than clean SFDC field-value pairs. Do not assume a 1:1 mapping between a search result and the SFDC field dictionary.

**Response envelope (primary transport).** The Glean search response returns results as an array of result objects. The full document content for a result lives at `data[0]['text']` (the `text` field of the first result object) — this is the primary transport and should be read first. The SFDC JSON blob, when present, arrives inside this `text` field, not in a separate structured field.

- **Primary:** read `data[0]['text']` for the full content of the top result; iterate `data[i]['text']` for additional results.
- **Fallback:** if `data[0]['text']` is empty, missing, or the envelope shape differs in the live tool schema, fall back to semantic-snippet parsing (the `snippets` array) plus the conflict-handling rules below. Do not fail closed — degrade to snippet parsing and note the transport used.

Parsing rules:

- SFDC results from Glean may arrive as a single large JSON blob inside the `data[0]['text']` field (or, in the fallback path, inside a snippets array). When this happens, parse the JSON-like content to extract field values using the field dictionary. Do not treat the raw blob as ordinary prose.
- Match snippets against the field dictionary labels when field names are visible.
- Extract concrete claims from snippets, not from surrounding boilerplate.
- If a snippet clearly contains a field value and the field label is visible, label it with the specific source, such as `Source: SFDC Identified Pain field`.
- If the result appears to come from Salesforce but the field label is unclear, label it `Source: SFDC (specific field not identified)` and classify the claim as `[inferred]` unless another source verifies it.
- If a result only mentions a theme such as "pain", "competition", or "decision criteria" without a specific field label or value, treat it as a lead for further searching, not as a verified claim.
- If multiple snippets conflict, surface the conflict in Open Questions rather than choosing one silently.

### SFDC JSON Extraction and Trimming

Glean can return a massive SFDC JSON blob containing the opportunity, account, contact records, activity metadata, and engagement fields. Do not carry the full blob forward into synthesis. Extract a compact canonical deal record first, then discard irrelevant raw fields from working context.

Canonical SFDC extraction order:

1. Opportunity metadata: account name, opportunity name, stage, ARR, close date, AE, SC, segment, company size, industry.
1. MEDDPICC and deal strategy fields listed in the SFDC Field Dictionary.
1. Notes, Solution Engineer Notes, Next Step, Next Step History, Capabilities, and any Data Duel or evaluation fields.
1. Stakeholders: name, title, role in deal, email/domain only when useful for disambiguation, source field, and any deal-relevant notes.
1. Technical and commercial risk fields: CRM, email provider, security notes, procurement/paper process, competition, pricing or AE promises.

Trim or ignore unless directly relevant:

- Contact activation metrics, generic engagement counters, enrichment metadata, unused CRM sync internals, stale activity fields, empty/null fields, and unrelated account/contact operational fields.
- Duplicate account/contact records after extracting the stakeholder identity and deal-relevant role.

If the raw SFDC blob contains hundreds of fields, produce an internal compact record before moving to Slack, Gong, web research, or synthesis. The brief should cite specific extracted fields, not the existence of the raw JSON blob.

### SFDC Field Dictionary

Apollo SFDC uses emoji-prefixed and `- CI` (Command of the Message) suffixed fields for several MEDDPICC concepts. **These are separate Salesforce fields, not alternate labels for one field — both must be ingested, not just whichever is matched first.** They can genuinely disagree (e.g. a real Opportunity's `Competition__c` read "Other;" while its `Competition_CI__c` read "Firmable" — the specific, useful answer was in the field that would have been skipped if only one were checked). If ingested values conflict, that is a real conflict — handle it per the existing rule above ("If multiple snippets conflict, surface the conflict in Open Questions rather than choosing one silently"). No new mechanism is needed beyond ingesting both.

| Logical field | Label(s) | Salesforce API field name(s) |
|---|---|---|
| Identified Pain | 🔴 Identified Pain; Pain Points - CI | `Before_Scenario__c`, `Pain_Points_CI__c` |
| Decision Criteria | 🟡 Decision Criteria; Decision Criteria - CI | `Decision_Criteria__c`, `Decision_Criteria_CI__c` |
| Decision Process | 🟡 Decision Process; Decision Process - CI | `Decision_Process_del__c`, `Decision_Process_CI__c` |
| Competition | 🔴 Competitors; Competition - CI | `Competition__c`, `Competition_CI__c` |
| Competitor Details | 🔴 Competitor Details | `Competitor_Details__c` |
| Champion | 🟡 Champion; Champion - CI | `Champion__c`, `Champion_CI__c` |
| Champion Details | 🟢 Champion Details | `Champion_Details__c` |
| Has Champion (flag) | 🔴 Has Champion (Yes/No — a corroborating signal, not a substitute for Champion Details) | `Champion_Identified__c` |
| Economic Buyer | 🔴 Economic Buyer (lookup field — see note below) | `Economic_Buyer__c` |
| Economic Buyer Details | 🟢 Economic Buyer Details; Economic Buyer - CI | `Economic_Buyer_Details__c`, `Economic_Buyer_CI__c` |
| Metrics | 🔴 Metrics; Metrics - CI | `Metrics__c`, `Metrics_CI__c` |
| Paper Process | 🟡 Paper Process; Paper Process - CI | `Paper_Process__c`, `Paper_Process_CI__c` |
| Notes | 🟢 Notes | `Notes__c` |
| Capabilities | Apollo capabilities flagged for the deal | `Number_of_JTBD_Added__c`, `Number_of_JTBD_Validated__c`, `Submit_JTBD__c`, `Validate_JTBD__c` |
| Solution Engineer Notes | Solution Engineer Notes | `Solution_Engineer_Notes__c` |
| Business Impact | Business Impact | `Negative_Consequences__c` |
| After Scenario | After Scenario | `After_Scenario__c` |

**Force Management's three constructs, and the one whose label hides it — added 2026-08-19, all three labels verified by a live `FieldDefinition` query against the org.** Force Management's before-state / negative-consequences / after-state trio maps onto this org's fields as follows, and two of the three do not read the way their API names suggest:

| Force Management construct | Verified label in this org | API field name |
|---|---|---|
| Before state | **🔴 Identified Pain** | `Before_Scenario__c` |
| Negative consequences | **Business Impact** | `Negative_Consequences__c` |
| After state | **After Scenario** | `After_Scenario__c` |

Two consequences worth stating, because both have already caused a real error:

- **`Negative_Consequences__c`'s label is "Business Impact," not "Negative Consequences."** Never render the plain reading of the API name as a label — the demo prep guide prototype did exactly that and shipped a field label that does not exist in the org.
- **`Before_Scenario__c` has no dedicated before-state field; it *is* Identified Pain.** Anyone reasoning about Force Management coverage from API names alone will conclude the before-state is missing when it is in practice the best-populated of the three. It appears twice in this dictionary on purpose — once as Identified Pain (its MEDDPICC role) and once here (its Force Management role) — because it is one field serving both.

**Why these two rows were added at all:** the dictionary is what the skill matches the raw record blob against, so a field missing from it is a field the skill can fail to recognize *even when it is fully populated* — the exact mechanism that once produced "no economic buyer identified" on an opportunity whose field was populated. Both fields are live and both were absent from this table until now, making that false negative latent for two of Force Management's three constructs.

**Economic Buyer is a lookup field, not free text — its value is a Salesforce record ID, never a name by itself.** Confirmed on a real record: `Economic_Buyer__c` held `003UM00000bZayZYAS`, not "Cara Christofi." Two ways to get the actual name, easiest first: (1) check **Economic Buyer Details** — it's free text and normally names the person directly (it did here: "Cara..., the Head of Regional Marketing... at Sokin..."). (2) If Details doesn't name them, use the Salesforce Contact ID to search for the direct Contact record. Never report the raw ID string itself as the answer.

**Dropped, verified 2026-07-09 via a live `describe_object` call against the real Opportunity schema (659 fields checked):** the original dictionary listed a bare "Champion Name" variant under Champion and bare "Identified Pain" / "Competitor Details" / "Metrics" / "Paper Process" variants without emoji or suffix. None of these appear as distinct fields in the real object schema — they were most likely imprecise restatements of the emoji-prefixed field's own label, not separate fields. Removed rather than carried forward unverified.

**Deliberately not added**, to avoid scope creep beyond what already existed: `zCompetition_Old__c` (explicitly a deprecated field) and several other competitor-adjacent fields serving different purposes (`AL_Competitors__c`, `LID__MainCompetitors__c`, `Gong__MainCompetitors__c`, `Lost_to_Competitor__c`) — these support other workflows (closed-lost analysis, other integrations), not live-deal MEDDPICC context.

### Deal Metadata to Extract

Stage, ARR, Close Date, Account Segment, company size, industry, Next Step, Next Step History.

### Stakeholders to Extract

Initial Meeting Contact (with title), Champion, Economic Buyer, technical evaluator, named end users.

## 2. Snowflake, If Available

Snowflake is optional and environment-dependent. Use it only if a Snowflake MCP/server is available in the live Claude Project and can be queried read-only.

Before querying:

- Inspect available databases, schemas, tables, and fields.
- Confirm the source contains opportunity or account-level deal data relevant to demo prep.
- Do not assume table names or column names.
- Do not write, update, create, or delete anything.

Use Snowflake when it provides cleaner structured data than Glean snippets, such as:

- Opportunity stage, ARR, close date, segment, owner, SC, AE.
- MEDDPICC field values mirrored from SFDC.
- Data Duel, enrichment test, or fill-rate results.
- Product usage or evaluation telemetry that is explicitly approved for sales use.

Use source labels such as:

- `Source: Snowflake opportunity table`
- `Source: Snowflake SFDC mirror`
- `Source: Snowflake Data Duel results`

If Snowflake and Glean/SFDC conflict, do not silently choose one. Surface the conflict in Open Questions or Landmines and tag the claims with their respective sources.

If Snowflake schema discovery is unavailable or too broad, skip Snowflake and continue with Glean, Slack, Gong, and web.

## 3. Slack Dealroom via Glean

Secondary source. Channel names vary widely:

- `#deal-[company]-[AE last name]`
- `dealroom-[company]`
- `[company]-deal-room`
- Informal company-name channels

### Dealroom Name Parsing

If the input is a Slack channel name, extract the likely company segment before searching other systems:

- Remove leading `#`.
- Remove known prefixes such as `deal-`, `dealroom-`, `deal-room-`, and `oppty-`.
- Remove common suffixes such as `-deal-room`, `-dealroom`, and trailing AE last names when they are clearly not part of the company name.
- Convert delimiters (`-`, `_`, repeated spaces) into spaces.
- Use the extracted company name as the primary SFDC/Gong/web search term.
- Also search the full original channel name as a secondary query when extraction is ambiguous.

Examples:

| Input | Primary extracted search term | Secondary query |
|---|---|---|
| `#deal-thredd-johnson` | `thredd` | `deal thredd johnson` |
| `dealroom-collage-group` | `collage group` | `dealroom collage group` |
| `keeper-security-deal-room` | `keeper security` | `keeper security deal room` |

### Search Strategy

Search broadly. In practice, keyword searches often return the relevant dealroom threads without needing channel filters. Start with keyword searches, then add channel filters only if the live Glean tool schema supports them and the keyword search is too noisy:

```
Glean:search(query="[account name] deal demo", app="slack")
Glean:search(query="[account name] pain technical competition", app="slack")
Glean:search(query="[account name]", app="slack", channel="deal*")
Glean:search(query="[account name]", app="slack", channel="dealroom*")
```

Before implementation in a new environment, inspect the live Glean search tool schema and align parameter names to the actual API. If channel filtering is not supported, do not pass a `channel` parameter. Use keyword fallbacks instead:

```
Glean:search(query="[account name] deal", app="slack")
Glean:search(query="[account name] dealroom", app="slack")
Glean:search(query="[account name] demo", app="slack")
Glean:search(query="[account name] pain technical competition", app="slack")
```

When channel filtering is unavailable, manually filter results for dealroom relevance by channel name, thread context, AE/SC participants, customer/account name, and recency.

### Channel search fallback chain (ordered)

When locating the dealroom, work down this chain and stop at the first step that returns a confident match. Record which step succeeded (or that all failed) so the `dealroom_status` below is accurate.

1. **Exact channel name** — if the SC supplied a channel name, search it verbatim (minus leading `#`).
1. **Extracted company term** — search the company segment parsed by Dealroom Name Parsing above (e.g. `thredd`).
1. **Channel-filter patterns** — if the live schema supports a `channel` parameter, try `channel="deal*"` then `channel="dealroom*"` then `channel="*[company]*"`.
1. **Keyword-only queries** — if channel filtering is unsupported or step 3 is empty, run the keyword fallbacks (`[account name] deal`, `dealroom`, `demo`, `pain technical competition`).
1. **Manual relevance filter** — filter whatever results returned by channel name, thread context, AE/SC participants, account name, and recency.
1. **Declare not found** — if steps 1–5 all fail, set `dealroom_status: not_found` (or `ambiguous` if multiple plausible channels compete) and continue with the other sources. Never fabricate a dealroom or silently assume one channel when the search was ambiguous.

### Assigned-Opportunity Output Contract (mandatory)

For any assigned-opportunity workflow (router default flow in SKILL.md, Deal Entry for assigned-opp intent in SC-GUIDE.md), this Slack/Glean dealroom search must run **before** the Internal AE / Dealroom Coordination Draft is produced and must return the following structured result:

```yaml
dealroom_status: found | not_found | ambiguous | unavailable
candidate_channels:
  - "#[channel-name]"  # zero or more
notes: "[optional one-line explanation, e.g. 'matched on AE last name', 'no exact match', 'Glean returned no slack results']"
```

Status definitions:

- `found` — exactly one channel clearly matches the account (channel name, AE/SC participants, recent activity). Use this channel as the coordination draft destination.
- `not_found` — search ran successfully but no channel matched. Coordination draft is an AE DM with an ask to confirm or create the dealroom.
- `ambiguous` — multiple plausible channels matched and no single one is clearly the active dealroom. Coordination draft is an AE DM listing the candidates.
- `unavailable` — Slack/Glean access is missing, blocked, or returns an error. Record the cause; coordination draft is an AE DM with an explicit caveat that no Slack search ran.

This contract is mandatory: the search runs first whenever Slack/Glean is available, and the resulting `dealroom_status`, `candidate_channels`, and (when applicable) `destination_reasoning` feed the internal router payload described under `SC-GUIDE.md`'s "Assigned Opportunity Visible Output (copyable-message-first)" section (under `dealroom_search`) — **corrected 2026-07-28; this previously named a "Step 1 Assigned Opp Router YAML Payload" heading that no longer exists** and the `coordination_draft.destination` selection rules in `deal-lifecycle-support.md`. The same values must remain visible in the SC-facing intake summary. **Current visible ordering (corrected 2026-07-28):** step 1 is the intake summary, step 2 is the copyable message — the older "step 1 = router YAML, step 2 = intake markdown" model is superseded, and the router YAML is internal-only, never rendered.

Extract from the last 30 days when available:

- Pain points, business drivers, technical questions, competitive mentions
- SC and AE strategy threads
- Customer-facing artifacts: slides, docs, data test files, test results
- Data Duel or enrichment test status and outcomes

## 4. Gong via Glean

Enrichment for prospect-language proof:

```
Glean:search(query="[account name]", app="gong")
```

Extract:

- Stakeholder quotes about pain, priorities, objections, success criteria
- Objections and the responses given
- Technical questions asked by the prospect
- Competitive mentions stated by the prospect
- Call dates and speaker names when visible

If date or speaker is not visible, label the source accordingly rather than inventing detail.

If SFDC Notes already contain dated call summaries with speaker names and substantive content, Gong search may be redundant for that deal. Still run the Gong search for completeness when available, but do not duplicate call-summary content already captured from SFDC. Prefer Gong only when it adds direct stakeholder quotes, objections, or details not present in SFDC.

**Gong indexing degradation (known failure mode).** Gong calls are indexed into Glean asynchronously, so the most recent call(s) may not yet be searchable — a Gong search can return stale or partial results, or nothing, for a call that happened in the last 24–48 hours even though it exists. Do not treat an empty or thin Gong result as proof that no recent call occurred. When the deal timeline (SFDC Next Step, calendar, or dealroom) implies a very recent call that Gong does not surface, note the gap explicitly (`Source: Gong — recent call may not be indexed yet`), lean on SFDC Notes / dealroom / calendar for that window, and flag it in Open Questions rather than asserting the call's content or its absence.

## 5. Gmail with Calendar Alignment

Use this when the SC says an AE sync, customer demo, technical call, follow-up demo, or prep meeting is already on calendar. This source is read-only and only aligns meeting context; it does not replace Salesforce, Slack, Gong, or transcript evidence.

Available connector observed: `gcal` ("Gmail with Calendar") with:

- `search_calendar`
- `search_email`

### Calendar Search

Use `search_calendar` to retrieve likely meeting events. The schema requires `queries`, `start_date`, and `end_date` fields, but at least one of them must be non-empty/non-null. Use short query variants and a narrow date range when the meeting timing is known.

Example argument pattern:

```json
{
  "queries": ["[account name]", "[AE name]", "[meeting title keyword]"],
  "start_date": "[ISO start date if known]",
  "end_date": "[ISO end date if known]"
}
```

Extract:

- Event title, date/time, attendees, organizer, and meeting type.
- Description or agenda language.
- Conference link context only when useful for identifying the meeting; do not expose private links in SC-facing artifacts unless needed.
- Any attachment or document references visible in the event.

### Email Search

Use `search_email` with `queries` as a list of Gmail-style search strings. Do not use unsupported `max_results`, `newer_than`, or a singular `query` field.

Example query set:

```json
{
  "queries": [
    "\"[Account Name]\"",
    "\"[meeting title]\"",
    "from:[AE email or name] \"[Account Name]\"",
    "\"[customer domain]\""
  ]
}
```

Extract:

- Scheduling or agenda threads.
- AE/customer prep asks.
- Customer questions, attachments, data-test files, security documents, or follow-up requests.
- Commitments or promises in email that the SC should not contradict.
- Mismatches between email, calendar, SFDC, Slack, and Gong.

### Alignment Output Contract

When this source is triggered, produce a compact internal alignment object before AE-sync questions, demo story, Context Center payload, or Apollo AI prompts:

```yaml
calendar_email_alignment:
  status: found | partial | not_found | unavailable
  calendar:
    matched_events:
      - title: string
        start_time: string
        attendees: [string]
        organizer: string
        notes: string
  email:
    relevant_threads:
      - subject: string
        participants: [string]
        signal: string
  mismatches:
    - string
  ae_sync_implications:
    - string
```

Use `found` when at least one relevant calendar event and one relevant email thread are found. Use `partial` when only calendar or email returns useful context. Use `not_found` when the connector searched successfully but nothing matched. Use `unavailable` when the connector is disconnected, blocked, or errors.

### Source Labels

- `Source: Calendar event, [date/time], [event title]`
- `Source: Gmail thread, [date], [subject]`

Calendar/email evidence should usually be `[verified]` for meeting logistics and `[inferred]` for deal meaning unless the email text directly states the claim.

## 6. Company Research

Company research is **lightweight for the seven-section brief** but **mandatory for the Apollo AI Context Center calibration payload** when SFDC, Slack, Gong, and SC-provided context do not give source-grounded answers for the prospect's offering, customer profile, buyer pains, value prop, competitors, and CTA. The Context Center payload calibrates Apollo AI on the prospect company; without grounded company facts, Apollo AI is calibrated against a generic or invented profile, which contaminates every downstream prompt.

### Brief-mode usage (lightweight)

For the seven-section brief, run a lightweight web search for account context:

```
web_search(query="[company name] [industry]")
```

Extract only what helps SC prep:

- What the company does
- Industry, size, segment, recent news
- Tech stack signals from job posts, integrations, public pages

Public research never overrides internal deal context.

### Context Center calibration usage (mandatory when internal sources are insufficient)

Whenever this skill is asked to produce an Apollo AI Context Center payload, Apollo AI prompts, or trial setup prompts, the upstream **Company + Business Understanding Gate** in `SKILL.md` requires source-grounded answers for: what the prospect company does, who they sell to, how they go to market, what pains *their* buyers have, their value prop, primary competitors *in their market*, social proof if verifiable, and CTA. If SFDC, Slack, Gong, and SC-provided context do not cover these fields, run targeted research before emitting the payload:

1. **Prospect website** — fetch the homepage and the most informative subpages (`/`, `/product` or `/platform` or `/solutions`, `/customers` or `/case-studies`, `/about`, `/pricing` if public). Use a web fetch when available; otherwise targeted web search:
   ```
   web_search(query="[company name] site:[domain] product")
   web_search(query="[company name] site:[domain] customers")
   web_search(query="[company name] site:[domain] about")
   ```
1. **Category and competitor language** — look up how the prospect is categorized and which competitors their buyers compare them against (review sites like G2/Capterra/TrustRadius for software vendors, or industry directories for non-software). Only record competitors that are clearly named in the prospect's market, not Apollo battlecard competitors.
1. **Social proof** — capture only verifiable named customers, case studies, or metrics that the prospect attests to or that appear in credible public sources. If unverifiable, omit.
1. **News / context** — recent funding, leadership changes, product launches, or strategy shifts that explain *why now*.

Use these source labels in the Context Center payload:

- `Source: Prospect website [path]`
- `Source: Prospect case study [title]`
- `Source: G2 / Capterra / TrustRadius listing`
- `Source: Public web research [query]`
- `Source: SFDC Account Description`

Confidence rules for Context Center company-profile fields:

- `[verified]` — directly attested by the prospect (their website, their case study, their AE-confirmed positioning) or a credible public source quoting them.
- `[inferred]` — derived from adjacent context (e.g. ICP inferred from their public customer logos and industry framing, value prop inferred from their homepage hero plus a couple of subpages).
- `[assumed]` — **not allowed** in the company-profile fields. If the only available evidence is `[assumed]`, omit the field and surface it in the Missing Business Context checklist.

If research cannot close a required field, do not invent. Render the Missing Business Context checklist defined in `SKILL.md` instead of a payload. Public research never overrides internal deal context, but it is required when the internal context is missing for the company-profile fields.

## Context Budget Priority

Rich deals can return very large SFDC, Slack, and Gong payloads. When context is constrained, prioritize in this order:

1. Extract SFDC field dictionary values and deal metadata first.
1. Extract stakeholder names, roles, and source-backed priorities.
1. Use Snowflake structured values for validation only when schema and provenance are clear.
1. Extract the most recent Slack dealroom updates, especially blocker, exec, pricing, and technical threads.
1. Extract Gong quotes only when they add new prospect-language evidence not already in SFDC notes.
1. Use Gmail/Calendar alignment only for scheduled-meeting context: attendees, agenda, timing, recent communication, and mismatches.
1. Use public web research last and only for account context.

For sparse deals, keep sections concise. Do not pad missing sections with boilerplate; use Unknown and move gaps into Open Questions.

## Source Labels

Use these specific labels in the brief:

- `Source: SFDC Identified Pain field`
- `Source: SFDC Decision Criteria field`
- `Source: SFDC Notes`
- `Source: Slack dealroom, [date], [person]`
- `Source: Gong call, [date], [speaker]`
- `Source: Calendar event, [date/time], [event title]`
- `Source: Gmail thread, [date], [subject]`
- `Source: Snowflake [table/view name]`
- `Source: Company website`
- `Source: Public web research`

When dates or speakers are unavailable:

- `Source: Gong result, date not visible`
- `Source: Slack dealroom result, author not visible`

## Graceful Degradation

| Data availability | Behavior |
|---|---|
| Full SFDC + Slack + Gong | Rich brief, high confidence, cross-source synthesis |
| SFDC populated, no Slack/Gong | Brief from SFDC + state: `No dealroom or call history found — brief based on SFDC data only.` |
| Sparse SFDC, active Slack | Pull from Slack, flag SFDC gaps as Open Questions, distinguish Slack-derived claims |
| Minimal data everywhere | Generate only what is supported, make Open Questions the longest section, state: `Sparse data — recommend AE sync before demo.` |
| **Glean transport unavailable (SFDC unresolved)** | Enter **degraded mode** (see §1 “Glean transport unavailable”). Declare `SFDC record NOT resolved`, allow tagged fallback to Slack/Notion/calendar/Apollo/web with every SFDC-origin field tagged `[inferred – dealroom/Notion]` or `[assumed]`, never as canonical SFDC fact. Offer the SC a paste-fields / retry recovery path. Still run the router default flow — do not improvise past its gates. |

Never invent stakeholders, pains, competitors, metrics, tech stack, or demo recommendations to fill gaps. **Never present a value derived from the dealroom, Notion, calendar, or web under an SFDC source label, or as canonical SFDC fact, when the SFDC record was not actually resolved (see the Provenance Guard in §1).**
