# Department Profiles — Jarvis Intelligence Network

**Owner:** Bridie Meredith | **Updated:** 2026-05-27
**Sources:** FY27 AOP docs, Glean People directory, Snowflake QUERY_HISTORY, alignment analysis

______________________________________________________________________

## Executive Office

- **Leader:** Matt Curl, CEO
- **AOP priorities:** (1) NRR improvement 71% to 100%, (2) AI-native transformation, (3) Financial discipline (Rule of 40)
- **Key metrics:** Total ARR $278M, NRR, revenue per employee $300K, credit consumption 2B+
- **Analytics partner(s):** Leo Liu (direct report)
- **Data sources:** All revenue tables, board-level aggregations
- **Measurement gaps:** Revenue per employee requires headcount data (Darwinbox integration incomplete)
- **Current risk level:** N/A — sets the strategy
- **Squads/teams:** Chief of Staff (Annie Bernhardt), BizOps (Russell Sims), BizSys (Patrick Sullivan)

______________________________________________________________________

## Sales / Revenue

- **Leader:** Adam Carr, CRO (with Max Angell as VP Sales)
- **AOP priorities:** (1) Rep-driven new ARR $41M (+79% YoY), (2) MM+ENT new logos 680 (+39%), (3) ACV improvement $9K to $11K
- **Key metrics:** Rep-driven ARR (new + upsell), ACV by segment, S1 to S2 CVR, PG$ (pipeline generated), CSQL win rate
- **Analytics partner(s):** Will Masket (Business Analytics, revenue-facing). Howie Chan (Sales Ops Senior Manager — co-owns Booked ARR section with Max Angell).
- **Data sources:** `DIM_SALESFORCE_OPPORTUNITIES`, `FCT_MONTHLY_REVENUE` (ARR_REP), `DIM_SALESFORCE_ACCOUNTS` (segment), `DIM_SALESFORCE_APOLLO_TEAMS`
- **Measurement gaps:** PQL/PQA scoring table missing, competitive win rate tracking unclear, sales coverage model not formalized
- **Current risk level:** MEDIUM — pipeline data well-covered but analytics partner stretched
- **Squads/teams:** SMB Sales (Dana Hensler), MM Sales (Garris Yeung), Customer Advocates (Paula Urrutia), Sales Development (Heather Hansen), Solutions Consultants (Alexis Rodriguez)
- **RBR #81 additions:** John Henwood (co-owns Managed/Rep Driven Renewed Org ARR with Tina Zhang), Howie Chan (co-owns Booked ARR with Max Angell)

______________________________________________________________________

## GTME (Go-To-Market Engineering)

- **Leader:** Eric Quanstrom, VP GTME
- **AOP priorities:** (1) Scale coverage to all Custom/Org customers (~$46M ARR, ~5K customers), (2) GRR improvement 61.2% to >70% = +$7.3M incremental GRR, (3) Expansion ARR $12.5M via CSQLs
- **Key metrics:** L1: NRR, GRR, Expansion ARR (CSQLs). L2: Credit consumption, intervention-centric productivity. L3: Emails/calls/meetings, forecast coverage, certification completion.
- **Analytics partner(s):** Will Masket (nominal but not delivering). Leo personally investigating GTME effectiveness. Shyam + Kaitlyn building signal pipeline.
- **Data sources:** `FCT_MONTHLY_REVENUE` (GRR/NRR), `AGG_TEAM_CREDITS` (credit consumption), `GTME_CALLS_AI_ANALYSIS`, `WEEKLY_TEAM_SIGNALS`, SFDC opportunities
- **Measurement gaps:** GTME metrics dashboard (Q2 deadline) has ZERO build progress. Credit tracking unreliable. No health scoring. No intervention-to-ARR attribution pipeline.
- **Current risk level:** HIGH — Q2 dashboard deadline approaching with zero progress
- **Squads/teams:** Named (MM) pods 2:1, Managed (SMB) pods 3:1, Scaled (pooled). Managers: Alison McDonough (Managed), Stephanie Ervin (Sr Mgr GTME)
- **RBR #81 additions:** Michelle Chang (Post Sales Renewals, co-owner with Eric Quanstrom — interventions + retention), Carrigan Santos (GTME, runs interventions on accounts)

______________________________________________________________________

## Customer Onboarding & Engagement

- **Leader:** James Boone, Senior Director
- **AOP priorities:** (1) HVO (High Velocity Onboarding) effectiveness, (2) F0-14 activation for paying customers, (3) Signal-based team interventions
- **Key metrics:** F14D Habit RA Rate (12% to 17%), onboarding session completion, activation milestones, weekly team signals
- **Analytics partner(s):** Adhiraj (activation — aligned), Kaitlyn (signals + HVO). Good coverage.
- **Data sources:** `ONBOARDING_HIGH_VELOCITY_SESSIONS`, `WEEKLY_TEAM_SIGNALS`, `DIM_USER_ACTIVATION`, `HVO_CALLS_CALL_CATEGORY_BACKFILL`, `DIM_SALESFORCE_OPPORTUNITIES`
- **Measurement gaps:** Activation definition ("4 Record Actions in 14 days") not in Snowflake as a flag. Computed in Hex/Amplitude only.
- **Current risk level:** MEDIUM — good analytics coverage but activation flag missing from Snowflake
- **Squads/teams:** HVO team (Sacbe Ibarra), HTO team (Shardul Navare), Digital Success. John Choi listed as Onboarding co-owner.
- **Note (May 2026):** HVO/HTO are now two distinct tracks under James Boone — Sacbe Ibarra owns HVO, Shardul Navare owns HTO. HVO restructuring in progress as of May 2026.

______________________________________________________________________

## Customer Care / Support

- **Leader:** Kenny Keesee, VP Support
- **AOP priorities:** (1) Voice + screenshare as default channel (CSAT 90%), (2) Save motion covering 90% of cancellation/downgrade tickets, (3) AI deflection 80% for free/self-serve
- **Key metrics:** CSAT (paid), FCR (90%), AI Repeat Contact Rate (\<10%), Escalation Rate (\<10%), AHT (~20 min), live interactions/day (~18), blended cost per ticket, AI resolution rate (80%)
- **Analytics partner(s):** Marie (support analytics — departed May 2026, successor: Cat Zhou), Tighe (support coverage). Leo personally invested.
- **Data sources:** `DIM_SUPPORT_CONVERSATIONS`, `INT_INTERCOM_CALL_TRANSCRIPTS`, `FCT_CANCELLATION_SURVEY_RESULTS`. CSAT/FCR/AHT live in Intercom, NOT Snowflake.
- **Measurement gaps:** Intercom data pipeline gaps — CSAT, topics/subtopics mostly null. AI deflection metrics not being built. NRR impact from save motions needs attribution.
- **Current risk level:** MEDIUM — solid analyst coverage but key metrics trapped in Intercom
- **Squads/teams:** Workforce (Stef Dey), Customer Experience LATAM (Sebastian Velandia, Santiago Taborda), Customer Experience US (Jackson Gibson), Customer Experience PH (April Kay Caviente)
- **Note (RBR #81):** Three-headed operational ownership: Jackson Gibson + Kenny Keesee + Joe Shen. Joe Shen is technically RevOps but operationally aligned to Support as co-owner.

______________________________________________________________________

## Revenue Operations

- **Leader:** Henry Mizel, VP Revenue Ops
- **AOP priorities:** (1) Revenue data accuracy, (2) SFDC infrastructure and segmentation, (3) Deal desk efficiency
- **Key metrics:** Data accuracy in revenue reporting, SFDC hygiene metrics, GTM systems reliability
- **Analytics partner(s):** Martin (SFDC opps), Will Masket (SFDC segmentation). Clark Sun is the operational RBR owner — scope broader than documented: co-owns SMB Rep-Funnel AND Customer Advocate sections in RBR.
- **Data sources:** All SFDC tables, `FCT_MONTHLY_REVENUE`, Stripe tables, `DIM_SALESFORCE_ACCOUNTS`
- **Measurement gaps:** Sales motion attribution has open alignment gaps (see `domain/sales_motion_definitions.md`). Two incompatible segment systems (account_segment vs market_segment_tier).
- **Current risk level:** MEDIUM — core data exists but definition alignment needed
- **Squads/teams:** Sales Ops (Howie Chan), GTM Systems (Andrew Lai), Support Ops (Joe Shen), Customer Ops (John Choi), GTM Strategy & Ops (Matthew Moore), Deal Desk (Anna Petrini)
- **RBR #81 additions:** Paul Bates (RBR Performance Summary owner — ARR forecasting + churn modeling), Givi Gigineishvili (RBR Performance Summary + LTV/ROI, forecasting), Brandon Aguirre (RBR Performance Summary)

______________________________________________________________________

## GTM Enablement

- **Leader:** Brittany Sarsfield, Director Head of GTM Enablement
- **AOP priorities:** (1) Rep enablement and training, (2) Onboarding new hires, (3) Competitive intelligence
- **Key metrics:** Rep ramp time, certification completion, enablement content engagement
- **Analytics partner(s):** NONE
- **Data sources:** Unknown — likely LMS/training systems
- **Measurement gaps:** No analytics coverage
- **Current risk level:** LOW — not a high-analytics-dependency function
- **Squads/teams:** Reports under Adam Carr (CRO)

______________________________________________________________________

## Partnerships

- **Leader:** Jennifer Rhima, Director
- **AOP priorities:** (1) $7.2M partner-sourced + partner-influenced ARR, (2) International expansion (Brazil, Germany), (3) Scale API Reseller program
- **Key metrics:** Partner-sourced ARR, partner-influenced ARR, SQL volume per partner, API Reseller deal consistency
- **Analytics partner(s):** NONE dedicated. Martin has run some PartnerStack queries (only analytics touch). CRITICAL gap.
- **Data sources:** PartnerStack (external), SFDC opportunities (partner-tagged). Minimal Snowflake footprint.
- **Measurement gaps:** Zero dedicated analytics. No partner attribution pipeline. No dashboard. $7.2M target growing to $30M FY28 with no measurement infrastructure.
- **Current risk level:** CRITICAL — most under-measured department at Apollo
- **Squads/teams:** Solution Partners (Vince Heaton), Technology Partners + API Resellers (Jessica Casler), Strategic Partnerships (Jennifer Rhima)

______________________________________________________________________

## Growth & Acquisition

- **Leader:** Dan Cronyn, VP Growth & Acquisition
- **AOP priorities:** (1) W2 FTP 4.0% to 4.5%, (2) PLSM pipeline creation (signal-based), (3) Golden population expansion (1-2 seat to 3+ seat teams)
- **Key metrics:** Core Registrations, W2 FTP rate, Stage 1 Opps (PLSM), PQL/PQA volume, ARPU/ARPA, credit/seat utilization, NMN >1.0
- **Analytics partner(s):** Adhiraj (activation — partial), Anvitha (inbound — aligned). NOBODY covers Lifecycle (Ben Frutos), Conversion, or Pricing & Packaging (Karthik).
- **Data sources:** `DIM_TEAMS` + conversion logic (FTP), `FCT_MONTHLY_REVENUE` (ARPU/ARPA), `FCT_TEAM_CREDITS_DAILY` (credit utilization), SFDC (Stage 1 Opps)
- **Measurement gaps:** FTP cohort definitions not standardized. PQL/PQA dashboards have zero development evidence. F0-14 activation system has no dedicated analyst. ARPA + expansion component analysis not built.
- **Current risk level:** HIGH — committed AOP deliverables to Growth are not being built
- **Squads/teams:** Paid Acquisition (Kenny Lee / Cam Thompson), AEO/SEO (Cam Thompson, Kelechi Ibe — SEO/AEO owner), Lifecycle (Ben Frutos, Jesse Fernandez — PLSM Q2+ Gap Plan Analysis), Conversion/Growth Product (Matt Woods, Sourabh Ahuja, Nancy Shao, Nick Gallinelli — CRO: marketing site CVR, demo CVR, AI SDR), Pricing & Packaging (Karthik Mahadevan)
- **RBR #81 additions:** Alex Beckham (Self-Serve NSMs and LTV/ROI Update, works with Dan Cronyn), Kelechi Ibe (SEO/AEO owner), Nick Gallinelli (CRO — conversion rate optimization), Jesse Fernandez (Lifecycle/Growth — PLSM Q2+ Gap Plan Analysis, works with Ben Frutos)
- **Note (RBR #81):** Rep Demand Gen is a cross-functional section: Kenny Lee + Ben Frutos + Cam Thompson co-own, spanning Demand Gen + Lifecycle + Paid Acquisition.

______________________________________________________________________

## Marketing

- **Leader:** Marcio Arnecke, CMO
- **AOP priorities:** (1) Brand clarity and market narrative, (2) Demand generation and pipeline creation, (3) Product marketing for multi-solution strategy
- **Key metrics:** MQL volume, Stage 1 Opps from marketing, brand awareness, content effectiveness, competitive win rate
- **Analytics partner(s):** NONE for core marketing (PMM, brand, comms). Growth & Acquisition sub-functions have partial coverage.
- **Data sources:** HubSpot form submissions, marketing attribution (unclear tooling), campaign data
- **Measurement gaps:** Marketing attribution end-to-end, content ROI, brand measurement
- **Current risk level:** MEDIUM — Growth covered partially, core marketing under-measured
- **Squads/teams:** Growth & Acquisition (Dan Cronyn), Demand Generation (Kenny Lee), Marketing Intelligence & Ops (Stephen Baker), Brand (Sarah Tran), Communications (Brooke Ferencsik), Product Marketing (Shari Diamond, Alexa Grabell, Andy McCotter-Bicknell, Xi-Er Dang, Leif Parcell, Cindy Chao, Michelle Pulver)

______________________________________________________________________

## Product

- **Leader:** Bela Stepanova, CPO
- **AOP priorities:** (1) COKR1 Win the Account/MM ($75M expansion + $25M displacement), (2) COKR2 Multi-Solution ($85M combined), (3) COKR3 Onboarding to Agentic (2hr to 15min), (4) COKR4 AI Native ($70M AI credits)
- **Key metrics:** Use cases per Paid WAT (1.18 to 1.33), F14D activation, AI WAT, W4 AI retention, inbound ARR, deals/CI ARR, AI credit consumption
- **Analytics partner(s):** Sai (AI data layer — COKR4), Kirk (DS team — experimentation), Adhiraj/Anvitha (COKR3 onboarding). Gaps: COKR1 and COKR2 Deals/CI have ZERO analytics support.
- **Data sources:** `DIM_ACTIVE_TEAMS_DAILY` (DS, quality suspect), Amplitude events, `DIM_MONGO_ASSISTANT_THREADS`, `AGG_TEAM_CREDITS`
- **Measurement gaps:** COKR1 ($100M) has no analyst. Deals/CI ($20M) has no analytics coverage. Multi-product usage not in trusted table. AI measurement framework incomplete.
- **Current risk level:** HIGH — two largest COKRs have zero analytics support
- **Squads/teams:** AI Product (Tyler Phillips), Product & Research (Anthony Medina), Product Management (Matt Lincoln), Product Design (Gene Lee), Pocus & Sheets (Isaac Pohl-Zaretsky), Product Data (Jon Jenkins)

______________________________________________________________________

## Engineering

- **Leader:** Dzmitry Markovich, SVP Engineering
- **AOP priorities:** (1) Product delivery velocity, (2) Platform reliability and instrumentation, (3) AI-native product development
- **Key metrics:** Ship velocity, incident rates, SLA compliance, engineering efficiency
- **Analytics partner(s):** No dedicated partner. Kirk queries engineering-adjacent tables.
- **Data sources:** `DIM_ENGINEERING_JIRA_ISSUES_AND_SLAS`, `APOLLO_INCIDENT_DATA`, Jira
- **Measurement gaps:** Engineering metrics largely owned by Engineering itself. Analytics provides infrastructure support but not analysis.
- **Current risk level:** LOW (from analytics perspective)
- **Squads/teams:** Too many to enumerate. Key leaders: Ray Li (CTO), Himanshu Gahlot (VP Eng — 134 reports), Aidan Li (Sr Dir — 70 reports), Ralph Pyne (CISO — 12 reports), Timmy Ho (Sr Mgr — 33 reports). 273 total reports.

______________________________________________________________________

## R&D (Product + Engineering combined view)

- **Leader:** Bela Stepanova (Product) + Dzmitry Markovich (Engineering)
- **AOP priorities:** (1) COKR1 Win the Account ($100M), (2) COKR2 Multi-Solution ($85M), (3) COKR3 Onboarding to Agentic, (4) COKR4 AI Native ($70M)
- **Key metrics:** Combined product + engineering metrics per COKR
- **Analytics partner(s):** See Product and Engineering sections
- **Data sources:** All product usage tables, engineering metrics tables
- **Measurement gaps:** Instrumentation standards for AI features before launch (not after). Usage to credits to outcomes linkage per AI feature. COKR3 measurement (% paid on >1 automation) has no single table.
- **Current risk level:** HIGH — $100M+ in targets with incomplete analytics
- **Squads/teams:** See Product and Engineering

______________________________________________________________________

## Analytics / Data

- **Leader:** Leo Liu, Senior Manager Product Analytics
- **AOP priorities:** (1) NRR Intelligence Engine, (2) AI Measurement Framework, (3) Unified Product + GTM Intelligence, (4) Analytics as a Platform (200 WAU), (5) Reliability + Instrumentation (95%+ SLA)
- **Key metrics:** Analytics Asset WAU (151 to 200), SLA compliance, Time-to-Insight reduction, NRR-impacting deliverables
- **Analytics partner(s):** This IS the analytics team.
- **Data sources:** All tables in ANALYTICS_DB
- **Measurement gaps:** Priority 5 (Reliability) under-invested. Priority 3 (Unified Intelligence) is thin. DIM_TEAMS_DAILY_V2 spine bug blocks downstream.
- **Current risk level:** MEDIUM — Priorities 1-2 well-covered, 3-5 thin
- **Squads/teams:** Analytics Engineering (Bridie, Tara, Kaitlyn, Martin, KT, Tighe), Data Science (Kirk, Shyam, Andrew, Pubudu, Anvitha, Mounica, Marie, Adhiraj), System Data Engineering, Data Platform Engineering (Sai, Deepak/Rahul)

______________________________________________________________________

## Finance & Strategy

- **Leader:** Julie Bi, VP Finance & Strategy
- **AOP priorities:** (1) Financial planning and ARR forecasting, (2) Unit economics and Rule of 40, (3) Revenue attribution accuracy
- **Key metrics:** ARR forecast accuracy, margin analysis, LTV:CAC, headcount ROI
- **Analytics partner(s):** NONE dedicated. Depends on Leo/RevOps for revenue data.
- **Data sources:** `FCT_MONTHLY_REVENUE`, Stripe tables, external financial systems
- **Measurement gaps:** Revenue infrastructure (billing/monetization) needs improvement for ARR-by-product attribution. Owned by Finance/Engineering.
- **Current risk level:** LOW (from analytics perspective — Finance has own tools)
- **Squads/teams:** Accounting (Gloria Gori), Finance & Strategy (Ford Whitticar, Matt Martin), Tax & Treasury (Ryan Hansen)

______________________________________________________________________

## People

- **Leader:** Rachel Noble, SVP People
- **AOP priorities:** (1) Employee engagement 80%, (2) Regrettable attrition \<8%, (3) Cost of hire $9K, (4) Overall attrition \<25%
- **Key metrics:** Engagement score, attrition rates, cost of hire, people team cost as % of ARR (3.2%)
- **Analytics partner(s):** NONE. Leo queries Darwinbox ad hoc.
- **Data sources:** Darwinbox (HR system), `LU_DARWINBOX_POSITIONS` in Snowflake
- **Measurement gaps:** Headcount/attrition analytics not formalized. People analytics is ad hoc.
- **Current risk level:** LOW (from analytics perspective)
- **Squads/teams:** Talent Acquisition (Brad Williams), Talent Management (Josh Blackburn), People Ops & Total Rewards (Cheri Martin), Communications & Culture (Mary Moreno), Sales Hiring (Sabrina Silva)

______________________________________________________________________

## Legal & Compliance

- **Leader:** Alexa Summer, General Counsel
- **AOP priorities:** (1) Legal risk management, (2) AI/product compliance, (3) Commercial legal operations
- **Key metrics:** Contract throughput, compliance posture, legal risk metrics
- **Analytics partner(s):** NONE — not needed for regular analytics work. KT may be working on Ironclad (contract management) data.
- **Data sources:** Ironclad (contract management), external legal systems
- **Measurement gaps:** N/A
- **Current risk level:** N/A
- **Squads/teams:** Product & Marketing Legal (Emily Whitney), Commercial Legal (Jen Dumas), Corporate (Alli Henry), Litigation & Compliance (Samantha Strauss), Legal Ops (Dani Rice)

______________________________________________________________________

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-05-27 | RBR #81 (May 26) updates: added Paul Bates, Givi Gigineishvili, Brandon Aguirre (RevOps); Alex Beckham, Kelechi Ibe, Nick Gallinelli, Jesse Fernandez (Growth); John Henwood, Howie Chan RBR role (Sales); Michelle Chang, Carrigan Santos (GTME); Sabrina Silva (People); HVO/HTO split + John Choi (Onboarding); Support 3-headed ownership; Clark Sun broader scope; Rep Demand Gen cross-functional note | Leo (via Jarvis) |
| 2026-03-24 | Created from AOP docs, Glean People directory, alignment analysis | Bridie (via Jarvis) |
