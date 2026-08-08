---
name: news-feed
description: Manual-invocation only. Weekly vendor announcement triage for DevOps-relevant AI, security, observability, platform, and infrastructure changes. Run via /apollo-eng-devops:news-feed.
disable-model-invocation: true
---

# DevOps Vendor News Feed

Use this skill to run the weekly vendor announcement flow for DevOps-relevant AI, security, platform, and infrastructure changes.

## Inputs

- Default lookback: 7 days.
- Default feeds: OpenAI news, Anthropic news listing, prioritized Cloudflare changelog feeds, Grafana feature announcements, Google Cloud release notes, PagerDuty platform release notes, Slack developer changelog, Atlassian/Jira developer changelogs, and Cursor changelog.
- PagerDuty, Slack, Atlassian/Jira, and Cursor feeds require AI-related keyword matches before they become candidates.
- Single-post evaluator: `/apollo-eng-devops:wtf-does-this-do <post-url>`.
- Apps DB source: Notion data source `collection://23bab2b3-b496-800a-b873-000b6835efe9`.

## Flow

1. Run the feed script:

   ```bash
   python3 plugins/apollo-eng-devops/skills/news-feed/scripts/fetch_vendor_posts.py --days 7
   ```

1. If the script returns fetch errors, keep going with successful feeds and mention feed failures only in the internal/thread note unless they prevent all review.

1. For every returned candidate, invoke `/apollo-eng-devops:wtf-does-this-do <post-url>`. Never invoke `wtf-does-this-do` on RSS feeds, listing pages, or vendor homepages.

1. Read [`references/vendor-apollo-context.md`](references/vendor-apollo-context.md) to contextualize each vendor announcement.

1. Search Apps DB in Notion for the vendor and any product names surfaced by the post or reference context.

1. Use Apps DB fields when present: `Name`, `Owner`, `Owner | Team`, `Users | Team`, `Status`, `Description`, `Website`, `Slack Channel`, `Notes`.

1. If the reference says Apollo uses the vendor/product but Apps DB has no matching active record, flag `Apps DB gap`.

1. Select 1-3 items based on Apollo relevance, operational risk, product leverage, and owner actionability.

## Selection Rules

- Share only announcements with a concrete Apollo implication.
- Prefer changes that affect security posture, compliance, account administration, APIs, model/platform capabilities, networking, observability, reliability, or cost/control surfaces.
- Drop pure marketing, hiring, awards, customer stories, and posts where Apollo has no plausible action.
- If no item clears the bar, write a short no-op note in the automation thread/log and do not post to Slack.

## Output

When posting, use this shape:

```markdown
## Vendor News Feed

### <Vendor>: <Announcement>

- What changed: <plain read>
- Why Apollo should care: <specific Apollo implication>
- Owner/team: <Apps DB owner/team or Apps DB gap>
- Investment path: <what trying/adopting/monitoring would look like>
- Confidence: verified / inferred
- Source: <post URL>
```

Post to Slack only when there are selected items and `SLACK_WEBHOOK_URL` is available. Never print or expose the webhook URL.

## Script Configuration

The script accepts extra feeds without editing code. RSS and Atom are parsed by default. For a vendor without a working RSS feed, use `|html_listing` as the fourth field. For changelog pages with dated headings and stable `CHANGE-*` anchors, use `html_changelog` in JSON config. For changelog pages organized as one HTML `<article>` per post, use `html_article_changelog`.

```bash
python3 plugins/apollo-eng-devops/skills/news-feed/scripts/fetch_vendor_posts.py \
  --feed "Vendor|Feed label|https://example.com/rss.xml" \
  --feed "Vendor|News listing|https://example.com/news|html_listing"
```

It can also read a JSON feed config. Use `required_keywords` when a source should be filtered to a narrower topic such as AI news, and `path_prefixes` when scraping an HTML listing without RSS:

```json
[
  {"vendor": "Vendor", "name": "Feed label", "url": "https://example.com/rss.xml"},
  {
    "vendor": "Vendor",
    "name": "AI-only feed",
    "url": "https://example.com/rss.xml",
    "required_keywords": ["AI", "agent"]
  },
  {
    "vendor": "Vendor",
    "name": "News listing",
    "url": "https://example.com/news",
    "kind": "html_listing",
    "path_prefixes": ["/news/"]
  }
]
```

Pass that file with `--feeds-json <path>`.
