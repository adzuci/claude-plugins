"""Write the support-windows calendar straight into a Google Sheet via the Sheets API.

Auth is Application Default Credentials. To avoid key files, impersonate a
service account that has been shared on the Sheet (see references/sheets-auth.md).
A plain API key cannot write to a Sheet, so it is not supported.
"""

from __future__ import annotations

SHEETS_SCOPE = "https://www.googleapis.com/auth/spreadsheets"
CLOUD_SCOPE = "https://www.googleapis.com/auth/cloud-platform"
API = "https://sheets.googleapis.com/v4/spreadsheets"
FIX_COLS = 2  # label + status columns before the month grid
OPEN_EDX_TABS = ["README", "Django Upgrade 3.2 Squad Participation", "IDA and Upgrade Status"]
STATUS_TAB = "Apollo Status"
STATUS_HEAD = ["Product", "Version", "Running?", "EOL", "State", "Ticket", "Note", "Source"]
STATE_COLORS = {"EOL PASSED": "#cc0000", "EOL < 6 MO": "#b45f06", "LIKELY EOL": "#cc0000", "UNKNOWN": "#666666"}


def rgb(hex_color):
    h = hex_color.lstrip("#")
    return {k: int(h[i:i + 2], 16) / 255 for k, i in (("red", 0), ("green", 2), ("blue", 4))}


def cell(value="", bg="#ffffff", fg="#000000", bold=False, align=None, note=None, links=None):
    out = {
        "userEnteredFormat": {
            "backgroundColor": rgb(bg),
            "textFormat": {"foregroundColor": rgb(fg), "bold": bold, "fontFamily": "Arial", "fontSize": 9},
        }
    }
    if align:
        out["userEnteredFormat"]["horizontalAlignment"] = align
    if value != "":
        out["userEnteredValue"] = {"stringValue": str(value)}
    if note:
        out["note"] = note
    if links:  # [(start, end, uri)] runs inside the string value
        runs, pos = [], 0
        for start, end, uri in links:
            if start > pos:
                runs.append({"startIndex": pos, "format": {}})
            runs.append({"startIndex": start, "format": {"link": {"uri": uri}}})
            pos = end
        if pos < len(str(value)):
            runs.append({"startIndex": pos, "format": {}})
        out["textFormatRuns"] = runs
    return out


def build_grid(payload):
    """Return (rows, borders, merges).

    borders and merges are (row, col, n_cols) tuples in 0-based grid coordinates.
    """
    months = 12 * (payload["endYear"] - payload["startYear"] + 1)
    width = FIX_COLS + months
    rows, borders, merges = [], [], []
    today = payload["todayCol"]

    year_row = [cell(f"Apollo support windows (as of {payload['generated']})", bold=True), cell()]
    month_row = [cell(), cell("Status")]
    for m in range(months):
        year_row.append(cell(payload["startYear"] + m // 12 if m % 12 == 0 else "", bold=True, align="CENTER"))
        month_row.append(cell("JFMAMJJASOND"[m % 12], bg="#f4cccc" if m == today else "#ffffff"))
    rows += [year_row, month_row]
    merges += [(0, FIX_COLS + 12 * y, 12) for y in range(months // 12)]

    for i, r in enumerate(payload["rows"]):
        line = [cell() for _ in range(width)]
        r_idx = 2 + i
        if r["kind"] == "header":
            line[0] = cell(r["label"], bg=r["color"], fg="#ffffff", bold=True)
        elif r["kind"] == "note":
            line[0] = cell(r["label"], note=r.get("hover"))
            line[1] = cell(r["status"], fg=STATE_COLORS.get(r["status"], "#000000"), bold=True)
        else:
            line[0] = cell(r["label"], bold=r["running"], note=r.get("hover"))
            line[1] = cell(r["status"], fg=STATE_COLORS.get(r["state"], "#000000") if r["running"] else "#000000")
            for c in range(r["first"], r["last"] + 1):
                line[FIX_COLS + c] = cell(bg=r["fill"], fg=r["fg"], bold=r["running"])
            if r["labelInBar"]:
                line[FIX_COLS + r["first"]] = cell(r["label"], bg=r["fill"], fg=r["fg"], bold=r["running"], align="LEFT")
                merges.append((r_idx, FIX_COLS + r["first"], r["last"] - r["first"] + 1))
            if r["running"]:
                borders.append((r_idx, FIX_COLS + r["first"], r["last"] - r["first"] + 1))
        rows.append(line)
    footer = [cell("Bold + outlined = version Apollo runs today. Light = supported but not run. Source: endoflife.date + eol-calendar skill products.yaml", fg="#666666")]
    rows.append(footer + [cell() for _ in range(width - 1)])
    return rows, borders, merges


def _rng(sheet_id, r0, c0, r1, c1):
    return {"sheetId": sheet_id, "startRowIndex": r0, "endRowIndex": r1, "startColumnIndex": c0, "endColumnIndex": c1}


def _border(style="SOLID_MEDIUM", color="#000000"):
    return {"style": style, "color": rgb(color)}


def calendar_requests(sheet_id, payload):
    rows, borders, merges = build_grid(payload)
    n_rows, n_cols = len(rows), len(rows[0])
    reqs = [
        {"unmergeCells": {"range": {"sheetId": sheet_id}}},
        # wipe values + formats (including borders) left over from the Open edX copy
        {"repeatCell": {"range": {"sheetId": sheet_id}, "cell": {}, "fields": "userEnteredValue,userEnteredFormat"}},
        {"updateSheetProperties": {
            "properties": {"sheetId": sheet_id, "gridProperties": {
                "rowCount": max(n_rows + 1, 2), "columnCount": n_cols, "frozenRowCount": 2, "frozenColumnCount": FIX_COLS}},
            "fields": "gridProperties(rowCount,columnCount,frozenRowCount,frozenColumnCount)"}},
        {"updateCells": {"start": {"sheetId": sheet_id, "rowIndex": 0, "columnIndex": 0},
                         "rows": [{"values": r} for r in rows],
                         "fields": "userEnteredValue,userEnteredFormat"}},
        {"updateDimensionProperties": {"range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 1},
                                       "properties": {"pixelSize": 220}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 1, "endIndex": 2},
                                       "properties": {"pixelSize": 120}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": FIX_COLS, "endIndex": n_cols},
                                       "properties": {"pixelSize": 17}, "fields": "pixelSize"}},
    ]
    for r, c, n in merges:
        reqs.append({"mergeCells": {"range": _rng(sheet_id, r, c, r + 1, c + n), "mergeType": "MERGE_ALL"}})
    for r, c, n in borders:
        b = _border()
        reqs.append({"updateBorders": {"range": _rng(sheet_id, r, c, r + 1, c + n), "top": b, "bottom": b, "left": b, "right": b}})
    for y in range((n_cols - FIX_COLS) // 12):  # solid divider at the start of every year
        reqs.append({"updateBorders": {"range": _rng(sheet_id, 0, FIX_COLS + 12 * y, n_rows - 1, FIX_COLS + 12 * y + 1),
                                       "left": _border("SOLID")}})
    col = payload["todayCol"]
    if 0 <= col < n_cols - FIX_COLS:
        reqs.append({"updateBorders": {"range": _rng(sheet_id, 0, FIX_COLS + col, n_rows - 1, FIX_COLS + col + 1),
                                       "left": _border("DASHED", "#cc0000")}})
    return reqs


def ticket_cell(s, jira):
    keys = s.get("tickets") or []
    s = {**s, "ticket": s.get("ticket", "")}
    if keys:
        links, pos = [], 0
        for k in keys:
            links.append((pos, pos + len(k), jira + k))
            pos += len(k) + 2
        return cell(s["ticket"], links=links)
    if s["ticket"] == "NO TICKET":
        return cell("NO TICKET", fg="#cc0000", bold=True)
    return cell(s["ticket"])


def status_requests(sheet_id, status, jira="https://apollopde.atlassian.net/browse/"):
    rows = [{"values": [cell(h, bold=True) for h in STATUS_HEAD]}]
    for s in status:
        vals = [s["product"], s["version"], s["running"], s["eol"], s["state"], s.get("ticket", ""), s["note"], s["source"]]
        line = [cell(v) for v in vals]
        line[5] = ticket_cell(s, jira)
        if s["state"] in STATE_COLORS:
            line[4] = cell(s["state"], fg=STATE_COLORS[s["state"]], bold=True)
        rows.append({"values": line})
    return [
        {"unmergeCells": {"range": {"sheetId": sheet_id}}},
        {"repeatCell": {"range": {"sheetId": sheet_id}, "cell": {}, "fields": "userEnteredValue,userEnteredFormat"}},
        {"updateSheetProperties": {"properties": {"sheetId": sheet_id, "gridProperties": {
            "rowCount": len(rows) + 1, "columnCount": len(STATUS_HEAD), "frozenRowCount": 1}},
            "fields": "gridProperties(rowCount,columnCount,frozenRowCount)"}},
        {"updateCells": {"start": {"sheetId": sheet_id, "rowIndex": 0, "columnIndex": 0}, "rows": rows,
                         "fields": "userEnteredValue,userEnteredFormat"}},
        {"autoResizeDimensions": {"dimensions": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 6}}},
    ]


def get_session(impersonate=None):
    """AuthorizedSession from ADC; optionally impersonating a service account (no key file)."""
    import google.auth
    from google.auth.transport.requests import AuthorizedSession

    if impersonate:
        from google.auth import impersonated_credentials

        source, _ = google.auth.default(scopes=[CLOUD_SCOPE])
        creds = impersonated_credentials.Credentials(
            source_credentials=source, target_principal=impersonate, target_scopes=[SHEETS_SCOPE])
    else:
        creds, _ = google.auth.default(scopes=[SHEETS_SCOPE])
    return AuthorizedSession(creds)


def _call(session, method, url, **kw):
    resp = session.request(method, url, timeout=60, **kw)
    if resp.status_code >= 400:
        raise RuntimeError(f"Sheets API {resp.status_code}: {resp.text[:400]}")
    return resp.json()


def push(spreadsheet_id, payload, sheet_name, impersonate=None, drop_openedx=False, dry_run=False):
    """Replace the calendar + status tabs. Returns a list of human-readable actions."""
    actions = []
    session = None if dry_run else get_session(impersonate)
    meta = {"sheets": []} if dry_run else _call(session, "GET", f"{API}/{spreadsheet_id}?fields=sheets.properties")
    ids = {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta["sheets"]}
    next_id = 1_000_001
    setup = []
    for name in (sheet_name, STATUS_TAB):
        if name not in ids:
            ids[name] = next_id
            next_id += 1
            setup.append({"addSheet": {"properties": {"sheetId": ids[name], "title": name}}})
            actions.append(f"add tab {name!r}")
    if drop_openedx:
        for name in OPEN_EDX_TABS:
            if name in ids:
                setup.append({"deleteSheet": {"sheetId": ids[name]}})
                actions.append(f"delete tab {name!r}")
    reqs = setup + calendar_requests(ids[sheet_name], payload) + status_requests(ids[STATUS_TAB], payload["status"], payload.get("jira", "https://apollopde.atlassian.net/browse/"))
    actions.append(f"rewrite {sheet_name!r} and {STATUS_TAB!r} ({len(reqs)} requests, one atomic batch)")
    if not dry_run:
        _call(session, "POST", f"{API}/{spreadsheet_id}:batchUpdate", json={"requests": reqs})
    return actions
