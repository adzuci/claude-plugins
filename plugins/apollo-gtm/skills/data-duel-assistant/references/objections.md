# Objection Handling Playbook

Common patterns from live data duels and how to handle them.

---

## "We only have name + company / address"

**Risk:** Test will show low match rate; customer will blame Apollo's coverage.

**Response:**
"To fairly judge any vendor's coverage, we need strong identifiers like company domains or LinkedIn
URLs. With just names and company strings, even the best vendors will struggle — this is a
fundamental limitation of how contact matching works, not specific to Apollo.

We have two options:
- A) Proceed with an explicit caveat: 'best effort on sparse identifiers.' We'll show you exactly
  which rows couldn't be matched and why, so you can see the true picture.
- B) Take a week to augment the list with domains or LinkedIn URLs, then run a fair test.

Which would you prefer?"

---

## "Can waterfall fix our match rate?"

**Risk:** Misaligned expectations; customer will be disappointed when match rate doesn't move.

**Response:**
"Waterfall's job is to find more emails and phones for people we can already identify. It doesn't
change whether we can figure out who a record actually is — that depends on the identifiers in
your file.

So what you'll see is:
- Match rate: same with or without waterfall
- Email and phone fill rate: higher with waterfall

This is actually a good thing for you — it means waterfall is additive on top of a solid match,
not a workaround for a weak one."

---

## "Your match rate is lower than ZoomInfo / Lusha"

**Response (if identifier gap is confirmed):**
"Before comparing those numbers, let's look at the identifier breakdown. [X]% of your rows had
no domain and no LinkedIn URL. For those rows, no vendor — including ZoomInfo — can reliably match.
When we look at rows with strong identifiers, our match rate is [Y]%. That's the apples-to-apples
comparison.

What's showing as a 'lower match rate' is actually a reflection of the input file's identifier
health, not our data coverage."

**Response (if true coverage gap):**
"You're right — for this segment [describe it specifically], we have a genuine coverage gap. I
want to be straight with you about that. Where Apollo is particularly strong is [describe]. For
your core ICP of [describe], the match rate is [X]% and the email fill rate is [Y]%."

---

## "Your validator disagrees with ours" (e.g., Trustlist/Lumrid vs Apollo "verified")

**Response:**
"Different validators use different heuristics and recency windows — it's not unusual to see
disagreements. The most reliable arbiter of email quality is actual campaign performance: bounce
rates and reply rates in a real sequence.

If you're open to it, we'd suggest a side-by-side pilot: run a sequence with Apollo emails and
one with your current data on a matched set of records, and compare actual bounce and engage rates.
That gives you real signal, not just conflicting validators."

---

## "We want an enormous pre-sale test — 10,000+ rows"

**Response:**
"We want to give you a thorough test. A 10,000-row waterfall run would consume well over a million
credits and take significant time to execute — for both sides. A well-designed 1,000-row sample
gives you 95% of the signal at under 10% of the cost and effort.

If we win on a representative 1,000-row sample that matches your real ICP, that's a much stronger
signal than a noisy 10,000-row run with mixed identifier quality. And if you sign, we can do the
full run post-signature as part of onboarding.

Can we agree on a representative 1,000-row sample?"

---

## "Your tech filters look thinner than SalesIntel / ZoomInfo"

**Response:**
"Their filter list is wider for certain technology categories — I won't pretend otherwise.

But let's zoom out to what you're actually trying to do with those filters. You want to reach
[describe their targeting need]. Let's build that filter set together in Apollo and see how the
actual contact counts and data quality compare. A long list of technology checkboxes doesn't
matter if the underlying contact data doesn't hold up.

And Apollo's advantage is the unified workflow — data, sequences, and automation in one place. The
metric that matters is pipeline generated per dollar, not checkbox count."

---

## "We're not sure if this sample is representative"

**Response:**
"That's exactly the right question to ask. Let's sanity-check it together:
- Does this sample include the regions you care most about? [check]
- Does it reflect the seniority levels you're targeting? [check]
- Is it from your actual CRM / pipeline, or a curated list? [check]

If we find gaps, we can adjust the sample now — it's much better to align on this before we run
than to argue about it after."

---

## "We don't have a domain column — just company names"

**Response:**
"Company name alone is one of the weakest matching signals we have — it's ambiguous (many
companies share similar names) and prone to inconsistencies (abbreviations, legal names vs.
trade names, etc.).

The single highest-ROI thing you can do before this test is add company domains. Even getting
domains on 50–60% of rows will significantly improve match rate. Want me to run through the file
and find the domains I can resolve automatically? We can tackle the rest together."

---

## Proactive Competitor Framing (Before the Customer Raises It)

Use these before the scorecard call to get ahead of the likely comparison.

---

### When the incumbent is ZoomInfo

**Open with this framing:**
"Before we look at the numbers together — you're used to ZoomInfo's interface and you've built
workflows around it. What I'd like you to focus on is two things: how the match rate compares
on your actual ICP file, and the difference in phone coverage — specifically direct dials and
mobiles. That's where we see the most meaningful difference for SDR teams. The third thing I'd
point to is what Apollo gives you alongside the data: sequences, AI-assisted outreach, and intent
signals all in one platform. That bundled value is hard to see in a pure data comparison."

**Known ZoomInfo weaknesses to proactively surface:**
- SMB/Mid-Market mobile phone coverage — Apollo typically outperforms here
- Data freshness on company changes (job changes, promotions) — Apollo re-verifies more frequently
- Cost structure: ZoomInfo contracts are often bundled with add-ons the customer doesn't fully use
- Platform fragmentation: ZoomInfo + Outreach/Salesloft + intent tool vs. Apollo as a unified platform

---

### When the incumbent is Lusha

**Open with this framing:**
"Lusha is a strong point solution for individual reps. What we're testing here is whether Apollo
gives your team the same or better data quality at a level that works for a coordinated GTM motion —
not just one rep prospecting. The areas where Apollo tends to have more depth are: EMEA coverage
outside of UK/DACH, broader TAM at the account level, and the ability to run a full outreach
workflow without switching tools."

**Known Lusha weaknesses to proactively surface:**
- TAM coverage outside Western Europe is thinner
- Limited workflow automation (Lusha is data-only; no sequencing)
- Team-level features (sequence coordination, intent) require additional tools
- If EMEA-heavy ICP: ask for an EMEA-heavy sample where Lusha is structurally weaker

---

### When the incumbent is SalesIntel

**Open with this framing:**
"SalesIntel's pitch is research-verified contacts and strong APAC coverage. What we want to
validate is whether that verification quality holds up on your specific ICP. Apollo's advantage
is the combination of data breadth and platform — you're not just getting a data provider,
you're getting a full GTM execution layer. Let's look at the match rate and email quality
on this sample, and then I'll show you the filter depth in Apollo's TAM builder."

**Known SalesIntel weaknesses to proactively surface:**
- US SMB coverage is thinner vs. Apollo
- Platform capabilities are limited (largely a data provider, not a full GTM tool)
- Intent data is narrower; Apollo's intent signal is broader and more integrated
- Filter granularity in TAM discovery is more limited than Apollo's filter set

---

### When the incumbent is Cognism

**Open with this framing:**
"Cognism is strong in EMEA — especially UK and DACH — and their GDPR compliance story is solid.
If your ICP is heavily EMEA-weighted, that's a legitimate strength and we won't pretend otherwise.
What we want to show you is: for your US coverage, Apollo has comparable or stronger depth, and
Apollo gives you a full platform — sequences, AI outreach, intent — that Cognism doesn't. For
most teams with a mixed US/EMEA motion, Apollo is stronger as the primary platform even if
Cognism might win on pure EMEA-only coverage."

**Known Cognism weaknesses to proactively surface:**
- US coverage is materially thinner — if ICP has significant US presence, this matters
- Platform is data-only; no sequences, no intent, no automation
- Pricing model is often seat-based with export limits
- Mobile verification methodology is different from Apollo's — worth validating in the test

---

### When it's an internal CRM / no incumbent

**Open with this framing:**
"You're not replacing a vendor — you're deciding whether to add Apollo to augment your existing
data. So the question isn't 'does Apollo beat ZoomInfo?' — it's 'how much incremental coverage
and reach does Apollo give you on the contacts you already have?' Let's look at what % of your
CRM records Apollo can enrich further, and then I'll show you where Apollo finds new contacts
that aren't in your CRM at all."

**Focus for CRM comparison duels:**
- Net-new coverage: contacts in the ICP that aren't in the customer's CRM at all
- Enrichment uplift: missing fields (email, phone, title) on existing records
- Freshness: how many of their existing records have stale data that Apollo can refresh

