#!/usr/bin/env python3
"""Render a self-contained HTML report for a day of support calls."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
from pathlib import Path
from typing import Any, Sequence


# Matches transcript lines like: [00:00:02] Speaker 1: "text".
# Speaker is kept broad ([^:]{1,60}) to handle names with punctuation; lines that
# don't match (e.g. long URL prefixes) fall through to the verbatim path below.
TRANSCRIPT_LINE = re.compile(
    r"^\s*(?:\[(?P<time>[^\]]+)\]\s*)?(?P<speaker>[^:]{1,60}?):\s*(?P<text>.*)$"
)


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


def parse_transcript(raw: str) -> list[dict[str, str]]:
    """Parse a raw call/chat transcript into structured timeline entries."""
    entries: list[dict[str, str]] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        match = TRANSCRIPT_LINE.match(line)
        if match:
            entries.append(
                {
                    "time": (match.group("time") or "").strip(),
                    "speaker": match.group("speaker").strip(),
                    "text": match.group("text").strip().strip('"'),
                }
            )
        else:
            # Keep unparseable lines as continuation text so nothing is dropped.
            entries.append({"time": "", "speaker": "", "text": line.strip()})
    return entries


def normalize_timeline(record: dict[str, Any]) -> list[dict[str, str]]:
    """Build timeline entries from a structured `timeline` list or raw `transcript`."""
    timeline = record.get("timeline")
    if isinstance(timeline, list) and timeline:
        normalized: list[dict[str, str]] = []
        for entry in timeline:
            if isinstance(entry, dict):
                normalized.append(
                    {
                        "time": str(entry.get("time") or "").strip(),
                        "speaker": str(entry.get("speaker") or "").strip(),
                        "text": str(entry.get("text") or "").strip(),
                    }
                )
            elif str(entry).strip():
                normalized.append({"time": "", "speaker": "", "text": str(entry).strip()})
        return normalized
    transcript = record.get("transcript")
    if isinstance(transcript, str) and transcript.strip():
        return parse_transcript(transcript)
    return []


def render_timeline(record: dict[str, Any]) -> str:
    entries = normalize_timeline(record)
    if not entries:
        return ""
    rows = []
    for entry in entries:
        time = esc(entry.get("time"))
        speaker = esc(entry.get("speaker"))
        text = esc(entry.get("text"))
        meta = " · ".join(part for part in (time, speaker) if part)
        meta_html = f'<span class="tl-meta">{meta}</span>' if meta else ""
        rows.append(f'<li>{meta_html}<span class="tl-text">{text}</span></li>')
    label = record.get("timeline_label") or "Full chat & call timeline"
    return f"""
      <details class="timeline">
        <summary>{esc(label)} ({len(entries)})</summary>
        <ol class="tl">{"".join(rows)}</ol>
      </details>"""


def render_call(record: dict[str, Any]) -> str:
    product_signals = render_list(as_list(record.get("product_signals")))
    followups = render_list(as_list(record.get("followups")))
    timeline = render_timeline(record)
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
      {timeline}
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
    .timeline {{ margin-top: 14px; border-top: 1px solid var(--border); padding-top: 12px; }}
    .timeline summary {{ cursor: pointer; color: var(--accent); font-weight: 600; }}
    .timeline summary:hover {{ color: var(--teal); }}
    ol.tl {{ margin: 12px 0 0; padding-left: 18px; }}
    ol.tl li {{ margin: 8px 0; }}
    .tl-meta {{ display: block; color: var(--muted); font-size: .78rem; }}
    .tl-text {{ display: block; }}
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
