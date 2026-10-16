---
name: office-hours
description: Manual-invocation only. Draft DevOps office-hours announcements and produce transcript-backed recap proposals for #xfn-h-devops. Run via /apollo-eng-devops:office-hours.
argument-hint: '[announce|recap] [--date YYYY-MM-DD]'
disable-model-invocation: true
---

# Office Hours

Draft DevOps office-hours announcements and recap posts. This skill is draft-first:
it may gather read-only context, but it never posts to Slack without explicit review
and approval.

## Invocation

```text
/apollo-eng-devops:office-hours [announce|recap] [--date YYYY-MM-DD]
```

Defaults:

| Argument | Default | Meaning |
| --- | --- | --- |
| `announce` / `recap` | Ask if missing | Workflow mode. |
| `--date YYYY-MM-DD` | Today for `recap` | Office-hours date in the caller's local timezone. |

## Mode: `announce`

Draft a short Slack-ready office-hours message. Do not post or create a Slack draft.

If the caller did not provide enough detail, ask only for what is missing:

- when office hours is happening;
- what topic, incident pattern, rollout, or open question people should bring;
- whether this is a reminder, open invite, or follow-up.

Produce 2-3 short options:

1. **Reminder** - lightweight nudge before the session.
1. **Open invite** - broader "bring me sharp edges" note.
1. **Follow-up** - thanks plus next step after the session, when relevant.

Use this static tone guide, distilled from Adam Blackwell's Obsidian people profile at
skill creation time. Do not read Obsidian at runtime.

- measured, collaborative, and concrete;
- prefer "we" and practical next steps;
- use `&`, `+`, and `w/` naturally when it fits;
- technical but approachable;
- praise people specifically, not ideas generically;
- avoid hype, manufactured urgency, blame, "just checking in", "circle back",
  "touch base", "synergy", "no-brainer", and "game-changer".

Keep messages short enough for Slack. Close with a clear next step or offer of help.

## Mode: `recap`

Find notes or transcripts for a DevOps office-hours session, propose a summary, and
draft the `#xfn-h-devops` update for review.

Before gathering evidence:

1. Resolve the date. If `--date` is absent, use today in the caller's local timezone.
1. Check which transcript/note sources are available.
1. Load [`references/transcript-sources.md`](references/transcript-sources.md).
1. Use at most two transcript/note sources total.

Source priority and query patterns live in the reference file; follow its order.

Do not use Slack as a recap evidence source unless the caller explicitly broadens the
scope. Slack is the posting destination by default, not the transcript source.

### Script Fallback

When direct Granola, Zoom, or Notion meeting-note tools are missing or return no useful
candidate, use the read-only script described in the reference file.

## Recap Output

Always show the proposed output before any Slack action:

```markdown
Sources checked:
- <source>: <ok/missing/skipped> - <short reason>

Proposed recap:
- Topics raised: <bullets>
- Current understanding / decisions: <bullets>
- Open questions: <bullets>
- Follow-ups / owners: <bullets>
- Links used: <source links or "none found">

Draft Slack update for #xfn-h-devops:
<short message>

Review gate:
Reply "post this" if you want me to send this exact update to #xfn-h-devops.
```

If evidence is thin, say so directly and mark confidence as `confirmed`, `likely`, or
`unknown`. Summarize transcripts and notes; do not paste long transcript excerpts.

## Safety Rules

- Draft, propose, and ask for review before Slack writes.
- Never post, schedule, or create a Slack draft in `announce` mode.
- In `recap` mode, post only after explicit approval of the exact message.
- Keep the source cap: no more than two transcript/note sources total.
- Cite source links or IDs for factual claims when tools provide them.
- If no transcript is found, produce a concise "no matching transcript found" result
  with sources checked and suggested next query.
