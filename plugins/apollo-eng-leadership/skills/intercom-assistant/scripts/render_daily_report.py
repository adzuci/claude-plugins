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
    """HTML-escape a value, returning an empty string for None."""
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def as_list(value: Any) -> list[Any]:
    """Coerce a value to a list; None becomes [], scalars become single-item lists."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def count_where(records: list[dict[str, Any]], key: str, value: str) -> int:
    """Count records where record[key].lower() == value."""
    return sum(1 for record in records if str(record.get(key, "")).lower() == value)


def render_list(items: list[Any]) -> str:
    """Render a list of items as an HTML <ul>, or a muted placeholder when empty."""
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
    """Render a collapsible HTML timeline from a record's timeline or transcript data."""
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


def first_nonempty(*values: Any) -> str:
    """Return the first non-empty value as a string."""
    for value in values:
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def format_duration(record: dict[str, Any]) -> str:
    """Format a duration from a record's explicit label or minute count."""
    label = first_nonempty(record.get("duration_label"), record.get("call_duration"))
    if label:
        return label
    minutes = record.get("duration_minutes")
    if minutes is None:
        return ""
    try:
        total = int(round(float(minutes)))
    except (TypeError, ValueError):
        return str(minutes)
    hours, mins = divmod(total, 60)
    if hours:
        return f"{hours}h {mins}m" if mins else f"{hours}h"
    return f"{mins}m"


def parse_clock_minutes(value: Any) -> int | None:
    """Parse common local clock labels into minutes after midnight."""
    if value is None:
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", text)
    if not match:
        return None
    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    suffix = match.group(3)
    if suffix == "pm" and hour != 12:
        hour += 12
    elif suffix == "am" and hour == 12:
        hour = 0
    return hour * 60 + minute


def activity_entries(report: dict[str, Any], records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return explicit activity entries or derive them from call records."""
    raw = report.get("activity_timeline")
    if isinstance(raw, list) and raw:
        return [entry for entry in raw if isinstance(entry, dict)]
    derived: list[dict[str, Any]] = []
    for record in records:
        if any(record.get(key) for key in ("start_time", "end_time", "duration_minutes", "duration_label", "channel", "included_call", "csat")):
            derived.append(
                {
                    "label": record.get("customer"),
                    "customer": record.get("customer"),
                    "channel": record.get("channel"),
                    "start_time": record.get("start_time"),
                    "end_time": record.get("end_time"),
                    "duration_minutes": record.get("duration_minutes"),
                    "duration_label": record.get("duration_label"),
                    "status": record.get("status"),
                    "included_call": record.get("included_call"),
                    "csat": record.get("csat"),
                }
            )
    return derived


def csat_label(value: Any) -> str:
    """Return a compact CSAT label for a top-level summary or record."""
    if value is None or value == "":
        return ""
    if isinstance(value, dict):
        label = first_nonempty(value.get("label"), value.get("score"), value.get("rating"))
        rated = value.get("rated")
        total = value.get("total")
        if label and rated is not None and total is not None:
            return f"{label} ({rated}/{total})"
        return label
    return str(value)


def is_csat_captured(value: Any) -> bool:
    """Return True only for actual CSAT values, not explicit missing labels."""
    label = csat_label(value).strip().lower()
    missing = {"", "not captured", "not captured (0/0)", "n/a", "na", "none", "unknown"}
    return label not in missing


def render_record_meta(record: dict[str, Any]) -> str:
    """Render compact metadata chips for a call/chat/shadow record."""
    chips: list[str] = []
    channel = first_nonempty(record.get("channel"))
    duration = format_duration(record)
    start = first_nonempty(record.get("start_time"))
    end = first_nonempty(record.get("end_time"))
    csat = csat_label(record.get("csat"))
    if channel:
        chips.append(channel)
    if start or end:
        chips.append(f"{start} - {end}" if start and end else start or end)
    if duration:
        chips.append(duration)
    if record.get("included_call") is True:
        chips.append("included call")
    elif record.get("included_call") is False:
        chips.append("no call captured")
    if csat:
        chips.append(f"CSAT: {csat}")
    if not chips:
        return ""
    return '<div class="meta-chips">' + "".join(f"<span>{esc(chip)}</span>" for chip in chips) + "</div>"


def render_shift_summary(report: dict[str, Any], records: list[dict[str, Any]]) -> str:
    """Render shift start/end plus call/CSAT coverage."""
    shift = report.get("shift") if isinstance(report.get("shift"), dict) else {}
    start = first_nonempty(shift.get("start"))
    end = first_nonempty(shift.get("end"))
    timezone = first_nonempty(shift.get("timezone"))
    label = first_nonempty(shift.get("label"), "Shift window")
    if not (start or end or timezone):
        return ""

    calls_included = sum(1 for record in records if record.get("included_call") is True)
    chats_or_records = len(records)
    csat = csat_label(report.get("csat_summary")) or "Not captured"
    duration_text = first_nonempty(shift.get("duration_label"))
    if not duration_text:
        start_min = parse_clock_minutes(start)
        end_min = parse_clock_minutes(end)
        if start_min is not None and end_min is not None and end_min >= start_min:
            hours, minutes = divmod(end_min - start_min, 60)
            duration_text = f"{hours}h {minutes}m" if minutes else f"{hours}h"

    stats = [
        ("Start", start or "Unknown"),
        ("End", end or "Unknown"),
        ("Timezone", timezone or "Unknown"),
        ("Duration", duration_text or "Unknown"),
        ("Records", str(chats_or_records)),
        ("Calls included", str(calls_included)),
        ("CSAT", csat),
    ]
    stat_html = "".join(f'<div class="mini-stat"><span>{esc(k)}</span><strong>{esc(v)}</strong></div>' for k, v in stats)
    return f"""
    <section class="panel shift-panel">
      <div class="section-heading">
        <h2>{esc(label)}</h2>
      </div>
      <div class="mini-grid">{stat_html}</div>
    </section>"""


def render_activity_timeline(report: dict[str, Any], records: list[dict[str, Any]]) -> str:
    """Render a visual day timeline of conversations, calls, and durations."""
    entries = activity_entries(report, records)
    if not entries:
        return ""
    shift = report.get("shift") if isinstance(report.get("shift"), dict) else {}
    shift_start = parse_clock_minutes(shift.get("start"))
    shift_end = parse_clock_minutes(shift.get("end"))
    parsed_starts = [parse_clock_minutes(e.get("start_time")) for e in entries]
    parsed_ends = [parse_clock_minutes(e.get("end_time")) for e in entries]
    known_points = [p for p in [shift_start, shift_end, *parsed_starts, *parsed_ends] if p is not None]
    lower = min(known_points) if known_points else 0
    upper = max(known_points) if known_points else lower + 1
    if upper <= lower:
        upper = lower + 1

    rows = []
    for entry in entries:
        start = parse_clock_minutes(entry.get("start_time"))
        end = parse_clock_minutes(entry.get("end_time"))
        duration_label = format_duration(entry)
        if end is None and start is not None and entry.get("duration_minutes") is not None:
            try:
                end = start + int(round(float(entry.get("duration_minutes"))))
            except (TypeError, ValueError):
                end = start
        left = 0 if start is None else max(0, min(100, ((start - lower) / (upper - lower)) * 100))
        width = 2
        if start is not None and end is not None and end >= start:
            width = max(2, min(100 - left, ((end - start) / (upper - lower)) * 100))
        channel = first_nonempty(entry.get("channel"), "conversation")
        call_class = " included" if entry.get("included_call") is True else ""
        no_call = " no-call" if entry.get("included_call") is False else ""
        title = first_nonempty(entry.get("label"), entry.get("customer"), "Unknown")
        time_label = " - ".join(part for part in (first_nonempty(entry.get("start_time")), first_nonempty(entry.get("end_time"))) if part)
        csat = csat_label(entry.get("csat")) or "CSAT not captured"
        status = first_nonempty(entry.get("status"))
        rows.append(
            f"""<div class="activity-row">
              <div class="activity-main">
                <strong>{esc(title)}</strong>
                <span>{esc(channel)}{(' · ' + esc(status)) if status else ''}</span>
              </div>
              <div class="activity-track" aria-label="{esc(title)} activity">
                <span class="activity-bar{call_class}{no_call}" style="left:{left:.2f}%;width:{width:.2f}%"></span>
              </div>
              <div class="activity-meta">
                <span>{esc(time_label or 'time unknown')}</span>
                <span>{esc(duration_label or 'duration unknown')}</span>
                <span>{esc(csat)}</span>
              </div>
            </div>"""
        )
    return f"""
    <section class="panel">
      <div class="section-heading">
        <h2>Activity Timeline</h2>
        <span>{len(entries)} records</span>
      </div>
      <div class="timeline-legend">
        <span><i class="legend-call"></i> Included call</span>
        <span><i class="legend-chat"></i> Chat or unknown</span>
        <span><i class="legend-open"></i> No call captured</span>
      </div>
      <div class="activity-list">{''.join(rows)}</div>
    </section>"""


def render_feedback_summary(report: dict[str, Any], records: list[dict[str, Any]]) -> str:
    """Render CSAT and Intercom CX Score rating as separate feedback metrics."""
    csat_summary = csat_label(report.get("csat_summary")) or "Not captured"
    csat_records = [csat_label(record.get("csat")) for record in records if is_csat_captured(record.get("csat"))]

    cx_summary = csat_label(report.get("cx_score_summary"))
    cx_records = [csat_label(record.get("cx_score_rating")) for record in records if is_csat_captured(record.get("cx_score_rating"))]

    items = [
        ("CSAT", csat_summary),
        ("Records with CSAT", str(len(csat_records))),
    ]
    if cx_summary or cx_records:
        items.extend(
            [
                ("CX Score rating", cx_summary or "Not captured"),
                ("Records with CX Score", str(len(cx_records))),
            ]
        )
    cards = "".join(f'<div class="mini-stat"><span>{esc(k)}</span><strong>{esc(v)}</strong></div>' for k, v in items)
    return f'<section class="panel csat-panel"><h2>Feedback Scores</h2><div class="mini-grid">{cards}</div></section>'


def render_shadow_info(records: list[Any]) -> str:
    """Render shadowing records as a separate section."""
    useful = [item for item in records if isinstance(item, dict)]
    if not useful:
        return ""
    cards = []
    for record in useful:
        cards.append(
            f"""
            <section class="call-card shadow-card">
              <div class="call-header">
                <h3>{esc(first_nonempty(record.get('title'), record.get('customer'), 'Shadowing record'))}</h3>
                <span class="badge shadow-badge">{esc(first_nonempty(record.get('status'), record.get('source'), 'shadow'))}</span>
              </div>
              {render_record_meta(record)}
              <dl>
                <dt>Context</dt><dd>{esc(first_nonempty(record.get('context'), record.get('issue'), 'Not provided'))}</dd>
                <dt>Outcome</dt><dd>{esc(first_nonempty(record.get('outcome'), 'Not provided'))}</dd>
                <dt>Next action</dt><dd>{esc(first_nonempty(record.get('next_action'), 'Not provided'))}</dd>
              </dl>
              <h4>Takeaways</h4>
              {render_list(as_list(record.get('takeaways') or record.get('product_signals')))}
              {render_timeline(record)}
            </section>"""
        )
    return f'<section><h2>Shadow Info</h2>{"".join(cards)}</section>'


def render_ideas_generated(items: list[Any]) -> str:
    """Render generated product/process/skill ideas as their own section."""
    useful = [item for item in items if item]
    if not useful:
        return ""
    cards = []
    for item in useful:
        if isinstance(item, dict):
            title = first_nonempty(item.get("idea"), item.get("title"), "Idea")
            source = first_nonempty(item.get("source"), item.get("category"))
            why = first_nonempty(item.get("why"), item.get("context"), item.get("description"))
            next_action = first_nonempty(item.get("next_action"), item.get("owner"), item.get("status"))
            cards.append(
                f"""<article class="idea-card">
                  <div class="call-header">
                    <h3>{esc(title)}</h3>
                    {f'<span class="badge">{esc(source)}</span>' if source else ''}
                  </div>
                  <p>{esc(why or 'No rationale captured.')}</p>
                  <p class="muted">{esc(next_action or 'No next action captured.')}</p>
                </article>"""
            )
        else:
            cards.append(f'<article class="idea-card"><h3>{esc(item)}</h3></article>')
    return f'<section><h2>Ideas Generated</h2><div class="ideas-grid">{"".join(cards)}</div></section>'

def render_call(record: dict[str, Any]) -> str:
    """Render a single call/chat record as an HTML card section."""
    product_signals = render_list(as_list(record.get("product_signals")))
    followups = render_list(as_list(record.get("followups")))
    timeline = render_timeline(record)
    meta = render_record_meta(record)
    return f"""
    <section class="call-card">
      <div class="call-header">
        <h3>{esc(record.get("customer") or "Unknown customer")}</h3>
        <span class="badge">{esc(record.get("status") or "captured")}</span>
      </div>
      {meta}
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


def _avg_of_times(values: list[str]) -> str:
    """Return a simple average label for a list of time strings, or em-dash if none."""
    if not values:
        return "&mdash;"
    return esc(values[0]) if len(values) == 1 else esc(values[0])


def render_cx_metrics(cx_metrics: list[dict[str, Any]], teammates: list[str]) -> str:
    """Return four collapsible CX feedback tables as an HTML string."""
    if not cx_metrics:
        return ""

    # Index metrics by name for easy lookup.
    by_name: dict[str, dict[str, Any]] = {m.get("name", ""): m for m in cx_metrics}

    # Ordered list: teammates first (in declared order), then any extras in cx_metrics.
    ordered_names: list[str] = []
    seen: set[str] = set()
    for name in teammates:
        if name not in seen:
            ordered_names.append(name)
            seen.add(name)
    for m in cx_metrics:
        name = m.get("name", "")
        if name and name not in seen:
            ordered_names.append(name)
            seen.add(name)

    def row(name: str) -> dict[str, Any]:
        return by_name.get(name, {})

    # ---- Table 1: Chats vs. Calls ----------------------------------------
    total_chats = sum(row(n).get("chats_started", 0) for n in ordered_names)
    total_calls = sum(row(n).get("calls_started", 0) for n in ordered_names)
    total_screen = sum(row(n).get("screenshare_offered", 0) for n in ordered_names)

    chats_rows = ""
    for name in ordered_names:
        r = row(name)
        chats_rows += (
            f'<tr><td>{esc(name)}</td>'
            f'<td>{esc(r.get("chats_started", 0))}</td>'
            f'<td>{esc(r.get("calls_started", 0))}</td>'
            f'<td>{esc(r.get("screenshare_offered", 0))}</td></tr>'
        )

    table_chats = f"""
<details class="cx-section" open>
  <summary>Chats vs. Calls</summary>
  <table class="cx-table">
    <thead><tr>
      <th>Teammate</th><th>Chats Started</th><th>Calls Started</th><th>Screenshare Offered</th>
    </tr></thead>
    <tbody>
      {chats_rows}
      <tr class="summary-row">
        <td>Summary</td>
        <td>{total_chats}</td>
        <td>{total_calls}</td>
        <td>{total_screen}</td>
      </tr>
    </tbody>
  </table>
</details>"""

    # ---- Table 2: Handle Time vs. Call Time --------------------------------
    handle_rows = ""
    for name in ordered_names:
        r = row(name)
        handle_rows += (
            f'<tr><td>{esc(name)}</td>'
            f'<td>{esc(r.get("avg_handle_time", ""))}</td>'
            f'<td>{esc(r.get("avg_call_duration", ""))}</td></tr>'
        )

    table_handle = f"""
<details class="cx-section" open>
  <summary>Handle Time vs. Call Time</summary>
  <table class="cx-table">
    <thead><tr>
      <th>Teammate</th><th>Avg Handle Time</th><th>Avg Call Duration</th>
    </tr></thead>
    <tbody>{handle_rows}</tbody>
  </table>
</details>"""

    # ---- Table 3: Avg FRT / Max FRT ----------------------------------------
    frt_rows = ""
    for name in ordered_names:
        r = row(name)
        frt_rows += (
            f'<tr><td>{esc(name)}</td>'
            f'<td>{esc(r.get("avg_frt", ""))}</td>'
            f'<td>{esc(r.get("max_frt", ""))}</td></tr>'
        )

    table_frt = f"""
<details class="cx-section" open>
  <summary>Avg FRT / Max FRT</summary>
  <table class="cx-table">
    <thead><tr>
      <th>Action performed by</th><th>Avg FRT</th><th>Max FRT</th>
    </tr></thead>
    <tbody>
      {frt_rows}
    </tbody>
  </table>
</details>"""

    # ---- Table 4: CSAT -------------------------------------------------------
    csat_rows = ""
    for name in ordered_names:
        r = row(name)
        score = r.get("csat_score")
        rated = r.get("csat_rated")
        total = r.get("csat_total")
        if score is not None and rated is not None and total is not None:
            label = f"{score}% ({rated}/{total})" if isinstance(score, (int, float)) else f"{esc(score)} ({rated}/{total})"
        elif score is not None:
            label = f"{score}%" if isinstance(score, (int, float)) else esc(score)
        else:
            label = "&mdash;"
        csat_rows += f'<tr><td>{esc(name)}</td><td>{label}</td></tr>'

    table_csat = f"""
<details class="cx-section" open>
  <summary>CSAT</summary>
  <table class="cx-table">
    <thead><tr>
      <th>Teammate</th><th>CSAT Score</th>
    </tr></thead>
    <tbody>{csat_rows}</tbody>
  </table>
</details>"""

    return table_chats + table_handle + table_frt + table_csat


def render_teammate_sections(records: list[dict[str, Any]]) -> str:
    """Group call cards into collapsible sections per teammate.

    Returns a flat HTML string. Falls back to ungrouped rendering when no
    records carry a `teammate` field.
    """
    has_teammates = any(r.get("teammate") for r in records)
    if not has_teammates:
        return "\n".join(render_call(r) for r in records) or '<p class="muted">No calls captured.</p>'

    # Group preserving insertion order.
    groups: dict[str, list[dict[str, Any]]] = {}
    for r in records:
        name = r.get("teammate") or "Unassigned"
        groups.setdefault(name, []).append(r)

    sections = []
    for name, calls in groups.items():
        count = len(calls)
        label = f"{esc(name)} ({count} call{'s' if count != 1 else ''})"
        cards = "\n".join(render_call(c) for c in calls)
        sections.append(
            f'<details class="teammate-section" open>'
            f"<summary>{label}</summary>"
            f"{cards}"
            f"</details>"
        )
    return "\n".join(sections)


def render_html(report: dict[str, Any], report_date: str) -> str:
    """Build a complete self-contained HTML document from a normalized report dict."""
    records = [item for item in report.get("calls", []) if isinstance(item, dict)]
    resolved = count_where(records, "status", "resolved")
    escalated = count_where(records, "status", "escalated")
    partial = count_where(records, "status", "partial")
    product_signals = sum(len(as_list(record.get("product_signals"))) for record in records)
    calls_included = sum(1 for record in records if record.get("included_call") is True)
    title = report.get("title") or "Support Rotation Daily Report"
    verdict = report.get("verdict") or "Daily support activity summarized from provided sources."
    themes = render_list(as_list(report.get("themes")))
    coaching = render_list(as_list(report.get("coaching_opportunities")))
    open_followups = render_list(as_list(report.get("open_followups")))
    methodology = render_list(as_list(report.get("methodology")))
    generated_at = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # CX metrics section (only when cx_metrics is present).
    cx_metrics: list[dict[str, Any]] = report.get("cx_metrics") or []
    teammates: list[str] = report.get("teammates") or []
    cx_section = render_cx_metrics(cx_metrics, teammates) if cx_metrics else ""

    shift_section = render_shift_summary(report, records)
    activity_section = render_activity_timeline(report, records)
    csat_section = render_feedback_summary(report, records)
    shadow_section = render_shadow_info(as_list(report.get("shadow_info")))
    ideas_section = render_ideas_generated(as_list(report.get("ideas_generated")))

    # Call cards grouped by teammate when teammate fields are present.
    calls_html = render_teammate_sections(records)

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
      --blue: #60a5fa;
    }}
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; color: var(--text); background: var(--bg); }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 32px 20px 48px; }}
    h1, h2, h3, h4 {{ margin: 0 0 12px; }}
    p {{ line-height: 1.55; }}
    .muted {{ color: var(--muted); }}
    .hero, .panel, .call-card, .kpi-card, .idea-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; }}
    .hero {{ padding: 28px; margin-bottom: 20px; }}
    .kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin: 20px 0; }}
    .kpi-card {{ padding: 16px; }}
    .kpi-label {{ color: var(--muted); font-size: 0.78rem; text-transform: uppercase; }}
    .kpi-value {{ font-size: 1.8rem; font-weight: 700; margin-top: 6px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; }}
    .panel, .call-card {{ padding: 18px; margin-bottom: 14px; }}
    .section-heading {{ display: flex; align-items: baseline; justify-content: space-between; gap: 12px; }}
    .section-heading > span {{ color: var(--muted); font-size: .9rem; }}
    .mini-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 10px; margin-top: 12px; }}
    .mini-stat {{ background: rgba(255,255,255,.035); border: 1px solid var(--border); border-radius: 8px; padding: 12px; }}
    .mini-stat span {{ display: block; color: var(--muted); font-size: .78rem; text-transform: uppercase; }}
    .mini-stat strong {{ display: block; margin-top: 4px; font-size: 1rem; }}
    .call-header {{ display: flex; align-items: start; justify-content: space-between; gap: 12px; }}
    .badge {{ color: var(--teal); border: 1px solid rgba(0, 212, 170, .35); border-radius: 999px; padding: 3px 9px; font-size: .8rem; white-space: nowrap; }}
    .shadow-badge {{ color: var(--yellow); border-color: rgba(255, 209, 102, .4); }}
    .meta-chips {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 4px 0 14px; }}
    .meta-chips span {{ color: var(--muted); border: 1px solid var(--border); border-radius: 999px; padding: 4px 9px; font-size: .78rem; }}
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
    .timeline-legend {{ display: flex; flex-wrap: wrap; gap: 14px; color: var(--muted); font-size: .85rem; margin: 4px 0 16px; }}
    .timeline-legend i {{ display: inline-block; width: 18px; height: 8px; border-radius: 999px; margin-right: 6px; vertical-align: middle; }}
    .legend-call {{ background: var(--teal); }}
    .legend-chat {{ background: var(--accent); }}
    .legend-open {{ background: transparent; border: 1px solid var(--yellow); }}
    .activity-list {{ display: grid; gap: 14px; }}
    .activity-row {{ display: grid; grid-template-columns: minmax(180px, 1.2fr) minmax(220px, 2fr) minmax(170px, .9fr); gap: 12px; align-items: center; }}
    .activity-main span, .activity-meta span {{ display: block; color: var(--muted); font-size: .82rem; }}
    .activity-track {{ position: relative; height: 14px; background: rgba(255,255,255,.055); border: 1px solid var(--border); border-radius: 999px; overflow: hidden; }}
    .activity-bar {{ position: absolute; top: 2px; bottom: 2px; min-width: 8px; border-radius: 999px; background: var(--accent); }}
    .activity-bar.included {{ background: var(--teal); }}
    .activity-bar.no-call {{ background: transparent; border: 1px solid var(--yellow); }}
    .ideas-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; }}
    .idea-card {{ padding: 16px; }}
    footer {{ color: var(--muted); margin-top: 24px; font-size: .9rem; }}
    .cx-table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
    .cx-table th {{ color: var(--muted); font-size: .78rem; text-transform: uppercase; text-align: left; padding: 8px 12px; border-bottom: 1px solid var(--border); }}
    .cx-table td {{ padding: 8px 12px; border-bottom: 1px solid var(--border); }}
    .cx-table tr.summary-row td {{ font-weight: 700; }}
    .cx-section {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 18px; margin-bottom: 14px; }}
    .cx-section > summary {{ cursor: pointer; font-size: 1.05rem; font-weight: 600; list-style: none; }}
    .cx-section > summary::-webkit-details-marker {{ display: none; }}
    .teammate-section > summary {{ cursor: pointer; font-size: 1rem; font-weight: 600; color: var(--accent); padding: 10px 0; }}
    @media (max-width: 760px) {{
      .activity-row {{ grid-template-columns: 1fr; }}
      dl {{ grid-template-columns: 1fr; }}
    }}
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
      <div class="kpi-card"><div class="kpi-label">Calls Included</div><div class="kpi-value">{calls_included}</div></div>
      <div class="kpi-card"><div class="kpi-label">Resolved</div><div class="kpi-value">{resolved}</div></div>
      <div class="kpi-card"><div class="kpi-label">Partial</div><div class="kpi-value">{partial}</div></div>
      <div class="kpi-card"><div class="kpi-label">Escalated</div><div class="kpi-value">{escalated}</div></div>
      <div class="kpi-card"><div class="kpi-label">Product Signals</div><div class="kpi-value">{product_signals}</div></div>
    </section>
    {shift_section}
    {activity_section}
    {csat_section}
    {cx_section}
    <section>
      <h2>Calls And Chats</h2>
      {calls_html}
    </section>
    {shadow_section}
    {ideas_section}
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
    """Parse CLI arguments for the report renderer."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="JSON file with normalized daily call records.")
    parser.add_argument("--date", default=dt.date.today().isoformat())
    parser.add_argument("--output", required=True, help="HTML output path.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point: read JSON input, render HTML, write to output path."""
    args = parse_args(argv)
    data = json.loads(Path(args.input).read_text())
    output = Path(args.output)
    output.write_text(render_html(data, args.date))
    print(f"HTML report saved to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
