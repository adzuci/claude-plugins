# Data sources — query patterns

Concrete guidance for reaching each system. Tool names below reflect common
connector setups; if the exact tool name differs in this environment, search the
available tools for the closest match rather than guessing at parameters. If a
connector isn't present, skip that portion and mark the affected section "No
data available".

---

## 1. Salesforce (commercial system of record)

Typical connector name: `Salesforce - CorpEng`. Query with SOQL.

**Resolve the account** (Step 1 — run autonomously, no user confirmation needed):
```sql
SELECT Id, Name, Website, Industry, NumberOfEmployees, AnnualRevenue, OwnerId, Type
FROM Account
WHERE Name LIKE '%<search term>%'
```
If the user gave a Salesforce account ID, fetch it directly. If multiple
accounts match a name search, pick the best one yourself (highest ARR, or the
one with an open opportunity) per SKILL.md Step 1 — don't ask the user which
one they meant. Either way, echo the resolved name and ID in the finished
plan's snapshot header so the person can spot a wrong match after the fact.

**GTME owner (required) — do NOT use CSM/CS fields.** Ownership field names are
custom. Run `salesforce_describe_object` on `Account`, find the GTME / GTM-owner
field (e.g. something like `GTME_Owner__c`), and use it. Explicitly ignore any
CSM or CS-owner field even if populated.

**Known field names (confirmed in this org — try these first, and only fall
back to a full `salesforce_describe_object` scan if one is missing or the org
has changed):**

```sql
SELECT Id, Name, Website, Industry, OwnerId, Owner.Name,
       CS_Owner__c, CS_Owner__r.Name,      -- labeled "GTME Owner" despite the API name; this IS the GTME field
       SF_Account_Owner__c, GTME_Manager__c,
       Account_Tier_Consolidated__c,        -- picklist: Tier 1/2/3/4
       Account_Segment__c,                  -- picklist: VSB/SMB/Mid-Market/Enterprise
       Total_Active_ARR_2__c, All_Teams_Total_ARR__c,
       All_Teams_Next_Renewal_Date__c, Renewal_Date_Next_Open__c,
       ZP_TEAM_PLAN_SEAT_LIMIT__c, All_Teams_Total_Paid_Seats__c,
       High_Risk_Account__c, Whitespace_ARR__c, Seat_Penetration__c
FROM Account WHERE Id = '<id>'
```

**Trap to avoid:** `CS_Owner__c` *looks* like a CSM/CS-ownership field from its
API name, but its field **label** is "GTME Owner" and it is in fact the correct
GTME field in this org — confirmed by cross-checking its value against the
`GTME` person named in the account's existing Notion page and Slack handoff
messages. Don't skip it just because the name starts with `CS_`; check the
field label via `salesforce_describe_object`, not just the API name, if unsure.
Use `All_Teams_Total_ARR__c` / `All_Teams_Next_Renewal_Date__c` /
`All_Teams_Total_Paid_Seats__c` for ARR/renewal/seats — they matched Notion and
Snowflake in testing, whereas the bare `Total_Active_ARR_2__c` was 0 for a real
paying account (it's tracking something narrower than total ARR).

**ARR / renewal** — also custom; look for fields such as `ARR__c`,
`Renewal_Date__c`, `Account_Tier__c` via `salesforce_describe_object` if the
confirmed field names above don't exist in your org.

**Open pipeline:**
```sql
SELECT Name, StageName, Amount, CloseDate, Probability
FROM Opportunity
WHERE AccountId = '<id>' AND IsClosed = false
ORDER BY CloseDate
```

**Recent closed deals (last 12 months):**
```sql
SELECT Name, StageName, Amount, CloseDate, IsWon
FROM Opportunity
WHERE AccountId = '<id>' AND IsClosed = true AND CloseDate = LAST_N_DAYS:365
ORDER BY CloseDate DESC
```

**Contacts + recent activity** (feeds the stakeholder map and single-threading check):
```sql
SELECT Name, Title, Email FROM Contact WHERE AccountId = '<id>'
```
```sql
SELECT Subject, ActivityDate, WhoId, OwnerId
FROM Task WHERE AccountId = '<id>' AND ActivityDate = LAST_N_DAYS:90
ORDER BY ActivityDate DESC
```

---

## 2. Snowflake (product usage & health)

Snowflake analytics connectors usually require a catalog/context lookup **first**.
If a `catalog-context-search` tool exists, call it before `execute-sql` — it
returns the right tables and column semantics. Don't hand-write SQL against
guessed table names.

**Shortcut tried and found not runnable in this environment:** the
`apollo-analytics:account-detail` plugin skill assumes a local jarvis repo
(`scripts/render_account_profile.py`, `queries.sql`, etc.) that doesn't exist
in a plain Claude session — don't spend time trying to invoke it here. Query
Snowflake directly instead, using the confirmed pattern below.

**Confirmed working pattern (3 queries, no catalog-context-search needed if
you copy this directly):**

1. **Resolve team_id from domain** — a domain can map to *many* team_id rows
   (test orgs, trials, etc.). Pick the one that's actually paid (nonzero ARR
   and seat limit):
   ```sql
   SELECT apollo_team_id, team_name, website_domain, arr,
          current_paid_seat_limit, first_active_date, account_owner_name,
          csm_name, team_edition, number_of_employees, team_created_date
   FROM ANALYTICS_DB.ANALYTICS_DATASCIENCE.DIM_TEAMS
   WHERE website_domain = '<domain>' AND (is_deleted = FALSE OR is_deleted IS NULL)
   ```
   Sort by `arr` / `current_paid_seat_limit` descending and use the top team_id
   — that's the real paying team, not a stray trial/test instance.

2. **Current feature usage (last 7/28 days), by team_id, most recent date:**
   ```sql
   SELECT date, is_paid_ind, active_user_counts_l7, active_user_counts_l28,
          genpipe_feature_sequence_user_counts_l7,
          email_sent_user_counts_outreach_automatic_l7,
          genpipe_feature_dialer_user_counts_l7,
          genpipe_feature_workflow_user_counts_l7,
          genpipe_feature_record_actioned_user_counts_l7,
          paid_seat_limit
   FROM ANALYTICS_DB.ANALYTICS.DIM_TEAMS_DAILY
   WHERE apollo_team_id = '<team_id>'
   ORDER BY date DESC LIMIT 5
   ```
   This table does not have separate CRM/AI/Meetings/Lists/MCP columns under
   those names — say so explicitly in the Feature Usage table rather than
   guessing at a column name for them.

3. **Enrichment activity (separate table, daily):**
   ```sql
   SELECT * FROM ANALYTICS_DB.JARVIS.FCT_TEAM_ENRICHMENT_DAILY
   WHERE team_id = '<team_id>' ORDER BY ds DESC LIMIT 10
   ```

**Cross-check, don't silently trust one source:** compare the Snowflake
`active_user_counts_l7` figure against any internal Slack/notes claim about
weekly-active seats. If they roughly agree, cite both; if they disagree
sharply, flag the conflict explicitly in the plan rather than picking one
silently — this happened in testing (Slack said "no emails sent in 30 days,"
Snowflake showed 2 active email users that week) and the honest flag was more
useful than resolving it.

Retrieve: adoption (active users/seats vs. provisioned), the primary consumption
metric across the last 3–6 periods (so the plan shows direction: growing / flat /
declining), and a health score if one exists. Join via the Salesforce account
id, domain, or team/org id — whichever the catalog indicates is the key.

---

## 3. Apollo MCP (enrichment, hiring signal & stakeholder map)

Typical connector name: `Apollo MCP`.

- `apollo_organizations_enrich` — firmographics, headcount, funding, tech.
  **Also check the `account.typed_custom_fields` block in the response** — on
  accounts with GTME history, this often carries free-text internal notes
  (GTME fit score/reasoning, prior handoff documents, EBR strategic angles,
  "account overview" summaries) that are more current and specific than
  anything else available, and are worth pulling directly into sections 1–3.
  This costs 1 Apollo credit; confirm with the user the first time in a
  session per the tool's own required confirmation message, then proceed.
- `apollo_organizations_job_postings` — hiring signals. Clusters of relevant
  roles (new SDR team, new data org, EMEA expansion) signal budget and new
  personas. Summarize themes with dates, not every listing.
- `apollo_mixed_people_api_search` / `apollo_contacts_search` — build the
  stakeholder map across sales leadership, revenue operations, marketing
  leadership, and sales enablement. Cross-check against the Salesforce contact
  list to mark who is already engaged vs. net-new.

---

## 4. Web research (business signals)

Use web search/fetch to build the "what's happening in their business" story.
Cover: the customer's website (positioning, products, case studies), recent
news/press, LinkedIn (company page, leadership posts, headcount trend), product
launches / release notes / blog, and earnings or funding if available.

**On the website, also determine who the account sells to.** Read their
homepage, solutions/product pages, "industries we serve", and customer/case
studies to extract: target customer types, company sizes, industries/verticals,
regions, and the buyer personas/titles they sell to. Then translate that into an
Apollo prospecting play: the firmographic + persona filters for lookalike target
lists, the specific buying-intent signals Apollo should monitor for their buyers
(e.g. relevant hiring, funding, exec changes, competitor/tech footprint,
headcount growth, website-visitor intent, news triggers), and how AI research +
the Context Center would personalize outbound. Feed this into the "Where can we
create value" section and into sample outreach snippets in "How will we start
the conversation" (see SKILL.md Step 3 and Step 4).

**Put a date on every finding** where one exists. Capture the 6–12 month change
story, then stop (see the stopping rule in SKILL.md). Prefer primary sources
(the company's own site, filings, verified press) over aggregators.

---

## 5. Transcripts, Slack, Glean (sentiment, exec alignment, internal context)

- **Transcripts** — `Granola`, `Gong`, and/or `Fireflies` connectors. Pull
  recent customer calls: who attended (exec presence = alignment signal),
  sentiment, objections, commitments, competitor mentions.
- **Slack** — `slack_search_channels` to find the account/deal channel.
  Confirmed naming pattern in this org: `#ZC:<channel_id>:<ACCOUNT_NAME>`
  (e.g. `#ZC:C0AFHQQ97SP:EBANX`) — search by the account name and it surfaces
  directly. Read the **full channel history** (paginate if needed), not just
  the most recent page — account handover messages, GTME transitions, and
  onboarding-completion summaries (which contain their own embedded usage
  snapshots) are often weeks or months back and are high-value. Also open any
  thread with several replies on a stakeholder-outreach message — the thread
  usually contains the actual outcome (e.g. "got a response," "meeting
  booked") that the parent message alone won't show.
- **Glean** — search for internal docs, notes, and context on the account not
  captured elsewhere.

These feed the stakeholder map's "engaged?", "exec alignment", and "sentiment"
fields. Because none of these has a clean field, base judgments on the evidence
and mark a confidence level; hedge when inferring. Summarize — don't quote long
threads or transcript passages verbatim.
