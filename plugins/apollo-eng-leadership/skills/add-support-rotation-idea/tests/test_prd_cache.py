from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

prd_cache = pytest.importorskip("prd_cache")


def test_normalize_payload_extracts_prd_results() -> None:
    payload = {
        "results": [
            {
                "document": {
                    "title": "Sequences PRD",
                    "url": "https://notion.so/sequences-prd",
                },
                "snippets": [{"text": "TLDR: Improve manual email steps."}],
            },
            {
                "document": {
                    "title": "Random meeting notes",
                    "url": "https://notion.so/meeting",
                },
                "snippets": [{"text": "Weekly sync notes."}],
            },
        ]
    }

    items = prd_cache.normalize_payload(payload)

    assert items == [
        {
            "title": "Sequences PRD",
            "url": "https://notion.so/sequences-prd",
            "tldr": "TLDR: Improve manual email steps.",
        }
    ]


def test_cache_freshness_uses_seven_day_ttl() -> None:
    now = datetime(2026, 6, 26, tzinfo=timezone.utc)

    assert prd_cache.is_cache_fresh({"generated_at": "2026-06-19T00:00:00+00:00"}, now=now)
    assert not prd_cache.is_cache_fresh({"generated_at": "2026-06-18T00:00:00+00:00"}, now=now)


def test_search_requires_fresh_cache(tmp_path) -> None:
    cache_path = tmp_path / "prd-cache.json"
    cache_path.write_text(
        json.dumps(
            {
                "generated_at": "2026-06-01T00:00:00+00:00",
                "items": [{"title": "Sequences PRD", "url": "https://notion.so/sequences", "tldr": "Manual email steps"}],
            }
        ),
        encoding="utf-8",
    )

    assert prd_cache.main(["--cache", str(cache_path), "search", "--query", "manual email"]) == 2


def test_search_scores_title_matches_first() -> None:
    items = [
        {"title": "Generic PRD", "url": "https://example.com/a", "tldr": "Manual email steps"},
        {"title": "Manual Email PRD", "url": "https://example.com/b", "tldr": "Sequence builder"},
    ]

    matches = prd_cache.search_items(items, "manual email", limit=2)

    assert matches[0]["title"] == "Manual Email PRD"


def test_query_tokens_includes_two_char_terms() -> None:
    tokens = prd_cache.query_tokens("AI CX PRD roadmap")

    assert "ai" in tokens
    assert "cx" in tokens
    assert "prd" in tokens


def test_refresh_subcommand_calls_glean(tmp_path, monkeypatch) -> None:
    glean_output = json.dumps(
        {
            "results": [
                {
                    "document": {"title": "Sequences PRD", "url": "https://notion.so/seq"},
                    "snippets": [{"text": "PRD for sequences."}],
                }
            ]
        }
    )

    def fake_run(cmd, capture_output, text, timeout=None):
        class Result:
            returncode = 0
            stdout = glean_output
            stderr = ""

        return Result()

    monkeypatch.setattr(prd_cache.subprocess, "run", fake_run)
    cache_path = tmp_path / "prd-cache.json"

    exit_code = prd_cache.main(["--cache", str(cache_path), "refresh"])

    assert exit_code == 0
    assert cache_path.exists()
    data = json.loads(cache_path.read_text())
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "Sequences PRD"
