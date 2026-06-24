#!/usr/bin/env python3
"""Render an HTML report from Ideation Log entries exported as JSON."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
SINCE_RE = re.compile(r"^(\d+)([dwm])$")


@dataclass
class Idea:
    title: str
    status: str
    impact: str
    effort: str
    product_area: str
    entry_type: str
    date: datetime | None
    description: str
    url: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render support-rotation ideas as HTML.")
    parser.add_argument("--input", required=True, help="JSON file containing Notion pages or idea rows.")
    parser.add_argument("--output", required=True, help="HTML report path to write.")
    parser.add_argument(
        "--since",
        default="1w",
        help="Timeframe: all, Nd, Nw, Nm, or YYYY-MM-DD. Default: 1w.",
    )
    parser.add_argument("--title", default="Support Rotation Ideas", help="Report title.")
    parser.add_argument(
        "--now",
        default="",
        help="Override current time for tests, e.g. 2026-06-15T12:00:00Z.",
    )
    return parser.parse_args()


def as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        parts = [as_text(item) for item in value]
        return ", ".join(part for part in parts if part)
    if isinstance(value, dict):
        if "plain_text" in value:
            return as_text(value.get("plain_text"))
        if "name" in value:
            return as_text(value.get("name"))
        if "title" in value:
            return as_text(value.get("title"))
        if "rich_text" in value:
            return as_text(value.get("rich_text"))
        if "select" in value:
            return as_text(value.get("select"))
        if "multi_select" in value:
            return as_text(value.get("multi_select"))
        if "date" in value:
            date = value.get("date") or {}
            return as_text(date.get("start") or date.get("end"))
        if "url" in value:
            return as_text(value.get("url"))
        if "checkbox" in value:
            return as_text(value.get("checkbox"))
    return str(value).strip()


def first_value(row: dict[str, Any], names: list[str]) -> str:
    properties = row.get("properties") if isinstance(row.get("properties"), dict) else row
    for name in names:
        if name in properties:
            text = as_text(properties[name])
            if text:
                return text
    return ""


def parse_date(value: str) -> datetime | None:
    if not value:
        return None
    match = DATE_RE.search(value)
    if not match:
        return None
    text = match.group(0)
    try:
        return datetime.fromisoformat(text).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def parse_now(value: str) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    text = value.replace("Z", "+00:00")
    return datetime.fromisoformat(text).astimezone(timezone.utc)


def since_cutoff(value: str, now: datetime) -> datetime | None:
    if value == "all":
        return None
    match = SINCE_RE.match(value)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        days = amount if unit == "d" else amount * 7 if unit == "w" else amount * 30
        return now - timedelta(days=days)
    parsed = parse_date(value)
    if parsed:
        return parsed
    raise ValueError("--since must be all, Nd, Nw, Nm, or YYYY-MM-DD")


def load_rows(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text())
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if isinstance(data, dict) and isinstance(data.get("results"), list):
        return [row for row in data["results"] if isinstance(row, dict)]
    raise ValueError("Input JSON must be a list or an object with a results array.")


def normalize(row: dict[str, Any]) -> Idea:
    date_text = first_value(row, ["Date", "date", "Created", "created_time", "Last edited time"])
    title = first_value(row, ["Idea Name", "Name", "Observation Title", "Title", "title"]) or "Untitled idea"
    return Idea(
        title=title,
        status=first_value(row, ["Status", "status"]) or "Unknown",
        impact=first_value(row, ["Impact Level", "Impact", "impact"]) or "Unknown",
        effort=first_value(row, ["Effort to Fix", "Effort", "effort"]) or "Unknown",
        product_area=first_value(row, ["Product Area", "Area", "product_area"]) or "Unknown",
        entry_type=first_value(row, ["Entry Type", "Type", "entry_type"]) or "Unknown",
        date=parse_date(date_text),
        description=first_value(row, ["Description", "Observation", "description"]) or "",
        url=as_text(row.get("url") or first_value(row, ["URL", "Notion URL", "url"])),
    )


def in_scope(idea: Idea, cutoff: datetime | None) -> bool:
    if cutoff is None:
        return True
    if idea.date is None:
        return False
    return idea.date >= cutoff


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def count_list(title: str, counts: Counter[str]) -> str:
    items = "".join(
        f"<li><span>{esc(name)}</span><strong>{count}</strong></li>"
        for name, count in counts.most_common()
    )
    return f"<section><h2>{esc(title)}</h2><ul class=\"counts\">{items or '<li>No data</li>'}</ul></section>"


def render(ideas: list[Idea], title: str, since: str, now: datetime) -> str:
    status = Counter(idea.status for idea in ideas)
    impact = Counter(idea.impact for idea in ideas)
    entry_type = Counter(idea.entry_type for idea in ideas)
    product_area = Counter(idea.product_area for idea in ideas)
    candidates = [
        idea
        for idea in ideas
        if idea.impact.lower() == "high" and idea.effort.lower() in {"low", "small", "low effort"}
    ]

    rows = []
    for idea in sorted(ideas, key=lambda i: (i.date or datetime.min.replace(tzinfo=timezone.utc)), reverse=True):
        date = idea.date.date().isoformat() if idea.date else "Unknown"
        idea_title_html = esc(idea.title)
        if idea.url:
            idea_title_html = f"<a href=\"{esc(idea.url)}\">{idea_title_html}</a>"
        rows.append(
            "<tr>"
            f"<td>{esc(date)}</td>"
            f"<td>{idea_title_html}</td>"
            f"<td>{esc(idea.status)}</td>"
            f"<td>{esc(idea.impact)}</td>"
            f"<td>{esc(idea.effort)}</td>"
            f"<td>{esc(idea.product_area)}</td>"
            f"<td>{esc(idea.entry_type)}</td>"
            f"<td>{esc(idea.description[:220])}</td>"
            "</tr>"
        )

    candidate_items = "".join(
        f"<li>{esc(idea.title)} <span>{esc(idea.product_area)} / {esc(idea.effort)}</span></li>"
        for idea in candidates
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<style>
:root {{ color-scheme: light; font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
body {{ margin: 0; background: #f7f7f4; color: #202124; }}
main {{ max-width: 1180px; margin: 0 auto; padding: 32px 24px 48px; }}
header {{ margin-bottom: 24px; }}
h1 {{ font-size: 32px; margin: 0 0 8px; letter-spacing: 0; }}
h2 {{ font-size: 16px; margin: 0 0 12px; }}
.meta {{ color: #5f6368; margin: 0; }}
.summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 12px; margin: 24px 0; }}
section {{ background: #fff; border: 1px solid #dedbd2; border-radius: 8px; padding: 16px; }}
.metric {{ font-size: 36px; font-weight: 700; margin-top: 6px; }}
.counts {{ list-style: none; padding: 0; margin: 0; display: grid; gap: 8px; }}
.counts li {{ display: flex; justify-content: space-between; gap: 16px; border-bottom: 1px solid #eeeae2; padding-bottom: 6px; }}
.candidates li {{ margin: 8px 0; }}
.candidates span {{ color: #5f6368; }}
table {{ width: 100%; border-collapse: collapse; background: #fff; border: 1px solid #dedbd2; }}
th, td {{ text-align: left; vertical-align: top; padding: 10px; border-bottom: 1px solid #eeeae2; font-size: 14px; }}
th {{ background: #ebe7dd; font-size: 12px; text-transform: uppercase; letter-spacing: .04em; }}
a {{ color: #1557c0; }}
</style>
</head>
<body>
<main>
<header>
<h1>{esc(title)}</h1>
<p class="meta">Timeframe: {esc(since)}. Generated: {esc(now.isoformat(timespec="seconds"))}. Rows in scope: {len(ideas)}.</p>
</header>
<div class="summary">
<section><h2>Total Ideas</h2><div class="metric">{len(ideas)}</div></section>
{count_list("By Status", status)}
{count_list("By Impact", impact)}
{count_list("By Product Area", product_area)}
{count_list("By Entry Type", entry_type)}
<section><h2>High Impact / Low Effort</h2><ul class="candidates">{candidate_items or "<li>No candidates in scope.</li>"}</ul></section>
</div>
<table>
<thead><tr><th>Date</th><th>Idea</th><th>Status</th><th>Impact</th><th>Effort</th><th>Product Area</th><th>Entry Type</th><th>Description</th></tr></thead>
<tbody>
{''.join(rows) or '<tr><td colspan="8">No ideas matched this timeframe.</td></tr>'}
</tbody>
</table>
</main>
</body>
</html>
"""


def main() -> int:
    args = parse_args()
    now = parse_now(args.now)
    cutoff = since_cutoff(args.since, now)
    rows = load_rows(Path(args.input))
    ideas = [idea for idea in (normalize(row) for row in rows) if in_scope(idea, cutoff)]
    html_text = render(ideas, args.title, args.since, now)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html_text)
    print(f"Wrote {len(ideas)} ideas to {args.output}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
