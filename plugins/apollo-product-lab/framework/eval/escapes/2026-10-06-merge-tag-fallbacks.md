---
id: campaigns-merge-tag-fallbacks-1
kind: retrospective
initiative: campaigns (no harness folder; an existing product)
artifact: backend PR for merge-tag fallbacks
owning_stage: E.review (architecture and backend lenses)
adjudicated_by: initiative EM
adjudicated_on: 2026-10-06
fix: doc 43 §4 (current behaviour map), §5 (owning team), §6 (sizing); platform-rules R6
---

# Merge-tag fallbacks: the change fought the existing send path

Retrospective case, not replay. The original design, prompts and model settings were not archived.

## Finding

A senior reviewer rejected the backend PR, and it was rebuilt as a new PR. Their points:

1. The send path already substitutes every template tag in one pass. The change added more render
   passes and a lot of link rewriting at send time. The reviewer asked to let substitution finish
   as usual and only fill the tags that stayed unresolved.
1. Fallback values are written by the template author, so check them when the template is saved,
   not when the email is sent.
1. Too many options and conditions.
1. Invalid or unsafe link destinations were replaced with a placeholder. Odd or broken links in
   sent email can make mailbox providers distrust Apollo's sending domains. That is Deliverability's
   area, and nobody asked them.

The frontend PR merged with almost no comments.

## Owning stage

The architecture and backend lenses at design review. The evidence was available: the send path
code and its specs, `surface-owners.yml`, and the Deliverability sensitive-file entry in
`apollo-dev-teams.yml`. A CI comment named Deliverability, but only after the code was written.

## Why it was missed

- **Existing path not found.** No lens traced save, substitution and output end to end before
  designing.
- **No lens for this.** No owning-team lens existed; the sensitive-file match ran only in CI.
- The engineer did not know the backend flow and followed the harness. The harness did not reopen
  the question.

## Fix

- doc 43 §4: a current behaviour map is required before a design that changes existing behaviour,
  with every added pass explained, validation at save time by default, and the regression cases
  listed (unresolved tags, invalid destinations).
- doc 43 §5: lenses are chosen by what the change affects; ownership is detected at intake with
  the repo's own matching and again on the diff; the owner's answer is recorded before coding.
- doc 43 §6: this change is medium (behaviour change in another team's surface), so it gets one
  cross-family review of the design and one of the PR.
- platform-rules R6.
