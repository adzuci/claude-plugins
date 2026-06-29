# Report Mode Reference

Use this reference when the caller asks for an HTML report, summary, dashboard, all ideas, or ideas from a timeframe such as `2d`, `1w`, `30d`, or `2026-06-01`.

## Fetch Entries

Use the Notion connector to query the Ideation Log database target defined in `notion-connector.md`.

If the connector supports server-side filters, apply the timeframe to the `Date` property first. If the schema uses a different date field, use the closest returned date property and note that choice in the recap.

If connector filtering is unavailable, fetch all accessible rows and let `scripts/render_ideas_report.py` filter locally.

If Notion is unavailable, ask the caller for exported or pasted Ideation Log JSON and continue from "Normalize Input for the Script." Do not claim the report covers live Notion data unless the connector fetch succeeded.

## Normalize Input for the Script

Save fetched pages as JSON. The script accepts:

- a raw list of Notion pages
- a Notion-style object with a `results` array
- a simple list of dictionaries using readable keys such as `Idea Name`, `Status`, `Impact Level`, `Product Area`, `Entry Type`, `Effort to Fix`, `Date`, and `Description`

Do not hand-edit the fetched data except to remove secrets or unrelated bulky blocks. Preserve page URLs when available.

## Render HTML

Run:

```bash
python3 scripts/render_ideas_report.py \
  --input <ideas.json> \
  --output <ideas-report.html> \
  --since <all|2d|1w|30d|YYYY-MM-DD> \
  --title "Support Rotation Ideas"
```

Use `--since all` when the caller asks for all ideas. If no timeframe is provided, default to `1w` for a recent operating report and say that you used one week.

## Report Content

The HTML report should include:

- total ideas in scope
- timeframe and generation time
- counts by status, impact, entry type, and product area
- high-impact / low-effort candidates
- a sortable-looking table or scannable list of all scoped ideas
- source links back to Notion pages when available

In the final recap, include the local HTML path, the timeframe used, the count of rows included, and any connector or schema caveats.
