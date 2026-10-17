"""
Generate Apollo's "Support Windows" EOL calendar for a Google Sheet.

Adapted from openedx/repo-tools barcalendar.py. Dates come from endoflife.date
(per-product slug) and can be overridden in products.yaml. Running versions are
bold + outlined; versions past EOL are flagged red.

Usage (from the skill directory; warnings, including drift vs endoflife.date, go to stderr):
    python scripts/eol_calendar.py > support_windows.gs   # paste into Apps Script
    python scripts/eol_calendar.py --status                # markdown status table
    python scripts/eol_calendar.py --push SHEET_ID [--impersonate SA] [--dry-run]
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys

import requests
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://endoflife.date/api/{slug}.json"
SOON_DAYS = 183
JIRA_BROWSE = "https://apollopde.atlassian.net/browse/"
EOL_STATES = {"EOL PASSED", "EOL < 6 MO", "LIKELY EOL"}


def parse_date(value):
    """endoflife.date uses false/null for 'no date'; return a date or None."""
    if not value or value is True:
        return None
    if isinstance(value, datetime.date):
        return value
    return datetime.date.fromisoformat(str(value))


def column(year, month, start_year):
    return (year - start_year) * 12 + month - 1


def make_bar(start, end, start_year, end_year):
    """Return (first_col, last_col) clamped to the chart window, or None."""
    width = 12 * (end_year - start_year + 1)
    first = column(start.year, start.month, start_year)
    last = width - 1 if end is None else column(end.year, end.month, start_year)
    if first >= width or last < 0:
        return None
    return max(first, 0), min(last, width - 1)


def classify(eol, running, today=None):
    if not running:
        return "n/a"
    today = today or datetime.date.today()
    if eol is None:
        return "NO EOL"
    if eol < today:
        return "EOL PASSED"
    if (eol - today).days <= SOON_DAYS:
        return "EOL < 6 MO"
    return "SUPPORTED"


def ticket_text(tickets, state, tracked):
    """Ticket column text: the keys, or NO TICKET when an EOL item has none."""
    if tickets:
        return ", ".join(tickets)
    return "NO TICKET" if (tracked and state in EOL_STATES) else ""


def row_note(note, tickets):
    out = note or ""
    if tickets:
        out += ("\n\n" if out else "") + "Tickets: " + ", ".join(JIRA_BROWSE + t for t in tickets)
    return out


def fetch_cycles(slug, warnings):
    """Return {cycle: {"start": date|None, "end": date|None}} for a slug."""
    try:
        resp = requests.get(
            API.format(slug=slug), headers={"Accept": "application/json"}, timeout=15
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        warnings.append(f"API fetch failed for {slug}: {exc}")
        return {}
    return {
        str(c["cycle"]): {
            "start": parse_date(c.get("releaseDate")),
            "end": parse_date(c.get("eol")),
        }
        for c in resp.json()
    }


def merge_dates(row, api, product):
    """Manual dates win over the API; report drift when both exist and differ."""
    if api is None:
        missing = [key for key in ("start", "end") if not row.get(key)]
        if missing:
            raise ValueError(
                f"{product} {row['cycle']}: missing manual {', '.join(missing)} "
                "date(s) and no API data"
            )
    warnings = []
    out = {}
    for key in ("start", "end"):
        manual = parse_date(row.get(key))
        from_api = api.get(key) if api else None
        if manual is not None and from_api is not None and manual != from_api:
            warnings.append(
                f"DRIFT {product} {row['cycle']} {key}: yaml={manual} endoflife.date={from_api}"
            )
        out[key] = manual if manual is not None else from_api
    return out, warnings


def build(config, today=None):
    """Resolve products.yaml into chartable rows + status rows."""
    today = today or datetime.date.today()
    warnings, bars, status = [], [], []
    for group in config["products"]:
        cycles = fetch_cycles(group["slug"], warnings) if group.get("slug") else {}
        bars.append({"header": group["name"], "color": group["color"]})
        for row in group["versions"]:
            running = bool(row.get("running"))
            planned = bool(row.get("planned"))
            label = f"{group['name']} {row.get('label', row['cycle'])}"
            if row.get("unverified"):
                tickets = row.get("tickets", [])
                st = row.get("state", "UNKNOWN")
                bars.append(dict(label=label, color=group["color"], note=True, state=st,
                                 hover=row_note(row.get("note", ""), tickets)))
                status.append(
                    dict(product=group["name"], version=row.get("label", row["cycle"]),
                         running="unverified", eol="", state=st,
                         tickets=tickets, ticket=ticket_text(tickets, st, True),
                         note=row.get("note", ""), source=row.get("source", ""))
                )
                continue
            api = cycles.get(str(row["cycle"]))
            if api is None and not (row.get("start") and row.get("end")):
                warnings.append(f"MISSING {group['name']} {row['cycle']}: not in API, skipped")
                continue
            dates, warn = merge_dates(row, api, group["name"])
            warnings += warn
            state = row.get("state") or classify(dates["end"], running, today)
            tickets = row.get("tickets", [])
            bars.append(
                dict(label=label, color=group["color"], running=running, planned=planned,
                     start=dates["start"], end=dates["end"], state=state,
                     hover=row_note(row.get("note", ""), tickets))
            )
            if running or planned:
                status.append(
                    dict(product=group["name"], version=row.get("label", row["cycle"]),
                         running="running" if running else "planned",
                         eol=dates["end"].isoformat() if dates["end"] else "none published",
                         state=state, tickets=tickets,
                         ticket=ticket_text(tickets, state, running),
                         note=row.get("note", ""), source=row.get("source", ""))
                )
    return bars, status, warnings


def lighten(hex_color, amount=0.55):
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    r, g, b = (int(v + (255 - v) * amount) for v in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def text_color(fill):
    """Black or white text, whichever reads better on the given fill."""
    r, g, b = (int(fill[i:i + 2], 16) for i in (1, 3, 5))
    return "#ffffff" if (0.299 * r + 0.587 * g + 0.114 * b) < 150 else "#000000"


MIN_LABEL_MONTHS = 5  # shorter bars are too narrow to hold their label


def to_payload(bars, status, cfg, today=None):
    """JSON-serialisable chart model shared by the Apps Script and Sheets API outputs.

    Everything render-specific (fill, text color, label placement, status text) is
    decided here so both renderers stay thin.
    """
    today = today or datetime.date.today()
    s_year, e_year = cfg["start_year"], cfg["end_year"]
    rows = []
    for b in bars:
        if "header" in b:
            rows.append(dict(kind="header", label=b["header"], color=b["color"]))
            continue
        if b.get("note"):
            rows.append(dict(kind="note", label=b["label"], status=b["state"], hover=b.get("hover", "")))
            continue
        bar = make_bar(b["start"], b["end"], s_year, e_year)
        if bar is None:
            continue
        fill = b["color"] if (b["running"] or b["planned"]) else lighten(b["color"])
        rows.append(
            dict(kind="bar", label=b["label"], first=bar[0], last=bar[1], fill=fill,
                 fg=text_color(fill), running=b["running"], state=b["state"],
                 status=b["state"] if b["running"] else ("PLANNED" if b["planned"] else ""),
                 labelInBar=bar[1] - bar[0] + 1 >= MIN_LABEL_MONTHS, hover=b.get("hover", ""))
        )
    today_col = column(today.year, today.month, s_year)
    return dict(
        sheet=cfg["sheet_name"], startYear=s_year, endYear=e_year, todayCol=today_col,
        generated=today.isoformat(), rows=rows, status=status, jira=JIRA_BROWSE,
    )


def to_script(payload):
    return JS_TEMPLATE.replace("__PAYLOAD__", json.dumps(payload, indent=1))


def status_markdown(status):
    lines = ["| Product | Version | Running | EOL | State | Ticket | Note |", "|---|---|---|---|---|---|---|"]
    for s in status:
        lines.append(
            f"| {s['product']} | {s['version']} | {s['running']} | {s['eol']} | {s['state']} | {s['ticket']} | {s['note']} |"
        )
    return "\n".join(lines)


JS_TEMPLATE = r"""
// Generated by the eol-calendar skill (scripts/eol_calendar.py) -- do not hand-edit.
const DATA = __PAYLOAD__;

function makeApolloSupportWindows() {
  const ss = SpreadsheetApp.getActive();
  const sh = ss.getSheetByName(DATA.sheet) || ss.insertSheet(DATA.sheet);
  // The upstream Open edX sheet is full of merged bars; unmerge before clearing.
  sh.getRange(1, 1, sh.getMaxRows(), sh.getMaxColumns()).breakApart();
  sh.clear();
  sh.clearConditionalFormatRules();
  const months = 12 * (DATA.endYear - DATA.startYear + 1);
  const FIX = 2;                       // label + status columns
  const nRows = DATA.rows.length + 3;  // years, months, rows, footer
  if (sh.getMaxColumns() < FIX + months) sh.insertColumnsAfter(sh.getMaxColumns(), FIX + months - sh.getMaxColumns());
  if (sh.getMaxRows() < nRows + 1) sh.insertRowsAfter(sh.getMaxRows(), nRows + 1 - sh.getMaxRows());
  const grid = [];
  const bg = [];
  const fontColor = [];
  const weight = [];
  const blank = (n, v) => Array(n).fill(v);
  const W = FIX + months;

  const yearRow = ["Apollo support windows (as of " + DATA.generated + ")", ""];
  const monthRow = ["", "Status"];
  for (let m = 0; m < months; m++) {
    yearRow.push(m % 12 === 0 ? String(DATA.startYear + m / 12) : "");
    monthRow.push("JFMAMJJASOND"[m % 12]);
  }
  grid.push(yearRow, monthRow);
  bg.push(blank(W, "#ffffff"), blank(W, "#ffffff"));
  fontColor.push(blank(W, "#000000"), blank(W, "#000000"));
  weight.push(blank(W, "bold"), blank(W, "normal"));

  const borders = [];
  const merges = [];
  const STATE_FG = {"EOL PASSED": "#cc0000", "EOL < 6 MO": "#b45f06", "LIKELY EOL": "#cc0000", "UNKNOWN": "#666666"};
  DATA.rows.forEach((r, i) => {
    const row = blank(W, "");
    const rbg = blank(W, "#ffffff");
    const rfc = blank(W, "#000000");
    const rw = blank(W, "normal");
    row[0] = r.label;
    if (r.kind === "header") {
      rbg.fill(r.color, 0, 1);
      rfc[0] = "#ffffff";
      rw[0] = "bold";
    } else if (r.kind === "note") {
      row[1] = r.status;
      rfc[1] = STATE_FG[r.status] || "#000000";
      rw[1] = "bold";
    } else {
      row[1] = r.status;
      if (STATE_FG[r.state] && r.running) rfc[1] = STATE_FG[r.state];
      for (let c = r.first; c <= r.last; c++) {
        rbg[FIX + c] = r.fill;
        rfc[FIX + c] = r.fg;
        if (r.running) rw[FIX + c] = "bold";
      }
      if (r.running) rw[0] = "bold";
      if (r.labelInBar) {
        row[FIX + r.first] = r.label;     // label sits inside the bar, like the Open edX original
        merges.push([i + 3, FIX + 1 + r.first, r.last - r.first + 1]);
      }
      if (r.running) borders.push([i + 3, FIX + 1 + r.first, 1, r.last - r.first + 1]);
    }
    grid.push(row); bg.push(rbg); fontColor.push(rfc); weight.push(rw);
  });
  grid.push(["Bold + outlined = version Apollo runs today. Light = supported but not run. Source: endoflife.date + eol-calendar skill products.yaml", ...blank(W - 1, "")]);
  bg.push(blank(W, "#ffffff")); fontColor.push(blank(W, "#666666")); weight.push(blank(W, "normal"));

  const rng = sh.getRange(1, 1, grid.length, W);
  rng.setValues(grid).setBackgrounds(bg).setFontColors(fontColor).setFontWeights(weight);
  rng.setFontFamily("Arial").setFontSize(9);
  // Hover notes on the version labels: why it matters + ticket links
  sh.getRange(3, 1, DATA.rows.length, 1).setNotes(DATA.rows.map(r => [r.hover || ""]));
  sh.setColumnWidth(1, 220);
  sh.setColumnWidth(2, 120);
  sh.setColumnWidths(FIX + 1, months, 17);
  sh.setFrozenRows(2);
  sh.setFrozenColumns(FIX);
  // One merged, centered header cell per year (the original does this too).
  for (let y = 0; y < months / 12; y++) {
    sh.getRange(1, FIX + 1 + 12 * y, 1, 12).merge().setHorizontalAlignment("center");
  }
  merges.forEach(m => sh.getRange(m[0], m[1], 1, m[2]).merge().setHorizontalAlignment("left"));
  borders.forEach(b => sh.getRange(b[0], b[1], b[2], b[3])
    .setBorder(true, true, true, true, false, false, "#000000", SpreadsheetApp.BorderStyle.SOLID_MEDIUM));
  // Solid divider at the start of every year
  for (let y = 0; y < months / 12; y++) {
    sh.getRange(1, FIX + 1 + 12 * y, grid.length - 1, 1)
      .setBorder(null, true, null, null, null, null, "#000000", SpreadsheetApp.BorderStyle.SOLID);
  }
  // Today marker: shaded month header + dashed line
  if (DATA.todayCol >= 0 && DATA.todayCol < months) {
    sh.getRange(2, FIX + 1 + DATA.todayCol).setBackground("#f4cccc");
    sh.getRange(1, FIX + 1 + DATA.todayCol, grid.length - 1, 1)
      .setBorder(null, true, null, false, false, false, "#cc0000", SpreadsheetApp.BorderStyle.DASHED);
  }
  makeStatusSheet_();
}

// Optional, run by hand: deletes the leftover Open edX tabs from the copied sheet.
function removeOpenEdxTabs() {
  const ss = SpreadsheetApp.getActive();
  ["README", "Django Upgrade 3.2 Squad Participation", "IDA and Upgrade Status"].forEach(name => {
    const s = ss.getSheetByName(name);
    if (s) ss.deleteSheet(s);
  });
}

function makeStatusSheet_() {
  const ss = SpreadsheetApp.getActive();
  const sh = ss.getSheetByName("Apollo Status") || ss.insertSheet("Apollo Status");
  sh.clear();
  const head = ["Product", "Version", "Running?", "EOL", "State", "Ticket", "Note", "Source"];
  const body = DATA.status.map(s => [s.product, s.version, s.running, s.eol, s.state, s.ticket, s.note, s.source]);
  // Plain text, or Sheets turns versions like "7.0" into the number 7.
  sh.getRange(1, 1, body.length + 1, head.length).setNumberFormat("@");
  sh.getRange(1, 1, 1, head.length).setValues([head]).setFontWeight("bold");
  if (body.length) sh.getRange(2, 1, body.length, head.length).setValues(body);
  sh.setFrozenRows(1);
  body.forEach((r, i) => {
    const c = sh.getRange(i + 2, 5);
    if (r[4] === "EOL PASSED" || r[4] === "LIKELY EOL") c.setFontColor("#cc0000").setFontWeight("bold");
    else if (r[4] === "EOL < 6 MO") c.setFontColor("#b45f06").setFontWeight("bold");
    else if (r[4] === "UNKNOWN") c.setFontColor("#666666");
    const t = sh.getRange(i + 2, 6);
    const keys = DATA.status[i].tickets || [];
    if (keys.length) {
      // each key links to its Jira ticket
      const rt = SpreadsheetApp.newRichTextValue().setText(r[5]);
      let pos = 0;
      keys.forEach(k => { rt.setLinkUrl(pos, pos + k.length, DATA.jira + k); pos += k.length + 2; });
      t.setRichTextValue(rt.build());
    } else if (r[5] === "NO TICKET") {
      t.setFontColor("#cc0000").setFontWeight("bold");
    }
  });
  sh.autoResizeColumns(1, head.length - 3);
}
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=os.path.join(HERE, "..", "products.yaml"))
    ap.add_argument("--status", action="store_true", help="print markdown status table instead of Apps Script")
    ap.add_argument("--push", metavar="SHEET_ID", help="write directly to this Google Sheet via the Sheets API")
    ap.add_argument("--impersonate", metavar="SA_EMAIL",
                    default=os.environ.get("EOL_SHEETS_SA"),
                    help="service account to impersonate (default: $EOL_SHEETS_SA, else your own ADC)")
    ap.add_argument("--drop-openedx-tabs", action="store_true", help="with --push: delete leftover Open edX tabs")
    ap.add_argument("--dry-run", action="store_true", help="with --push: list actions, call no API")
    args = ap.parse_args()
    with open(args.config) as fh:
        config = yaml.safe_load(fh)
    bars, status, warnings = build(config)
    for w in warnings:
        print(w, file=sys.stderr)
    if args.status:
        print(status_markdown(status))
        return
    payload = to_payload(bars, status, config["chart"])
    if args.push:
        # Running this file directly puts its parent, not scripts/, on sys.path.
        if HERE not in sys.path:
            sys.path.insert(0, HERE)
        import sheets_push

        for action in sheets_push.push(args.push, payload, config["chart"]["sheet_name"],
                                       impersonate=args.impersonate,
                                       drop_openedx=args.drop_openedx_tabs, dry_run=args.dry_run):
            print(("[dry-run] " if args.dry_run else "") + action)
    else:
        print(to_script(payload))


if __name__ == "__main__":
    main()
