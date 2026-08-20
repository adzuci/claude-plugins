#!/usr/bin/env python3
"""Render a self-contained account brief from a JSON payload.

Markdown by default, HTML with --html. Stdlib only (no templating library).

Guiding rule: never fabricate. Render only the fields present in the payload.
For a known field that is missing, show the explicit placeholder
"unknown / needs checking" so a reader never mistakes a gap for a fact.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import sys
from pathlib import Path
from typing import Any, Sequence

UNKNOWN = "unknown / needs checking"
TIER_ORDER = {"P0": 0, "P1": 1, "P2": 2}


def esc(value: Any) -> str:
    """HTML-escape a value; None becomes an empty string."""
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def as_list(value: Any) -> list[Any]:
    """Coerce a value to a list; None -> [], scalar -> single-item list."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def present(value: Any) -> bool:
    """True only when a value carries real content (not None or blank string)."""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def field(record: dict[str, Any], key: str) -> str:
    """Return a record field as text, or the explicit unknown placeholder."""
    value = record.get(key)
    return str(value).strip() if present(value) else UNKNOWN


def sort_flags(flags: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Order red-flag signals by tier (P0 first), preserving input order within a tier."""
    return sorted(
        (flag for flag in flags if isinstance(flag, dict)),
        key=lambda flag: TIER_ORDER.get(str(flag.get("tier", "")).upper(), 99),
    )


# --------------------------------------------------------------------------- #
# Markdown renderer
# --------------------------------------------------------------------------- #


def _md_header(account: dict[str, Any], mode: str) -> list[str]:
    name = field(account, "name")
    title = "Daily Ticket Summary" if mode == "daily" else "Account Brief"
    lines = [f"# {title}: {name}", ""]
    meta = [
        ("Account id", field(account, "id")),
        ("Domain", field(account, "domain")),
        ("Account Manager", field(account, "am")),
        ("CSM", field(account, "csm")),
        ("Plan", field(account, "plan")),
        ("ARR", field(account, "arr")),
        ("Renewal date", field(account, "renewal_date")),
    ]
    for label, value in meta:
        lines.append(f"- **{label}:** {value}")
    lines.append("")
    return lines


def _md_health(health: dict[str, Any]) -> list[str]:
    lines = ["## Health Summary", ""]
    labels = [
        ("Overall status", "status"),
        ("Renewal risk", "renewal_risk"),
        ("CSAT", "csat"),
        ("Usage trend", "usage_trend"),
        ("Notes", "notes"),
    ]
    for label, key in labels:
        lines.append(f"- **{label}:** {field(health, key)}")
    lines.append("")
    return lines


def _md_tickets(tickets: list[dict[str, Any]]) -> list[str]:
    lines = ["## Open Support Tickets", ""]
    rows = [ticket for ticket in tickets if isinstance(ticket, dict)]
    if not rows:
        lines += ["No open support tickets recorded.", ""]
        return lines
    lines.append("| Ticket | Subject | Severity | Status | Age (days) | Owner |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for ticket in rows:
        lines.append(
            "| {id} | {subject} | {severity} | {status} | {age} | {owner} |".format(
                id=field(ticket, "id"),
                subject=field(ticket, "subject"),
                severity=field(ticket, "severity"),
                status=field(ticket, "status"),
                age=field(ticket, "age_days"),
                owner=field(ticket, "owner"),
            )
        )
    lines.append("")
    return lines


def _md_flags(flags: list[dict[str, Any]]) -> list[str]:
    lines = ["## Red-Flag Signals", ""]
    ordered = sort_flags(flags)
    if not ordered:
        lines += ["No red-flag signals recorded.", ""]
        return lines
    for flag in ordered:
        tier = str(flag.get("tier", "")).upper() or UNKNOWN
        signal = field(flag, "signal")
        detail = field(flag, "detail")
        source = field(flag, "source")
        lines.append(f"- **[{tier}] {signal}**: {detail} (source: {source})")
    lines.append("")
    return lines


def _md_activity(activity: list[Any]) -> list[str]:
    lines = ["## Recent Activity", ""]
    entries = [entry for entry in activity if present(entry)]
    if not entries:
        lines += ["No recent activity recorded.", ""]
        return lines
    for entry in entries:
        if isinstance(entry, dict):
            when = field(entry, "when")
            summary = field(entry, "summary")
            source = field(entry, "source")
            lines.append(f"- **{when}:** {summary} (source: {source})")
        else:
            lines.append(f"- {str(entry).strip()}")
    lines.append("")
    return lines


def render_markdown(payload: dict[str, Any]) -> str:
    """Render the full brief (or daily summary) as Markdown from a payload dict."""
    account = payload.get("account") if isinstance(payload.get("account"), dict) else {}
    health = payload.get("health") if isinstance(payload.get("health"), dict) else {}
    mode = "daily" if str(payload.get("mode", "")).lower() == "daily" else "brief"

    lines: list[str] = []
    lines += _md_header(account, mode)
    lines += _md_health(health)
    lines += _md_tickets(as_list(payload.get("open_tickets")))
    lines += _md_flags(as_list(payload.get("red_flags")))
    lines += _md_activity(as_list(payload.get("recent_activity")))

    generated = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines.append(f"_Generated by account-brief at {generated}. Fields marked \"{UNKNOWN}\" were not in the payload._")
    lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# HTML renderer
# --------------------------------------------------------------------------- #


def _html_kv(label: str, value: str) -> str:
    return f"<div class='kv'><span>{esc(label)}</span><strong>{esc(value)}</strong></div>"


def _html_tickets(tickets: list[dict[str, Any]]) -> str:
    rows = [ticket for ticket in tickets if isinstance(ticket, dict)]
    if not rows:
        return "<p class='muted'>No open support tickets recorded.</p>"
    body = ""
    for ticket in rows:
        body += (
            "<tr>"
            f"<td>{esc(field(ticket, 'id'))}</td>"
            f"<td>{esc(field(ticket, 'subject'))}</td>"
            f"<td>{esc(field(ticket, 'severity'))}</td>"
            f"<td>{esc(field(ticket, 'status'))}</td>"
            f"<td>{esc(field(ticket, 'age_days'))}</td>"
            f"<td>{esc(field(ticket, 'owner'))}</td>"
            "</tr>"
        )
    return (
        "<table><thead><tr>"
        "<th>Ticket</th><th>Subject</th><th>Severity</th><th>Status</th><th>Age (days)</th><th>Owner</th>"
        f"</tr></thead><tbody>{body}</tbody></table>"
    )


def _html_flags(flags: list[dict[str, Any]]) -> str:
    ordered = sort_flags(flags)
    if not ordered:
        return "<p class='muted'>No red-flag signals recorded.</p>"
    items = ""
    for flag in ordered:
        tier = str(flag.get("tier", "")).upper() or UNKNOWN
        tier_class = tier.lower() if tier in TIER_ORDER else "unknown"
        items += (
            f"<li><span class='tier tier-{tier_class}'>{esc(tier)}</span> "
            f"<strong>{esc(field(flag, 'signal'))}</strong>: {esc(field(flag, 'detail'))} "
            f"<span class='muted'>(source: {esc(field(flag, 'source'))})</span></li>"
        )
    return f"<ul class='flags'>{items}</ul>"


def _html_activity(activity: list[Any]) -> str:
    entries = [entry for entry in activity if present(entry)]
    if not entries:
        return "<p class='muted'>No recent activity recorded.</p>"
    items = ""
    for entry in entries:
        if isinstance(entry, dict):
            items += (
                f"<li><strong>{esc(field(entry, 'when'))}:</strong> {esc(field(entry, 'summary'))} "
                f"<span class='muted'>(source: {esc(field(entry, 'source'))})</span></li>"
            )
        else:
            items += f"<li>{esc(str(entry).strip())}</li>"
    return f"<ul>{items}</ul>"


def render_html(payload: dict[str, Any]) -> str:
    """Render a complete self-contained HTML document from a payload dict."""
    account = payload.get("account") if isinstance(payload.get("account"), dict) else {}
    health = payload.get("health") if isinstance(payload.get("health"), dict) else {}
    mode = "daily" if str(payload.get("mode", "")).lower() == "daily" else "brief"
    title = "Daily Ticket Summary" if mode == "daily" else "Account Brief"
    name = field(account, "name")
    generated = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    meta_html = "".join(
        _html_kv(label, field(account, key))
        for label, key in (
            ("Account id", "id"),
            ("Domain", "domain"),
            ("Account Manager", "am"),
            ("CSM", "csm"),
            ("Plan", "plan"),
            ("ARR", "arr"),
            ("Renewal date", "renewal_date"),
        )
    )
    health_html = "".join(
        _html_kv(label, field(health, key))
        for label, key in (
            ("Overall status", "status"),
            ("Renewal risk", "renewal_risk"),
            ("CSAT", "csat"),
            ("Usage trend", "usage_trend"),
            ("Notes", "notes"),
        )
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}: {esc(name)}</title>
  <style>
    :root {{ --bg:#0f1117; --surface:#1a1d27; --border:#2d3148; --text:#e4e4e7; --muted:#9ca3af; --accent:#6c63ff; --p0:#ff6b6b; --p1:#ffb454; --p2:#ffd166; }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif; color:var(--text); background:var(--bg); }}
    main {{ max-width:960px; margin:0 auto; padding:32px 20px 48px; }}
    h1,h2 {{ margin:0 0 12px; }}
    section {{ background:var(--surface); border:1px solid var(--border); border-radius:8px; padding:18px; margin-bottom:16px; }}
    .muted {{ color:var(--muted); }}
    .kv-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:10px; }}
    .kv {{ border:1px solid var(--border); border-radius:8px; padding:10px; }}
    .kv span {{ display:block; color:var(--muted); font-size:.75rem; text-transform:uppercase; }}
    .kv strong {{ display:block; margin-top:4px; }}
    table {{ width:100%; border-collapse:collapse; margin-top:8px; }}
    th,td {{ text-align:left; padding:8px 10px; border-bottom:1px solid var(--border); }}
    th {{ color:var(--muted); font-size:.75rem; text-transform:uppercase; }}
    ul.flags {{ list-style:none; padding:0; }}
    ul.flags li {{ padding:8px 0; border-bottom:1px solid var(--border); }}
    .tier {{ display:inline-block; border-radius:999px; padding:2px 8px; font-size:.72rem; font-weight:700; color:#111; margin-right:6px; }}
    .tier-p0 {{ background:var(--p0); }} .tier-p1 {{ background:var(--p1); }} .tier-p2 {{ background:var(--p2); }}
    .tier-unknown {{ background:var(--border); color:var(--text); }}
    footer {{ color:var(--muted); font-size:.85rem; margin-top:16px; }}
  </style>
</head>
<body>
  <main>
    <section>
      <p class="muted">{esc(generated)}</p>
      <h1>{esc(title)}: {esc(name)}</h1>
      <div class="kv-grid">{meta_html}</div>
    </section>
    <section>
      <h2>Health Summary</h2>
      <div class="kv-grid">{health_html}</div>
    </section>
    <section>
      <h2>Open Support Tickets</h2>
      {_html_tickets(as_list(payload.get("open_tickets")))}
    </section>
    <section>
      <h2>Red-Flag Signals</h2>
      {_html_flags(as_list(payload.get("red_flags")))}
    </section>
    <section>
      <h2>Recent Activity</h2>
      {_html_activity(as_list(payload.get("recent_activity")))}
    </section>
    <footer>Generated by account-brief at {esc(generated)}. Fields marked "{esc(UNKNOWN)}" were not in the payload.</footer>
  </main>
</body>
</html>
"""


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def load_payload(json_arg: str | None) -> dict[str, Any]:
    """Load the payload from a file path, or from stdin when path is '-' or omitted."""
    if json_arg and json_arg != "-":
        raw = Path(json_arg).read_text()
    else:
        raw = sys.stdin.read()
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("payload must be a JSON object")
    return data


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", default=None, help="Path to the JSON payload, or '-' for stdin (default: stdin).")
    parser.add_argument("--html", action="store_true", help="Render HTML instead of Markdown.")
    parser.add_argument("--output", default=None, help="Write to this path instead of stdout.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    payload = load_payload(args.json)
    rendered = render_html(payload) if args.html else render_markdown(payload)
    if args.output:
        Path(args.output).write_text(rendered)
        print(f"Account brief saved to {args.output}")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
