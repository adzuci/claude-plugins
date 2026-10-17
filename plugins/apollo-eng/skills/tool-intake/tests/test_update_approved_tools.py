from __future__ import annotations

import json
from pathlib import Path

import pytest


updater = pytest.importorskip("update_approved_tools")


def export(tool_id: str = "baseten") -> dict:
    return {
        "schema_version": 1,
        "snapshot": {
            "effective_at": "2026-07-21T00:00:00Z",
            "owner": "Approval Source Owner",
            "reviewed_by": "Authorized Reviewer",
            "source_sha256": "a" * 64,
            "source_url": "https://example.com/controlled-export",
            "status": "AUTHORITATIVE",
        },
        "tools": [{
            "id": tool_id,
            "names": ["Baseten"],
            "domains": ["baseten.co"],
            "repositories": ["github.com/basetenlabs/truss"],
            "packages": [],
            "delivery": ["SaaS"],
            "status": "APPROVED_WITH_CONDITIONS",
            "scope": "Synthetic evaluation only",
            "version_scope": None,
            "data_classes": ["synthetic"],
            "conditions": ["Complete intake"],
            "owner": "Platform",
            "reviewed_at": "2026-07-21T00:00:00Z",
            "expires_at": None,
            "source_url": "https://example.com/approval/baseten",
        }],
    }


def test_validate_normalizes_and_hashes_import() -> None:
    result = updater.validate_export(export(), "b" * 64)

    assert result["tools"][0]["id"] == "baseten"
    assert result["snapshot"]["import_sha256"] == "b" * 64


def test_validate_rejects_duplicate_aliases() -> None:
    payload = export()
    duplicate = dict(payload["tools"][0])
    duplicate["id"] = "duplicate"
    payload["tools"].append(duplicate)

    with pytest.raises(ValueError, match="duplicate alias"):
        updater.validate_export(payload, "b" * 64)


def test_validate_rejects_non_authoritative_source() -> None:
    payload = export()
    payload["snapshot"]["status"] = "DRAFT"

    with pytest.raises(ValueError, match="AUTHORITATIVE"):
        updater.validate_export(payload, "b" * 64)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("id", 42, "id must be a string"),
        ("version_scope", [], "version_scope must be a string or null"),
        ("status", [], "status has an unsupported value"),
    ],
)
def test_validate_rejects_invalid_tool_field_types(field: str, value: object, message: str) -> None:
    payload = export()
    payload["tools"][0][field] = value

    with pytest.raises(ValueError, match=message):
        updater.validate_export(payload, "b" * 64)


def test_snapshot_schema_models_authoritative_and_unconfigured_states() -> None:
    schema_path = Path(__file__).parents[1] / "references" / "approved-tools.schema.json"
    snapshot_schema = json.loads(schema_path.read_text())["properties"]["snapshot"]

    statuses = {branch["properties"]["status"]["const"] for branch in snapshot_schema["oneOf"]}
    assert statuses == {"AUTHORITATIVE", "UNCONFIGURED"}
    assert snapshot_schema["oneOf"][0]["properties"]["source_url"]["pattern"] == "^https://"

    tool_source_url = json.loads(schema_path.read_text())["properties"]["tools"]["items"]["properties"]["source_url"]
    assert tool_source_url["pattern"] == "^https://"


def test_diff_reports_added_changed_and_removed() -> None:
    current = {"tools": [{"id": "old"}, {"id": "baseten", "scope": "old"}]}
    proposed = updater.validate_export(export(), "b" * 64)

    assert updater.diff_snapshots(current, proposed) == {
        "added": [],
        "changed": ["baseten"],
        "removed": ["old"],
    }


def test_atomic_write_round_trips_json(tmp_path) -> None:
    target = tmp_path / "snapshot.json"
    payload = updater.validate_export(export(), "b" * 64)

    updater.atomic_write(target, payload)

    assert json.loads(target.read_text())["tools"][0]["id"] == "baseten"


def test_apply_requires_explicit_removal_confirmation() -> None:
    changes = {"added": [], "changed": [], "removed": ["old-tool"]}

    with pytest.raises(ValueError, match="allow-removals"):
        updater.validate_apply(changes, "Authorized Reviewer", False)

    assert updater.validate_apply(changes, "Authorized Reviewer", True) == "Authorized Reviewer"


def run_main(monkeypatch, capsys, *argv: str) -> dict:
    monkeypatch.setattr("sys.argv", ["update_approved_tools.py", *argv])
    assert updater.main() == 0
    return json.loads(capsys.readouterr().out)


def test_apply_prints_local_audit_record_for_the_pr(tmp_path, monkeypatch, capsys) -> None:
    source = tmp_path / "export.json"
    source.write_text(json.dumps(export()))
    target = tmp_path / "approved-tools.json"

    summary = run_main(
        monkeypatch, capsys,
        "--source", str(source), "--target", str(target),
        "--apply", "--authorized-by", "Authorized Reviewer",
    )

    audit_path = tmp_path / "approved-tools.audit.jsonl"
    lines = audit_path.read_text().splitlines()
    assert len(lines) == 1
    assert summary["audit_log"] == str(audit_path)
    assert summary["audit_record"] == json.loads(lines[0])
    assert summary["audit_record"]["authorized_by"] == "Authorized Reviewer"


def test_dry_run_writes_no_audit_log(tmp_path, monkeypatch, capsys) -> None:
    source = tmp_path / "export.json"
    source.write_text(json.dumps(export()))
    target = tmp_path / "approved-tools.json"

    summary = run_main(monkeypatch, capsys, "--source", str(source), "--target", str(target))

    assert "audit_record" not in summary
    assert not (tmp_path / "approved-tools.audit.jsonl").exists()
    assert not target.exists()


def test_default_audit_log_is_gitignored() -> None:
    skill_dir = Path(__file__).resolve().parent.parent
    ignore = (skill_dir / ".gitignore").read_text().splitlines()
    assert "references/*.audit.jsonl" in ignore
