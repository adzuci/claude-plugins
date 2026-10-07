"""render_html.py — deterministic HTML report renderer for
gcp-cost-optimization-review's `html` argument.

The skill (an LLM following SKILL.md) runs the BigQuery and gcloud steps,
then writes ONE JSON "report bundle" (schema: references/report-bundle.md)
and pipes it through this script. The script owns every design decision:
layout, palette, typography, zero-column folding, sparklines, the accuracy
disclaimer. That keeps the report identical in shape from run to run and
keeps the LLM from hand-authoring 300 lines of HTML each week.

    python scripts/render_html.py bundle.json > gcp-cost-review-2026-09-14.html
    python scripts/render_html.py --sample-bundle > bundle.json   # starting point
    python scripts/render_html.py --sample > sample.html          # what it looks like

Pure functions at module scope so they are testable without GCP. No
external assets: inline CSS, inline SVG sparklines, Google Fonts with a real
fallback stack (the only external request, and the page reads fine if it is
blocked). No JavaScript.

Python 3.9 compatible (see repo CLAUDE.md Testing convention).
"""
from __future__ import annotations

import html
import json
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple

SKILL_COMMAND = "/apollo-eng-devops:gcp-cost-optimization-review"
BILLING_TABLE = (
    "databricks-apolloio.billing_export.gcp_billing_export_v1_0174D0_6590F0_824CC0"
)

DEFAULT_METHODOLOGY = [
    "Source: the BigQuery billing export, queried read-only from indigo-lotus-415. "
    "Query IDs (Q1, Q12, Q18, ...) refer to references/bq-queries.md.",
    "All headline figures are net of credits. Credits run 35 to 40% of gross at Apollo, "
    "so a gross figure overstates the bill by roughly a third.",
    "The most recent 2 days are excluded from every trend; billing data finalizes 24 to 48 hours "
    "after usage. Weekly buckets are complete Monday to Sunday weeks.",
    "The Console reports by billing period (28 to 32 days); this report uses calendar months. "
    "An additional, uncharacterized Console-vs-export gap exists. Spot-check before quoting externally.",
    "No sku.category field exists; resource-type splits are pattern-matched on sku.description "
    "and are approximate.",
    "Read-only: no infrastructure, ticket, or configuration was changed to produce this report.",
]

ACCURACY_DISCLAIMER = (
    "Assembled by an AI assistant from Apollo's billing export without a second reviewer. "
    "Verify any figure before using it in a deck, a budget, or a vendor negotiation. "
    "Internal to Apollo DevOps."
)

EFFORT_LABEL = {"S": "small", "M": "medium", "L": "large"}


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def esc(value: Any) -> str:
    """HTML-escape anything the bundle hands us. Every string that reaches
    the page goes through here; the bundle is LLM-authored and may contain
    resource names with angle brackets or ampersands."""
    return html.escape("" if value is None else str(value), quote=True)


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def fmt_usd(value: Any, signed: bool = False) -> str:
    """$12,345 style. Rounds to whole dollars above $100, keeps cents below
    so a $2.99 idle-disk recommendation does not render as $3. Negative
    values get a leading minus; `signed` adds an explicit plus."""
    if not is_number(value):
        return esc(value)
    magnitude = abs(float(value))
    if magnitude >= 100:
        body = "${0:,.0f}".format(magnitude)
    elif magnitude == 0:
        body = "$0"
    else:
        body = "${0:,.2f}".format(magnitude)
    if value < 0:
        return "-" + body
    if signed and value > 0:
        return "+" + body
    return body


def fmt_pct(value: Any, signed: bool = True) -> str:
    if not is_number(value):
        return esc(value)
    sign = "+" if (signed and value > 0) else ""
    return "{0}{1:.1f}%".format(sign, float(value))


def fmt_cell(value: Any, fmt: str) -> str:
    if value is None:
        return ""
    if not is_number(value):
        return esc(value)
    if fmt == "usd":
        return fmt_usd(value)
    if fmt == "usd_signed":
        return fmt_usd(value, signed=True)
    if fmt == "pct":
        return fmt_pct(value)
    if fmt == "int":
        return "{0:,.0f}".format(float(value))
    return esc(value)


# ---------------------------------------------------------------------------
# Table shaping
# ---------------------------------------------------------------------------


def _is_zero(value: Any) -> bool:
    if value is None:
        return True
    if is_number(value):
        return float(value) == 0.0
    text = str(value).strip().replace("$", "").replace(",", "")
    try:
        return float(text) == 0.0
    except ValueError:
        return False


def drop_zero_columns(
    columns: Sequence[str], rows: Sequence[Sequence[Any]]
) -> Tuple[List[str], List[List[Any]], List[str]]:
    """Remove columns that are zero (or empty) in every row.

    The mongo/main review shipped a 10-column table where pd-ssd,
    pd-balanced, snapshots, nat and egress were zero on every line. Five
    zero columns are not information, they are a labeling gap; the gap is
    reported once in a note (see render_section) and the table keeps only
    columns that carry a value. Returns (columns, rows, dropped). The first
    column is never dropped: it is the row key."""
    if not rows:
        return list(columns), [list(r) for r in rows], []
    keep: List[int] = []
    dropped: List[str] = []
    for idx, name in enumerate(columns):
        if idx == 0:
            keep.append(idx)
            continue
        col = [r[idx] if idx < len(r) else None for r in rows]
        if all(_is_zero(v) for v in col):
            dropped.append(str(name))
        else:
            keep.append(idx)
    new_cols = [str(columns[i]) for i in keep]
    new_rows = [[(r[i] if i < len(r) else None) for i in keep] for r in rows]
    return new_cols, new_rows, dropped


def column_is_numeric(rows: Sequence[Sequence[Any]], idx: int) -> bool:
    vals = [r[idx] for r in rows if idx < len(r) and r[idx] is not None and r[idx] != ""]
    return bool(vals) and all(is_number(v) for v in vals)


# ---------------------------------------------------------------------------
# Sparkline (inline SVG, no library)
# ---------------------------------------------------------------------------


def sparkline_svg(
    values: Sequence[float],
    labels: Optional[Sequence[str]] = None,
    width: int = 560,
    height: int = 72,
    title: str = "",
) -> str:
    """Bar sparkline for a short weekly series. One scale, baseline at zero,
    the final bar emphasized, first and last x labels only. Bars carry a
    <title> so hovering reads the exact value; no JS needed."""
    vals = [float(v) for v in values if is_number(v)]
    if len(vals) < 2:
        return ""
    n = len(vals)
    pad_l, pad_r, pad_t, pad_b = 4, 4, 6, 18
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b
    vmax = max(vals) if max(vals) > 0 else 1.0
    gap = 2
    bar_w = max(2.0, (plot_w - gap * (n - 1)) / n)
    parts = [
        '<svg class="spark" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        'role="img" aria-label="{t}">'.format(w=width, h=height, t=esc(title))
    ]
    baseline_y = pad_t + plot_h
    parts.append(
        '<line x1="{0}" y1="{1}" x2="{2}" y2="{1}" class="spark-base"/>'.format(
            pad_l, baseline_y, pad_l + plot_w
        )
    )
    for i, v in enumerate(vals):
        h = 0.0 if v <= 0 else max(1.0, plot_h * (v / vmax))
        x = pad_l + i * (bar_w + gap)
        y = baseline_y - h
        cls = "spark-bar last" if i == n - 1 else "spark-bar"
        label = (labels[i] if labels and i < len(labels) else str(i + 1))
        parts.append(
            '<rect class="{cls}" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}">'
            "<title>{lab}: {val}</title></rect>".format(
                cls=cls, x=x, y=y, w=bar_w, h=h, lab=esc(label), val=fmt_usd(v)
            )
        )
    if labels and len(labels) >= 2:
        parts.append(
            '<text class="spark-label" x="{0}" y="{1}">{2}</text>'.format(
                pad_l, height - 4, esc(labels[0])
            )
        )
        parts.append(
            '<text class="spark-label" x="{0}" y="{1}" text-anchor="end">{2}</text>'.format(
                pad_l + plot_w, height - 4, esc(labels[-1])
            )
        )
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------


def render_kpis(kpis: Sequence[Dict[str, Any]]) -> str:
    if not kpis:
        return ""
    tiles = []
    for k in kpis[:5]:
        tone = k.get("tone", "neutral")
        if tone not in ("up", "down", "warn", "neutral"):
            tone = "neutral"
        value = k.get("value")
        value_text = fmt_usd(value) if is_number(value) else esc(value)
        tiles.append(
            '<div class="kpi"><span class="kpi-l">{label}</span>'
            '<span class="kpi-v mono {tone}">{value}</span>'
            '<span class="kpi-d">{delta}</span></div>'.format(
                label=esc(k.get("label", "")),
                tone=tone,
                value=value_text,
                delta=esc(k.get("delta", "")),
            )
        )
    return '<section class="kpis" aria-label="Key figures">{0}</section>'.format("".join(tiles))


def sort_recommendations(recs: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Rank by monthly dollar impact, largest first; unknown impact last."""

    def key(r: Dict[str, Any]) -> Tuple[int, float]:
        v = r.get("monthly_usd")
        return (0, -float(v)) if is_number(v) else (1, 0.0)

    return sorted(recs, key=key)


def render_recommendations(recs: Sequence[Dict[str, Any]]) -> str:
    if not recs:
        return (
            '<section class="panel"><h2>Actions</h2><p class="empty">No recommendation cleared the '
            "quality bar this run (named resource, dollar estimate from a query that ran, owner). "
            "That is a valid result; do not pad it.</p></section>"
        )
    ordered = sort_recommendations(recs)[:4]
    total = sum(float(r["monthly_usd"]) for r in ordered if is_number(r.get("monthly_usd")))
    items = []
    for i, r in enumerate(ordered, start=1):
        usd = r.get("monthly_usd")
        effort = str(r.get("effort", "")).upper()
        tags = []
        if is_number(usd):
            tags.append('<span class="tag mono">{0}/mo</span>'.format(fmt_usd(usd)))
        if effort in EFFORT_LABEL:
            tags.append('<span class="tag">{0} effort</span>'.format(EFFORT_LABEL[effort]))
        if r.get("risk"):
            tags.append('<span class="tag">{0} risk</span>'.format(esc(r["risk"])))
        if r.get("owner"):
            tags.append('<span class="tag">owner: {0}</span>'.format(esc(r["owner"])))
        rows = []
        for field, label in (("what", "What"), ("why", "Evidence"), ("next_step", "Next step")):
            if r.get(field):
                rows.append(
                    '<div class="rec-row"><span class="rec-k">{0}</span><span>{1}</span></div>'.format(
                        label, esc(r[field])
                    )
                )
        items.append(
            '<li class="rec"><div class="rec-head"><span class="rec-n mono">{n}</span>'
            '<h3>{action}</h3></div><div class="tags">{tags}</div>{rows}</li>'.format(
                n=i, action=esc(r.get("action", "")), tags="".join(tags), rows="".join(rows)
            )
        )
    head = (
        '<h2>Actions <span class="h2-sub">ranked by monthly impact'
        + (", {0}/mo addressable".format(fmt_usd(total)) if total else "")
        + "</span></h2>"
    )
    return '<section class="panel actions">{0}<ol class="recs">{1}</ol>'.format(
        head, "".join(items)
    ) + (
        '<p class="note">Recommendations only. Nothing in this report has been actioned; '
        "each item names the deep-dive skill or runbook that owns the change.</p></section>"
    )


def render_findings(findings: Sequence[Dict[str, Any]]) -> str:
    if not findings:
        return ""
    out = []
    for f in findings:
        kind = f.get("kind", "info")
        if kind not in ("gap", "anomaly", "info", "good"):
            kind = "info"
        out.append(
            '<div class="callout {kind}"><b>{title}</b> {body}</div>'.format(
                kind=kind, title=esc(f.get("title", "")), body=esc(f.get("body", ""))
            )
        )
    return '<section class="findings">{0}</section>'.format("".join(out))


def render_since_last(items: Sequence[Dict[str, Any]], prior: Optional[str]) -> str:
    if not prior:
        return '<p class="meta-line">First run against this working directory. No prior report to compare.</p>'
    if not items:
        return '<p class="meta-line">Prior report {0}. No prior recommendations to carry forward.</p>'.format(
            esc(prior)
        )
    rows = []
    for it in items:
        status = str(it.get("status", "open")).lower()
        if status not in ("done", "open", "superseded"):
            status = "open"
        rows.append(
            '<tr><td>{0}</td><td><span class="pill {1}">{1}</span></td><td>{2}</td></tr>'.format(
                esc(it.get("recommendation", "")), status, esc(it.get("note", ""))
            )
        )
    return (
        '<section class="panel"><h2>Since {0}</h2><div class="wrap"><table>'
        "<thead><tr><th>Prior recommendation</th><th>Status</th><th>Note</th></tr></thead>"
        "<tbody>{1}</tbody></table></div></section>"
    ).format(esc(prior), "".join(rows))


def render_table(
    columns: Sequence[str], rows: Sequence[Sequence[Any]], fmt: str
) -> str:
    if not rows:
        return '<p class="empty">No rows.</p>'
    numeric = [column_is_numeric(rows, i) for i in range(len(columns))]
    head = "".join(
        '<th{0}>{1}</th>'.format(' class="r"' if numeric[i] else "", esc(c))
        for i, c in enumerate(columns)
    )
    body_rows = []
    for r in rows:
        cells = []
        for i in range(len(columns)):
            v = r[i] if i < len(r) else None
            cls = ' class="mono r"' if numeric[i] else (' class="mono"' if i == 0 else "")
            cells.append("<td{0}>{1}</td>".format(cls, fmt_cell(v, fmt)))
        body_rows.append("<tr>{0}</tr>".format("".join(cells)))
    return '<div class="wrap"><table><thead><tr>{0}</tr></thead><tbody>{1}</tbody></table></div>'.format(
        head, "".join(body_rows)
    )


def render_section(section: Dict[str, Any]) -> str:
    """One technical-detail block. Open by default when the bundle says so
    (the scoped workload's own tables), collapsed otherwise."""
    columns = list(section.get("columns", []))
    rows = [list(r) for r in section.get("rows", [])]
    fmt = section.get("format", "usd")
    dropped: List[str] = []
    if columns and section.get("fold_zero_columns", True):
        columns, rows, dropped = drop_zero_columns(columns, rows)
    parts = []
    if section.get("series"):
        s = section["series"]
        parts.append(
            '<figure class="spark-wrap">{0}<figcaption>{1}</figcaption></figure>'.format(
                sparkline_svg(s.get("y", []), s.get("x"), title=s.get("label", "")),
                esc(s.get("label", "")),
            )
        )
    if columns:
        parts.append(render_table(columns, rows, fmt))
    elif section.get("body"):
        parts.append("<p>{0}</p>".format(esc(section["body"])))
    if dropped:
        parts.append(
            '<p class="note fold">Zero in every row and folded out of the table: <b>{0}</b>. '
            "A category that is zero for the whole window is an attribution gap or a pattern "
            "miss, not a saving.</p>".format(esc(", ".join(dropped)))
        )
    if section.get("note"):
        parts.append('<p class="note">{0}</p>'.format(esc(section["note"])))
    if section.get("defer_to"):
        parts.append(
            '<p class="note">Deep dive: <code>{0}</code>.</p>'.format(esc(section["defer_to"]))
        )
    summary = '<summary><span class="step mono">{0}</span> {1}<span class="hint">{2}</span></summary>'.format(
        esc(section.get("step", "")), esc(section.get("title", "")), esc(section.get("hint", ""))
    )
    return '<details{open}>{summary}<div class="body">{body}</div></details>'.format(
        open=" open" if section.get("open") else "", summary=summary, body="".join(parts)
    )


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

CSS = """
:root{color-scheme:light;
  --bg:#F3F5F1;--surf:#FFFFFF;--ink:#16202A;--mute:#5C6B76;--rule:#D8DED9;
  --acc:#0F6E6B;--acc-soft:#E1EFEC;
  --up:#A8520A;--up-soft:#FBEBDC;--down:#1F7A4D;--down-soft:#E2F2E8;
  --warn:#8A6A00;--warn-soft:#FAF1D3;--bad:#A3262C;--bad-soft:#F8E3E4}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;
  --bg:#141719;--surf:#1C2124;--ink:#EEF1EC;--mute:#9BA6AB;--rule:#2B3236;
  --acc:#5FC3B8;--acc-soft:#16302E;
  --up:#F0A05A;--up-soft:#3A2A18;--down:#5FCF8F;--down-soft:#17301F;
  --warn:#E5C45A;--warn-soft:#33300F;--bad:#F08A8E;--bad-soft:#3A1C1E}}
:root[data-theme="dark"]{color-scheme:dark;
  --bg:#141719;--surf:#1C2124;--ink:#EEF1EC;--mute:#9BA6AB;--rule:#2B3236;
  --acc:#5FC3B8;--acc-soft:#16302E;
  --up:#F0A05A;--up-soft:#3A2A18;--down:#5FCF8F;--down-soft:#17301F;
  --warn:#E5C45A;--warn-soft:#33300F;--bad:#F08A8E;--bad-soft:#3A1C1E}
*{box-sizing:border-box}
body{margin:0;padding:28px 32px 56px;background:var(--bg);color:var(--ink);
  font:14px/1.5 "IBM Plex Sans",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
.mono{font-family:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace;font-variant-numeric:tabular-nums}
.r{text-align:right}
main{max-width:1100px;margin:0 auto;display:grid;gap:20px}
header{max-width:1100px;margin:0 auto 22px}
h1{font-size:22px;font-weight:600;margin:0 0 6px;letter-spacing:-.01em;text-wrap:balance}
h2{font-size:13px;letter-spacing:.06em;text-transform:uppercase;color:var(--mute);margin:0 0 12px;font-weight:600}
.h2-sub{text-transform:none;letter-spacing:0;font-weight:400;margin-left:8px}
h3{font-size:15px;font-weight:600;margin:0}
.meta{color:var(--mute);font-size:12.5px;max-width:80ch;margin:0 0 4px}
.meta code,code{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:12px}
.meta-line{color:var(--mute);font-size:12.5px;margin:0}
.summary{font-size:15px;max-width:72ch;margin:12px 0 0}
a{color:var(--acc)}
.panel{background:var(--surf);border:1px solid var(--rule);padding:16px 18px}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.kpi{background:var(--surf);border:1px solid var(--rule);padding:12px 14px;display:flex;flex-direction:column;gap:2px}
.kpi-l{font-size:11.5px;color:var(--mute);letter-spacing:.04em;text-transform:uppercase}
.kpi-v{font-size:24px;font-weight:500;line-height:1.2}
.kpi-d{font-size:12px;color:var(--mute)}
.up{color:var(--up)}.down{color:var(--down)}.warn{color:var(--warn)}.neutral{color:var(--ink)}
.findings{display:grid;gap:10px}
.callout{border-left:3px solid var(--rule);background:var(--surf);padding:10px 14px;font-size:13px;max-width:90ch}
.callout b{margin-right:4px}
.callout.gap{border-color:var(--warn);background:var(--warn-soft)}.callout.gap b{color:var(--warn)}
.callout.anomaly{border-color:var(--bad);background:var(--bad-soft)}.callout.anomaly b{color:var(--bad)}
.callout.good{border-color:var(--down);background:var(--down-soft)}.callout.good b{color:var(--down)}
.callout.info{border-color:var(--acc);background:var(--acc-soft)}.callout.info b{color:var(--acc)}
.recs{list-style:none;margin:0;padding:0;display:grid;gap:14px}
.rec{border-top:1px solid var(--rule);padding-top:12px;display:grid;gap:6px}
.rec-head{display:flex;gap:10px;align-items:baseline}
.rec-n{color:var(--acc);font-size:13px;min-width:1.5em}
.tags{display:flex;flex-wrap:wrap;gap:6px}
.tag{font-size:11.5px;border:1px solid var(--rule);padding:1px 7px;color:var(--mute);background:var(--bg)}
.rec-row{display:grid;grid-template-columns:7em 1fr;gap:8px;font-size:13px;max-width:90ch}
.rec-k{color:var(--mute);font-size:11.5px;letter-spacing:.04em;text-transform:uppercase;padding-top:2px}
.pill{font-size:11.5px;padding:1px 8px;border:1px solid var(--rule);text-transform:uppercase;letter-spacing:.04em}
.pill.done{color:var(--down);border-color:var(--down);background:var(--down-soft)}
.pill.open{color:var(--warn);border-color:var(--warn);background:var(--warn-soft)}
.pill.superseded{color:var(--mute)}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th{text-align:left;color:var(--mute);font-weight:500;font-size:11.5px;letter-spacing:.04em;text-transform:uppercase;padding:6px 8px;border-bottom:1px solid var(--rule)}
th.r{text-align:right}
td{padding:6px 8px;border-bottom:1px solid var(--rule);white-space:nowrap}
tbody tr:last-child td{border-bottom:none}
.wrap{overflow-x:auto}
details{background:var(--surf);border:1px solid var(--rule)}
details+details{margin-top:-1px}
summary{cursor:pointer;padding:12px 18px;font-weight:600;font-size:14px;display:flex;gap:10px;align-items:baseline;list-style:none}
summary::-webkit-details-marker{display:none}
summary::before{content:"\\25B8";color:var(--mute);font-size:11px}
details[open]>summary::before{content:"\\25BE"}
summary:hover{color:var(--acc)}
summary:focus-visible{outline:2px solid var(--acc);outline-offset:-2px}
.step{color:var(--acc);font-size:12px;min-width:2.2em}
.hint{margin-left:auto;font-weight:400;font-size:12px;color:var(--mute)}
.body{padding:4px 18px 16px;display:grid;gap:12px;border-top:1px solid var(--rule)}
.note{font-size:12.5px;color:var(--mute);margin:0;max-width:90ch}
.note.fold b{color:var(--ink);font-weight:500}
.empty{color:var(--mute);font-size:13px;margin:0}
.spark-wrap{margin:8px 0 0}
.spark{display:block;max-width:100%;height:auto}
.spark-bar{fill:var(--acc);opacity:.55}.spark-bar.last{opacity:1}
.spark-base{stroke:var(--rule);stroke-width:1}
.spark-label{fill:var(--mute);font-size:10px;font-family:"IBM Plex Mono",ui-monospace,monospace}
figcaption{font-size:12px;color:var(--mute);margin-top:4px}
footer{max-width:1100px;margin:32px auto 0;color:var(--mute);font-size:12.5px;display:grid;gap:10px}
footer ul{margin:0;padding-left:18px;max-width:90ch}
footer li{margin:2px 0}
.disclaimer{border-top:1px solid var(--rule);padding-top:12px}
.disclaimer b{color:var(--ink)}
@media (max-width:800px){.kpis{grid-template-columns:1fr 1fr}body{padding:20px 16px 40px}.rec-row{grid-template-columns:1fr}}
@media print{body{padding:0;background:#fff;color:#000}details>summary{pointer-events:none}
  details:not([open])>.body{display:grid!important}summary::before{content:""}details{break-inside:avoid}}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
"""


def _page_title(bundle: Dict[str, Any]) -> str:
    scope = bundle.get("scope")
    if scope and scope not in ("all", "account-wide", "all projects"):
        return "GCP Cost Review, {0}".format(scope)
    return "GCP Cost Review"


def render_report(bundle: Dict[str, Any]) -> str:
    """Whole page. Order is deliberate: name and scope, plain-language
    summary, KPI strip, findings that need attention, actions, what moved
    since last run, then technical detail collapsed, then methodology and
    the accuracy disclaimer."""
    title = bundle.get("title") or _page_title(bundle)
    run_date = bundle.get("run_date", "")
    command = bundle.get("command") or SKILL_COMMAND
    prior = bundle.get("prior_report")
    period = bundle.get("period", "")
    methodology = list(bundle.get("methodology", [])) + DEFAULT_METHODOLOGY
    queries = bundle.get("queries_run", [])

    sections_html = "".join(render_section(s) for s in bundle.get("sections", []))
    meta_bits = []
    if run_date:
        meta_bits.append("Run {0}".format(esc(run_date)))
    if period:
        meta_bits.append("Period {0}".format(esc(period)))
    meta_bits.append("Billing account <code>0174D0-6590F0-824CC0</code>")
    meta_bits.append("Net of credits unless labelled gross")
    meta_bits.append("Read-only")

    head = (
        "<!DOCTYPE html>\n"
        '<html lang="en"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>{title}</title>\n"
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600'
        '&family=IBM+Plex+Mono:wght@400;500&display=swap">\n'
        "<style>{css}</style>\n</head><body>\n"
    ).format(title=esc(title), css=CSS)

    header = (
        "<header><h1>{title}</h1>"
        '<p class="meta">{meta}</p>'
        '<p class="meta">Output of <code>{cmd}</code>.{links}</p>'
        "{since}"
        "{summary}</header>"
    ).format(
        title=esc(title),
        meta=" · ".join(meta_bits),
        cmd=esc(command),
        links=(
            ' <a href="{0}">Skill source</a>.'.format(esc(bundle["source_url"]))
            if bundle.get("source_url")
            else ""
        ),
        since=(
            '<p class="meta-line">Prior report: {0}.</p>'.format(esc(prior))
            if prior
            else '<p class="meta-line">First run in this directory; no prior baseline.</p>'
        ),
        summary=(
            '<p class="summary">{0}</p>'.format(esc(bundle["summary"])) if bundle.get("summary") else ""
        ),
    )

    body = [
        render_kpis(bundle.get("kpis", [])),
        render_findings(bundle.get("findings", [])),
        render_recommendations(bundle.get("recommendations", [])),
    ]
    if prior:
        body.append(render_since_last(bundle.get("since_last", []), prior))
    if sections_html:
        body.append(
            '<section><h2>Detail <span class="h2-sub">expand a step; everything opens when printed</span></h2>'
            "{0}</section>".format(sections_html)
        )

    footer = (
        "<footer>"
        "<div><b>Method</b><ul>{method}</ul></div>"
        "{queries}"
        '<p class="disclaimer"><b>Accuracy.</b> {disc}</p>'
        "<p>Generated by <code>{cmd}</code>{when}. Re-run the same command to refresh; "
        "keep dated reports in the working directory so the next run can compare.</p>"
        "</footer>"
    ).format(
        method="".join("<li>{0}</li>".format(esc(m)) for m in methodology),
        queries=(
            '<p>Queries run: <span class="mono">{0}</span>.</p>'.format(esc(", ".join(str(q) for q in queries)))
            if queries
            else ""
        ),
        disc=esc(ACCURACY_DISCLAIMER),
        cmd=esc(SKILL_COMMAND),
        when=(" on {0}".format(esc(run_date)) if run_date else ""),
    )

    return head + header + "<main>" + "".join(b for b in body if b) + "</main>" + footer + "\n</body></html>\n"


# ---------------------------------------------------------------------------
# Sample bundle (the 2026-09-14 mongo/main run, re-shaped the way the
# renderer wants it). Serves as the schema example and the test fixture.
# ---------------------------------------------------------------------------


def sample_bundle() -> Dict[str, Any]:
    weeks = [
        "2026-07-20", "2026-07-27", "2026-08-03", "2026-08-10",
        "2026-08-17", "2026-08-24", "2026-08-31", "2026-09-07",
    ]
    commitments = [30727, 30735, 30724, 30798, 30829, 30804, 30825, 26432]
    cores = [363, 345, 382, 269, 220, 267, 232, 177]
    ram = [19, 14, 16, 12, 5, 9, 8, 9]
    other = [1, 1, 1, 1, 1, 1, 2, 1]
    q18_rows = [
        [w, c, co, r, 0, 0, 0, 0, 0, o]
        for w, c, co, r, o in zip(weeks, commitments, cores, ram, other)
    ]
    totals = [sum(x) for x in zip(commitments, cores, ram, other)]
    return {
        "scope": "mongo/main",
        "run_date": "2026-09-14",
        "period": "Aug 2026 vs Jul 2026, plus 8 weekly points",
        "command": SKILL_COMMAND + " workload=mongo/main html",
        "source_url": "https://github.com/apolloio/claude-plugins/pull/275",
        "prior_report": None,
        "summary": (
            "mongo/main cost $137.6k net in August, up $8.4k on July, and is flat week over week. "
            "99% of what the billing export attributes to it is 3-year commitment charges; its "
            "persistent disks carry no workload label, so the largest real cost driver for a "
            "database cluster is invisible at this grain."
        ),
        "kpis": [
            {"label": "mongo/main, Aug net", "value": 137635, "delta": "+$8,430 vs Jul (+6.5%)", "tone": "up"},
            {"label": "mongo, this week vs last", "value": "-0.4%", "delta": "$73,058 vs $73,367 net. Under both flag thresholds", "tone": "neutral"},
            {"label": "8-week total, mongo/main", "value": 248659, "delta": "8 complete weeks, net", "tone": "neutral"},
            {"label": "Attributed disk cost", "value": 0, "delta": "Disks and snapshots carry no infra labels", "tone": "warn"},
        ],
        "findings": [
            {
                "kind": "gap",
                "title": "Disk cost is unattributable by label.",
                "body": (
                    "pd-ssd, pd-balanced and snapshots are zero for every workload because persistent "
                    "disks are not labeled with infra_workload or infra_cluster. The $1.08M SSD line on "
                    "the 90-day bill cannot be split by workload today. Labeling gap, not a saving."
                ),
            },
            {
                "kind": "info",
                "title": "Commitments attribute cleanly.",
                "body": "3-year C3 CUD charges carry the instance labels and land under mongo/main at about $30.8k a week.",
            },
        ],
        "recommendations": [
            {
                "action": "Backfill infra_workload and infra_cluster labels on persistent disks",
                "monthly_usd": None,
                "effort": "M",
                "risk": "low",
                "owner": "DevOps",
                "what": "Every PD and snapshot in production, starting with the mongo/main disks (name pattern main-*).",
                "why": "Q18 returns zero disk cost for all 31 clusters; Q11 label coverage fell from 86.6% to 71.2% since May.",
                "next_step": "Terraform label block on the disk resources; verify with gcloud compute disks list --format=value(labels) before the next run.",
            },
            {
                "action": "Price mongo/main provisioned SSD from gcloud until labels land",
                "monthly_usd": None,
                "effort": "S",
                "risk": "low",
                "owner": "DevOps",
                "what": "gcloud compute disks list --filter=name~main, summed sizeGb, times the account-wide pd-ssd rate from Q4.",
                "why": "Gives a defensible disk figure for the workload this month rather than reporting $0.",
                "next_step": "Run disk-inventory for the full capacity and IOPS view.",
            },
        ],
        "since_last": [],
        "sections": [
            {
                "step": "2c",
                "title": "Weekly decomposition, mongo/main",
                "hint": "Q18",
                "open": True,
                "columns": ["Week", "commitments", "cores", "ram", "pd-ssd", "pd-balanced", "snapshots", "nat", "egress", "other"],
                "rows": q18_rows,
                "format": "usd",
                "series": {"label": "Weekly net, mongo/main, all categories", "x": weeks, "y": totals},
                "note": (
                    "Categories from sku.description patterns. The final week's drop is the "
                    "commitment line, not a usage change; confirm against gcp-commitment-review."
                ),
                "defer_to": "gcp-commitment-review",
            },
            {
                "step": "2b",
                "title": "Month over month by workload, top 10",
                "hint": "Q12, account-wide context",
                "open": False,
                "columns": ["Workload", "Cluster", "Project", "Aug", "Jul", "Delta"],
                "rows": [
                    ["(unlabeled)", "", "data-platform-production", 439566, 251581, 187986],
                    ["elasticsearch", "main-v1", "production", 122301, 93930, 28372],
                    ["(unlabeled)", "", "production", 514868, 492164, 22704],
                    ["gke", "production", "production", 143201, 131186, 12015],
                    ["(unlabeled)", "", "data-platform-stg", 58252, 46736, 11516],
                    ["mongo", "main", "production", 137635, 129206, 8430],
                    ["gke", "ops", "devops", 71520, 66358, 5162],
                    ["(unlabeled)", "", "devops", 45501, 41483, 4018],
                    ["mongo", "contacts", "production", 44315, 40504, 3810],
                    ["mongo", "noncustomer", "production", 40510, 38026, 2485],
                ],
                "format": "usd",
                "note": (
                    "The unlabeled production row is mostly persistent disk. The unlabeled "
                    "data-platform-production row is Claude on Vertex. Both are why the (unlabeled) "
                    "row stays first-class."
                ),
            },
            {
                "step": "2b",
                "title": "Week over week by workload",
                "hint": "Q13, flag at >20% and >$2k",
                "open": False,
                "columns": ["Workload", "This week", "Last week", "Change"],
                "rows": [["mongo", 73058, 73367, "-0.4%"]],
                "format": "usd",
                "note": "No workload cleared both thresholds.",
            },
        ],
        "queries_run": ["Q12", "Q13", "Q18"],
        "methodology": [
            "Scoped run: Steps 2b and 2c only. The full weekly review also runs spend summary, "
            "anomalies, Recommender, and governance."
        ],
    }


USAGE = (
    "usage: python render_html.py <bundle.json>      render a report bundle to HTML on stdout\n"
    "       python render_html.py --sample-bundle    print the sample bundle JSON (schema example)\n"
    "       python render_html.py --sample           render the sample bundle\n"
    "Bundle schema: references/report-bundle.md"
)


def main(argv: List[str]) -> int:
    if not argv or any(a in ("-h", "--help") for a in argv):
        print(USAGE)
        return 0 if argv else 2
    if argv[0] == "--sample-bundle":
        json.dump(sample_bundle(), sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    if argv[0] == "--sample":
        sys.stdout.write(render_report(sample_bundle()))
        return 0
    with open(argv[0], "r", encoding="utf-8") as fh:
        bundle = json.load(fh)
    if not isinstance(bundle, dict):
        print("ERROR: bundle must be a JSON object", file=sys.stderr)
        return 1
    sys.stdout.write(render_report(bundle))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
