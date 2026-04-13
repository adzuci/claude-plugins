# Churn Taxonomy — Proposed Framework

**Purpose:** Standardized categorization of why teams churn. Used to answer "Why are teams churning?" and drive product prioritization.

**Audience:** Jarvis, product team, analytics, VoC
**Date:** 2026-03-30 (DRAFT — awaiting product/VoC finalization)
**Owner:** Bridie Meredith (structure), Product/VoC (definition refinement)
**Status:** Proposed only; not yet live in Snowflake (Gap 5)

---

## Proposed Taxonomy (7 Categories)

Organized by causality: what drove the churn decision.

### 1. **Low Engagement / Not Using Enough**

**Definition:** Team did not achieve regular usage; failed to form habit.

**Indicators:**
- <10 active days in final month
- <50 emails sent lifetime
- <2 Record Actions total

**VoC signals:** "We weren't using it enough," "Our team moved on to other priorities," "We didn't see the value."

**What we know (FY26 data):**
- ~36% of churned teams cite low engagement (largest category)
- Of those, 19% say "wasn't sure how to get value"
- Often accompanied by: <$100/mo MRR, <3 seat purchases

**Product responsibility:** Activation (F14D), onboarding, value messaging, customer education

**Mitigation:** Improve F14D activation rate (17% target); earlier value delivery; success playbooks for VSB/SMB

---

### 2. **Role / Job Change**

**Definition:** Decision-maker or budget owner left company or changed roles; new owner didn't prioritize renewal.

**Indicators:**
- Primary admin account deactivated before churn
- Company headcount change signal
- GTME turnover

**VoC signals:** "My responsibilities changed," "The person who bought this left," "New leadership didn't approve renewal."

**What we know:**
- ~18% of churned teams involve role changes
- Often non-recoverable (exogenous to product)
- Higher in VSB (small teams; single point of failure)

**Product responsibility:** NONE — exogenous factor

**Mitigation:** Multi-seat adoption (reduce single-user dependency); executive relationships (sales motion)

---

### 3. **Product Gap / Feature Not Available**

**Definition:** Team needed feature that Apollo doesn't have; gap prevented value realization.

**Indicators:**
- Specific feature mentioned in cancellation survey
- Support tickets referencing missing capability
- Competitive loss to product with feature

**VoC signals:** "We need [X feature]," "Competitor had [X] which we needed," "This doesn't integrate with our CRM the way we need."

**Examples (from recent churn):**
- "Need mobile app for field reps"
- "CRM sync didn't work reliably"
- "Enrichment coverage for our vertical is low"

**Product responsibility:** Product roadmap, quality, integrations

**Mitigation:** Roadmap prioritization; CRM data quality; vertical-specific enrichment

---

### 4. **Complexity / Too Hard to Use**

**Definition:** Product complexity or usability issues prevented team from getting started.

**Indicators:**
- Churned <30 days (failed onboarding)
- Multiple support tickets during trial
- <1 Record Action (not even attempting)

**VoC signals:** "Too complicated," "The onboarding didn't help," "We needed more training," "Interface is confusing."

**What we know:**
- ~12% of churned teams cite complexity
- Correlated with: <10 person teams (fewer technical resources), freemail domains (lower sophistication)
- Often recoverable with better UX or support

**Product responsibility:** Onboarding, UI/UX, support/education

**Mitigation:** Improve FUX (onboarding redesign, Q2); better self-serve docs; support quality

---

### 5. **Competitive Loss**

**Definition:** Team switched to competitor; Apollo lost deal or renewal.

**Indicators:**
- Competitive mention in CRM opportunity (lost deal)
- Specific competitor named in cancellation survey
- Account marked "competitive loss" by AE

**VoC signals:** "We switched to [Competitor X]," "Competitor had better [feature]," "Better pricing."

**Common competitors:** HubSpot, Outreach, Lemlist (email); Apollo Dialer competitors; ZoomInfo (enrichment)

**What we know:**
- ~8-10% of churned teams (most identified via Gong/CRM, not surveys)
- Higher in Mid-Market (competitors have better enterprise features)
- Often involves price + product combination

**Product responsibility:** Product competitiveness, pricing, GTM positioning

**Mitigation:** Product parity (feature speed), competitive pricing, sales/CS awareness

---

### 6. **Cost / Budget Constraint**

**Definition:** Team or company made budget cuts; product was deemed non-essential.

**Indicators:**
- Mention of "budget cuts," "economic pressure"
- Cancellation during known recession/layoff period
- Downgrades prior to churn (signal of cost pressure)

**VoC signals:** "Budget freeze," "Cost-cutting initiative," "Can't justify the spend right now."

**What we know:**
- ~8-10% of churned teams (growing during economic downturns)
- Largely exogenous to product quality
- Often recoverable in future if customer situation improves

**Product responsibility:** NONE — macro factor; maybe pricing efficiency

**Mitigation:** Lower-cost tier; seat-based vs. fixed pricing; CPM efficiency

---

### 7. **Other / Miscellaneous**

**Definition:** Churn reasons not fitting above categories.

**Indicators:**
- No reason given in survey
- Reason doesn't map to taxonomy
- Support-only churn (no VoC signal)

**Examples:**
- "Company shut down"
- "Switching to internal tool"
- "Unclear" (no response)

**What we know:**
- ~10-15% of churned teams
- By definition, heterogeneous; hard to address systematically

**Mitigation:** Better survey design to reduce "other" category

---

## Mapping to Data & Measurement

**Primary source:** `CANCELLATION_SURVEYS` in RAW_MONGO (unstructured survey responses)

**Secondary sources:**
- `FCT_ZENDESK_CHURN_TICKETS` (support-identified reasons)
- CRM opportunity loss reasons (Sales-Ops)
- Gong competitive transcripts (Sales engagement)

**Live version (Goal):**
```
DIM_CHURN_REASONS:
  - team_id, churn_date, primary_reason, secondary_reason, confidence_score
  - Rows synced daily from cleaned CANCELLATION_SURVEYS
  - Joined to FCT_DAILY_REVENUE churn events
```

**View (Goal):**
```sql
V_CHURN_REASONS_BY_SEGMENT:
  SELECT segment, churn_reason, COUNT(*) as churn_count,
         ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY segment), 1) as pct
  FROM joined_tables
  GROUP BY segment, churn_reason
```

---

## How Jarvis Uses This

When exec asks: "Why are teams churning?"

**Jarvis response (once live):**
> "Churn breakdown by reason (last 30 days):
> - Low engagement: 38% ($2.1M ARR)
> - Role change: 16% ($900k ARR) — not product-fixable
> - Product gap: 12% ($680k ARR) — feedback: missing feature [X]
> - Complexity: 9% ($500k ARR)
> - Competitive: 8% ($450k ARR)
> - Cost: 10% ($560k ARR)
> - Other: 7% ($400k ARR)
>
> **By segment:** VSB churn is 40% low-engagement (activation issue); MM+Ent is 25% competitive + 18% product gap (feature richness). Different playbooks per segment."

**Current (before live):**
> "Churn reasons aren't yet in Snowflake, but from Voice of Customer we know: 36% of low-usage churn is role/responsibility changes, 19% report 'wasn't sure how to get value.' The team is building a churn taxonomy and will have Snowflake queries live by mid-April. Until then, using VoC data with a caveat that this is unstructured and may have bias toward survey respondents."

---

## Known Limitations (Draft Status)

1. **Survey response bias:** Teams that respond may differ from silent churners
2. **Single vs. multiple reasons:** Some churns have multiple contributing factors; taxonomy treats as primary only
3. **Timing:** Reason collected at cancellation; actual causal factor may have been months earlier
4. **Coverage:** ~30% of churned teams respond to survey (rest are "other")
5. **Granularity:** Proposed categories may be too broad or too narrow once we see data

---

## Next Steps (Implementation)

1. **Product/VoC review** (This week): Validate category definitions; refine wording
2. **Classification scheme** (Week 2): Define rules for mapping survey text → category
3. **Manual calibration** (Week 2-3): Tag 200-500 historical surveys; measure inter-rater agreement
4. **DE sync** (Week 3): Request Mongo mirror of CANCELLATION_SURVEYS
5. **Build & validate** (Week 4): Create DIM_CHURN_REASONS; validate against manual tags
6. **Deploy** (End of April): Live in Snowflake; Jarvis queries enabled

---

## See Also

- `pending_definitions.md` — Gap 5 (Churn taxonomy)
- `business_state.md` — Current churn status + risks
- `theory_of_change.md` — Retention lever discussion
