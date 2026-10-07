# Weekly Template Fallback

Use only when no human-written template post is found. Slack mrkdwn. Replace `<...>` placeholders; mark missing data as `unavailable`, never estimate.

```text
*<Team> OKR Status:* <status emoji> (as of <day>, data through <YYYY-MM-DD>)

*TL;DR*
- <one-line summary>

*Why <color>?*
- <observed value> vs target <target> (<metric>, <window>)

*Shipped*
- <summary> (<https://.../browse/KEY|KEY>)

*Next 2 weeks*
- <item>

*Next month*
- <item>

*Big rocks*
- <item>

*Changes to flag*
- <item, or "None">
```

Status emoji: `:large_green_circle:` every confirmed target met, `:large_yellow_circle:` a target missed but still reachable by period end, `:red_circle:` period target out of reach. Pick a color only when observed numbers against confirmed targets, or the current tracker's status column, support it. Otherwise write `*<Team> OKR Status:* pending metrics` and replace `*Why <color>?*` with `*Why pending?*` listing the missing inputs, with no status emoji.
