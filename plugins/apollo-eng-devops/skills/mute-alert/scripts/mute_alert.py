#!/usr/bin/env python3
"""Create, list and expire time-boxed Grafana alert silences (stdlib only).

Requires `gcx` (Grafana CLI), already logged in: all calls go through `gcx api`.
Run `doctor` to check readiness.

Exit codes: 0 ok, 2 bad input, 3 API error.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone

API = "/api/alertmanager/grafana/api/v2"
GCX_TIMEOUT = 30
DEFAULT_DURATION = "60m"
MAX_DURATION = timedelta(hours=4)
MAX_LONG_DURATION = timedelta(hours=12)
SCOPING_LABELS = ("cluster", "instance")
SELFTEST_ALERT = "__mute_alert_selftest__"
NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
DURATION_RE = re.compile(r"^(\d+)([mh])$")
SETUP_DOC = "skills/mute-alert/references/gcx-setup.md"
NOT_READY_MSG = ("gcx is missing or not logged in.\n"
                 "Run `mute_alert.py doctor`, then follow %s" % SETUP_DOC)
REGEX_CHARS = set("*|^$[]()?+\\{}")


class InputError(Exception):
    """Bad user input or gcx not ready (exit 2)."""


class ApiError(Exception):
    """Grafana/gcx failure (exit 3)."""


# ---- validation (pure, no network) ----
def parse_duration(s: str, allow_long: bool = False) -> timedelta:
    m = DURATION_RE.match((s or "").strip())
    if not m:
        raise InputError("invalid duration %r (use e.g. 30m, 90m, 1h)" % s)
    n, unit = int(m.group(1)), m.group(2)
    d = timedelta(minutes=n) if unit == "m" else timedelta(hours=n)
    if d <= timedelta(0):
        raise InputError("duration must be positive")
    limit = MAX_LONG_DURATION if allow_long else MAX_DURATION
    if d > limit:
        hint = "" if allow_long else " (use --allow-long for up to 12h)"
        raise InputError("duration %s exceeds max %dh%s" % (s, limit.total_seconds() // 3600, hint))
    return d


def parse_matcher(s: str) -> dict:
    if "=" not in s:
        raise InputError("matcher %r must be name=value" % s)
    name, value = s.split("=", 1)
    if value.startswith("~") or name.endswith(("!", "~")):
        raise InputError("matcher %r: regex/negative matchers are not allowed" % s)
    if not NAME_RE.match(name):
        raise InputError("matcher %r: invalid label name" % s)
    if not value.strip():
        raise InputError("matcher %r: empty value" % s)
    if REGEX_CHARS & set(value):
        raise InputError("matcher %r: wildcard/regex characters are not allowed" % s)
    return {"name": name, "value": value, "isRegex": False, "isEqual": True}


def validate_matchers(matchers: list, allow_broad: bool) -> None:
    if not any(m["name"] == "alertname" for m in matchers):
        raise InputError("an exact alertname matcher is required (--matcher alertname=...)")
    if not allow_broad and not any(m["name"] in SCOPING_LABELS for m in matchers):
        raise InputError("add a scoping label (%s) or pass --allow-broad" % " or ".join(SCOPING_LABELS))


def build_payload(matchers, now, duration, created_by, comment, ticket=None) -> dict:
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    text = comment.strip() + (" (%s)" % ticket if ticket else "")
    return {"matchers": matchers, "startsAt": now.strftime(fmt), "endsAt": (now + duration).strftime(fmt),
            "createdBy": created_by, "comment": text}


# ---- gcx ----
def _gcx_out(*args):
    """Run a read-only gcx subcommand; return (returncode, stdout) or (None, '')."""
    try:
        r = subprocess.run(["gcx", *args], capture_output=True, text=True, timeout=GCX_TIMEOUT)
        return r.returncode, (r.stdout or "").strip()
    except (subprocess.TimeoutExpired, OSError):
        return None, ""


def gcx_ready() -> bool:
    return bool(shutil.which("gcx")) and _gcx_out("config", "check")[0] == 0


def require_gcx() -> None:
    if not gcx_ready():
        raise InputError(NOT_READY_MSG)


def doctor() -> int:
    has_gcx = bool(shutil.which("gcx"))
    ok = False
    print("[%s] gcx on PATH" % ("x" if has_gcx else " "))
    if has_gcx:
        ok = _gcx_out("config", "check")[0] == 0
        print("[%s] gcx config check" % ("x" if ok else " "))
        ctx = _gcx_out("config", "current-context")[1].splitlines()
        print("    context: %s" % (ctx[0][:60] if ctx else "none"))
    print("verdict: %s  (setup guide: %s)" % ("gcx OK" if ok else "NOT READY", SETUP_DOC))
    return 0 if ok else 2


def call(method: str, path: str, body=None):
    argv = ["gcx", "api", API + path] + (["-X", method] if method != "GET" else [])
    argv += (["-d", "@-"] if body is not None else []) + ["-o", "json"]
    try:
        r = subprocess.run(argv, input=json.dumps(body) if body is not None else None,
                           capture_output=True, text=True, timeout=GCX_TIMEOUT)
    except subprocess.TimeoutExpired:
        raise ApiError("gcx request timed out after %ds" % GCX_TIMEOUT)
    except OSError as e:
        raise ApiError("could not run gcx: %s" % e)
    if r.returncode != 0:
        raise ApiError("gcx api failed (exit %d): %s" % (r.returncode, (r.stderr or "").strip()[:300]))
    try:
        return json.loads(r.stdout) if (r.stdout or "").strip() else {}
    except ValueError:
        raise ApiError("unexpected non-JSON response from Grafana")


# ---- operations ----
def do_create(payload) -> dict:
    res = call("POST", "/silences", payload)
    sid = res.get("silenceID") if isinstance(res, dict) else None
    if not sid:
        raise ApiError("Grafana did not return a silenceID")
    return {"id": sid, **{k: payload[k] for k in ("startsAt", "endsAt", "matchers", "comment")},
            "expire_command": "python %s expire %s" % (os.path.relpath(__file__), sid)}


def do_list(active_only=False) -> list:
    res = call("GET", "/silences")
    if not isinstance(res, list):
        raise ApiError("unexpected list response shape")
    return [s for s in res if not active_only or (s.get("status") or {}).get("state") == "active"]


def do_expire(sid) -> None:
    call("DELETE", "/silence/" + sid)


def state_of(sid):
    return next(((s.get("status") or {}).get("state") for s in do_list() if s.get("id") == sid), None)


def created_by_env() -> str:
    return os.environ.get("MUTE_ALERT_CREATED_BY") or os.environ.get("USER") or "mute-alert"


def self_test() -> bool:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    payload = build_payload([parse_matcher("alertname=" + SELFTEST_ALERT)], now,
                            timedelta(minutes=2), created_by_env(), "mute-alert self-test")
    sid = do_create(payload)["id"]
    try:
        active = state_of(sid) == "active"
        print("created %s; active: %s" % (sid, active))
    finally:
        do_expire(sid)  # always undo
    st = state_of(sid)
    print("state after expire: %s" % st)
    ok = active and st == "expired"
    print("PASS" if ok else "FAIL")
    return ok


# ---- CLI ----
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mute_alert.py", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create", help="create a time-boxed silence")
    c.add_argument("--matcher", action="append", default=[], help="name=value (repeatable)")
    c.add_argument("--duration", default=DEFAULT_DURATION, help="e.g. 30m, 90m, 1h (default 60m, max 4h)")
    c.add_argument("--comment")
    c.add_argument("--ticket")
    c.add_argument("--allow-broad", action="store_true", help="allow no cluster/instance matcher")
    c.add_argument("--allow-long", action="store_true", help="allow duration up to 12h")
    c.add_argument("--dry-run", action="store_true")
    c.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
    l = sub.add_parser("list", help="list silences")
    l.add_argument("--active", action="store_true")
    e = sub.add_parser("expire", help="expire a silence now")
    e.add_argument("id")
    sub.add_parser("doctor", help="check gcx readiness (no writes)")
    sub.add_parser("self-test", help="create+verify+expire a silence that matches nothing")
    return p


def _out(obj) -> None:
    print(json.dumps(obj, indent=2))


def _create(a) -> int:
    matchers = [parse_matcher(m) for m in a.matcher]
    validate_matchers(matchers, a.allow_broad)
    duration = parse_duration(a.duration, a.allow_long)
    if not a.comment or not a.comment.strip():
        raise InputError("--comment is required")
    now = datetime.now(timezone.utc).replace(microsecond=0)
    payload = build_payload(matchers, now, duration, created_by_env(), a.comment, a.ticket)
    if a.dry_run:
        _out({"dry_run": True, **payload})
        return 0
    require_gcx()  # fail fast, before prompting
    if not a.yes:
        if not sys.stdin.isatty():
            raise InputError("refusing to create without --yes (needs explicit approval)")
        print(json.dumps(payload, indent=2))
        if input("Create this silence? [y/N] ").strip().lower() != "y":
            raise InputError("aborted")
    _out(do_create(payload))
    print("Silences stop PAGES only; Argus posts and INCIDENT tickets still occur, "
          "and real failures are hidden. Verify the work separately.", file=sys.stderr)
    return 0


def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    try:
        if a.cmd == "doctor":
            return doctor()
        if a.cmd == "create":
            return _create(a)
        require_gcx()
        if a.cmd == "list":
            _out(do_list(a.active))
        elif a.cmd == "expire":
            do_expire(a.id)
            _out({"id": a.id, "expired": True})
        else:
            return 0 if self_test() else 3
        return 0
    except InputError as e:
        print("error: %s" % e, file=sys.stderr)
        return 2
    except ApiError as e:
        print("error: %s" % e, file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
