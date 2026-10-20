from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "ensure-terraform.sh"


def _run(path_dir, *args):
    env = {"PATH": f"{path_dir}:/usr/bin:/bin", "HOME": str(path_dir)}
    return subprocess.run(["bash", str(SCRIPT), *args], capture_output=True, text=True, env=env)


def _fake(tmp_path, name, body):
    p = tmp_path / name
    p.write_text(f"#!/bin/sh\n{body}\n")
    p.chmod(p.stat().st_mode | stat.S_IEXEC)


def test_already_installed(tmp_path):
    _fake(tmp_path, "terraform", 'echo "Terraform v1.9.8"')
    r = _run(tmp_path)
    assert r.returncode == 0
    assert "already installed" in r.stdout


def test_dry_run_prefers_tfenv(tmp_path):
    _fake(tmp_path, "tfenv", "exit 0")
    r = _run(tmp_path, "--dry-run")
    assert r.returncode == 0
    assert "tfenv install" in r.stdout


def test_dry_run_falls_back_to_download(tmp_path):
    r = _run(tmp_path, "--dry-run")
    assert r.returncode == 0
    assert "releases.hashicorp.com" in r.stdout
