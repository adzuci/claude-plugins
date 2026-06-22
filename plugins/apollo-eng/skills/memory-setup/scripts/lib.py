"""
lib.py — Pure, I/O-free helper functions for the memory-setup skill.

All functions are deterministic and side-effect-free; they are unit-tested
directly. Scripts import these helpers and add the thin argparse + I/O layer.
"""
from __future__ import annotations

import copy
import re


# ---------------------------------------------------------------------------
# SessionEnd hook helpers
# ---------------------------------------------------------------------------

def is_hook_present(settings: dict, hook_cmd: str) -> bool:
    """Return True if any SessionEnd hook entry contains a hooks[].command
    that exactly equals hook_cmd."""
    session_end = settings.get("hooks", {}).get("SessionEnd", [])
    for entry in session_end:
        for h in entry.get("hooks", []):
            if h.get("command") == hook_cmd:
                return True
    return False


def merge_session_end_hook(settings: dict, hook_cmd: str) -> dict:
    """Return a NEW settings dict with the SessionEnd hook appended.

    Idempotent: if an existing entry already has a hooks[].command equal to
    hook_cmd the input is returned unchanged (deep-copied).  Existing
    SessionEnd entries (e.g. a claudebar matcher entry) and all other hook
    events are left undisturbed.  Creates the 'hooks'/'SessionEnd' keys if
    absent.

    Does NOT mutate the input dict.
    """
    result = copy.deepcopy(settings)
    if is_hook_present(result, hook_cmd):
        return result

    hooks = result.setdefault("hooks", {})
    session_end = hooks.setdefault("SessionEnd", [])
    session_end.append({"hooks": [{"type": "command", "command": hook_cmd}]})
    return result


# ---------------------------------------------------------------------------
# Obsidian community-plugins helpers
# ---------------------------------------------------------------------------

def merge_community_plugins(existing: list, new_ids: list) -> list:
    """Return an ordered set-union of plugin IDs.

    Preserves the order of *existing* then appends any ids from *new_ids* that
    are not already present.  Deduplicates within existing as well.
    """
    seen: set[str] = set()
    result: list[str] = []
    for pid in existing:
        if pid not in seen:
            seen.add(pid)
            result.append(pid)
    for pid in new_ids:
        if pid not in seen:
            seen.add(pid)
            result.append(pid)
    return result


# ---------------------------------------------------------------------------
# Template rendering
# ---------------------------------------------------------------------------

def render_template(text: str, mapping: dict) -> str:
    """Replace {{KEY}} tokens in *text* using *mapping*.

    Raises ValueError if any {{...}} token remains unfilled after substitution.
    """
    for key, value in mapping.items():
        text = text.replace("{{" + key + "}}", str(value))
    remaining = re.findall(r"\{\{[^}]+\}\}", text)
    if remaining:
        raise ValueError(
            f"Unfilled template tokens: {remaining}"
        )
    return text


# ---------------------------------------------------------------------------
# CLAUDE.md upsert
# ---------------------------------------------------------------------------

def upsert_claude_md(
    content: str, block: str, begin_marker: str, end_marker: str
) -> str:
    """Insert or replace a managed block in *content*.

    If both *begin_marker* and *end_marker* are present in *content*, replace
    everything between (and including) them with *block*.  Otherwise append
    *block* preceded by a blank line.

    *block* is expected to already contain the markers.  Idempotent when the
    block is unchanged.
    """
    if begin_marker in content and end_marker in content:
        pattern = re.escape(begin_marker) + r".*?" + re.escape(end_marker)
        return re.sub(pattern, block, content, flags=re.DOTALL)
    else:
        if not content:
            separator = ""
        elif content.endswith("\n\n"):
            separator = ""
        elif content.endswith("\n"):
            separator = "\n"
        else:
            separator = "\n\n"
        return content + separator + block


# ---------------------------------------------------------------------------
# GitHub release asset helpers
# ---------------------------------------------------------------------------

def resolve_release_asset(release_json: dict, names: list) -> dict:
    """Return {name: browser_download_url} for each requested name found in
    a GitHub Releases API payload.

    Raises KeyError if manifest.json or main.js is missing from the assets.
    styles.css is optional and omitted from the result if absent.
    """
    REQUIRED = {"manifest.json", "main.js"}
    OPTIONAL = {"styles.css"}

    asset_map: dict[str, str] = {}
    for asset in release_json.get("assets", []):
        n = asset.get("name")
        url = asset.get("browser_download_url")
        if n and url:
            asset_map[n] = url

    result: dict[str, str] = {}
    for name in names:
        if name in REQUIRED:
            if name not in asset_map:
                raise KeyError(
                    f"Required asset '{name}' not found in release. "
                    "Check that the release is valid."
                )
            result[name] = asset_map[name]
        elif name in OPTIONAL:
            if name in asset_map:
                result[name] = asset_map[name]
        else:
            # Non-standard name: include if found, skip if not
            if name in asset_map:
                result[name] = asset_map[name]

    return result


# ---------------------------------------------------------------------------
# Plugin directory validation
# ---------------------------------------------------------------------------

def validate_plugin_dir(files: dict) -> list:
    """Return a sorted list of REQUIRED files missing from *files*.

    Required files: manifest.json, main.js.
    *files* is a mapping of {filename: bytes_or_str}.
    """
    REQUIRED = {"manifest.json", "main.js"}
    missing = sorted(REQUIRED - set(files.keys()))
    return missing


# ---------------------------------------------------------------------------
# claude-mem hook stripping
# ---------------------------------------------------------------------------

def strip_claude_mem_hooks(settings: dict) -> tuple:
    """Return (new_settings, removed) stripping claude-mem hook entries.

    *new_settings* has any hook entry whose command contains "claude-mem"
    removed from every hook-event array.  *removed* is the list of removed
    command strings.

    Does NOT mutate *settings*.
    """
    result = copy.deepcopy(settings)
    removed: list[str] = []

    hooks = result.get("hooks", {})
    for event_key in list(hooks.keys()):
        entries = hooks[event_key]
        new_entries = []
        for entry in entries:
            inner_hooks = entry.get("hooks", [])
            clean_inner = []
            for h in inner_hooks:
                cmd = h.get("command", "")
                if "claude-mem" in cmd:
                    removed.append(cmd)
                else:
                    clean_inner.append(h)
            if clean_inner:
                new_entry = dict(entry)
                new_entry["hooks"] = clean_inner
                new_entries.append(new_entry)
            elif not inner_hooks:
                # Entry had no hooks sub-key — keep it
                new_entries.append(entry)
            # If all inner hooks were removed, drop the entire entry
        hooks[event_key] = new_entries

    return result, removed


# ---------------------------------------------------------------------------
# Memory tooling classification
# ---------------------------------------------------------------------------

# Names that are known safe (not unexpected memory tooling).
_KNOWN_SAFE: frozenset[str] = frozenset(
    {
        "session-end.sh",
        "claudebar",
        "claude-mem",
        "thedotmack",
        # common infra/sre plugin names that contain innocent substrings
        "mem-exporter",
        "prometheus-mem",
    }
)

# Substrings that suggest memory tooling.
_MEMORY_SUBSTRINGS: tuple[str, ...] = ("mem", "memory", "recall", "knowledge")


def classify_memory_tooling(
    settings: dict, plugin_dirs: list, mcp_names: list
) -> dict:
    """Classify installed memory tooling.

    Returns::

        {
            "claude_mem": bool,   # True if claude-mem / thedotmack is in use
            "unknown": [...]      # memory-suggestive names that are NOT known-safe
        }

    **claude_mem** is True when ANY of:
    - A settings hook command contains "claude-mem"
    - A plugin_dir name contains "claude-mem" or "thedotmack"
    - An mcp_name contains "claude-mem" or "thedotmack"

    **unknown** lists names from *plugin_dirs* and *mcp_names* that:
    - Contain at least one of the _MEMORY_SUBSTRINGS
    - Are NOT in the _KNOWN_SAFE set
    - Do NOT contain "claude-mem" or "thedotmack" (those are in claude_mem)

    The heuristic is intentionally conservative: it flags names that *might*
    be unexpected memory tooling so the operator can review, while keeping
    false positives low by only matching on common memory-related substrings.
    """
    _CLAUDE_MEM_SIGNALS = ("claude-mem", "thedotmack")

    claude_mem = False

    # Check hook commands
    for entries in settings.get("hooks", {}).values():
        for entry in entries:
            for h in entry.get("hooks", []):
                cmd = h.get("command", "")
                if "claude-mem" in cmd:
                    claude_mem = True

    # Check plugin dirs and mcp names for claude-mem signals
    all_names = list(plugin_dirs) + list(mcp_names)
    for name in all_names:
        for signal in _CLAUDE_MEM_SIGNALS:
            if signal in name:
                claude_mem = True

    # Build unknown list
    unknown: list[str] = []
    for name in all_names:
        # Skip known-safe
        if name in _KNOWN_SAFE:
            continue
        # Skip if already captured as claude_mem
        if any(signal in name for signal in _CLAUDE_MEM_SIGNALS):
            continue
        # Flag if it contains a memory substring
        lower_name = name.lower()
        if any(sub in lower_name for sub in _MEMORY_SUBSTRINGS):
            unknown.append(name)

    return {"claude_mem": claude_mem, "unknown": unknown}
