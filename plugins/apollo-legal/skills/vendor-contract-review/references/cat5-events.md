# Category 5 — Event Contracts

Use this playbook when the contract is for a physical event: venues, hotels, catering, AV,
team dinners, offsites, conferences, sponsorships, or team activities.

**Redline posture: Minimal.** Event contracts are largely standardized and exist for a
purpose — the venue or vendor needs to protect its space, and Apollo needs to attend an event.
Standard event terms, including one-sided indemnification in favor of the venue, nonrefundable
deposits, and attrition clauses, are normal market practice. Do not over-flag.

The goal is to catch the genuine hard stops quickly, generate an operator comment for hotel
contracts, and get out of the way.

---

## Calibration Notes — Read Before Applying the Matrix

**Standard one-sided indemnification is GREEN.** Apollo indemnifying the venue for claims
arising from Apollo's own use of the space is completely normal for physical events. Do not
flag it.

**Nonrefundable deposits are GREEN.** This is standard market practice for event venues,
hotels, and dinners. Silence on whether the deposit is refundable if the venue cancels is also
GREEN — don't flag it.

**Attrition is a business decision, not a legal one — never redline it.** Whatever the
threshold, note it in the operator comment so the requester knows what they're committing to.
Only escalate (flag in summary) if the threshold is above 90% or the penalty is uncapped.

**Missing liability caps under $50k are GREEN.** For event contracts under $50,000, the
contract value itself limits the financial exposure. A missing liability cap at this size is
not a problem.

**The vendor's own insurance requirements are irrelevant.** Only flag what the contract
requires Apollo to carry — never flag what the vendor carries.

---

## Clause Review Matrix

### Indemnification
- **Desired**: Mutual indemnification — each party covers claims arising from its own acts,
  omissions, or negligence.
- **Acceptable**: One-sided indemnification where Apollo indemnifies the venue for claims
  arising from Apollo's own use of the space. This is standard market practice for physical
  events — GREEN.
- **Will NOT Accept**: Apollo indemnifies the venue for the venue's own negligence or
  misconduct. One-sided indemnification with no carveout for the venue's own fault is a hard
  stop.

### Liability Cap
- **Desired**: Mutual cap at the total contract value.
- **Acceptable**: No explicit liability cap on contracts under $50,000 — deal size limits
  exposure. Any reasonable cap between $10k–$50k is acceptable.
- **Will NOT Accept**: Uncapped or unlimited Apollo liability on a contract over $50,000.

### IP and Content Ownership
- **Desired**: Apollo retains ownership of all content it creates at or for the event: photos,
  recordings, presentations, creative materials. Vendor retains rights to their own
  independently created materials.
- **Acceptable**: Vendor gets a non-commercial, internal-documentation license to event
  content — acceptable if it doesn't constitute an ownership claim.
- **Will NOT Accept**: Vendor claims ownership of, or a broad commercial license to, content
  created by or featuring Apollo at the event (photos, videos, brand assets, presentations).
  Hard stop.

### Insurance Requirements (Apollo's Obligations Only)
Only evaluate what the contract requires Apollo to carry. The vendor's own insurance is
irrelevant — do not flag it.
- **Acceptable**: No insurance obligation on Apollo, or a standard COI requirement at
  commercially normal limits (general liability coverage standard for events of this type).
  Requiring Apollo to add the venue as an additional insured under event-specific general
  liability is also standard and GREEN.
- **Will NOT Accept**: Contract imposes onerous insurance obligations on Apollo — requiring
  specialized coverage not standard for event attendance, limits grossly disproportionate to
  the contract value, or naming the vendor as an additional insured on Apollo's primary
  corporate policies.

### Attrition Clause (Hotel Room Blocks Only)
Attrition is a **business decision, not a legal one**. Do NOT redline it. Instead, always
note the threshold in the operator comment so the requester understands what they're
committing to. The right place for this is the operator comment, not a markup.

- **80% or below**: Standard market practice — note in operator comment, no summary flag.
- **81–90%**: Above standard — note the specific percentage prominently in the operator
  comment. No redline, no summary flag.
- **Above 90%**: Escalate — flag in the summary AND note in the operator comment. This is
  above market and worth the requester pushing back before signing. Still no redline; it's a
  business negotiation.
- **Uncapped penalty structure**: RED — the legal problem is unlimited financial exposure
  regardless of how many rooms go unfilled.

### Nonrefundable Deposit
Nonrefundable deposits are standard market practice. Do not flag them.
- **Acceptable**: Nonrefundable deposit on customer cancellation. Silence on venue-initiated
  cancellation. Both are GREEN.
- **Note**: There is no "will not accept" threshold for event deposits — this is a business
  decision, not a legal one.

### Personal Data — Attendee Information
Some event contracts require Apollo to provide attendee data (names, dietary restrictions,
health information, contact details) to the venue for logistics purposes. This is not
automatically a concern, but warrants attention if significant personal data is involved.
- **Acceptable**: Vendor needs basic logistics information (names for registration, meal
  preferences) and there are no data retention or secondary use concerns.
- **Flag as YELLOW**: Contract requires Apollo to provide sensitive personal data
  (health/medical information, government IDs) and there are no data protection
  acknowledgments. Or vendor retains attendee data for its own marketing purposes. Or vendor
  shares attendee data with third parties without restriction.
- **Note**: Do not redline simple attendee name/dietary collection — flag as YELLOW only when
  the scope of data or the vendor's use of it is genuinely concerning.

### Cancellation Fees
Cancellation fee schedules are standard event contract terms. Do not flag standard tiered
cancellation schedules.
- **Acceptable**: Tiered cancellation schedule with defined deadlines and amounts.
- **Flag as YELLOW only if**: Cancellation fees are grossly disproportionate to the event
  value (e.g., 100% non-refundable regardless of when cancellation occurs, even months in
  advance). Rare — most schedules are reasonable.

---

## GREEN / YELLOW / RED Assessment Rules

### 🔴 RED — Any one of these fires:
- Vendor claims ownership of or a broad commercial license to event content (photos, videos,
  presentations, Apollo brand assets)
- Apollo indemnifies the vendor for the vendor's own negligence or misconduct
- Contract requires Apollo to carry insurance that is grossly onerous or disproportionate
- Personal data access: vendor will access/process Apollo system data or Apollo customer
  records (this is the universal personal data trigger — not attendee logistics)
- Attrition penalty structure is uncapped/unlimited regardless of rooms unfilled

### 🟡 YELLOW — No RED, but one or more of:
- Insurance requirement on Apollo beyond standard commercial general liability (flag the
  specific obligation — type and limits)
- Contract requires Apollo to provide significant personal data about attendees without any
  data protection acknowledgment, or vendor retains attendee data for its own purposes
- Contract value over $50,000 (standard review threshold applies to liability exposure)
- Attrition above 90% (flag in summary and operator comment — no redline)
- Cancellation fees that are grossly disproportionate to the event value

### 🟢 GREEN — All of the following are true:
- No IP ownership claims over Apollo event content
- Indemnification is either mutual OR standard one-sided venue indemnification (both are fine)
- No onerous insurance obligations on Apollo
- No significant personal data concerns with attendee data handling
- Contract value under $50,000 OR liability structure is reasonable at any value
- Attrition penalty is capped (threshold alone doesn't determine GREEN — only uncapped
  penalties or thresholds above 90% escalate)

---

## Operator Comment — Hotel and Venue Contracts

After the triage report, if the contract involves a hotel (room block, F&B minimum, meeting
space) or a venue with meaningful financial commitments, generate a plain-language heads-up
comment for the requester.

### When to generate
- Hotel group sales agreements (room blocks, F&B minimums, meeting room rentals)
- Venue contracts with attrition, deposit, or cancellation obligations the requester needs
  to understand before signing

Do NOT generate for: simple restaurant reservations, one-time activity bookings, conference
sponsorships with no room or F&B commitments.

### What to include
Scan for each of the following and include anything present. Skip items not in the contract —
don't invent them.

- **Taxes and fees excluded from quoted rates**: List every tax, fee, or mandatory charge not
  built into the quoted rate. If a resort fee is waived, call that out as good news.
- **Early departure fee**: Any charge for checking out before the reserved checkout date.
- **Attrition / room retention**: Always include this for hotel room block contracts. State
  the retention percentage, note whether it's above or below the standard 80%, and explain
  what it means in plain terms (e.g., "you need to fill 27 of your 27 rooms or pay for the
  difference"). This is a business decision — give the requester the info they need to decide
  whether to push back before signing.
- **F&B minimum**: The dollar commitment for food and beverage.
- **Meeting space rental**: Any room rental charges — rate and total.
- **Small group surcharges**: Per-event fees triggered by low attendance.
- **Cancellation fee schedule**: Each tier with date range and dollar amount or percentage.
- **Notable concessions**: Anything the hotel/venue is giving Apollo (waived fees, upgrades,
  discounts).
- **AV / vendor rules**: Restrictions on outside AV vendors, required in-house AV use, or
  advance notification requirements.

### Tone and format

Write it in a direct, conversational tone — no legal jargon. Vary the opening
line using phrases like "As always here's my list of heads ups:", "Just a handful of things
I always point out:", or "As I normally do, here are my callouts:". Use a numbered list. End
with a short sign-off inviting approval (e.g., "If that all works for you, just let me know
and I'll approve!" or "Let me know if you're good with these terms and I'll move it forward.").

Append the operator comment directly below the triage report, separated by a horizontal rule,
under the header **Operator Comment**.

---

## Hilton Standard Additional Terms — Known Acceptable

Hilton group hotel agreements incorporate additional terms by reference at a URL like
`hilton.com/en/p/hilton-distributions/express-usa-agreement-terms-and-conditions/`. These
terms are standard Hilton boilerplate (last revised April 1, 2024) and are **acceptable
as-is** under Apollo's Cat 5 playbook. If this URL appears in a Hilton contract, note in
the review that these terms were reviewed and are acceptable — do not flag the linked URL
as an incomplete review caveat.

Key provisions in Hilton's standard additional T&C:

**Indemnification**: Apollo assumes responsibility only for damage caused by Apollo, its
employees, guests, or contractors — there is an explicit carveout excluding damage not
caused by Apollo. Not responsible for guest room damage unless Apollo guaranteed that room's
payment. GREEN.

**Data handling**: Each party is an independent Data Controller under GDPR. Hilton handles
guest data per its Global Privacy Statement. Apollo must obtain attendee consent before
requesting Hilton to share reservation data with Apollo's team. Standard and acceptable —
GREEN.

**Governing law and disputes**: Governed by the laws of the state where the Hotel is located.
Informal resolution first (30 days), then litigation in Hotel's city/state. Jury trial
waived. Prevailing party gets attorney's fees (mutual). Standard for hotel contracts — GREEN.

**IP / Promotional**: Hotel can review materials referencing the Hotel's name or Hilton logos
— this protects the Hotel's brand only. No claim over Apollo's event content — GREEN.

**Outside contractors**: Apollo must notify Hotel 30 days in advance and contractors may need
to sign a hold harmless. Standard operational requirement — GREEN.

**Cancellation for cause**: Hotel can cancel without liability if deposits aren't paid on
time. Standard remedy — GREEN.