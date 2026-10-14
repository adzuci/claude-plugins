"""
Stdlib-only loader for the config.md format used by skill-generalizer.

config.md looks like:

    ---
    team_name: "Growth Conversion"
    jira_project_key: "CVR"
    preferred_assignees: ["alice", "bob"]
    ---
    # Setup Guide
    ...

This loader parses just the YAML frontmatter (between the leading `---`
and the next `---`) and returns it as a dict. It handles the small subset
of YAML actually used in config.md: strings, booleans, nulls, double-quoted
strings, and simple flow-style lists like ["a", "b"]. Numbers are left as
strings so identifiers keep their exact form.

It does NOT handle nested dicts, multi-line strings, anchors, or any of
the other YAML features. If your config grows beyond what this can parse,
swap in PyYAML.

Usage:
    from config_loader import load_config
    cfg = load_config()  # finds config.md alongside this script
    print(cfg["team_name"])
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def _coerce(raw: str) -> Any:
    s = raw.strip()
    if not s:
        return ""
    if s.lower() == "true":
        return True
    if s.lower() == "false":
        return False
    if s.lower() in ("null", "~"):
        return None
    if s.startswith("[") and s.endswith("]"):
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            inner = s[1:-1].strip()
            if not inner:
                return []
            return [_coerce(part) for part in inner.split(",")]
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    # Everything else stays a string on purpose. Config values are identifiers
    # (project keys, database IDs, channel names), and coercing "007" to 7 or
    # "1.10" to 1.1 silently corrupts them.
    return s


def _strip_inline_comment(raw: str) -> str:
    """Drop a trailing ` # comment`, ignoring `#` inside quotes.

    A value that *starts* with `#` is kept. Strict YAML would read it as a
    comment, but in this format a leading `#` is nearly always a channel name
    (`#growth-conversion-pd`), and silently blanking it is the worse failure.
    """
    out: list[str] = []
    quote = None
    # Strip first, so a value that starts with `#` is seen at position 0 rather
    # than after the space that `partition(":")` leaves behind.
    for ch in raw.strip():
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            out.append(ch)
        elif ch == "#" and out and out[-1].isspace():
            break
        else:
            out.append(ch)
    return "".join(out).strip()


def parse_frontmatter(text: str) -> dict[str, Any]:
    # The closing `---` may be the last line with no trailing newline.
    match = re.match(r"^---\s*\n(.*?)\n---[ \t]*(?:\n|$)", text, re.DOTALL)
    if not match:
        return {}
    body = match.group(1)
    out: dict[str, Any] = {}
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        out[key.strip()] = _coerce(_strip_inline_comment(value))
    return out


USER_CONFIG_ROOT = Path("~/.claude/plugin-config").expanduser()


def user_config_path(plugin: str, skill: str) -> Path:
    """Where this user's own answers live, outside the plugin install folder."""
    return USER_CONFIG_ROOT / plugin / f"{skill}.md"


def load_config(
    path: str | Path | None = None,
    plugin: str | None = None,
    skill: str | None = None,
) -> dict[str, Any]:
    """Load config, with the user's saved answers layered over shipped defaults.

    The `config.md` inside a skill folder is shipped content. For an installed
    plugin that folder is replaced on every update, so answers written there are
    lost and the user gets re-asked everything. Answers belong in a file the user
    owns; the shipped file supplies defaults and documentation.

    Pass `plugin` and `skill` to enable the layering. Passing `path` alone reads
    exactly that file, which is what the tests and one-off inspection want.
    """
    if path is None:
        here = Path(__file__).resolve().parent
        for candidate in (here / "config.md", here.parent / "config.md"):
            if candidate.exists():
                path = candidate
                break
        else:
            raise FileNotFoundError("No config.md found alongside this script or its parent.")

    shipped = parse_frontmatter(Path(path).read_text(encoding="utf-8"))
    if not (plugin and skill):
        return shipped

    saved_path = user_config_path(plugin, skill)
    if not saved_path.exists():
        return shipped
    saved = parse_frontmatter(saved_path.read_text(encoding="utf-8"))
    # A saved answer wins, including a deliberate empty string. Only skip keys
    # the user has not actually answered.
    merged = dict(shipped)
    merged.update({k: v for k, v in saved.items() if not is_unset(v)})
    return merged


def save_config(plugin: str, skill: str, values: dict[str, Any]) -> Path:
    """Write answers to the user-owned config file, creating parents as needed."""
    target = user_config_path(plugin, skill)
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = ["---"]
    for key, value in values.items():
        if isinstance(value, list):
            rendered = "[" + ", ".join(json.dumps(str(v)) for v in value) + "]"
        elif value is None:
            rendered = "null"
        elif isinstance(value, bool):
            rendered = "true" if value else "false"
        else:
            rendered = json.dumps(str(value))
        lines.append(f"{key}: {rendered}")
    lines += ["---", "", f"# Saved config for {plugin}:{skill}", "",
              "Written by the skill. Safe to edit by hand. This file is outside the plugin",
              "install folder, so a plugin update won't overwrite your answers.", ""]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target


def is_unset(value: Any) -> bool:
    """True only when a value still needs to be supplied.

    An empty string is a deliberate answer in this format, not a missing one:
    `team_context_dirs: ""` means "skip the local scan" and an empty
    `jira_secondary_project_key` means "we only have one project". Treating
    those as unset re-asks the same questions on every run.
    """
    return value is None or (isinstance(value, str) and value.strip() == "<UNSET>")


if __name__ == "__main__":
    import sys
    cfg = load_config(sys.argv[1] if len(sys.argv) > 1 else None)
    print(json.dumps(cfg, indent=2))
