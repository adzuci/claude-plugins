#!/usr/bin/env python3
"""Small fixture tests for fetch_vendor_posts.py."""

import json
import subprocess
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("fetch_vendor_posts.py")


RSS_FIXTURE = """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>Vendor RSS</title>
    <item>
      <title>New API security audit controls</title>
      <link>https://example.com/security-api</link>
      <pubDate>Tue, 19 May 2026 12:00:00 GMT</pubDate>
      <description>SSO, audit logs, and compliance features for enterprise teams.</description>
    </item>
    <item>
      <title>Customer story</title>
      <link>https://example.com/customer-story</link>
      <pubDate>Tue, 19 May 2026 12:00:00 GMT</pubDate>
      <description>A customer story with no relevant keywords.</description>
    </item>
    <item>
      <title>Old WAF update</title>
      <link>https://example.com/old-waf</link>
      <pubDate>Tue, 05 May 2026 12:00:00 GMT</pubDate>
      <description>WAF rules changed.</description>
    </item>
  </channel>
</rss>
"""


ATOM_FIXTURE = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Vendor Atom</title>
  <entry>
    <title>Claude agent platform release</title>
    <link href="https://example.com/claude-agent"/>
    <updated>2026-05-20T12:00:00Z</updated>
    <summary>New MCP and agent workflow support.</summary>
  </entry>
  <entry>
    <title>Hiring update</title>
    <link href="https://example.com/hiring"/>
    <updated>2026-05-20T12:00:00Z</updated>
    <summary>New regional office.</summary>
  </entry>
</feed>
"""


GRAFANA_FIXTURE = """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>Grafana What's New</title>
    <item>
      <title>RBAC behavior changes with Grafana 13</title>
      <link>https://example.com/grafana-rbac</link>
      <pubDate>Wed, 20 May 2026 12:00:00 GMT</pubDate>
      <description>Terraform-managed roles and dashboard permissions need review.</description>
    </item>
  </channel>
</rss>
"""


HTML_FIXTURE = """<!doctype html>
<html>
  <body>
    <a href="/news/claude-opus">
      <div><span>Product</span><time>May 20, 2026</time></div>
      <h2>Introducing Claude Opus platform controls</h2>
      <p>New Claude Enterprise audit and SSO controls for agent workflows.</p>
    </a>
    <a href="/news/community-event">
      <div><span>Company</span><time>May 20, 2026</time></div>
      <h2>Community meetup</h2>
      <p>Join us for snacks.</p>
    </a>
  </body>
</html>
"""


CURSOR_HTML_FIXTURE = """<!doctype html>
<html>
  <body>
    <a href="/changelog/cursor-in-jira">
      <div><time>May 19, 2026</time></div>
      <h2>Cursor in Jira</h2>
      <p>Mention Cursor in a Jira work item to start a cloud agent.</p>
    </a>
    <a href="/changelog/theme-polish">
      <div><time>May 19, 2026</time></div>
      <h2>Theme polish</h2>
      <p>New editor colors.</p>
    </a>
  </body>
</html>
"""


ARTICLE_CHANGELOG_FIXTURE = """<!doctype html>
<html>
  <body>
    <article>
      <a href="/changelog/05-20-26"><time dateTime="2026-05-20T00:00:00.000Z">May 20, 2026</time></a>
      <h1><a href="/changelog/05-20-26">Improvements to Cursor Automations</a></h1>
      <div class="prose"><p>Cursor agents can now run automations across multiple repos.</p></div>
    </article>
    <article>
      <a href="/changelog/05-19-26"><time dateTime="2026-05-19T00:00:00.000Z">May 19, 2026</time></a>
      <h1><a href="/changelog/05-19-26">Theme polish</a></h1>
      <div class="prose"><p>Color updates.</p></div>
    </article>
  </body>
</html>
"""


AI_FILTER_FIXTURE = """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>AI required fixture</title>
    <item>
      <title>Incident API update</title>
      <link>https://example.com/api-only</link>
      <pubDate>Wed, 20 May 2026 12:00:00 GMT</pubDate>
      <description>New API fields for incident workflows.</description>
    </item>
    <item>
      <title>Insights Agent for incidents</title>
      <link>https://example.com/agent-incidents</link>
      <pubDate>Wed, 20 May 2026 12:00:00 GMT</pubDate>
      <description>New agent automation for incident analysis.</description>
    </item>
  </channel>
</rss>
"""


CHANGELOG_HTML_FIXTURE = """<!doctype html>
<html>
  <body>
    <h2>May 20, 2026</h2>
    <div id="CHANGE-100">
      <h4><span>Added</span> Rovo agent controls for Jira</h4>
      <p>Atlassian Intelligence and Rovo controls are available in Jira.</p>
    </div>
    <div id="CHANGE-101">
      <h4><span>Changed</span> Marketplace badge update</h4>
      <p>Non-AI marketplace copy.</p>
    </div>
  </body>
</html>
"""


def run_script(feed_path: Path) -> dict:
    result = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--feeds-json",
            str(feed_path),
            "--now",
            "2026-05-22T12:00:00Z",
            "--days",
            "7",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        rss_path = tmp_path / "sample.rss"
        atom_path = tmp_path / "sample.atom"
        grafana_path = tmp_path / "grafana.rss"
        html_path = tmp_path / "anthropic.html"
        cursor_html_path = tmp_path / "cursor.html"
        article_changelog_path = tmp_path / "article-changelog.html"
        ai_filter_path = tmp_path / "ai-filter.rss"
        changelog_html_path = tmp_path / "changelog.html"
        feeds_path = tmp_path / "feeds.json"

        rss_path.write_text(RSS_FIXTURE)
        atom_path.write_text(ATOM_FIXTURE)
        grafana_path.write_text(GRAFANA_FIXTURE)
        html_path.write_text(HTML_FIXTURE)
        cursor_html_path.write_text(CURSOR_HTML_FIXTURE)
        article_changelog_path.write_text(ARTICLE_CHANGELOG_FIXTURE)
        ai_filter_path.write_text(AI_FILTER_FIXTURE)
        changelog_html_path.write_text(CHANGELOG_HTML_FIXTURE)
        feeds_path.write_text(
            json.dumps(
                [
                    {
                        "vendor": "OpenAI",
                        "name": "RSS fixture",
                        "url": str(rss_path),
                    },
                    {
                        "vendor": "Anthropic",
                        "name": "Atom fixture",
                        "url": str(atom_path),
                    },
                    {
                        "vendor": "Grafana",
                        "name": "Grafana fixture",
                        "url": str(grafana_path),
                    },
                    {
                        "vendor": "Anthropic",
                        "name": "HTML fixture",
                        "url": f"file://{html_path}",
                        "kind": "html_listing",
                    },
                    {
                        "vendor": "Cursor",
                        "name": "Cursor HTML fixture",
                        "url": f"file://{cursor_html_path}",
                        "kind": "html_listing",
                        "required_keywords": ["agent", "Cursor"],
                        "path_prefixes": ["/changelog"],
                    },
                    {
                        "vendor": "Cursor",
                        "name": "Article changelog fixture",
                        "url": f"file://{article_changelog_path}",
                        "kind": "html_article_changelog",
                        "required_keywords": ["agent", "Cursor"],
                    },
                    {
                        "vendor": "PagerDuty",
                        "name": "AI required fixture",
                        "url": str(ai_filter_path),
                        "required_keywords": ["agent", "AI"],
                    },
                    {
                        "vendor": "Atlassian",
                        "name": "HTML changelog fixture",
                        "url": f"file://{changelog_html_path}",
                        "kind": "html_changelog",
                        "required_keywords": ["Rovo", "AI"],
                    },
                ]
            )
        )

        output = run_script(feeds_path)
        candidates = output["candidates"]
        urls = {candidate["url"] for candidate in candidates}

        assert "https://example.com/security-api" in urls
        assert "https://example.com/claude-agent" in urls
        assert "https://example.com/grafana-rbac" in urls
        assert any(
            candidate["title"] == "Introducing Claude Opus platform controls"
            for candidate in candidates
        )
        assert any(candidate["title"] == "Cursor in Jira" for candidate in candidates)
        assert any(
            candidate["title"] == "Improvements to Cursor Automations"
            for candidate in candidates
        )
        assert "https://example.com/agent-incidents" in urls
        assert any(candidate["url"].endswith("#CHANGE-100") for candidate in candidates)
        assert "https://example.com/customer-story" not in urls
        assert "https://example.com/old-waf" not in urls
        assert "https://example.com/api-only" not in urls
        assert output["errors"] == []

    print("fetch_vendor_posts.py fixture tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
