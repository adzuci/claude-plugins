# Billing Scenarios — Reference

> Source of truth: Apollo Escalation Matrix spreadsheet + Billing Policy docs
> Last updated: June 2026
> Owner: Jocel / Billing team

______________________________________________________________________

## ⚠️ BEFORE YOU PROCESS ANYTHING

Run through these three checks before acting on any billing request. If any check fails or is unclear, pause and escalate rather than proceeding.

> **Note:** The steps below are based on observed patterns from the support channel. Where marked with 💡, these are recommendations — confirm the exact procedure with your team lead or Jocel if you're unsure.

______________________________________________________________________

### CHECK 1 — Verify customer identity

Required whenever the request involves a refund, cancellation, account access change, or is coming from someone other than the primary account holder.

**💡 Recommended verification fields** (confirm with your team which are required for your ticket type):

- Email address on the account
- Admin name
- Last 4 digits of the card on file
- Card type (Visa, Mastercard, etc.)
- Card expiry date
- Date of last invoice / charge amount

**If the customer is contacting from a different Apollo account** (seen frequently in the channel): treat this as higher-risk. Require at least 3 matching fields before proceeding.

**If verification fails or is incomplete:** do not process the request. Let the customer know you need to verify their identity first. If they cannot verify, escalate to your team lead.

> 💡 Check with your team lead whether there is a formal verification SOP or Intercom macro you should be using for this — the above is a pattern observed from the channel, not a confirmed company-wide standard.

______________________________________________________________________

### CHECK 2 — Check prior refund / exception history

Every scenario in this document assumes "first-time exception." Before approving anything, confirm no prior exception exists.

**💡 Recommended places to check** (confirm with your team lead which are authoritative):

1. **Activity Log in Teams** — look for pinned notes from previous reps referencing exceptions, refunds, or "no more refunds" flags
1. **Intercom conversation history** — search for prior tickets on the same account
1. **The relevant tracking sheet** (e.g., Accidental Upgrades from Trials log in Notion) — some scenarios require logging there; check if the account already appears

**What counts as a prior exception:** any note in the Activity Log indicating a refund was given, a cancellation was processed as an exception, or an explicit "no further exceptions" flag was set.

**If you find a prior exception:** do not approve another one under standard rules. Escalate to Jocel if there's a compelling reason (legal/churn/bad press risk).

> 💡 The exact set of systems to check may vary by scenario — confirm with your team lead if you're unsure which log is authoritative for a given case.

______________________________________________________________________

### CHECK 3 — Confirm you haven't hit your monthly refund limit

PAs and Billing Advocates have monthly refund limits. Attempting to process a refund when you've hit your limit will fail.

**💡 Recommended:** Before processing any cash refund, check whether you're near or at your monthly limit. If you're blocked mid-process, reach out to Billing for assistance rather than leaving the ticket in a partial state.

Per the refund limits table below:

- Billing Advocates: max **$1,200 per transaction** (monthly limit applies separately — confirm the current limit with Jocel or Billing)
- If you've hit your limit: post in `#ama-support-billing` and ask Billing to process on your behalf

> 💡 The exact monthly cap amount is not documented here — confirm the current limit with Jocel or your team lead. This check is a recommendation based on channel observations where reps discovered limits mid-processing.

______________________________________________________________________

## WHO HANDLES WHAT

| Scenario | First Contact | PA can handle? |
|---|---|---|
| Accidental seat upgrade (≤10 days, 0–10% usage) | PA / Billing Advocates | ✅ Yes |
| Accidental credit upsell reversal (≤10 days) | Billing Advocates | ✅ Yes, first time only |
| Auto-renewal refund (≤10 days, \<$1,200, \<10% M2M / \<5% annual) | PA / Billing Advocates | ✅ Yes |
| Unused account refund (\<$300/mo, 0% usage last 90 days) | Billing Advocates | ✅ Yes (last 3 invoices) |
| Voiding open invoice (first time, ≤10%/5% usage, ≤$1,200) | Billing Advocates | ✅ Yes |
| Temporary/courtesy credits (≤1,000 email / ≤100 mobile / ≤6,000 unified) | Billing Advocates | ✅ Yes |
| Refund > $1,200 or > 3 months | Jocel | ❌ Escalate |
| Accidental annual plan upgrade | Billing Advocates | First-time exception only |
| Downgrades during term | Not allowed (standard) | ❌ Escalate if exception needed |
| Invoices older than 6 months | Not allowed (standard) | ❌ Escalate |
| Contracts (tiered pricing, multi-year, rollover) | Legal | ❌ Escalate |
| Early terminations / opt-out clauses | Legal / Billing | ❌ Escalate |

______________________________________________________________________

## REFUND LIMITS

| Type | Billing Advocates max | Jocel max | Escalate to Billing if over |
|---|---|---|---|
| Cash | $1,200 | $2,400 | > $2,400 |
| Unified credits | 15,000 | No known limit | If error/limit hit |
| Email credits | 10,000 | 20,000 | > 20,000 |
| Mobile credits | 100 | 200 | > 200 |
| Export credits | 1,000 | 2,000 | > 2,000 |

**Hard rule:** Cannot refund more than 3 months in the past, even with zero usage.

______________________________________________________________________

## SCENARIO PLAYBOOKS

### Accidental seat upgrade

- **≤10 days + seat only + 0–10% usage** → PA reverses and refunds. Confirm first-time.
- **>10 days OR credit upsell** → Senior leadership approval required.
- Escalation: `#ama-support-billing` → *PA Billing Refund Exception Request*. Approver: Jocel.

### Accidental annual upgrade (self-serve)

- First time + 0–5% usage + contacted ≤7 days → cancel and full refund.
- After 7 days, 0–5% usage → partial refund at most.
- Prior exception given → decline. Only override for legal/churn/bad press risk.

### Auto-renewed plan — customer wants retroactive cancellation

- ≤10 days + monthly cost \<$1,200 + usage \<10% (M2M) or \<5% (annual) → PA approves.
- Check Activity Log for prior notes before processing.
- Customer claims they already cancelled: search all platforms. If not found + no usage → unused account workflow. If usage → no refund without senior leadership.

### Unused self-serve account refund

- \<$300/mo + 0% usage last 90 days → cancel and refund last 3 invoices.
- > $300/mo → senior leadership approval.
- Maximum: 6 months (only if customer pushes back hard against 3-month limit).
- Use the Usage tab in Teams to verify 90-day usage.

### Voiding an open invoice

All conditions must be met for PA to void:

1. First time (check logs)
1. ≤10% usage (M2M) or ≤5% usage (annual)
1. Invoice ≤$1,200
1. **Never void an invoice for an account on a contract.**

If account is already deactivated, same rules still apply.

### AI credits consumed unexpectedly (Qualify Contact / Qualify Account / Waterfall)

- Valid basis for courtesy credit, not cash refund (standard).
- First time + \<40,000 AI credits → PA can approve 100% credit refund.
- Over 40,000 → get approval before granting 100%.
- Always walk customer through disabling the feature before closing.
- Customer insists on cash → route to Billing for review.

### Temporary/courtesy credits

- ≤1,000 email / ≤100 mobile / ≤6,000 unified → PA grants, first time only.
- 1,001–25,000 email / 101–2,000 mobile / 6,001–10,000 unified → escalate to Billing.
- > 25,000 email / >2,000 mobile / >10,000 unified → senior leadership also required.
- AI fields specifically: up to 40,000 unified, 100% refund OK if first time. Over 40k → get approval.
- Temp credits expire end of current billing period — cannot be extended beyond that.

### Customer threatening chargeback / dispute

- Do not approve or deny based on threat alone. Route to Billing for review.
- Small amount (\<$300) + all standard conditions met → use judgment.

### Admin no longer with the company

- Verify identity. If ≤10 days + usage \<10% (M2M) or \<5% (annual) → PA can proceed.
- Otherwise escalate to Billing. Approver: Jocel.

### Account with promo auto-renews at regular pricing

- Minimal usage + within first 2 weeks of renewal → cancel and refund.
- Startup discount extension (2nd year): first-time exception OK without escalation. 3rd year: auto-denied.
- 80% cancellation/retention promo already fully used → no reinstatement. Can offer \<$20 off current rate.
- Promo disrupted 1–3 months in: can request reapplication if first time. No exceptions if it happened more than twice.

### Payment sent (ACH) not reflected

- Valid bank transfer proof (not Bill.com, not a check) + no Activity Log note against reprieve → PA can proceed.
- Credit card M2M customers: no reprieves.
- No reprieve button available → cannot help; money must actually hit the account.

### Voiding invoices >6 months old

- Standard: not allowed.
- Exception: legal threat, churn risk, or leadership escalation.
- Process through Kenny (no longer Ray). DM Kenny if approved.

### Refund for seat count / active user mismatch

1. Verify: seats billed vs. seats active; timing of downgrade; any documented downgrade request; discount structure.
1. Review credit usage — if usage aligns with fewer seats, consider partial refund.
1. Full refund only for clear system error or billing misconfiguration.
1. Always: correct seat count going forward, adjust discounts, do not stack refund + credit adjustment.

### Accidental credit purchase during downgrade / promo flow

1. Verify: timing of downgrade attempt vs. credit purchase; whether cancellation promo is active; refund amount; prior refund history.
1. If credits unused + low amount + no abuse pattern + high operational effort to fix → issue refund directly and preserve existing promo.
1. No refund if: credits used, significant amount, repeated pattern, or clear downgrade path was available.
1. Always: set to Pending Downgrade if appropriate; document rationale; preserve active promotions.
