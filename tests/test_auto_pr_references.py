"""Checks for the auto-pr skill's reference docs.

These guard the two things about `references/` that rot silently: intra-repo links
that point at files nobody moved yet, and the LeadGenie drift marker. Neither can
verify freshness against `apolloio/leadgenie` — that needs cross-repo read access
CI does not have — so this only enforces that the marker stays parseable and
internally consistent.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
REFERENCES = REPO / "plugins" / "apollo-eng" / "skills" / "auto-pr" / "references"
GOTCHAS = REFERENCES / "leadgenie-gotchas.md"

MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
VERIFIED_RE = re.compile(
    r"Last verified (?P<date>\d{4}-\d{2}-\d{2}) against LeadGenie `CLAUDE\.md` at\s+"
    r"\[`(?P<short_sha>[0-9a-f]{7,40})`\]\("
    r"https://github\.com/apolloio/leadgenie/blob/(?P<full_sha>[0-9a-f]{40})/CLAUDE\.md\)"
)


def _reference_docs() -> list[Path]:
    return sorted(REFERENCES.glob("*.md"))


def test_references_directory_is_populated() -> None:
    assert _reference_docs(), f"no reference docs found under {REFERENCES}"


@pytest.mark.parametrize("doc", _reference_docs(), ids=lambda p: p.name)
def test_relative_links_resolve(doc: Path) -> None:
    """Intra-repo links must point at files that exist in this checkout.

    A link to `https://github.com/apolloio/claude-plugins/blob/main/<path>` looks
    fine in review but 404s until the branch merges, so relative paths are the
    convention here and this test is what keeps them honest.
    """
    broken = []
    for target in MARKDOWN_LINK_RE.findall(doc.read_text()):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        path = (doc.parent / target.split("#", 1)[0]).resolve()
        if not path.exists():
            broken.append(target)

    assert not broken, f"{doc.name}: unresolvable relative link(s): {broken}"


def test_no_hardcoded_main_branch_links_to_this_repo() -> None:
    """`blob/main` self-links break on any branch where the target is new."""
    offenders = [
        doc.name
        for doc in _reference_docs()
        if "github.com/apolloio/claude-plugins/blob/main/" in doc.read_text()
    ]
    assert not offenders, (
        "use a relative path for intra-repo links instead of a blob/main URL: "
        f"{offenders}"
    )


def test_leadgenie_drift_marker_is_wellformed() -> None:
    match = VERIFIED_RE.search(GOTCHAS.read_text())
    assert match, (
        f"{GOTCHAS.name}: missing or malformed 'Last verified <date> against "
        "LeadGenie `CLAUDE.md` at [`<sha>`](<blob url>)' marker"
    )

    full_sha = match.group("full_sha")
    short_sha = match.group("short_sha")
    assert full_sha.startswith(short_sha), (
        f"{GOTCHAS.name}: link text SHA {short_sha!r} does not match the URL SHA "
        f"{full_sha!r} — update both when re-verifying"
    )

    verified_on = dt.date.fromisoformat(match.group("date"))
    assert verified_on <= dt.date.today(), (
        f"{GOTCHAS.name}: 'Last verified' date {verified_on} is in the future"
    )


def test_leadgenie_drift_check_command_matches_verified_sha() -> None:
    """The copy-paste drift command has to compare against the pinned SHA."""
    text = GOTCHAS.read_text()
    match = VERIFIED_RE.search(text)
    assert match, "drift marker must parse before its command can be checked"

    full_sha = match.group("full_sha")
    assert f"compare/{full_sha}...master" in text, (
        f"{GOTCHAS.name}: drift-check command must compare against the pinned SHA "
        f"{full_sha!r}; update the command and the marker together"
    )
