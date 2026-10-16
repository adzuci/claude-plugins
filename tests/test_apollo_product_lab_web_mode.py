from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "plugins" / "apollo-product-lab" / "scripts"))
import storage  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
PLUGIN = REPO / "plugins" / "apollo-product-lab"
STORAGE = PLUGIN / "scripts" / "storage.py"
PACKAGE = PLUGIN / "scripts" / "package.py"
CASES = json.loads((PLUGIN / "framework" / "eval" / "web-mode" / "detection-cases.json").read_text())["cases"]


def _clean_env(**extra):
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_CODE_REMOTE", "HARNESS_SURFACE", "HARNESS_REPO_ROOT")}
    env.update(extra)
    return env


def _storage(*args, cwd, env):
    return subprocess.run([sys.executable, str(STORAGE), *map(str, args)], cwd=cwd, env=env, capture_output=True, text=True)


def _git_init(path: Path):
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", "-b", "WO-1/harness-artifacts"], cwd=path, check=True)


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_storage_detection_cases(tmp_path, case):
    home = tmp_path / "home"
    home.mkdir()
    if case.get("home_writable", True) is False:
        (home / ".claude").write_text("not a directory")
    elif case.get("profile_storage"):
        (home / ".claude").mkdir()
        (home / ".claude" / "harness-profile.yml").write_text(f"persona: designer\nstorage: {case['profile_storage']}  # override\n")
    work = tmp_path / "work"
    if case["repo"] == "none":
        work.mkdir()
    else:
        _git_init(work)
        if case["repo"] == "git+ai":
            (work / ".ai").mkdir()
    args = ["detect"] + (["--surface", case["surface"]] if case.get("surface") else [])
    r = _storage(*args, cwd=work, env=_clean_env(HOME=str(home), **case.get("env", {})))
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    for key, want in case["expected"].items():
        if key == "skip_mentions":
            assert any(want in s for s in out["skip"]), out["skip"]
        else:
            assert out[key] == want, (key, out)
    assert out["say"].startswith(f"storage: {out['storage']}")


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0, reason="root ignores directory permissions")
def test_detection_falls_back_to_notion_when_the_record_folder_is_read_only(tmp_path):
    work = tmp_path / "work"
    _git_init(work)
    (work / ".ai").mkdir()
    (work / ".ai").chmod(0o500)
    try:
        out = json.loads(_storage("detect", cwd=work, env=_clean_env(HOME=str(tmp_path))).stdout)
    finally:
        (work / ".ai").chmod(0o700)
    assert out["storage"] == "notion" and any("not writable" in r for r in out["reasons"])


class FakeNotion:
    """Stands in for the Notion MCP: executes the calls storage.py prints and serves fetches."""

    def __init__(self):
        self.pages = {}
        self.calls = []

    def run(self, plan):
        self.calls.append(plan["tool"])
        args = plan["args"]
        if plan["tool"] == "notion-create-pages":
            assert len(args["pages"]) == 1
            assert ("parent" in args) != ("creation_mode" in args), "Notion refuses a parent with draft mode"
            page = args["pages"][0]
            pid = f"page-{len(self.pages) + 1}"
            self.pages[pid] = {"title": page["properties"]["title"], "parent": args.get("parent"), "content": page["content"]}
            return pid
        if plan["tool"] == "notion-update-page":
            assert args["command"] == "insert_content" and args["position"] == {"type": "end"}
            self.pages[args["page_id"]]["content"] += args["content"]
            return args["page_id"]
        raise AssertionError(plan["tool"])

    def fetch(self, pid, path: Path) -> Path:
        page = self.pages[pid]
        path.write_text(f'<page url="https://www.notion.so/{pid}">\n# {page["title"]}\n\n{page["content"]}\n</page>\n')
        return path


SNAPSHOT = """---
initiative: demo
run_id: demo-run1
stage: D.design
notion: https://www.notion.so/human-page
---

## Checks
| Check | Pass/Fail | Evidence |
|---|---|---|
| copy rule | checked | `register.md` |

```bash
echo nested fence
```
"""


INDEX = "| Stage | as_of | Gate | Path |\n|---|---|---|---|\n| D.design | 2026-10-09 | open | D.design.snapshot.md |\n"


def _record(tmp_path, rel, text):
    path = tmp_path / ".ai" / "demo" / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def test_notion_mode_snapshot_write_round_trips_byte_for_byte(tmp_path):
    src = _record(tmp_path, "runs/demo-run1/D.design.snapshot.md", SNAPSHOT)
    r = _storage("to-notion", src, "--initiative", "demo", "--parent-id", "run-page", cwd=tmp_path, env=_clean_env())
    assert r.returncode == 0, r.stderr
    [plan] = json.loads(r.stdout)
    assert plan["record_key"] == "runs/demo-run1/D.design.snapshot.md"
    assert plan["args"]["parent"] == {"page_id": "run-page"}
    content = plan["args"]["pages"][0]["content"]
    assert ".ai/" not in content and str(tmp_path) not in content
    notion = FakeNotion()
    pid = notion.run(plan)
    fetched = notion.fetch(pid, tmp_path / "fetched.md")
    out_root = tmp_path / "restored"
    r = _storage("from-notion", fetched, "--initiative", "demo", "--root", out_root, cwd=tmp_path, env=_clean_env())
    assert r.returncode == 0, r.stderr
    assert (out_root / ".ai" / "demo" / "runs" / "demo-run1" / "D.design.snapshot.md").read_text() == SNAPSHOT


def test_notion_mode_refuses_a_hand_edited_record(tmp_path):
    src = _record(tmp_path, "runs/demo-run1/D.design.snapshot.md", SNAPSHOT)
    [plan] = json.loads(_storage("to-notion", src, "--initiative", "demo", cwd=tmp_path, env=_clean_env()).stdout)
    assert plan["args"]["parent"] == {"resolve": "run:demo-run1"}
    notion = FakeNotion()
    pid = notion.run(plan)
    body = notion.pages[pid]["content"]
    b64 = re.search(r"```text\n(.*?)\n```", body, re.S).group(1)
    edited = base64.b64encode(base64.b64decode("".join(b64.split())).replace(b"copy rule", b"copy rule edited")).decode()
    notion.pages[pid]["content"] = body.replace(b64, edited)
    r = _storage("from-notion", notion.fetch(pid, tmp_path / "f.md"), "--stdout", cwd=tmp_path, env=_clean_env())
    assert r.returncode == 3 and "sha256" in r.stderr


def test_notion_mode_ledger_appends_validate_and_refuse_duplicates(tmp_path):
    first = {"ts": "2026-10-09T10:00:00+00:00", "run_id": "demo-run1", "event_id": "e001-intake", "initiative": "demo",
             "task_class": "A.intake", "agent": "harness-intake", "outcome": "resolved-clean"}
    ledger = _record(tmp_path, "ledger.jsonl", json.dumps(first) + "\n")
    [plan] = json.loads(_storage("to-notion", ledger, "--initiative", "demo", "--parent-id", "root", cwd=tmp_path, env=_clean_env()).stdout)
    notion = FakeNotion()
    pid = notion.run(plan)
    base = ["demo", "--run", "demo-run1", "--stage", "D.design", "--agent", "harness-snapshot", "--outcome", "resolved-clean"]
    r = _storage("ledger-entry", notion.fetch(pid, tmp_path / "l.md"), "--", *base, "--event", "e002-design", cwd=tmp_path, env=_clean_env())
    assert r.returncode == 0, r.stderr
    call = json.loads(r.stdout)
    call["args"]["page_id"] = pid
    notion.run(call)
    dup = _storage("ledger-entry", notion.fetch(pid, tmp_path / "l2.md"), "--", *base, "--event", "e002-design", cwd=tmp_path, env=_clean_env())
    assert dup.returncode == 1 and "already recorded" in dup.stderr
    bad = _storage("ledger-entry", tmp_path / "l2.md", "--", "demo", "--run", "demo-run1", "--stage", "bogus", "--agent", "a",
                   "--outcome", "resolved-clean", "--event", "e003", cwd=tmp_path, env=_clean_env())
    assert bad.returncode == 1
    tampered = tmp_path / "l3.md"
    tampered.write_text((tmp_path / "l2.md").read_text().replace('"harness-snapshot"', '"someone-else"'))
    assert _storage("from-notion", tampered, "--stdout", cwd=tmp_path, env=_clean_env()).returncode == 3
    restored = _storage("from-notion", tmp_path / "l2.md", "--stdout", cwd=tmp_path, env=_clean_env())
    lines = [json.loads(l) for l in restored.stdout.splitlines()]
    assert [l["event_id"] for l in lines] == ["e001-intake", "e002-design"]
    assert notion.calls == ["notion-create-pages", "notion-update-page"]


def test_notion_mode_profile_is_private_and_round_trips(tmp_path):
    profile = tmp_path / "harness-profile.yml"
    profile.write_text("persona: designer\nsurface: claude-ai-chat\nstorage: notion\n")
    refused = _storage("to-notion", profile, "--initiative", "demo", cwd=tmp_path, env=_clean_env())
    assert refused.returncode == 1 and "profile-to-notion" in refused.stderr
    plan = json.loads(_storage("profile-to-notion", profile, "--name", "Dana", cwd=tmp_path, env=_clean_env()).stdout)
    assert plan["args"]["creation_mode"] == "draft" and "parent" not in plan["args"]
    assert plan["args"]["pages"][0]["properties"]["title"] == "Harness profile (Dana)"
    notion = FakeNotion()
    out = _storage("from-notion", notion.fetch(notion.run(plan), tmp_path / "p.md"), "--stdout", cwd=tmp_path, env=_clean_env())
    assert out.returncode == 0 and out.stdout == profile.read_text()
    _record(tmp_path, "harness-profile.yml", "persona: x\n")
    _record(tmp_path, "harness-manifest.md", "x\n")
    keys = [p["record_key"] for p in json.loads(_storage("to-notion", tmp_path / ".ai" / "demo", "--initiative", "demo", cwd=tmp_path, env=_clean_env()).stdout)]
    assert keys == ["harness-manifest.md"]


def _page(tmp_path, rel, text, name="f.md"):
    src = _record(tmp_path, rel, text)
    [plan] = json.loads(_storage("to-notion", src, "--initiative", "demo", cwd=tmp_path, env=_clean_env()).stdout)
    notion = FakeNotion()
    pid = notion.run(plan)
    return notion, pid, notion.fetch(pid, tmp_path / name)


def test_round_trip_keeps_exact_bytes_even_without_a_final_newline_or_with_escape_lookalikes(tmp_path):
    tricky = "no final newline `\u200b`` and ```fence``` and trailing spaces   "
    _, _, fetched = _page(tmp_path, "knowledge/odd.md", tricky)
    out = _storage("from-notion", fetched, "--stdout", cwd=tmp_path, env=_clean_env())
    assert out.returncode == 0 and out.stdout == tricky


def test_import_refuses_path_escapes_overwrites_and_unverifiable_hashes(tmp_path):
    _, _, fetched = _page(tmp_path, "runs/demo-run1/D.design.snapshot.md", SNAPSHOT)
    root = tmp_path / "dest"
    evil = tmp_path / "evil.md"
    evil.write_text(fetched.read_text().replace("record_key: runs/demo-run1/D.design.snapshot.md", "record_key: ../../outside.txt"))
    r = _storage("from-notion", evil, "--initiative", "demo", "--root", root, cwd=tmp_path, env=_clean_env())
    assert r.returncode == 1 and "unsafe record_key" in r.stderr and not (tmp_path / "outside.txt").exists()
    assert _storage("from-notion", fetched, "--initiative", "../x", "--root", root, cwd=tmp_path, env=_clean_env()).returncode == 1
    dest = root / ".ai" / "demo" / "runs" / "demo-run1" / "D.design.snapshot.md"
    dest.parent.mkdir(parents=True)
    dest.write_text("newer local edit\n")
    r = _storage("from-notion", fetched, "--initiative", "demo", "--root", root, cwd=tmp_path, env=_clean_env())
    assert r.returncode == 1 and "different content" in r.stderr and dest.read_text() == "newer local edit\n"
    assert _storage("from-notion", fetched, "--initiative", "demo", "--root", root, "--replace", cwd=tmp_path, env=_clean_env()).returncode == 0
    assert dest.read_text() == SNAPSHOT
    assert "unchanged" in _storage("from-notion", fetched, "--initiative", "demo", "--root", root, cwd=tmp_path, env=_clean_env()).stdout
    nohash = tmp_path / "nohash.md"
    nohash.write_text(re.sub(r"^sha256: .*$", "sha256: unavailable (no code execution)", fetched.read_text(), flags=re.M))
    r = _storage("from-notion", nohash, "--stdout", cwd=tmp_path, env=_clean_env())
    assert r.returncode == 1 and "--unverified" in r.stderr
    assert _storage("from-notion", nohash, "--stdout", "--unverified", cwd=tmp_path, env=_clean_env()).stdout == SNAPSHOT
    dest.unlink()
    r = _storage("from-notion", nohash, "--initiative", "demo", "--root", root, "--unverified", cwd=tmp_path, env=_clean_env())
    assert r.returncode == 0 and "unverified" in r.stdout
    log = [json.loads(l) for l in (root / ".ai" / "demo" / "unverified-imports.jsonl").read_text().splitlines()]
    assert log[0]["record_key"] == "runs/demo-run1/D.design.snapshot.md"


LEAKS = {
    "mac-home": "/Users/dana/leadgenie/app.rb",
    "mac-home-lowercase": "/users/dana/x",
    "linux-home": "/home/dana/x",
    "windows-backslash": "C:\\Users\\dana\\x",
    "windows-forward-slash": "C:/Users/dana/x",
    "windows-other-drive": "D:\\work\\x",
    "unc-backslash": "\\\\fileserver\\share\\x",
    "unc-forward-slash": "//fileserver/share/x",
    "env-userprofile": "%USERPROFILE%\\x",
    "env-appdata": "%LOCALAPPDATA%\\x",
    "env-home": "$HOME/x",
    "env-home-braced": "${HOME}/x",
    "powershell-env": "$env:USERPROFILE\\x",
    "tilde": "~/notes/x.md",
    "tilde-user": "~dana/x",
    "macos-temp": "/private/var/folders/ab/T/x",
    "var-folders": "/var/folders/ab/T/x",
    "private-tmp": "/private/tmp/x",
    "tmp": "/tmp/x",
    "volumes": "/Volumes/Work/x",
    "wsl-mount": "/mnt/c/Users/dana/x",
    "file-url": "file:///Users/dana/x",
    "unicode-escape": "\\u002FUsers\\u002Fdana\\u002Fx",
    "braced-unicode-escape": "\\u{2F}home\\u{2F}dana",
    "hex-escape": "\\x2Fhome\\x2Fdana\\x2Fx",
    "escaped-slash": "\\/Users\\/dana\\/x",
    "url-encoded": "%2FUsers%2Fdana%2Fx",
    "html-entity": "&#47;Users&#47;dana&#47;x",
    "fullwidth-slash": "\uff0fUsers\uff0fdana\uff0fx",
    "zero-width-split": "/Us\u200bers/dana/x",
    "double-slash-absolute": "//Users/dana/x",
    "url-encoded-6x": "%2525252525252FUsers%2525252525252Fdana",
    "base64": "L1VzZXJzL2RhbmEveA==",
    "yaml-binary-in-a-string": "path: !!binary L1VzZXJzL2RhbmEveA==",
}
SAFE = [
    "runs/demo-run1/D.design.snapshot.md",
    "packs/billing/docs/credit-usage-surface.md and src/home/page.tsx",
    "https://www.notion.so/abc123 and https://github.com/apolloio/leadgenie/blob/master/app/Users/x.rb",
    "http://localhost:3000/#/home/dashboard",
    "about ~5/10 users, ratio 3/4, ~~struck/out~~",
    "`.ai/demo/ledger.jsonl` at commit a424649",
    "https://example.com/login?next=/home/dashboard and //example.com/docs/index.html",
    "src//home/page.tsx",
    "sha256: " + "ab12" * 16,
]


def _forms(leak):
    """The same leak as markdown, frontmatter, a nested JSON value, a JSON key, YAML, and JSONL."""
    return {
        "x.snapshot.md": f"evidence: {leak}\n",
        "fm.snapshot.md": f"---\ninitiative: demo\nevidence: \"{leak}\"\n---\n\nbody\n",
        "nested.json": json.dumps({"a": {"b": [{"c": leak}]}}),
        "keyed.json": json.dumps({leak: "value"}),
        "list.yml": f"items:\n  - name: x\n    path: \"{leak}\"\n",
        "lines.jsonl": json.dumps({"ok": "runs/x.md"}) + "\n" + json.dumps({"evidence": [leak]}) + "\n",
    }


@pytest.mark.parametrize("leak", list(LEAKS.values()), ids=list(LEAKS))
def test_export_refuses_laptop_paths_in_every_encoding(tmp_path, leak):
    for name, text in _forms(leak).items():
        src = _record(tmp_path, f"runs/demo-run1/{name}", text)
        r = _storage("to-notion", src, "--initiative", "demo", cwd=tmp_path, env=_clean_env())
        assert r.returncode == 1 and "laptop path" in r.stderr, (name, r.stdout[:200])
        src.unlink()


def test_export_reads_paths_only_a_yaml_parser_reveals(tmp_path):
    b64 = base64.b64encode(b"/Users/dana/x").decode()
    for name, text in {
        "value.yml": "path: \"/Us\\\n  ers/dana\"\n",
        "key.yml": "? \"/Us\\\n  ers/dana\"\n: 1\n",
        "fm.snapshot.md": f"---\nevidence: !!binary {b64}\n---\n\nbody\n",
    }.items():
        src = _record(tmp_path, f"runs/demo-run1/{name}", text)
        r = _storage("to-notion", src, "--initiative", "demo", cwd=tmp_path, env=_clean_env())
        assert r.returncode == 1 and "laptop path" in r.stderr, name


def test_export_refuses_a_laptop_path_in_utf16_and_in_a_bulk_export(tmp_path):
    src = _record(tmp_path, "runs/demo-run1/wide.md", "")
    src.write_bytes("evidence: /Users/dana/x\n".encode("utf-16"))
    assert _storage("to-notion", src, "--initiative", "demo", cwd=tmp_path, env=_clean_env()).returncode == 1
    src.unlink()
    _record(tmp_path, "runs/demo-run1/ok.md", "fine\n")
    _record(tmp_path, "runs/demo-run1/zz.snapshot.md", "see ~/x\n")
    r = _storage("to-notion", tmp_path / ".ai" / "demo", "--initiative", "demo", cwd=tmp_path, env=_clean_env())
    assert r.returncode == 1 and "laptop path" in r.stderr and r.stdout == ""


@pytest.mark.parametrize("safe", SAFE)
def test_export_and_ledger_keep_repo_relative_paths_and_urls(tmp_path, safe):
    for name, text in _forms(safe).items():
        storage.check_publishable(name, text.encode())
    _, _, page = _page(tmp_path, "ledger.jsonl", json.dumps(LEDGER_FIRST) + "\n", name="safe-ledger.md")
    r = _storage("ledger-entry", page, "--", *LEDGER_ARGS, "--evidence", safe, "--note", safe, cwd=tmp_path, env=_clean_env())
    assert r.returncode == 0, r.stderr


LEDGER_FIRST = {"ts": "2026-10-09T10:00:00+00:00", "run_id": "r1", "event_id": "e001", "task_class": "A.intake", "agent": "a",
                "outcome": "resolved-clean"}
LEDGER_ARGS = ["demo", "--run", "r1", "--stage", "D.design", "--agent", "a", "--outcome", "resolved-clean", "--event", "e002"]


@pytest.mark.parametrize("leak", list(LEAKS.values()), ids=list(LEAKS))
def test_ledger_entry_refuses_laptop_paths_in_every_encoding(tmp_path, leak):
    _, _, page = _page(tmp_path, "ledger.jsonl", json.dumps(LEDGER_FIRST) + "\n")
    for extra in (["--evidence", leak], ["--note", leak], ["--note", json.dumps({leak: 1})],
                  ["--note", f"---\nevidence: \"{leak}\"\n---"]):
        r = _storage("ledger-entry", page, "--", *LEDGER_ARGS, *extra, cwd=tmp_path, env=_clean_env())
        assert r.returncode == 1 and "laptop path" in r.stderr, (extra, r.stdout)


def test_export_refuses_symlinks_hard_links_and_files_outside_the_initiative(tmp_path):
    secret = tmp_path / "credentials.txt"
    secret.write_text("token: s3cr3t\n")
    _record(tmp_path, "runs/demo-run1/index.md", INDEX)
    folder = tmp_path / ".ai" / "demo"
    link = folder / "runs" / "demo-run1" / "creds.md"
    link.symlink_to(secret)
    for target in (folder, link):
        r = _storage("to-notion", target, "--initiative", "demo", cwd=tmp_path, env=_clean_env())
        assert r.returncode == 1 and "symlink" in r.stderr and "s3cr3t" not in r.stdout, target
    link.unlink()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "x.md").write_text("token: s3cr3t\n")
    (folder / "linked-dir").symlink_to(outside, target_is_directory=True)
    for target in (folder, folder / "linked-dir", folder / "linked-dir" / "x.md"):
        r = _storage("to-notion", target, "--initiative", "demo", cwd=tmp_path, env=_clean_env())
        assert r.returncode == 1 and "symlink" in r.stderr and "s3cr3t" not in r.stdout, (target, r.stderr)
    dotted = _storage("to-notion", f"{folder}/linked-dir/../runs/demo-run1/index.md", "--initiative", "demo", cwd=tmp_path, env=_clean_env())
    assert dotted.returncode == 0 and [p["record_key"] for p in json.loads(dotted.stdout)] == ["runs/demo-run1/index.md"]
    (folder / "linked-dir").unlink()
    os.link(secret, folder / "hard.md")
    r = _storage("to-notion", folder, "--initiative", "demo", cwd=tmp_path, env=_clean_env())
    assert r.returncode == 1 and "hard link" in r.stderr
    (folder / "hard.md").unlink()
    r = _storage("to-notion", secret, "--initiative", "demo", cwd=tmp_path, env=_clean_env())
    assert r.returncode == 1 and "not under .ai/demo" in r.stderr
    real = tmp_path / "elsewhere" / "demo"
    real.mkdir(parents=True)
    (real / "x.md").write_text("fine\n")
    (tmp_path / "repo2" / ".ai").mkdir(parents=True)
    (tmp_path / "repo2" / ".ai" / "demo").symlink_to(real, target_is_directory=True)
    r = _storage("to-notion", tmp_path / "repo2" / ".ai" / "demo", "--initiative", "demo", cwd=tmp_path, env=_clean_env())
    assert r.returncode == 1 and "symlink" in r.stderr
    assert [p["record_key"] for p in json.loads(_storage("to-notion", folder, "--initiative", "demo", cwd=tmp_path,
                                                         env=_clean_env()).stdout)] == ["runs/demo-run1/index.md"]


def _hand_built_ledger(tmp_path):
    """A ledger page as claude.ai chat writes it with code execution off: later events carry no real hash."""
    _, _, page = _page(tmp_path, "ledger.jsonl", json.dumps(LEDGER_FIRST) + "\n", name="hb.md")
    second = json.dumps({**LEDGER_FIRST, "event_id": "e002", "task_class": "D.design"})
    third = json.dumps({**LEDGER_FIRST, "event_id": "e003", "task_class": "D.design"})
    text = page.read_text().replace("</page>", f"```text\n{second}\nsha256: unavailable (no code execution)\n```\n\n```text\n{third}\n```\n</page>")
    page.write_text(text)
    return page, second, third


def test_unverified_ledger_import_keeps_hand_built_events_and_logs_them(tmp_path):
    page, second, third = _hand_built_ledger(tmp_path)
    r = _storage("from-notion", page, "--stdout", cwd=tmp_path, env=_clean_env())
    assert r.returncode == 1 and "--unverified" in r.stderr
    r = _storage("from-notion", page, "--stdout", "--unverified", cwd=tmp_path, env=_clean_env())
    assert r.returncode == 0 and r.stdout == json.dumps(LEDGER_FIRST) + "\n" + second + "\n" + third + "\n"
    root = tmp_path / "dest"
    r = _storage("from-notion", page, "--initiative", "demo", "--root", root, "--unverified", cwd=tmp_path, env=_clean_env())
    assert r.returncode == 0 and "unverified" in r.stdout
    [entry] = [json.loads(l) for l in (root / ".ai" / "demo" / "unverified-imports.jsonl").read_text().splitlines()]
    assert entry["record_key"] == "ledger.jsonl" and entry["unverified_events"] == ["e002", "e003"] and entry["source"] == "hb.md"
    assert _storage("ledger-entry", page, "--", *LEDGER_ARGS[:-1], "e004", cwd=tmp_path, env=_clean_env()).returncode == 1
    r = _storage("ledger-entry", page, "--unverified", "--", *LEDGER_ARGS[:-1], "e004", cwd=tmp_path, env=_clean_env())
    assert r.returncode == 0, r.stderr
    dup = _storage("ledger-entry", page, "--unverified", "--", *LEDGER_ARGS, cwd=tmp_path, env=_clean_env())
    assert dup.returncode == 1 and "already recorded" in dup.stderr


def test_unverified_import_still_refuses_a_hash_mismatch(tmp_path):
    page, _, _ = _hand_built_ledger(tmp_path)
    tampered = tmp_path / "t.md"
    tampered.write_text(page.read_text().replace('"e001"', '"e999"', 1))
    r = _storage("from-notion", tampered, "--stdout", "--unverified", cwd=tmp_path, env=_clean_env())
    assert r.returncode == 3 and "sha256" in r.stderr
    _, _, record = _page(tmp_path, "runs/demo-run1/D.design.snapshot.md", SNAPSHOT, name="rec.md")
    body = record.read_text()
    b64 = re.search(r"```text\n(.*?)\n```", body, re.S).group(1)
    edited = base64.b64encode(base64.b64decode("".join(b64.split())) + b"x").decode()
    record.write_text(body.replace(b64, edited))
    assert _storage("from-notion", record, "--stdout", "--unverified", cwd=tmp_path, env=_clean_env()).returncode == 3


def test_ledger_entry_refuses_laptop_paths_and_damaged_pages(tmp_path):
    first = {"ts": "2026-10-09T10:00:00+00:00", "run_id": "r1", "event_id": "e001", "task_class": "A.intake", "agent": "a", "outcome": "resolved-clean"}
    notion, pid, page = _page(tmp_path, "ledger.jsonl", json.dumps(first) + "\n")
    args = ["demo", "--run", "r1", "--stage", "D.design", "--agent", "a", "--outcome", "resolved-clean", "--event", "e002"]
    r = _storage("ledger-entry", page, "--", *args, "--evidence", "/Users/dana/x.md", cwd=tmp_path, env=_clean_env())
    assert r.returncode == 1 and "laptop path" in r.stderr
    r = _storage("ledger-entry", page, "--", *args, "--evidence", "C:\\Users\\dana\\x.md", cwd=tmp_path, env=_clean_env())
    assert r.returncode == 1 and "laptop path" in r.stderr
    win = {**first, "event_id": "e009", "evidence": ["C:\\Users\\dana\\x.md"]}
    winsrc = _record(tmp_path, "ledger.jsonl", json.dumps(first) + "\n" + json.dumps(win) + "\n")
    assert _storage("to-notion", winsrc, "--initiative", "demo", cwd=tmp_path, env=_clean_env()).returncode == 1
    unclosed = tmp_path / "unclosed.md"
    unclosed.write_text(page.read_text().rstrip().rsplit("```", 1)[0])
    assert _storage("from-notion", unclosed, "--stdout", cwd=tmp_path, env=_clean_env()).returncode == 1
    bad = _record(tmp_path, "runs/r1/../../ledger.jsonl", "x\r\n")
    assert _storage("to-notion", bad, "--initiative", "demo", cwd=tmp_path, env=_clean_env()).returncode == 1


def test_record_sync_reads_a_profile_fetched_from_notion(tmp_path):
    repo = tmp_path / "repo"
    _git_init(repo)
    (repo / ".ai" / "demo").mkdir(parents=True)
    fetched = tmp_path / "profile.yml"
    fetched.write_text("persona: designer\ncollaboration: team\n")
    env = _clean_env(HOME=str(tmp_path / "nohome"), HARNESS_REPO_ROOT=str(repo))
    sync = PLUGIN / "scripts" / "record-sync.sh"
    solo = subprocess.run(["bash", str(sync), "pull", "demo"], cwd=repo, env=env, capture_output=True, text=True)
    assert "solo" in solo.stdout
    team = subprocess.run(["bash", str(sync), "pull", "demo"], cwd=repo, env={**env, "HARNESS_PROFILE": str(fetched)}, capture_output=True, text=True)
    assert "solo" not in team.stdout and team.returncode == 2


RECORD_WRITERS = [
    "skills/harness-snapshot/SKILL.md",
    "skills/harness-council/SKILL.md",
    "skills/harness-intake/SKILL.md",
    "skills/product-harness-init/SKILL.md",
    "skills/design-diff/SKILL.md",
    "skills/artifact-audit/SKILL.md",
    "skills/harness-escape/SKILL.md",
    "agents/product-orchestrator.md",
]


def test_every_record_writer_resolves_storage_first():
    for rel in RECORD_WRITERS:
        text = (PLUGIN / rel).read_text()
        assert "storage.py" in text and "detect" in text and "notion" in text, rel
        assert "no Bash and no Write tool" in text, rel


def test_onboarding_asks_the_surface_and_stores_the_profile_in_notion_on_the_web():
    text = (PLUGIN / "skills/harness-onboard/SKILL.md").read_text()
    assert "Where are you running this?" in text
    for surface in ("terminal", "Code tab", "claude.ai/code", "claude.ai chat"):
        assert surface in text, surface
    assert "creation_mode" in text and "Harness profile" in text and "notion_records_root" in text
    assert "never a\n   PR or a staging link" in text or "never a PR or a staging link" in text
    template = (PLUGIN / "framework/templates/harness-profile.yml").read_text()
    assert "storage:" in template and "surface:" in template


def test_designer_flow_runs_every_lens_and_never_asks_for_a_pr():
    intake = (PLUGIN / "skills/harness-intake/SKILL.md").read_text()
    designer = intake.split("**Designer**", 1)[1].split("**Engineer**", 1)[0]
    for word in ("thought or a PRD", "Competitive analysis", "AI lens", "Reuse audit", "fabric-core", "Storybook",
                 "Platform lens", "CSV import", "Review panel", "never ask a designer for a PR"):
        assert word in designer, word
    reviewer = (PLUGIN / "agents/product-reviewer.md").read_text()
    assert "Platform mode" in reviewer and "one proposed reusable flow" in reviewer
    council = (PLUGIN / "skills/harness-council/SKILL.md").read_text()
    assert "Designer panel" in council and "engineering feasibility" in council and "degraded: in-thread lenses" in council


def test_session_start_reports_cloud_storage_without_a_profile(tmp_path):
    out = subprocess.run(["bash", str(PLUGIN / "scripts/session-start.sh")], cwd=tmp_path, input="{}", capture_output=True, text=True,
                         env=_clean_env(HOME=str(tmp_path), CLAUDE_CODE_REMOTE="true", CLAUDE_PLUGIN_ROOT=str(PLUGIN))).stdout
    assert "storage: notion" in out and "Harness profile" in out


def test_package_builds_an_uploadable_plugin_and_chat_skills(tmp_path):
    r = subprocess.run([sys.executable, str(PACKAGE), "--out", str(tmp_path)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    with zipfile.ZipFile(tmp_path / "apollo-product-lab.zip") as z:
        names = z.namelist()
        assert ".claude-plugin/plugin.json" in names and "BUILD" in names and "scripts/storage.py" in names
        assert not any("__pycache__" in n or n.startswith("apollo-product-lab/") for n in names)
    skills = sorted(p.name for p in (tmp_path / "skills").iterdir())
    yaml = pytest.importorskip("yaml")
    assert skills == sorted(f"{s}.zip" for s in ("harness-onboard", "harness-intake", "harness-snapshot", "harness-council",
                                                  "artifact-audit", "product-harness-init"))
    for zname in skills:
        skill = zname[:-4]
        with zipfile.ZipFile(tmp_path / "skills" / zname) as z:
            names = z.namelist()
            assert all(n.startswith(f"{skill}/") for n in names)
            assert f"{skill}/scripts/storage.py" in names and f"{skill}/framework/45-web-mode-and-storage.md" in names
            assert not any("/framework/eval/" in n for n in names)
            md = z.read(f"{skill}/SKILL.md").decode()
            fm = yaml.safe_load(re.match(r"^---\n(.*?)\n---\n", md, re.S).group(1))
            assert list(fm) == ["name", "description"] and fm["name"] == skill
            assert "<" not in fm["description"] and ">" not in fm["description"] and len(fm["description"]) <= 1024
            body = md.split("---", 2)[2]
            for ref in set(re.findall(r"\b((?:framework|skills|agents|scripts)/[\w./-]+\.(?:md|yml|py|json))\b", body)):
                if "*" in ref or "<" in ref or "INITIATIVE" in ref:
                    continue
                assert f"{skill}/{ref}" in names, (skill, ref)
            for n in names:
                if n.endswith((".md", ".yml", ".py", ".sh", ".json")):
                    assert "${CLAUDE_PLUGIN_ROOT}" not in z.read(n).decode(), n


def test_publish_check_rejects_what_it_cannot_scan(tmp_path):
    deep = "a: " + "{b: " * 700 + "!!binary L1VzZXJzL2RhbmEveA==" + "}" * 700 + "\n"
    src = _record(tmp_path, "runs/demo-run1/deep.yml", deep)
    r = _storage("to-notion", src, "--initiative", "demo", cwd=tmp_path, env=_clean_env())
    assert r.returncode == 1 and "unscannable" in r.stderr
    noyaml = tmp_path / "noyaml"
    noyaml.mkdir()
    (noyaml / "yaml.py").write_text("raise ImportError('blocked for the test')\n")
    src.write_text("fine\n")
    r = _storage("to-notion", src, "--initiative", "demo", cwd=tmp_path, env=_clean_env(PYTHONPATH=str(noyaml)))
    assert r.returncode == 1 and "PyYAML" in r.stderr


def test_export_never_reads_through_a_folder_swapped_for_a_symlink_mid_export(tmp_path, monkeypatch):
    _record(tmp_path, "runs/demo-run1/index.md", INDEX)
    outside = tmp_path / "outside" / "demo-run1"
    outside.mkdir(parents=True)
    (outside / "index.md").write_text("| token |\n|---|\n| s3cr3t |\n")
    folder = tmp_path / ".ai" / "demo"
    real_open = storage._open_initiative

    def swap_after_root_is_pinned(repo, initiative):
        fd = real_open(repo, initiative)
        (folder / "runs").rename(folder / "runs.real")
        (folder / "runs").symlink_to(outside.parent, target_is_directory=True)
        return fd

    monkeypatch.setattr(storage, "_open_initiative", swap_after_root_is_pinned)
    for target in (folder / "runs" / "demo-run1" / "index.md", folder / "runs", folder):
        with pytest.raises(storage.RecordError, match="symlink"):
            storage.to_notion(str(target), "demo", None)
        (folder / "runs").unlink()
        (folder / "runs.real").rename(folder / "runs")
    monkeypatch.setattr(storage, "_open_initiative", real_open)
    real_walk = storage._walk

    def swap_after_parent_is_pinned(dir_fd, prefix, *rest):
        if prefix == ["runs"]:
            (folder / "runs").rename(folder / "runs.real")
            (folder / "runs").symlink_to(outside.parent, target_is_directory=True)
        return real_walk(dir_fd, prefix, *rest)

    monkeypatch.setattr(storage, "_walk", swap_after_parent_is_pinned)
    [plan] = storage.to_notion(str(folder / "runs"), "demo", None)
    assert base64.b64decode(re.search(r"```text\n(.*?)\n```", plan["args"]["pages"][0]["content"], re.S).group(1)) == INDEX.encode()


def test_ledger_import_refuses_other_fences_stray_events_and_shrinking(tmp_path):
    page, second, third = _hand_built_ledger(tmp_path)
    text = page.read_text()
    for name, evil in {
        "tilde": text.replace(f"```text\n{third}\n```", f"~~~text\n{third}\n~~~"),
        "indented": text.replace(f"```text\n{third}\n```", f" ```text\n {third}\n ```"),
        "stray": text.replace(f"```text\n{third}\n```", third),
    }.items():
        bad = tmp_path / f"{name}.md"
        bad.write_text(evil)
        r = _storage("from-notion", bad, "--stdout", "--unverified", cwd=tmp_path, env=_clean_env())
        assert r.returncode == 1 and r.stdout == "", name
    _, _, record = _page(tmp_path, "runs/demo-run1/D.design.snapshot.md", SNAPSHOT, name="rec.md")
    extra = tmp_path / "extra.md"
    extra.write_text(record.read_text().replace("</page>", "~~~text\nsecond body\n~~~\n</page>"))
    r = _storage("from-notion", extra, "--stdout", cwd=tmp_path, env=_clean_env())
    assert r.returncode == 1 and "fence" in r.stderr
    root = tmp_path / "dest"
    assert _storage("from-notion", page, "--initiative", "demo", "--root", root, "--unverified", cwd=tmp_path, env=_clean_env()).returncode == 0
    shorter = tmp_path / "shorter.md"
    shorter.write_text(text.replace(f"```text\n{third}\n```", ""))
    r = _storage("from-notion", shorter, "--initiative", "demo", "--root", root, "--unverified", "--replace", cwd=tmp_path, env=_clean_env())
    assert r.returncode == 1 and "append-only" in r.stderr
    assert (root / ".ai" / "demo" / "ledger.jsonl").read_text().count("\n") == 3


def test_hash_mismatch_cannot_be_downgraded(tmp_path):
    _, _, page = _page(tmp_path, "ledger.jsonl", json.dumps(LEDGER_FIRST) + "\n", name="up.md")
    upper = tmp_path / "upper.md"
    upper.write_text(re.sub(r"sha256: ([0-9a-f]{64})", lambda m: "sha256: " + m.group(1).upper(), page.read_text()))
    assert _storage("from-notion", upper, "--stdout", cwd=tmp_path, env=_clean_env()).returncode == 0
    tampered = tmp_path / "t.md"
    tampered.write_text(upper.read_text().replace('"e001"', '"e999"'))
    assert _storage("from-notion", tampered, "--stdout", "--unverified", cwd=tmp_path, env=_clean_env()).returncode == 3
    r = _storage("ledger-entry", tampered, "--unverified", "--", *LEDGER_ARGS, cwd=tmp_path, env=_clean_env())
    assert r.returncode == 3 and "sha256" in r.stderr
    _, _, record = _page(tmp_path, "runs/demo-run1/D.design.snapshot.md", SNAPSHOT, name="rec.md")
    shadowed = tmp_path / "shadow.md"
    shadowed.write_text(record.read_text().replace("format: harness-record/2", "sha256: unavailable\nformat: harness-record/2"))
    r = _storage("from-notion", shadowed, "--stdout", "--unverified", cwd=tmp_path, env=_clean_env())
    assert r.returncode == 1 and "repeats its sha256" in r.stderr


def test_unverified_import_of_identical_bytes_still_records_provenance(tmp_path):
    page, second, third = _hand_built_ledger(tmp_path)
    root = tmp_path / "dest"
    ledger = root / ".ai" / "demo" / "ledger.jsonl"
    ledger.parent.mkdir(parents=True)
    ledger.write_text(json.dumps(LEDGER_FIRST) + "\n" + second + "\n" + third + "\n")
    for _ in range(2):
        r = _storage("from-notion", page, "--initiative", "demo", "--root", root, "--unverified", cwd=tmp_path, env=_clean_env())
        assert r.returncode == 0 and "unchanged" in r.stdout and "unverified" in r.stdout
    [entry] = [json.loads(l) for l in (root / ".ai" / "demo" / "unverified-imports.jsonl").read_text().splitlines()]
    assert entry["unverified_events"] == ["e002", "e003"]


def test_round5_regressions_url_cells_tilde_yaml_blocks_and_nested_initiative_folders(tmp_path):
    for name, text in {
        "table.md": "| link | evidence |\n|---|---|\n|https://example.com|/Users/dana/x|\n",
        "tilde.md": "# Notes\n\n~~~yaml\npath: \"/Us\\\n  ers/dana/x\"\n~~~\n",
        "indented.md": "# Notes\n\n   ```yaml\npath: \"/Us\\\n  ers/dana/x\"\n   ```\n",
    }.items():
        src = _record(tmp_path, f"runs/demo-run1/{name}", text)
        r = _storage("to-notion", src, "--initiative", "demo", cwd=tmp_path, env=_clean_env())
        assert r.returncode == 1 and "laptop path" in r.stderr, name
        src.unlink()
    outside = tmp_path / "outside"
    (outside / ".ai" / "demo").mkdir(parents=True)
    (outside / ".ai" / "demo" / "x.md").write_text("token: s3cr3t\n")
    folder = tmp_path / ".ai" / "demo"
    (folder / "link").symlink_to(outside, target_is_directory=True)
    r = _storage("to-notion", folder / "link" / ".ai" / "demo" / "x.md", "--initiative", "demo", cwd=tmp_path, env=_clean_env())
    assert r.returncode == 1 and "symlink" in r.stderr and "s3cr3t" not in r.stdout


def test_publish_allowlist_refuses_files_that_are_not_records(tmp_path):
    for rel, text in {
        "notes.md": "fine\n",
        "runs/demo-run1/scratch.md": "fine\n",
        "runs/demo-run1/report.json": "{}\n",
        "unverified-imports.jsonl": json.dumps({"record_key": "x"}) + "\n",
        "design-gap-2026-10-09.md": "fine\n",
    }.items():
        src = _record(tmp_path, rel, text)
        r = _storage("to-notion", src, "--initiative", "demo", cwd=tmp_path, env=_clean_env())
        assert r.returncode == 1 and r.stdout == "" and f"{rel} is not a harness record file" in r.stderr, rel
        src.unlink()


def test_publish_allowlist_checks_the_shape_of_each_record_kind(tmp_path):
    council = SNAPSHOT.replace("stage: D.design", "stage: council.adr-p3")
    bad = {
        "runs/demo-run1/D.design.snapshot.md": ("# no frontmatter\n", "no YAML frontmatter"),
        "runs/demo-run1/E.review.snapshot.md": (SNAPSHOT, "stage is 'D.design', its path says 'E.review'"),
        "runs/demo-run2/D.design.snapshot.md": (SNAPSHOT, "run_id is 'demo-run1', its path says 'demo-run2'"),
        "runs/demo-run1/council.adr-p3.memo.md": (SNAPSHOT, "stage is 'D.design', its path says 'council.adr-p3'"),
        "runs/demo-run1/council.other.adversary.md": (council, "its path says 'council.other'"),
        "runs/demo-run1/index.md": ("| no rule row |\n", "no index table"),
        "ledger.jsonl": (json.dumps({**LEDGER_FIRST, "outcome": "made-up"}) + "\n", "line 1 (e001) fails the ledger schema"),
        "document-graph.yml": ("- a list\n", "not a YAML mapping"),
    }
    for rel, (text, why) in bad.items():
        src = _record(tmp_path, rel, text)
        r = _storage("to-notion", src, "--initiative", "demo", cwd=tmp_path, env=_clean_env())
        assert r.returncode == 1 and r.stdout == "" and why in r.stderr and rel.split("/")[-1] in r.stderr, (rel, r.stderr)
        src.unlink()
    other = _record(tmp_path, "runs/demo-run1/D.design.snapshot.md", SNAPSHOT.replace("initiative: demo", "initiative: elsewhere"))
    r = _storage("to-notion", other, "--initiative", "demo", cwd=tmp_path, env=_clean_env())
    assert r.returncode == 1 and "initiative is 'elsewhere'" in r.stderr
    other.unlink()
    good = {
        "runs/demo-run1/D.design.snapshot.md": SNAPSHOT,
        "runs/demo-run1/D.design.snapshot.2.md": SNAPSHOT,
        "runs/demo-run1/council.adr-p3.memo.md": council,
        "runs/demo-run1/council.adr-p3.adversary.md": council,
        "runs/demo-run1/index.md": INDEX,
        "ledger.jsonl": json.dumps(LEDGER_FIRST) + "\n",
        "harness-manifest.md": "# Manifest\n",
        "document-graph.yml": "documents: []\n",
        "domain/frontend.md": "# Frontend\n",
        "knowledge/ai-opportunities.md": "# AI opportunities\n",
    }
    for rel, text in good.items():
        _record(tmp_path, rel, text)
    _record(tmp_path, "runs/demo-run1/scratch.md", "fine\n")
    r = _storage("to-notion", tmp_path / ".ai" / "demo", "--initiative", "demo", cwd=tmp_path, env=_clean_env())
    assert r.returncode == 0, r.stderr
    assert sorted(p["record_key"] for p in json.loads(r.stdout)) == sorted(good)
    assert "skipped runs/demo-run1/scratch.md: not a harness record file" in r.stderr


def test_ledger_import_refuses_a_blockquoted_event_with_an_escaped_key(tmp_path):
    _, _, page = _page(tmp_path, "ledger.jsonl", json.dumps(LEDGER_FIRST) + "\n", name="bq.md")
    hidden = json.dumps({**LEDGER_FIRST, "event_id": "e009"}).replace('"event_id"', '"event\\u005fid"')
    text = page.read_text()
    for name, quoted in {
        "line": f"> {hidden}\n",
        "nested": f"> > {hidden}\n",
        "fenced": f"> ```text\n> {hidden}\n> ```\n",
        "html-escaped": "&gt; " + hidden.replace('"', "&quot;") + "\n",
    }.items():
        evil = tmp_path / f"bq-{name}.md"
        evil.write_text(text.replace("</page>", quoted + "</page>"))
        n = evil.read_text().splitlines().index(quoted.splitlines()[0]) + 1
        r = _storage("from-notion", evil, "--stdout", cwd=tmp_path, env=_clean_env())
        assert r.returncode == 1 and r.stdout == "" and f"line {n}" in r.stderr, (name, r.stderr)
        r = _storage("from-notion", evil, "--initiative", "demo", "--root", tmp_path / "dest", cwd=tmp_path, env=_clean_env())
        assert r.returncode == 1 and not (tmp_path / "dest" / ".ai" / "demo" / "ledger.jsonl").exists(), name


def _local_ledger_with_an_unexported_event(tmp_path):
    """Local ledger e001, e002, e003 where e003 was appended after the export that the page holds."""
    second = json.dumps({**LEDGER_FIRST, "event_id": "e002"})
    _, _, page = _page(tmp_path, "ledger.jsonl", json.dumps(LEDGER_FIRST) + "\n" + second + "\n", name="exported.md")
    root = tmp_path / "dest"
    ledger = root / ".ai" / "demo" / "ledger.jsonl"
    ledger.parent.mkdir(parents=True)
    third = json.dumps({**LEDGER_FIRST, "event_id": "e003"})
    ledger.write_text(json.dumps(LEDGER_FIRST) + "\n" + second + "\n" + third + "\n")
    return page, root, ledger, third


def test_replace_import_never_writes_the_ledger_through_an_aliased_key(tmp_path):
    page, root, ledger, third = _local_ledger_with_an_unexported_event(tmp_path)
    before = ledger.read_text()
    (root / ".ai" / "demo" / "runs").mkdir()
    (root / ".ai" / "demo" / "runs" / "alias").symlink_to("..", target_is_directory=True)
    shorter = (json.dumps(LEDGER_FIRST) + "\n").encode()
    for key in ("runs/alias/ledger.jsonl", "runs/alias/runs/alias/ledger.jsonl"):
        evil = tmp_path / "alias.md"
        evil.write_text(storage.record_body(key, shorter))
        r = _storage("from-notion", evil, "--initiative", "demo", "--root", root, "--replace", cwd=tmp_path, env=_clean_env())
        assert r.returncode == 1 and "symlink" in r.stderr and ledger.read_text() == before and third in before, (key, r.stderr)


def test_replace_import_never_writes_the_ledger_through_a_case_alias(tmp_path):
    page, root, ledger, third = _local_ledger_with_an_unexported_event(tmp_path)
    if not (ledger.parent / "LEDGER.JSONL").exists():
        pytest.skip("case-sensitive file system: LEDGER.JSONL is a different file here")
    before = ledger.read_text()
    evil = tmp_path / "alias-case.md"
    evil.write_text(storage.record_body("LEDGER.JSONL", (json.dumps(LEDGER_FIRST) + "\n").encode()))
    r = _storage("from-notion", evil, "--initiative", "demo", "--root", root, "--replace", cwd=tmp_path, env=_clean_env())
    assert r.returncode == 1 and "ledger.jsonl" in r.stderr and ledger.read_text() == before, r.stderr


def test_replace_import_keeps_an_event_appended_locally_while_it_runs(tmp_path, monkeypatch, capsys):
    page, root, ledger, third = _local_ledger_with_an_unexported_event(tmp_path)
    ledger.write_text(ledger.read_text().replace(third + "\n", ""))
    grown = tmp_path / "grown.md"
    fourth = json.dumps({**LEDGER_FIRST, "event_id": "e004"})
    grown.write_text(page.read_text().replace("</page>", storage.ledger_append_block(fourth) + "</page>"))
    real_makedirs = os.makedirs

    def local_append_lands_mid_import(*args, **kwargs):
        with open(ledger, "a") as f:
            f.write(third + "\n")
        monkeypatch.setattr(storage.os, "makedirs", real_makedirs)
        return real_makedirs(*args, **kwargs)

    monkeypatch.setattr(storage.os, "makedirs", local_append_lands_mid_import)
    storage.from_notion(str(grown), str(root), "demo", False, replace=True)
    assert third in ledger.read_text().splitlines()


def test_replace_import_appends_new_remote_events_to_the_local_ledger(tmp_path):
    page, root, ledger, third = _local_ledger_with_an_unexported_event(tmp_path)
    ledger.write_text(ledger.read_text().replace(third + "\n", ""))
    before = ledger.read_text()
    grown = tmp_path / "grown.md"
    grown.write_text(page.read_text().replace("</page>", storage.ledger_append_block(third) + "</page>"))
    r = _storage("from-notion", grown, "--initiative", "demo", "--root", root, "--replace", cwd=tmp_path, env=_clean_env())
    assert r.returncode == 0 and ledger.read_text() == before + third + "\n", r.stderr
    r = _storage("from-notion", page, "--initiative", "demo", "--root", root, "--replace", cwd=tmp_path, env=_clean_env())
    assert r.returncode == 1 and "append-only" in r.stderr and ledger.read_text() == before + third + "\n"


def test_import_never_writes_the_ledger_through_a_hard_link_or_another_name(tmp_path):
    page, root, ledger, third = _local_ledger_with_an_unexported_event(tmp_path)
    before = ledger.read_text()
    os.link(ledger, ledger.parent / "copy.md")
    evil = tmp_path / "hard.md"
    evil.write_text(storage.record_body("copy.md", (json.dumps(LEDGER_FIRST) + "\n").encode()))
    r = _storage("from-notion", evil, "--initiative", "demo", "--root", root, "--replace", cwd=tmp_path, env=_clean_env())
    assert r.returncode == 1 and "hard link" in r.stderr and ledger.read_text() == before


def test_ledger_import_refuses_an_encoded_event_outside_the_blocks(tmp_path):
    _, _, page = _page(tmp_path, "ledger.jsonl", json.dumps(LEDGER_FIRST) + "\n", name="enc.md")
    event = json.dumps({**LEDGER_FIRST, "event_id": "e009"})
    for name, line in {
        "base64": base64.b64encode(event.encode()).decode(),
        "quoted-base64": "> " + base64.b64encode(event.encode()).decode(),
        "yaml-binary": "note: !!binary " + base64.b64encode(event.encode()).decode(),
    }.items():
        evil = tmp_path / f"enc-{name}.md"
        evil.write_text(page.read_text().replace("</page>", line + "\n</page>"))
        for extra in ([], ["--unverified"]):
            r = _storage("from-notion", evil, "--stdout", *extra, cwd=tmp_path, env=_clean_env())
            assert r.returncode == 1 and r.stdout == "" and "outside a code block" in r.stderr, (name, extra, r.stderr)


def test_publish_allowlist_accepts_the_names_the_skills_write_and_checks_shape_in_folder_exports(tmp_path):
    intake = SNAPSHOT.replace("stage: D.design", "stage: A.intake")
    council = SNAPSHOT.replace("stage: D.design", "stage: council.adr-p3")
    for rel, text in {"runs/demo-run1/intake.snapshot.md": intake, "runs/demo-run1/council.adr-p3.r2.memo.md": council,
                      "runs/demo-run1/council.adr-p3.r2.adversary.md": council}.items():
        src = _record(tmp_path, rel, text)
        r = _storage("to-notion", src, "--initiative", "demo", cwd=tmp_path, env=_clean_env())
        assert r.returncode == 0 and json.loads(r.stdout)[0]["record_key"] == rel, (rel, r.stderr)
    _record(tmp_path, "runs/demo-run1/D.design.2.snapshot.md", SNAPSHOT)
    r = _storage("to-notion", tmp_path / ".ai" / "demo", "--initiative", "demo", cwd=tmp_path, env=_clean_env())
    assert r.returncode == 1 and r.stdout == "" and "D.design.2.snapshot.md frontmatter stage" in r.stderr
