#!/usr/bin/env python3
"""Maintain a tiny local PRD title/TLDR cache for support-rotation idea lookup."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CACHE_TTL_DAYS = 7
GLEAN_QUERY = "PRD product requirements one pager roadmap"
GLEAN_PAGE_SIZE = 25
GLEAN_FIELDS = "results.document.title,results.document.url,results.snippets"
DEFAULT_CACHE_PATH = (
    Path.home()
    / ".cache"
    / "apollo-skills"
    / "add-support-rotation-idea"
    / "prd-title-cache.json"
)
PRD_MARKERS = ("prd", "product requirement", "product requirements", "one-pager", "one pager")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def cache_age_days(cache: dict[str, Any], now: datetime | None = None) -> int | None:
    generated_at = parse_timestamp(cache.get("generated_at"))
    if generated_at is None:
        return None
    now = now or utc_now()
    return max(0, (now - generated_at).days)


def is_cache_fresh(cache: dict[str, Any], now: datetime | None = None, ttl_days: int = CACHE_TTL_DAYS) -> bool:
    age = cache_age_days(cache, now=now)
    return age is not None and age <= ttl_days


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_cache(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    data = read_json(path)
    if not isinstance(data, dict):
        raise ValueError(f"Cache must be a JSON object: {path}")
    return data


def _first_text(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _snippet_text(snippets: Any) -> str:
    if isinstance(snippets, str):
        return snippets.strip()
    if isinstance(snippets, list):
        parts: list[str] = []
        for snippet in snippets:
            if isinstance(snippet, str):
                parts.append(snippet)
            elif isinstance(snippet, dict):
                parts.append(_first_text(snippet.get("text"), snippet.get("snippet"), snippet.get("content")))
        return " ".join(part.strip() for part in parts if part and part.strip())
    return ""


def _records_from_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("results", "documents", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def normalize_record(record: dict[str, Any]) -> dict[str, str] | None:
    document = record.get("document") if isinstance(record.get("document"), dict) else {}
    title = _first_text(record.get("title"), document.get("title"), record.get("name"))
    url = _first_text(record.get("url"), document.get("url"), record.get("web_url"), record.get("permalink"))
    tldr = _first_text(
        record.get("tldr"),
        record.get("summary"),
        record.get("snippet"),
        _snippet_text(record.get("snippets")),
        document.get("summary"),
    )
    haystack = f"{title} {url} {tldr}".lower()
    if not title or not any(marker in haystack for marker in PRD_MARKERS):
        return None
    return {
        "title": title,
        "url": url,
        "tldr": " ".join(tldr.split())[:700],
    }


def normalize_payload(payload: Any) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    items: list[dict[str, str]] = []
    for record in _records_from_payload(payload):
        normalized = normalize_record(record)
        if normalized is None:
            continue
        key = (normalized["title"].casefold(), normalized["url"])
        if key in seen:
            continue
        seen.add(key)
        items.append(normalized)
    return items


def write_cache(path: Path, items: list[dict[str, str]], source_query: str = "") -> dict[str, Any]:
    cache = {
        "generated_at": utc_now().isoformat(timespec="seconds"),
        "ttl_days": CACHE_TTL_DAYS,
        "source_query": source_query,
        "items": items,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return cache


def query_tokens(query: str) -> list[str]:
    return [token for token in re.findall(r"[a-z0-9]+", query.lower()) if len(token) >= 2]


def score_item(item: dict[str, str], tokens: list[str]) -> int:
    text = f"{item.get('title', '')} {item.get('tldr', '')}".lower()
    return sum(3 if token in item.get("title", "").lower() else 1 for token in tokens if token in text)


def search_items(items: list[dict[str, str]], query: str, limit: int) -> list[dict[str, str]]:
    tokens = query_tokens(query)
    if not tokens:
        return []
    scored = [(score_item(item, tokens), item) for item in items]
    return [item for score, item in sorted(scored, key=lambda pair: pair[0], reverse=True) if score > 0][:limit]


def cmd_status(args: argparse.Namespace) -> int:
    cache = load_cache(args.cache)
    if cache is None:
        print(f"missing: {args.cache}")
        return 1
    age = cache_age_days(cache)
    item_count = len(cache.get("items", [])) if isinstance(cache.get("items"), list) else 0
    freshness = "fresh" if is_cache_fresh(cache) else "stale"
    print(f"{freshness}: {item_count} PRD summaries, age={age if age is not None else 'unknown'}d, cache={args.cache}")
    return 0 if freshness == "fresh" else 1


def cmd_write(args: argparse.Namespace) -> int:
    payload = read_json(args.input)
    items = normalize_payload(payload)
    write_cache(args.cache, items, source_query=args.source_query or "")
    print(f"wrote {len(items)} PRD summaries to {args.cache}")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    cache = load_cache(args.cache)
    if cache is None or not is_cache_fresh(cache):
        print(f"PRD cache missing or stale: {args.cache}", file=sys.stderr)
        return 2
    items = cache.get("items", [])
    if not isinstance(items, list):
        raise ValueError("Cache items must be a list")
    matches = search_items([item for item in items if isinstance(item, dict)], args.query, args.limit)
    print(json.dumps(matches, indent=2, sort_keys=True))
    return 0


def cmd_refresh(args: argparse.Namespace) -> int:
    query = args.query or GLEAN_QUERY
    cmd = [
        "glean", "search",
        "--page-size", str(args.page_size),
        "--fields", GLEAN_FIELDS,
        query,
    ]
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"glean search failed: {result.stderr.strip()}", file=sys.stderr)
            return 1
        tmp_path.write_text(result.stdout, encoding="utf-8")
        payload = read_json(tmp_path)
        items = normalize_payload(payload)
        write_cache(args.cache, items, source_query=query)
        print(f"refreshed: {len(items)} PRD summaries written to {args.cache}")
        return 0
    finally:
        tmp_path.unlink(missing_ok=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE_PATH)
    subparsers = parser.add_subparsers(dest="command", required=True)

    status = subparsers.add_parser("status", help="Check whether the local PRD cache is fresh")
    status.set_defaults(func=cmd_status)

    write = subparsers.add_parser("write", help="Build the cache from a bounded Glean JSON result")
    write.add_argument("--input", type=Path, required=True)
    write.add_argument("--source-query", default="")
    write.set_defaults(func=cmd_write)

    search = subparsers.add_parser("search", help="Search cached PRD titles and TLDRs")
    search.add_argument("--query", required=True)
    search.add_argument("--limit", type=int, default=5)
    search.set_defaults(func=cmd_search)

    refresh = subparsers.add_parser("refresh", help="Fetch PRDs from Glean and rebuild the cache")
    refresh.add_argument("--query", default="", help="Override the default Glean search query")
    refresh.add_argument("--page-size", type=int, default=GLEAN_PAGE_SIZE)
    refresh.set_defaults(func=cmd_refresh)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
