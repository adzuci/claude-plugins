# Apollo CLI GTM Agent Workflow Templates

Use these templates to make Apollo CLI installation feel worth it. The value is not the CLI itself. The value is giving a GTM agent high-quality account, contact, enrichment, workflow, and reporting data.

Keep first tests small, visible, and easy to verify.

## Highest-Value Use Cases

| Use case | Why it matters | First safe proof |
| --- | --- | --- |
| ICP account discovery | Finds companies that match a target market or segment. | Read-only company search with JSON output. |
| Buying committee mapping | Finds likely decision makers, champions, and operators at target accounts. | Read-only people search by domain, title, seniority, or department. |
| Account qualification | Adds firmographic, hiring, news, and account context before a seller spends time. | Company search, company detail, jobs, or news lookup. |
| Enrichment and data repair | Fills missing fields so the agent can reason with current data. | One approved person or company enrichment. |
| CRM or list staging | Converts approved outputs into reviewable contacts or accounts. | Small approved JSON file, dedupe plan, no sequence action. |
| Seller task creation | Turns agent research into work sellers can review. | One task tied to a known contact or account. |
| Paused sequence staging | Prepares outbound without sending. | Add one approved contact to paused status after sender confirmation. |
| Usage and impact reporting | Shows credit use, agent activity, and workflow value. | Usage credits and approved analytics payload. |

## Template 1: ICP Account Discovery

Goal: find accounts matching a target ICP.

Read-only examples:

```bash
apollo companies search --industry fintech --employees "100,1000" --per-page 10 --format json
apollo companies search --query "data platform" --per-page 10 --format json
```

Success proof:

- Companies match the requested segment.
- The agent can explain why each company fits.
- No credits spent and no records created.

## Template 2: Buying Committee Mapping

Goal: find the right people inside target accounts.

Read-only examples:

```bash
apollo people search --domain example.com --title "VP Sales" --per-page 10 --format json
apollo people search --domain example.com --department sales --seniority director --per-page 10 --format json
```

Success proof:

- Relevant personas returned for the account.
- The agent groups contacts by likely role: economic buyer, champion, operator, technical evaluator, or blocker.
- No enrichment or email lookup unless separately approved.

## Template 3: Account Qualification

Goal: help the agent decide whether an account is worth seller time.

Read-only examples:

```bash
apollo companies enrich --domain example.com --format json
apollo companies jobs --id ORGANIZATION_ID --format json
apollo news search --company "Example" --format json
```

Approval note:

- Company enrichment may spend credits. Confirm before running it.
- Jobs and news lookup can be used as safer first context when available.

Success proof:

- The agent produces a short qualification summary.
- The summary names evidence and missing data separately.

## Template 4: Enrichment and Data Repair

Goal: fill missing person or company fields for one approved target.

Preview:

```markdown
Target:
Command type: enrichment
Credit impact: approval required
Record creation: no, unless separately approved
```

Examples:

```bash
apollo companies enrich --domain example.com --format json
apollo people enrich --email person@example.com --format json
```

Success proof:

- The enriched fields are visible.
- Credit impact is known.
- No record is created unless that was separately approved.

## Template 5: CRM or List Staging

Goal: convert approved agent output into reviewable records.

Input: approved records in a file or pasted JSON.

Example:

```bash
apollo contacts bulk-create --file ./approved-contacts.json --format json
```

Require:

- Dedupe plan.
- Approved labels, owners, or account IDs.
- No sequence action in the same step.

## Template 6: Seller Task Creation

Goal: turn agent research into seller action without sending outbound.

Example:

```bash
apollo tasks create --user-id USER_ID --contact-id CONTACT_ID --type action_item --title "Review agent-qualified account" --priority medium --status scheduled --format json
```

Success proof:

- A seller has one reviewable task.
- No email is sent.
- The task points back to the account or contact evidence.

## Template 7: Paused Sequence Staging

Goal: prepare outbound without active sends.

Required reads:

```bash
apollo sequences search --query "TARGET_SEQUENCE_NAME" --format json
apollo email-accounts list --format json
```

Approval-gated example:

```bash
apollo sequences add-contacts --id SEQUENCE_ID --contact-id CONTACT_ID --from-email-account EMAIL_ACCOUNT_ID --status paused --format json
```

Keep paused status for first tests unless the user explicitly approves active enrollment.

## Template 8: Usage and Impact Reporting

Goal: show the agent's cost and workflow impact.

Examples:

```bash
apollo usage credits --format json
apollo users profile --credits --format json
apollo analytics report --payload ./report-payload.json --format json
```

Require the analytics payload to be approved or generated from a documented reporting need.

## First Recommendation

If the user asks where to start, recommend one of these:

1. ICP account discovery plus buying committee mapping for a known segment.
1. One-account qualification using company data, jobs, news, and key personas.
1. One approved enrichment followed by one seller task.
1. One paused sequence staging test only after sender and sequence IDs are verified.
