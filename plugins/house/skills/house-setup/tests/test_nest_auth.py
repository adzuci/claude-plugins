"""Tests for the Nest auth/status helper (no network, no real Keychain)."""

from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "nest_auth.py"
spec = importlib.util.spec_from_file_location("nest_auth", SCRIPT)
nest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nest)

SECRET = "super-secret-client-value"
REFRESH = "1//refresh-token-value"
ACCESS = "ya29.access-token-value"


class FakeStore:
    def __init__(self, **items):
        self.items = dict(items)

    def get(self, account):
        return self.items.get(account)

    def set(self, account, value):
        self.items[account] = value


def run(tmp_path, argv, **kwargs):
    out = io.StringIO()
    code = nest.main(["--config", str(tmp_path / "config.json")] + argv, out=out, **kwargs)
    return code, out.getvalue()


def configure(tmp_path):
    return run(tmp_path, ["configure", "--project-id", "proj-123", "--client-id", "cid.apps.googleusercontent.com"])


def test_build_auth_url_has_required_params():
    url = nest.build_auth_url("proj-123", "cid", "https://www.google.com")
    parsed = urlparse(url)
    assert parsed.path == "/partnerconnections/proj-123/auth"
    query = parse_qs(parsed.query)
    assert query["client_id"] == ["cid"]
    assert query["access_type"] == ["offline"]
    assert query["prompt"] == ["consent"]
    assert query["response_type"] == ["code"]
    assert query["scope"] == [nest.SCOPE]
    assert query["redirect_uri"] == ["https://www.google.com"]


def test_build_auth_url_requires_ids():
    with pytest.raises(nest.NestError):
        nest.build_auth_url("", "cid")


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("4/0Abc", "4/0Abc"),
        ("https://www.google.com/?code=4/0Abc&scope=https://www.googleapis.com/auth/sdm.service", "4/0Abc"),
        ("  4/0Abc  ", "4/0Abc"),
    ],
)
def test_parse_code(raw, expected):
    assert nest.parse_code(raw) == expected


def test_parse_code_rejects_empty():
    with pytest.raises(nest.NestError):
        nest.parse_code("   ")


def test_configure_writes_no_secrets_and_is_private(tmp_path):
    code, _ = configure(tmp_path)
    assert code == 0
    path = tmp_path / "config.json"
    data = json.loads(path.read_text())
    assert data["nest"]["project_id"] == "proj-123"
    assert oct(path.stat().st_mode & 0o777) == "0o600"


def test_url_requires_configuration(tmp_path):
    code, _ = run(tmp_path, ["url"])
    assert code == 2


def test_url_prints_authorization_link(tmp_path):
    configure(tmp_path)
    code, out = run(tmp_path, ["url"])
    assert code == 0
    assert "partnerconnections/proj-123/auth" in out


def test_exchange_stores_secrets_in_keychain_and_prints_none(tmp_path):
    configure(tmp_path)
    store = FakeStore()
    answers = iter([SECRET, "https://www.google.com/?code=4/0Abc&scope=x"])
    seen = {}

    def post(url, data):
        seen.update(data)
        return {"refresh_token": REFRESH, "access_token": ACCESS}

    code, out = run(tmp_path, ["exchange"], store=store, post=post, secret_prompt=lambda _p: next(answers))
    assert code == 0
    assert store.items[nest.ACCOUNT_SECRET] == SECRET
    assert store.items[nest.ACCOUNT_REFRESH] == REFRESH
    assert seen["code"] == "4/0Abc"
    assert seen["grant_type"] == "authorization_code"
    for secret in (SECRET, REFRESH, ACCESS):
        assert secret not in out
        assert secret not in (tmp_path / "config.json").read_text()


def test_exchange_without_refresh_token_fails(tmp_path):
    configure(tmp_path)
    store = FakeStore(**{nest.ACCOUNT_SECRET: SECRET})
    code, _ = run(
        tmp_path, ["exchange"], store=store,
        post=lambda u, d: {"access_token": ACCESS},
        secret_prompt=lambda _p: "4/0Abc",
    )
    assert code == 2
    assert nest.ACCOUNT_REFRESH not in store.items


DEVICES = {
    "devices": [
        {
            "name": "enterprises/proj/devices/abc",
            "type": "sdm.devices.types.THERMOSTAT",
            "parentRelations": [{"displayName": "Hallway"}],
            "traits": {
                "sdm.devices.traits.Temperature": {"ambientTemperatureCelsius": 20.0},
                "sdm.devices.traits.Humidity": {"ambientHumidityPercent": 41.4},
                "sdm.devices.traits.ThermostatMode": {"mode": "HEAT"},
                "sdm.devices.traits.ThermostatHvac": {"status": "HEATING"},
                "sdm.devices.traits.ThermostatTemperatureSetpoint": {"heatCelsius": 21.0},
                "sdm.devices.traits.Connectivity": {"status": "ONLINE"},
            },
        },
        {
            "type": "sdm.devices.types.THERMOSTAT",
            "parentRelations": [{"displayName": "Garage"}],
            "traits": {
                "sdm.devices.traits.Temperature": {"ambientTemperatureCelsius": 4.0},
                "sdm.devices.traits.Connectivity": {"status": "OFFLINE"},
            },
        },
    ]
}


def test_summarize_devices_converts_units():
    summary = nest.summarize_devices(DEVICES)
    assert summary[0]["name"] == "Hallway"
    assert summary[0]["temperature_f"] == 68.0
    assert summary[0]["humidity_percent"] == 41
    assert summary[0]["heat_setpoint_f"] == 69.8
    assert summary[0]["mode"] == "HEAT"


def test_flags_offline_and_freeze():
    flags = nest.flags_for(nest.summarize_devices(DEVICES))
    assert any("Garage is offline" in f for f in flags)
    assert any("freeze risk" in f for f in flags)


def test_status_requires_authorization(tmp_path):
    configure(tmp_path)
    code, _ = run(tmp_path, ["status"], store=FakeStore())
    assert code == 2


def test_status_markdown_and_json(tmp_path):
    configure(tmp_path)
    store = FakeStore(**{nest.ACCOUNT_SECRET: SECRET, nest.ACCOUNT_REFRESH: REFRESH})
    calls = []

    def post(url, data):
        calls.append(data["grant_type"])
        return {"access_token": ACCESS}

    def get(url, headers):
        assert url.endswith("/enterprises/proj-123/devices")
        assert headers["Authorization"] == f"Bearer {ACCESS}"
        return DEVICES

    code, out = run(tmp_path, ["status"], store=store, post=post, get=get)
    assert code == 0 and "| Hallway |" in out and "Flags:" in out
    assert calls == ["refresh_token"]
    code, out = run(tmp_path, ["status", "--json"], store=store, post=post, get=get)
    assert code == 0 and json.loads(out)["devices"][0]["name"] == "Hallway"
    for secret in (SECRET, REFRESH, ACCESS):
        assert secret not in out


def test_check_reports_booleans_only(tmp_path):
    configure(tmp_path)
    store = FakeStore(**{nest.ACCOUNT_SECRET: SECRET})
    code, out = run(tmp_path, ["check"], store=store)
    report = json.loads(out)
    assert report["client_secret_in_keychain"] is True
    assert report["refresh_token_in_keychain"] is False
    assert code == 1
    assert SECRET not in out


def test_keychain_refuses_dangerous_values():
    with pytest.raises(nest.NestError):
        nest.KeychainStore().set("a", 'bad"value')
