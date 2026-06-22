"""
Shared helpers for memory-setup session importers.
"""
from __future__ import annotations

import re
from pathlib import Path

SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?[^'\"\s`]+"),
    re.compile(r"sk-[A-Za-z0-9_-]{12,}"),
)


def _redact_match(match: re.Match[str]) -> str:
    key = match.group(1) if match.lastindex else None
    return f"{key}=[REDACTED]" if key else "[REDACTED]"


def redact(text: str) -> str:
    for pattern in SECRET_PATTERNS:
        text = pattern.sub(_redact_match, text)
    return text


def ensure_daily_file(vault: Path, date: str) -> Path:
    sessions_dir = vault / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    path = sessions_dir / f"{date}.md"
    if not path.exists():
        path.write_text(f"---\ndate: {date}\n---\n\n# Session: {date}\n\n")
    return path


def read_state(path: Path) -> set[str]:
    try:
        return {line.strip() for line in path.read_text().splitlines() if line.strip()}
    except FileNotFoundError:
        return set()


def write_state(path: Path, ids: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{sid}\n" for sid in sorted(ids)))
