# Mode B: CONTEXT QUERY Pipeline 5 Template

Use when you want machine-parseable output, are running a diagnostic, or are firing as part of an automated pipeline.

**Tag format reminder:**

- If pasting into Slack UI: use `@Apollo Agent` (Slack autocomplete will resolve to the mention)
- If sending via MCP API: use `<@U0ABEQ94H7Z>` (the literal mention syntax)
- The skill converts between these automatically based on the action you pick. The template below uses the UI format; the skill swaps it before any API send.

**Channel for all posts:** `#gtme-support-apollo-agent-forum` (`C0A3HGMHMN2`)

______________________________________________________________________

## Fill-in template

```
@Apollo Agent CONTEXT QUERY (Pipeline 5: Communications Orchestrator)
Task: [research_for_reply | diagnose_issue | verify_feature | check_account_config]
Audience: [customer_admin | customer_end_user | internal_gtme]
Customer: [CUSTOMER_NAME]
Team ID: [24-char ObjectID, e.g., 68dd80c2f62bd1000d40e67c]
Domain: [customer.com]
User email: [optional, specific user being investigated]
Godmode: [full godmode URL]
Notion BoB: [optional sub-page link]

[1-3 sentences of situational context: stage of relationship, urgency, what is at stake. Skip if pure feature verification.]

Questions:
1. [Specific question 1]
2. [Specific question 2]
3. [Specific question 3]
4. [Specific question 4, optional]
5. [Specific question 5, optional]

For each question, provide:
- Answer
- Confidence label: VERIFIED (KB or backend data) | INFERRED (logical conclusion with assumptions stated) | UNKNOWN (cannot determine, with what is missing)
- Evidence (KB link, backend data point, Jira ticket, Slack thread, code reference)
- Customer impact (if applicable)
- Recommended next step or reply snippet

Output format: [Plain text sections | JSON in code block per schema v1.0]
```

______________________________________________________________________

## Field rules

### `Task` (required, single value)

| Value | Use when |
|---|---|
| `research_for_reply` | Drafting a reply to a client message; need facts + KB links + a recommended snippet |
| `diagnose_issue` | Something is broken or behaving unexpectedly; need root cause + fix path |
| `verify_feature` | Checking whether Apollo does X, or whether a config is set correctly |
| `check_account_config` | Inspecting an existing setup (workflows, sequences, scoring, mailboxes) |

### `Audience` (required, single value)

| Value | Use when |
|---|---|
| `customer_admin` | Answer will be relayed to an admin (Sales Ops, RevOps, GTM Engineer) |
| `customer_end_user` | Answer will be relayed to a BDR/AE, simpler language |
| `internal_gtme` | Answer is for our team to act on, technical depth is fine |

### Customer identifier fields (split, do not combine)

The Apollo Agent explicitly asked for these as separate fields. Do not jam everything into one overloaded string.

- `Team ID`: the 24-char Mongo ObjectID (visible in admin URL after `/teams/`)
- `Domain`: customer's email domain
- `User email`: optional, when investigating one user
- `Godmode`: the full URL with `godemail=` param
- `Notion BoB`: optional sub-page link if relevant context lives there

At least one of `Team ID`, `Domain`, or `Godmode` is required for account-specific queries.

### Questions (required, 1-5, topically related)

- Each question must be self-contained (do not reference "the previous question")
- Questions must share a topic. If you have deliverability AND billing AND a feature request, post three separate Mode B queries.
- Each question should be answerable in 2-5 sentences. If a question needs a 20-paragraph answer, split it.

### Output format (required)

Pick one:

- `Plain text sections` — agent returns prose organized by question, easier to skim
- `JSON in code block per schema v1.0` — agent returns the validated v1.0 JSON schema, parseable

______________________________________________________________________

## Anti-patterns

- Combining customer identifiers into one URL field (use the split fields)
- More than 5 questions in one post
- Mixing unrelated topics
- Asking for out-of-scope items: refunds, ops actions, video/audio, secrets, third-party URL HTTP checks
- Omitting the confidence label request (you cannot tell verified facts from guesses without it)
- Omitting the output format spec (you get freeform prose, harder to act on)
