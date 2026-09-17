---
name: bruh
description: Rewrite the assistant's last response in plain, simple language. Fixes dense, jargon-heavy, made-up-terminology output ("Claudisms"). Activate when the user says "/bruh", "bruh it", "bruh-ify", "talk like a bro", "make that make sense", or asks you to simplify your last message.
---

# Bruh

Rewrites your last response in plain language. Claude often writes dense, jargon-heavy
text with invented terms that force the reader to decode them ("the enrollment token is
fetched at boot", "nothing to install until public catches up"). This skill fixes that.
It does not add slang or a persona. It removes jargon.

## What to do

1. Take your own last message as the input (not the user's message).
2. Rewrite it in simple, plain English:
   - One idea per sentence. Keep sentences short.
   - Use common words, not invented or compressed terms. If a word wouldn't come up in
     normal conversation, replace it or explain it.
   - Use active voice with a clear subject ("I changed X", not "X was updated").
   - Don't coin new terms. Use the existing project/domain term, or just explain what
     you mean.
   - Cut hedging, throat-clearing, and context the user already has.
   - Keep it the same length or shorter. This step clarifies, it doesn't add detail.
3. Keep all facts exactly as they were: file paths, line numbers, command output, error
   text, and code. Only the surrounding prose changes.
4. Output only the rewritten version.

## When to activate

- User says "/bruh", "bruh it", "bruh-ify", "make that make sense", "in English please"
- User says your last response was confusing or hard to follow
- You suspect your last response was too dense or jargon-heavy
