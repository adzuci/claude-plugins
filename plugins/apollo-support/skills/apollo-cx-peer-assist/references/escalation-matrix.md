# Escalation Matrix — Reference

> Source of truth: Apollo Escalation Matrix spreadsheet
> Last updated: June 2026
> Owner: Jocel / Billing team

______________________________________________________________________

## ESCALATION CHANNELS & WORKFLOWS

| Situation | Channel | Workflow / Method | Approver |
|---|---|---|---|
| Billing refund exception | `#ama-support-billing` | *PA Billing Refund Exception Request* workflow | Jocel |
| Billing escalation follow-up (live chat) | `#ama-support-peer-assist` | *Billing Escalation Follow-Up* bot | Billing Advocates team |
| Tech escalation follow-up | `#ama-support-peer-assist` | *Tech Escalation Follow-Up* bot | Tech Support team |
| Fraud / security concern | Intercom | *Fraud Review BO* ticket type OR *Escalate to External Fraud* flow | Security team |
| Stripe info request (locate team by card) | `#ama-support-peer-assist` | *Stripe Information Request* bot | Stripe/Billing Ops |
| Invoices >6 months (if approved) | DM | DM Jocel + Kenny | Kenny |
| Contracts / legal scenarios | SD (Sales Dev channel) | Flag for Legal | Legal team |
| Partnerships promo application | `#partnerships` | Post for Tania or Allie | Tania / Allie |

______________________________________________________________________

## APPROVERS QUICK REFERENCE

| Situation | Approver |
|---|---|
| Most billing refund exceptions | Jocel |
| Cash refunds >$2,400 | Billing team |
| Invoices >6 months (if exception granted) | Kenny |
| Contracts / legal | Legal team |
| Fraud / security | Security team |
| Partnerships promo (Startup discount etc.) | Jocel can apply, or Tania/Allie via `#partnerships` |

______________________________________________________________________

## WHEN TO ESCALATE TO BILLING / ACCOUNT ADVOCATES

Escalate via `#ama-support-billing` → *PA Billing Refund Exception Request* when:

- Refund exceeds PA cash limit (>$1,200)
- Customer has had a prior exception
- Auto-renewal exception outside the standard window
- Accidental annual upgrade not meeting first-time criteria
- Bad press risk, legal threats, or churn risk on a material account
- Temp credits request over PA limit (>1,000 email / >100 mobile / >6,000 unified)
- AI field credit refund over 40,000 credits

______________________________________________________________________

## WHEN TO ESCALATE TO LEGAL

- Tiered pricing language in an agreement
- Multi-year deals
- Rollover credits ($50K ARR+ threshold)
- Early opt-out clauses ($50K ARR+ and CRO approved)
- Non-standard term lengths (only 12-month increments allowed)
- Early terminations (exceptions for our mistakes or platform issues only)
- Any customer threatening legal action (loop in Legal)
- Notify accounting (Gloria) for most contract exceptions

______________________________________________________________________

## WHEN TO ESCALATE TO TECH SUPPORT

Escalate using the *Tech Escalation Follow-Up* workflow when:

- Issue cannot be reproduced or confirmed as a product bug
- Root cause requires backend investigation
- API-level issues (rate limits, enrichment behavior, Fivetran/Snowflake sync)
- Privacy / security concerns (support access logs, account takeover suspicion, DPA questions)
- Feature flag behavior questions requiring backend confirmation
- Integration issues (Salesforce email sync, Apollo ↔ Snowflake via Fivetran)

______________________________________________________________________

## WHEN TO ESCALATE TO SECURITY / FRAUD

- DDOS attacks or ToS violations → *Fraud Review BO* ticket in Intercom, or *Escalate to External Fraud* flow
- Suspected account takeover → Security team
- No refunds for ToS violations. No exceptions.
- Do NOT process any refund or reprieve for fraud cases — Security decides.

______________________________________________________________________

## ARR THRESHOLDS FOR CONTRACT EXCEPTIONS

| Exception type | ARR threshold |
|---|---|
| Tiered pricing / multi-year | $50K ARR+ |
| Rollover credits | $50K ARR+ |
| Early opt-out | $50K ARR+ (+ CRO approval) |
| Adding licenses on schedule | $15K ARR+ |
| Changing payment schedule mid-term | $15K ARR+ |
