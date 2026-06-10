#!/usr/bin/env python3
"""Fetch vendor RSS/Atom feeds and return recent keyword-matched posts as JSON."""

import argparse
import email.utils
import html
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse


DEFAULT_KEYWORDS = [
    "AI",
    "agent",
    "Claude",
    "ChatGPT",
    "Codex",
    "API",
    "model",
    "MCP",
    "security",
    "compliance",
    "DLP",
    "CASB",
    "SSO",
    "audit",
    "gateway",
    "network",
    "DNS",
    "WAF",
    "workers",
    "platform",
    "reliability",
    "incident",
    "observability",
    "data residency",
    "Grafana Assistant",
    "alerting",
    "IRM",
    "SLO",
    "Loki",
    "Tempo",
    "Mimir",
    "Prometheus",
    "OpenTelemetry",
    "Kubernetes",
    "traces",
    "logs",
    "metrics",
    "dashboards",
    "RBAC",
    "Terraform",
    "cost",
    "k6",
    "Alloy",
    "Google Cloud",
    "GCP",
    "Gemini",
    "Vertex AI",
    "PagerDuty",
    "AIOps",
    "Atlassian Intelligence",
    "Rovo",
    "Jira",
    "Slack AI",
    "Cursor",
    "Composer",
]

DEFAULT_AI_REQUIRED_KEYWORDS = [
    "AI",
    "agent",
    "agents",
    "AIOps",
    "artificial intelligence",
    "automation",
    "Claude",
    "ChatGPT",
    "Codex",
    "Composer",
    "Cursor",
    "Duet AI",
    "Gemini",
    "GenAI",
    "generative AI",
    "LLM",
    "machine learning",
    "Rovo",
    "Slack AI",
    "Vertex AI",
]

DEFAULT_FEEDS = [
    {
        "vendor": "OpenAI",
        "name": "OpenAI News",
        "url": "https://openai.com/news/rss.xml",
    },
    {
        "vendor": "Anthropic",
        "name": "Anthropic News listing",
        "url": "https://www.anthropic.com/news",
        "kind": "html_listing",
    },
    {
        "vendor": "Cloudflare",
        "name": "Cloudflare changelog: global",
        "url": "https://developers.cloudflare.com/changelog/rss/index.xml",
    },
    {
        "vendor": "Cloudflare",
        "name": "Cloudflare changelog: Cloudflare One",
        "url": "https://developers.cloudflare.com/changelog/rss/cloudflare-one.xml",
    },
    {
        "vendor": "Cloudflare",
        "name": "Cloudflare changelog: Core platform",
        "url": "https://developers.cloudflare.com/changelog/rss/core-platform.xml",
    },
    {
        "vendor": "Cloudflare",
        "name": "Cloudflare changelog: Developer platform",
        "url": "https://developers.cloudflare.com/changelog/rss/developer-platform.xml",
    },
    {
        "vendor": "Grafana",
        "name": "Grafana Labs What's New",
        "url": "https://grafana.com/whats-new/index.xml",
    },
    {
        "vendor": "Google Cloud",
        "name": "Google Cloud release notes",
        "url": "https://docs.cloud.google.com/feeds/gcp-release-notes.xml",
    },
    {
        "vendor": "PagerDuty",
        "name": "PagerDuty platform release notes",
        "url": "https://support.pagerduty.com/main/changelog.rss",
        "required_keywords": DEFAULT_AI_REQUIRED_KEYWORDS,
    },
    {
        "vendor": "Slack",
        "name": "Slack developer changelog",
        "url": "https://docs.slack.dev/changelog/rss.xml",
        "required_keywords": DEFAULT_AI_REQUIRED_KEYWORDS,
    },
    {
        "vendor": "Atlassian",
        "name": "Atlassian developer changelog",
        "url": "https://developer.atlassian.com/changelog/",
        "kind": "html_changelog",
        "required_keywords": DEFAULT_AI_REQUIRED_KEYWORDS,
    },
    {
        "vendor": "Atlassian",
        "name": "Jira Software Cloud changelog",
        "url": "https://developer.atlassian.com/cloud/jira/software/changelog/",
        "kind": "html_changelog",
        "required_keywords": DEFAULT_AI_REQUIRED_KEYWORDS,
    },
    {
        "vendor": "Cursor",
        "name": "Cursor changelog",
        "url": "https://cursor.com/changelog",
        "kind": "html_article_changelog",
        "required_keywords": DEFAULT_AI_REQUIRED_KEYWORDS,
    },
]


@dataclass(frozen=True)
class Feed:
    vendor: str
    name: str
    url: str
    kind: str = "xml"
    required_keywords: tuple[str, ...] = ()
    path_prefixes: tuple[str, ...] = ("/news/", "/research/")


def strip_namespace(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def direct_child(element: ET.Element, *names: str) -> ET.Element | None:
    wanted = {name.lower() for name in names}
    for child in list(element):
        if strip_namespace(child.tag) in wanted:
            return child
    return None


def direct_text(element: ET.Element, *names: str) -> str:
    child = direct_child(element, *names)
    if child is None or child.text is None:
        return ""
    return clean_text(child.text)


def clean_text(value: str) -> str:
    value = html.unescape(value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def parse_datetime(value: str) -> datetime | None:
    if not value:
        return None

    try:
        parsed = email.utils.parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError, IndexError):
        pass

    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        pass

    for fmt in ("%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(value.strip(), fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            pass

    return None


def keyword_pattern(keyword: str) -> re.Pattern[str]:
    escaped = re.escape(keyword)
    prefix = r"\b" if keyword[0].isalnum() else ""
    suffix = r"\b" if keyword[-1].isalnum() else ""
    return re.compile(prefix + escaped + suffix, re.IGNORECASE)


def matched_keywords(text: str, keywords: Iterable[str]) -> list[str]:
    matches = []
    for keyword in keywords:
        if keyword_pattern(keyword).search(text):
            matches.append(keyword)
    return matches


def read_url(url: str, timeout: int) -> bytes:
    parsed = urlparse(url)
    if parsed.scheme == "file":
        return Path(parsed.path).read_bytes()
    if not parsed.scheme:
        return Path(url).read_bytes()

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "apollo-vendor-news-feed/1.0 (+https://apollo.io)",
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def item_link(item: ET.Element) -> str:
    link = direct_child(item, "link")
    if link is None:
        return ""
    href = link.attrib.get("href")
    if href:
        return href.strip()
    if link.text:
        return link.text.strip()
    return ""


def parse_entries(xml_bytes: bytes) -> list[dict[str, str]]:
    root = ET.fromstring(xml_bytes)
    root_name = strip_namespace(root.tag)

    if root_name == "rss":
        channel = direct_child(root, "channel")
        if channel is None:
            return []
        items = [child for child in list(channel) if strip_namespace(child.tag) == "item"]
        return [
            {
                "title": direct_text(item, "title"),
                "url": item_link(item),
                "published_raw": direct_text(item, "pubDate", "published", "updated", "dc:date"),
                "summary": direct_text(item, "description", "summary", "content", "encoded"),
            }
            for item in items
        ]

    if root_name == "feed":
        entries = [child for child in list(root) if strip_namespace(child.tag) == "entry"]
        return [
            {
                "title": direct_text(entry, "title"),
                "url": item_link(entry),
                "published_raw": direct_text(entry, "published", "updated"),
                "summary": direct_text(entry, "summary", "content"),
            }
            for entry in entries
        ]

    return []


def parse_html_listing_entries(
    html_bytes: bytes, base_url: str, path_prefixes: tuple[str, ...]
) -> list[dict[str, str]]:
    text = html_bytes.decode("utf-8", errors="replace")
    entries: list[dict[str, str]] = []
    seen: set[str] = set()

    anchor_pattern = re.compile(
        r'<a\b[^>]*href=["\'](?P<href>[^"\']+)["\'][^>]*>'
        r"(?P<body>.*?)</a>",
        re.IGNORECASE | re.DOTALL,
    )
    title_pattern = re.compile(r"<h[1-6]\b[^>]*>(?P<title>.*?)</h[1-6]>", re.IGNORECASE | re.DOTALL)
    time_pattern = re.compile(r"<time\b[^>]*>(?P<date>.*?)</time>", re.IGNORECASE | re.DOTALL)
    summary_pattern = re.compile(r"<p\b[^>]*>(?P<summary>.*?)</p>", re.IGNORECASE | re.DOTALL)

    for match in anchor_pattern.finditer(text):
        href = match.group("href")
        url = urljoin(base_url, href)
        path = urlparse(url).path
        if not any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in path_prefixes):
            continue
        if url in seen:
            continue

        body = match.group("body")
        title_match = title_pattern.search(body)
        title = clean_text(title_match.group("title")) if title_match else clean_text(body)
        if not title:
            continue

        time_match = time_pattern.search(body)
        summary_match = summary_pattern.search(body)
        seen.add(url)
        entries.append(
            {
                "title": title,
                "url": url,
                "published_raw": clean_text(time_match.group("date")) if time_match else "",
                "summary": clean_text(summary_match.group("summary")) if summary_match else "",
            }
        )

    return entries


def parse_html_changelog_entries(html_bytes: bytes, base_url: str) -> list[dict[str, str]]:
    text = html_bytes.decode("utf-8", errors="replace")
    entries: list[dict[str, str]] = []
    date_matches = list(
        re.finditer(r"<h2\b[^>]*>(?P<date>.*?)</h2>", text, re.IGNORECASE | re.DOTALL)
    )
    entry_pattern = re.compile(
        r'<div\b[^>]*\bid=["\'](?P<id>CHANGE-[^"\']+)["\'][^>]*>.*?'
        r"<h4\b[^>]*>(?P<title>.*?)</h4>(?P<body>.*?)(?=<div\b[^>]*\bid=[\"']CHANGE-|$)",
        re.IGNORECASE | re.DOTALL,
    )

    for index, date_match in enumerate(date_matches):
        block_start = date_match.end()
        block_end = date_matches[index + 1].start() if index + 1 < len(date_matches) else len(text)
        block = text[block_start:block_end]
        published_raw = clean_text(date_match.group("date"))

        for entry_match in entry_pattern.finditer(block):
            title = clean_text(entry_match.group("title"))
            if not title:
                continue
            entries.append(
                {
                    "title": title,
                    "url": f"{base_url.rstrip('/')}#{entry_match.group('id')}",
                    "published_raw": published_raw,
                    "summary": clean_text(entry_match.group("body")),
                }
            )

    return entries


def parse_html_article_changelog_entries(html_bytes: bytes, base_url: str) -> list[dict[str, str]]:
    text = html_bytes.decode("utf-8", errors="replace")
    entries: list[dict[str, str]] = []
    seen: set[str] = set()
    article_pattern = re.compile(r"<article\b[^>]*>(?P<body>.*?)</article>", re.IGNORECASE | re.DOTALL)
    href_pattern = re.compile(r'href=["\'](?P<href>/changelog/[^"\']+)["\']', re.IGNORECASE)
    time_pattern = re.compile(
        r"<time\b(?P<attrs>[^>]*)>(?P<date>.*?)</time>",
        re.IGNORECASE | re.DOTALL,
    )
    datetime_attr_pattern = re.compile(
        r'(?:dateTime|datetime)=["\'](?P<datetime>[^"\']+)["\']',
        re.IGNORECASE,
    )
    title_pattern = re.compile(r"<h1\b[^>]*>(?P<title>.*?)</h1>", re.IGNORECASE | re.DOTALL)
    prose_pattern = re.compile(
        r'<div\b[^>]*class=["\'][^"\']*\bprose\b[^"\']*["\'][^>]*>(?P<summary>.*?)</div>',
        re.IGNORECASE | re.DOTALL,
    )

    for article_match in article_pattern.finditer(text):
        body = article_match.group("body")
        href_match = href_pattern.search(body)
        title_match = title_pattern.search(body)
        if not href_match or not title_match:
            continue

        url = urljoin(base_url, href_match.group("href"))
        if url in seen:
            continue

        time_match = time_pattern.search(body)
        datetime_attr_match = (
            datetime_attr_pattern.search(time_match.group("attrs")) if time_match else None
        )
        prose_match = prose_pattern.search(body)
        seen.add(url)
        entries.append(
            {
                "title": clean_text(title_match.group("title")),
                "url": url,
                "published_raw": (
                    datetime_attr_match.group("datetime")
                    if datetime_attr_match
                    else clean_text(time_match.group("date"))
                    if time_match
                    else ""
                ),
                "summary": clean_text(prose_match.group("summary")) if prose_match else "",
            }
        )

    return entries


def collect_candidates(
    feeds: Iterable[Feed],
    keywords: list[str],
    since: datetime,
    timeout: int,
    include_undated: bool,
) -> tuple[list[dict[str, object]], list[dict[str, str]]]:
    candidates: list[dict[str, object]] = []
    errors: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for feed in feeds:
        try:
            feed_bytes = read_url(feed.url, timeout)
            if feed.kind == "html_listing":
                entries = parse_html_listing_entries(feed_bytes, feed.url, feed.path_prefixes)
            elif feed.kind == "html_changelog":
                entries = parse_html_changelog_entries(feed_bytes, feed.url)
            elif feed.kind == "html_article_changelog":
                entries = parse_html_article_changelog_entries(feed_bytes, feed.url)
            else:
                entries = parse_entries(feed_bytes)
        except Exception as exc:
            errors.append(
                {
                    "vendor": feed.vendor,
                    "feed": feed.name,
                    "url": feed.url,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            continue

        for entry in entries:
            url = entry["url"]
            if not url or url in seen_urls:
                continue

            published = parse_datetime(entry["published_raw"])
            if published is None and not include_undated:
                continue
            if published is not None and published < since:
                continue

            text = " ".join([entry["title"], entry["summary"]])
            matches = matched_keywords(text, keywords)
            if not matches:
                continue
            required_matches = matched_keywords(text, feed.required_keywords)
            if feed.required_keywords and not required_matches:
                continue

            seen_urls.add(url)
            candidates.append(
                {
                    "vendor": feed.vendor,
                    "feed": feed.name,
                    "title": entry["title"],
                    "url": url,
                    "published_at": published.isoformat() if published else None,
                    "matched_keywords": matches,
                    "required_keyword_matches": required_matches,
                    "summary": entry["summary"],
                }
            )

    candidates.sort(key=lambda item: item.get("published_at") or "", reverse=True)
    return candidates, errors


def load_feeds(path: str | None, feed_specs: list[str]) -> list[Feed]:
    raw_feeds = list(DEFAULT_FEEDS)

    if path:
        raw_feeds = json.loads(Path(path).read_text())

    for spec in feed_specs:
        parts = spec.split("|", 3)
        if len(parts) not in (3, 4):
            raise ValueError("--feed must use 'Vendor|Feed label|URL' or 'Vendor|Feed label|URL|kind'")
        raw_feeds.append(
            {
                "vendor": parts[0],
                "name": parts[1],
                "url": parts[2],
                "kind": parts[3] if len(parts) == 4 else "xml",
            }
        )

    feeds = []
    for item in raw_feeds:
        feeds.append(
            Feed(
                vendor=item["vendor"],
                name=item["name"],
                url=item["url"],
                kind=item.get("kind", "xml"),
                required_keywords=tuple(item.get("required_keywords", [])),
                path_prefixes=tuple(item.get("path_prefixes", ["/news/", "/research/"])),
            )
        )
    return feeds


def parse_now(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    parsed = parse_datetime(value)
    if parsed is None:
        raise ValueError(f"Could not parse --now value: {value}")
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=7, help="Lookback window in days.")
    parser.add_argument("--now", help="Override current time for deterministic tests.")
    parser.add_argument("--feeds-json", help="JSON file containing feed objects.")
    parser.add_argument(
        "--feed",
        action="append",
        default=[],
        help="Add a feed as 'Vendor|Feed label|URL'.",
    )
    parser.add_argument(
        "--keyword",
        action="append",
        default=[],
        help="Add a keyword to the default keyword list.",
    )
    parser.add_argument("--timeout", type=int, default=20, help="Network timeout in seconds.")
    parser.add_argument(
        "--include-undated",
        action="store_true",
        help="Include keyword-matched posts that do not expose a parseable date.",
    )
    args = parser.parse_args()

    now = parse_now(args.now)
    since = (now - timedelta(days=args.days)).replace(hour=0, minute=0, second=0, microsecond=0)
    feeds = load_feeds(args.feeds_json, args.feed)
    keywords = DEFAULT_KEYWORDS + args.keyword
    candidates, errors = collect_candidates(
        feeds=feeds,
        keywords=keywords,
        since=since,
        timeout=args.timeout,
        include_undated=args.include_undated,
    )

    print(
        json.dumps(
            {
                "generated_at": now.isoformat(),
                "since": since.isoformat(),
                "keywords": keywords,
                "candidates": candidates,
                "errors": errors,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
