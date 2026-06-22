"""
install_plugins.py — Download and install Obsidian community plugins into a vault.

Installs:
  claudian  → YishenTu/claudian
  obsidian-git → Vinzent03/obsidian-git

Usage:
    python install_plugins.py --vault VAULTPATH [--pin-claudian TAG]
        [--pin-git TAG] [--dry-run] [--force]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from lib import merge_community_plugins, resolve_release_asset, validate_plugin_dir

PLUGINS: dict[str, str] = {
    "claudian": "YishenTu/claudian",
    "obsidian-git": "Vinzent03/obsidian-git",
}

ASSET_NAMES = ["manifest.json", "main.js", "styles.css"]


def _github_api_url(repo: str, pin: str | None) -> str:
    if pin:
        return f"https://api.github.com/repos/{repo}/releases/tags/{pin}"
    return f"https://api.github.com/repos/{repo}/releases/latest"


def _auth_headers() -> dict:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _require_https(url: str) -> None:
    """Refuse any non-GitHub HTTPS URL before opening it.

    Guards against urllib honoring local schemes (e.g. file://) on a
    dynamically constructed URL — only github.com over HTTPS is expected.
    """
    parsed = urlparse(url)
    if parsed.scheme.lower() != "https":
        raise ValueError(f"refusing non-https URL: {url!r}")
    if parsed.hostname not in {"api.github.com", "github.com"}:
        raise ValueError(f"refusing non-GitHub URL: {url!r}")


def _fetch_json(url: str) -> dict:
    _require_https(url)
    req = urllib.request.Request(url, headers=_auth_headers())
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 (scheme checked)
        return json.loads(resp.read().decode())


def _download_bytes(url: str) -> bytes:
    _require_https(url)
    req = urllib.request.Request(url, headers=_auth_headers())
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 (scheme checked)
        return resp.read()


def _installed_plugin_complete(plugin_dir: Path, plugin_id: str) -> bool:
    files = {p.name: p.read_bytes() for p in plugin_dir.iterdir()} if plugin_dir.is_dir() else {}
    missing = validate_plugin_dir(files)
    if missing:
        return False
    try:
        manifest = json.loads(files["manifest.json"])
    except Exception:
        return False
    return manifest.get("id") == plugin_id


def install_plugin(
    plugin_id: str,
    repo: str,
    vault: Path,
    pin: str | None,
    dry_run: bool,
    force: bool,
) -> dict:
    plugin_dir = vault / ".obsidian" / "plugins" / plugin_id

    if _installed_plugin_complete(plugin_dir, plugin_id) and not force:
        return {
            "plugin": plugin_id,
            "status": "skipped",
            "reason": "already installed (use --force to reinstall)",
        }

    api_url = _github_api_url(repo, pin)

    if dry_run:
        return {
            "plugin": plugin_id,
            "status": "dry_run",
            "would_fetch_api": api_url,
            "would_download_assets": ASSET_NAMES,
        }

    # Fetch release metadata
    try:
        release = _fetch_json(api_url)
    except urllib.error.HTTPError as e:
        return {
            "plugin": plugin_id,
            "status": "error",
            "error": f"HTTP {e.code} fetching release from {api_url}. "
                     "See references/plugin-gui-fallback.md for manual install steps.",
        }
    except Exception as e:
        return {
            "plugin": plugin_id,
            "status": "error",
            "error": f"Failed to fetch release: {e}. "
                     "See references/plugin-gui-fallback.md for manual install steps.",
        }

    # Resolve asset URLs
    try:
        asset_urls = resolve_release_asset(release, ASSET_NAMES)
    except KeyError as e:
        return {
            "plugin": plugin_id,
            "status": "error",
            "error": f"Missing required asset: {e}. "
                     "See references/plugin-gui-fallback.md for manual install steps.",
        }

    # Download into a staging dir so a failed run cannot leave a manifest-only
    # plugin that future runs mistakenly treat as installed.
    staging_dir = plugin_dir.parent / f".{plugin_id}.tmp-install"
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True, exist_ok=True)
    downloaded: dict[str, bytes] = {}
    for asset_name, url in asset_urls.items():
        try:
            data = _download_bytes(url)
            (staging_dir / asset_name).write_bytes(data)
            downloaded[asset_name] = data
        except Exception as e:
            shutil.rmtree(staging_dir, ignore_errors=True)
            return {
                "plugin": plugin_id,
                "status": "error",
                "error": f"Failed to download {asset_name}: {e}. "
                         "See references/plugin-gui-fallback.md for manual install steps.",
            }

    # Validate plugin dir
    missing = validate_plugin_dir(downloaded)
    if missing:
        shutil.rmtree(staging_dir, ignore_errors=True)
        return {
            "plugin": plugin_id,
            "status": "error",
            "error": f"Plugin dir is incomplete — missing: {missing}. "
                     "See references/plugin-gui-fallback.md for manual install steps.",
        }

    # Verify manifest id
    try:
        manifest = json.loads(downloaded["manifest.json"])
        if manifest.get("id") != plugin_id:
            shutil.rmtree(staging_dir, ignore_errors=True)
            return {
                "plugin": plugin_id,
                "status": "error",
                "error": f"Manifest id '{manifest.get('id')}' does not match expected '{plugin_id}'. "
                         "See references/plugin-gui-fallback.md for manual install steps.",
            }
    except Exception as e:
        shutil.rmtree(staging_dir, ignore_errors=True)
        return {
            "plugin": plugin_id,
            "status": "error",
            "error": f"Failed to parse manifest.json: {e}. "
                     "See references/plugin-gui-fallback.md for manual install steps.",
        }

    plugin_dir.mkdir(parents=True, exist_ok=True)
    for asset_name in asset_urls:
        shutil.move(str(staging_dir / asset_name), str(plugin_dir / asset_name))
    shutil.rmtree(staging_dir, ignore_errors=True)

    return {
        "plugin": plugin_id,
        "status": "installed",
        "assets": list(asset_urls.keys()),
    }


def _read_community_plugins(cp_path: Path) -> list[str]:
    if not cp_path.exists():
        return []
    try:
        existing = json.loads(cp_path.read_text())
    except Exception as e:
        raise ValueError(f"Failed to parse {cp_path}: {e}") from e
    if not isinstance(existing, list) or not all(isinstance(pid, str) for pid in existing):
        raise ValueError(f"{cp_path} must contain a JSON array of plugin ids")
    return existing


def update_community_plugins(vault: Path, installed_ids: list) -> dict:
    """Merge installed plugin IDs into community-plugins.json."""
    cp_path = vault / ".obsidian" / "community-plugins.json"
    try:
        existing = _read_community_plugins(cp_path)
    except ValueError as e:
        return {"ok": False, "path": str(cp_path), "error": str(e)}

    merged = merge_community_plugins(existing, installed_ids)
    cp_path.parent.mkdir(parents=True, exist_ok=True)
    cp_path.write_text(json.dumps(merged, indent=2) + "\n")
    return {"ok": True, "path": str(cp_path), "plugins": merged}


def main() -> None:
    parser = argparse.ArgumentParser(description="Install Obsidian community plugins into a vault.")
    parser.add_argument("--vault", required=True, help="Path to the Obsidian vault.")
    parser.add_argument("--pin-claudian", default=None, help="Pin claudian to a specific release tag.")
    parser.add_argument("--pin-git", default=None, help="Pin obsidian-git to a specific release tag.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned actions without downloading.")
    parser.add_argument("--force", action="store_true", help="Reinstall even if already present.")
    args = parser.parse_args()

    vault = Path(args.vault).expanduser()
    pins = {
        "claudian": args.pin_claudian,
        "obsidian-git": args.pin_git,
    }

    results = []
    successfully_installed = []

    for plugin_id, repo in PLUGINS.items():
        result = install_plugin(
            plugin_id=plugin_id,
            repo=repo,
            vault=vault,
            pin=pins.get(plugin_id),
            dry_run=args.dry_run,
            force=args.force,
        )
        results.append(result)
        if result.get("status") == "installed":
            successfully_installed.append(plugin_id)

    community_plugins = None
    if successfully_installed and not args.dry_run:
        community_plugins = update_community_plugins(vault, successfully_installed)
        if not community_plugins["ok"]:
            results.append({
                "plugin": "community-plugins.json",
                "status": "error",
                "error": community_plugins["error"],
            })

    summary = {
        "dry_run": args.dry_run,
        "vault": str(vault),
        "plugins": results,
    }
    if community_plugins is not None:
        summary["community_plugins"] = community_plugins
    print(json.dumps(summary, indent=2))

    any_error = any(r.get("status") == "error" for r in results)
    if any_error:
        sys.exit(1)


if __name__ == "__main__":
    main()
