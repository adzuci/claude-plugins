# Notion Tracking

## Notion Tracking Database

| Field | Value |
|-------|-------|
| Database ID | `d34d17c8a5f540a8a6e35b41ab5cd217` |
| Data source ID | `7e11624f-456d-42a0-963e-4dc4af5f2a6d` |
| URL | <https://app.notion.com/p/d34d17c8a5f540a8a6e35b41ab5cd217> |

## Notion Insert Call

Use tool `mcp__notion__notion-create-pages` with this argument shape:

```json
{
  "parent": {
    "type": "data_source_id",
    "data_source_id": "7e11624f-456d-42a0-963e-4dc4af5f2a6d"
  },
  "properties": {
    "Name": {
      "title": [
        {
          "text": {
            "content": "<name> setup"
          }
        }
      ]
    },
    "date:Date:start": "YYYY-MM-DD",
    "Issues hit": {
      "rich_text": [
        {
          "text": {
            "content": "- plugin install skipped (GitHub rate limit); used GUI fallback\n- none"
          }
        }
      ]
    }
  }
}
```

**Note:** The date property key is `date:Date:start` (not `"Date"`). Use an ISO date string (`YYYY-MM-DD`). Set `"Issues hit"` to a bullet list of problems encountered this run, or `"none"` if everything went cleanly.

## Filled Example

```json
{
  "parent": {
    "type": "data_source_id",
    "data_source_id": "7e11624f-456d-42a0-963e-4dc4af5f2a6d"
  },
  "properties": {
    "Name": {
      "title": [
        {
          "text": {
            "content": "devops setup"
          }
        }
      ]
    },
    "date:Date:start": "2026-06-03",
    "Issues hit": {
      "rich_text": [
        {
          "text": {
            "content": "none"
          }
        }
      ]
    }
  }
}
```
