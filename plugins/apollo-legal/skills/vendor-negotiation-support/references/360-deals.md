# 360 (Two-Way) Deals

_A reference the vendor-negotiation-support skill loads on demand, not a standalone policy
doc — confirm live deal facts in Apollo's systems and loop in Procurement and Legal before
acting on anything here._

Use this when Apollo is buying from a vendor that is also an Apollo customer or prospect. A 360
deal is the strongest leverage in vendor negotiation and the easiest to blow up. Play it as a
partnership, never as a trade.

## Detection

Check for the two-way signal before writing the first counter:

| Signal | Where to look | What it tells you |
| --- | --- | --- |
| Apollo sales activity on the vendor | Apollo CRM: account, open opportunities, stage, close date, AE owner | The vendor is a customer or live prospect — this is a 360 deal |
| Vendor-named Slack channels | `#<vendor>`, `#ext-<vendor>*`, `#ext-*-<vendor>`, `#tmp-<vendor>-negotiation`, `#ZC:*:<Vendor>` | Who owns the relationship, what has already been asked, whether Legal is mid-thread |
| GTM chatter | Glean or Slack for `<vendor>` plus `deal`, `renewal`, `POC`, `contract` | A deal closing on the same clock as yours |
| Shared exec or investor ties | Apollo people data | A warm path to someone who can move both sides |

Confirm it before you frame anything around it. A rumored deal is not leverage — find the CRM
record or the channel, or call it unverified.

What changes once it is confirmed:

- Their economics are net, not gross. What they spend with Apollo offsets what Apollo spends
  with them.
- Both sides now have a deadline and something to lose from delay. Price arguments become speed
  arguments, which are far easier to win.
- The relationship outranks the line item. Do not trade it for a few points.
- Handled badly, it creates optics problems for both companies. Procurement and sales are
  formally separate for good reason.

## The Reciprocity Math

Run the net flow before deciding how hard to push. Count only contracted revenue — weighted
pipeline is a forecast, not money the vendor has committed:

```text
Apollo outflow      = Apollo annual commit to the vendor
Vendor inflow       = vendor's contracted annual spend with Apollo (signed only)
Net flow to vendor  = Apollo outflow - vendor inflow
Concession ask      = vendor proposal - Apollo counter

Only when Apollo outflow > 0:  effective net rate = net flow / Apollo outflow
Only when net flow > 0:        ask as % of net    = concession ask / net flow
```

Track weighted pipeline separately as upside, never as an offset. If net flow is zero or
negative — they buy as much from Apollo as Apollo buys from them — skip the percentages
entirely, state the position in dollars, and let the account team lead the relationship.

Example (illustrative):

```text
Apollo pays vendor       $400K/yr
Vendor pays Apollo       $150K/yr contracted (+$60K weighted pipeline, upside only)
Net flow to vendor       $250K/yr
Apollo counter $340K/yr  ->  concession ask $60K = 15% of gross, 24% of net
```

How to use it:

- Net flow sets your patience and tone. It is not a scoreboard — "you only net $250K from us"
  lands as a threat.
- Do say, warmly, that the relationship runs both ways and both teams win when both deals land.
  That frame does the work; the arithmetic stays in your notes.
- Growing vendor spend with Apollo means the relationship is worth more to them than the
  concession you are asking for. Hold that quietly.
- Never condition Apollo's revenue on Apollo's spend, or the reverse.

## Partnership Framing, Never Quid Pro Quo

The whole play in one line: **ask for help and speed, not a trade.**

| Say this | Not this |
| --- | --- |
| "We're both trying to close something this quarter — can we help each other land both this week?" | "We'll sign yours when you sign ours." |
| "You're a customer as well as a supplier, so I want this to be easy on both sides." | "Our renewal depends on how your team handles our deal." |
| "Can you help me unblock the process on your side? Our legal calendars are open." | "Give us the discount and I'll get your paper signed." |

The distinction is not cosmetic. Signature-for-signature conditioning creates real exposure on
both sides: procurement and sales run separately, and reciprocal dealing can trigger
revenue-recognition scrutiny and compliance review at the vendor and at Apollo. A deal that
looks like a round trip gets pulled apart by someone's controller, and both sides slip.

Speed and goodwill are yours to give. Conditional signatures are not.

## Working a Dual Decision Maker

One person who can influence both deals is the highest-leverage 30 minutes available. Sequence
the call:

1. **Open with the relationship.** Mutual customer, both teams trying to get something done. No
   asks in the first two minutes.
1. **Spend the first ask on process.** Parallel legal tracks, a named owner per document, dates.
   Cheap for them, worth weeks to you.
1. **Make one clean commercial ask.** One number, one structure, said once. Five asks invite
   five counters and read as nickel-and-diming a partner.
1. **Keep a trade menu so every give buys something.**
1. **Close with owners and dates** on both deals, and recap it in writing the same day.

Trade menu, cheapest first:

| Give | Cost to Apollo | Ask it buys |
| --- | --- | --- |
| Same-day turnaround / fast signature | None | Rate movement, process unblocking |
| Reference call or case study | Low; needs Marketing sign-off | Discount, protective terms |
| Co-marketing or joint logo use | Low-moderate; needs Marketing sign-off | Discount, renewal cap |
| Payment timing (annual up front) | Cash timing | Real rate movement |
| Longer term | Flexibility — term judgment lives in `multiyear-strategy.md` | Deepest discount plus price hold |

Never promise publicity or logo rights on a call. Say "I can probably get that approved" and
route it.

## Timing Leverage

Both sides are on a clock: their quarter-end booking against Apollo's renewal or notice date.

- **A vendor deadline binds the vendor too.** If their AE needs the booking this month, the
  urgency is shared.
- **Buy speed with it, not a worse rate.** The ask is "let's both close this week," backed by
  same-day turnaround on your side.
- **Do not let their quarter set yours.** If Apollo's review is incomplete, ask for a deadline
  extension. A rushed signature costs more than a missed discount.
- **Watch the reverse pressure.** A vendor who knows Apollo wants their deal to close may
  slow-walk yours. If that starts, drop the reciprocity frame and negotiate the purchase on its
  own merits.
- Keep exact dates on the record: their booking date, Apollo's renewal and notice dates, and the
  approval lead time you need.

## Guardrails

- **No signature contingency in writing, ever.** Assume both companies' counsel read every
  message later.
- **Both deals stay in their own approval paths.** The purchase runs through Zip and IronClad
  exactly as it otherwise would; the sale runs through Apollo's normal sales process.
- **Verbal concessions land in the order form or they do not exist.** Not a follow-up email —
  the paper, before signature.
- **Loop in Procurement and Legal before the reciprocity conversation**, not after. They are the
  ones who defend the optics.
- **Write down who agreed to what, and when.** Two-way deals attract retroactive
  interpretation.
- Align internally first. The account team and the buying team must not negotiate against each
  other.
- If the vendor introduces explicit conditioning, do not match it. Redirect to the partnership
  frame in writing and tell Procurement and Legal.

## Escalation Ladder

One rung at a time — each rung spends relationship capital:

1. **AE stalled** — restate the ask, set a date, name what unblocks it.
1. **Sales manager or deal desk** — ask the AE to bring in rate authority.
1. **Exec warm intro** — Apollo leadership to their VP of Sales or Contracts & Renewals. Spend
   it on process plus one clean commercial ask.
1. **Joint legal call** — 30 minutes, both counsel live, parallel document tracks agreed on the
   call.
1. **Formal deadline extension** — last resort, and better than a rushed signature. Route
   through Procurement and Legal.

## Quick Reference

```text
DETECT:     Apollo CRM account/opportunity + vendor Slack channels
            (#<vendor>, #ext-*, #ZC:*:<Vendor>). Confirm before framing anything on it.
MATH:       Net flow = Apollo commit - vendor's contracted spend with Apollo.
            Pipeline is upside, never an offset. Sets your patience; never recited.
FRAME:      "Help both deals land this week." Never "you sign, we sign."
DUAL DM:    Relationship -> process ask -> ONE commercial ask -> trade menu ->
            owners, dates, same-day recap.
TIMING:     Their deadline binds them too. Buy speed with it, not a worse rate.
GUARDRAIL:  No signature contingency in writing. Both deals keep their own
            approval paths (Zip/IronClad). Verbal -> order form before signature.
ESCALATE:   AE -> sales manager -> exec intro -> joint legal call -> deadline
            extension. Never a rushed signature.
```
