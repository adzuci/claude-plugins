# Salesforce Logging Reference — Data Duel Fields

Log on the **Opportunity** record after every completed duel.

## Required Fields

| Field Label | Field API Name | Type | Valid Values / Notes |
|-------------|---------------|------|---------------------|
| Data Test Conducted | `Data_Test_Conducted__c` | Checkbox | Yes / No |
| Test Type | `Data_Test_Type__c` | Picklist | Contact Enrichment, Account Enrichment, TAM Contact Discovery, TAM Account Discovery, Data Accuracy Check |
| Test Date | `Data_Test_Date__c` | Date | YYYY-MM-DD |
| Sample Size | `Data_Test_Sample_Size__c` | Number | Integer row count |
| Main Competitor(s) | `Data_Test_Competitors__c` | Multi-select picklist | ZoomInfo, Lusha, SalesIntel, Clearbit, Cognism, Other |
| Match Rate Apollo | `Data_Test_Match_Rate__c` | Percent | Apollo-only match rate |
| Email Fill Rate | `Data_Test_Email_Fill__c` | Percent | Overall (not just matched rows) |
| Phone Fill Rate | `Data_Test_Phone_Fill__c` | Percent | Overall |
| Waterfall Run | `Data_Test_Waterfall__c` | Checkbox | Yes / No |
| Waterfall Email Uplift | `Data_Test_Waterfall_Email_Delta__c` | Percent | Delta vs Apollo-only; leave blank if waterfall not run |
| Identifier Health Score | `Data_Test_ID_Health__c` | Percent | % rows with ≥1 strong identifier |
| Primary Failure Reason | `Data_Test_Failure_Reason__c` | Picklist | Identifier Gap, True Coverage Gap, Input Noise, Mixed, N/A — Matched Well |
| Test Outcome | `Data_Test_Outcome__c` | Picklist | Won, Lost, Ongoing, No Decision |
| Notes | `Data_Test_Notes__c` | Long text | Key context: segment-specific findings, ICP alignment, follow-up actions, any anomalies |

## Navigation

1. Open the Opportunity: `https://apolloio.lightning.force.com/lightning/o/Opportunity/list`
2. Search for the account/opportunity by name
3. Open the record → Edit → find the Data Test section
4. Fill all required fields
5. Save and confirm to the rep

## Why This Matters

Over time, this structured logging will let the team answer:
- Which test designs win deals vs. which don't?
- Which competitors do we beat most reliably and in which segments?
- Where are our true coverage gaps (vs. identifier gap misattributions)?
- Which AEs/SCs run the most effective duels?

Do not use free-text Notes as a substitute for structured picklist fields — that data can't be
aggregated or reported on.
