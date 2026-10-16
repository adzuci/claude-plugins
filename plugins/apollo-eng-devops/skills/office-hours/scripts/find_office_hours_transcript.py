#!/usr/bin/env python3
"""Find office-hours transcript candidates through scriptable indexed sources.

Run from the skill directory (plugins/apollo-eng-devops/skills/office-hours) or use
an absolute path; the script has no relative file dependencies.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from typing import Any


DEFAULT_SOURCES = ["zoom", "notion"]
QUERY_VARIANTS = [
    "{query} {date}",
    "devops {date}",
    "xfn h devops {date}",
    "Adam Blackwell {date}",
    "Eng Design Office Hours {date}",
    "DOH {date}",
    "{query}",
]
RELEVANCE_TERMS = [
    "office hour",
    "office-hour",
    "devops",
    "xfn h devops",
    "doh",
    "eng design office hours",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only search for office-hours transcript candidates via the local glean CLI."
    )
    parser.add_argument("--date", required=True, help="Office-hours date as YYYY-MM-DD.")
    parser.add_argument("--query", default="office hours", help="Primary search query.")
    parser.add_argument(
        "--sources",
        default=",".join(DEFAULT_SOURCES),
        help="Comma-separated Glean datasources to search in order.",
    )
    parser.add_argument(
        "--max-sources",
        type=int,
        default=2,
        help="Maximum number of sources to query.",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=5,
        help="Results to request per query variant.",
    )
    parser.add_argument(
        "--max-candidates",
        type=int,
        default=8,
        help="Maximum candidates to emit per source.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON. The script always emits JSON; this flag keeps the CLI explicit.",
    )
    return parser.parse_args()


def run_command(argv: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(argv, capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout, proc.stderr


def load_json(raw: str) -> dict[str, Any]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def result_document(result: dict[str, Any]) -> dict[str, Any]:
    document = result.get("document")
    if isinstance(document, dict):
        return document
    return result


def snippets_for(result: dict[str, Any]) -> list[str]:
    snippets: list[str] = []
    for key in ("snippets", "allSnippets"):
        values = result.get(key)
        if isinstance(values, list):
            for item in values:
                if isinstance(item, str):
                    snippets.append(item)
                elif isinstance(item, dict):
                    text = item.get("snippet") or item.get("text")
                    if isinstance(text, str):
                        snippets.append(text)
    document = result_document(result)
    for key in ("snippets", "allSnippets"):
        values = document.get(key)
        if isinstance(values, list):
            for item in values:
                if isinstance(item, str):
                    snippets.append(item)
                elif isinstance(item, dict):
                    text = item.get("snippet") or item.get("text")
                    if isinstance(text, str):
                        snippets.append(text)
    return snippets


def compact(text: str, limit: int = 1200) -> str:
    squashed = " ".join(text.split())
    if len(squashed) <= limit:
        return squashed
    return squashed[: limit - 3] + "..."


def date_matches(doc: dict[str, Any], snippets: list[str], date: str) -> bool:
    parsed = datetime.strptime(date, "%Y-%m-%d")
    month_full = parsed.strftime("%B")
    month_short = parsed.strftime("%b")
    date_forms = {
        date,
        f"{month_full} {parsed.day}, {parsed.year}",
        f"{month_short} {parsed.day}, {parsed.year}",
        f"{month_full} {parsed.day}",
        f"{month_short} {parsed.day}",
    }
    haystack_parts: list[str] = []
    for key in ("updateTime", "createdTime", "modifiedTime"):
        value = doc.get(key)
        if isinstance(value, str):
            haystack_parts.append(value)
    haystack_parts.extend(snippets)
    return any(form in part for form in date_forms for part in haystack_parts)


def confidence_for(doc: dict[str, Any], snippets: list[str], date: str) -> str:
    if date_matches(doc, snippets, date):
        return "likely"
    if any(doc.get(key) for key in ("updateTime", "createdTime", "modifiedTime")):
        return "low"
    return "unknown"


def is_relevant(title: Any, snippets: list[str]) -> bool:
    text = " ".join([str(title or ""), *snippets]).lower()
    return any(term in text for term in RELEVANCE_TERMS)


def search_source(
    glean_path: str,
    source: str,
    query: str,
    date: str,
    page_size: int,
    max_candidates: int,
) -> dict[str, Any]:
    source_report: dict[str, Any] = {
        "source": source,
        "status": "not_found",
        "queries": [],
        "candidates": [],
        "failure_reason": None,
    }

    for variant_template in QUERY_VARIANTS:
        variant = variant_template.format(query=query, date=date)
        source_report["queries"].append(variant)
        code, stdout, stderr = run_command(
            [
                glean_path,
                "search",
                "--datasource",
                source,
                "--page-size",
                str(page_size),
                "--max-snippet-size",
                "800",
                "--output",
                "json",
                variant,
            ]
        )
        if code != 0:
            source_report["status"] = "error"
            source_report["failure_reason"] = compact(stderr or stdout or "glean search failed")
            return source_report

        data = load_json(stdout)
        results = data.get("results")
        if not isinstance(results, list) or not results:
            continue

        for result in results:
            if not isinstance(result, dict):
                continue
            doc = result_document(result)
            snippets = snippets_for(result)
            title = doc.get("title") or result.get("title")
            if not is_relevant(title, snippets):
                continue
            url = doc.get("url") or result.get("url")
            candidate = {
                "query": variant,
                "title": title,
                "url": url,
                "confidence": confidence_for(doc, snippets, date),
                "preview": compact(" ".join(snippets)),
            }
            if url:
                candidate["document_preview"] = fetch_document_preview(glean_path, url)
            source_report["candidates"].append(candidate)
            if len(source_report["candidates"]) >= max_candidates:
                break

        if any(candidate["confidence"] == "likely" for candidate in source_report["candidates"]):
            source_report["status"] = "found"
            return source_report
        if len(source_report["candidates"]) >= max_candidates:
            break

    if source_report["candidates"]:
        source_report["status"] = "unverified_candidates"
        source_report["failure_reason"] = "Candidates found, but none matched the requested date."
        return source_report

    source_report["failure_reason"] = "No matching candidates returned by Glean search."
    return source_report


def fetch_document_preview(glean_path: str, url: str) -> str | None:
    payload = {"documentSpecs": [{"url": url}]}
    code, stdout, _stderr = run_command(
        [glean_path, "documents", "get", "--json", json.dumps(payload)]
    )
    if code != 0:
        return None
    data = load_json(stdout)
    return extract_text_preview(data)


def extract_text_preview(value: Any) -> str | None:
    found: list[str] = []

    def walk(node: Any) -> None:
        if len(" ".join(found)) > 1200:
            return
        if isinstance(node, dict):
            for key, child in node.items():
                if key in {"text", "content", "body", "snippet"} and isinstance(child, str):
                    found.append(child)
                else:
                    walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(value)
    preview = compact(" ".join(found))
    return preview or None


def main() -> int:
    args = parse_args()
    try:
        datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        print(json.dumps({"status": "error", "error": "--date must be YYYY-MM-DD"}))
        return 2

    glean_path = shutil.which("glean")
    if not glean_path:
        print(
            json.dumps(
                {
                    "status": "error",
                    "error": "glean CLI not found on PATH",
                    "sources": [],
                },
                indent=2,
            )
        )
        return 1

    sources = [source.strip() for source in args.sources.split(",") if source.strip()]
    selected_sources = sources[: max(args.max_sources, 0)]
    reports = [
        search_source(
            glean_path,
            source,
            args.query,
            args.date,
            args.page_size,
            args.max_candidates,
        )
        for source in selected_sources
    ]
    status = "found" if any(report["status"] == "found" for report in reports) else "not_found"
    output = {
        "status": status,
        "date": args.date,
        "query": args.query,
        "source_limit": args.max_sources,
        "sources": reports,
        "posting": "disabled",
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
