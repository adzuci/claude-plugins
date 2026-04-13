# INT_MONGO_APOLLO_CUSTOMER_DATA_CUSTOM_FIELD_CONTACTS

**Schema:** `ANALYTICS_DB.ANALYTICS`
**Grain:** One row per Apollo contact (customer prospect record)
**Refresh:** Daily
**Owner:** Analytics Engineering
**Trust Level:** High — intermediate table built from raw Mongo, used in production pipelines

## Description

Contact-level bridge table that links Apollo contacts (prospects in customer accounts) to the Apollo team that owns them. Primary use: resolving `contact_id` references in conversation/call transcripts back to an `apollo_team_id`.

## Key Columns

| Column | Type | Notes |
|--------|------|-------|
| `CONTACT_ID` | TEXT | PK — Apollo contact ObjectId |
| `APOLLO_TEAM_ID` | TEXT | The customer team that owns this contact |
| `APOLLO_USER_ID` | TEXT | The user who owns this contact |
| `ACCOUNT_ID` | TEXT | Linked account ObjectId |
| `IS_PRIMARY_CONTACT` | BOOLEAN | Primary contact for the account |
| `IS_USER_ENABLED` | BOOLEAN | Whether the owning user is active |
| `HAS_CRM_LINKED` | BOOLEAN | CRM integration active |
| `HAS_MAILBOX_LINKED` | BOOLEAN | Mailbox connected |

## Common Uses

- Join `FCT_MONGO_CONVERSATIONS` participant flatten → this table → `APOLLO_TEAM_ID` to attribute call/meeting records to a customer team
- Used in `account_lookup.py` HVO call attribution

## Gotchas

- ~26M rows — always filter on `CONTACT_ID` or join with a specific team; avoid full scans
- `APOLLO_TEAM_ID` is the customer team, not an Apollo internal team
