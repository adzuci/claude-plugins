# Phase 3b — Detect and Fetch Linked Terms

Many vendor order forms and short-form agreements incorporate their full governing terms by
reference to a URL rather than attaching them. Without fetching those terms, the review is
incomplete — the liability cap, indemnification, DPA, and IP clauses are almost certainly in
the linked document, not in the order form.

## Step 0 — Check for a previously executed agreement

Before attempting to fetch any terms, scan the extracted text for language indicating that the
Order Form incorporates a *previously executed* agreement — one already signed by both parties
on a specific date. Common patterns:

- `"executed by the parties with an effective date of [date]"`
- `"entered into as of [date]"` or `"Agreement dated [date]"`
- `"previously executed [agreement type]"` or `"signed [agreement type] dated [date]"`
- `"the [Agreement Name] between [parties]... effective [date]"`

The distinction matters: a reference to a URL (e.g., "governed by our MSA available at
https://...") points to the vendor's current public terms, which can be fetched and treated
as authoritative. A reference to a previously executed agreement with a specific date means
the parties may have negotiated custom terms that differ from what the vendor publishes today
— and only the signed document reflects the actual deal.

If a previously executed agreement with a specific date is detected:

1. **Alert the user immediately**, before proceeding with any term fetching:

   > ⚠️ **Executed Agreement Detected**: This Order Form incorporates the **[Agreement Name]**
   > executed on **[date]**. That signed agreement may contain negotiated terms that differ
   > from the vendor's current public terms. Do you have a copy to upload? If so, share it
   > and I'll use it for the review instead of fetching public terms. If not, I'll proceed
   > using the vendor's current public terms, but the review may not reflect what was actually
   > agreed at signing.

2. **Wait for the user's response.**
   - If she uploads the executed agreement: use it as the governing terms source. Skip
     Steps 1–3 below (no need to fetch public terms). Proceed to Phase 4.
   - If she confirms she doesn't have it or wants to proceed anyway: continue with Steps
     1–3 below, but add this caveat prominently in the Phase 8 summary:

     > ⚠️ **Review Based on Public Terms**: The governing agreement (**[Agreement Name]**,
     > effective **[date]**) was not available. This review is based on the vendor's current
     > public terms, which may not match what was negotiated at signing. Verify key provisions
     > — indemnification, liability cap, DPA, data use — against the executed agreement before
     > relying on this analysis.

## Step 1 — Scan for linked terms

Search the extracted text for patterns indicating incorporated external terms. Common forms:

- `"available at [URL]"` — e.g., "governed by the MSA available at https://..."
- `"located at [URL]"` or `"accessible at [URL]"`
- `"terms of service at [URL]"`, `"subscription agreement at [URL]"`
- `"incorporated by reference"` followed by a URL
- Any URL containing words like: `/legal`, `/agreements`, `/terms`, `/msa`, `/tos`, `/privacy`

If no linked terms are found, skip to Phase 4.

## Step 2 — Attempt to fetch each linked URL

Try each method in order until one succeeds:

### Attempt 1 — web_fetch
Call the `web_fetch` tool with the URL. If it returns useful text (over 500 characters), use it.
If it fails or returns insufficient content, proceed to Attempt 2.

### Attempt 2 — WebSearch fallback
If web_fetch fails or returns insufficient content, search for the terms:
- Query: `"<vendor name>" master subscription agreement terms`
- If a direct URL to the MSA is returned in results, attempt web_fetch on that URL
- If the search returns a page URL (not a PDF), fetch it and look for a link to the MSA PDF

For each successful fetch, append the content to the contract text under a clear separator:

```
=== LINKED TERMS: <URL> ===
<fetched content>
=== END LINKED TERMS ===
```

## Step 3 — Always fetch the DPA

After fetching the MSA or linked terms, scan the full retrieved text for a DPA URL. Common
patterns: `/dpa`, `/data-processing`, `/data-processing-addendum`, `trustandcompliance`,
`privacy-addendum`. The DPA is always a separate document from the MSA and is critical for
Cat 1 and Cat 3 reviews — it contains the breach notification window, security measures,
subprocessor list, deletion timelines, and data processing restrictions that the MSA only
references by URL.

For each DPA URL found:
1. Attempt web_fetch on the URL directly.
2. If web_fetch fails, search: `"<vendor name>" data processing addendum DPA`
3. Append fetched DPA content under its own separator:

```
=== DPA: <URL> ===
<fetched content>
=== END DPA ===
```

If the DPA cannot be fetched, flag prominently in the summary:
> ⚠️ **DPA Not Retrieved**: The DPA at `[URL]` could not be fetched. Breach notification
> window, security measures, and data deletion terms are unknown. Review DPA manually before
> signing — especially for Cat 1 and Cat 3 contracts.

## Step 4 — Handle fetch failures gracefully

If all fetch attempts fail for the MSA or linked terms (login-gated, unavailable, or returns
no useful text):

- Note the failure prominently in the output summary
- Flag the specific unfetched URL
- Continue the review with what is available, but add a clear caveat:

  > ⚠️ **Review Incomplete**: The governing terms at `[URL]` could not be retrieved. Key
  > provisions (indemnification, liability cap, DPA) may be in those terms. Do not sign
  > without reviewing them manually.

## Step 5 — Note all sources used in the summary

In the Phase 8 summary report, always list what was reviewed:
- The uploaded/downloaded file
- Each linked URL (MSA, terms, DPA) that was successfully fetched
- Each linked URL that could not be fetched (with the incomplete-review caveat)
