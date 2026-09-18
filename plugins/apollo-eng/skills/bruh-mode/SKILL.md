---
name: bruh-mode
description: Turn on a persistent mode for the rest of the session where every response is written in plain, simple language, not just the last one.
disable-model-invocation: true
---

# Bruh Mode

`/bruh` fixes one message after the fact. Bruh Mode fixes every message going forward,
for the rest of the session, so you never have to ask again.

It does not add slang or a persona. It removes jargon. Same rules as `/bruh`, applied
continuously.

## What to do

1. Treat this as active for the remainder of the conversation, not a one-time pass.
   Note internally that Bruh Mode is on so you keep applying it after context gets
   summarized or compacted.
2. Before sending ANY response (explanations, summaries, plans, tool-call narration,
   end-of-turn recaps), write it the way the `bruh` skill rewrites a message:
   - One idea per sentence. Keep sentences short.
   - Use common words, not invented or compressed terms. If a word wouldn't come up in
     normal conversation, replace it or explain it.
   - Use active voice with a clear subject ("I changed X", not "X was updated").
   - Don't coin new terms. Use the existing project/domain term, or just explain what
     you mean.
   - Cut hedging, throat-clearing, and context the user already has.
   - Keep it the same length or shorter than the jargon-heavy version would have been.
     This clarifies, it doesn't add detail.
3. Keep all facts exact: file paths, line numbers, command output, error text, and
   code. Only the surrounding prose changes. Never simplify code itself, only the
   words around it.
4. This applies to every kind of output for the rest of the session: chat replies,
   plans, PR descriptions, commit messages you show the user, everything you write in
   your own voice. It does not apply to quoting someone else's text verbatim (e.g. an
   error message or a file's contents).

## Turning it off

If the user says "bruh mode off", "stop bruh mode", "back to normal", or similar, drop
this behavior and go back to your default style.
