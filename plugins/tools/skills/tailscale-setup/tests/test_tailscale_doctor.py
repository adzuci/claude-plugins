"""Tests for the read-only Tailscale doctor (no network, no real tailscale)."""

from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "tailscale_doctor.py"
spec = importlib.util.spec_from_file_location("tailscale_doctor", SCRIPT)
tsd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tsd)

CLI = "/opt/homebrew/bin/tailscale"

SECRET_BITS = ("nodekey:abc123", "AuthURL", "https://login.tailscale.com/a/secret", "PublicKey")

RUNNING = {
    "BackendState": "Running",
    "AuthURL": "https://login.tailscale.com/a/secret",
    "Self": {
        "HostName": "mac",
        "DNSName": "mac.tail1234.ts.net.",
        "TailscaleIPs": ["100.64.0.5", "fd7a:115c:a1e0::5"],
        "PublicKey": "nodekey:abc123",
        "Online": True,
    },
    "CurrentTailnet": {"Name": "adam@example.com", "MagicDNSSuffix": "tail1234.ts.net"},
    "Health": [],
    "Peer": {
        "nodekey:abc123": {
            "HostName": "intel-mac",
            "DNSName": "intel-mac.tail1234.ts.net.",
            "TailscaleIPs": ["100.110.21.77", "fd7a:115c:a1e0::9"],
            "Online": True,
            "OS": "macOS",
        },
        "nodekey:def456": {
            "HostName": "old-laptop",
            "DNSName": "old-laptop.tail1234.ts.net.",
            "TailscaleIPs": ["100.100.1.1"],
            "Online": False,
            "OS": "linux",
        },
    },
}

PONG = "pong from intel-mac (100.110.21.77) via 192.168.40.70:41641 in 6ms\n" * 2
PONG_DERP = "pong from intel-mac (100.110.21.77) via DERP(nyc) in 41ms\n"


def make_runner(responses):
    """responses: list of (prefix-list, (rc, out, err)); first prefix match wins."""
    calls = []

    def runner(cmd):
        calls.append(cmd)
        for prefix, result in responses:
            if cmd[: len(prefix)] == prefix:
                return result
        return 127, "", "not mocked"

    runner.calls = calls
    return runner


def which_with(**found):
    return lambda name: found.get(name)


def test_is_tailnet_ip():
    assert tsd.is_tailnet_ip("100.64.0.5")
    assert tsd.is_tailnet_ip("100.127.255.254")
    assert not tsd.is_tailnet_ip("100.128.0.1")
    assert not tsd.is_tailnet_ip("192.168.40.64")
    assert not tsd.is_tailnet_ip("not-an-ip")


def test_summarize_status_drops_secrets_and_sorts_online_first():
    summary = tsd.summarize_status(RUNNING)
    blob = json.dumps(summary)
    for secret in SECRET_BITS:
        assert secret not in blob
    assert summary["self_tailnet_ip"] == "100.64.0.5"
    assert summary["self_dns"] == "mac.tail1234.ts.net"
    assert [p["name"] for p in summary["peers"]] == ["intel-mac", "old-laptop"]
    assert summary["peers"][0]["ips"] == ["100.110.21.77"]  # IPv6 filtered out


def test_find_cli_prefers_path_then_app_bundle():
    assert tsd.find_cli(which_with(tailscale=CLI), lambda p: False) == CLI
    assert tsd.find_cli(which_with(), lambda p: p == tsd.APP_CLI) == tsd.APP_CLI
    assert tsd.find_cli(which_with(), lambda p: False) is None


def test_check_not_installed_suggests_install():
    runner = make_runner([(["/opt/homebrew/bin/brew", "info"], (0, "", ""))])
    report = tsd.check(runner, which_with(brew="/opt/homebrew/bin/brew"), lambda p: False, "Darwin", "arm64")
    assert report["macos"] and report["arch"] == "arm64"
    assert report["cask_available"] is True and report["cask"] == "tailscale-app"
    assert report["cli"] is None and report["next"] == "install"
    # read-only: only `brew info` was run
    assert all(c[1] == "info" for c in runner.calls)


def test_check_reports_other_vpn_apps():
    exists = lambda p: p == "/Applications/NordVPN.app"
    report = tsd.check(make_runner([]), which_with(), exists, "Darwin", "x86_64")
    assert report["other_vpn_apps"] == ["NordVPN"] and report["arch"] == "x86_64"


@pytest.mark.parametrize(
    "state,expected",
    [
        ("Running", "verify"),
        ("NeedsLogin", "login"),
        ("Stopped", "turn-tailscale-on"),
        ("NeedsMachineAuth", "approve-machine-in-admin-console"),
        ("Starting", "wait-then-recheck"),
        ("Weird", "inspect-health"),
    ],
)
def test_check_next_step_by_backend_state(state, expected):
    payload = json.dumps({"BackendState": state})
    runner = make_runner([([CLI, "status"], (0, payload, ""))])
    report = tsd.check(runner, which_with(tailscale=CLI), lambda p: False, "Darwin", "arm64")
    assert report["next"] == expected


def test_check_daemon_not_running():
    runner = make_runner([([CLI, "status"], (1, "", "failed to connect to local tailscaled"))])
    report = tsd.check(runner, which_with(tailscale=CLI), lambda p: False, "Darwin", "arm64")
    assert report["next"] == "start-the-app" and "tailscaled" in report["status_error"]


def test_parse_ping_direct_and_relay():
    direct = tsd.parse_ping(PONG)
    assert direct["ok"] and direct["path"] == "direct" and direct["pongs"] == 2 and direct["ms"] == 6.0
    relay = tsd.parse_ping(PONG_DERP)
    assert relay["ok"] and relay["path"] == "relay"
    assert tsd.parse_ping("no matching peer")["ok"] is False


def test_verify_pings_first_online_peer():
    runner = make_runner([
        ([CLI, "status"], (0, json.dumps(RUNNING), "")),
        ([CLI, "ping"], (0, PONG, "")),
    ])
    result = tsd.verify(None, runner, which_with(tailscale=CLI), lambda p: False)
    assert result["ok"] is True
    assert result["checks"] == {"running": True, "tailnet_ip": True, "ping": True}
    assert runner.calls[-1][-1] == "100.110.21.77"
    assert "nodekey" not in json.dumps(result)


def test_verify_without_peers_is_not_ok_but_explains():
    payload = dict(RUNNING, Peer={})
    runner = make_runner([([CLI, "status"], (0, json.dumps(payload), ""))])
    result = tsd.verify(None, runner, which_with(tailscale=CLI), lambda p: False)
    assert result["ok"] is False and "No online peer" in result["note"]


def test_verify_needs_login_fails_running_check():
    runner = make_runner([([CLI, "status"], (0, json.dumps({"BackendState": "NeedsLogin"}), ""))])
    result = tsd.verify("intel-mac", runner, which_with(tailscale=CLI), lambda p: False)
    assert result["checks"]["running"] is False and result["ok"] is False


def test_verify_without_cli():
    result = tsd.verify(None, make_runner([]), which_with(), lambda p: False)
    assert result["ok"] is False and "install" in result["error"]


def test_peer_ok_uses_pinged_ip_and_default_port():
    runner = make_runner([
        ([CLI, "ping"], (0, PONG, "")),
        (["nc"], (0, "", "Connection to 100.110.21.77 port 14318 [tcp/*] succeeded!")),
    ])
    result = tsd.peer_check("intel-mac", 14318, runner, which_with(tailscale=CLI), lambda p: False)
    assert result["ok"] and result["tcp_open"] and result["ping"]["path"] == "direct"
    assert runner.calls[-1] == ["nc", "-vz", "-G", "3", "100.110.21.77", "14318"]


def test_peer_port_closed_gives_hint():
    runner = make_runner([
        ([CLI, "ping"], (0, PONG_DERP, "")),
        (["nc"], (1, "", "nc: connect to 100.110.21.77 port 14318 (tcp) failed: Connection refused")),
    ])
    result = tsd.peer_check("100.110.21.77", 14318, runner, which_with(tailscale=CLI), lambda p: False)
    assert result["ok"] is False and result["tcp_open"] is False and "port is closed" in result["hint"]


def test_peer_no_tailnet_path_hint():
    runner = make_runner([
        ([CLI, "ping"], (1, "", "no matching peer")),
        (["nc"], (1, "", "timed out")),
    ])
    result = tsd.peer_check("ghost", 14318, runner, which_with(tailscale=CLI), lambda p: False)
    assert result["ok"] is False and "No tailnet path" in result["hint"]


@pytest.mark.parametrize("target", ["", "-bad", "a b", "x;rm -rf /", "$(id)", "a" * 300])
def test_peer_rejects_unsafe_targets(target):
    runner = make_runner([])
    result = tsd.peer_check(target, 14318, runner, which_with(tailscale=CLI), lambda p: False)
    assert result["ok"] is False and "error" in result and runner.calls == []


@pytest.mark.parametrize("port", [0, 70000, -1])
def test_peer_rejects_bad_ports(port):
    result = tsd.peer_check("intel-mac", port, make_runner([]), which_with(tailscale=CLI), lambda p: False)
    assert result["ok"] is False and "Port" in result["error"]


def test_main_outputs_json_and_exit_codes(monkeypatch):
    monkeypatch.setattr(tsd.shutil, "which", lambda name: CLI if name == "tailscale" else None)
    monkeypatch.setattr(tsd.os.path, "exists", lambda p: False)
    runner = make_runner([
        ([CLI, "status"], (0, json.dumps(RUNNING), "")),
        ([CLI, "ping"], (0, PONG, "")),
        (["nc"], (0, "", "succeeded!")),
    ])
    out = io.StringIO()
    assert tsd.main(["peer", "intel-mac", "--port", "14318"], runner=runner, out=out) == 0
    assert json.loads(out.getvalue())["ok"] is True
    out = io.StringIO()
    assert tsd.main(["check"], runner=runner, out=out) == 0
    assert json.loads(out.getvalue())["next"] == "verify"
    out = io.StringIO()
    assert tsd.main(["peer", "bad target"], runner=runner, out=out) == 1
