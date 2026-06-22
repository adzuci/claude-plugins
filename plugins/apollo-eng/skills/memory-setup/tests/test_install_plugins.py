"""
test_install_plugins.py — Unit tests for resolve_release_asset using realistic
GitHub release JSON fixtures.

No network calls are made in any test.
"""
from __future__ import annotations

import pytest

from .conftest import load_script_module

lib = load_script_module("lib")
install_plugins = load_script_module("install_plugins")

# ---------------------------------------------------------------------------
# Realistic GitHub release payload fixture
# ---------------------------------------------------------------------------

REALISTIC_RELEASE = {
    "tag_name": "v2.31.1",
    "name": "2.31.1",
    "published_at": "2024-11-01T12:00:00Z",
    "assets": [
        {
            "name": "manifest.json",
            "content_type": "application/json",
            "size": 512,
            "browser_download_url": "https://github.com/Vinzent03/obsidian-git/releases/download/v2.31.1/manifest.json",
        },
        {
            "name": "main.js",
            "content_type": "application/javascript",
            "size": 204800,
            "browser_download_url": "https://github.com/Vinzent03/obsidian-git/releases/download/v2.31.1/main.js",
        },
        {
            "name": "styles.css",
            "content_type": "text/css",
            "size": 4096,
            "browser_download_url": "https://github.com/Vinzent03/obsidian-git/releases/download/v2.31.1/styles.css",
        },
        {
            "name": "obsidian-git-v2.31.1.zip",
            "content_type": "application/zip",
            "size": 209920,
            "browser_download_url": "https://github.com/Vinzent03/obsidian-git/releases/download/v2.31.1/obsidian-git-v2.31.1.zip",
        },
        {
            "name": "checksums.txt",
            "content_type": "text/plain",
            "size": 256,
            "browser_download_url": "https://github.com/Vinzent03/obsidian-git/releases/download/v2.31.1/checksums.txt",
        },
    ],
}

RELEASE_WITHOUT_MAIN_JS = {
    "tag_name": "v1.0.0",
    "assets": [
        {
            "name": "manifest.json",
            "browser_download_url": "https://example.com/manifest.json",
        },
        {
            "name": "styles.css",
            "browser_download_url": "https://example.com/styles.css",
        },
        {
            "name": "plugin-v1.0.0.zip",
            "browser_download_url": "https://example.com/plugin.zip",
        },
    ],
}

RELEASE_WITHOUT_MANIFEST = {
    "tag_name": "v1.0.0",
    "assets": [
        {
            "name": "main.js",
            "browser_download_url": "https://example.com/main.js",
        },
    ],
}

REQUESTED_ASSETS = ["manifest.json", "main.js", "styles.css"]


class TestResolveReleaseAssetRealistic:
    def test_all_assets_resolved(self) -> None:
        result = lib.resolve_release_asset(REALISTIC_RELEASE, REQUESTED_ASSETS)
        assert "manifest.json" in result
        assert "main.js" in result
        assert "styles.css" in result

    def test_manifest_url_correct(self) -> None:
        result = lib.resolve_release_asset(REALISTIC_RELEASE, REQUESTED_ASSETS)
        assert "manifest.json" in result["manifest.json"]
        assert "v2.31.1" in result["manifest.json"]

    def test_main_js_url_correct(self) -> None:
        result = lib.resolve_release_asset(REALISTIC_RELEASE, REQUESTED_ASSETS)
        assert "main.js" in result["main.js"]

    def test_styles_css_url_correct(self) -> None:
        result = lib.resolve_release_asset(REALISTIC_RELEASE, REQUESTED_ASSETS)
        assert "styles.css" in result["styles.css"]

    def test_zip_not_in_result(self) -> None:
        result = lib.resolve_release_asset(REALISTIC_RELEASE, REQUESTED_ASSETS)
        assert "obsidian-git-v2.31.1.zip" not in result

    def test_checksums_not_in_result(self) -> None:
        result = lib.resolve_release_asset(REALISTIC_RELEASE, REQUESTED_ASSETS)
        assert "checksums.txt" not in result

    def test_only_requested_assets_returned(self) -> None:
        result = lib.resolve_release_asset(REALISTIC_RELEASE, REQUESTED_ASSETS)
        assert set(result.keys()) == {"manifest.json", "main.js", "styles.css"}


class TestResolveReleaseAssetMissingMain:
    def test_raises_key_error(self) -> None:
        with pytest.raises(KeyError):
            lib.resolve_release_asset(RELEASE_WITHOUT_MAIN_JS, REQUESTED_ASSETS)

    def test_error_message_mentions_main_js(self) -> None:
        with pytest.raises(KeyError, match="main.js"):
            lib.resolve_release_asset(RELEASE_WITHOUT_MAIN_JS, REQUESTED_ASSETS)


class TestResolveReleaseAssetMissingManifest:
    def test_raises_key_error(self) -> None:
        with pytest.raises(KeyError):
            lib.resolve_release_asset(RELEASE_WITHOUT_MANIFEST, REQUESTED_ASSETS)

    def test_error_message_mentions_manifest(self) -> None:
        with pytest.raises(KeyError, match="manifest.json"):
            lib.resolve_release_asset(RELEASE_WITHOUT_MANIFEST, REQUESTED_ASSETS)


class TestResolveReleaseAssetStylesOptional:
    def test_styles_omitted_when_absent(self) -> None:
        release = {
            "assets": [
                {
                    "name": "manifest.json",
                    "browser_download_url": "https://example.com/manifest.json",
                },
                {
                    "name": "main.js",
                    "browser_download_url": "https://example.com/main.js",
                },
            ]
        }
        result = lib.resolve_release_asset(release, REQUESTED_ASSETS)
        assert "styles.css" not in result
        assert "manifest.json" in result
        assert "main.js" in result

    def test_result_has_exactly_two_keys_when_no_styles(self) -> None:
        release = {
            "assets": [
                {
                    "name": "manifest.json",
                    "browser_download_url": "https://example.com/manifest.json",
                },
                {
                    "name": "main.js",
                    "browser_download_url": "https://example.com/main.js",
                },
            ]
        }
        result = lib.resolve_release_asset(release, REQUESTED_ASSETS)
        assert set(result.keys()) == {"manifest.json", "main.js"}


class TestInstallPluginSafety:
    def test_require_https_rejects_non_github_hosts(self) -> None:
        with pytest.raises(ValueError, match="non-GitHub"):
            install_plugins._require_https("https://example.com/main.js")

    def test_require_https_allows_github_release_assets(self) -> None:
        install_plugins._require_https(
            "https://github.com/Vinzent03/obsidian-git/releases/download/v1/main.js"
        )

    def test_manifest_only_plugin_is_repaired(self, tmp_path, monkeypatch) -> None:
        vault = tmp_path / "vault"
        plugin_dir = vault / ".obsidian" / "plugins" / "demo"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "manifest.json").write_text('{"id":"demo"}')

        release = {
            "assets": [
                {"name": "manifest.json", "browser_download_url": "https://example.com/manifest.json"},
                {"name": "main.js", "browser_download_url": "https://example.com/main.js"},
            ]
        }
        monkeypatch.setattr(install_plugins, "_fetch_json", lambda url: release)
        monkeypatch.setattr(
            install_plugins,
            "_download_bytes",
            lambda url: b'{"id":"demo"}' if url.endswith("manifest.json") else b"main",
        )

        result = install_plugins.install_plugin("demo", "owner/repo", vault, None, False, False)

        assert result["status"] == "installed"
        assert (plugin_dir / "main.js").read_bytes() == b"main"

    def test_failed_download_does_not_leave_staging_dir(self, tmp_path, monkeypatch) -> None:
        vault = tmp_path / "vault"
        release = {
            "assets": [
                {"name": "manifest.json", "browser_download_url": "https://example.com/manifest.json"},
                {"name": "main.js", "browser_download_url": "https://example.com/main.js"},
            ]
        }
        monkeypatch.setattr(install_plugins, "_fetch_json", lambda url: release)

        def fail_main(url: str) -> bytes:
            if url.endswith("main.js"):
                raise RuntimeError("boom")
            return b'{"id":"demo"}'

        monkeypatch.setattr(install_plugins, "_download_bytes", fail_main)

        result = install_plugins.install_plugin("demo", "owner/repo", vault, None, False, False)

        assert result["status"] == "error"
        assert not (vault / ".obsidian" / "plugins" / ".demo.tmp-install").exists()

    def test_reinstall_preserves_plugin_data_json(self, tmp_path, monkeypatch) -> None:
        vault = tmp_path / "vault"
        plugin_dir = vault / ".obsidian" / "plugins" / "demo"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "manifest.json").write_text('{"id":"demo"}')
        (plugin_dir / "main.js").write_text("old")
        (plugin_dir / "data.json").write_text('{"setting":true}')
        release = {
            "assets": [
                {"name": "manifest.json", "browser_download_url": "https://example.com/manifest.json"},
                {"name": "main.js", "browser_download_url": "https://example.com/main.js"},
            ]
        }
        monkeypatch.setattr(install_plugins, "_fetch_json", lambda url: release)
        monkeypatch.setattr(
            install_plugins,
            "_download_bytes",
            lambda url: b'{"id":"demo"}' if url.endswith("manifest.json") else b"new",
        )

        result = install_plugins.install_plugin("demo", "owner/repo", vault, None, False, True)

        assert result["status"] == "installed"
        assert (plugin_dir / "main.js").read_text() == "new"
        assert (plugin_dir / "data.json").read_text() == '{"setting":true}'

    def test_update_community_plugins_rejects_malformed_json(self, tmp_path) -> None:
        vault = tmp_path / "vault"
        cp_path = vault / ".obsidian" / "community-plugins.json"
        cp_path.parent.mkdir(parents=True)
        cp_path.write_text("{bad")

        result = install_plugins.update_community_plugins(vault, ["claudian"])

        assert result["ok"] is False
        assert "Failed to parse" in result["error"]
        assert cp_path.read_text() == "{bad"

    def test_update_community_plugins_rejects_non_list_json(self, tmp_path) -> None:
        vault = tmp_path / "vault"
        cp_path = vault / ".obsidian" / "community-plugins.json"
        cp_path.parent.mkdir(parents=True)
        cp_path.write_text('{"plugins":["old"]}')

        result = install_plugins.update_community_plugins(vault, ["claudian"])

        assert result["ok"] is False
        assert "JSON array" in result["error"]
        assert cp_path.read_text() == '{"plugins":["old"]}'
