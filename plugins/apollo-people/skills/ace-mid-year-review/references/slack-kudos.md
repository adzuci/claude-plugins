# Slack Kudos Scraping

Shoutouts in #kudos and #eoq-celebration usually **@-mention** the person and
rarely include their full name as plain text. A single name search misses most
of them. Run multiple passes and combine the results:

1. Search **within each channel** explicitly (scope the query to the channel,
   e.g. `in:#kudos`), not just a global keyword search.
1. Search for the employee's **@-mention / username**, their **first name**,
   and their **full name** separately — kudos posts often use just a first name
   or an @-handle.
1. Cross-check via **Glean**, which indexes Slack — it can surface kudos a
   direct Slack search misses.
1. Cover the **full review window (1 Feb – 31 Jul 2026)** — recognition
   clusters around quarter-ends (late April, late July), so don't stop at the
   first page of recent results.

For each hit, record who posted it, the date, the exact wording, and a direct
link to the message — you'll cite by name and link in the draft.
