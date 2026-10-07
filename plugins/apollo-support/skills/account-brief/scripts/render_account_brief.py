#!/usr/bin/env python3
"""Render a self-contained account brief from a JSON payload.

Slack mrkdwn with --slack, Markdown by default, HTML with --html, or every
artifact at once with --bundle. Stdlib only (no templating library).

Guiding rule: never fabricate. Render only the fields present in the payload.
For a known field that is missing, show the explicit placeholder
"unknown / needs checking" so a reader never mistakes a gap for a fact.

Data-source caveats render at the top of every format, never at the bottom. A
reader who stops after the first few lines still learns which sources were
missing and which numbers they should not trust.
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

# A source is only clean when it explicitly says so. Anything else (missing,
# partial, never queried, unknown) produces a visible caveat.
CLEAN_SOURCE_STATUSES = {"ok", "available", "verified"}

# Slack section blocks cut off past 3000 characters. Stay under that so the
# summary is never silently truncated mid-flag by Slack itself.
SLACK_CHAR_BUDGET = 2600
SLACK_MAX_FLAGS = 5
SLACK_MAX_TICKETS = 5
SLACK_MAX_ACTIVITY = 3


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
# Data-source caveats (shared by every format)
# --------------------------------------------------------------------------- #


def degraded_sources(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the sources that did not come back clean, in payload order."""
    return [
        source
        for source in as_list(payload.get("sources"))
        if isinstance(source, dict)
        and str(source.get("status", "")).strip().lower() not in CLEAN_SOURCE_STATUSES
    ]


def caveat_lines(payload: dict[str, Any]) -> list[str]:
    """Plain-text caveat lines: one per degraded source, then any free-text caveats.

    Free-text caveats carry the things a status field cannot, most often
    freshness: "Intercom pulled at 09:00 PT, later conversations not included".
    """
    lines = []
    for source in degraded_sources(payload):
        name = field(source, "name")
        status = str(source.get("status", "")).strip() or UNKNOWN
        impact = source.get("impact")
        text = f"{name} {status}"
        if present(impact):
            text += f": {str(impact).strip()}"
        lines.append(text)
    lines.extend(str(item).strip() for item in as_list(payload.get("caveats")) if present(item))
    return lines


def coverage_headline(payload: dict[str, Any]) -> str:
    """One line stating how complete this brief is, shown even when nothing is missing."""
    sources = [source for source in as_list(payload.get("sources")) if isinstance(source, dict)]
    degraded = degraded_sources(payload)
    extra = len([item for item in as_list(payload.get("caveats")) if present(item)])

    if not sources and not extra:
        return "Source coverage not recorded. Treat every field as unverified until you confirm it."
    if not degraded and not extra:
        return f"All {len(sources)} data sources returned. No coverage gaps recorded."
    parts = []
    if degraded:
        parts.append(f"{len(degraded)} of {len(sources)} data sources incomplete")
    if extra:
        parts.append(f"{extra} freshness caveat{'s' if extra != 1 else ''}")
    return ", ".join(parts).capitalize() + ". Fields below may be stale or unverified."


def _md_caveats(payload: dict[str, Any]) -> list[str]:
    lines = ["## Data Coverage And Caveats", "", coverage_headline(payload), ""]
    caveats = caveat_lines(payload)
    lines.extend(f"- {text}" for text in caveats)
    if caveats:
        lines.append("")
    return lines


def _html_caveats(payload: dict[str, Any]) -> str:
    items = "".join(f"<li>{esc(text)}</li>" for text in caveat_lines(payload))
    body = f"<ul>{items}</ul>" if items else ""
    tone = "warn" if (degraded_sources(payload) or items) else "ok"
    return (
        f"<section class='caveats caveats-{tone}'>"
        "<h2>Data Coverage And Caveats</h2>"
        f"<p><strong>{esc(coverage_headline(payload))}</strong></p>{body}</section>"
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
    lines += _md_caveats(payload)
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
    .caveats {{ border-left:4px solid var(--border); }}
    .caveats-warn {{ border-left-color:var(--p1); background:#241f16; }}
    .caveats ul {{ margin:8px 0 0; padding-left:20px; }}
    .caveats li {{ padding:2px 0; }}
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
    {_html_caveats(payload)}
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
# Slack renderer
# --------------------------------------------------------------------------- #
#
# Slack does not speak Markdown. It uses mrkdwn: *bold* (not **bold**), no `#`
# headers, and no pipe tables. Pasting the Markdown or HTML brief into a thread
# is what produced the unreadable output this format exists to replace.


def _slack_truncate(rows: list[str], limit: int, noun: str) -> list[str]:
    """Cap a list and say plainly how many rows moved to the attachment."""
    if len(rows) <= limit:
        return rows
    hidden = len(rows) - limit
    return rows[:limit] + [f"_+{hidden} more {noun} in the attached brief._"]


def _slack_ticket(ticket: dict[str, Any]) -> str:
    severity = field(ticket, "severity")
    age = field(ticket, "age_days")
    age_text = f"{age}d" if age != UNKNOWN else UNKNOWN
    return (
        f"• `{severity}` *{field(ticket, 'id')}* {field(ticket, 'subject')} "
        f"· {field(ticket, 'status')} · {age_text} · {field(ticket, 'owner')}"
    )


def render_slack(payload: dict[str, Any], attachments: Sequence[str] | None = None) -> str:
    """Render a concise Slack-native summary that stands alone if attachments fail.

    This is the message body, not the whole brief: enough for an AM to act on or
    decide to open the attachment, with caveats above the numbers they qualify.
    """
    account = payload.get("account") if isinstance(payload.get("account"), dict) else {}
    health = payload.get("health") if isinstance(payload.get("health"), dict) else {}
    mode = "daily" if str(payload.get("mode", "")).lower() == "daily" else "brief"
    title = "Daily Ticket Summary" if mode == "daily" else "Account Brief"
    generated = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [f"*{title}: {field(account, 'name')}*"]
    subtitle = [f"Generated {generated}"]
    if present(account.get("domain")):
        subtitle.append(str(account["domain"]).strip())
    if present(payload.get("data_window")):
        subtitle.append(f"Window: {str(payload['data_window']).strip()}")
    lines.append(f"_{' · '.join(subtitle)}_")
    lines.append("")

    # Caveats sit directly under the title, above every number they qualify.
    caveats = caveat_lines(payload)
    marker = ":warning: " if (degraded_sources(payload) or caveats) else ""
    lines.append(f"{marker}*Data coverage:* {coverage_headline(payload)}")
    lines.extend(f"• {text}" for text in _slack_truncate(caveats, 4, "caveats"))
    lines.append("")

    lines.append("*Health*")
    for label, key in (
        ("Status", "status"),
        ("Renewal risk", "renewal_risk"),
        ("CSAT", "csat"),
        ("Usage trend", "usage_trend"),
    ):
        lines.append(f"• {label}: {field(health, key)}")
    if present(health.get("notes")):
        lines.append(f"• Notes: {str(health['notes']).strip()}")
    lines.append("")

    flags = sort_flags(as_list(payload.get("red_flags")))
    lines.append(f"*Red flags ({len(flags)})*")
    if flags:
        rendered = [
            f"• `{str(flag.get('tier', '')).upper() or UNKNOWN}` *{field(flag, 'signal')}*: "
            f"{field(flag, 'detail')} (source: {field(flag, 'source')})"
            for flag in flags
        ]
        lines.extend(_slack_truncate(rendered, SLACK_MAX_FLAGS, "flags"))
    else:
        lines.append("• No red-flag signals recorded.")
    lines.append("")

    tickets = [ticket for ticket in as_list(payload.get("open_tickets")) if isinstance(ticket, dict)]
    lines.append(f"*Open tickets ({len(tickets)})*")
    if tickets:
        lines.extend(_slack_truncate([_slack_ticket(ticket) for ticket in tickets], SLACK_MAX_TICKETS, "tickets"))
    else:
        lines.append("• No open support tickets recorded.")

    activity = [entry for entry in as_list(payload.get("recent_activity")) if present(entry)]
    if activity:
        lines.append("")
        lines.append("*Recent activity*")
        rendered = [
            f"• *{field(entry, 'when')}:* {field(entry, 'summary')}"
            if isinstance(entry, dict)
            else f"• {str(entry).strip()}"
            for entry in activity
        ]
        lines.extend(_slack_truncate(rendered, SLACK_MAX_ACTIVITY, "entries"))

    files = [name for name in (attachments or []) if str(name).strip()]
    lines.append("")
    if files:
        lines.append(f"_Full brief attached: {', '.join(files)}._")
    else:
        lines.append("_No attachment rendered. This summary is the complete output for this run._")

    text = "\n".join(lines)
    if len(text) > SLACK_CHAR_BUDGET:
        text = text[:SLACK_CHAR_BUDGET].rsplit("\n", 1)[0] + "\n_Summary truncated. See the attached brief._"
    return text


# --------------------------------------------------------------------------- #
# Bundle: every Slack artifact in one call
# --------------------------------------------------------------------------- #


def render_bundle(payload: dict[str, Any], outdir: Path, slug: str = "account-brief") -> dict[str, Any]:
    """Write Markdown, HTML, PNG, and the Slack summary into outdir.

    Returns a manifest naming what was written and, when the PNG could not be
    built, why. PNG failure degrades the bundle; it never fails it.
    """
    outdir.mkdir(parents=True, exist_ok=True)
    html_path = outdir / f"{slug}.html"
    md_path = outdir / f"{slug}.md"
    png_path = outdir / f"{slug}.png"

    md_path.write_text(render_markdown(payload))
    html_path.write_text(render_html(payload))

    try:
        script_dir = str(Path(__file__).resolve().parent)
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)
        from render_png import render_png  # local sibling script

        png_ok, png_detail = render_png(html_path, png_path)
    except Exception as exc:  # noqa: BLE001 - a missing renderer degrades the bundle, never fails it
        png_ok, png_detail = False, f"PNG step unavailable: {type(exc).__name__}: {exc}"

    # Attach the PNG first: Slack previews it inline, and the HTML is the
    # fallback for anyone who needs to copy text out of it.
    attachments = ([png_path.name] if png_ok else []) + [html_path.name]
    manifest = {
        "outdir": str(outdir),
        "markdown": str(md_path),
        "html": str(html_path),
        "png": str(png_path) if png_ok else None,
        "png_detail": png_detail,
        "attachments": attachments,
        "slack_text": render_slack(payload, attachments),
    }
    (outdir / f"{slug}.slack.txt").write_text(manifest["slack_text"])
    manifest["slack_file"] = str(outdir / f"{slug}.slack.txt")
    return manifest


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
    # One output format per run. Without this, --slack --html would silently
    # ignore one of them instead of saying which output you actually get.
    formats = parser.add_mutually_exclusive_group()
    formats.add_argument("--html", action="store_true", help="Render HTML instead of Markdown.")
    formats.add_argument("--slack", action="store_true", help="Render a concise Slack mrkdwn summary.")
    formats.add_argument(
        "--bundle",
        default=None,
        metavar="DIR",
        help="Write Markdown, HTML, PNG, and Slack summary into DIR and print a JSON manifest.",
    )
    parser.add_argument("--slug", default="account-brief", help="Filename stem for --bundle (default: account-brief).")
    parser.add_argument(
        "--attach",
        action="append",
        default=None,
        metavar="NAME",
        help="Attachment filename to cite in the --slack footer. Repeatable.",
    )
    parser.add_argument("--output", default=None, help="Write to this path instead of stdout.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    payload = load_payload(args.json)

    if args.bundle:
        manifest = render_bundle(payload, Path(args.bundle), args.slug)
        print(json.dumps(manifest, indent=2))
        return 0

    if args.slack:
        rendered = render_slack(payload, args.attach)
    elif args.html:
        rendered = render_html(payload)
    else:
        rendered = render_markdown(payload)

    if args.output:
        Path(args.output).write_text(rendered)
        print(f"Account brief saved to {args.output}")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
