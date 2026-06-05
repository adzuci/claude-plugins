---
name: md-to-slack
description: >-
  Converts markdown output into Slack-ready mrkdwn and outputs it directly in
  the conversation — no artifact, no copy-paste of code. Trigger this skill whenever the
  user asks to "format for Slack", "convert to Slack", "make this Slack-friendly",
  "post this to Slack", "reformat for Slack", "Slack format", "copy to Slack",
  "share in Slack", or anything similar. Also trigger when the user says "format your
  last response for Slack" or "turn this into a Slack message." This skill outputs clean
  mrkdwn inside a single copyable code block so the user can paste it straight into any
  Slack channel, DM, or thread.
---

# Markdown → Slack Formatter

Convert Claude's markdown output to Slack-compatible mrkdwn and output it ready to copy-paste.

## Output format

Always produce:

1. One short line like: `Here's your message formatted for Slack — copy and paste directly:`
1. A single fenced code block containing **only** the converted mrkdwn text
1. A short note (outside the block) if any elements couldn't be converted cleanly (e.g. a complex table was restructured)

Nothing else. No commentary inside the code block. No repeated explanations.

## Source content

- User pastes text → convert that text
- User says "format your last response" / "format the above" / "format this" → convert the most recent Claude message in the conversation
- Ambiguous → ask once which content to convert, then proceed

______________________________________________________________________

## Conversion rules

Apply every rule below in order. When in doubt, prefer the simpler Slack-compatible form.

### 1. Bold

```
**text**   →   *text*
__text__   →   *text*
```

### 2. Italic

```
*text*    →   _text_     (single asterisk italic, not yet consumed by bold)
_text_    →   _text_     (already correct)
```

### 3. Bold + Italic

```
***text***  →  *_text_*
```

### 4. Strikethrough

```
~~text~~  →  ~text~
```

### 5. Inline code

Leave as-is: `` `code` `` is identical in Slack.

### 6. Code blocks

Strip the language hint from the opening fence; keep the content unchanged:

````
```python        →   ```
def foo(): ...       def foo(): ...
```              →   ```
````

### 7. Headings → bold lines

Slack has no heading syntax. Convert all heading levels to a bold line:

```
# Title       →   *Title*
## Section    →   *Section*
### Sub       →   *Sub*
```

Ensure a blank line before and after each converted heading for visual separation.

### 8. Links

```
[display text](url)   →   <url|display text>
```

Leave bare URLs as-is; Slack auto-links them.

### 9. Unordered lists

```
- item    →   • item
* item    →   • item
+ item    →   • item
```

One level of nesting is supported with 4-space indent + `◦`:

```
- Parent      →   • Parent
  - Child     →       ◦ Child
    - Deep    →       ◦ Deep  (flatten to child level)
```

### 10. Ordered lists

Leave as-is — `1. item` renders correctly in Slack.

### 11. Blockquotes

Leave as-is — `> text` renders correctly in Slack.

### 12. Horizontal rules

```
---   →   (remove; replace with a blank line)
***   →   (remove)
___   →   (remove)
```

### 13. Tables

Slack does not render Markdown tables. Choose the best strategy:

**2-column table → key/value bullet list:**

```
| Setting | Value |        *Settings:*
|---------|-------|   →    • *Setting:* Value
| Port    | 3000  |        • *Port:* 3000
```

**Small table (≤5 cols, ≤8 rows) → fixed-width inside a code block:**

```
```

Col1 Col2 Col3
────── ────── ──────
val1 val2 val3

```
```

Add a note: `_ℹ️ Slack doesn't render tables — shown as fixed-width text above._`

**Comparison / feature table → sectioned bold list:**

```
| Tool    | Pros       | Cons      |
|---------| -----------|-----------|

→

*Tool*
• *Pros:* …
• *Cons:* …
```

### 14. Images

```
![alt](url)   →   <url|alt>
```

Note to user that images don't embed inline in Slack messages.

### 15. Checkboxes

```
- [ ] task   →   • ☐ task
- [x] task   →   • ☑ task
```

### 16. Special HTML entities in content

Escape literal `<`, `>`, `&` that aren't part of a link:

```
<  →  &lt;
>  →  &gt;   (except leading > for blockquotes)
&  →  &amp;
```

______________________________________________________________________

## Length guidance

| Output length | Suggestion |
|--------------|------------|
| < 1,500 chars | Fine as a single message |
| 1,500–4,000 chars | Add a note: "This is long — consider splitting into 2–3 messages" |
| > 4,000 chars | Add a note: "This is very long — consider using a Slack Canvas instead" |

______________________________________________________________________

## Quick validation checklist (run mentally before outputting)

- [ ] No `**double asterisk**` bold remaining
- [ ] No `## headers` remaining
- [ ] No `[text](url)` links remaining
- [ ] No `---` horizontal rules remaining
- [ ] Tables handled (not left as raw Markdown)
- [ ] Code block language hints stripped
- [ ] Nested lists flattened to max 2 levels
- [ ] Output is inside a single fenced code block
