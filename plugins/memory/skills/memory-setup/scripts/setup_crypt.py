"""
setup_crypt.py — Enable git-crypt encryption for sensitive vault directories.

Default: dry-run (safe, read-only).  Pass --apply to make changes.

Usage:
    python setup_crypt.py --vault VAULTPATH [--apply]
        [--paths memory,sessions,...] [--key-out PATH] [--unlock KEYFILE]

Modes (auto-detected, reported as "mode" in the JSON output):
  fresh    — new vault, no git-crypt yet: init, write .gitattributes,
             export the key, commit.
  migrate  — existing vault with tracked plaintext: same as fresh, plus
             re-encrypt already-tracked files under the sensitive paths.
             Old commits keep plaintext (history_warning: true).
  unlock   — the checkout is git-crypt-locked (e.g. a fresh clone on a
             second machine): requires --unlock KEYFILE.
  noop     — git-crypt is already configured and unlocked; nothing to do.

Never touches the remote, never prints key material.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from lib import upsert_claude_md

DEFAULT_PATHS = ["memory", "sessions", "coaching", "meetings", "raw", "handoffs"]

GITCRYPT_MAGIC = b"\x00GITCRYPT"

_BEGIN_MARKER = "# BEGIN memory-setup git-crypt"
_END_MARKER = "# END memory-setup git-crypt"


def _run(cmd: list, cwd: Path) -> "tuple[bool, str, str]":
    """Run a command; return (success, stdout, stderr). Never raises."""
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, cwd=str(cwd)
        )
        return r.returncode == 0, r.stdout.strip(), r.stderr.strip()
    except Exception as e:  # FileNotFoundError etc.
        return False, "", str(e)


# ---------------------------------------------------------------------------
# Pure helpers (unit-tested directly)
# ---------------------------------------------------------------------------

def build_gitattributes_block(paths: list) -> str:
    """Return the managed .gitattributes block for *paths*."""
    lines = [_BEGIN_MARKER]
    for p in paths:
        p = p.strip().strip("/")
        if p:
            lines.append(f"{p}/** filter=git-crypt diff=git-crypt")
    lines.append(".gitattributes !filter !diff")
    lines.append(_END_MARKER)
    return "\n".join(lines) + "\n"


def merge_gitattributes(existing: str, paths: list) -> str:
    """Upsert the managed git-crypt block into existing .gitattributes text.

    Idempotent: replaces the block in place when the markers are present,
    otherwise appends it.  Surrounding content is preserved.
    """
    block = build_gitattributes_block(paths).rstrip("\n")
    merged = upsert_claude_md(existing, block, _BEGIN_MARKER, _END_MARKER)
    if not merged.endswith("\n"):
        merged += "\n"
    return merged


def is_locked_file(first_bytes: bytes) -> bool:
    """True if a working-tree file's leading bytes are git-crypt ciphertext."""
    return first_bytes.startswith(GITCRYPT_MAGIC)


# ---------------------------------------------------------------------------
# State detection
# ---------------------------------------------------------------------------

def _gitattributes_has_filter(vault: Path) -> bool:
    ga = vault / ".gitattributes"
    try:
        return "filter=git-crypt" in ga.read_text()
    except Exception:
        return False


def _local_key_present(vault: Path) -> bool:
    """True after `git-crypt init` or `git-crypt unlock` on this checkout."""
    if (vault / ".git" / "git-crypt").is_dir():
        return True
    ok, out, _ = _run(
        ["git", "config", "--local", "--get", "filter.git-crypt.smudge"], vault
    )
    return ok and bool(out)


def _tracked_files(vault: Path, prefix: str = "") -> list:
    args = ["git", "ls-files", "-z"]
    if prefix:
        args.append(prefix)
    ok, out, _ = _run(args, vault)
    if not ok or not out:
        return []
    return [f for f in out.split("\0") if f]


def _working_tree_locked(vault: Path, paths: list) -> bool:
    """True if any tracked file under *paths* is ciphertext on disk."""
    for p in paths:
        for rel in _tracked_files(vault, p.strip("/") + "/"):
            f = vault / rel
            try:
                with open(f, "rb") as fh:
                    if is_locked_file(fh.read(len(GITCRYPT_MAGIC))):
                        return True
            except Exception:
                continue
    return False


def _commit_count(vault: Path) -> int:
    ok, out, _ = _run(["git", "rev-list", "--count", "HEAD"], vault)
    try:
        return int(out) if ok else 0
    except ValueError:
        return 0


def detect_mode(vault: Path, paths: list) -> str:
    """Return one of: fresh, migrate, unlock, noop."""
    has_filter = _gitattributes_has_filter(vault)
    local_key = _local_key_present(vault)

    if has_filter and not local_key:
        return "unlock"
    if has_filter and local_key:
        if _working_tree_locked(vault, paths):
            return "unlock"
        return "noop"
    # No git-crypt filter yet.
    tracked_sensitive = any(
        _tracked_files(vault, p.strip("/") + "/") for p in paths
    )
    if _commit_count(vault) <= 1 and not tracked_sensitive:
        return "fresh"
    return "migrate"


# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------

def run(
    vault: Path,
    paths: list,
    key_out: Path,
    apply: bool,
    unlock_key: "Path | None" = None,
    which=shutil.which,
) -> dict:
    if which("git-crypt") is None:
        return {
            "ok": False,
            "error": "git-crypt binary not found. Install it first: "
                     "`brew install git-crypt` (macOS) or your package manager.",
        }
    if not (vault / ".git").exists():
        return {"ok": False, "error": f"Not a git repository: {vault}"}

    # Never allow the exported key inside the vault (it would get committed).
    try:
        key_inside = key_out.resolve().is_relative_to(vault.resolve())
    except AttributeError:  # Python 3.8 — not supported by CI, but be safe
        key_inside = str(key_out.resolve()).startswith(str(vault.resolve()) + "/")
    if key_inside:
        return {
            "ok": False,
            "error": f"--key-out must not be inside the vault: {key_out}",
        }

    mode = detect_mode(vault, paths)

    # The default key location is the vault's parent dir. If that dir is
    # itself inside a git work tree, the exported key could be committed by
    # that repo — warn so the caller surfaces it (the key must be deleted
    # after the password-manager handoff either way).
    key_location_warning = None
    key_dir = key_out.parent
    if mode in ("fresh", "migrate") and key_dir.is_dir():
        ok, top, _ = _run(["git", "rev-parse", "--show-toplevel"], key_dir)
        if ok and top:
            key_location_warning = (
                f"Key export location {key_dir} is inside a git repo at "
                f"'{top}' — make sure the key file is never committed there; "
                "delete it right after saving to your password manager."
            )

    result: dict = {
        "ok": True,
        "dry_run": not apply,
        "mode": mode,
        "vault": str(vault),
        "paths": paths,
        "key_out": str(key_out) if mode in ("fresh", "migrate") else None,
        "history_warning": mode == "migrate",
        "actions": [],
    }
    if key_location_warning:
        result["key_location_warning"] = key_location_warning

    if mode == "noop":
        result["note"] = "git-crypt already configured and unlocked; nothing to do."
        return result

    if mode == "unlock":
        result["key_out"] = None
        if unlock_key is None:
            result["ok"] = False
            result["error"] = (
                "This checkout is git-crypt-locked. Download the key from your "
                "password manager and re-run with --unlock <keyfile>."
            )
            return result
        if not unlock_key.is_file():
            result["ok"] = False
            result["error"] = f"Key file not found: {unlock_key}"
            return result
        result["actions"].append(f"git-crypt unlock {unlock_key}")
        if apply:
            ok, _, err = _run(["git-crypt", "unlock", str(unlock_key)], vault)
            if not ok:
                result["ok"] = False
                result["error"] = f"git-crypt unlock failed: {err}"
                return result
            result["note"] = (
                "Unlocked. Delete the downloaded key file now that this "
                "machine is set up."
            )
        return result

    # --- fresh / migrate ---
    plan = [
        "git-crypt init",
        f"write managed block to {vault / '.gitattributes'}",
        f"git-crypt export-key {key_out} (store in your password manager)",
    ]
    if mode == "migrate":
        plan.append("git-crypt status -f (re-encrypt tracked files under sensitive paths)")
    plan.append('git commit -m "chore: enable git-crypt for sensitive dirs"')
    result["actions"] = plan

    if not apply:
        result["note"] = "Dry run — no changes made. Re-run with --apply."
        return result

    if not _local_key_present(vault):
        ok, _, err = _run(["git-crypt", "init"], vault)
        if not ok:
            result["ok"] = False
            result["error"] = f"git-crypt init failed: {err}"
            return result

    ga_path = vault / ".gitattributes"
    existing = ga_path.read_text() if ga_path.exists() else ""
    ga_path.write_text(merge_gitattributes(existing, paths))

    if not key_out.exists():
        key_out.parent.mkdir(parents=True, exist_ok=True)
        ok, _, err = _run(["git-crypt", "export-key", str(key_out)], vault)
        if not ok:
            result["ok"] = False
            result["error"] = f"git-crypt export-key failed: {err}"
            return result
        key_out.chmod(0o600)

    if mode == "migrate":
        # Re-encrypts and stages tracked files that should now be encrypted.
        ok, _, err = _run(["git-crypt", "status", "-f"], vault)
        if not ok:
            result["ok"] = False
            result["error"] = f"git-crypt status -f failed: {err}"
            return result

    _run(["git", "add", "-A"], vault)
    ok, _, err = _run(
        ["git", "commit", "-m", "chore: enable git-crypt for sensitive dirs"],
        vault,
    )
    result["commit"] = ok
    if not ok:
        result["commit_error"] = err

    result["note"] = (
        "Key exported. Store it in 1Password (or your password manager) as a "
        "document, then DELETE the local copy. Never commit it."
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Enable git-crypt encryption for sensitive vault directories."
    )
    parser.add_argument("--vault", required=True, help="Path to the vault git repo.")
    parser.add_argument("--paths", default=",".join(DEFAULT_PATHS),
                        help="Comma-separated vault-relative dirs to encrypt.")
    parser.add_argument("--key-out", default=None,
                        help="Where to export the key (default: <vault-parent>/<vault-name>.gitcrypt.key).")
    parser.add_argument("--unlock", default=None, metavar="KEYFILE",
                        help="Unlock a locked checkout with this exported key.")
    parser.add_argument("--apply", action="store_true",
                        help="Actually apply changes (default is dry-run).")
    args = parser.parse_args()

    vault = Path(args.vault).expanduser().resolve()
    paths = [p.strip() for p in args.paths.split(",") if p.strip()]
    key_out = (
        Path(args.key_out).expanduser()
        if args.key_out
        else vault.parent / f"{vault.name}.gitcrypt.key"
    )
    unlock_key = Path(args.unlock).expanduser() if args.unlock else None

    result = run(vault=vault, paths=paths, key_out=key_out,
                 apply=args.apply, unlock_key=unlock_key)
    print(json.dumps(result, indent=2))
    if not result.get("ok"):
        sys.exit(1)


if __name__ == "__main__":
    main()
