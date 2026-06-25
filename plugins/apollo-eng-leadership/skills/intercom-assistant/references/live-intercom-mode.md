# Live Intercom Mode

Use this reference when the user asks about a real support question or provides an Intercom conversation, customer, company, email, or vague live-support ask without `sim`.

## Pre-Reply Recap (start here)

Before drafting any reply, lead with a short recap so the EM or Product Advocate sees the customer and account at a glance. Pull facts from Intercom (and GodMode or account tools when available). Leave a field blank or mark it "not verified" rather than guessing. Show any dates or times in the customer's timezone and state the zone (see the skill's Core Behavior). Do not use em dashes.

```text
Pre-reply recap

Customer / company:
Plan tier / seats / ARR (if available):
Account age: <how long the company account has existed, e.g. "2y 4mo (created 2024-02-11)">
This user signed up: <when this contact was created, e.g. "2025-03-09 PT">
What is the customer asking for?
What outcome are they trying to get?
What have they already tried or been told?
Issue type: <how-to, bug, billing, access, deliverability, or account setup>
Account context that matters (from Intercom/GodMode):
Recent related tickets or repeated friction:
Recommended first reply:
Offer a call in the first response? <yes/no + one-line why>
If stuck, escalate to: <#ama-technical-support or #ama-support-peer-assist + why>
```

Source the two account-tenure fields from Intercom: "Account age" from the company `created_at`, and "This user signed up" from the contact `created_at` (or `signed_up_at` when present). Compute and label the age (for example, "2y 4mo") and convert the raw signup timestamp to the customer's timezone. If either timestamp is unavailable, mark the field "not verified" instead of inventing it.

## Fast Start (emit first, then keep digging)

Live mode should not go silent while it investigates. Do the single conversation fetch, then immediately emit a short first pass so the rep has something to act on within the first few seconds:

```text
Quick read (still digging):
Customer / company: <name or "pulling">
Customer ask: <one line, from the latest customer message>
Issue type: <how-to / bug / billing / access / deliverability / setup>
Apollo Team ID: <id or "not found">
Conversation: <ID or URL>
Status: investigating account context and history, full recap to follow.
```

Source this entirely from the one `get_conversation`/`fetch` payload (latest customer part plus `custom_attributes` and `source.url`). Do not block it on GodMode, Glean, or Mongo. Then continue the full workflow below and replace it with the complete Pre-Reply Recap. If a step is slow, keep the rep informed rather than waiting in silence.

## Investigation Workflow

1. Identify the lookup key:
   - conversation ID or Intercom URL
   - customer email or contact ID
   - company name, domain, or company ID
1. Use Intercom tools before drafting conclusions:
   - `mcp__intercom.fetch` for prefixed IDs or Intercom URLs
   - `mcp__intercom.get_conversation` for raw conversation IDs
   - `mcp__intercom.search` with `object_type:contacts email:<email>` or `object_type:conversations ...`
   - `mcp__intercom.search_conversations` for structured conversation filters
   - `mcp__intercom.get_contact` / `get_company` for full profiles when needed
   - Extract `source.url` from the conversation — it often reveals which Apollo page the customer was on (e.g. a sequence URL like `https://app.apollo.io/#/sequences/<id>`). Surface this in private notes; it is useful context even before the customer describes their issue.
   - Extract `Apollo Team ID` from the contact's `custom_attributes` — use it to look up the account in GodMode (see **GodMode and Apollo Admin** below).
1. Read the full thread before drafting a reply if a conversation is provided.
1. Build a short private diagnosis:
   - customer goal
   - observed symptom
   - account or permission facts found
   - what is unverified
   - likely next best action
1. If the issue involves sequences, check sequence and mailbox context (see **Sequences and Mailboxes** below) before drafting advice.
1. If the route is clear, use `routing-and-macros.md` to propose the appropriate Intercom macro/workflow. Do not apply it.
1. If the customer asks a product/process/how-to/troubleshooting question, use `glean-support-rep-assistant.md` before drafting factual guidance.
1. For the highest-volume escalated topics, use the focused triage references: billing or charges -> `billing-triage.md`; login, SSO, locked accounts, or seats -> `access-and-credentials-faq.md`; API or the Chrome extension -> `product-area-faqs.md`. These are post-Fin triage aids: lead with what to verify and where to route, not with an article to paste.
1. If the customer asks about eligibility, age, legal, compliance, ToS, privacy, or account policy, check `apollo-policies.md` before drafting any answer. Link to the authoritative document (https://www.apollo.io/terms or https://www.apollo.io/privacy-policy) in the customer-facing reply.
1. For monetization or credit questions, identify the credit model (unified vs export) from GodMode Basics before quoting specific credit amounts — Glean returns both models and quoting the wrong one will confuse the customer. The GodMode Basics tab shows "Credits (in your plan)" with the monthly amount; unified credits are labeled as a single number (e.g. 4,000 credits/mo).
1. Decide whether a Slack escalation draft is useful:
   - Use `#ama-technical-support` when the issue needs technical/product debugging, account-specific investigation, Apollo Agent help, logs, feature behavior confirmation, or "why did Apollo do X?" context that Support cannot verify from Intercom, GodMode, Glean, or IKB alone.
   - Use `#ama-support-peer-assist` when the issue is a Support process, macro, routing, policy, or peer-calibration question after the normal checks are exhausted.
   - Do not escalate just because the customer is impatient. First identify the exact unanswered question and what source is blocked or insufficient.
   - If a Slack post makes sense, include a paste-ready Slack escalation draft in the output. Do not post automatically unless the user explicitly asks to send it and a Slack send tool is available.
1. Produce the Pre-Reply Recap (see top) first, then draft a customer-facing response that acknowledges the concrete situation, verifies the goal, guides, and sets expectations. The live output leads with the Pre-Reply Recap, followed by the customer-facing reply and private notes from the skill's live output shape.

## Customer-Facing Style

- Do not apologize for Apollo, the product, or product behavior unless Apollo has clearly made an error and that tone is appropriate.
- Do not infer feelings the customer did not state. Avoid "I can see how frustrating..." and similar phrases.
- Acknowledge facts instead: deadline, blocked workflow, missing button, account change, failed step, or stated concern.
- Use calm ownership language: "I can help narrow this down", "Let's check the exact screen", "The fastest path is a quick screen share."

## Search Starters

```text
object_type:contacts email:"customer@example.com"
object_type:contacts email_domain:"example.com"
object_type:conversations source_author_email:"customer@example.com"
object_type:conversations state:open source_body:contains:"export"
```

## Tool Efficiency (minimize wasted calls)

Intercom MCP calls are the most expensive part of a live investigation. Keep them few and targeted.

- Fetch the conversation **once** with `get_conversation` or `fetch`, then reuse that single payload. It already contains `conversation_parts`, `source.url`, `statistics`, and the contact/company references. Re-read the object you already have instead of re-querying.
- When you already have an ID or Intercom URL, use `fetch`/`get_conversation` directly. Do not run `search` to rediscover something you can address by key.
- Pull `custom_attributes` (including `Apollo Team ID`), `source.url`, and PA-pickup timestamps from the conversation payload in one pass, rather than a separate call per field.
- Only call `get_contact`/`get_company` when the conversation payload does not already embed what you need.
- Cache the Glean Support Rep Assistant answer in your private notes and reuse it; do not re-ask the same question within a session.
- The `--mongo` classifier (`diagnose_mongo_sequence_mailbox.py`) is pure local logic and makes no MCP calls. Run it before any Mongo MCP call so you only query the collections in its plan, with its filter hints, rather than broad scans.

## Snoozing

Snooze is a routing action, so this skill only suggests it. Do not snooze automatically. The `Live Support Snooze for 24 Hours` workflow and the rule to prefer it over Intercom's manual snooze are defined in `routing-and-macros.md`; this section adds only when it applies.

- Valid reasons to suggest a snooze: the customer is away, the customer is testing a fix, the customer is unresponsive, or you are waiting on engineering.
- Invalid reasons: the issue is resolved, the conversation is active, a handoff is in progress, or you would be using the snooze to mask an unmet SLA.
- Always suggest leaving an internal note before stepping away.
- A 24-hour snooze is for us-blocked-on-them or us-blocked-on-engineering, never us-blocked-on-us. It does not pause the customer's wait or stop the response-time clock.

## Conflict And Output Guardrails

The tool search order (GodMode, then Glean/IKB, then Apollo Agent, then Slack search, then `#ama-support-peer-assist`) is defined in `SKILL.md` and `wave2-patterns.md` `## Toolkit Order`. Use that order. This section adds only the conflict and output rules:

- When sources disagree, IKB wins. Flag the discrepancy in `#ama-support-peer-assist` so the other source can be corrected.
- Never send IKB article links to customers. Translate the steps into plain customer-facing language.
- Never paste Apollo Agent or other tool output verbatim to a customer. Rewrite it in your own words and verify it first.

## Mongo-Backed Investigation (--mongo flag)

When the user invokes `live --mongo`, run the standard live flow first (Intercom fetch, pre-reply recap, Glean Support Rep Assistant for product/process questions), then add a Mongo evidence pass when the issue is sequence- or mailbox-related.

### When to trigger the Mongo pass

Use the classifier to decide:

```bash
python3 scripts/diagnose_mongo_sequence_mailbox.py --question "<customer issue description>" [--team-id <team_id>]
```

The script returns:

- `issue_class` — one of the five classes below
- `trigger_mongo` — True/False based on keyword analysis
- `query_plan` — which Mongo MCP servers and collections to check, with field and filter hints

**Trigger for these issue classes** (v1 scope — high-volume areas only):

- `sequence_activation_sending_failure` — sequence is on but not sending
- `contact_enrollment_failure` — contacts added but nothing happened
- `delayed_scheduled_send` — stuck, queued, or late emails
- `mailbox_linkage_auth_ramp` — mailbox disconnected, auth issues, ramp behavior
- `deliverability_configuration` — bounce rates, auth flags, tracking domain issues

**Do not trigger** for generic informational questions (how-to, what-is, pricing, plan) unless there is a clear investigative signal ("why isn't", "not working", "broken", "failed").

### Mongo collection mapping

Raw Mongo collections accessed via MCP (staging environment):

| MCP server | Collection | Analytics mirror concept |
| --- | --- | --- |
| `mcp__mongodb-mcp-staging-main` | `emailer_campaigns` | FCT_MONGO_EMAILER_CAMPAIGNS |
| `mcp__mongodb-mcp-staging-main` | `emailer_steps` | DIM_MONGO_EMAILER_STEPS |
| `mcp__mongodb-mcp-staging-main` | `emailer_contacts` | enrollment/contact state |
| `mcp__mongodb-mcp-staging-emailermessages` | `emailer_messages` | FCT_MONGO_EMAILER_MESSAGES |
| `mcp__mongodb-mcp-staging-email` | `email_accounts` | FCT_MONGO_EMAIL_ACCOUNT_CONTACTS |

> **Staging data:** These MCP servers point to the staging environment. Mongo-backed findings reflect staging state, not the customer's production account. Always note "Mongo check ran against staging — production state not verified" in private notes when citing Mongo evidence, and flag any staging/production discrepancy to `#ama-technical-support` before acting on the finding.

### Mongo investigation workflow

1. Run the classifier. If `trigger_mongo` is False, skip the Mongo pass entirely.
1. Read the `query_plan` checks. Run each via the appropriate Mongo MCP `find` tool with the suggested fields and filter hints.
1. Separate verified facts (records found) from inference (patterns implied by absence or partial data).
1. Add the structured Mongo block to **private notes only** using `format_mongo_block()` from the script:

```text
Mongo evidence (private -- do not share with customer)

Issue class: <class>
Confidence: <high|medium|low>
Signals matched: <keywords>

Mongo checks run:
  - <check label and collection queried>

Verified Mongo-backed facts:
  - <fact> (source: <collection>/<field>)

Remaining unknowns:
  - <what Mongo could not confirm>

Escalation trigger: <none / reason to escalate>
```

5. If Mongo MCP is unavailable or returns an auth error, note "Mongo MCP unavailable -- not Mongo-verified" in private notes and continue with Intercom and Glean evidence only. **Do not block the live flow.**

### Issue-to-query mapping summary

| Issue class | Primary collections | Key signal |
| --- | --- | --- |
| Sequence activation/sending | `emailer_campaigns`, `emailer_steps`, `emailer_contacts`, `emailer_messages` | `status`, `active`, step `active` flags, message count |
| Contact enrollment failure | `emailer_contacts`, `emailer_campaigns`, `emailer_messages` | Zero enrollment records = silent failure |
| Delayed/scheduled send | `emailer_messages` (pending/queued), `email_accounts` (daily cap), `emailer_campaigns` (send window) | `scheduled_at`, `sent_today`, send window |
| Mailbox linkage/auth/ramp | `email_accounts` | `status`, `auth_error`, `warmup_status`, `daily_send_limit` |
| Deliverability/config | `email_accounts` (SPF/DKIM/DMARC flags), `emailer_messages` (bounces) | `spf_valid`, `dkim_valid`, `bounce_code` |

### Guardrails

- Read-only. Never write, update, retry, or mutate records through Mongo.
- Mongo is a supplement to Intercom and Glean, not a replacement.
- Do not surface Mongo internal field names or raw document structure in customer-facing copy.
- Separate facts (record found) from inference (pattern implied by absence).
- If the Mongo MCP returns no results, report that clearly rather than guessing.

## Sequences and Mailboxes

Surface sequence and mailbox context whenever the issue involves sequences, email sending, rotation, deliverability, or enrollment.

**Quick triage tree** (the `--mongo` classifier `scripts/diagnose_mongo_sequence_mailbox.py` is the source of truth; this is a fast lookup):

- Sequence is on but not sending -> `sequence_activation_sending_failure`: check step toggles, activation state, send caps.
- Contacts added but nothing happened -> `contact_enrollment_failure`: check enrollment records (zero records is a silent failure).
- Emails stuck, queued, or late -> `delayed_scheduled_send`: check daily cap and send window.
- Mailbox disconnected, unlinking, or warming up -> `mailbox_linkage_auth_ramp`: check mailbox status, auth, and ramp.
- Bounces, spam, or low inbox rate -> `deliverability_configuration`: check SPF/DKIM/DMARC and bounce codes.

When `--mongo` is active, each branch maps to the query plan in **Mongo-Backed Investigation** above. The full issue-to-query table is also in that section. If the symptom is unclear, run the classifier rather than guessing the branch.

**Finding sequence context:**

- `source.url` in the Intercom conversation often contains the sequence URL the customer was viewing — extract the sequence ID and include it in private notes.
- Apollo MCP (`mcp__claude_ai_Apollo_MCP__*`) authenticates as the EM's own Apollo account and shows the EM's team's data only — it cannot see a customer's sequences or mailboxes. Not useful for customer lookups.
- For deep customer sequence/mailbox investigation, use the `--mongo` flag (see **Mongo-Backed Investigation** above).
- If neither is available, ask the customer for the sequence name or URL and work from what they share.

**Sequence enrollment decisions — check first:**

Before recommending any contact removal, re-enrollment, or rotation change, confirm whether the sequence is currently active (i.e. contacts are enrolled and steps are running). Getting this wrong causes real harm:

- **Sequence is active:** do not remove and re-enroll contacts — this resets them to Step 1, restarting the entire sequence. Instead: (1) pause the sequence first to prevent new sends firing from the old mailbox during reassignment, (2) use the manual sender swap: Contacts tab → filter "Send Emails From" → select contacts → "Email from different user" → Save, (3) resume once the reassignment is confirmed. Skipping the pause creates a race condition where some contacts get the new mailbox and some still fire from the old one.
- **Sequence is paused or contacts are not yet enrolled:** re-enrollment with rotation enabled is safe and the preferred path.

**New mailbox added — proactive warmup check and sequence intent:**

If the customer mentions adding a new or second mailbox to use in sequences:

1. **Ask what they want to do with existing sequences.** Two distinct intents, handled differently:
   - "Use this mailbox for future new enrollments only" — point them to the sequence settings to add the mailbox to the rotation pool before their next enrollment. No change to currently enrolled contacts.
   - "Spread some existing enrolled contacts to the new mailbox" — use the pause-first manual sender swap path above. Clarify that rotation cannot be enabled retroactively; this is a one-time manual redistribution.
1. **Check warmup status before they send at volume.** A new mailbox has no sending reputation; high-volume sending from a cold address risks spam flags and ESP throttling. Point them to: Settings → Email → Email Accounts → select the mailbox → Warm Up tab. The first mailbox warmup is free on paid plans; additional mailboxes cost monthly credits (verify the exact amount and credit model from GodMode before quoting — see below).
1. **Note the credit impact.** If the mailbox was added after the billing cycle started, warmup credits will be prorated. Confirm in GodMode before quoting a number.

## GodMode and Apollo Admin

GodMode is Apollo's internal admin tool. It provides plan, seats, ARR, credit model, feature flags, usage, permissions, and activity that Intercom does not expose.

**How to get GodMode data:**

1. **Apollo Team ID** — always present in the Intercom contact's `custom_attributes` (`Apollo Team ID` field). Use it to navigate directly to the account in Apollo Admin.
1. **Apollo Admin URL** — open Apollo Admin and look up the team by ID or the customer's email. The Basics tab shows plan, seats, credits/mo, and credit model. The Features/Permissions tab shows flags.
1. **EM shares a screenshot or paste** — treat this as verified GodMode evidence. Cite it in private notes as "GodMode (screenshot shared by EM)". Do not ask the customer to share GodMode data.
1. **Apollo MCP** — if authenticated, may expose account-level data. Try it as a fallback when the EM cannot access Admin directly.

If GodMode is unavailable and the question requires account-specific facts (plan limits, flags, ARR, credit model), say what is unverified and ask the EM to check rather than guessing.

## PA Handoff and Response Time

When reviewing how quickly a PA responded, measure from the bot handoff to the PA — not from the customer's first message. Using the wrong baseline overstates the gap and misrepresents PA performance.

**How to calculate correctly from conversation parts:**

1. Find the `message_strategy_assignment` part — this is when the bot assigned the conversation to a specific PA admin. Its `created_at` is the handoff timestamp.
1. Find the first `comment` part authored by an admin (not a bot) after that assignment — that is the PA's first reply.
1. Gap = first admin `comment.created_at` minus `message_strategy_assignment.created_at`.

**Common confusion:** Intercom's built-in `statistics.time_to_admin_reply` and `statistics.first_admin_reply_at` measure from when the conversation was created, not from PA assignment. These fields will show a larger number that includes the bot triage time and are not an accurate measure of PA pickup speed.

**In the Pre-Reply Recap**, if the conversation has already received a PA reply, surface the gap as:

```text
PA pickup time: <N min> (from PA assignment at <time> to first PA reply at <time>)
```

If no PA reply yet, note:

```text
PA pickup time: awaiting first reply (assigned <N min> ago)
```

## Evidence Rules

- Cite Intercom conversation IDs or URLs in private notes.
- Do not expose internal-only facts in customer-facing copy unless they are appropriate to share.
- If search results are incomplete, say exactly what was searched and what remains unverified.
- If Intercom tools are unavailable or auth fails, ask for pasted context or a screenshot and label the answer as not live-verified.
- Do not propose a macro or workflow unless the route is clear from source-backed context.

## Product Ideas and Bugs

When live triage surfaces a product bug or UX gap, collect it in private notes under a "Product ideas" heading. Do not surface these in the customer-facing reply.

Format each item as a ready-to-copy invocation:

```text
/apollo-eng-leadership:add-support-rotation-idea "<one-line title>" --context "<brief context from the conversation>"
```

Example:

```text
/apollo-eng-leadership:add-support-rotation-idea "Mailbox warmup cost not visible before adding a second mailbox" --context "Customer added a second mailbox and was surprised by the credit charge; no warning shown in the UI before confirming."
```

If `add-support-rotation-idea` is not installed, capture the ideas in private notes and tell the EM to submit them via the skill when it becomes available.

## Escalation Ask Template

```text
Customer/account:
Issue:
Customer goal:
What I checked:
Evidence:
Need help with:
Urgency:
```

## Slack Escalation Output

When Slack escalation is warranted, include this block after the customer-facing reply and private notes:

```text
Slack escalation:
Channel: #ama-technical-support or #ama-support-peer-assist
Post:
<paste-ready Slack message>

Why Slack now:
<one sentence explaining the blocked source-backed question>

Customer-safe follow-up:
<short Intercom reply that sets expectations while waiting>
```

For `#ama-technical-support`, prefer the channel's concise Apollo Agent style:

```text
Apollo Agent this team: <team_id or "not verified yet">. <symptom and customer goal>. Checked: <Intercom/GodMode/Glean/IKB/Apollo Agent checks or "not yet checked">. Need help with: <specific technical question>. Evidence: <conversation ID, account ID, timestamps, error text, or unknown>. Urgency: <business impact or "normal">.
```

Good escalation drafts are specific enough for someone else to answer without re-reading the entire Intercom thread. Include team/account identifiers only when verified. If the team ID, error, timestamp, or prior checks are missing, keep the missing fields explicit instead of inventing them.
