# Slack Delivery

How to deliver a brief when the session answers into Slack (a Claude tag, a
thread reply, or `/apollo-support:account-brief` invoked from Slack). This is
the default delivery shape. One run should be enough: the AM should never have
to ask a follow-up question to get something readable.

## The Rule

Post a concise Slack summary as the message text, and attach the rendered
artifacts. Never paste the full HTML document or the full Markdown brief into a
Slack message.

Slack does not render HTML. Pasted markup arrives as escaped tag soup, and Slack
mangles parts of it. Slack also does not speak Markdown: it uses mrkdwn, where
bold is `*text*` (not `**text**`), `#` headers do not render, and pipe tables do
not render at all. The renderer's `--slack` mode already emits valid mrkdwn.

## One Command

```bash
python3 scripts/render_account_brief.py --json <payload.json> --bundle ./brief-out
```

That writes `account-brief.md`, `account-brief.html`, `account-brief.png`, and
`account-brief.slack.txt` into `./brief-out`, then prints a JSON manifest:

| Manifest key | Use |
| --- | --- |
| `slack_text` | Post this as the Slack message body, verbatim |
| `attachments` | Upload these files, in this order (PNG first) |
| `png` | Path to the PNG, or `null` when it could not be rendered |
| `png_detail` | The renderer that produced the PNG, or why it failed |

## Why PNG First

Slack previews an attached PNG inline, so the AM reads the brief without
opening anything. The HTML goes along with it for anyone who needs to copy text
out or open it full size. Attach the PNG first so it is the visible preview.

When `png` is `null`, attach the HTML alone and say in the message that the
image could not be rendered. Do not silently drop it. `png_detail` carries the
reason and the fix (usually an uninstalled Playwright or Chrome).

## When Attachments Fail

Uploading a file can fail, and sometimes it cannot be confirmed at all. Treat
attachments as best-effort and the message text as the deliverable.

`slack_text` is written to stand alone: it carries the coverage caveats, the
health line, the top red flags, and the top open tickets, with a truncation note
naming how many rows moved into the attachment. If an upload fails or you cannot
confirm it landed:

1. Still post the summary. It is useful on its own.
1. Say plainly that the attachment did not upload.
1. Give the local artifact path from the manifest so the operator can retrieve
   or re-upload it.

Never withhold the summary while retrying an upload, and never claim a file was
attached when you did not confirm it.

## Caveats Go Above The Numbers

Data-source caveats render at the top of the Slack summary, directly under the
title and above the health and ticket numbers they qualify. Do not move them to
the end, fold them into a footnote, or drop them because the summary got long.

A reader who stops after four lines must still know which sources were missing.
Populate `sources` and `caveats` in the payload (see
`references/output-shapes.md`); the renderer handles placement and the warning
marker. When no sources were recorded at all, the renderer says so rather than
implying full coverage.

## Freshness And Superseding

Every brief states its generation time and, when set, its `data_window`. This
matters when a slow source lands after the run: an Intercom or Jarvis pull that
arrives later does not retroactively make the earlier brief correct.

- Put the pull time in `caveats` for any source that lags, for example
  "Intercom pulled at 09:00 PT. Conversations after that are not included."
- When newer data arrives, render a new brief and say it supersedes the earlier
  one. Do not present the earlier run's numbers as current.
- Never restate a number from a previous run without re-querying it or marking
  it Unverified with the time it came from.

## Message Shape

The summary the renderer produces, in order:

1. Bold title line with the account name.
1. Italic subtitle: generation time, domain, data window.
1. Data coverage line, with a `:warning:` marker when anything is incomplete,
   followed by one bullet per caveat.
1. Health bullets.
1. Red flags, P0 first, capped with a "+N more" note.
1. Open tickets, capped the same way.
1. Recent activity, when present.
1. Attachment footer naming the files, or stating that none were rendered.

Keep it that shape. If you need to add context, put it in the thread as a
separate message rather than expanding the summary past the point where an AM
stops reading.
