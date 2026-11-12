#!/usr/bin/env python3
"""Read-only Tailscale doctor for macOS: check, verify, and peer reachability.

This script never installs, logs in, changes settings, or prints secrets. It
reads `tailscale status --json` and keeps only a small allow-list of fields
(backend state, own name/IPs, peer names/IPs/online flags); keys, auth URLs and
other raw fields are dropped. Install, login, and uninstall are done by the
skill with the user's confirmation, and login always happens in the Tailscale
app, never here.

Subcommands (all emit JSON; exit 0 ready, 1 not ready, 2 usage/error):
  check                  environment and Tailscale state, with a suggested next step
  verify [--peer P]      require Running + a 100.x address, ping one peer
  peer TARGET [--port N] tailnet ping, then TCP probe (default 14318, NVIDIA PAIR)
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple

CASK = "tailscale-app"
APP_PATH = "/Applications/Tailscale.app"
APP_CLI = "/Applications/Tailscale.app/Contents/MacOS/Tailscale"
DEFAULT_PORT = 14318
CGNAT = ipaddress.ip_network("100.64.0.0/10")
TARGET_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9.-]{0,251}[A-Za-z0-9])?$")
OTHER_VPN_APPS = ("NordVPN", "ProtonVPN", "Mullvad VPN", "ExpressVPN", "Cloudflare WARP", "Surfshark", "Private Internet Access")

Runner = Callable[[List[str]], Tuple[int, str, str]]


def default_runner(cmd: List[str]) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except FileNotFoundError:
        return 127, "", f"{cmd[0]}: not found"
    except subprocess.TimeoutExpired:
        return 124, "", "timed out"
    return proc.returncode, proc.stdout, proc.stderr


def find_cli(
    which: Optional[Callable[[str], Optional[str]]] = None,
    exists: Optional[Callable[[str], bool]] = None,
) -> Optional[str]:
    which = which or shutil.which
    exists = exists or os.path.exists
    found = which("tailscale")
    if found:
        return found
    if exists(APP_CLI):
        return APP_CLI
    return None


def is_tailnet_ip(value: str) -> bool:
    try:
        return ipaddress.ip_address(value) in CGNAT
    except ValueError:
        return False


def trim_dns(name: str) -> str:
    return name[:-1] if name.endswith(".") else name


def summarize_status(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Keep only non-sensitive fields from `tailscale status --json`."""
    me = raw.get("Self") or {}
    ips = [ip for ip in me.get("TailscaleIPs", []) if isinstance(ip, str)]
    tailnet = raw.get("CurrentTailnet") or {}
    peers: List[Dict[str, Any]] = []
    for peer in (raw.get("Peer") or {}).values():
        peers.append(
            {
                "name": peer.get("HostName", ""),
                "dns": trim_dns(peer.get("DNSName", "")),
                "ips": [ip for ip in peer.get("TailscaleIPs", []) if is_tailnet_ip(ip)],
                "online": bool(peer.get("Online")),
                "os": peer.get("OS", ""),
            }
        )
    peers.sort(key=lambda p: (not p["online"], p["name"]))
    return {
        "backend_state": raw.get("BackendState", "Unknown"),
        "self_name": me.get("HostName", ""),
        "self_dns": trim_dns(me.get("DNSName", "")),
        "self_ips": ips,
        "self_tailnet_ip": next((ip for ip in ips if is_tailnet_ip(ip)), None),
        "tailnet": tailnet.get("Name", ""),
        "magicdns_suffix": tailnet.get("MagicDNSSuffix") or raw.get("MagicDNSSuffix", ""),
        "health": [str(h) for h in raw.get("Health") or []],
        "peers": peers,
    }


def read_status(runner: Runner, cli: str) -> Tuple[Optional[Dict[str, Any]], str]:
    code, out, err = runner([cli, "status", "--json"])
    if not out.strip():
        return None, (err.strip() or f"tailscale status exited {code}")[:200]
    try:
        return summarize_status(json.loads(out)), ""
    except json.JSONDecodeError:
        return None, "tailscale status did not return JSON"


def next_step(report: Dict[str, Any]) -> str:
    if not report["cli"]:
        return "install"
    state = report.get("status", {}).get("backend_state") if report.get("status") else None
    if state is None:
        return "start-the-app"
    return {
        "Running": "verify",
        "NeedsLogin": "login",
        "NeedsMachineAuth": "approve-machine-in-admin-console",
        "Stopped": "turn-tailscale-on",
        "Starting": "wait-then-recheck",
    }.get(state, "inspect-health")


def check(
    runner: Runner = default_runner,
    which: Optional[Callable[[str], Optional[str]]] = None,
    exists: Optional[Callable[[str], bool]] = None,
    system: str = "",
    machine: str = "",
) -> Dict[str, Any]:
    which = which or shutil.which
    exists = exists or os.path.exists
    system = system or platform.system()
    machine = machine or platform.machine()
    cli = find_cli(which, exists)
    brew = which("brew")
    cask_ok = False
    if brew:
        cask_ok = runner([brew, "info", "--cask", CASK])[0] == 0
    report: Dict[str, Any] = {
        "macos": system == "Darwin",
        "arch": machine,
        "brew": bool(brew),
        "cask": CASK,
        "cask_available": cask_ok,
        "app_installed": exists(APP_PATH),
        "cli": cli,
        "other_vpn_apps": [name for name in OTHER_VPN_APPS if exists(f"/Applications/{name}.app")],
        "status": None,
        "status_error": "",
    }
    if cli:
        status, error = read_status(runner, cli)
        report["status"], report["status_error"] = status, error
    report["next"] = next_step(report)
    return report


def parse_ping(output: str) -> Dict[str, Any]:
    pongs = re.findall(r"pong from (\S+) \(([^)]+)\) via (\S+(?:\s*\([^)]*\))?) in (\d+(?:\.\d+)?)ms", output)
    if not pongs:
        return {"ok": False, "pongs": 0}
    name, ip, via, ms = pongs[-1]
    return {
        "ok": True,
        "pongs": len(pongs),
        "peer": name,
        "ip": ip,
        "path": "relay" if via.upper().startswith("DERP") else "direct",
        "via": via,
        "ms": float(ms),
    }


def ping(runner: Runner, cli: str, target: str, count: int = 3) -> Dict[str, Any]:
    code, out, err = runner([cli, "ping", "-c", str(count), "--timeout", "5s", target])
    result = parse_ping(out + "\n" + err)
    if not result["ok"]:
        result["error"] = (err.strip() or out.strip() or f"exit {code}")[:200]
    return result


def verify(
    peer: Optional[str] = None,
    runner: Runner = default_runner,
    which: Optional[Callable[[str], Optional[str]]] = None,
    exists: Optional[Callable[[str], bool]] = None,
) -> Dict[str, Any]:
    cli = find_cli(which, exists)
    result: Dict[str, Any] = {"ok": False, "checks": {}}
    if not cli:
        result["error"] = "Tailscale CLI not found; run the install step."
        return result
    status, error = read_status(runner, cli)
    if status is None:
        result["error"] = error
        return result
    result["status"] = {k: status[k] for k in ("backend_state", "self_name", "self_dns", "self_tailnet_ip", "tailnet", "health")}
    result["checks"]["running"] = status["backend_state"] == "Running"
    result["checks"]["tailnet_ip"] = bool(status["self_tailnet_ip"])
    target = peer
    if not target:
        online = [p for p in status["peers"] if p["online"] and p["ips"]]
        target = online[0]["ips"][0] if online else None
    if target and TARGET_RE.match(target):
        result["ping"] = ping(runner, cli, target)
        result["checks"]["ping"] = result["ping"]["ok"]
    else:
        result["ping"] = None
        result["note"] = "No online peer to ping yet. Sign in on the other Mac, then re-run with --peer."
    result["ok"] = all(result["checks"].values()) and result["ping"] is not None
    return result


def peer_check(
    target: str,
    port: int = DEFAULT_PORT,
    runner: Runner = default_runner,
    which: Optional[Callable[[str], Optional[str]]] = None,
    exists: Optional[Callable[[str], bool]] = None,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {"target": target, "port": port, "ok": False}
    if not TARGET_RE.match(target):
        result["error"] = "Target must be a MagicDNS name, hostname, or 100.x address."
        return result
    if not 1 <= port <= 65535:
        result["error"] = "Port must be 1-65535."
        return result
    cli = find_cli(which, exists)
    if not cli:
        result["error"] = "Tailscale CLI not found; run the install step."
        return result
    result["ping"] = ping(runner, cli, target)
    host = result["ping"].get("ip") or target
    code, out, err = runner(["nc", "-vz", "-G", "3", host, str(port)])
    text = (out + err).lower()
    result["tcp_open"] = code == 0 and "succeeded" in text
    result["tcp_detail"] = (err.strip() or out.strip())[:160]
    result["ok"] = bool(result["ping"]["ok"] and result["tcp_open"])
    if result["ping"]["ok"] and not result["tcp_open"]:
        result["hint"] = "Tailnet path works but the port is closed: is PAIR running on the peer, and does a firewall block it?"
    elif not result["ping"]["ok"]:
        result["hint"] = "No tailnet path: check both Macs are Running in the same tailnet and the peer is online."
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check")
    ver = sub.add_parser("verify")
    ver.add_argument("--peer")
    peer = sub.add_parser("peer")
    peer.add_argument("target")
    peer.add_argument("--port", type=int, default=DEFAULT_PORT)
    return parser


def main(argv: Optional[List[str]] = None, *, runner: Runner = default_runner, out: Any = None) -> int:
    args = build_parser().parse_args(argv)
    out = out or sys.stdout
    if args.command == "check":
        result = check(runner)
        code = 0 if result["next"] == "verify" else 1
    elif args.command == "verify":
        result = verify(args.peer, runner)
        code = 0 if result["ok"] else 1
    else:
        result = peer_check(args.target, args.port, runner)
        code = 0 if result["ok"] else 1
    print(json.dumps(result, indent=2), file=out)
    return code


if __name__ == "__main__":
    sys.exit(main())
