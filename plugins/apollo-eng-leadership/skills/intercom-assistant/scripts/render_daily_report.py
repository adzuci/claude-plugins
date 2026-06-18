#!/usr/bin/env python3
"""Render a self-contained HTML report for a day of support calls."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
from pathlib import Path
from typing import Any, Sequence


def esc(value: Any) -> str:
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def count_where(records: list[dict[str, Any]], key: str, value: str) -> int:
    return sum(1 for record in records if str(record.get(key, "")).lower() == value)


def render_list(items: list[Any]) -> str:
    useful = [item for item in items if str(item).strip()]
    if not useful:
        return '<p class="muted">None captured.</p>'
    return "<ul>" + "".join(f"<li>{esc(item)}</li>" for item in useful) + "</ul>"


def render_call(record: dict[str, Any]) -> str:
    product_signals = render_list(as_list(record.get("product_signals")))
    followups = render_list(as_list(record.get("followups")))
    return f"""
    <section class="call-card">
      <div class="call-header">
        <h3>{esc(record.get("customer") or "Unknown customer")}</h3>
        <span class="badge">{esc(record.get("status") or "captured")}</span>
      </div>
      <dl>
        <dt>Issue</dt><dd>{esc(record.get("issue") or "Not provided")}</dd>
        <dt>Outcome</dt><dd>{esc(record.get("outcome") or "Not provided")}</dd>
        <dt>Next action</dt><dd>{esc(record.get("next_action") or "Not provided")}</dd>
        <dt>Escalation</dt><dd>{esc(record.get("escalation") or "None captured")}</dd>
      </dl>
      <h4>Product signals</h4>
      {product_signals}
      <h4>Follow-ups</h4>
      {followups}
    </section>
    """


def render_html(report: dict[str, Any], report_date: str) -> str:
    records = [item for item in report.get("calls", []) if isinstance(item, dict)]
    resolved = count_where(records, "status", "resolved")
    escalated = count_where(records, "status", "escalated")
    partial = count_where(records, "status", "partial")
    product_signals = sum(len(as_list(record.get("product_signals"))) for record in records)
    title = report.get("title") or "Support Rotation Daily Report"
    verdict = report.get("verdict") or "Daily support activity summarized from provided sources."
    themes = render_list(as_list(report.get("themes")))
    coaching = render_list(as_list(report.get("coaching_opportunities")))
    open_followups = render_list(as_list(report.get("open_followups")))
    methodology = render_list(as_list(report.get("methodology")))
    calls_html = "\n".join(render_call(record) for record in records) or '<p class="muted">No calls captured.</p>'
    generated_at = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)} - {esc(report_date)}</title>
  <style>
    :root {{
      --bg: #0f1117;
      --surface: #1a1d27;
      --surface-hover: #232736;
      --border: #2d3148;
      --text: #e4e4e7;
      --muted: #9ca3af;
      --accent: #6c63ff;
      --teal: #00d4aa;
      --red: #ff6b6b;
      --yellow: #ffd166;
    }}
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; color: var(--text); background: var(--bg); }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 32px 20px 48px; }}
    h1, h2, h3, h4 {{ margin: 0 0 12px; }}
    p {{ line-height: 1.55; }}
    .muted {{ color: var(--muted); }}
    .hero, .panel, .call-card, .kpi-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; }}
    .hero {{ padding: 28px; margin-bottom: 20px; }}
    .kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin: 20px 0; }}
    .kpi-card {{ padding: 16px; }}
    .kpi-label {{ color: var(--muted); font-size: 0.78rem; text-transform: uppercase; }}
    .kpi-value {{ font-size: 1.8rem; font-weight: 700; margin-top: 6px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; }}
    .panel, .call-card {{ padding: 18px; margin-bottom: 14px; }}
    .call-header {{ display: flex; align-items: start; justify-content: space-between; gap: 12px; }}
    .badge {{ color: var(--teal); border: 1px solid rgba(0, 212, 170, .35); border-radius: 999px; padding: 3px 9px; font-size: .8rem; }}
    dl {{ display: grid; grid-template-columns: 120px 1fr; gap: 8px 12px; }}
    dt {{ color: var(--muted); }}
    dd {{ margin: 0; }}
    li {{ margin: 6px 0; }}
    footer {{ color: var(--muted); margin-top: 24px; font-size: .9rem; }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <p class="muted">{esc(report_date)}</p>
      <h1>{esc(title)}</h1>
      <p>{esc(verdict)}</p>
    </section>
    <section class="kpis">
      <div class="kpi-card"><div class="kpi-label">Interactions</div><div class="kpi-value">{len(records)}</div></div>
      <div class="kpi-card"><div class="kpi-label">Resolved</div><div class="kpi-value">{resolved}</div></div>
      <div class="kpi-card"><div class="kpi-label">Partial</div><div class="kpi-value">{partial}</div></div>
      <div class="kpi-card"><div class="kpi-label">Escalated</div><div class="kpi-value">{escalated}</div></div>
      <div class="kpi-card"><div class="kpi-label">Product Signals</div><div class="kpi-value">{product_signals}</div></div>
    </section>
    <section>
      <h2>Calls And Chats</h2>
      {calls_html}
    </section>
    <section class="grid">
      <div class="panel"><h2>Themes</h2>{themes}</div>
      <div class="panel"><h2>Coaching Opportunities</h2>{coaching}</div>
      <div class="panel"><h2>Open Follow-ups</h2>{open_followups}</div>
      <div class="panel"><h2>Methodology</h2>{methodology}</div>
    </section>
    <footer>Generated by Intercom Assistant at {esc(generated_at)}.</footer>
  </main>
</body>
</html>
"""


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="JSON file with normalized daily call records.")
    parser.add_argument("--date", default=dt.date.today().isoformat())
    parser.add_argument("--output", required=True, help="HTML output path.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    data = json.loads(Path(args.input).read_text())
    output = Path(args.output)
    output.write_text(render_html(data, args.date))
    print(f"HTML report saved to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
