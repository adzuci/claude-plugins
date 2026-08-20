# Statistical Tells

Generated data carries the shape of the loop that produced it. These checks
find that shape. They are probabilistic — a single weak signal proves nothing,
several together are decisive.

## Cross-column ordinal correlation

**The strongest check available, and the cheapest.**

Take two identifier columns that claim to come from different systems. Extract
the trailing digits of each. If they agree on most rows, the file was generated
by a loop:

```text
APOLLO_TEAM_ID              SFDC_ACCOUNT_ID
66ttx...0000027             001TTX000000027
66ttx...0000024             001TTX000000024
66ttx...0000003             001TTX000000003
```

Two independent systems have never coordinated a counter. In genuine joined
data these values are unrelated. Here they are the same number in two costumes,
which is what `for i in range(n)` looks like from the outside.

```bash
python3 scripts/check_id_formats.py sample.csv --correlate COL_A COL_B
```

The script reports the ratio of agreeing rows. Above 0.9 is conclusive; a
handful of coincidental matches across a large file is not.

## Uniform category distributions

Real categorical data is lumpy. Customers cluster by segment, contacts cluster
by source, stages cluster by where deals actually stall.

Seven CRM stages at 14.3% each, or five sources at 20% each, describes
`random.choice` over a list. Compute the distribution of every low-cardinality
column and look for suspicious evenness.

## Timestamp granularity clustering

Look at the distribution of timestamps modulo useful units:

- All values landing exactly on midnight, or on the hour
- Dates uniformly spread across an interval with no weekday or seasonal shape
- A "snapshot" timestamp identical across every row when the data would
  naturally have per-record update times

Real activity data has weekends in it.

## Sequential identifiers

Where the source system emits non-sequential identifiers, sequence is a tell.
Mongo ObjectIds embed a timestamp and a random component; they only look
sequential when generated within the same second by the same process. Salesforce
ids are not ordinal at all.

## Value pool size

Count distinct values in name, city, and street columns. A file of two million
contacts drawing first names from a pool of forty, or addresses from a dozen
city templates, is generated. Real data has a long tail.

## Internal consistency against a summary

If the sample arrives with a summary document — a claimed record count, a
breakdown by country, an impact assessment — **recompute every figure from the
data itself.**

A summary and its dataset can disagree, and the summary is the one people
quote. This is not merely a data-quality nicety: a jurisdiction breakdown that
omits countries actually present in the file will produce the wrong regulator
notification list.

## What none of this can do

Every check here is falsification only. A sufficiently careful fabricator
produces data that passes all of them, and a genuine export of unusual data can
trip one. Weigh signals together, state confidence honestly, and remember that
proving a sample fake does not prove an exposure did not happen.
