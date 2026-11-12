#!/usr/bin/env python3
"""Nest (Google Smart Device Management API) auth and read-only status helper.

The OAuth client secret and refresh token live in the macOS Keychain. They are
never printed, never written to the config file, and never passed on a command
line. The config file holds only non-secret identifiers (project id, client id).

Subcommands:
  configure  write the project id / client id to the config file
  url        print the one-time authorization URL to open in a browser
  exchange   trade the pasted redirect URL/code for a refresh token (Keychain)
  status     read-only summary of thermostat devices (markdown or --json)
  check      report which pieces are configured, without revealing any secret
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

SERVICE = "adzuci-house-nest"
ACCOUNT_SECRET = "client-secret"
ACCOUNT_REFRESH = "refresh-token"
AUTH_BASE = "https://nestservices.google.com/partnerconnections"
TOKEN_URL = "https://www.googleapis.com/oauth2/v4/token"
SDM_BASE = "https://smartdevicemanagement.googleapis.com/v1"
SCOPE = "https://www.googleapis.com/auth/sdm.service"
DEFAULT_REDIRECT = "https://www.google.com"
DEFAULT_CONFIG = "~/.config/adzuci-house/config.json"


class NestError(RuntimeError):
    """Raised for user-facing failures. Messages never contain secrets."""


# --------------------------------------------------------------------------
# Keychain
# --------------------------------------------------------------------------
class KeychainStore:
    """Thin wrapper over the macOS `security` tool.

    Values are written through `security -i` (commands on stdin) so they never
    appear in the process list.
    """

    def __init__(self, service: str = SERVICE) -> None:
        self.service = service

    def get(self, account: str) -> Optional[str]:
        proc = subprocess.run(
            ["security", "find-generic-password", "-a", account, "-s", self.service, "-w"],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            return None
        return proc.stdout.rstrip("\n") or None

    def set(self, account: str, value: str) -> None:
        if any(ch in value for ch in ('"', "\\", "\n", "\r")):
            raise NestError("Refusing to store a value containing quotes, backslashes or newlines.")
        command = f'add-generic-password -a "{account}" -s "{self.service}" -w "{value}" -U\n'
        proc = subprocess.run(
            ["security", "-i"], input=command, capture_output=True, text=True
        )
        if proc.returncode != 0:
            raise NestError("Could not write to the macOS Keychain.")

    def delete(self, account: str) -> None:
        subprocess.run(
            ["security", "delete-generic-password", "-a", account, "-s", self.service],
            capture_output=True,
            text=True,
        )


# --------------------------------------------------------------------------
# HTTP (injectable for tests)
# --------------------------------------------------------------------------
def _open(request: urllib.request.Request) -> Dict[str, Any]:
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as err:
        detail = ""
        try:
            payload = json.loads(err.read().decode("utf-8"))
            error = payload.get("error")
            if isinstance(error, dict):
                detail = str(error.get("message", ""))
            elif error:
                detail = str(payload.get("error_description") or error)
        except Exception:  # noqa: BLE001 - best-effort detail only
            pass
        raise NestError(f"Google API returned HTTP {err.code}. {detail}".strip()) from None
    except urllib.error.URLError as err:
        raise NestError(f"Network error: {err.reason}") from None


def default_post(url: str, data: Dict[str, str]) -> Dict[str, Any]:
    body = urllib.parse.urlencode(data).encode("utf-8")
    request = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    return _open(request)


def default_get(url: str, headers: Dict[str, str]) -> Dict[str, Any]:
    return _open(urllib.request.Request(url, headers=headers))


# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------
def load_config(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as err:
        raise NestError(f"Config file is not valid JSON: {path}") from err


def save_config(path: Path, config: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n")
    os.chmod(path, 0o600)


def nest_settings(config: Dict[str, Any]) -> Dict[str, str]:
    nest = config.get("nest") or {}
    return {
        "project_id": str(nest.get("project_id", "")),
        "client_id": str(nest.get("client_id", "")),
        "redirect_uri": str(nest.get("redirect_uri") or DEFAULT_REDIRECT),
    }


# --------------------------------------------------------------------------
# OAuth + API
# --------------------------------------------------------------------------
def build_auth_url(project_id: str, client_id: str, redirect_uri: str = DEFAULT_REDIRECT) -> str:
    if not project_id or not client_id:
        raise NestError("Both a project id and a client id are required.")
    query = urllib.parse.urlencode(
        {
            "redirect_uri": redirect_uri,
            "access_type": "offline",
            "prompt": "consent",
            "client_id": client_id,
            "response_type": "code",
            "scope": SCOPE,
        }
    )
    return f"{AUTH_BASE}/{project_id}/auth?{query}"


def parse_code(raw: str) -> str:
    """Accept either the full redirect URL or just the `code` value."""
    raw = raw.strip()
    if not raw:
        raise NestError("No code provided.")
    if "code=" in raw:
        parsed = urllib.parse.urlparse(raw)
        query = parsed.query or raw.split("?", 1)[-1]
        values = urllib.parse.parse_qs(query).get("code")
        if not values:
            raise NestError("Could not find a code in the pasted URL.")
        return values[0]
    return raw


def exchange_code(
    post: Callable[[str, Dict[str, str]], Dict[str, Any]],
    client_id: str,
    client_secret: str,
    code: str,
    redirect_uri: str,
) -> Dict[str, Any]:
    tokens = post(
        TOKEN_URL,
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        },
    )
    if not tokens.get("refresh_token"):
        raise NestError(
            "Google did not return a refresh token. Re-run the authorization URL "
            "(it uses prompt=consent) and use a fresh code."
        )
    return tokens


def refresh_access_token(
    post: Callable[[str, Dict[str, str]], Dict[str, Any]],
    client_id: str,
    client_secret: str,
    refresh_token: str,
) -> str:
    tokens = post(
        TOKEN_URL,
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
    )
    access = tokens.get("access_token")
    if not access:
        raise NestError("Google did not return an access token.")
    return str(access)


def list_devices(
    get: Callable[[str, Dict[str, str]], Dict[str, Any]], project_id: str, access_token: str
) -> Dict[str, Any]:
    url = f"{SDM_BASE}/enterprises/{project_id}/devices"
    return get(url, {"Authorization": f"Bearer {access_token}"})


def c_to_f(celsius: float) -> float:
    return round(celsius * 9 / 5 + 32, 1)


def summarize_devices(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Reduce the SDM device list to the few fields a weekly digest needs."""
    summary: List[Dict[str, Any]] = []
    for device in payload.get("devices", []):
        traits = device.get("traits", {})
        kind = str(device.get("type", "")).rsplit(".", 1)[-1] or "UNKNOWN"
        room = ""
        for relation in device.get("parentRelations", []):
            room = relation.get("displayName") or room
        name = (traits.get("sdm.devices.traits.Info") or {}).get("customName") or room or kind
        entry: Dict[str, Any] = {"name": name, "type": kind, "room": room}
        temp = traits.get("sdm.devices.traits.Temperature", {}).get("ambientTemperatureCelsius")
        if temp is not None:
            entry["temperature_c"] = round(float(temp), 1)
            entry["temperature_f"] = c_to_f(float(temp))
        humidity = traits.get("sdm.devices.traits.Humidity", {}).get("ambientHumidityPercent")
        if humidity is not None:
            entry["humidity_percent"] = round(float(humidity))
        mode = traits.get("sdm.devices.traits.ThermostatMode", {}).get("mode")
        if mode:
            entry["mode"] = mode
        hvac = traits.get("sdm.devices.traits.ThermostatHvac", {}).get("status")
        if hvac:
            entry["hvac"] = hvac
        setpoint = traits.get("sdm.devices.traits.ThermostatTemperatureSetpoint", {})
        if "heatCelsius" in setpoint:
            entry["heat_setpoint_f"] = c_to_f(float(setpoint["heatCelsius"]))
        if "coolCelsius" in setpoint:
            entry["cool_setpoint_f"] = c_to_f(float(setpoint["coolCelsius"]))
        connectivity = traits.get("sdm.devices.traits.Connectivity", {}).get("status")
        if connectivity:
            entry["connectivity"] = connectivity
        summary.append(entry)
    return summary


def flags_for(summary: List[Dict[str, Any]]) -> List[str]:
    """Plain-language things worth surfacing in the digest."""
    flags: List[str] = []
    for device in summary:
        label = device["name"]
        if device.get("connectivity") and device["connectivity"] != "ONLINE":
            flags.append(f"{label} is {device['connectivity'].lower()}")
        temp = device.get("temperature_f")
        if temp is not None and temp < 50:
            flags.append(f"{label} reads {temp}F (freeze risk)")
        if temp is not None and temp > 85:
            flags.append(f"{label} reads {temp}F (very hot)")
    return flags


def format_markdown(summary: List[Dict[str, Any]]) -> str:
    if not summary:
        return "No Nest devices were shared with this project."
    lines = ["| Device | Temp | Humidity | Mode | HVAC | Online |", "| --- | --- | --- | --- | --- | --- |"]
    for d in summary:
        temp = f"{d['temperature_f']}F" if "temperature_f" in d else "-"
        humidity = f"{d['humidity_percent']}%" if "humidity_percent" in d else "-"
        lines.append(
            f"| {d['name']} | {temp} | {humidity} | {d.get('mode', '-')} | "
            f"{d.get('hvac', '-')} | {d.get('connectivity', '-')} |"
        )
    flags = flags_for(summary)
    if flags:
        lines += ["", "Flags: " + "; ".join(flags)]
    return "\n".join(lines)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--config", default=DEFAULT_CONFIG, help="path to the house config file")
    sub = parser.add_subparsers(dest="command", required=True)

    configure = sub.add_parser("configure", help="save project id and client id (no secrets)")
    configure.add_argument("--project-id", required=True)
    configure.add_argument("--client-id", required=True)
    configure.add_argument("--redirect-uri", default=DEFAULT_REDIRECT)

    sub.add_parser("url", help="print the authorization URL")
    sub.add_parser("exchange", help="exchange the pasted code for a refresh token (Keychain)")
    status = sub.add_parser("status", help="read-only thermostat summary")
    status.add_argument("--json", action="store_true", help="emit JSON instead of markdown")
    sub.add_parser("check", help="report what is configured, without revealing secrets")
    return parser


def main(
    argv: Optional[List[str]] = None,
    *,
    store: Optional[Any] = None,
    post: Optional[Callable[[str, Dict[str, str]], Dict[str, Any]]] = None,
    get: Optional[Callable[[str, Dict[str, str]], Dict[str, Any]]] = None,
    secret_prompt: Callable[[str], str] = getpass.getpass,
    out: Any = None,
) -> int:
    args = build_parser().parse_args(argv)
    out = out or sys.stdout
    store = store or KeychainStore()
    post = post or default_post
    get = get or default_get
    path = Path(args.config).expanduser()

    try:
        config = load_config(path)

        if args.command == "configure":
            config["nest"] = {
                "project_id": args.project_id.strip(),
                "client_id": args.client_id.strip(),
                "redirect_uri": args.redirect_uri.strip(),
            }
            save_config(path, config)
            print(f"Saved Nest project and client ids to {path} (no secrets).", file=out)
            return 0

        settings = nest_settings(config)

        if args.command == "check":
            report = {
                "project_id": bool(settings["project_id"]),
                "client_id": bool(settings["client_id"]),
                "client_secret_in_keychain": store.get(ACCOUNT_SECRET) is not None,
                "refresh_token_in_keychain": store.get(ACCOUNT_REFRESH) is not None,
            }
            print(json.dumps(report, indent=2), file=out)
            return 0 if all(report.values()) else 1

        if not settings["project_id"] or not settings["client_id"]:
            raise NestError("Run `configure --project-id ... --client-id ...` first.")

        if args.command == "url":
            print(build_auth_url(settings["project_id"], settings["client_id"], settings["redirect_uri"]), file=out)
            return 0

        client_secret = store.get(ACCOUNT_SECRET)

        if args.command == "exchange":
            if not client_secret:
                client_secret = secret_prompt("OAuth client secret (input hidden): ").strip()
                if not client_secret:
                    raise NestError("No client secret provided.")
                store.set(ACCOUNT_SECRET, client_secret)
            code = parse_code(secret_prompt("Paste the redirect URL or code (input hidden): "))
            tokens = exchange_code(post, settings["client_id"], client_secret, code, settings["redirect_uri"])
            store.set(ACCOUNT_REFRESH, str(tokens["refresh_token"]))
            print("Stored the refresh token in the macOS Keychain.", file=out)
            return 0

        if args.command == "status":
            refresh = store.get(ACCOUNT_REFRESH)
            if not client_secret or not refresh:
                raise NestError("Not authorized yet. Run the `exchange` step first.")
            access = refresh_access_token(post, settings["client_id"], client_secret, refresh)
            summary = summarize_devices(list_devices(get, settings["project_id"], access))
            if args.json:
                print(json.dumps({"devices": summary, "flags": flags_for(summary)}, indent=2), file=out)
            else:
                print(format_markdown(summary), file=out)
            return 0
    except NestError as err:
        print(f"error: {err}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
