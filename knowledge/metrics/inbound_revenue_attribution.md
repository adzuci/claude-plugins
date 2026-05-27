# Inbound Revenue Attribution

> **Owner:** Marketing Analytics
> **OKR Target:** $4M of $10M
> **Status:** BLOCKED — needs AE answers below

## What this metric measures

Revenue attributed to inbound marketing channels.

## What we already have

- `FCT_TEAM_REVENUE_DAILY` — daily ARR per team
- `LU_TEAM_ATTRIBUTES` — team metadata including `tof_sales_bucket`, UTM fields
- Stub SQL with the skeleton logic

## What we need from you

Fill in each section below. Plain language is fine — Claude will convert to SQL.

### 1. What counts as "inbound"?

Which channels or values define inbound?

- Which `tof_sales_bucket` values? (e.g., 'Inbound', 'Marketing Qualified'?)
- Are there UTM source/medium values that should be included?
- Include partner/referral channels or strictly marketing-sourced?

```
YOUR ANSWER:

```

### 2. Attribution model

How should revenue be attributed?

- First-touch? Last-touch? Multi-touch? Time-decay?
- Attributed at the opportunity level or account level?
- If multi-touch, how is credit split?

```
YOUR ANSWER:

```

### 3. Revenue definition

What revenue number are we attributing?

- Closed-won ARR? First-year ACV? Total contract value?
- Only new business or include expansion?
- Any minimum deal size or segment filter?

```
YOUR ANSWER:

```

### 4. Time grain and reporting

How should this be reported?

- Monthly totals? Cumulative toward the $4M target?
- Attribution date = opportunity close date? Or marketing touch date?
- Breakdowns by channel, campaign, or region?

```
YOUR ANSWER:

```

### 5. Anything else

Anything we're missing or getting wrong?

```
YOUR ANSWER:

```
