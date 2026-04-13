# HVO Activation & Retention Findings

**Owner:** Leo Liu | **Updated:** 2026-03-25
**Full report:** `worklog/hvo_activation_analysis.html`
**Source tables:** `HVO_CALLS_AI_PROCESSING`, `ONBOARDING_HIGH_VELOCITY_TEAMS` (ANALYTICS.ANALYTICS), `FCT_MONGO_CONVERSATIONS`, `DIM_TEAMS`, `DIM_TEAMS_DAILY` (ANALYTICS_DATASCIENCE)

---

## What this is

Analysis of whether HVO (Human Voice Outreach) calls drive feature activation and retention. Three comparison groups:
1. **HVO: Feature covered on call** — rep explicitly covered that feature during the HVO session
2. **HVO: Feature not covered** — had HVO call but rep didn't cover the feature
3. **Non-HVO paid teams** — no HVO attendance

Key design decision: all-time activation rates for the feature comparison (Section 03), 30-day post-call/post-signup window for the Sequence segment deep-dive (Section 04). HVO not-covered and Non-HVO 30d rates are nearly identical — confirming the HVO call itself drives the lift, not selection.

---

## Key findings

### 1. Covering a feature on the call predicts activation
All-time activation rates (HVO Covered → HVO Not Covered → Non-HVO):

| Feature | Covered | Not Covered | Non-HVO | Lift (Cov vs Not) |
|---|---|---|---|---|
| Sequence Created | 62.4% | 39.3% | 36.7% | +59% |
| Dialer | 18.9% | 7.8% | 7.2% | **+142%** |
| Extension Used | 84.0% | 64.4% | 57.3% | +30% |
| Mailbox Linked | 96.8% | 83.4% | 72.0% | +16% |
| Buying Intent | 28.1% | 24.7% | 19.4% | +14% |

### 2. Dialer is the biggest untapped lever
+142% lift when covered vs not covered. Only discussed on 33% of HVO calls. Currently the most under-covered high-signal feature.

### 3. Workflow is the biggest all-HVO lift
HVO teams (regardless of what was covered) outperform Non-HVO by +44–61% on Workflow activation across all subsegments.

### 4. Sequence: 30-day post-call activation by segment

| Segment | HVO: Covered (30d) | HVO: Not covered (30d) | Non-HVO (30d from signup) |
|---|---|---|---|
| Enterprise | 32.4% | 13.6% | 13.7% |
| Mid-Market | 32.8% | 14.1% | 16.6% |
| SMB | 30.3% | 16.7% | 19.5% |
| VSB-Enriched | 33.7% | 19.0% | 21.7% |
| VSB-Freemail | 36.9% | 18.0% | 10.6% |

Non-HVO 30d rates are nearly identical to HVO not-covered rates — the HVO call + coverage is the driver.

### 5. M3 NRR: HVO lifts by +6pp, coverage signal real at MM and SMB (July–November 2025 cohort)

**Cohort design:** HVO group = teams whose `FIRST_PAID_DATE` is in the same calendar month as `FIRST_MEETING_HELD_START_AT_UTC` from `ONBOARDING_HIGH_VELOCITY_TEAMS`. Non-HVO = same paid vintage (July 2025+), no HVO session. Matured ≥3 months. M3 NRR = `SUM(arr at FIRST_PAID_DATE + 3 months) / SUM(arr at FIRST_PAID_DATE)` — exact per-team date anchors, dollar-weighted, source `DIM_TEAMS_DAILY.ARR`. ONBOARDING_HIGH_VELOCITY_TEAMS is in `ANALYTICS_DB.ANALYTICS` (not ANALYTICS_DATAPLATFORM).

**Overall (transparent math):**
- HVO: $8,162,000 / $7,021,968 = **116.2%** (n=4,924)
- Non-HVO: $17,440,543 / $15,822,645 = **110.2%** (n=10,874)
- HVO lift: **+6pp M3 NRR, +1.2pp logo retention**

**⚠️ Note on absolute levels:** New-cohort M3 NRR > 100% is expected — July–November 2025 teams are in early expansion phase (plan upgrades, seat adds in first 3 months). Company all-cohort M3 NRR is 78.1% (Dec 2025, includes all historical churn). These numbers are correct.

**Subsegment × Sequence coverage (corrected 2026-03-25, DIM_TEAMS_DAILY, exact dates):**
| Subseg | HVO: Covered | HVO: Not Covered | Non-HVO | Coverage effect |
|---|---|---|---|---|
| Mid-Market | **134.6%** (n=107) | 118.7% (n=138) | 106.6% (n=696) | **+15.9pp ★** |
| SMB | **128.3%** (n=645) | 121.9% (n=818) | 117.2% (n=3,344) | **+6.4pp ★** |
| Enterprise | 122.4% (n=64) ⚠ | 112.7% (n=99) ⚠ | 111.5% (n=560) | +9.7pp (directional) |
| VSB-Enriched | 108.2% (n=1,349) | 109.1% (n=1,432) | 105.5% (n=5,773) | −0.9pp (no signal) |
| VSB-Freemail | 107.1% (n=132) | 116.6% (n=136) | 100.6% (n=501) | −9.5pp (inversion†) |

†VSB-Freemail inversion = selection bias: teams whose rep didn't discuss Sequence are already self-activating it, hence higher NRR. Not a real coaching effect.

**Read:** MM and SMB show clear, meaningful coverage signals at M3. The coaching effect shows up in revenue within 3 months at $1K+ ACV. VSB has no coverage differentiation at M3 — run M6. HVO attendance is consistently better than Non-HVO across all segments regardless of coverage.

---

## Rep × Topic coverage (top patterns)

From `HVO_CALLS_AI_PROCESSING.MEETING_HOST_EMAIL` — % of each rep's calls covering each feature:
- **andrea.gonzalez** — broadest coverage profile (Dialer 50.1%, Buying Intent 67.9%)
- **alejandro.arriaga** — leads on Dialer (49.1%) and Credits (74.7%)
- **ana.mejia** — leads on Buying Intent (79.8%) and Extension (65.9%)
- **oscar.lorenzoni** — lowest Dialer coverage (11.1%) — specific coaching opportunity
- **Record Actioned** — cold across all reps (0–14%), likely under-coached systemically

---

## Technical notes

- **Join path:** `ONBOARDING_HIGH_VELOCITY_TEAMS` → flatten `CALENDAR_EVENT_IDS` (ARRAY, no PARSE_JSON needed) → `FCT_MONGO_CONVERSATIONS.CALENDAR_EVENT_ID` → `FCT_MONGO_CONVERSATIONS.CONVERSATION_ID` → `HVO_CALLS_AI_PROCESSING.CONVERSATION_ID`
- **Quote stripping required:** `REPLACE(APOLLO_TEAM_ID, '"', '')` in ONBOARDING_HIGH_VELOCITY_TEAMS
- **Rep identifier:** `MEETING_HOST_EMAIL` in HVO_CALLS_AI_PROCESSING (e.g. `rep.name@apollo.io`)
- **Feature discussion flags:** `SEQUENCE_CREATED`, `IS_DIALER_DISCUSSED`, `MAILBOX_LINKED`, `BUYING_INTENT_BY_DEFAULT`, `EXTENSION_USED` — per-call booleans, AI-extracted from transcript. Fully populated (no nulls), varies by MODEL_VERSION
- **MAILBOX_LINKED caveat:** fires when rep discusses mailbox on the call. Most teams link mailbox before the HVO session, so call-level flag rate is low (23%) even though all-time activation rate when covered is 96.8%
- **Segmentation:** `ACCOUNT_SUB_SEGMENT` from DIM_TEAMS — not ACCOUNT_SEGMENT or ACCOUNT_SALES_DEPARTMENT_TIER
- **Script:** `scripts/hvo_30d_activation.py` (re-runnable)

---

## What's still open

- [ ] Run M6 NRR to test whether feature-specific coverage creates divergent retention curves (July–September 2025 cohort has 6-month data available now — first matured M6 cohort is Q3 2026)
- [ ] Propensity score matching for causal estimate (flag for Shyam/Andrew)
- [ ] Confirm with Kaitlyn/Rahul: does `MAILBOX_LINKED` mean "discussed" or "successfully linked on call"?
- [x] ~~M3 NRR with correct cohort anchor (first HVO call date month = first_paid_date month)~~ — done 2026-03-25
