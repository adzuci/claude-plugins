# Report Bundle Schema (HTML output)

The `html` argument does not have the agent write HTML. The agent writes **one JSON bundle** and
`scripts/render_html.py` turns it into a self-contained page. The script owns layout, palette,
typography, zero-column folding, sparklines, print behaviour, and the accuracy disclaimer, so every
run looks the same and every number on the page came from the bundle.

```bash
python scripts/render_html.py --sample-bundle > gcp-cost-review-YYYY-MM-DD.bundle.json  # edit this
python scripts/render_html.py gcp-cost-review-YYYY-MM-DD.bundle.json > gcp-cost-review-YYYY-MM-DD.html
python scripts/render_html.py --sample > /tmp/sample.html   # see what the output looks like
```

Keep the bundle next to the HTML. The next run reads the prior bundle at Step 0 to fill
`since_last`, which is what makes the week-over-week narrative work.

## Page order (fixed)

1. Name and scope, run metadata, one plain-language summary paragraph.
1. KPI strip (up to 5 tiles).
1. Findings callouts: what needs attention or cannot be measured.
1. Actions: up to 4 recommendations ranked by monthly dollars, then the addressable total.
1. Since last run: status of each prior recommendation (only when `prior_report` is set).
1. Detail: one collapsible block per step. Zero-in-every-row columns are folded out of tables
   and named once in a note. Weekly series get an inline SVG sparkline.
1. Method, queries run, accuracy disclaimer.

## Top-level keys

| Key | Type | Notes |
| --- | --- | --- |
| `scope` | string | `"all projects"` for the weekly review, or `"mongo/main"` for a `workload=` run. Sets the page title. |
| `title` | string | Optional override of the derived title. |
| `run_date` | `YYYY-MM-DD` | Required. |
| `period` | string | Human-readable window, e.g. `"Aug 2026 vs Jul 2026, plus 8 weekly points"`. |
| `command` | string | The exact invocation, so a reader can re-run it. |
| `source_url` | URL | Optional link to the skill source or PR. |
| `prior_report` | `YYYY-MM-DD` or `null` | Date of the prior report found at Step 0. `null` on a first run. |
| `summary` | string | Two or three sentences for someone who does not work in the console. No SKU names. |
| `kpis` | list | See below. Max 5 rendered. |
| `findings` | list | See below. |
| `recommendations` | list | See below. Max 4 rendered, ranked by `monthly_usd` desc; unknown impact sorts last. |
| `since_last` | list | `{recommendation, status: done\|open\|superseded, note}`. |
| `sections` | list | See below. One per step that produced output. |
| `queries_run` | list of strings | `["Q1", "Q2", ...]`, printed in the footer. |
| `methodology` | list of strings | Run-specific notes. The standard net-vs-gross, lag, and read-only notes are appended automatically. |

### `kpis[]`

```json
{"label": "Net spend, Aug", "value": 1845374, "delta": "+$296k vs Jul (+19.1%)", "tone": "up"}
```

`value` may be a number (rendered as `$1,845,374`) or a preformatted string (`"-0.4%"`).
`tone` is `up` (cost increase), `down` (saving or decrease), `warn`, or `neutral`. Tone is semantic
colour, not decoration: `up` is amber because a rising bill is not good news.

### `findings[]`

```json
{"kind": "gap", "title": "Disk cost is unattributable by label.", "body": "..."}
```

`kind` is `gap` (data or labeling gap), `anomaly` (cleared a threshold), `good`, or `info`. Use
`gap` for anything the report could not measure. A zero that is really a gap must never be shown as
a zero without a `gap` finding beside it.

### `recommendations[]`

```json
{
  "action": "Resize the 3 MachineTypeRecommender-flagged VMs in apollo-ops",
  "monthly_usd": 340,
  "effort": "S",
  "risk": "low",
  "owner": "DevOps",
  "what": "vm-a, vm-b, vm-c in us-central1-b, n2-standard-8 to n2-standard-4",
  "why": "google.compute.instance.MachineTypeRecommender, 14-day utilisation under 20%",
  "next_step": "gcp-vms-migration-advisor for the family question; otherwise a Terraform PR"
}
```

`monthly_usd` is `null` when the value is real but not yet priced (a labeling backfill, for
example). Every recommendation must name a specific resource, project, or service and cite the query
or recommender that produced it. `owner` is the team or person who would make the change.

### `sections[]`

```json
{
  "step": "2c",
  "title": "Weekly decomposition, mongo/main",
  "hint": "Q18",
  "open": true,
  "columns": ["Week", "commitments", "cores", "ram", "pd-ssd"],
  "rows": [["2026-07-20", 30727, 363, 19, 0]],
  "format": "usd",
  "fold_zero_columns": true,
  "series": {"label": "Weekly net, mongo/main", "x": ["2026-07-20", "..."], "y": [31110, 31095]},
  "note": "Categories from sku.description patterns.",
  "defer_to": "gcp-commitment-review",
  "body": "Prose used instead of a table when a step has no rows (e.g. the Step 6 handoff)."
}
```

- `rows` are lists in column order. Numbers stay numbers; the renderer formats them with `format`
  (`usd`, `usd_signed`, `pct`, `int`, `plain`) and right-aligns numeric columns. Preformatted
  strings pass through as-is.
- `open: true` for the tables the run is about (the scoped workload); collapsed otherwise.
- `fold_zero_columns` defaults to `true`. The first column is the row key and is never folded.
- `series` is optional. Give the weekly totals, not a single category, unless the category is the
  finding.

## Publishing

Write the `.html` to the working directory. If the Artifact tool is available in the session,
publish the same file as an artifact (title is taken from the page) and give the user the link; the
file stays on disk either way. If the tool is not available, tell the user the path and that the
page opens offline in any browser and prints with every section expanded.
