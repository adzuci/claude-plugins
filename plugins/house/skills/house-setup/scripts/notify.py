#!/usr/bin/env python3
"""Send an urgent house alert by SMS or phone call through the Twilio CLI.

Dry-run by default: nothing is sent unless `--send` is passed. Quiet hours are
enforced unless `--ignore-quiet-hours` is passed. Credentials live in the Twilio
CLI profile (created by `twilio login`); this script never sees them.

Config (non-secret) comes from the house config file under "notify":
  {"to": "+19785551234", "from": "+15555550100", "profile": "house",
   "quiet_hours": "22-7"}
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from xml.sax.saxutils import escape

DEFAULT_CONFIG = "~/.config/adzuci-house/config.json"
E164 = re.compile(r"^\+[1-9]\d{6,14}$")
MAX_LEN = 300


class NotifyError(RuntimeError):
    pass


def valid_e164(number: str) -> bool:
    return bool(E164.match(number or ""))


def in_quiet_hours(spec: str, now: dt.datetime) -> bool:
    """`spec` is 'START-END' in 24h local hours, e.g. '22-7' (wraps midnight)."""
    match = re.match(r"^(\d{1,2})-(\d{1,2})$", spec or "")
    if not match:
        return False
    start, end = int(match.group(1)), int(match.group(2))
    hour = now.hour
    if start == end:
        return False
    if start < end:
        return start <= hour < end
    return hour >= start or hour < end


def load_notify_config(path: Path) -> Dict[str, Any]:
    try:
        config = json.loads(path.read_text())
    except FileNotFoundError:
        raise NotifyError(f"No config at {path}. Run the house-setup skill first.") from None
    notify = config.get("notify") or {}
    for key in ("to", "from"):
        if not valid_e164(str(notify.get(key, ""))):
            raise NotifyError(f"notify.{key} must be an E.164 phone number like +19785551234.")
    return notify


def build_command(kind: str, notify: Dict[str, Any], message: str) -> List[str]:
    base = ["twilio"]
    if notify.get("profile"):
        base += ["-p", str(notify["profile"])]
    if kind == "sms":
        return base + [
            "api:core:messages:create",
            "--from", notify["from"],
            "--to", notify["to"],
            "--body", message,
        ]
    twiml = f"<Response><Say>{escape(message)}</Say></Response>"
    return base + [
        "api:core:calls:create",
        "--from", notify["from"],
        "--to", notify["to"],
        "--twiml", twiml,
    ]


def run(
    argv: Optional[List[str]] = None,
    *,
    now: Optional[dt.datetime] = None,
    runner: Callable[..., Any] = subprocess.run,
    out: Any = None,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("kind", choices=["sms", "call"])
    parser.add_argument("--message", required=True, help=f"alert text (max {MAX_LEN} chars)")
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--send", action="store_true", help="actually send (default is a dry run)")
    parser.add_argument("--ignore-quiet-hours", action="store_true")
    args = parser.parse_args(argv)
    out = out or sys.stdout
    now = now or dt.datetime.now()

    try:
        notify = load_notify_config(Path(args.config).expanduser())
        message = " ".join(args.message.split())
        if not message:
            raise NotifyError("Message is empty.")
        if len(message) > MAX_LEN:
            raise NotifyError(f"Message is {len(message)} chars; keep it under {MAX_LEN}.")
        quiet = notify.get("quiet_hours", "22-7")
        if in_quiet_hours(quiet, now) and not args.ignore_quiet_hours:
            print(f"Skipped: quiet hours ({quiet}). Use --ignore-quiet-hours for a true emergency.", file=out)
            return 3
        command = build_command(args.kind, notify, message)
        if not args.send:
            shown = [part if not part.startswith("+") else part[:-4] + "XXXX" for part in command]
            print("Dry run. Would run:", " ".join(shown), file=out)
            return 0
        result = runner(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise NotifyError("The Twilio CLI reported an error; run `twilio profiles:list` and check the account.")
        print(f"Sent {args.kind} to the configured number.", file=out)
        return 0
    except NotifyError as err:
        print(f"error: {err}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(run())
