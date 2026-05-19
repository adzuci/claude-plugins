# Summary Format Reference

## Template

The triage summary follows a strict format. Do not deviate.

### AM Mode

```
*AM Triage // [Weekday Mon DD]* — [N] threads · [N] drafts · [N] Slack msgs · GEN-SE: [N / not triggered]

*🔴 ACT*
*[Subject/name]* — [One tight sentence: what + why] → [Specific action]

*🟡 WATCH*
*[Deal/subject]* — [$amt · Close [date] · Stage] [Open loops: (1) owner/task. (2) owner/task.] → [Recommended move]

*🟢 FYI*
*[Topic]* — [One line] ([source, date])

*Open loops*
[Item] → [Owner] · [deadline or "no deadline"]
```

### PM / EOD Mode

Same as AM, plus this section at the end:

```
*Tomorrow's first 3*
1. [Highest-priority item — deal risk, GEN-SE escalation, or hard deadline]
2. [Second priority]
3. [Third priority]
```

## Formatting Rules

1. **Header is ONE line.** All stats inline. No line breaks in the header.

2. **Three tiers only.** ACT, WATCH, FYI. No other tier names.
   - ACT: requires action before the AE's next commitment (AM) or before EOD (PM)
   - WATCH: deal threads, overdue items, close-date risk. Monitor.
   - FYI: informational only. One line each.

3. **Empty sections are omitted entirely.** Clean inbox = just the header line
   plus "Inbox clear — nothing actionable."

4. **No horizontal dividers.** Do not use `---` in Slack messages. It breaks formatting.

5. **No em dashes.** Use commas, periods, or parentheses instead.

6. **GEN-SE outputs map to tiers:**
   - Draft ready → WATCH with "[Draft ready]" appended. If `draft_notes` is populated, append context: "[Draft ready — pricing context needed]" or similar.
   - Escalation → ACT with GEN-SE's stated reason
   - BLOCK → ACT with "GEN-SE BLOCK: [reason]"

7. **Open loops section:** flat list. Each line: item → owner · deadline.
   No sub-bullets, no nesting.

8. **"Tomorrow's first 3"** (PM only): ranked by genuine deal and deadline
   priority, not recency. GEN-SE escalations and hard deadlines rank highest.

9. **Deal entries in WATCH:** compress to two lines max. Format:
   `*[Name]* — $[amt] · Close [date] · [Stage]`
   then open loops on same or next line.

10. **Slack mrkdwn only.** Bold = `*text*`. No markdown headers (#), no
    code blocks for the summary body. Bullets use `-` not `•` if needed,
    but prefer inline lists over bullet points.
